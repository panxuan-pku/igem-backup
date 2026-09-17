import os
from pathlib import Path
import numpy as np
import scanpy as sc
from celloracle import Oracle
from celloracle.data.load_promoter_base_GRN import load_human_promoter_base_GRN
from scipy.stats import spearmanr

BASE = Path(__file__).resolve().parents[1]

adata = sc.read_h5ad(os.path.join(BASE, "03_intermediate/processed.h5ad"))
print("adata:", adata.shape, "| GTF2I 在 var:", "GTF2I" in adata.var_names)

oracle = Oracle()
oracle.import_anndata_as_raw_count(adata=adata, cluster_column_name="cluster", embedding_name="X_umap")

base_GRN = load_human_promoter_base_GRN(version="hg38_gimmemotifsv5_fpr2")
oracle.import_TF_data(TF_info_matrix=base_GRN)
print("GTF2I 是 regulator:", "GTF2I" in oracle.TFdict, "| 靶基因数(全库):", len(oracle.TFdict.get("GTF2I", [])))

oracle.perform_PCA()
oracle.knn_imputation(n_pca_dims=10, k=10, balanced=False, n_jobs=4)
print("imputation 完成")

oracle.fit_GRN_for_simulation(alpha=10, GRN_unit="cluster", verbose_level=1)
print("fit_GRN 完成")

# 原始 imputed 数据
orig = np.asarray(oracle.adata.layers["imputed_count"].todense()) if hasattr(oracle.adata.layers["imputed_count"], "todense") else np.asarray(oracle.adata.layers["imputed_count"])
gtf2i_idx = list(adata.var_names).index("GTF2I")
gtf2i_mean = orig[:, gtf2i_idx].mean()
print(f"GTF2I imputed 均值: {gtf2i_mean:.3f}")

# KO（敲低到 0）
oracle.simulate_shift(perturb_condition={"GTF2I": 0.0}, GRN_unit="cluster", n_propagation=3)
sim_ko = np.asarray(oracle.adata.layers["simulated_count"].todense()) if hasattr(oracle.adata.layers["simulated_count"], "todense") else np.asarray(oracle.adata.layers["simulated_count"])
shift_ko = sim_ko.mean(0) - orig.mean(0)

# OE（过表达 2x，模拟剂量补偿）
oe_val = float(gtf2i_mean * 2)
print(f"OE 目标值: {oe_val:.3f}")
oracle.simulate_shift(perturb_condition={"GTF2I": oe_val}, GRN_unit="cluster", n_propagation=3)
sim_oe = np.asarray(oracle.adata.layers["simulated_count"].todense()) if hasattr(oracle.adata.layers["simulated_count"], "todense") else np.asarray(oracle.adata.layers["simulated_count"])
shift_oe = sim_oe.mean(0) - orig.mean(0)

# 真实疾病 DE（WS vs CTRL）
raw = adata.copy()
sc.pp.normalize_total(raw, target_sum=1e4)
sc.pp.log1p(raw)
ctrl = np.asarray(raw[raw.obs["condition"] == "CTRL"].X.mean(0)).ravel()
ws = np.asarray(raw[raw.obs["condition"] == "WS"].X.mean(0)).ravel()
real_de = ws - ctrl   # 患者 vs 对照

genes = list(adata.var_names)

def report(name, shift, real_de):
    r, p = spearmanr(shift, real_de)
    mask = np.abs(shift) > 1e-8
    r2, p2 = spearmanr(shift[mask], real_de[mask])
    print(f"[{name}] Spearman(shift, 真实DE) r={r:+.4f} (p={p:.2g}), 非零基因 r={r2:+.4f}")
    return r

print("\n===== 预测 vs 真实 WS 疾病 DE 对比 =====")
print("期望: KO 与疾病DE正相关(敲低复现疾病)、OE 负相关(过表达逆转疾病=回到健康)")
r_ko = report("GTF2I KO (敲低→0)", shift_ko, real_de)
r_oe = report("GTF2I OE (过表达2x→剂量补偿)", shift_oe, real_de)

# 输出 OE 后"被拉回健康方向"最明显的 top 基因
print("\nOE 位移与疾病 DE 相反(即被恢复)最明显的 top 20 基因:")
restored = -shift_oe * real_de   # 正值 = OE 朝健康方向
order = np.argsort(-restored)
for i in order[:20]:
    print(f"  {genes[i]:12s} OE位移={shift_oe[i]:+.4f} 疾病DE={real_de[i]:+.4f}")

np.savez(os.path.join(BASE, "04_results/results.npz"), shift_ko=shift_ko, shift_oe=shift_oe, real_de=real_de, genes=np.array(genes))
print("\n已保存 results.npz")
