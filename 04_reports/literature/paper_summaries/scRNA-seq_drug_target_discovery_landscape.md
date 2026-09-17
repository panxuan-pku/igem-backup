# 前沿单细胞测序数据在药物靶点筛选中的应用全景

> 调研日期：2026-09-07 · 关联：管线架构预审质询 #0
> 来源：Nature Reviews Drug Discovery (2023), Frontiers Drug Discovery (2024), Nature Cell Biology (2025) 等

---

## 核心结论

**scRNA-seq 在靶点发现中的主流应用全部集中在——肿瘤和免疫疾病——这两类疾病有共同特征：存在"疾病 vs 正常"的差异表达信号，且靶点通常是"抑制一个被疾病上调的基因"。这与你的 SINEUP 应用场景（胚系缺失→剂量减半→需要上调一个基因）在逻辑上是反向的。**

---

## 一、scRNA-seq 在药物发现中的六大应用方向

| 方向 | 做什么 | 典型案例 | 与你的场景的相关性 |
|---|---|---|---|
| **1. 细胞亚型发现** | 从疾病组织中识别新的细胞类型/状态，作为靶点来源 | Villani et al. (2017) 发现新树突状细胞亚群; Sade-Feldman et al. (2018) 发现免疫治疗响应相关 T 细胞状态 | 🟡 间接相关——可帮你理解脑类器官中有哪些细胞类型表达你的候选基因 |
| **2. Perturb-seq** | 大规模 CRISPR 扰动 + scRNA-seq 读out，直接建立基因→表型的因果链接 | Ursu et al. (2022) 在癌细胞中大规模表型化编码变异; 2024-2025 年扩展到组合扰动 | 🔴 **不可用**：所有 Perturb-seq 数据来自癌细胞系，你的发育/神经基因不在训练空间中 |
| **3. 耐药机制发现** | 比较耐药 vs 敏感细胞的转录组，找出驱动耐药的基因 | Cohen et al. (2021) 在多发性骨髓瘤中发现耐药通路和靶点; Tanaka et al. (2018) 发现铂类耐药基因 COX7B | 🔴 不适用——你的场景不存在"耐药"的概念 |
| **4. 配体-受体/细胞通讯** | 分析细胞间互作网络，找到可药物干预的信号轴 | 多种 CellChat/NicheNet 分析肿瘤微环境中的免疫逃逸信号 | 🟡 间接相关——可分析脑类器官中候选基因参与哪些细胞间通讯 |
| **5. GWAS-eQTL 共定位** | 将 GWAS 风险位点定位到特定细胞类型和基因 | scRNA-seq 数据 × GWAS 信号 → 细胞类型特异性因果基因 | 🟡 间接相关——如果某个微缺失病有 GWAS 数据 |
| **6. 药物响应预测** | 用 scRNA-seq 特征预测细胞/患者对药物的敏感性 | scGSDR (2025) 深度学习框架预测抗癌药物在单细胞水平的响应 | 🔴 不适用——需要大规模药筛数据，且逻辑是预测抑制而非激活 |

---

## 二、Perturb-seq：靶点筛选的黄金标准——为什么你无法使用

Perturb-seq 是目前唯一能从 scRNA-seq 中建立**因果**基因-表型关系的方法。原理：

```
CRISPR 文库（数千个基因）→ 每个细胞敲除/敲低一个基因
→ scRNA-seq 读取每个细胞的转录组状态
→ 比较"敲了基因 X 的细胞"vs"未敲的细胞"
→ 如果敲了 X 导致表型逆转 → X 是因果靶点
```

**为什么对你不可用**：

| Perturb-seq 的需求 | 你的场景 |
|---|---|
| 使用的细胞类型 | K562/A549/癌细胞系 → 不表达发育/神经基因 |
| 测量的表型 | 增殖、凋亡、耐药 → 不相关 |
| 方向 | KO/KD → 抑制 → "敲了哪个基因让癌细胞死了？" | 你需要 **upregulate** → "上调哪个基因能恢复缺失表型？" |
| 基因空间 | ~5000 个在癌细胞中表达的基因 | 你的微缺失区间基因大多不在其中 (GEARS 退场: 41 个基因只有 4 个) |

**在 Nature Cell Biology (2025) 和 Nature Biotechnology (2022) 中描述的 Perturb-seq 最新进展（组合扰动、多模态读out）——全部基于癌细胞系。**

---

## 三、"用 scRNA-seq 发现靶点"的成功故事——全部在一个方向上

成功的靶点发现故事共同的特征：

1. **疾病 vs 正常有明确的差异表达信号**：癌细胞 vs 正常细胞、耐药 vs 敏感、疾病组织 vs 健康组织
2. **靶点是被疾病上调的基因**：靶向 = 抑制 → 恢复 → 表型逆转
3. **细胞类型是靶点发现的核心**：不是"什么基因重要"，而是"什么基因在哪种细胞类型中驱动疾病"

**你的场景在这三个维度上都有结构性不匹配**：

| | 成功故事 | 你的场景 |
|---|---|---|
| 差异表达 | 有明显 DE 信号（癌 vs 正常） | mRNA 隐身，Δattr≈0 |
| 靶向方向 | 抑制被上调的基因 | 上调被剂量减半的基因 |
| 细胞类型 | 肿瘤细胞/免疫细胞 | 脑类器官中的发育神经细胞 |

---

## 四、一篇关键论文的结论（medRxiv 2024）

**"Estimating the impact of single-cell RNA sequencing of human tissues on drug target validation"**

这篇论文量化了一个问题：scRNA-seq 数据用于靶点验证（而非发现）有多大价值？

结论：scRNA-seq 对靶点**验证**（确认靶点在相关组织中表达）有显著价值，但对靶点**发现**（从零找到新靶点）的独立增量有限。最大的贡献在于：
- 确认靶点在目标组织的目标细胞类型中确实表达（降低脱靶风险）
- 排除在关键安全器官（肝、心、肾）中高表达的靶点（安全性过滤）

**这与你的管线当前状态完全一致——scRNA-seq 的合理角色就是验证和过滤，不是发现。**

---

## 五、对你管线的启示

| 你能做的 | 你不能做的 |
|---|---|
| 用 scRNA-seq 验证候选基因在靶组织中的表达 | 用 scRNA-seq 从零发现缺失区间 |
| 用 scRNA-seq 确定候选基因在哪些细胞类型中表达 | 用 scRNA-seq 推断基因的因果性 |
| 用 scRNA-seq 检查患者细胞中基因表达是否被补偿 | 用 Perturb-seq 预测上调后的表型（域外） |
| 用 HPA 多组织数据做组织可行性 + 安全性过滤 | — |

**这是一个诚实的限制，不是管线的失败。** 整个前沿都在往同一个方向走——scRNA-seq 的靶点价值在于"细胞类型分辨率"和"人类组织原位验证"，而不是"从零发现因果靶点"。后者是遗传学（GWAS、家系研究、ClinGen）和 Perturb-seq（因果实验）的领地。

---

## 参考文献

1. Van de Sande B et al. *Applications of single-cell RNA sequencing in drug discovery and development.* Nature Reviews Drug Discovery, 2023. DOI: 10.1038/s41573-023-00688-4
2. *Single-cell technology for drug discovery and development.* Frontiers in Drug Discovery, 2024. DOI: 10.3389/fddsv.2024.1459962
3. *Decoding heterogeneous single-cell perturbation responses.* Nature Cell Biology, 2025. DOI: 10.1038/s41556-025-01626-9
4. Ursu O et al. *Massively parallel phenotyping of coding variants in cancer with Perturb-seq.* Nature Biotechnology, 2022. DOI: 10.1038/s41587-021-01160-7
5. *Estimating the impact of single-cell RNA sequencing of human tissues on drug target validation.* medRxiv, 2024. DOI: 10.1101/2024.04.04.24305313
6. *SCTA: An Agentic Framework for Stable and Interpretable Target Gene Discovery from Single-Cell RNA Sequencing.* arXiv, 2025. 2607.23821
7. *Single-Cell Transcriptomics and Computational Frameworks for Target Discovery in Cancer.* Targets, 2025. DOI: 10.3390/targets4010006