import os, sys
from pathlib import Path
import numpy as np
import scanpy as sc
import torch

BASE = Path(__file__).resolve().parents[1]
SIG_DIR = BASE.parent / "05_tools" / "SIGnature"
sys.path.insert(0, os.path.join(SIG_DIR, "src"))
from SIGnature.models.scimilarity import SCimilarityWrapper
from captum.attr import IntegratedGradients

DATA = BASE / "01_rawdata"
rng = np.random.default_rng(0)

# 1. 载入 Williams 6 样本（原始 counts，全基因空间）
adatas = []
for cond, names in [("CTRL", ["CTRL1","CTRL2","CTRL3"]), ("WS", ["WS1","WS2","WS3"])]:
    for n in names:
        ad = sc.read_10x_mtx(f"{DATA}/{n}", var_names="gene_symbols", cache=False)
        ad.var_names_make_unique()
        ad.obs["condition"] = cond
        adatas.append(ad)
adata = adatas[0].concatenate(adatas[1:], batch_key="sample", join="outer")
adata.var_names_make_unique()
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)
print("原始合并:", adata.shape)

# 2. 子采样（5000 ctrl + 5000 WS）
n = 5000
ci = np.where(adata.obs["condition"].values == "CTRL")[0]
wi = np.where(adata.obs["condition"].values == "WS")[0]
sub = np.concatenate([rng.choice(ci, n, replace=False), rng.choice(wi, n, replace=False)])
adata = adata[sub].copy()
print("子采样:", adata.shape)

# 3. SCimilarity 基因空间对齐 + lognorm
wrapper = SCimilarityWrapper(model_path=os.path.join(SIG_DIR, "model_files/model_files/scimilarity"))
wrapper.model.eval()
gidx = {g: i for i, g in enumerate(wrapper.gene_order)}
map_ = [gidx[g] if g in gidx else -1 for g in adata.var_names]
print(f"基因映射: {sum(1 for m in map_ if m>=0)}/{len(map_)} 在 SCimilarity 28231 空间")
for g in ["GTF2I","GTF2IRD1","BAZ1B","ELN","LIMK1","CLIP2","STX1A"]:
    print(f"  删失基因 {g} 在 SCimilarity 空间: {g in gidx}")

Xraw = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
lib = Xraw.sum(1, keepdims=True) + 1e-9
Xn = np.log1p(Xraw / lib * 1e4)  # lognorm
Xscim = np.zeros((Xn.shape[0], len(wrapper.gene_order)), dtype=np.float32)
for j, m in enumerate(map_):
    if m >= 0:
        Xscim[:, m] = Xn[:, j]
del Xraw, Xn

# 4. IG 归因（分批）
ig = IntegratedGradients(lambda x: wrapper.model(x).sum(dim=1))
def attr_batch(xs):
    t = torch.tensor(xs, dtype=torch.float32, requires_grad=True)
    return ig.attribute(t, baselines=torch.zeros_like(t), n_steps=16).detach().numpy()

attr = []
BS = 1000
for i in range(0, Xscim.shape[0], BS):
    attr.append(attr_batch(Xscim[i:i+BS]))
attr = np.vstack(attr)
print("归因矩阵:", attr.shape)

# 5. 差异归因（WS - CTRL）
ctrl_attr = attr[:n].mean(0)
ws_attr = attr[n:].mean(0)
dattr = ws_attr - ctrl_attr
genes = np.array(wrapper.gene_order)

# 真实差异表达（WS vs CTRL）作为对照
de = adata.obs["condition"].values == "WS"
ctrl_X = Xscim[:n].mean(0) if False else None
# 用 lognorm 表达算 DE
raw = adata.copy()
sc.pp.normalize_total(raw, target_sum=1e4)
sc.pp.log1p(raw)
ctrl_expr = np.asarray(raw[raw.obs["condition"]=="CTRL"].X.mean(0)).ravel()
ws_expr = np.asarray(raw[raw.obs["condition"]=="WS"].X.mean(0)).ravel()
real_de_5045 = ws_expr - ctrl_expr
# 映射到 28231 空间（按基因符号对齐）
de_full = np.zeros(len(genes), dtype=np.float64)
for j, g in enumerate(adata.var_names):
    m = map_[j]
    if m >= 0:
        de_full[m] = real_de_5045[j]

# 6. 报告
print("\n===== 差异归因（WS vs CTRL）：|Δattr| 最大的 top 20 基因 =====")
order = np.argsort(-np.abs(dattr))
for i in order[:20]:
    tag = " ★删失基因" if genes[i] in ["GTF2I","GTF2IRD1","BAZ1B","ELN","LIMK1","CLIP2","STX1A"] else ""
    print(f"  {genes[i]:12s} Δattr={dattr[i]:+.4f} | DE={de_full[i]:+.3f}{tag}")

print("\n===== 删失基因本身的归因变化 =====")
for g in ["GTF2I","GTF2IRD1","BAZ1B","ELN","LIMK1","CLIP2","STX1A"]:
    if g in gidx:
        k = gidx[g]
        print(f"  {g:10s} Δattr={dattr[k]:+.4f}  ctrl_attr={ctrl_attr[k]:+.4f}  ws_attr={ws_attr[k]:+.4f}  DE={de_full[k]:+.3f}")

# 7. 差异归因 vs 差异表达 的相关性（诚实 caveat：归因是否只是 DE 的代理）
from scipy.stats import spearmanr
valid = ~np.isnan(dattr)
r_abs, p_abs = spearmanr(np.abs(dattr[valid]), np.abs(de_full[valid]))
r_signed, p_signed = spearmanr(dattr[valid], de_full[valid])
print(f"\n差异归因 vs 差异表达: |Δattr| vs |DE| r={r_abs:+.3f} (p={p_abs:.2g}), 带符号 r={r_signed:+.3f} (p={p_signed:.2g})")

np.savez(BASE / "04_results" / "attribution_results.npz",
         dattr=dattr, de_full=de_full, genes=genes)
print("\n已保存 attribution_results.npz")
