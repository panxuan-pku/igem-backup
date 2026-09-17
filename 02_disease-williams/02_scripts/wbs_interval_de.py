#!/usr/bin/env python3
"""DE analysis for 7q11.23 interval genes in WS brain organoids.
Answers: does GTF2I (and other deleted genes) show DE != 0?"""
import scanpy as sc
import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, mannwhitneyu
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
H5AD = PROJECT_ROOT / "02_disease-williams" / "03_intermediate" / "processed.h5ad"
OUT = PROJECT_ROOT / "06_epidemiology" / "data" / "wbs_interval_de_analysis.csv"

# WBS 7q11.23 interval genes (core set from literature + CNV pipeline)
WBS_GENES = [
    "GTF2I", "GTF2IRD1", "GTF2IRD2", "ELN", "LIMK1", "BAZ1B", "CLIP2",
    "STX1A", "FZD9", "FKBP6", "EIF4H", "LAT2", "RFC2", "CLDN3", "CLDN4",
    "WBSCR22", "WBSCR27", "ABHD11", "ABHD11-AS1", "BUD23", "METTL27",
    "TMEM270", "TBL2", "MLXIPL", "DNAJC30", "POM121C", "NSUN5", "TRIM50",
    "CYB5D2", "SPDYE1", "SPDYE2", "SPDYE3", "SPDYE4", "SPDYE5", "SPDYE6",
]

def load(use_raw=True):
    adata = sc.read_h5ad(H5AD)
    if use_raw and "counts" in adata.layers:
        adata.X = adata.layers["counts"]
    adata.obs["is_WS"] = (adata.obs["condition"] == "WS").astype(int)
    for g in WBS_GENES:
        if g not in adata.var_names:
            print(f"WARN: {g} not in var_names, skipping")
    return adata

def pseudobulk_de(adata):
    """Per-sample pseudobulk → t-test on log2(CPM+0.5)"""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
    
    # aggregate raw counts per sample
    samples = sorted(adata.obs["sample"].unique())
    is_ws = {s: (adata.obs[adata.obs["sample"]==s]["condition"].iloc[0] == "WS")
             for s in samples}
    
    # build sample x gene matrix of summed counts
    mat = np.zeros((len(samples), adata.n_vars))
    for i, s in enumerate(samples):
        mask = adata.obs["sample"] == s
        mat[i, :] = np.asarray(adata[mask].X.sum(axis=0)).ravel()
    
    # CPM + log2
    lib_size = mat.sum(axis=1, keepdims=True)
    cpm = mat / lib_size * 1e6
    log_cpm = np.log2(cpm + 0.5)
    
    genes_of_interest = [g for g in WBS_GENES if g in adata.var_names]
    
    rows = []
    for gene in genes_of_interest:
        idx = list(adata.var_names).index(gene)
        ws_vals = log_cpm[[i for i, s in enumerate(samples) if is_ws[s]], idx]
        ctrl_vals = log_cpm[[i for i, s in enumerate(samples) if not is_ws[s]], idx]
        
        # also per-cell stats for context
        cell_mask = adata.var_names == gene
        cell_vals = np.asarray(adata[:, cell_mask].X.toarray()).ravel()
        ws_cells = cell_vals[adata.obs["is_WS"] == 1]
        ctrl_cells = cell_vals[adata.obs["is_WS"] == 0]
        
        mean_ws = ws_cells.mean()
        mean_ctrl = ctrl_cells.mean()
        pct_ws = (ws_cells > 0).mean()
        pct_ctrl = (ctrl_cells > 0).mean()
        
        # pseudobulk log2FC
        log2fc = ws_vals.mean() - ctrl_vals.mean()
        
        # per-sample t-test (n=3 vs 3)
        if ws_vals.std() > 0 or ctrl_vals.std() > 0:
            t_stat, t_pval = ttest_ind(ws_vals, ctrl_vals, equal_var=False)
        else:
            t_stat, t_pval = np.nan, np.nan
        
        # per-cell mann-whitney as secondary check
        try:
            _, mw_pval = mannwhitneyu(ws_cells, ctrl_cells, alternative='two-sided')
        except ValueError:
            mw_pval = np.nan
        
        rows.append({
            "gene": gene,
            "log2FC_pseudobulk": round(log2fc, 4),
            "t_stat": round(t_stat, 4) if not np.isnan(t_stat) else np.nan,
            "t_pval": round(t_pval, 6) if not (isinstance(t_pval, float) and np.isnan(t_pval)) else np.nan,
            "mw_pval": round(mw_pval, 6) if not (isinstance(mw_pval, float) and np.isnan(mw_pval)) else np.nan,
            "mean_counts_WS": round(mean_ws, 2),
            "mean_counts_CTRL": round(mean_ctrl, 2),
            "pct_expr_WS": round(pct_ws, 4),
            "pct_expr_CTRL": round(pct_ctrl, 4),
        })
    
    return pd.DataFrame(rows).sort_values("log2FC_pseudobulk")

def main():
    print("Loading data...")
    adata = load()
    
    print(f"CTRL cells: {(adata.obs['condition']=='CTRL').sum()}, WS cells: {(adata.obs['condition']=='WS').sum()}")
    print(f"Samples: {sorted(adata.obs['sample'].unique())}")
    print(f"WS samples: {sorted(adata.obs[adata.obs['condition']=='WS']['sample'].unique())}")
    
    print("\nRunning DE analysis...")
    result = pseudobulk_de(adata)
    
    # sort by absolute log2FC
    result["abs_log2FC"] = result["log2FC_pseudobulk"].abs()
    result = result.sort_values("abs_log2FC", ascending=False)
    
    print(f"\n=== 7q11.23 Interval Genes: DE Analysis ===")
    print(f"(Positive log2FC = higher in WS patients)")
    print(f"(Negative log2FC = lower in WS patients — consistent with hemizygous deletion)")
    print()
    
    cols_show = ["gene", "log2FC_pseudobulk", "t_pval", "mean_counts_WS", "mean_counts_CTRL", "pct_expr_WS", "pct_expr_CTRL"]
    print(result[cols_show].to_string(index=False, float_format=lambda x: f"{x:.4f}" if not np.isnan(x) else "nan"))
    
    # highlight GTF2I
    gtf2i = result[result["gene"] == "GTF2I"]
    if not gtf2i.empty:
        row = gtf2i.iloc[0]
        print(f"\n>>> GTF2I specifically:")
        print(f"    log2FC (pseudobulk) = {row['log2FC_pseudobulk']:.4f}")
        print(f"    WS mean counts/cell = {row['mean_counts_WS']:.2f}, CTRL = {row['mean_counts_CTRL']:.2f}")
        print(f"    ratio WS/CTRL = {row['mean_counts_WS']/row['mean_counts_CTRL']:.3f}" if row['mean_counts_CTRL'] > 0 else "    ratio = N/A (CTRL zero)")
        print(f"    t-test p-value = {row['t_pval']:.6f}")
        print(f"    pct cells expressing (WS) = {row['pct_expr_WS']:.2%}, (CTRL) = {row['pct_expr_CTRL']:.2%}")
    
    result.to_csv(OUT, index=False)
    print(f"\nFull results saved to {OUT}")

if __name__ == "__main__":
    main()
