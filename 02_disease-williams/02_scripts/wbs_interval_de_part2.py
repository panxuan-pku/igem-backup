#!/usr/bin/env python3
"""Part 2: Per-cell Wilcoxon DE + variance analysis for WBS interval genes."""
import scanpy as sc
import pandas as pd
import numpy as np
from pathlib import Path

H5AD = Path(__file__).resolve().parents[1] / "03_intermediate" / "processed.h5ad"
WBS_GENES = [g for g in [
    "GTF2I", "GTF2IRD1", "GTF2IRD2", "ELN", "LIMK1", "BAZ1B", "CLIP2",
    "STX1A", "FZD9", "FKBP6", "EIF4H", "LAT2", "RFC2", "CLDN3", "CLDN4",
    "MLXIPL", "TBL2", "SPDYE1", "SPDYE3", "SPDYE5", "SPDYE6", "CYB5D2",
] if g in sc.read_h5ad(H5AD).var_names]

# Reload
adata = sc.read_h5ad(H5AD)
adata.X = adata.layers["counts"].copy()
adata.obs["is_WS"] = (adata.obs["condition"] == "WS").astype(int)

# Per-cell Wilcoxon: scanpy's rank_genes_groups
print("Running per-cell Wilcoxon DE...")
sc.tl.rank_genes_groups(
    adata, groupby="condition", groups=["WS"], reference="CTRL",
    method="wilcoxon", n_genes=len(WBS_GENES),
    key_added="de_wilcoxon"
)

# Extract results
de_result = sc.get.rank_genes_groups_df(adata, group="WS", key="de_wilcoxon")
wbs_de = de_result[de_result["names"].isin(WBS_GENES)].copy()
wbs_de = wbs_de.rename(columns={"names": "gene"})

# Merge with per-cell stats
cell_stats = []
for gene in WBS_GENES:
    idx = list(adata.var_names).index(gene)
    vals = np.asarray(adata[:, idx].X.toarray()).ravel()
    ws_c = vals[adata.obs["is_WS"] == 1]
    ctrl_c = vals[adata.obs["is_WS"] == 0]
    cell_stats.append({
        "gene": gene,
        "mean_WS": ws_c.mean(), "mean_CTRL": ctrl_c.mean(),
        "var_WS": ws_c.var(), "var_CTRL": ctrl_c.var(),
        "pct_WS": (ws_c > 0).mean(), "pct_CTRL": (ctrl_c > 0).mean(),
        "n_WS": len(ws_c), "n_CTRL": len(ctrl_c),
    })
stats_df = pd.DataFrame(cell_stats)

result = wbs_de.merge(stats_df, on="gene")
result["ratio_WS_CTRL"] = result["mean_WS"] / result["mean_CTRL"].replace(0, np.nan)
result["log2FC_raw"] = np.log2((result["mean_WS"] + 0.01) / (result["mean_CTRL"] + 0.01))
result["abs_log2FC"] = result["log2FC_raw"].abs()
result = result.sort_values("abs_log2FC", ascending=False)

print(f"\n=== Per-Cell Wilcoxon DE: 7q11.23 Interval Genes ===")
print(f"(Negative log2FC = lower in WS = consistent with deletion)")
print()
cols = ["gene", "log2FC_raw", "pvals_adj", "mean_WS", "mean_CTRL", "ratio_WS_CTRL", "pct_WS", "pct_CTRL"]
for _, r in result.iterrows():
    print(f"{r['gene']:12s}  log2FC={r['log2FC_raw']:+.4f}  adj.p={r['pvals_adj']:.4f}  "
          f"mean WS={r['mean_WS']:.4f} CTRL={r['mean_CTRL']:.4f}  "
          f"ratio={r['ratio_WS_CTRL']:.3f}  "
          f"pct WS={r['pct_WS']:.1%} CTRL={r['pct_CTRL']:.1%}")

# Focus on GTF2I
gtf2i = result[result["gene"] == "GTF2I"].iloc[0]
print(f"\n>>> GTF2I specifically (per-cell Wilcoxon):")
print(f"    log2FC = {gtf2i['log2FC_raw']:+.4f}")
print(f"    adjusted p-value = {gtf2i['pvals_adj']:.6f}")
print(f"    mean counts WS = {gtf2i['mean_WS']:.2f}, CTRL = {gtf2i['mean_CTRL']:.2f}")
print(f"    ratio WS/CTRL = {gtf2i['ratio_WS_CTRL']:.4f}")
print(f"    var WS = {gtf2i['var_WS']:.2f}, var CTRL = {gtf2i['var_CTRL']:.2f}")

# Variance test
print(f"\n=== Variance Analysis ===")
print(f"Genes with high expression (>0.1 mean in CTRL):")
high_expr = result[result["mean_CTRL"] > 0.1].copy()
high_expr["var_ratio"] = high_expr["var_WS"] / high_expr["var_CTRL"]
print(f"{'gene':12s}  {'var_WS':>8s}  {'var_CTRL':>8s}  {'var_ratio':>8s}  {'ratio_WS/CTRL':>10s}")
for _, r in high_expr.iterrows():
    print(f"{r['gene']:12s}  {r['var_WS']:8.2f}  {r['var_CTRL']:8.2f}  {r['var_ratio']:8.3f}  {r['ratio_WS_CTRL']:10.4f}")

print(f"\n=== Key conclusion ===")
gtf2i_fc = gtf2i['log2FC_raw']
gtf2i_ratio = gtf2i['ratio_WS_CTRL']
print(f"GTF2I ratio WS/CTRL = {gtf2i_ratio:.4f}")
print(f"A naive expectation for hemizygous deletion (1 copy vs 2): ratio ≈ 0.50")
print(f"Observed: ratio ≈ {gtf2i_ratio:.2f}")
if gtf2i_ratio > 0.95:
    print("→ GTF2I expression is essentially IDENTICAL in patient and control cells.")
    print("  The mRNA level shows NO evidence of haploinsufficiency.")
    print("  This is consistent with transcriptional dosage compensation.")
else:
    print(f"→ GTF2I shows a {(1-gtf2i_ratio)*100:.0f}% reduction in patients.")
