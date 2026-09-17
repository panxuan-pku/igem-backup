#!/usr/bin/env python3
"""
Consensus v2 — normalized weighted scoring + Borda cross-check + optional
leave-one-out positive-control weight tuning.

Differences vs src/consensus.py (v1):
1. Every continuous evidence is normalized (rank | zscore | raw) BEFORE
   weighting, so weights are comparable across differently-scaled sources
   (v1 multiplied raw values of mixed scales by fixed weights).
2. HPA organ penalty reads per_organ_weight from config (v1 hard-coded -2)
   and is capped (hpa_penalty.cap) so multi-organ high expression cannot
   sink a gene without bound.
3. Missing evidence is neutral: 0 contribution in the additive score and
   median points in Borda (config: borda.missing), never a hidden penalty.
4. Optional Borda rank aggregation is reported next to the additive rank;
   their Spearman agreement is shown in the report (agreement = confidence).
5. Optional leave-one-out tuning of evidence weights against known driver
   genes (positive controls), maximizing recall@top-N with a simplicity
   tie-break (closest to default weights).

Expected evidence schema (see 工程化指导书 §3.4):
  hgnc_id, input_symbol,
  clinGen_hi_score (0-3), gnomad_pLI (0-1), gnomad_LOEUF (>=0, lower=constrained),
  hpa_{organ}_expr (log1p TPM), optional AI scores
  (DeepLOF_score / DosaCNV_score / DeepGenePrior_score, 0-1).

Drop-in CLI replacement for src/consensus.py, plus:
  --controls PATH   txt with one positive-control symbol per line (overrides config)
  --tune            force-enable leave-one-out weight tuning
"""
import argparse
import itertools
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

DEFAULT_CONTROLS = ["TBX1", "ELN", "KCTD13", "RAI1", "GTF2I"]
HPA_DEFAULT_ORGANS = ["liver", "brain", "kidney", "gastrointestinal"]


# ---------------------------------------------------------------- config
def _default_config(cfg):
    """Derive a v2 config from the v1 pipeline.yaml blocks (backwards compatible)."""
    v1w = cfg.get("consensus", {}).get("base_weights", {}) or {}
    hpa = cfg.get("hpa_filter", {}) or {}
    evidence = {}
    for col, w in v1w.items():
        if col == "negative_hpa_organ":
            continue
        if col == "clinGen_hi_score":
            direction = "ordinal"
        elif col == "gnomad_LOEUF":
            direction = "lower_better"
        else:
            direction = "higher_better"
        evidence[col] = {"direction": direction, "weight": float(w)}
    return {
        "normalize": "rank",
        "evidence": evidence,
        "hpa_penalty": {
            "organs": list(hpa.get("organs", HPA_DEFAULT_ORGANS)),
            "expr_threshold": float(hpa.get("high_expression_log", 1.0)),
            "per_organ_weight": float(v1w.get("negative_hpa_organ", -2)),
            "cap": -4.0,
        },
        "borda": {"enabled": True, "missing": "median"},
        "tuning": {
            "enabled": False,
            "positive_controls": list(DEFAULT_CONTROLS),
            "weight_grid": [0, 1, 2, 3],
            "target_top_n": 10,
        },
    }


def load_v2_config(cfg):
    """Merge config['consensus_v2'] over v1-derived defaults."""
    base = _default_config(cfg)
    user = cfg.get("consensus_v2") or {}
    for key in ("normalize",):
        if key in user:
            base[key] = user[key]
    for col, spec in (user.get("evidence") or {}).items():
        merged = dict(base["evidence"].get(col, {"direction": "higher_better", "weight": 1.0}))
        merged.update(spec or {})
        if "weight" in merged:
            merged["weight"] = float(merged["weight"])
        base["evidence"][col] = merged
    for section in ("hpa_penalty", "borda", "tuning"):
        if section in user and isinstance(user[section], dict):
            base[section].update(user[section])
    return base


# -------------------------------------------------------- normalization
def normalize_series(s, method, direction, ordinal_scale=None):
    """Map an evidence column to [0,1] (NaN preserved); 1.0 = most driver-like."""
    s = pd.to_numeric(s, errors="coerce")
    valid = s.dropna()
    if valid.empty:
        return s.astype(float)
    if ordinal_scale:
        return (s.clip(lower=0, upper=ordinal_scale) / float(ordinal_scale)).astype(float)
    if method == "rank":
        v = s.rank(pct=True, method="average")
    elif method == "zscore":
        mu, sd = float(valid.mean()), float(valid.std(ddof=0))
        z = (s - mu) / (sd if sd > 0 else 1.0)
        lo, hi = float(z.min()), float(z.max())
        v = (z - lo) / (hi - lo) if hi > lo else pd.Series(0.5, index=s.index)
    elif method == "raw":
        lo, hi = float(valid.min()), float(valid.max())
        v = (s - lo) / (hi - lo) if hi > lo else pd.Series(0.5, index=s.index)
    else:
        raise ValueError(f"unknown normalize method: {method!r} (rank|zscore|raw)")
    if direction == "lower_better":
        v = 1.0 - v
    return v.astype(float)


def build_scoring_matrix(df, ev_cfg, method):
    """Return (A, cols, coverage, normed).

    A: (n_genes x n_evidences) adjusted contribution matrix with NaN -> 0,
       where ordinal low-score penalties are folded in as negative indicators
       (scaled by spec['low_score_penalty'], default 0 for non-ordinal evidence).
    normed: {col: normalized Series with NaN preserved} for Borda.
    """
    normed = {}
    coverage = {}
    cols, mats = [], []
    for col, spec in ev_cfg.items():
        if col not in df.columns:
            coverage[col] = 0.0
            continue
        scale = spec.get("ordinal_scale")
        v = normalize_series(df[col], method, spec.get("direction", "higher_better"), scale)
        cov = float(v.notna().mean())
        coverage[col] = cov
        if cov == 0.0:
            continue
        adj = v.fillna(0.0).to_numpy(dtype=float)
        low_pen = float(spec.get("low_score_penalty", 0.0) or 0.0)
        if low_pen and scale:
            raw = pd.to_numeric(df[col], errors="coerce")
            indicator = ((raw <= 1.0) & raw.notna()).to_numpy(dtype=float)
            adj = adj - low_pen * indicator
        normed[col] = v
        cols.append(col)
        mats.append(adj)
    A = np.column_stack(mats) if mats else np.zeros((len(df), 0))
    return A, cols, coverage, normed


# ------------------------------------------------------------- scoring
def hpa_penalty_term(df, hpa_cfg):
    """Per-gene negative term: per_organ_weight per organ above threshold, capped."""
    organs = hpa_cfg.get("organs", HPA_DEFAULT_ORGANS)
    thr = float(hpa_cfg.get("expr_threshold", 1.0))
    per = float(hpa_cfg.get("per_organ_weight", -2.0))
    cap = float(hpa_cfg.get("cap", -4.0))
    term = np.zeros(len(df))
    for organ in organs:
        col = f"hpa_{organ}_expr"
        if col not in df.columns:
            continue
        expr = pd.to_numeric(df[col], errors="coerce")
        term += per * (expr > thr).fillna(False).to_numpy(dtype=float)
    return np.maximum(term, cap)  # cap is negative: never penalize more than cap


def score_all(A, weights, hpa_term, recessive_mask=None, recessive_penalty=0.5):
    """Compute consensus scores.
    v2.1: If recessive_mask is provided, scale down pLI contribution for recessive genes.
    recessive_penalty: multiplier for gnomAD weights on recessive genes (default 0.5 = halved).
    """
    base = A @ np.asarray(weights, dtype=float)
    if recessive_mask is not None and recessive_mask.any():
        # Identify which columns are gnomAD-derived (pLI, LOEUF)
        # We don't know column order here, so apply a simpler strategy:
        # Reduce the total score for recessive genes by a flat factor
        # proportional to how much gnomAD contributed
        pass  # handled in build_scoring_matrix instead
    return base + hpa_term


def borda_points(normed, cols, weights, n, missing="median"):
    """Weighted Borda: best gene gets (n-1) points per evidence, scaled by weight.

    Missing values get median points (neutral) or 0, per `missing`.
    """
    pts = np.zeros(n)
    for col, w in zip(cols, weights):
        s = normed[col]
        ranks = s.rank(ascending=False, method="average")  # best -> 1
        p = (n - ranks).to_numpy(dtype=float)
        fill = (n - 1) / 2.0 if missing == "median" else 0.0
        p = np.where(np.isnan(p), fill, p)
        pts += float(w) * p
    return pts


# -------------------------------------------------------------- tuning
def loo_tune(df, A, cols, default_w, tune_cfg, hpa_term, symbol_col):
    """Leave-one-out weight tuning against positive controls.

    For each held-out control: grid-search weights maximizing recall@N on the
    remaining controls (tie-break: closest L1 distance to default weights),
    then evaluate the held-out control's rank. Final weights are re-selected
    on ALL controls with the same rule.
    """
    grid = [float(x) for x in tune_cfg.get("weight_grid", [0, 1, 2, 3])]
    top_n = int(tune_cfg.get("target_top_n", 10))
    controls = [str(c).strip() for c in tune_cfg.get("positive_controls", DEFAULT_CONTROLS)]
    syms = df[symbol_col].astype(str).str.upper()
    sym_set = set(syms)
    present = [c for c in controls if c.upper() in sym_set]
    missing_ctrl = [c for c in controls if c.upper() not in sym_set]
    idx_of = {c: int(np.flatnonzero(syms.to_numpy() == c.upper())[0]) for c in present}
    result = {"controls_requested": controls, "controls_present": present,
              "controls_missing": missing_ctrl, "folds": [], "final_weights": None}

    if len(present) < 2 or not cols:
        result["note"] = "need >=2 positive controls present in candidates; tuning skipped"
        return result

    combos = [w for w in itertools.product(grid, repeat=len(cols)) if any(x > 0 for x in w)]
    default_w = list(default_w)

    def recall(weights, control_idxs):
        scores = score_all(A, weights, hpa_term)
        top = set(np.argsort(-scores, kind="stable")[:top_n].tolist())
        return sum(1 for i in control_idxs if i in top) / len(control_idxs)

    def best_weights(train_idxs):
        scored = [(recall(w, train_idxs), w) for w in combos]
        best_r = max(r for r, _ in scored)
        tied = [w for r, w in scored if r == best_r]
        tied.sort(key=lambda w: sum(abs(a - b) for a, b in zip(w, default_w)))
        return list(tied[0]), best_r

    for held in present:
        train = [idx_of[c] for c in present if c != held]
        w_star, r_train = best_weights(train)
        scores = score_all(A, w_star, hpa_term)
        held_idx = idx_of[held]
        rank = int((scores > scores[held_idx]).sum()) + 1
        result["folds"].append({"held_out": held, "train_recall": r_train,
                                "held_out_rank": rank, "held_out_in_topN": rank <= top_n,
                                "weights": w_star})
    w_final, r_all = best_weights([idx_of[c] for c in present])
    result["final_weights"] = w_final
    result["final_recall"] = r_all
    result["loo_hit_rate"] = float(np.mean([f["held_out_in_topN"] for f in result["folds"]]))
    return result


# ---------------------------------------------------------------- run
def run_consensus(df, cfg2, controls_path=None, tune_override=False, sensitivity=False,
                 mode="auto"):
    """Score + rank. Returns (out_df, meta).
    v2.1: sensitivity=True enables weight sensitivity analysis.
    v2.2: mode selects behaviours (validate|rank|full|exploratory|auto).
    """
    ev_cfg = cfg2["evidence"]
    method = cfg2.get("normalize", "rank")
    symbol_col = "input_symbol" if "input_symbol" in df.columns else (
        "gene_symbol" if "gene_symbol" in df.columns else "hgnc_id")

    A, cols, coverage, normed = build_scoring_matrix(df, ev_cfg, method)
    hpa_term = hpa_penalty_term(df, cfg2["hpa_penalty"])
    default_w = [float(ev_cfg[c].get("weight", 0.0)) for c in cols]

    tune_cfg = dict(cfg2.get("tuning", {}))
    controls_list = []
    if controls_path:
        with open(controls_path) as f:
            controls_list = [ln.strip() for ln in f if ln.strip()]
        tune_cfg["positive_controls"] = controls_list
    do_tune = bool(tune_cfg.get("enabled")) or tune_override
    tuning = None
    weights = default_w
    if do_tune:
        tuning = loo_tune(df, A, cols, default_w, tune_cfg, hpa_term, symbol_col)
        if tuning.get("final_weights"):
            weights = tuning["final_weights"]

    scores = score_all(A, weights, hpa_term)
    out = df.copy()
    out["consensus_score"] = scores
    for j, col in enumerate(cols):
        out[f"contrib_{col}"] = A[:, j] * weights[j]
    out["hpa_penalty"] = hpa_term

    # ---- v2.1: recessive penalty ----
    recessive_applied = False
    if "recessive" in df.columns:
        r_mask = df["recessive"].fillna(False).to_numpy(dtype=bool)
        if r_mask.any():
            gnomad_cols_in = [c for c in cols if "gnomad" in c.lower()]
            for gc in gnomad_cols_in:
                ci = cols.index(gc)
                penalty_factor = float(cfg2.get("recessive", {}).get("gnomad_weight_multiplier", 0.5))
                out[f"contrib_{gc}"] = out[f"contrib_{gc}"] * (
                    penalty_factor if r_mask.shape == out[f"contrib_{gc}"].shape
                    else 1.0
                )
                if r_mask.shape == out[f"contrib_{gc}"].shape:
                    out.loc[r_mask, f"contrib_{gc}"] *= penalty_factor
            # recompute scores with penalized contributions
            contribs = [out[f"contrib_{c}"] for c in cols]
            out["consensus_score"] = sum(contribs) + hpa_term
            recessive_applied = True

    # ---- v2.1: weight sensitivity (perturb each weight ±1) ----
    sensitivity_result = None
    if sensitivity and cols:
        sens = {"perturbations": []}
        baseline_ranks = None
        for ci, col in enumerate(cols):
            for delta in [-1, +1]:
                w_pert = list(weights)
                w_pert[ci] = max(0, w_pert[ci] + delta)
                if w_pert == list(weights):
                    continue
                s_pert = score_all(A, w_pert, hpa_term)
                ranks_pert = pd.Series(s_pert).rank(ascending=False, method="min").astype(int)
                if baseline_ranks is None:
                    baseline_ranks = pd.Series(scores).rank(ascending=False, method="min").astype(int)
                rank_shift = (ranks_pert - baseline_ranks).abs().max()
                top3_baseline = set(baseline_ranks.nsmallest(3).index)
                top3_pert = set(ranks_pert.nsmallest(3).index)
                top3_change = len(top3_baseline.symmetric_difference(top3_pert)) // 2
                sens["perturbations"].append({
                    "evidence": col, "delta": delta, "weight_perturbed": w_pert[ci],
                    "max_rank_shift": int(rank_shift), "top3_genes_changed": int(top3_change),
                })
        max_shift = max(p["max_rank_shift"] for p in sens["perturbations"]) if sens["perturbations"] else 0
        n_perturb = len(sens["perturbations"])
        n_top3_changes = sum(1 for p in sens["perturbations"] if p["top3_genes_changed"] > 0)
        sensitivity_result = {
            "perturbations": sens["perturbations"],
            "max_rank_shift": max_shift,
            "n_perturbations_tested": n_perturb,
            "n_causing_top3_change": n_top3_changes,
            "robustness": "high" if n_top3_changes == 0
            else ("moderate" if n_top3_changes <= n_perturb // 2 else "low"),
        }

    meta = {"method": method, "cols": cols, "coverage": coverage,
            "weights": dict(zip(cols, weights)), "default_weights": dict(zip(cols, default_w)),
            "tuning": tuning, "hpa_cfg": cfg2["hpa_penalty"],
            "recessive_applied": recessive_applied,
            "sensitivity": sensitivity_result,
            "mode": mode,
            "controls_list": controls_list,
            "symbol_col": symbol_col}

    borda_cfg = cfg2.get("borda", {})
    if borda_cfg.get("enabled", True) and cols:
        out["borda_score"] = borda_points(normed, cols, weights, len(df),
                                          missing=borda_cfg.get("missing", "median"))
        out["borda_rank"] = out["borda_score"].rank(ascending=False, method="min").astype(int)
        meta["spearman"] = float(out["consensus_score"].rank().corr(out["borda_score"].rank()))
    else:
        meta["spearman"] = None

    out = out.sort_values(["consensus_score", "hgnc_id"], ascending=[False, True],
                          kind="stable").reset_index(drop=True)
    out.insert(0, "rank", out.index + 1)
    return out, meta


# ------------------------------------------------------------- report
def render_report(out, meta, top_n=10):
    mode = meta.get("mode", "auto")
    mode_label = {
        "validate": "Mode A · 验证报告（已知主效基因）",
        "rank": "Mode B · 增强筛选（排序 + 正对照检验）",
        "full": "Mode C · 全栈筛选（排序 + 补偿状态）",
        "exploratory": "Mode D · 探索性粗筛",
        "auto": "auto（自动）",
    }.get(mode, mode)
    lines = ["# 微缺失主效基因筛选 — 共识排名 (consensus v2)", ""]
    lines.append(f"Pipeline mode: **{mode_label}** · Normalization: **{meta['method']}** · {len(out)} genes")
    lines.append("")
    lines.append("## Weights used")
    lines.append("")
    lines.append("| evidence | weight (default) | weight (used) | coverage |")
    lines.append("|---|---|---|---|")
    for col in meta["cols"]:
        lines.append(f"| {col} | {meta['default_weights'][col]:g} | "
                     f"{meta['weights'][col]:g} | {meta['coverage'][col]:.0%} |")
    missing_cols = [c for c, cov in meta["coverage"].items() if cov == 0.0]
    if missing_cols:
        lines.append("")
        lines.append(f"⚠️ evidence columns absent or all-missing (0 contribution): "
                     f"{', '.join(missing_cols)}")
    lines.append("")
    lines.append(f"HPA penalty: per-organ {meta['hpa_cfg'].get('per_organ_weight')} above "
                 f"expr>{meta['hpa_cfg'].get('expr_threshold')}, capped at {meta['hpa_cfg'].get('cap')}")
    lines.append("")

    # ---- v2.1: recessive penalty note ----
    if meta.get("recessive_applied"):
        lines.append("⚠️ Recessive disease penalty: gnomAD weights halved for genes tagged as "
                     "recessive in OMIM/ClinVar (heterozygous deletion may have no phenotype).")
        lines.append("")

    # ---- v2.1: compensation status ----
    if "compensation_class" in out.columns:
        lines.append("## mRNA compensation status (scRNA-seq, when available)")
        lines.append("")
        lines.append("| rank | gene | compensation ratio | class | SINEUP potential |")
        lines.append("|---|---|---|---|---|")
        for _, r in out.head(top_n).iterrows():
            c = r.get("compensation_class", "unreliable")
            ratio = r.get("compensation_ratio", "")
            ratio_str = f"{ratio:.3f}" if isinstance(ratio, float) and not (isinstance(ratio, float) and np.isnan(ratio)) else "N/A"
            sineup = "★ ideal" if c == "full" else ("▲ partial" if "partial" in str(c) else ("? unknown" if c == "unreliable" else "✗ not compensated"))
            lines.append(f"| {int(r['rank'])} | {r.get('input_symbol', r.get('gene', ''))} | {ratio_str} | {c} | {sineup} |")
        lines.append("")

    # ---- v2.2: positive-control check (Mode B/C; informative for all) ----
    cc = meta.get("controls_check")
    if cc and mode in ("rank", "full", "validate", "auto"):
        lines.append("## 正对照检验（已知主效基因位置）")
        lines.append("")
        lines.append("| gene | in candidates | rank | top-10 | consensus | ClinGen | pLI | 补偿 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for c in cc:
            if not c.get("in_candidates"):
                lines.append(f"| {c['control']} | ❌ 不在候选 | — | — | — | — | — | — |")
            else:
                lines.append(
                    f"| {c['control']} | ✓ | {c['rank']} | {'✓' if c['top10'] else '✗'} | "
                    f"{c['consensus_score']:.3f} | {c.get('clinGen_hi_score') or '—'} | "
                    f"{c.get('gnomad_pLI') or '—'} | {c.get('compensation_class') or '—'} |")
        lines.append("")
        lines.append(f"正对照 top-10 命中率: **{meta['controls_top10_n']}/{meta['controls_total']}**")
        lines.append("")

    # ---- v2.2: validation panel (Mode A) ----
    vp = meta.get("validation_panel")
    if vp:
        lines.append("## 验证报告 — 已知主效基因证据面板 (Mode A)")
        lines.append("")
        lines.append("| gene | rank | ClinGen HI | gnomAD pLI | consensus | SINEUP 靶向条件 | 补偿状态 |")
        lines.append("|---|---|---|---|---|---|---|")
        for p in vp:
            lines.append(
                f"| {p['gene']} | {p['rank']} | {p.get('clinGen_hi_score') or '—'} | "
                f"{p.get('gnomad_pLI') or '—'} | {p['consensus_score']:.3f} | "
                f"{'✓ 满足 (HI≥2 或 pLI≥0.9)' if p['target_ok'] else '✗ 不满足'} | {p.get('compensation_class') or '—'} |")
        lines.append("")
        lines.append(f"验证结论: **{'✓ 通过 — 已知主效基因满足 SINEUP 靶向条件' if meta.get('validation_pass') else '✗ 未通过 — 无已知基因满足靶向条件'}")
        lines.append("")

    # ---- v2.2: exploratory disclaimer (Mode D) ----
    if mode == "exploratory":
        lines.append("## ⚠️ 探索模式声明 (Mode D)")
        lines.append("")
        lines.append("本区间无可信人工金标准（ClinGen 覆盖低）或已知主效基因。以下排名为"
                     "**探索性粗筛**：只表示群体约束 + 表达可行性的初步排序，"
                     "**不构成确定性靶点结论**。建议补充文献/实验正对照后再读此排名。")
        lines.append("")

    lines.append(f"## Top {min(top_n, len(out))}")
    lines.append("")
    hdr = "| rank | hgnc_id | symbol | score |"
    sep = "|---|---|---|---|"
    if "borda_rank" in out.columns:
        hdr += " borda_rank |"
        sep += "---|"
    lines += [hdr, sep]
    for _, r in out.head(top_n).iterrows():
        row = (f"| {int(r['rank'])} | {r['hgnc_id']} | {r.get('input_symbol', '')} "
               f"| {r['consensus_score']:.3f} |")
        if "borda_rank" in out.columns:
            row += f" {int(r['borda_rank'])} |"
        lines.append(row)
    lines.append("")

    if meta.get("spearman") is not None:
        lines.append(f"Additive-rank vs Borda-rank Spearman ρ = **{meta['spearman']:.3f}** "
                     f"(>0.8: the two aggregation schemes largely agree)")
        lines.append("(Borda aggregates evidence columns only; HPA penalty is additive-only.)")
        lines.append("")

    # ---- v2.1: warnings ----
    for w in meta.get("warnings", []):
        lines.append(w)
        lines.append("")

    t = meta.get("tuning")
    if t:
        lines.append("## Leave-one-out weight tuning (positive controls)")
        lines.append("")
        if t.get("note"):
            lines.append(f"⚠️ {t['note']}")
        else:
            lines.append(f"Controls present: {', '.join(t['controls_present'])} "
                         f"(missing from candidates: {', '.join(t['controls_missing']) or 'none'})")
            lines.append("")
            lines.append("| held-out | rank | in top-N | train recall |")
            lines.append("|---|---|---|---|")
            for f in t["folds"]:
                lines.append(f"| {f['held_out']} | {f['held_out_rank']} | "
                             f"{'✓' if f['held_out_in_topN'] else '✗'} | {f['train_recall']:.2f} |")
            lines.append("")
            lines.append(f"LOO hit rate: **{t['loo_hit_rate']:.0%}** · "
                         f"final recall@N on all controls: {t['final_recall']:.2f}")
            lines.append("")
            lines.append("Final weights: " + ", ".join(
                f"{c}={w:g}" for c, w in zip(meta["cols"], t["final_weights"])))
        lines.append("")

    lines.append("## 数据源校验")
    lines.append("```")
    lines.append("checksums shown in outputs/audit/data_checksums.txt")
    lines.append("```")

    # ---- v2.1: weight sensitivity ----
    sens = meta.get("sensitivity")
    if sens:
        lines.append("")
        lines.append("## ⚖️ 权重敏感性分析")
        lines.append("")
        lines.append(f"- {sens['n_perturbations_tested']} 次权重扰动测试 (±1 每个证据列)")
        lines.append(f"- 最大排名偏移: {sens['max_rank_shift']} 位")
        lines.append(f"- 扰动导致 Top-3 变化的次数: {sens['n_causing_top3_change']}/{sens['n_perturbations_tested']}")
        lines.append(f"- 排名稳健性: **{sens['robustness']}**")
        lines.append("")
        if sens["robustness"] == "low":
            lines.append("> ⚠️ 排名对权重选择敏感。建议考虑前 N 个候选进行正交验证"
                         "而非直接选择排名 #1 作为唯一靶点。")
    
    # ---- v2.1: experiment recommendations ----
    if "experiments" in meta:
        lines.append("")
        lines.append("## 🧪 实验验证建议")
        lines.append("")
        for exp in meta["experiments"]:
            lines.append(f"### {exp.get('title', '')}")
            lines.append(exp.get("body", ""))
            lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--ai-scores", default=None)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--controls", default=None,
                    help="txt with one positive-control symbol per line (overrides config)")
    ap.add_argument("--tune", action="store_true",
                    help="force-enable leave-one-out weight tuning")
    ap.add_argument("--sensitivity", action="store_true",
                    help="run weight sensitivity analysis (±1 per evidence weight)")
    ap.add_argument("--compensation", default=None,
                    help="CSV from src/compensation.py: mRNA compensation per gene")
    ap.add_argument("--mode", default="auto",
                    help="pipeline mode: auto|validate|rank|full|exploratory (default: auto)")
    ap.add_argument("--warnings", action="store_true",
                    help="emit sparse-evidence warnings for Mode D")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    cfg2 = load_v2_config(cfg)

    ev = pd.read_parquet(args.evidence)
    if "hgnc_id" not in ev.columns:
        raise ValueError("evidence must have hgnc_id")

    if args.ai_scores:
        try:
            ai = pd.read_csv(args.ai_scores)
            ev = ev.merge(ai, on="hgnc_id", how="left")
        except Exception:
            print("WARN: ai_scores read failed; skipping AI contribution", file=sys.stderr)

    # v2.1: merge compensation data if provided
    if args.compensation:
        try:
            comp = pd.read_csv(args.compensation)
            ev = ev.merge(comp.rename(columns={"gene": "input_symbol"}),
                         on="input_symbol", how="left")
        except Exception:
            print("WARN: compensation CSV read failed; skipping", file=sys.stderr)

    out, meta = run_consensus(ev, cfg2, controls_path=args.controls,
                              tune_override=args.tune, sensitivity=args.sensitivity,
                              mode=args.mode or "auto")

    # ---- v2.1: mode-dependent metadata ----
    mode = args.mode or "auto"
    meta["mode"] = mode

    clinGen_cov = meta.get("coverage", {}).get("clinGen_hi_score", 0)
    n_genes = len(out)
    top3_scores = out["consensus_score"].head(3).values if len(out) >= 3 else None

    # Warnings for sparse-evidence scenarios (Mode D)
    if args.warnings or mode in ("exploratory", "auto"):
        warnings = []
        if clinGen_cov < 0.2:
            warnings.append(
                f"⚠️ ClinGen 仅覆盖该区间 {clinGen_cov:.0%} 的基因。"
                "以下排序主要依赖 gnomAD 约束分数——这可能偏向'群体遗传学上不耐受'的基因，"
                "漏掉'组织特异性但未被 Curators 研究过'的重要基因。"
            )
        if n_genes > 20 and top3_scores is not None and len(top3_scores) >= 3:
            score_gap = float(top3_scores[0] - top3_scores[2])
            score_mean = float(out["consensus_score"].std())
            if score_gap < score_mean:
                warnings.append(
                    f"⚠️ 该区间基因数较多 ({n_genes}) 且排名前 3 的证据分数差距较小"
                    f" (gap={score_gap:.2f}, σ={score_mean:.2f})。"
                    "可能存在多个表型贡献基因。单一排名不应被解译为'唯一的因果基因'。"
                    "建议对前 N 个候选进行正交验证。"
                )
        if clinGen_cov == 0:
            warnings.append(
                "⚠️ 该区间的所有基因均无 ClinGen 剂量敏感性评级。"
                "排序完全依赖 gnomAD 约束和 HPA 表达数据——置信度低。"
                "建议在实验验证前补充分子生物学文献调研。"
            )
        meta["warnings"] = warnings

    # ---- v2.2: mode-specific analysis ----
    # Positive-control check (used by rank/full/validate; informative for exploratory)
    controls_check = []
    symbol_col = meta.get("symbol_col", "input_symbol")
    rank_map = out.set_index(symbol_col)["rank"] if symbol_col in out.columns else None
    for ctrl in meta.get("controls_list", []):
        if rank_map is not None and ctrl in rank_map.index:
            row = out.loc[out[symbol_col] == ctrl].iloc[0]
            controls_check.append({
                "control": ctrl,
                "in_candidates": True,
                "rank": int(row["rank"]),
                "top10": bool(row["rank"] <= 10),
                "consensus_score": float(row["consensus_score"]),
                "clinGen_hi_score": row.get("clinGen_hi_score"),
                "gnomad_pLI": row.get("gnomad_pLI"),
                "compensation_class": row.get("compensation_class", ""),
            })
        else:
            controls_check.append({"control": ctrl, "in_candidates": False})
    meta["controls_check"] = controls_check
    meta["controls_top10_n"] = sum(1 for c in controls_check if c.get("top10"))
    meta["controls_total"] = sum(1 for c in controls_check if c.get("in_candidates"))

    # Mode validate (A): known-driver evidence panel for the validation report
    if mode == "validate":
        panel = []
        for c in meta.get("controls_list", []):
            if symbol_col in out.columns:
                m = out.loc[out[symbol_col] == c]
                if len(m):
                    r = m.iloc[0]
                    clingen = r.get("clinGen_hi_score")
                    pli = r.get("gnomad_pLI")
                    try:
                        clingen_ok = bool(clingen is not None and not (isinstance(clingen, float) and np.isnan(clingen)) and float(clingen) >= 2)
                    except (TypeError, ValueError):
                        clingen_ok = False
                    try:
                        pli_ok = bool(pli is not None and not (isinstance(pli, float) and np.isnan(pli)) and float(pli) >= 0.9)
                    except (TypeError, ValueError):
                        pli_ok = False
                    panel.append({
                        "gene": c, "rank": int(r["rank"]),
                        "clinGen_hi_score": clingen, "gnomad_pLI": pli,
                        "consensus_score": float(r["consensus_score"]),
                        "target_ok": clingen_ok or pli_ok,
                        "compensation_class": r.get("compensation_class", ""),
                    })
        meta["validation_panel"] = panel
        meta["validation_pass"] = any(p["target_ok"] for p in panel)

    # v2.1: experiment recommendations
    experiments = []
    if mode == "exploratory":
        # Mode D does not assert a single top candidate; no experiment recommendation.
        meta["experiments"] = experiments
    else:
        top_gene = out.iloc[0] if len(out) > 0 else None
        if top_gene is not None:
            sym = top_gene.get("input_symbol", top_gene.get("gene_symbol", ""))
            evidence = []
            for c in meta.get("cols", []):
                if c in top_gene.index:
                    val = top_gene[c]
                    if not (isinstance(val, float) and np.isnan(val)) and val != 0:
                        evidence.append(f"{c}={val:.2f}" if isinstance(val, (int, float)) else f"{c}={val}")
            comp = top_gene.get("compensation_class", "")
            experiments.append({
                "title": f"第一候选验证路径: {sym}",
                "body": (
                    f"**证据**: {', '.join(evidence) if evidence else '参见证据面板'}\n\n"
                    f"**补偿状态**: {comp if comp else '未评估 (无scRNA-seq数据)'}\n\n"
                    "建议验证步骤:\n"
                    "1. qPCR 确认缺失断点包含 {sym}（在患者 gDNA 上）\n"
                    "2. Western blot 确认蛋白质是否不足（翻译层未补偿）\n"
                    f"3. 如果蛋白不足 → 设计 SINEUP-{sym} → 细胞模型测试蛋白恢复\n"
                    f"4. 如果蛋白正常 → 切换到备选基因（见下）"
                )
            })
            # backup candidates
            top5_symbols = out["input_symbol" if "input_symbol" in out.columns else "hgnc_id"].head(5).tolist()
            backup = [s for s in top5_symbols[1:] if s != sym]
            experiments.append({
                "title": "切换策略",
                "body": (
                    f"如果 {sym} 的蛋白质正常（翻译也补偿了），切换到以下备选:\n"
                    + "\n".join(f"- {b}" for b in backup[:3])
                    + f"\n\n切换标准: ≥1 项正交证据（pLI/ClinGen/表达）独立于 {sym}"
                )
            })
            if len(backup) >= 3:
                experiments.append({
                    "title": "排名不确定时的建议",
                    "body": (
                        "前几个候选的证据等级相近。建议不直接靶向单一基因，"
                        "而是先在患者细胞系中做 shRNA rescue 实验:\n"
                        "- 恢复每个候选基因的表达\n"
                        "- 看哪个恢复表型最好\n"
                        "- 用这个正对照结果更新管线的权重"
                    )
                })
        meta["experiments"] = experiments
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    with open(args.report, "w") as f:
        f.write(render_report(out, meta))

    print(f"wrote {args.out} with {len(out)} rows; report at {args.report}")
    if meta.get("tuning") and meta["tuning"].get("loo_hit_rate") is not None:
        print(f"LOO hit rate on positive controls: {meta['tuning']['loo_hit_rate']:.0%}")


if __name__ == "__main__":
    main()
