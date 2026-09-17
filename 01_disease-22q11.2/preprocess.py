import scanpy as sc
import numpy as np
import os
from pathlib import Path

sc.settings.verbosity = 1
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

# 22q11.2 区段基因（强制保留，避免 HVG 筛掉）
FORCE = ["TBX1","COMT","DGCR8","PRODH","HIRA","UFD1L","SEPT5","CLTCL1","RTN4R","GNB1L",
         "DGCR6","DGCR2","TSSK2","GSC2","SLC25A1","CLDN5","GP1BB","TXNRD2","ARVCF","RANBP1"]

def read_sample(tag):
    ad = sc.read_10x_mtx(os.path.join(DATA, tag), var_names="gene_symbols", cache=False)
    ad.var_names_make_unique()
    return ad

print("读取矩阵 ...")
ctrl = read_sample("JS001/cellranger_analysis_outs/filtered_feature_bc_matrix")
case = read_sample("JS002/cellranger_analysis_outs/filtered_feature_bc_matrix")
ctrl.obs["condition"] = "ctrl"
case.obs["condition"] = "case"
print(f"ctrl {ctrl.shape} / case {case.shape}")

adata = ctrl.concatenate(case, batch_key="batch", join="outer")
adata.var_names_make_unique()
print("合并后:", adata.shape)

# QC
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)
print("QC 后:", adata.shape)

# 保留原始 counts（CellOracle 需要 raw counts 在 X；X 本来就还是 raw counts）
adata.layers["counts"] = adata.X.copy()

# 归一化拷贝做聚类
adata_clust = adata.copy()
sc.pp.normalize_total(adata_clust, target_sum=1e4)
sc.pp.log1p(adata_clust)
sc.pp.highly_variable_genes(adata_clust, n_top_genes=3000, flavor="seurat")
sc.pp.pca(adata_clust, n_comps=30)
sc.pp.neighbors(adata_clust, n_neighbors=15, n_pcs=30)
sc.tl.umap(adata_clust)
sc.tl.leiden(adata_clust, resolution=0.8)

# 把聚类 + UMAP 传回 raw adata
adata.obsm["X_umap"] = adata_clust.obsm["X_umap"].copy()
adata.obs["cluster"] = adata_clust.obs["leiden"].astype(str).values
print("cluster 分布:", dict(adata.obs["cluster"].value_counts()))

# HVG 子集 + 强制基因
hvgs = set(adata_clust.var_names[adata_clust.var.highly_variable])
keep = [g for g in adata.var_names if (g in hvgs) or (g in FORCE)]
forced_kept = [g for g in FORCE if g in keep and g not in hvgs]
print(f"子集基因数: {len(keep)}（HVG {len(hvgs)} + 强制 {len(forced_kept)}: {forced_kept}）")
print("TBX1 在子集:", "TBX1" in keep, "| TBX1 原本是 HVG:", "TBX1" in hvgs)
adata = adata[:, keep]   # X 自动变为 raw counts 子集

out = BASE / "processed.h5ad"
adata.write(out)
print("已保存:", out, adata.shape)
