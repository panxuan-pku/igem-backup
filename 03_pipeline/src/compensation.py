#!/usr/bin/env python3
"""mRNA compensation status analysis (v2.1 — 质询 #0).

Given scRNA-seq data with patient/control groups, computes per-gene
compensation ratio and classification.

A hemizygous deletion without compensation predicts ratio ≈ 0.5.
Ratio ≈ 1.0 suggests transcriptional dosage compensation.
"""
import argparse
import sys
import numpy as np
import pandas as pd

COMPENSATION_THRESHOLDS = {
    "full": (0.95, 1.05),
    "partial_high": (0.85, 0.95),
    "partial_low": (0.70, 0.85),
    "uncompensated": (0.40, 0.70),
    "unreliable": None,  # low-expression genes
}

def compute_compensation(adata, genes_of_interest, group_col="condition",
                         patient_cat="WS", ref_cat="CTRL",
                         layer="counts",
                         min_detection_pct=0.01):
    """For each gene, compute patient/control expression ratio and classify.

    Returns DataFrame: gene, ratio, compensation_class, mean_pat, mean_ref,
    pct_pat, pct_ref, n_pat, n_ref
    """
    if group_col not in adata.obs.columns:
        raise ValueError(f"adata.obs lacks {group_col!r}")
    groups = adata.obs[group_col].astype(str)
    pat_mask = (groups == str(patient_cat)).to_numpy()
    ref_mask = (groups == str(ref_cat)).to_numpy()
    if pat_mask.sum() == 0 or ref_mask.sum() == 0:
        raise ValueError(f"No cells for {patient_cat!r} or {ref_cat!r}")

    X = adata.layers[layer] if layer else adata.X
    var_idx = pd.Index(adata.var_names.astype(str))

    rows = []
    in_data = [g for g in genes_of_interest if g in var_idx]
    missing = [g for g in genes_of_interest if g not in var_idx]
    if missing:
        print(f"WARN: {len(missing)} genes not in adata: {missing[:5]}...",
              file=sys.stderr)

    for gene in in_data:
        gi = var_idx.get_loc(gene)
        col = X[:, gi]
        vals = col.toarray().ravel() if hasattr(col, "toarray") else np.asarray(col).ravel()
        pv, rv = vals[pat_mask], vals[ref_mask]
        mp, mr = float(pv.mean()), float(rv.mean())
        pp = float((pv > 0).mean())
        rp = float((rv > 0).mean())
        ratio = mp / mr if mr > 0 else np.nan

        classification = "unreliable"
        if pp < min_detection_pct and rp < min_detection_pct:
            classification = "unreliable"
        elif not np.isnan(ratio):
            for cls, (lo, hi) in {
                k: v for k, v in COMPENSATION_THRESHOLDS.items() if v is not None
            }.items():
                if lo <= ratio <= hi:
                    classification = cls
                    break
            else:
                if ratio > 1.05:
                    classification = "overcompensated"
                elif ratio < 0.40:
                    classification = "strongly_down"

        rows.append({
            "gene": gene,
            "compensation_ratio": round(ratio, 4) if not np.isnan(ratio) else np.nan,
            "compensation_class": classification,
            "mean_patient": round(mp, 4),
            "mean_reference": round(mr, 4),
            "pct_patient": round(pp, 4),
            "pct_reference": round(rp, 4),
            "n_patient": int(pat_mask.sum()),
            "n_reference": int(ref_mask.sum()),
        })

    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5ad", required=True)
    ap.add_argument("--genes", required=True, help="CSV of gene_symbols (one column)")
    ap.add_argument("--group-col", default="condition")
    ap.add_argument("--patient", default="WS")
    ap.add_argument("--reference", default="CTRL")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    try:
        import scanpy as sc
    except ImportError:
        print("FATAL: scanpy not installed", file=sys.stderr)
        sys.exit(3)

    adata = sc.read_h5ad(args.h5ad)
    genes_df = pd.read_csv(args.genes)
    gene_col = "gene_symbol" if "gene_symbol" in genes_df.columns else genes_df.columns[0]
    genes = genes_df[gene_col].dropna().astype(str).tolist()

    result = compute_compensation(adata, genes,
                                  group_col=args.group_col,
                                  patient_cat=args.patient,
                                  ref_cat=args.reference)
    result.to_csv(args.out, index=False)
    print(f"wrote {args.out}: {len(result)} genes assessed")

    # summary
    counts = result["compensation_class"].value_counts()
    for cls in ["full", "partial_high", "partial_low", "uncompensated",
                "overcompensated", "strongly_down", "unreliable"]:
        n = counts.get(cls, 0)
        labels = {
            "full": "fully compensated (ratio 0.95-1.05)",
            "partial_high": "partial: high (0.85-0.95)",
            "partial_low": "partial: low (0.70-0.85)",
            "uncompensated": "uncompensated (0.40-0.70)",
            "overcompensated": "overcompensated (>1.05)",
            "strongly_down": "strongly downregulated (<0.40)",
            "unreliable": "unreliable (low expression)",
        }
        if n > 0:
            print(f"  {cls}: {n} genes ({labels[cls]})")


if __name__ == "__main__":
    main()