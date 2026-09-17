#!/usr/bin/env python3
"""
Compute weighted consensus ranking from evidence.parquet (+ optional AI scores).
Writes candidates_ranked.csv and report.md.
"""
import argparse
import pandas as pd
import yaml

def score_row(row, weights):
    score = 0.0
    votes = []

    def val(col):
        v = row.get(col)
        return v if v is not None and v == v else None  # NaN check

    cg = val("clinGen_hi_score")
    if cg is not None:
        w = weights.get("clinGen_hi_score", 0)
        try:
            s = int(cg)
            if s >= 3:
                contrib = w
            elif s == 2:
                contrib = w * 0.5
            elif s <= 1:
                contrib = -w * 0.5
            else:
                contrib = 0
            score += contrib
            votes.append(("clinGen_hi", contrib))
        except Exception:
            pass

    pli = val("gnomad_pLI")
    if pli is not None:
        w = weights.get("gnomad_pLI", 0)
        try:
            pli_f = float(pli)
            if pli_f > 0.9:
                contrib = w
            elif pli_f > 0.5:
                contrib = w * 0.5
            else:
                contrib = 0
            score += contrib
            votes.append(("pLI", contrib))
        except Exception:
            pass

    loeuf = val("gnomad_LOEUF")
    if loeuf is not None:
        w = weights.get("gnomad_LOEUF", 0)
        try:
            loe = float(loeuf)
            if loe < 0.35:
                contrib = w
            elif loe < 0.6:
                contrib = w * 0.5
            else:
                contrib = 0
            score += contrib
            votes.append(("LOEUF", contrib))
        except Exception:
            pass

    for col in ["DeepLOF_score", "DosaCNV_score", "DeepGenePrior_score"]:
        s = val(col)
        if s is not None:
            w = weights.get(col, 0)
            try:
                sf = float(s)
                if sf > 0.5:
                    score += w
                    votes.append((col, w))
                elif sf > 0:
                    score += w * 0.5
                    votes.append((col, w * 0.5))
            except Exception:
                pass

    neg = 0.0
    for organ in ["liver", "brain", "kidney", "gastrointestinal"]:
        col = f"hpa_{organ}_expr"
        v = val(col)
        if v is not None:
            try:
                vf = float(v)
                if vf > 1.0:
                    neg -= 2
                    votes.append((f"hpa_{organ}", -2))
            except Exception:
                pass
    score += neg
    return score, votes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--ai-scores", default=None)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    weights = cfg["consensus"]["base_weights"]

    ev = pd.read_parquet(args.evidence)
    if "hgnc_id" not in ev.columns:
        raise ValueError("evidence must have hgnc_id")

    if args.ai_scores:
        try:
            ai = pd.read_csv(args.ai_scores)
            ev = ev.merge(ai, on="hgnc_id", how="left")
        except Exception:
            print("WARN: ai_scores read failed; skipping AI contribution")

    scores = ev.apply(lambda r: score_row(r, weights), axis=1)
    ev_cons = pd.DataFrame([list(s) for s in scores], columns=["consensus_score", "votes"])
    out = pd.concat([ev.reset_index(drop=True), ev_cons[["consensus_score"]]], axis=1)
    out = out.sort_values(["consensus_score", "hgnc_id"], ascending=[False, True]).reset_index(drop=True)
    out.insert(0, "rank", out.index + 1)

    out.to_csv(args.out, index=False)

    top = out.head(10)
    lines = [
        "# 微缺失主效基因筛选 — 共识排名",
        "",
        f"Top {len(top)} of {len(out)} genes.",
        "",
        "| rank | hgnc_id | input_symbol | consensus_score |",
        "|------|---------|--------------|-----------------|",
    ]
    for _, r in top.iterrows():
        lines.append(f"| {int(r['rank'])} | {r['hgnc_id']} | {r.get('input_symbol','')} | {r['consensus_score']:.2f} |")
    lines.append("")
    lines.append("## 数据源校验")
    lines.append("```")
    lines.append("checksums shown in outputs/audit/data_checksums.txt")
    lines.append("```")
    open(args.report, "w").write("\n".join(lines))

    print(f"wrote {args.out} with {len(out)} rows; report at {args.report}")

if __name__ == "__main__":
    main()
