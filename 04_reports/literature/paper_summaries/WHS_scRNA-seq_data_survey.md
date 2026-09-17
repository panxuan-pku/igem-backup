# Wolf-Hirschhorn Syndrome (WHS) — scRNA-seq 数据调研

> 调研日期：2026-09-07 · 项目：iGEM SINEUP WHS 主效基因筛选

---

## 核心结论：目前没有公开的 WHS scRNA-seq 数据

经过对 GEO、SRA、PubMed 的系统搜索，**Wolf-Hirschhorn 综合征（4p16.3 缺失）目前没有任何公开的 scRNA-seq 数据集**。这与 Williams 综合征（WS，GSE283473）形成鲜明对比——WS 已经有脑类器官 scRNA-seq 数据和相关的 Nature 级别论文，而 WHS 仍然停留在 hiPSC 细胞系构建阶段。

---

## 一、WHS 的转录组学研究现状

### 唯一相关的公开 GEO 数据

| 数据集 | 类型 | 组织 | 物种 | 年份 |
|---|---|---|---|---|
| **GSE232564 / GSE232566** | Bulk RNA-seq + ChIP-seq | E15.5 全脑 | Nsd2 KO 小鼠 | 2024 |

这是 Frontier in Genetics (2024) 发表的 NSD2 敲除小鼠胚胎脑的 bulk RNA-seq 和 H3K36me2 ChIP-seq 数据。结论是 NSD2 缺失导致突触传递和形成相关基因失调——但这只是 NSD2 单基因敲除的表型，不是 WHS 区间全部基因的效应。

### hiPSC 细胞系（无转录组数据）

| 论文 | 内容 | 年份 |
|---|---|---|
| **Human Cell (2025)** | 从 3 个 WHS 患者成纤维细胞建立了 hiPSC 系，CNV 分析确认了 4p15.1–p16.3 杂合缺失 | 2025 |
| **Elucidata rare disease datasets** | GSE84878 — WHS 小鼠 bulk RNA-seq（5 个样本，2017 年） | 2017 |

---

## 二、WHS 已知关键基因与表型关联

WHS 的 4p16.3 缺失区间大小不一（从 <400 kb 到 >10 Mb），但有一个 **WHSCR（WHS critical region，约 165–200 kb）** 被划定为核心区域。

### 核心基因

| 基因 | 别名 | 功能 | 关联表型 | 证据强度 |
|---|---|---|---|---|
| **NSD2** | WHSC1 | 组蛋白甲基转移酶 (H3K36me2)，调控突触基因表达 | 🟢 被认为是 WHS 的**最关键因果基因**。单基因 NSD2 功能缺失变异（Rauch-Steindl 综合征）可独立产生整体 WHS 样表型（生长迟缓、DD/ID、小头畸形、面部特征），不依赖缺失其他基因 | 🔴 极强——已从"缺失区间候选"升级为"主要的因果基因" |
| **NELFA** | WHSC2 | 负延伸因子复合体亚基，转录调控 | 🟡 NSD2 之后最可能与核心表型相关。功能缺失变异产生非典型 WHS 表型 | 🟡 中等 |
| **LETM1** | — | 线粒体 Ca²⁺/H⁺ 转运蛋白 | 🟡 **癫痫**表型的主要候选基因。双等位基因变异导致的线粒体疾病以神经系统为主 | 🟡 中等 |
| **TACC3** | — | 神经嵴细胞迁移调控，颅面发育 | 🟡 与**颅面畸形**相关。在 Xenopus 中敲低导致颅面缺陷 | 🟡 中弱 |
| **SLBP** | — | 组蛋白 mRNA 茎环结合蛋白 | 🟡 可能与细胞增殖异常相关 | 🟡 弱 |
| **CTBP1** | — | 转录辅助抑制因子 | 🟡 位于远端 4p16.3，部分缺失区间包含 | 🟡 弱 |

### 关键发现（2022 年后的范式转变）

> **NSD2 单基因功能缺失即可产生整体 WHS 核心表型。**
> (From Wolf-Hirschhorn syndrome to NSD2 haploinsufficiency: a shifting paradigm, Italian Journal of Pediatrics, 2022)

这意味着 NSD2 不再只是"候选基因之一"，而可能是 WHS 的**最主要甚至唯一的因果基因**。其他区间基因修饰了表型的严重程度和额外特征（如癫痫 = LETM1，颅面 = TACC3 等）。

---

## 三、与 WS (Williams 综合征) 的对比：为什么 WHS 落后这么多？

| | Williams 综合征 (7q11.23) | Wolf-Hirschhorn 综合征 (4p16.3) |
|---|---|---|
| 患病率 | ~1/7,500 | ~1/50,000（更罕见 ~7倍） |
| scRNA-seq 数据 | GSE283473 脑类器官 + GSE67535 iPSC 神经元 | **无** |
| iPSC 模型 | 前脑类器官模型已发表 (eLife 2024) | hiPSC 系刚建立 (Human Cell 2025) |
| 小鼠模型 | 多种缺失小鼠模型 | Nsd2 KO 有，但无多基因缺失小鼠 |
| 主效基因 | 多基因争议（GTF2I vs GTF2IRD1 vs LIMK1） | **NSD2 共识较强** |
| "找到主效基因"的难度 | 高（多个贡献大小相似的神经基因） | **低（NSD2 占主导地位）** |

---

## 四、对 iGEM 管线的意义

### 好消息：基因筛选的任务可能比 WS 简单得多

WHS 的基因发现格局和 WS 完全不同：

- **WS**：7q11.23 区间 25-27 个基因，多基因贡献，GTF2I/LIMK1/BAZ1B/CLIP2/ELN 各负责不同表型，筛选需要复杂的多证据排名
- **WHS**：NSD2 已被确认为核心因果基因。其他基因（LETM1, NELFA, TACC3）对特异性表型有贡献，但不是"主效基因"争论的核心

### 坏消息：没有单细胞数据

如果要走和 WS 管线完全相同的路径（scRNA-seq → CNV → 表达 QC → 证据层排序），在当前是无法实现的——因为根本没有公开的 WHS scRNA-seq 数据。

### 可行路径

| 选项 | 内容 | 投入 |
|---|---|---|
| **A: 直接以 NSD2 为主效基因** | 文献已经为 NSD2 提供了很强的证据。跳过 scRNA-seq 步骤，用 ClinGen/gnomAD/HPA 证据层直接验证 NSD2 的剂量敏感性和组织表达可行性 | 低——现有管线直接可用 |
| **B: 用 Nsd2 KO 小鼠 bulk RNA-seq** | GSE232564 有 NSD2 KO 小鼠 E15.5 脑 bulk RNA-seq，可以做差异表达分析来确认 NSD2 缺失的下游效应 | 中——需要下载和分析 bulk RNA-seq |
| **C: 用已发表的 WHS hiPSC 做自我验证** | 2025 年的 hiPSC 系刚建立，没有公开的转录组数据。可以联系作者获取细胞系，自行分化+scRNA-seq | 高——几周到几个月 |
| **D: 用 HPA/GTEx 正常组织数据模拟 WHS 区间基因表达** | 在正常脑组织中看 4p16.3 区间基因的表达模式，推理缺失的影响 | 低——现有公共数据 |

---

## 参考文献

1. Kimura S et al. *Loss of NSD2 causes dysregulation of synaptic genes and altered H3K36 dimethylation in mice.* Frontiers in Genetics, 2024. GSE232564/GSE232566
2. Takada M et al. *Generation of human induced pluripotent stem cell lines derived from Wolf-Hirschhorn syndrome patients.* Human Cell, 2025. PMID: 40971060
3. Tassano E et al. *From Wolf-Hirschhorn syndrome to NSD2 haploinsufficiency: a shifting paradigm.* Italian Journal of Pediatrics, 2022. DOI: 10.1186/s13052-022-01267-w
4. Zanoni P et al. *De novo loss-of-function variants in NSD2 associate with a subset of Wolf-Hirschhorn syndrome.* Cold Spring Harbor Molecular Case Studies, 2019. DOI: 10.1101/mcs.a004044
5. Kerzendorfer C et al. *Characterizing the functional consequences of haploinsufficiency of NELF-A (WHSC2) and SLBP.* Human Molecular Genetics, 2012. DOI: 10.1093/hmg/dds033
6. Andersen EF et al. *Deletions involving genes WHSC1 and LETM1 may be necessary but not sufficient to cause Wolf-Hirschhorn syndrome.* European Journal of Human Genetics, 2014. DOI: 10.1038/ejhg.2013.192
7. Mills A et al. *Wolf-Hirschhorn Syndrome-Associated Genes Are Enriched in Motile Neural Crest Cells and Affect Craniofacial Development in Xenopus laevis.* Frontiers in Physiology, 2019.
8. Kaiyrzhanov R et al. *Bi-allelic LETM1 variants perturb mitochondrial ion homeostasis.* American Journal of Human Genetics, 2022. DOI: 10.1016/j.ajhg.2022.07.007