"""M1+M2: 数据管线 — PBMC 3k → SCimilarity embedding → UMAP
产物: data/embeddings.npy, data/expr_aligned.npz, data/meta.csv, data/umap.npy, data/pbmc3k_raw.h5ad

这是千兆级工具链的第一步。数据预处理通常只需跑一次，
之后的 web demo 和验证脚本都从 data/ 读取。
"""
import os, sys, time
import numpy as np
import pandas as pd
import scanpy as sc
import scipy.sparse as sp
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from paths import SIG_DIR, MODEL_DIR, DATA_DIR

sys.path.insert(0, os.path.join(SIG_DIR, "src"))
from SIGnature.models.scimilarity import SCimilarityWrapper
from SIGnature.utils import align_dataset, lognorm_counts

os.makedirs(DATA_DIR, exist_ok=True)

# ── 1. 获取 PBMC 3k ──
print("1/5 下载 PBMC 3k 数据集 ...")
adata = sc.datasets.pbmc3k()
print(f"   细胞 {adata.n_obs}, 基因 {adata.n_vars}")

# 保存原始数据供后续使用
raw_path = os.path.join(DATA_DIR, "pbmc3k_raw.h5ad")
adata.write(raw_path)
print(f"   保存: {raw_path}")

# ── 2. 对齐到 SCimilarity 28231 基因空间 ──
print("2/5 对齐 SCimilarity 基因空间 ...")
wrapper = SCimilarityWrapper(model_path=MODEL_DIR)
overlap = int(sum(adata.var_names.isin(wrapper.gene_order)))
print(f"   基因重合: {overlap}/{len(adata.var_names)}")
adata = align_dataset(adata, wrapper.gene_order, gene_overlap_threshold=500)
adata.layers["counts"] = adata.X.copy()
lognorm_counts(adata)
X = adata.X if sp.issparse(adata.X) else sp.csr_matrix(adata.X)
print(f"   aligned: {adata.n_obs} x {adata.n_vars}")

# ── 3. 计算 SCimilarity embedding ──
print("3/5 计算 embedding (128 维) ...")
model = wrapper.model.eval()
embs = []
t0 = time.time()
with torch.no_grad():
    for i in range(0, X.shape[0], 512):
        xb = X[i:i + 512].toarray().astype(np.float32)
        embs.append(model(torch.tensor(xb)).numpy())
emb = np.vstack(embs)
print(f"   {emb.shape} ({time.time() - t0:.0f}s)")

# ── 4. 导出并计算 UMAP ──
print("4/5 导出数据 + UMAP ...")
# 稀疏格式落盘，节省空间
sp.save_npz(os.path.join(DATA_DIR, "expr_aligned.npz"), X)
np.save(os.path.join(DATA_DIR, "embeddings.npy"), emb)

# metadata（细胞类型标签等等）
meta = pd.DataFrame({
    "cell_type": adata.obs["louvain"].astype(str).tolist(),
    "barcode": adata.obs_names.tolist(),
})
meta.to_csv(os.path.join(DATA_DIR, "meta.csv"), index=False)

# UMAP（n_neighbors=15 适合 PBMC 3k 的 2700 细胞规模）
import umap
reducer = umap.UMAP(n_neighbors=15, min_dist=0.5, random_state=42).fit(emb)
umap_coords = reducer.embedding_
np.save(os.path.join(DATA_DIR, "umap.npy"), umap_coords)
print(f"   UMAP: {umap_coords.shape}")

# ── 5. Sanity check ──
print("5/5 验证 ...")
import json
centroids = {}
for ct in meta.cell_type.unique():
    mask = (meta.cell_type == ct).values
    centroids[ct] = emb[mask].mean(axis=0).tolist()
print(f"   细胞类型: {list(centroids.keys())}")

validation = {
    "n_cells": int(adata.n_obs),
    "n_genes": int(adata.n_vars),
    "embedding_dim": int(emb.shape[1]),
    "cell_types": list(centroids.keys()),
}
json.dump(validation, open(os.path.join(DATA_DIR, "pbmc_info.json"), "w"), indent=2, ensure_ascii=False)
print("✅ 数据管线完成，产物:")
for f in ["embeddings.npy", "expr_aligned.npz", "meta.csv", "umap.npy", "pbmc3k_raw.h5ad"]:
    p = os.path.join(DATA_DIR, f)
    if os.path.exists(p):
        size_mb = os.path.getsize(p) / 1e6
        print(f"   data/{f} ({size_mb:.1f} MB)")
    else:
        print(f"   ⚠️ data/{f} 不存在！")