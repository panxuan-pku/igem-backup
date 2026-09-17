#!/usr/bin/env python3
"""Convert official precomputed DeepLOF scores into the L1 pipeline's ai_scores.csv.

Source: LaPolice & Huang (2023), BMC Bioinformatics 24:347.
Official scores: "Additional file 3 / Data File 2 — Scores from the nonlinear
DeepLOF model" (figshare 24159504, CC BY 4.0), mirrored to data/DeepLOF_scores.csv.
MD5 (official): 4f7a9c6520b840db677963cfe82d3e34

Output contract (docs/api/ai_scores.md): outputs/ai_scores.csv with columns
  hgnc_id, DeepLOF_score
read by src/consensus_v2.py via `--ai-scores`.

Usage (from 03_pipeline/):
  uv run --with pandas python -m src.ai_scores deeplof \
      --scores data/DeepLOF_scores.csv \
      --aliases data/hgnc_aliases.tsv \
      --out outputs/ai_scores.csv
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import pandas as pd

OFFICIAL_MD5 = "4f7a9c6520b840db677963cfe82d3e34"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_symbol_map(alias_path):
    alias = pd.read_csv(alias_path, sep="\t", dtype=str)
    m = {}
    for _, row in alias.iterrows():
        hg = row.get("hgnc_id")
        if not hg:
            continue
        for sym_col in ("symbol", "prev_symbol", "alias_symbol"):
            for s in str(row.get(sym_col, "")).split(","):
                s = s.strip().upper()
                if s and s not in m:
                    m[s] = hg
    return m


def cmd_deeplof(args):
    scores = pd.read_csv(args.scores)
    required = {"ensembl", "gene_symbol", "DeepLOF_score"}
    if not required <= set(scores.columns):
        raise ValueError(f"scores file must have columns {sorted(required)}, "
                         f"got {scores.columns.tolist()}")

    md5 = hashlib.md5(Path(args.scores).read_bytes()).hexdigest()
    if md5 != OFFICIAL_MD5:
        print(f"WARN: md5 {md5} != official {OFFICIAL_MD5}; proceed anyway", file=sys.stderr)

    symbol_map = build_symbol_map(args.aliases)
    out = scores[["gene_symbol", "DeepLOF_score"]].copy()
    out["gene_symbol_upper"] = out["gene_symbol"].str.upper()
    out["hgnc_id"] = out["gene_symbol_upper"].map(symbol_map)
    mapped = out["hgnc_id"].notna().sum()
    print(f"mapped {mapped}/{len(out)} genes to HGNC ID "
          f"({mapped / len(out):.1%})")
    out = out[["hgnc_id", "DeepLOF_score"]].dropna(subset=["hgnc_id"])
    out = out.drop_duplicates("hgnc_id")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    # score distribution
    q = out["DeepLOF_score"].quantile([0.1, 0.5, 0.9])
    print(f"DeepLOF score distribution: median {q[0.5]:.3f}, "
          f"p10 {q[0.1]:.3f}, p90 {q[0.9]:.3f}")

    audit = {
        "source": "figshare 24159504 (Additional file 3, Data File 2)",
        "md5_official": OFFICIAL_MD5,
        "md5_downloaded": md5,
        "n_genes_total": len(scores),
        "n_genes_mapped": len(out),
        "mapping_rate": round(mapped / len(scores), 4),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    out_path.parent.joinpath("audit").mkdir(parents=True, exist_ok=True)
    Path(out_path.parent / "audit" / f"ai_scores_deeplof_{time.strftime('%Y%m%d')}.json").write_text(
        json.dumps(audit, indent=2))
    print(f"wrote {out_path} ({len(out)} genes); audit saved")
    return out


def main():
    ap = argparse.ArgumentParser(prog="ai_scores")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("deeplof")
    p.add_argument("--scores", required=True)
    p.add_argument("--aliases", required=True)
    p.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.cmd == "deeplof":
        cmd_deeplof(args)


if __name__ == "__main__":
    main()