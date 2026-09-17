# AI 虚拟细胞扰动响应预测工具调研报告：经典奠基与 2024–2026 前沿

> 任务：以任务 0（t_916cd9f6）提取的知乎博客清单为基线，系统调研「AI 虚拟细胞扰动响应预测」领域的经典与前沿工具，找出博客之外遗漏或更新的工作。
> 调研日期：2026-09-12。检索源：bioRxiv、Nature Methods、Nature、Nature Biotechnology、Molecular Systems Biology、arXiv、NeurIPS、AI4Bio Learning Hub（xqiu625.github.io）、Arc Institute 官网、各工具 GitHub 官方仓库。

---

## 0. 结论先行（3 行）

1. 博客基线（= 同济 Qi Liu 组 scPerturBench，Nat Methods 2025）覆盖 23 个命名方法，几乎全是「经典奠基 + 2024 基础模型」一代（scGen/CPA/CellOT/GEARS/scGPT/scFoundation 等），但**遗漏了 2024–2026 三条最重要的新方向**：因果推理/流匹配生成（CellFlow、CINEMA-OT、PerturbDiff、Squidiff）、物理理论驱动（CIPHER）、以及 Arc Institute 的 set-transformer 虚拟细胞模型（State、Stack）。

2. 本次新增发现 11 个博客未收录工具：**Geneformer、CINEMA-OT、CellOracle、SAMS-VAE、PerturbNet、Squidiff、CellFlow、State、Stack、CIPHER、PerturbDiff**，其中 State/Stack/CellFlow/CIPHER 是 2025–2026 的最前沿（含 Arc 100M+ 细胞扰动数据训练、流匹配生成、线性响应理论三条独立路线）。

3. 领域共识正在收敛到三点：(a) 基础模型不自动占优，线性/可解释基线屡次追平甚至反超（Ahlmann-Eltze 等 Nat Methods 2025 基准、scPerturBench 真实排名）；(b) 泛化硬伤在「未见扰动」与「未见细胞上下文」两个零样本切分上；(c) 官方竞赛（Arc Virtual Cell Challenge 2025/2026）正在成为事实标准，2026 年已升级为零样本跨细胞系 CRISPRi 预测、无训练集。

---

## 1. 调研方法与置信度声明

| 事项 | 结果 |
|------|------|
| 博客基线 | 复用任务 0 产物（scPerturBench 23 命名方法 + 4 基线，来自论文官方仓库 bm2-lab/scPerturBench README） |
| 新增发现路径 | web 检索 → bioRxiv/期刊原文/官方 GitHub 核对论文、代码、年份、团队 |
| 置信度 | 论文/代码/年份/团队 = 高（逐条核对官方源）；「基准表现」= 中（引用论文声明的数字，未独立复现） |
| 未独立验证项 | 各工具的 benchmark 分数为论文自报或第三方基准（scPerturBench/PerturBench）引用，均标注来源 |

---

## 2. 领域地图（方法分类全景）

按方法核心思想分为 7 类，标注博客是否已收录：

| 方法类别 | 核心思想 | 代表工具（博客已收录 / 本次新增） |
|---------|---------|--------------------------------|
| ① VAE 潜空间算术 | 扰动 = 潜空间向量加减 | scGen、CPA、trVAE、scVIDR、scPreGAN（已收录）／SAMS-VAE（新增） |
| ② 图神经网络 + 知识图谱 | GRN/GO 图传播扰动效应 | GEARS（已收录）／CellOracle（新增，线性 GRN 传播） |
| ③ 最优传输 / 流匹配 | 分布间最优映射（OT/Flow） | CellOT、SCREEN（已收录）／CINEMA-OT、CellFlow、PerturbDiff（新增） |
| ④ 扩散模型 | 迭代去噪生成扰动态 | —（博客缺失）／Squidiff、PerturbDiff（新增） |
| ⑤ 基础模型（Transformer 预训练） | 大规模预训练 + 微调 | scGPT、scFoundation、GeneCompass、scELMo（已收录）／Geneformer、State、Stack（新增） |
| ⑥ 物理/理论驱动 | 线性响应、统计物理 | linearModel 基线（已收录）／CIPHER（新增） |
| ⑦ 因果推理 | 反事实匹配 + 因果效应 | —（博客缺失，仅见于可视化子任务）／CINEMA-OT（新增） |

**关键观察**：博客基线几乎完全集中在 ①②③⑤ 四类，对 ④（扩散）、⑥（物理理论）、⑦（因果推理）三类几乎空白——这正是本次新增发现的价值所在。

---

## 3. 经典奠基（~2023 前及 2023 年）

### 3.1 博客已收录（基线，简表）

以下为博客/scPerturBench 已覆盖的代表性奠基方法，仅列核心信息，详见任务 0 报告：

| 工具 | 论文 | 代码 | 年份 | 团队 | 核心思想 | 扰动类型 |
|------|------|------|------|------|---------|---------|
| scGen | [Nat Methods 2019](https://www.nature.com/articles/s41592-019-0494-8) | [theislab/scgen](https://github.com/theislab/scgen) | 2019 | Theis 组 | VAE 潜空间向量算术 | 药物/基因 |
| CPA | [Mol Syst Biol 2023](https://www.embopress.org/doi/full/10.15252/msb.202211517) | [theislab/cpa](https://github.com/theislab/cpa) | 2023 | Theis 组 | 组合扰动条件 VAE | 药物(组合/剂量)/基因 |
| CellOT | [Nat Methods 2023](https://www.nature.com/articles/s41592-023-01969-x) | [bunnech/cellot](https://github.com/bunnech/cellot) | 2023 | Bunne/ETH | 输入凸神经网络(ICNN)最优传输 | 药物/基因 |
| GEARS | [Nat Biotechnol](https://www.nature.com/articles/s41587-023-01905-6) | [snap-stanford/GEARS](https://github.com/snap-stanford/GEARS) | 2022 在线/2023 | Stanford SNAP (Zou) | 双知识图谱 GNN | 多基因(组合) |
| scGPT | [Nat Methods 2024](https://www.nature.com/articles/s41592-024-02201-0) | [bowang-lab/scGPT](https://github.com/bowang-lab/scGPT) | 2024 | Bo Wang 组 | 单细胞生成式预训练基础模型 | 基因/药物 |
| scFoundation | [Nat Methods 2024](https://www.nature.com/articles/s41592-024-02305-7) | [biomap-research/scFoundation](https://github.com/biomap-research/scFoundation) | 2024 | BIOMAP | 读深感知大规模基础模型 | 基因/药物 |

其余已收录：trVAE、scVIDR、chemCPA、PRnet、scPreGAN、biolord、scDisInFact、GeneCompass、scELMo、GenePert、AttentionPert、cycleCDR、SCREEN、scPRAM、scouter、inVAE（详见任务 0 报告清单）。

### 3.2 博客遗漏的经典（本次补遗）

#### Geneformer —— 注意力机制 in silico 扰动（博客遗漏 ★）
- **论文**：[Nature 2023, DOI 10.1038/s41586-023-06139-9](https://www.nature.com/articles/s41586-023-06139-9)
- **代码**：[HuggingFace ctheodoris/Geneformer](https://huggingface.co/ctheodoris/Geneformer)（`geneformer/in_silico_perturber.py`）
- **年份/团队**：2023，Christina V. Theodoris（Gladstone/Broad/DFCI，原 Broad 博后）
- **核心思想**：基于 ~3000 万（现 >1 亿）单细胞转录组的上下文感知双向 Transformer 基础模型。in silico 扰动通过「删除某基因的 rank-value token 并量化其余基因嵌入的位移」来模拟基因敲除/激活，无需任何扰动训练数据。
- **扰动类型**：基因敲除/抑制（in silico deletion/overexpression），零样本
- **训练数据规模**：Genecorpus-30M（~30M 细胞，现扩展至 >100M）
- **基准表现与局限**：在心肌病剂量敏感基因预测等任务上显著优于替代方法；局限是「删除 token」的近似并非真正的表达变化模拟，输出是嵌入位移排序（靶点优先级）而非定量表达谱，不直接做转录组水平预测。

#### CellOracle —— GRN 线性传播 in silico 扰动（博客遗漏 ★）
- **论文**：[Nature 2023, DOI 10.1038/s41586-022-05688-9](https://www.nature.com/articles/s41586-022-05688-9)
- **代码**：[morris-lab/CellOracle](https://github.com/morris-lab/CellOracle)
- **年份/团队**：2023，Morris/Cahan 组（Washington Univ / JHU）
- **核心思想**：两阶段——(1) 用 scATAC-seq + scRNA-seq 经贝叶斯/Bagging 岭回归推断细胞类型特异的 GRN；(2) 沿 GRN 边做**线性**传播，模拟 TF 敲除/过表达后的细胞身份位移（输出为低维向量场而非绝对表达）。
- **扰动类型**：转录因子敲除/过表达
- **训练数据规模**：仅需未扰动野生型多组学数据（无需扰动训练）
- **基准表现与局限**：在斑马鱼胚胎发生、造血 TF 扰动上正确复现表型变化；局限是线性传播假设、输出限于细胞身份位移（2D 向量场）而非全转录组定量预测。

---

## 4. 2024–2025 前沿（本次新增为主）

### 4.1 流匹配 / 扩散生成（2024–2026）

#### CellFlow —— 流匹配生成扰动表型（博客遗漏 ★★，任务点名）
- **论文**：[bioRxiv 2025, DOI 10.1101/2025.04.11.648220](https://www.biorxiv.org/content/10.1101/2025.04.11.648220)
- **代码**：[theislab/CellFlow](https://github.com/theislab/CellFlow)（文档 cellflow.readthedocs.io）
- **年份/团队**：2025，Fabian J. Theis 组（Helmholtz Munich + TUM，联合 Treutlein/Regev/Camp）
- **核心思想**：用流匹配（flow matching）学习控制分布→扰动分布的连续速度场，把扰动响应建模为**分布到分布**的映射，天然捕获细胞异质性。支持组合药物、剂量、时序。
- **扰动类型**：细胞因子刺激、药物（单药/组合）、基因敲除、形态素组合
- **训练数据规模**：高内涵表型筛选数据（药物/遗传/细胞因子）；可扩展至全胚胎发育扰动、类器官协议
- **基准表现与局限**：在多种表型筛选上准确预测未见条件响应，并完成「虚拟类器官筛选」；局限是需配对的控制/扰动批量数据，未见扰动的纯零样本泛化弱于基础模型路线。

#### Squidiff —— 扩散模型预测响应（博客遗漏 ★）
- **论文**：Squidiff: Predicting cellular development and responses to perturbations using a diffusion model（[PMC12407682](https://pmc.ncbi.nlm.nih.gov/articles/PMC12407682)）
- **代码**：见论文（diffusion autoencoder + DDIM）
- **年份/团队**：2025
- **核心思想**：扩散自编码器（semantic encoder + 条件 DDIM），在语义潜空间做扩散，预测跨细胞类型的转录组响应。
- **扰动类型**：细胞分化、基因扰动、药物处理
- **基准表现与局限**：跨三种任务（分化/基因/药物）验证稳健性；局限是扩散采样慢、条件组合外推有限。

#### PerturbDiff —— 函数式扩散（博客遗漏 ★，2026 预印）
- **论文**：[arXiv 2602.19685](https://arxiv.org/html/2602.19685v1)
- **代码**：论文声明「code and data 即将公开」
- **年份/团队**：2026 预印
- **核心思想**：把「细胞分布」本身（经核均值嵌入 kernel mean embedding 表示）当作扩散的随机变量，而非把单个细胞当随机变量；MM-DiT 块对控制/扰动 token 流做联合注意力。显式建模分布级变异性，克服传统模型「单一固定响应分布」假设。
- **扰动类型**：基因/药物
- **基准表现与局限**：在既有数据集上达 SOTA 且对未见扰动泛化更强；局限是预印、代码未公开、核均值嵌入计算开销。

### 4.2 Arc Institute 虚拟细胞模型（2025–2026）

#### State —— 首代 set-transformer 虚拟细胞模型（博客遗漏 ★★★，任务点名）
- **论文**：[bioRxiv 2025, DOI 10.1101/2025.06.26.661135](https://www.biorxiv.org/content/10.1101/2025.06.26.661135v1)
- **代码**：[ArcInstitute/state](https://github.com/ArcInstitute/state)
- **年份/团队**：2025，Arc Institute（Abhinav Adduri 等，合作 Stanford Leskovec、UCSF Gilbert/Konermann、Patrick Hsu）
- **核心思想**：跨物理尺度的 set-based Transformer，由两部分组成——**状态转移模型**（在细胞集合上学习扰动效应）+ **细胞嵌入模型**（SE，State Embedding）。用双向注意力在细胞群体上建模，而非单细胞独立嵌入。用嵌入模型在「从未见过扰动的全新细胞上下文」中识别强扰动。
- **扰动类型**：遗传（CRISPRi/a）、化学（药物）、环境
- **训练数据规模**：>100M 扰动细胞（70 个细胞上下文）+ 167M 人观测细胞
- **基准表现与局限**：在 Tahoe-100M 上扰动效应判别提升 50%+、真 DEG 识别精度 2×；局限是 2025-06 发布、太新未经独立第三方验证。

#### Stack —— 上下文学习（in-context learning）虚拟细胞模型（博客遗漏 ★★★）
- **论文**：[bioRxiv 2026, DOI 10.64898/2026.01.09.698608](https://biorxiv.org/content/10.64898/2026.01.09.698608v1.article-info)
- **代码**：[ArcInstitute/stack](https://github.com/ArcInstitute/stack)
- **年份/团队**：2026，Arc Institute（Mingze Dong、Abhinav Adduri、Yusuf Roohani 等，合作 Yale）
- **核心思想**：tabular attention 架构，把细胞×基因矩阵分块作为输入单元，实现细胞内（基因间）与细胞间双重信息流。**真正的上下文学习**：推理时给一组带标签的 prompt 细胞集，即零样本预测未见扰动响应，无需任何权重更新/微调。
- **扰动类型**：化学、遗传、供体水平扰动
- **训练数据规模**：150M 统一预处理单细胞 + 55M 细胞 post-training（CellxGene + Parse PBMC）
- **基准表现与局限**：在 31 项 in-context 评测中 28 项排第 1（零样本扰动/供体/条件迁移）；发布 Perturb-Sapiens 图谱（513,870 细胞、28 组织、40 细胞类、201 扰动）。局限是 2026 预印、需 GPU 推理。

> State 与 Stack 关系：State = 微调范式（对目标任务 fine-tune set-transformer）；Stack = 上下文学习范式（零权重更新）。二者互补，同属 Arc 虚拟细胞路线。

### 4.3 物理理论驱动（2025）

#### CIPHER —— 线性响应理论（博客遗漏 ★★）
- **论文**：[bioRxiv 2025, DOI 10.1101/2025.06.27.661814](https://doi.org/10.1101/2025.06.27.661814)（Goyal 组，Northwestern）
- **代码**：[GoyalLab/CIPHER](https://github.com/GoyalLab/CIPHER)（PyPI: cipher-perturb）
- **核心思想**：统计物理的线性响应理论——响应 Δx = Σu，其中 Σ 是**未扰动细胞**的基因-基因协方差矩阵，u 是稀疏驱动向量。只靠基线涨落结构预测全转录组扰动结果，配 Bayesian（Horseshoe 先验）不确定度估计。
- **扰动类型**：基因敲低（CRISPRi）、激活（CRISPRa）
- **训练数据规模**：仅需未扰动控制细胞（无需任何扰动训练），11 数据集 / 4,234 扰动 / 1.36M 细胞验证
- **基准表现与局限**：合成网络上 R² 达 1.0；扰动识别 AUROC=0.92（超越传统差异表达指标）；消除基因-基因协方差使性能下降 11 倍，证明涨落结构是核心信息。局限是线性近似、对强非线性响应可能失效。

### 4.4 生成模型补遗（2023–2025）

#### SAMS-VAE —— 稀疏可加机制偏移 VAE（博客遗漏 ★）
- **论文**：[NeurIPS 2023, arXiv 2311.02794](https://arxiv.org/abs/2311.02794)
- **代码**：[insitro/sams-vae](https://github.com/insitro/sams-vae)
- **年份/团队**：2023（NeurIPS），insitro
- **核心思想**：扰动样本潜态 = 局部潜变量（样本特异性）+ 稀疏全局扰动潜变量之和；对每个扰动做稀疏化以得到可解耦、可组合的扰动特异潜子空间。
- **扰动类型**：药物/基因（含组合）
- **基准表现与局限**：在组合扰动任务上超越 CPA；局限是稀疏约束的调参、对大规模数据集扩展性。

#### PerturbNet —— 未见化学/遗传扰动预测（博客遗漏 ★）
- **论文**：[Mol Syst Biol 2025, DOI 10.1038/s44320-025-00131-3](https://link.springer.com/article/10.1038/s44320-025-00131-3)
- **代码**：见论文（VAE + OT + ChemicalVAE 嵌入）
- **年份/团队**：2025
- **核心思想**：VAE（ZINB 似然直接建模原始计数）+ 最优传输，用药物嵌入（ChemicalVAE）与基因功能注释辅助预测未见化学/遗传扰动后的细胞状态分布。
- **扰动类型**：化学（药物）、遗传（CRISPRa/i）
- **基准表现与局限**：在未见化学扰动 R²/Pearson 上超越 chemCPA 与线性基线；对未见基因扰动显著优于先前方法。局限是依赖药物/基因功能注释的覆盖。

### 4.5 因果推理（2023，博客遗漏、任务点名）

#### CINEMA-OT —— 因果反事实匹配（博客遗漏 ★★）
- **论文**：[Nat Methods 2023, DOI 10.1038/s41592-023-02040-5](https://www.nature.com/articles/s41592-023-02040-5)
- **代码**：[vandijklab/CINEMA-OT](https://github.com/vandijklab/CINEMA-OT)（新版并入 scverse/pertpy）
- **年份/团队**：2023，van Dijk 组（Yale）
- **核心思想**：ICA 分解出混杂因子与治疗相关因子 → 在混杂空间做熵正则化最优传输（Sinkhorn）得到反事实细胞对 → 估计个体治疗效应（ITE）、响应聚类、归因、协同分析。
- **扰动类型**：细胞因子、病毒、药物（处理效应）
- **训练数据规模**：无监督，需配对控制/处理组
- **基准表现与局限**：在治疗效应估计任务上优于其他单细胞扰动分析方法；局限是回答「因果反事实」而非「表达谱预测」，与生成式预测工具是互补而非替代。

---

## 5. 对比分析总表

| 工具 | 年份 | 类别 | 扰动类型 | 训练数据需求 | 博客收录 | 主要优势 | 主要局限 |
|------|------|------|---------|-------------|---------|---------|---------|
| scGen | 2019 | VAE | 药物/基因 | 配对扰动数据 | ✅ | 简单、经典 | 假设同质响应 |
| CPA | 2023 | VAE | 药物组合/剂量 | 配对扰动数据 | ✅ | 组合/剂量建模 | 每扰动需训练数据 |
| CellOT | 2023 | OT | 药物/基因 | 未配对控制/处理 | ✅ | 单细胞级轨迹 | 计算开销 |
| GEARS | 2022/23 | GNN | 多基因组合 | 扰动数据+知识图谱 | ✅ | 遗传互作 40% 精度提升 | 依赖 GO 图谱，弱连接基因退化 |
| scGPT | 2024 | 基础模型 | 基因/药物 | 33M+ 细胞预训练 | ✅ | 大规模预训练 | 扰动任务反被线性基线超越 |
| scFoundation | 2024 | 基础模型 | 基因/药物 | 50M 细胞 | ✅ | 读深感知 | 同上，单基因扰动不占优 |
| **Geneformer** | 2023 | 基础模型 | 基因(零样本) | 30M→100M 细胞 | ❌新增 | 零样本 in silico 扰动 | 输出排序而非表达谱 |
| **CellOracle** | 2023 | GRN | TF 敲除/过表达 | 仅野生型多组学 | ❌新增 | 可解释、无需扰动数据 | 线性假设、输出限于身份位移 |
| **CINEMA-OT** | 2023 | 因果+OT | 细胞因子/病毒/药物 | 控制/处理组 | ❌新增 | 反事实、ITE、协同 | 非表达谱预测 |
| **SAMS-VAE** | 2023 | VAE | 药物/基因组合 | 扰动数据 | ❌新增 | 稀疏可加、超越 CPA | 稀疏调参 |
| **PerturbNet** | 2025 | VAE+OT | 化学/遗传(未见) | 扰动数据+注释 | ❌新增 | 未见扰动强泛化 | 依赖功能注释 |
| **Squidiff** | 2025 | 扩散 | 分化/基因/药物 | 扰动数据 | ❌新增 | 扩散生成稳健 | 采样慢 |
| **CellFlow** | 2025 | 流匹配 | 细胞因子/药物/基因 | 配对控制/扰动 | ❌新增 | 异质性、虚拟类器官 | 需配对数据 |
| **State** | 2025 | set-transformer | 遗传/化学/环境 | 100M+ 扰动细胞 | ❌新增 | 扰动判别 50%+ 提升 | 太新未验证 |
| **Stack** | 2026 | 上下文学习 | 化学/遗传/供体 | 150M 细胞 | ❌新增 | 零样本免微调 | 预印、需 GPU |
| **CIPHER** | 2025 | 线性响应 | 基因敲低/激活 | 仅控制细胞 | ❌新增 | 可解释、AUROC 0.92 | 线性近似 |
| **PerturbDiff** | 2026 | 函数扩散 | 基因/药物 | 扰动数据 | ❌新增 | 分布级 SOTA | 代码未公开 |

---

## 6. 基准/竞赛生态（博客未充分展开的前沿）

| 基准/竞赛 | 范围 | 年份 | 关键发现 |
|-----------|------|------|---------|
| scPerturBench（博客基线） | 27 方法/29 数据集/6 指标 | Nat Methods 2025 | 基础模型不自动占优，线性模型反超 |
| Ahlmann-Eltze 等基准 | 5 基础模型 + 2 深度方法 vs 线性基线 | [Nat Methods 2025, DOI 10.1038/s41592-025-02772-6](https://www.nature.com/articles/s41592-025-02772-6) | 无一个深度模型击败线性/可加基线；发现「模式坍缩」（预测不随扰动变化） |
| PerturBench | 扰动预测统一基准 | NeurIPS 2024 | 指标统一化 |
| Arc Virtual Cell Challenge 2025 | H1 hESC 单上下文泛化 | Cell 2025（[Commentary](https://www.cell.com/cell/fulltext/S0092-8674(25)00675-0)） | 冠军 Team BM_xTVC（BioMap，xTrimoSCPerturb）仍需手工统计特征叠加深度学习 |
| Arc Virtual Cell Challenge 2026 | 零样本跨 6 细胞系 CRISPRi，无训练集 | [2026-08](https://arcinstitute.org/news/virtual-cell-challenge-2026) | 评分改用 6 指标聚合，防止指标过拟合 |

**前沿数据基石**：Tahoe-100M（[bioRxiv 2025.02.20.639398](https://doi.org/10.1101/2025.02.20.639398)，100M 细胞/50 癌症系/1,100 药）、scPerturb（[Nat Methods 2024](https://www.nature.com/articles/s41592-023-02144-y)，44 数据集）、Replogle 2022 全基因组 Perturb-seq（K562 2.5M 细胞）。

---

## 7. 值得深挖的开放问题

1. **零样本跨细胞系泛化是否可解**：Arc 2026 Challenge 明确把「未见细胞上下文的 CRISPRi 响应预测」设为 $100K 任务且无训练集——State/Stack 的 in-context learning 能否经受独立评测，是当前最关键的未决问题。
2. **线性基线之谜**：CIPHER 的线性响应理论 + Ahlmann-Eltze 的线性可加基线为何持续追平深度学习？是否说明当前扰动效应本质上接近线性、还是现有非线性模型训练不足？这条线索可能指向新一代「物理先验 + 深度学习」混合架构。
3. **流匹配 vs 扩散 vs 上下文学习**：三条 2025 新路线（CellFlow/PerturbDiff、Squidiff、Stack）尚无头对头独立评测，需统一在 scPerturBench/PerturBench/Virtual Cell Challenge 上对比。
4. **预测「表达谱」与「因果反事实」的鸿沟**：CINEMA-OT 与生成式工具回答不同问题，未来需要把因果框架与生成模型融合（如 bioLord-emCell 的解耦方向）。
5. **评测指标的诚实性**：父任务已指出「Pearson-delta vs 原始 Pearson」「control-mean 基线」的陷阱，跨论文分数不可直接比较——需要一份带 evidence 的第三方复现报告。

---

## 8. 参考文献（DOI / 链接）

经典奠基
- Lotfollahi et al. scGen. Nat Methods 2019. DOI 10.1038/s41592-019-0494-8
- Lotfollahi et al. CPA. Mol Syst Biol 2023. DOI 10.15252/msb.202211517
- Bunne et al. CellOT. Nat Methods 2023. DOI 10.1038/s41592-023-01969-x
- Roohani et al. GEARS. Nat Biotechnol. DOI 10.1038/s41587-023-01905-6
- Cui et al. scGPT. Nat Methods 2024. DOI 10.1038/s41592-024-02201-0
- Hao et al. scFoundation. Nat Methods 2024. DOI 10.1038/s41592-024-02305-7
- Theodoris et al. Geneformer. Nature 2023. DOI 10.1038/s41586-023-06139-9
- Kamimoto et al. CellOracle. Nature 2023. DOI 10.1038/s41586-022-05688-9
- Dong et al. CINEMA-OT. Nat Methods 2023. DOI 10.1038/s41592-023-02040-5
- Bereket & Karaletsos. SAMS-VAE. NeurIPS 2023. arXiv 2311.02794

2024–2026 前沿
- Klein et al. CellFlow. bioRxiv 2025. DOI 10.1101/2025.04.11.648220
- Adduri et al. State. bioRxiv 2025. DOI 10.1101/2025.06.26.661135
- Dong et al. Stack. bioRxiv 2026. DOI 10.64898/2026.01.09.698608
- Kuznets-Speck et al. CIPHER. bioRxiv 2025. DOI 10.1101/2025.06.27.661814
- PerturbNet. Mol Syst Biol 2025. DOI 10.1038/s44320-025-00131-3
- Squidiff. 2025. PMC12407682
- PerturbDiff. arXiv 2026. 2602.19685

基准/竞赛
- Wei et al. scPerturBench. Nat Methods 2025. DOI 10.1038/s41592-025-02980-0（博客基线）
- Ahlmann-Eltze et al. Nat Methods 2025. DOI 10.1038/s41592-025-02772-6
- Arc Virtual Cell Challenge 2025/2026: arcinstitute.org
- Tahoe-100M. bioRxiv 2025. DOI 10.1101/2025.02.20.639398
- Peidli et al. scPerturb. Nat Methods 2024. DOI 10.1038/s41592-023-02144-y
