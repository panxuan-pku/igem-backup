# 干实验项目进展汇报（详尽版）

> 项目：iGEM 2026「AAV 递送 + RNA binder 剂量补偿治疗染色体微缺失病」干实验/建模部分
> 时间跨度：2026-07-27 → 2026-09-01
> 配套材料：[工作日志](WORKLOG.md) ｜ [方法论复盘报告](02_disease-williams/05_report/微缺失病计算通路复盘报告.md) ｜ [架构图](architecture.html)

---

## 一、想法的提出：从一篇论文到一条通路（07-27）

### 1.1 我们要回答的问题

药物主线是：**AAV 载体递送 RNA binder，把微缺失病患者体内“剂量减半”的主效基因翻译水平上调回 100%**（剂量补偿）。干实验要回答的核心问题只有一个：

> **该上调哪个基因？改了它，细胞会变好吗？**

### 1.2 启发的来源

7 月 27 日，我系统调研了 Genentech 发表于 Nature Biotechnology 的论文 *Scoring gene importance by interpreting single-cell foundation models*（doi:10.1038/s41587-026-03112-5），即 **SIGnature 框架**。它的核心思路：把可解释 AI 的归因算法（Integrated Gradients 等）搬到单细胞基础模型上，给每个基因算一个“对细胞身份的重要性分数”。招牌案例是从一个炎症基因签名出发，在 412 项研究、2200 万细胞里**新发现**川崎病等三种疾病关联，并用患者血清实验完成验证闭环——这种“计算筛选 → 实验验证”的故事弧正是我们想要的范式。

同日完成仓库克隆与框架解析，确定技术选型：

| 组件 | 选型 | 角色 |
|---|---|---|
| 细胞编码器 | SCimilarity（Genentech, 23M 细胞预训练, 28231 基因→128 维嵌入） | 把细胞表达变成可比较的“坐标” |
| 归因算法 | Captum Integrated Gradients（n_steps=16） | 算每个基因的重要性分数 |
| 扰动模拟 | CellOracle（GRN 调控网络模拟）→ 后尝试 GEARS | “改一个基因，细胞怎么变” |
| 交互展示 | 自建 VirtualCellTool（FastAPI + Plotly） | 评委可上手操作的 demo |

### 1.3 设计的五步通路

**确定疾病 → 确定细胞类型 → 患者单细胞数据归因 → 候选基因列表 → 模拟扰动验证**

> 论文调研中已注意到两个伏笔，后来在实验中逐一兑现：①论文自己声明“归因 ≠ 因果”；②论文招牌方法是“先有签名→查疾病”，方向与我们的“先有疾病→找基因”相反。

---

## 二、想法的修改：三次被数据推动的修正

### 修改一（08-16）：不换“更大”的模型

- **起因**：担心 SCimilarity 对微缺失病基因覆盖不足，考虑换模型。
- **检验方法**：把 8 种微缺失病的 41 个候选基因逐一比对 SCimilarity 的 28,231 基因输入空间。
- **结果**：关键基因几乎全覆盖（22q11.2 命中 9/10、Williams 7/7、Angelman 4/4、Smith-Magenis 3/3）；反而是 scGPT（默认 3000 高变基因）、Geneformer（~16k）这类模型会缩减基因空间、可能漏掉疾病基因。
- **结论**：基因维度上 SCimilarity 反而有优势，不换；真正的风险在“脑类器官细胞状态覆盖”，留待后续实测。

### 修改二（08-17）：归因的价值边界——从“找靶点”到“候选生成器”

在真实的基因敲低实验数据上做了三组检验：

| 检验 | 数据来源 | 方法/工具 | 结果 | 含义 |
|---|---|---|---|---|
| 差分归因 vs 真实差异表达（幅度） | Norman Perturb-seq 5 个单基因敲低（KLF1/CEBPA/BAK1/ETS2/CEBPE） | SCimilarity + IG 归因 | r ≈ 0.81–0.85 | 归因确实追踪真实生物学，被敲基因能被捞回（KLF1 排第 1） |
| 差分归因方向性 | 同上 | 符号相关 | r ≈ 0.03–0.12 | 归因**给不了**“升还是降”的方向 |
| 归因 vs 真实扰动效应（预测性测试） | 同上，n=101 基因 | tier0 检验 | **r = 0.02 (p=0.83)** | 归因分数**预测不了因果** |
| 归因 vs 表达量 | 同上 | 相关性 | r = 0.86 | 归因 ≈ 差异表达，无独立信息 |

- **结论**：归因的合法定位是“候选生成器”——把搜索空间从全基因组压缩到几十个优先候选；它不是“证明器”，替代不了因果验证。这成为后续所有叙事的地基。

### 修改三（08-17）：扰动模型的更换尝试——GEARS 的接入与退场 ⭐

这是本次汇报新增的重点。起因、尝试、结果完整记录如下：

**起因**：v1 版扰动用 SCimilarity 编码器直接做反事实外推（改基因表达→看嵌入位移），但它是**单遍编码器、无调控级联**，扰动后的嵌入位移只有 **0.01**——信号太弱，且转录因子类低表达基因根本拨不动。需要一个“有级联传播”的因果扰动模型。

**尝试**：接入 **GEARS**（Stanford 的 Perturb-seq 因果预测模型），形成“归因找靶点 → GEARS 预测 → 重新归因验证”的 v2 闭环。

- **工具/版本**：cell-gears 0.1.2（注意：PyPI 上的 `gears` 是错误包名）；模型权重来自 HuggingFace `matthewshu/gears-norman`
- **数据来源**：Norman Perturb-seq 数据，官方 dataverse 被 AWS WAF 封锁，改用 Zenodo 镜像 17252307
- **验证方法**：在留出（held-out）的 CEBPA 敲低数据上，比较 GEARS 预测表达谱 vs 真实敲低细胞

**结果（正面）**：

| 指标 | v1（SCimilarity 反事实） | v2（GEARS 闭环） |
|---|---|---|
| 预测 vs 真实相关性 | 无法逐基因预测 | **r = 0.972** |
| 扰动嵌入位移 | 0.01 | **0.338（v1 的 34 倍）** |
| 生物学方向 | 一阶、无级联 | 红系↓髓系↑，符合已知生物学 |

v2 闭环建成（`tools/VirtualCellTool/src/v2_closed_loop.py`）。

**转折（退场原因）**：当我们准备把 GEARS 用到微缺失病主效基因上时，做了覆盖性检查——把 8 种病的 41 个候选基因逐一比对 GEARS 训练图（Norman 5045 基因共表达图）：

| 病 | 主效基因 | 在 GEARS 训练图中？ |
|---|---|---|
| 22q11.2DS | TBX1 | ❌ |
| Angelman | UBE3A | ❌ |
| Williams | GTF2I / GTF2IRD1 | ❌ |
| Smith-Magenis | RAI1 | ❌ |
| 15q13.3 / Cri-du-chat / 1p36 等 | CHRNA7 / CTNND2 / SKI 等 | ❌ |

41 个基因里只有 4 个在图中，且全是次要基因（COMT、UFD1L、CLIP2、FGFR3）。

- **根因**：所有 Perturb-seq 数据集（Norman/Adamson/Replogle）都是**癌细胞系**（K562 等），根本不表达发育/神经特异性基因——这是**结构性死路**，换数据集也救不了。叠加文献结论（Ahlmann-Eltze 2024：深度扰动模型在未见扰动上不优于线性基线），GEARS 对“人脑神经元里 GTF2I 半剂量”是双重域外。
- **结论**：GEARS 作为“微缺失病逐基因药效预测”这条线**画叉**；v2 闭环本身（工具拼接能力）保留为技术资产，GEARS 仅用于展示“工具能接通”而非用于本项目靶点决策。回退方案：SCimilarity 嵌入层做“恢复 G → 细胞朝健康态位移”的整体验证（能覆盖任意基因，代价是只有嵌入层面读数）。

### 修改四（08-18）：疾病对象从 22q11.2 换成 Williams

原计划 22q11.2DS + TBX1 验证全流程，实测 **TBX1 在脑类器官中仅 15/9,293 细胞表达**（心脏 TF，脑里“拨不动”）→ pivot 到 **Williams 综合征 + GTF2I**（82% 细胞表达，均值 3.39，且是 TF）。pivot 的原始数据证据保留在 `01_disease-22q11.2/`，写入复盘报告第 1 步。

---

## 三、干实验的设计与产出

### 3.1 平台层：VirtualCellTool（08-13，3 小时冲刺建成）

**设计**：按 iGEM Engineering 支柱的 DBTL 双循环组织，开工先立验收标准（AC1 方向性 / AC2 区分度 / AC3 延迟 <2s / AC4 可复现），并从第一天维护 `ATTRIBUTIONS.md` 归属登记。

| 模块 | 工具 | 数据 | 产出 |
|---|---|---|---|
| 预处理 | scanpy | PBMC 3k（10x Genomics） | `src/prepare_data.py` → embeddings/umap/expr |
| 归因 | SIGnature + SCimilarity + Captum IG | 同上 | `src/attribute.py` |
| 扰动引擎 | SCimilarity 编码器 | 同上 | `src/perturb.py` |
| 交互前端 | FastAPI + Plotly（端口 8377） | 同上 | `web/app.py`、`web/index.html` |

**结果**：B 细胞归因 Top 基因（MS4A1/CD79A/BANK1）**精确复现原论文**；AC1/AC2 通过（方向性 p<0.0005）；AC3 端到端 1.4 秒。

**产出**：`tools/VirtualCellTool/`（README、ATTRIBUTIONS.md、docs/ENGINEERING.md）

### 3.2 首个真实疾病数据验证：多发性硬化（08-13）

| 项 | 内容 |
|---|---|
| 数据 | CELLxGENE 16c1e722「Progressive MS 少突胶质细胞」，17,799 细胞（MS 11,208 vs 正常 6,591） |
| 方法 | 批量 IG 归因（645 细胞/秒，n_steps=16）→ 疾病 vs 对照差异归因 |
| 工具 | `src/compute_ms_attribution.py` |
| 结果 | Sanity check 通过：PLP1 两组第一、MOG 在 MS 中重要性减半 |
| 产出 | `tools/VirtualCellTool/data/ms_differential_attribution.csv`、`ms_analysis_report.png` |

**踩坑记录**：CELLxGENE 的 h5ad 里 var_names 是 Ensembl ID，需用 `var['feature_name']` 映射成基因符号。

### 3.3 主线验证：Williams 五步通路（08-18）

| 步骤 | 数据 | 方法/工具 | 结果 |
|---|---|---|---|
| 1. 确定疾病 | GSE283473（Williams 脑类器官）+ 22q11.2 脑数据 | CellOracle 可行性检查（TF 表达量） | TBX1 脑不表达 → pivot 到 GTF2I（82%） |
| 2. 数据预处理 | CTRL1-3 + WS1-3，6 样本 | scanpy：合并 → QC → HVG3000 + **强制保留 7q11.23 区段 20 基因** → Leiden 聚类 | 96,969 细胞 × 3,016 基因，16 cluster；产出 `03_intermediate/processed.h5ad` |
| 3. 差异归因 | 5,000 患者 + 5,000 对照子采样 | SIGnature + SCimilarity 基因空间对齐 + IG 批量归因（`02_scripts/attribution_analysis.py`） | 疾病信号 = 神经元分化基因；**删失基因自身 Δattr ≈ 0**；Δattr vs DE **r = 0.949** |
| 4. 候选基因 | 上步结果 + 真实 DE 对照 | 取 \|Δattr\| Top 基因 | 候选 = NEUROD2/6、SOX5、NFIA、ZEB2、BCL11B |
| 5. 扰动验证 | `processed.h5ad` | CellOracle + hg38 promoter base GRN（gimmemotifsv5_fpr2）→ GTF2I 敲低→0 / 过表达→2×（`02_scripts/celloracle_run.py`） | KO r=−0.046 / OE r=+0.072（全局≈0）；但 Top 被恢复基因方向正确（神经基因被 OE 往上拉） |

**最硬的正面结果**：SIGnature（归因）与 CellOracle（GRN 扰动）两个**互相独立**的方法，收敛到**同一批候选基因**（神经元分化程序）。交叉验证成立，这是本项目最经得起推敲的正面产出。

**产出**：`02_disease-williams/04_results/attribution_results.npz` + `results.npz`；`02_disease-williams/05_report/微缺失病计算通路复盘报告.md/.docx/.pdf`（五步通路逐环节【问题/思路/方法/结果/不足】+ 22 个术语表 + 三个根本不足）。

### 3.4 整理归档（09-01）

- 4 个散落仓库收拢为总目录 `iGEM-Microdeletion/`（01_disease-22q11.2 废弃 pivot 案例 / 02_disease-williams 主线五层结构 / tools/SIGnature / tools/VirtualCellTool），批量修正 17 个文件的硬编码路径并验证可运行
- 产出交互式架构图 `architecture.html`（archify 工具，showcase 级 9/9 校验通过）

---

## 四、结果分析闭环：负结果为什么是资产

### 4.1 三个结构性天花板（换工具也解决不了）

1. **翻译层盲区**：我们的药作用在蛋白翻译层，而所有 mRNA 模型默认“mRNA 量 = 蛋白量”——模型从结构上看不见药效。
2. **单基因 vs 多基因错配**：微缺失是 ~25 个基因同时剂量减半，段内往往只有 1 个 TF 可扰；单基因视角只能抓到疾病信号的零头（Williams 实测：GTF2I 扰动相关性≈0）。
3. **删失基因稳态 mRNA“隐身”**：单倍不足效应在静态转录组里测不到（GTF2I 的 DE≈0、Δattr≈0）。

### 4.2 由此收敛出的新策略（08-26 团队汇报后确定）

- **证据金字塔替代单一模型**：L1 人类遗传学剂量证据（LOEUF/pLI/pHaplo 公开表格）→ L2 真实 Perturb-seq 数据 → L3 虚拟扰动只做机制假设并诚实报告其失效。
- **A/B 线解耦**：药物线的靶点用文献确证结论（TBX1/RAI1/ELN 等）定，不再依赖计算筛选；计算工具线作为独立的“优先级排序框架”成为 Contribution 交付物，用 RAI1/ELN/TBX1 已知答案做方法学正对照。
- **可成药性约束加入排序**：靶点须满足“剂量不足驱动 + 翻译上调可挽救 + 过表达安全 + 出生后可逆”，直接对齐 AAV/RNA binder 模态。

### 4.3 完整 DBTL 闭环

假设（归因找靶点）→ 实现（VCT + 双工具通路）→ 验证（r=0.02、r=0.949、GTF2I 扰动≈0）→ 学习（归因≠因果、三个天花板）→ 新框架（证据金字塔 + 正对照）。负结果排除了死路，避免团队在错误方向上继续投入数月——这是本阶段干实验的核心价值。

---

## 五、产出清单与链接

| 产出 | 位置 | 说明 |
|---|---|---|
| 交互平台 VirtualCellTool | `tools/VirtualCellTool/` | FastAPI demo，`:8377`，启动命令见 README |
| 归因框架环境 | `tools/SIGnature/` | .venv（py3.11）+ 235MB 模型包 |
| Williams 主线数据与结果 | `02_disease-williams/` | 01_rawdata → 05_report 五层结构 |
| 22q11.2 pivot 证据 | `01_disease-22q11.2/` | TBX1 脑不表达的原始数据 |
| 方法论复盘报告 | `02_disease-williams/05_report/` | md / docx / pdf 三份 |
| 架构图 | `architecture.html` | 交互式，双主题，可导出 PNG/SVG |
| 工作日志 | `WORKLOG.md` | 逐日记录 + 会话存档链接 |
| GEARS v2 闭环 | `tools/VirtualCellTool/src/v2_closed_loop.py` | r=0.972 验证（已说明适用范围） |
| MS 差异归因 | `tools/VirtualCellTool/data/ms_differential_attribution.csv` | 首个真实疾病数据产物 |

**会话存档**（可跳回原始讨论）：07-27 论文调研 @session:default/20260727_142714_bf5a5d3e ｜ 08-13 平台搭建 @session:default/20260813_120050_362dbb3f ｜ 08-16 可行性检查 @session:default/20260816_172608_b32271a2 ｜ 08-17 方法学检验 + GEARS 更换 @session:default/20260817_084149_d3d9be1b ｜ 08-18 Williams 主线 @session:default/20260818_104152_0aea53d1 ｜ 08-19 汇报反思 @session:default/20260819_104655_37786720 ｜ 08-26 方向收敛 @session:default/20260826_182830_c6ec3c91
