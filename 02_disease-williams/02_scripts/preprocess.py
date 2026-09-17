import scanpy as sc
import numpy as np
import os
from pathlib import Path

sc.settings.verbosity = 1
BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "01_rawdata"

# Williams 7q11.23 区段基因（强制保留，重点 GTF2I）
FORCE = ["GTF2I","GTF2IRD1","GTF2IRD2","ELN","LIMK1","BAZ1B","CLIP2","STX1A","CLDN3","CLDN4",
         "TBL2","WBSCR22","WBSCR27","WBSCR28","RFC2","FZD9","LAT2","EIF4H","MLXIPL","NCF1"]

samples = {"CTRL": ["CTRL1","CTRL2","CTRL3"], "WS": ["WS1","WS2","WS3"]}

adatas = []
for cond, names in samples.items():
    for n in names:
        ad = sc.read_10x_mtx(os.path.join(DATA, n), var_names="gene_symbols", cache=False)
        ad.var_names_make_unique()
        ad.obs["condition"] = cond
        ad.obs["sample"] = n
        adatas.append(ad)
        print(f"{n} ({cond}): {ad.shape}")

adata = adatas[0].concatenate(adatas[1:], batch_key="sample", join="outer")
adata.var_names_make_unique()
print("合并:", adata.shape)

sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)
print("QC 后:", adata.shape)
adata.layers["counts"] = adata.X.copy()

adata_clust = adata.copy()
sc.pp.normalize_total(adata_clust, target_sum=1e4)
sc.pp.log1p(adata_clust)
sc.pp.highly_variable_genes(adata_clust, n_top_genes=3000, flavor="seurat")
sc.pp.pca(adata_clust, n_comps=30)
sc.pp.neighbors(adata_clust, n_neighbors=15, n_pcs=30)
sc.tl.umap(adata_clust)
sc.tl.leiden(adata_clust, resolution=0.8)

adata.obsm["X_umap"] = adata_clust.obsm["X_umap"].copy()
adata.obs["cluster"] = adata_clust.obs["leiden"].astype(str).values
print("cluster 分布:", dict(adata.obs["cluster"].value_counts()))

hvgs = set(adata_clust.var_names[adata_clust.var.highly_variable])
keep = [g for g in adata.var_names if (g in hvgs) or (g in FORCE)]
forced = [g for g in FORCE if g in keep and g not in hvgs]
print(f"子集 {len(keep)} 基因（HVG {len(hvgs)} + 强制 {len(forced)}: {forced}）")
print("GTF2I 在子集:", "GTF2I" in keep, "| GTF2I 是 HVG:", "GTF2I" in hvgs)
adata = adata[:, keep]

# GTF2I 表达 sanity check（最关键，避免 TBX1 的坑）
raw = adata.copy(); sc.pp.normalize_total(raw, target_sum=1e4); sc.pp.log1p(raw)
for g in ["GTF2I","GTF2IRD1","ELN","LIMK1","BAZ1B","CLIP2"]:
    if g in raw.var_names:
        i = list(raw.var_names).index(g)
        x = np.asarray(raw.X[:, i].todense()).ravel() if hasattr(raw.X[:, i], "todense") else np.asarray(raw.X[:, i]).ravel()
        print(f"  {g:10s} 表达 {(x>0).sum()}/{len(x)} 细胞, 均值 {x.mean():.3f}")

adata.write(BASE / "03_intermediate" / "processed.h5ad")
print("已保存 processed.h5ad", adata.shape)
