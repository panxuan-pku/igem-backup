import os
from pathlib import Path
import numpy as np
import scanpy as sc
import celloracle as co
from celloracle import Oracle
from celloracle.data.load_promoter_base_GRN import load_human_promoter_base_GRN
from scipy.stats import spearmanr

BASE = Path(__file__).resolve().parent

# ---------- 1. 数据 ----------
adata = sc.read_h5ad(os.path.join(BASE, "processed.h5ad"))
print("adata:", adata.shape)

def get_gene_vec(adata, gene):
    i = list(adata.var_names).index(gene)
    x = adata.X[:, i]
    return np.asarray(x.todense()).ravel() if hasattr(x, "todense") else np.asarray(x).ravel()

# TBX1 表达 sanity check
if "TBX1" in adata.var_names:
    x = get_gene_vec(adata, "TBX1")
    print(f"TBX1 表达: 细胞数 {(x>0).sum()}/{len(x)} | 均值 {x.mean():.4f}")

# ---------- 2. Oracle 导入 ----------
oracle = Oracle()
oracle.import_anndata_as_raw_count(adata=adata, cluster_column_name="cluster", embedding_name="X_umap")

# ---------- 3. base GRN ----------
base_GRN = load_human_promoter_base_GRN(version="hg38_gimmemotifsv5_fpr2")
oracle.import_TF_data(TF_info_matrix=base_GRN)
print("TFdict 大小:", len(oracle.TFdict))
print("TBX1 的靶基因数(全库):", len(oracle.TFdict.get("TBX1", [])))
print("TBX1 在 regulator:", "TBX1" in oracle.TFdict)

# ---------- 4. PCA + imputation ----------
oracle.perform_PCA()
oracle.knn_imputation(n_pca_dims=10, k=10, balanced=False, n_jobs=4)
print("imputation 完成")

# ---------- 5. fit GRN ----------
oracle.fit_GRN_for_simulation(alpha=10, GRN_unit="cluster", verbose_level=1)
print("fit_GRN 完成")

# ---------- 6. 模拟 ----------
# 原始 imputed 数据（模拟起点）
orig = np.asarray(oracle.adata.layers["imputed_count"].todense()) if hasattr(oracle.adata.layers["imputed_count"], "todense") else np.asarray(oracle.adata.layers["imputed_count"])

# KO（敲低 TBX1 到 0）
oracle.simulate_shift(perturb_condition={"TBX1": 0.0}, GRN_unit="cluster", n_propagation=3)
sim_ko = np.asarray(oracle.adata.layers["simulated_count"].todense()) if hasattr(oracle.adata.layers["simulated_count"], "todense") else np.asarray(oracle.adata.layers["simulated_count"])
shift_ko = sim_ko.mean(0) - orig.mean(0)

# OE（过表达 TBX1，剂量补偿）
oracle.simulate_shift(perturb_condition={"TBX1": 10.0}, GRN_unit="cluster", n_propagation=3)
sim_oe = np.asarray(oracle.adata.layers["simulated_count"].todense()) if hasattr(oracle.adata.layers["simulated_count"], "todense") else np.asarray(oracle.adata.layers["simulated_count"])
shift_oe = sim_oe.mean(0) - orig.mean(0)

# ---------- 7. 真实疾病 DE（case vs ctrl，log 归一化）----------
raw = adata.copy()
sc.pp.normalize_total(raw, target_sum=1e4)
sc.pp.log1p(raw)
ctrl = raw[raw.obs["condition"] == "ctrl"].X
case = raw[raw.obs["condition"] == "case"].X
ctrl_mean = np.asarray(ctrl.mean(0)).ravel()
case_mean = np.asarray(case.mean(0)).ravel()
real_de = case_mean - ctrl_mean   # 患者 vs 对照

genes = list(adata.var_names)

# ---------- 8. 对比 ----------
def report(name, shift, real_de):
    r, p = spearmanr(shift, real_de)
    # 只统计有变化的基因（shift != 0）
    mask = np.abs(shift) > 1e-8
    r2, p2 = spearmanr(shift[mask], real_de[mask])
    top_ko = set(np.argsort(-np.abs(shift))[:50])
    top_de = set(np.argsort(-np.abs(real_de))[:50])
    jacc = len(top_ko & top_de) / len(top_ko | top_de)
    print(f"[{name}] Spearman(shift, 真实DE) r={r:+.4f} (p={p:.2g}), 非零基因 r={r2:+.4f}, top50 Jaccard={jacc:.3f}")
    return r

print("\n===== 预测 vs 真实疾病 DE 对比 =====")
r_ko = report("TBX1 KO (模拟敲低)", shift_ko, real_de)
r_oe = report("TBX1 OE (模拟剂量补偿)", shift_oe, real_de)

# 期望：KO 应正相关（敲低 → 复现疾病）、OE 应负相关（过表达 → 逆转疾病）
print("\n期望: KO 与疾病DE正相关(复现疾病)、OE 负相关(逆转疾病)")

# 保存
np.savez(os.path.join(BASE, "results.npz"), shift_ko=shift_ko, shift_oe=shift_oe, real_de=real_de, genes=np.array(genes))
print("已保存 results.npz")
