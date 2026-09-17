# SIGnature 项目上下文（供 AI Agent 阅读）

> 本文件为 coding agent（GitHub Copilot / Codespace agent 等）提供项目背景、已有框架结构与改进方向。
> 论文：*Scoring gene importance by interpreting single-cell foundation models*（Nature Biotechnology, 2026）
> 上游仓库：https://github.com/Genentech/SIGnature ｜ 文档：https://genentech.github.io/SIGnature/index.html

---

## 1. 项目背景

### 1.1 要解决的科学问题

单细胞 RNA 测序（scRNA-seq）中，**基因的绝对表达量 ≠ 功能重要性**：

- 关键调控基因（如转录因子 FOXP3、GATA3、RORC）表达量低，容易被 dropout 丢失；
- 高表达基因（线粒体基因、核糖体基因、MALAT1）对细胞特异功能贡献有限；
- 传统方法（DESeq2、GSEA、GSVA、Scanpy/Seurat 的 score_genes）都是**数据集内相对比较**，换数据集后背景分布、测序深度、批次效应不同，分数无法跨研究比较；
- 公共库已有数千个 scRNA-seq 实验，逐一做标准化整合不现实。

**核心需求**：一把"标准化尺子"，能跨数据集客观衡量"某个基因对某个细胞有多重要"。

### 1.2 核心思想

把可解释 AI（XAI）的**归因方法（attribution）**应用到单细胞**基础模型（foundation model, FM）**上：

- 类比图像分类：归因高亮的像素 = 模型判断"这是狗"最依赖的像素；
- 在 scRNA-seq FM 中，每个基因的 attribution = 该基因对细胞在 latent space 中位置的贡献；
- 因为所有细胞都与**同一个标准化 FM 嵌入**比较，attribution 天然支持跨数据集分析；
- attribution 可对超大图谱**预计算**，之后查询一个基因集只是简单数学运算：22M 细胞几分钟出结果（传统方法需数小时~数天）。

### 1.3 关键验证结果（论文结论）

1. **生物学意义更强**：B 细胞 attribution 最高的基因是 BANK1/CD79A/MS4A1（已知标志物），而表达量最高的是 MALAT1/线粒体/核糖体基因；低表达转录因子在对应细胞亚型中 attribution 排名显著高于表达排名。
2. **抗技术噪音**：与 UMI 测序深度几乎不相关（ρ=-0.12，表达量 ρ=0.71）；模拟 50% dropout 后 top 基因 93% 重叠。
3. **跨研究 NMF**：多数据集 attribution 矩阵拼接做 NMF，得到的基因程序更少批次效应、更接近有监督 scETM 的效果，但**无需重新训练**。
4. **基因集打分 SOTA**：与 ANS、JASMINE、UCell、Scanpy、Mean Expression 对比，32 项测试赢 23 项；Scanpy 曾把 CD4+ T 细胞误判得比真 CD8+ 更高分，attribution 打分正确。
5. **大规模发现 + 实验验证闭环**：用 MS1 基因程序（~100 基因，脓毒症/重症 COVID 相关单核细胞状态）查询 412 个疾病研究、2200 万细胞，新发现**川崎病（KD）、SFTS、HLH** 三种高炎症疾病存在 MS1 激活；并用 KD 患者血清体外诱导 MS1 表型做了实验验证。

### 1.4 已承认的局限

- attribution 质量受限于 FM 对特定细胞类型的表征能力（眼部数据提升不明显）；
- Integrated Gradients 计算最慢；
- 归因 ≠ 因果，下游假设需实验验证。

---

## 2. 已有框架（代码结构与技术栈）

### 2.1 仓库结构（上游 Genentech/SIGnature）

```
SIGnature/
├── src/SIGnature/
│   ├── __init__.py          # 导出 SIGnature, Meta 两个主类
│   ├── SIGnature.py         # 核心类：attribution 存储/查询（TileDB 后端）
│   ├── meta.py              # Meta 类：细胞 metadata 管理、打分、hit 判定
│   ├── utils.py             # 数据对齐、log 归一化、TileDB 写入、矩阵处理
│   └── models/
│       ├── scimilarity.py   # SCimilarity 包装（论文主用模型，MLP 编码器）
│       ├── scfoundation.py  # scFoundation 包装（transformer）
│       ├── scvi.py          # scVI 包装（CZI Census 预训练）
│       └── ssl.py           # SSL-scTab 自监督模型包装
├── docs/notebooks/          # 三个官方教程（见 2.3）
├── docker/                  # Docker 环境
└── pyproject.toml / setup.py
```

### 2.2 核心 API

**`SIGnature` 类**（`SIGnature.py`）——attribution 的生成与查询：
- `__init__(gene_order, attribution_tiledb_uri=None)`：固定基因顺序 + 可选 TileDB 存储
- `check_genes(gene_list)`：检查基因集与模型输入空间的重合
- `create_tiledb(npz_path, batch_size=25000)`：把预计算 attribution 写入 TileDB
- `query_attributions(gene_list, cell_indices=None)`：按基因集查询细胞级分数

**`Meta` 类**（`meta.py`）——metadata 与打分：
- `add_scores(score_dict, mode="value")`、`add_hits(...)`（top% 判定 hit 细胞）、`cat_by_min(...)`

**模型包装层**（`models/*.py`）：统一接口，基于 **Captum** 实现三种归因算法：
- `ig` = IntegratedGradients（论文主用，慢但稳）
- `dl` = DeepLift
- `ixg` = Input×Gradient（Saliency）
- 实现细节：在预训练网络后加**求和层**，把多维嵌入输出适配到标量归因。

### 2.3 三条标准工作流（官方 notebooks）

1. **QueryingAttributions**：加载 Zenodo 预计算 attribution → 查询基因集 → 细胞级打分 → 疾病/细胞类型富集分析（最快路径，分钟级）。
2. **GeneratingAttributions**：对自己的 scRNA-seq 数据计算 attribution：`align_dataset`（对齐基因序）→ `lognorm_counts` → 选模型 wrapper → Captum 归因 → 存 npz/TileDB。
3. **IntegratingAttributions**：多数据集 attribution 拼接 → NMF → 跨研究基因程序发现。

### 2.4 支持的预训练模型与权重来源

| 模型 | 架构 | 权重 |
|---|---|---|
| **SCimilarity**（默认推荐） | MLP 编码器，23M 细胞训练 | Zenodo 17903196（含在 helper files） |
| scFoundation | Transformer | huggingface.co/genbio-ai/scFoundation |
| scVI | VAE | cellxgene.cziscience.com/census-models |
| SSL-scTab | 自监督 MLP | huggingface.co/TillR/sc_pretrained |

### 2.5 外部资源

- 预计算 attribution（22M 细胞 / 412 研究）：https://zenodo.org/communities/signature/
- 生成新 attribution 所需 helper files：https://zenodo.org/records/17903196
- 安装：`pip install sc-signature`（发布版）或 `pip install -e .`（开发版）
- 关键依赖：Captum、TileDB、scanpy/anndata、PyTorch、scikit-learn

### 2.6 选模型/方法的经验法则（来自论文 benchmark）

- 要快：MLP 类模型（SCimilarity）远快于 transformer（scGPT/scFoundation）；
- 三种归因方法中 IG 最慢但质量稳定，IxG 最快；
- 含细胞类型标签训练的模型（SCimilarity、微调 SSL-scTab）对 marker 基因提升最强；
- 眼部等 FM 训练数据覆盖不足的组织，attribution 提升有限——**换组织前先做小规模 sanity check**。

---

## 3. 利用与改良建议（给 Agent 的工作方向）

> 按"直接可用 → 轻度改造 → 深度扩展"分层。每条注明改动位置与预期收益。

### 3.1 直接可用（无需改代码）

1. **查询自己的基因 signature**：用工作流 1（QueryingAttributions），把自己课题相关的基因集（如工程菌靶点、通路 marker、疾病 signature）在 22M 细胞预计算 attribution 里查询，得到细胞类型/疾病富集结果。适合作为 iGEM 项目的"人类相关性验证"环节。
2. **对自己的数据算 attribution**：工作流 2，输入 h5ad → 得到每个细胞×每个基因的重要性矩阵 → 用 `Meta.add_scores/add_hits` 找高激活细胞群。
3. **复现论文 MS1 分析**：用 MS1 ~100 基因列表（Reyes et al. 2021）查询，验证管线端到端跑通，作为新 signature 查询的模板。

### 3.2 轻度改造（改配置/小代码）

4. **接入新的基础模型**：仿照 `models/scimilarity.py` 的 `SCimilarityWrapper` 写新 wrapper（如 Geneformer、scBERT、UCE）。要求：固定基因输入 + 细胞级嵌入；最后加求和层即可复用 Captum 归因管线。注意 transformer 模型显存开销大，需减小 batch。
5. **更换/新增归因算法**：Captum 还提供 GradientShap、DeepLiftShap、FeatureAblation。在 wrapper 的 `attribute()` 方法里加新分支即可，用论文 Fig.2 的 5 项指标（计算时间/UMI 相关/核糖体 rank/G2M fold-change/marker rank）做对比。
6. **调整 hit 阈值与打分聚合**：论文默认 top 10% 为 hit；`Meta.add_hits` 支持改阈值，建议做 5%/10%/15%/20% 敏感性分析（论文 Extended Data Fig. 9b 同款验证）。
7. **空间转录组扩展**：论文已在模拟 Visium spot 上验证（spot 内细胞比例与 attribution 强度相关）。可将真实空间数据聚合成 spot 后走同一管线。

### 3.3 深度扩展（新模块）

8. **跨研究 NMF 基因程序发现 pipeline 产品化**：把"多数据集 attribution 拼接 → cNMF → factor 与细胞类型/批次关联检验"封装成 CLI 或 snakemake 流程，输出标准化报告。
9. **扰动响应预测**：attribution 反映"改变该基因表达会如何移动细胞嵌入"，可与 Perturb-seq 数据对照，验证高 attribution 基因是否真的是有效扰动靶点（连接归因与因果）。
10. **多组学/多模态**：scFoundation、scGPT 支持更多模态；可探索 ATAC-seq 或蛋白组特征归因（需新 wrapper + 输入对齐）。
11. **iGEM 干湿结合闭环**：计算端用 SIGnature 筛选"在某细胞状态下最重要的基因/通路"→ 实验端设计合成生物学干预（如报告基因、启动子模块）→ 用 flow/qPCR 验证。论文的"MS1 → 川崎病 → 血清诱导实验"就是标准叙事模板。

### 3.4 注意事项（Agent 执行时）

- attribution 与 FM 强绑定：换模型后所有预计算结果不可混用，查询前确认 `gene_order` 与模型输入一致；
- 归一化必须走 `utils.lognorm_counts`（target_sum=1e4 级别的 log-normalize），与论文保持一致；
- IG 在大 batch 上很慢，建议先用 `ixg` 快速迭代、最终用 `ig` 出报告数据；
- 结果为相关性证据，任何"某基因驱动某表型"的结论都需要湿实验验证，写报告时注意措辞。
