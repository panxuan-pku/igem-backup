#!/usr/bin/env python3
"""CLI orchestrator: scRNA-seq → CNV intervals → candidate gene list for the L1 pipeline.

Subcommands (run from the pipeline root, 03_pipeline/):

  stage-samples   link raw GEO files into per-sample 10x dirs
  prepare-order   GTF → gene order table (data/gencode_gene_order.tsv)
  infercnv        load samples → QC → normalize → infercnvpy → window signals + h5ad
  call-segments   window signals → deletion segment tables (per resolution)
  extract-genes   segments + known clinical intervals → candidates.csv + expression QC + report
  all             prepare-order → infercnv → call-segments → extract-genes

Outputs land under config['output']['dir'] (default outputs/cnv/).
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .expression_qc import interval_gene_qc
from .gene_order import genes_in_interval, parse_gtf_genes
from .segments import call_deletion_segments, filter_segments, segment_overlap_frac


# ------------------------------------------------------------------ helpers
def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def sha256_file(p, _chunk=8192):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(_chunk), b""):
            h.update(chunk)
    return h.hexdigest()


def _outdir(cfg):
    d = Path(cfg.get("output", {}).get("dir", "outputs/cnv"))
    (d / "audit").mkdir(parents=True, exist_ok=True)
    return d


def _write_audit(cfg, outdir, stage, extra=None):
    payload = {"stage": stage, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "project": cfg.get("project"), "config": {
                   "qc": cfg.get("qc"), "infercnv": cfg.get("infercnv"),
                   "segments": cfg.get("segments"),
                   "known_intervals": cfg.get("known_intervals")}}
    if extra:
        payload.update(extra)
    run_file = outdir / "audit" / f"run_{stage}.json"
    run_file.write_text(json.dumps(payload, indent=2, default=str))
    return run_file


# ------------------------------------------------------------------ stages
def cmd_stage_samples(cfg):
    """Link raw GEO per-sample files (GSMxxx_SAMPLE_matrix.mtx.gz ...) into
    per-sample 10x dirs expected by scanpy.read_10x_mtx."""
    staged = []
    for s in cfg["samples"]:
        raw_dir = Path(s["raw_dir"])
        prefix = s["raw_prefix"]
        dest = Path(s["path"])
        dest.mkdir(parents=True, exist_ok=True)
        for src_name, dst_name in [
            (f"{prefix}_matrix.mtx.gz", "matrix.mtx.gz"),
            (f"{prefix}_barcodes.tsv.gz", "barcodes.tsv.gz"),
            (f"{prefix}_genes.tsv.gz", "genes.tsv.gz"),
        ]:
            src, dst = raw_dir / src_name, dest / dst_name
            if not src.exists():
                raise FileNotFoundError(f"missing raw file: {src}")
            if not dst.exists():
                dst.symlink_to(src.resolve())
        _ensure_features_tsv(dest)
        staged.append(str(dest))
    print(f"staged {len(staged)} samples: {staged}")


def _ensure_features_tsv(dest):
    """Newer scanpy only reads features.tsv.gz (3 cols: id, name, feature_type).
    GEO 'genes.tsv.gz' files are often the old 2-col format — convert in place."""
    import gzip
    genes = dest / "genes.tsv.gz"
    feat = dest / "features.tsv.gz"
    if feat.exists() or not genes.exists():
        return
    with gzip.open(genes, "rt") as f:
        first = f.readline()
    if len(first.rstrip("\n").split("\t")) >= 3:
        feat.symlink_to(genes.resolve())
        return
    with gzip.open(genes, "rt") as fin, gzip.open(feat, "wt") as fout:
        for line in fin:
            parts = line.rstrip("\n").split("\t")
            parts = (parts + ["Gene Expression"] * 3)[:3]
            fout.write("\t".join(parts) + "\n")


def cmd_prepare_order(cfg):
    ann = cfg["annotation"]
    genes = parse_gtf_genes(ann["gtf"])
    out = Path(ann["gene_order_tsv"])
    out.parent.mkdir(parents=True, exist_ok=True)
    genes.to_csv(out, sep="\t", index=False)
    print(f"wrote {out}: {len(genes)} genes ({genes['chrom'].nunique()} chromosomes)")
    return genes


def _load_gene_order(cfg):
    tsv = Path(cfg["annotation"]["gene_order_tsv"])
    if not tsv.exists():
        print(f"gene order table missing at {tsv}; building from GTF")
        return cmd_prepare_order(cfg)
    return pd.read_csv(tsv, sep="\t")


def cmd_infercnv(cfg):
    from . import infercnv as ic  # deferred: needs scanpy/infercnvpy

    outdir = _outdir(cfg)
    genes = _load_gene_order(cfg)
    qc = cfg.get("qc", {})
    cnv_cfg = cfg.get("infercnv", {})

    adata = ic.load_samples(cfg["samples"],
                            min_genes=qc.get("min_genes_per_cell", 200),
                            max_mito_pct=qc.get("max_mito_pct", 20.0),
                            downsample=qc.get("downsample_per_sample"),
                            seed=qc.get("seed", 0))
    print(f"loaded {adata.n_obs} cells × {adata.n_vars} genes "
          f"({dict(adata.obs['group'].value_counts())})")
    adata = ic.normalize_for_cnv(adata)
    adata = ic.order_by_position(adata, genes)
    print(f"positioned genes: {adata.n_vars}")

    input_path = outdir / "cnv_input.h5ad"
    adata.write_h5ad(input_path)

    resolutions = cnv_cfg.get("resolutions",
                              [{"name": "standard", "window_size": 100, "step": 10}])
    exclude = cnv_cfg.get("exclude_chromosomes", ["chrX", "chrY"])
    for res in resolutions:
        ic.run_infercnv(adata, reference_key="group",
                        reference_cat=cnv_cfg.get("reference_group", "reference"),
                        window_size=res["window_size"], step=res["step"],
                        exclude_chromosomes=exclude)
        tab = ic.window_table(adata, res["window_size"], res["step"],
                              group_col="group",
                              patient_cat=cnv_cfg.get("patient_group", "patient"),
                              ref_cat=cnv_cfg.get("reference_group", "reference"),
                              exclude_chromosomes=exclude)
        sig_path = outdir / f"window_signal_{res['name']}.tsv"
        tab.to_csv(sig_path, sep="\t", index=False)
        print(f"[{res['name']}] {len(tab)} windows → {sig_path} "
              f"(patient mean |score| {tab['score'].abs().mean():.4f}, "
              f"ref mean {tab['ref_score'].abs().mean():.4f})")

    _save_heatmap(adata, cfg, outdir)
    _write_audit(cfg, outdir, "infercnv", extra={
        "input_checksums": _sample_checksums(cfg), "n_cells": adata.n_obs,
        "n_positioned_genes": adata.n_vars, "h5ad": str(input_path)})


def _save_heatmap(adata, cfg, outdir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import infercnvpy as cnv
        cnv_cfg = cfg.get("infercnv", {})
        pat = cnv_cfg.get("patient_group", "patient")
        sub = adata[adata.obs["group"] == pat]
        cnv.pl.chromosome_heatmap(sub, groupby="sample", show=False)
        path = outdir / "heatmap_patient.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close("all")
        print(f"heatmap → {path}")
    except Exception as e:  # heatmap is evidence, not a gate
        print(f"WARN: heatmap skipped ({e})", file=sys.stderr)


def _sample_checksums(cfg):
    checks = {}
    for s in cfg["samples"]:
        for f in ("matrix.mtx.gz", "barcodes.tsv.gz", "features.tsv.gz"):
            p = Path(s["path"]) / f
            if p.exists():
                checks[str(p)] = sha256_file(p)
    gtf = Path(cfg["annotation"]["gtf"])
    if gtf.exists():
        checks[str(gtf)] = sha256_file(gtf)
    return checks


def cmd_call_segments(cfg):
    outdir = _outdir(cfg)
    seg_cfg = cfg.get("segments", {})
    z = seg_cfg.get("z_threshold", 1.5)
    min_w = seg_cfg.get("min_windows", 3)
    max_bp = (seg_cfg.get("max_segment_mb") or 0) * 1_000_000 or None
    resolutions = cfg.get("infercnv", {}).get(
        "resolutions", [{"name": "standard", "window_size": 100, "step": 10}])

    frames = []
    for res in resolutions:
        sig = pd.read_csv(outdir / f"window_signal_{res['name']}.tsv", sep="\t")
        segs = call_deletion_segments(sig[["chr", "start", "end", "score"]],
                                      z_threshold=z, min_windows=min_w)
        n_raw = len(segs)
        segs = filter_segments(segs, max_bp)
        segs["resolution"] = res["name"]
        segs.to_csv(outdir / f"segments_{res['name']}.csv", index=False)
        frames.append(segs)
        print(f"[{res['name']}] {len(segs)} deletion segments "
              f"(z<=-{z}, min {min_w} windows; {n_raw - len(segs)} dropped by size cap)")
    all_segs = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    all_segs.to_csv(outdir / "segments_all.csv", index=False)
    _write_audit(cfg, outdir, "call_segments",
                 extra={"n_segments": int(len(all_segs))})
    return all_segs


def cmd_extract_genes(cfg):
    outdir = _outdir(cfg)
    genes = _load_gene_order(cfg)
    cnv_cfg = cfg.get("infercnv", {})
    known = cfg.get("known_intervals", {}) or {}
    include_auto = cfg.get("extract", {}).get("include_auto_in_candidates", False)

    seg_path = outdir / "segments_all.csv"
    auto = pd.read_csv(seg_path) if seg_path.exists() else pd.DataFrame(
        columns=["chr", "start", "end", "resolution"])

    # ---- interval genes (known + auto, tracked separately) ------------------
    interval_genes, known_rows, auto_rows = {}, [], []
    for iv_id, iv in known.items():
        g = genes_in_interval(genes, iv["chr"], iv["start"], iv["end"])
        interval_genes[iv_id] = g
        for _, r in g.iterrows():
            known_rows.append({"gene_symbol": r["gene_name"], "source": "known_interval",
                               "deletion_id": iv_id, "chrom": r["chrom"],
                               "start": r["start"], "end": r["end"]})
    for i, s in auto.iterrows():
        iv_id = f"auto_{s['resolution']}_{i}"
        g = genes_in_interval(genes, s["chr"], s["start"], s["end"])
        interval_genes[iv_id] = g
        for _, r in g.iterrows():
            auto_rows.append({"gene_symbol": r["gene_name"], "source": "auto_segment",
                              "deletion_id": iv_id, "chrom": r["chrom"],
                              "start": r["start"], "end": r["end"]})

    known_cand = pd.DataFrame(known_rows)
    auto_cand = pd.DataFrame(auto_rows)
    if not known_cand.empty:
        known_cand = known_cand.drop_duplicates(["gene_symbol", "deletion_id"])
    if not auto_cand.empty:
        auto_cand = auto_cand.drop_duplicates(["gene_symbol", "deletion_id"])
        auto_cand.to_csv(outdir / "auto_segment_genes.csv", index=False)

    # candidates.csv = the L1-ready input; auto segments are exploratory by default
    cand = pd.concat([known_cand, auto_cand], ignore_index=True) if include_auto else known_cand
    cand_all = pd.concat([known_cand, auto_cand], ignore_index=True)
    if not cand.empty:
        cand = cand.drop_duplicates(["gene_symbol", "deletion_id"])
        cand.to_csv(outdir / "candidates.csv", index=False)
    if not cand_all.empty:
        cand_all = cand_all.drop_duplicates(["gene_symbol", "deletion_id"])
        cand_all.to_csv(outdir / "candidates_all.csv", index=False)
    print(f"candidates.csv: {cand['gene_symbol'].nunique() if not cand.empty else 0} genes "
          f"(known intervals only={not include_auto}); "
          f"candidates_all.csv: {cand_all['gene_symbol'].nunique() if not cand_all.empty else 0} genes")

    # ---- expression QC -------------------------------------------------------
    qc_df = pd.DataFrame()
    all_iv_genes = (pd.concat(interval_genes.values()).drop_duplicates("gene_name")
                    if interval_genes else pd.DataFrame())
    h5ad = outdir / "cnv_input.h5ad"
    if not all_iv_genes.empty and h5ad.exists():
        import anndata
        adata = anndata.read_h5ad(h5ad)
        qc_df = interval_gene_qc(adata, all_iv_genes, group_col="group",
                                 patient_cat=cnv_cfg.get("patient_group", "patient"),
                                 ref_cat=cnv_cfg.get("reference_group", "reference"),
                                 layer="counts")
        qc_df.to_csv(outdir / "interval_gene_expression_qc.csv", index=False)

    # ---- validation vs known intervals ----------------------------------------
    val_cfg = cfg.get("validation", {})
    min_ov = val_cfg.get("min_overlap_frac", 0.5)
    validations = []
    for iv_id, iv in known.items():
        g = interval_genes.get(iv_id, pd.DataFrame())
        overlaps = [segment_overlap_frac(s["chr"], s["start"], s["end"],
                                         iv["chr"], iv["start"], iv["end"])
                    for _, s in auto.iterrows()]
        best_ov = max(overlaps) if overlaps else 0.0
        markers = iv.get("markers", [])
        found = set(qc_df.loc[qc_df["found"] == True, "gene_name"]) if not qc_df.empty else set()
        iv_genes_found = set(g["gene_name"]) & found
        iv_fc = (qc_df[qc_df["gene_name"].isin(iv_genes_found)]["log2fc_patient_vs_ref"].mean()
                 if not qc_df.empty and iv_genes_found else float("nan"))
        validations.append({
            "interval": iv_id,
            "n_genes": int(len(g)),
            "n_genes_in_expression": int(len(iv_genes_found)),
            "mean_log2fc_interval_genes": float(iv_fc),
            "auto_overlap_frac": float(best_ov),
            "AC-CNV-1 (auto recovers known interval)": "PASS" if best_ov >= min_ov else "FAIL",
            "markers": ",".join(markers),
            "markers_in_expression": ",".join(m for m in markers if m in found),
            "AC-CNV-2 (markers detected in data)": (
                "PASS" if markers and all(m in found for m in markers) else "FAIL"),
        })
    val = pd.DataFrame(validations)
    if not val.empty:
        val.to_csv(outdir / "validation_known_intervals.csv", index=False)

    _write_report(cfg, outdir, cand, cand_all, qc_df, auto, val, include_auto,
                  known_genes=set(pd.concat([g for k, g in interval_genes.items()
                                             if k in known])["gene_name"]) if known else set())
    _write_audit(cfg, outdir, "extract_genes", extra={
        "n_candidates": int(cand["gene_symbol"].nunique()) if not cand.empty else 0,
        "validation": validations})
    return cand, qc_df, val


# ------------------------------------------------------------------ report
def _write_report(cfg, outdir, cand, cand_all, qc_df, auto, val, include_auto,
                  known_genes=None):
    lines = ["# scRNA-seq → 缺失区间基因 工作流报告", ""]
    lines.append(f"项目: {cfg.get('project')} · "
                 f"样本: {', '.join(s['id'] + '(' + s['group'] + ')' for s in cfg['samples'])}")
    lines.append("")
    lines.append("## 验收门槛 (AC)")
    lines.append("")
    if val.empty:
        lines.append("（config 中未配置 known_intervals，跳过验证）")
    else:
        lines.append("| interval | 区间基因数 | 检出基因数 | 区间基因平均 log2FC | 自动发现覆盖率 | AC-CNV-1 | AC-CNV-2 |")
        lines.append("|---|---|---|---|---|---|---|")
        for _, r in val.iterrows():
            lines.append(f"| {r['interval']} | {r['n_genes']} | {r['n_genes_in_expression']} | "
                         f"{r['mean_log2fc_interval_genes']:.2f} | "
                         f"{r['auto_overlap_frac']:.0%} | "
                         f"{r['AC-CNV-1 (auto recovers known interval)']} | "
                         f"{r['AC-CNV-2 (markers detected in data)']} |")
        lines.append("")
        lines.append("> 区间基因平均 log2FC ≈ 0 并不否定缺失存在：本项目 E8 已发现"
                     "杂合缺失在稳态 mRNA 层面被剂量补偿吸收（'mRNA 隐身'）。"
                     "这也正是表达型 CNV 自动发现困难的机制原因。")
        if (val["AC-CNV-1 (auto recovers known interval)"] == "FAIL").any():
            lines.append("")
            lines.append("> **AC-CNV-1 FAIL（负结果，预期内）**：表达型 CNV 推断未能自动恢复已知微缺失。"
                         "胚系杂合 1–3 Mb 缺失处于 inferCNV 分辨率极限；自动片段只作探索性候选，"
                         "candidates.csv 的生成不依赖它们。")
    lines.append("")
    lines.append("## 自动发现的缺失片段（探索性，需正交验证）")
    lines.append("")
    if auto.empty:
        lines.append("（无）")
    else:
        lines.append("| chr | start | end | 窗口数 | mean_z | resolution |")
        lines.append("|---|---|---|---|---|---|")
        for _, s in auto.iterrows():
            lines.append(f"| {s['chr']} | {int(s['start'])} | {int(s['end'])} | "
                         f"{s.get('n_windows', '')} | {s.get('mean_z', float('nan')):.2f} | "
                         f"{s['resolution']} |")
    lines.append("")
    lines.append("## 候选基因（供 L1 管线）")
    lines.append("")
    lines.append(f"- `candidates.csv`（**L1 管线输入**）: "
                 f"{cand['gene_symbol'].nunique() if not cand.empty else 0} 个基因"
                 f"{'（含自动片段基因）' if include_auto else '（仅已知临床区间，推荐）'}")
    lines.append(f"- `candidates_all.csv`（已知区间 + 自动片段并集）: "
                 f"{cand_all['gene_symbol'].nunique() if not cand_all.empty else 0} 个基因")
    lines.append(f"- `auto_segment_genes.csv`（仅自动片段，探索性）")
    lines.append("")
    lines.append("接入 L1 管线：")
    lines.append("```bash")
    lines.append(f"cp {outdir}/candidates.csv input/candidates.csv")
    lines.append("python -m src.normalize --input input/candidates.csv "
                 "--out data/normalized.csv --hgnc-alias data/hgnc_aliases.tsv")
    lines.append("```")
    lines.append("")
    lines.append("## 区间基因表达 QC（防 E6 型 pivot，仅已知临床区间）")
    lines.append("")
    qc_show = (qc_df[qc_df["gene_name"].isin(known_genes)] if known_genes else qc_df) \
        if not qc_df.empty else qc_df
    if qc_show.empty:
        lines.append("（无 h5ad 或无区间基因，跳过）")
    else:
        sub = qc_show.sort_values("log2fc_patient_vs_ref").head(10)
        lines.append("患者 vs 对照 log2FC 最低的 10 个区间基因：")
        lines.append("")
        lines.append("| gene | chr | mean_counts_patient | mean_counts_ref | "
                     "pct_expr_patient | pct_expr_ref | log2FC |")
        lines.append("|---|---|---|---|---|---|---|")
        for _, r in sub.iterrows():
            lines.append(f"| {r['gene_name']} | {r.get('chrom', '')} | "
                         f"{r['mean_counts_patient']:.3f} | {r['mean_counts_ref']:.3f} | "
                         f"{r['pct_expr_patient']:.1%} | {r['pct_expr_ref']:.1%} | "
                         f"{r['log2fc_patient_vs_ref']:.2f} |")
        silent = qc_show[(qc_show["found"] == True) & (qc_show["pct_expr_patient"] < 0.05)]
        if not silent.empty:
            lines.append("")
            lines.append(f"⚠️ 患者中表达细胞比例 <5% 的区间基因（E6 风险，"
                         f"L3 扰动工具不可用）: {', '.join(silent['gene_name'])}")
    lines.append("")
    lines.append("## 方法学说明")
    lines.append("")
    lines.append("- 表达型 CNV 推断（infercnvpy）为**回退路径**：胚系杂合微缺失（1–3 Mb）"
                 "处于其分辨率极限，自动片段只作候选，需正交方法（CNV 芯片/WGS/MLPA）确认。")
    lines.append("- 已知临床区间的基因提取**不依赖**表达信号，AC-CNV-1 失败不影响 candidates.csv 的生成。")
    lines.append("- 表达 QC 用 raw counts；log2FC 加 0.5 伪计数。")
    lines.append("")
    lines.append("审计: `audit/run_*.json` · 热图: `heatmap_patient.png`")
    (outdir / "cnv_report.md").write_text("\n".join(lines))
    print(f"report → {outdir / 'cnv_report.md'}")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(prog="cnv_workflow")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("stage-samples", "prepare-order", "infercnv",
                 "call-segments", "extract-genes", "all"):
        p = sub.add_parser(name)
        p.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = load_config(args.config)

    if args.cmd == "stage-samples":
        cmd_stage_samples(cfg)
    elif args.cmd == "prepare-order":
        cmd_prepare_order(cfg)
    elif args.cmd == "infercnv":
        cmd_infercnv(cfg)
    elif args.cmd == "call-segments":
        cmd_call_segments(cfg)
    elif args.cmd == "extract-genes":
        cmd_extract_genes(cfg)
    elif args.cmd == "all":
        cmd_prepare_order(cfg)
        cmd_infercnv(cfg)
        cmd_call_segments(cfg)
        cmd_extract_genes(cfg)


if __name__ == "__main__":
    main()
