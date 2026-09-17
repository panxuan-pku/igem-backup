# scRNA-seq 推断 CNV/微缺失：方法全景与文献调研

> 调研日期：2026-09-07 · 项目：iGEM SINEUP 微缺失主效基因筛选
> 关联 notebook 条目：call_be77599d909e463289e19e0c

---

## 核心结论（TL;DR）

**对于你的 1–3 Mb 胚系杂合微缺失场景，当前的 scRNA-seq CNV 推断方法几乎没有可用的现成方案。** 你的质疑是对的。

---

## 1. 方法分类

所有方法分为两类：

| 类别 | 原理 | 代表工具 | 能检测的 CNV 类型 |
|---|---|---|---|
| **表达型 (expression-centric)** | 基因在缺失区表达降低、重复区表达升高 | inferCNV, CopyKAT, SCEVAN, Clonalscope | gain / loss（只看拷贝数变化） |
| **等位基因感知型 (allele-aware)** | 同时用表达信号 + 杂合 SNP 的 BAF（B-allele frequency）偏离 | Numbat, XClone, HoneyBADGER, CaSpER | gain / loss / CN-LOH（拷贝中性杂合性丢失） |

---

## 2. 三篇主要 Benchmark 论文的关键结论

### Nature Communications (Schmid et al., 2025) — 6 方法 × 21 数据集

- **Numbat (Expr)** 和 **CopyKAT** 在 F1 分数上并列最高（≈0.57–0.59）
- **所有方法对 focal CNV（<3 Mb）的灵敏度极低**——"all scRNA-seq callers are, in general, not suitable for identifying them"
- 性能与数据集特征强相关：癌细胞数多、基因数多 → 好；CNV 覆盖率高（>75% 基因组） → 差（找不准基线）
- 表达型方法之间的相关性有时超过它们各自与 DNA 金标准之间的相关性 → 存在系统性的转录组偏差

### Precision Clinical Medicine (Chen et al., 2025) — 5 方法 × 4 平台

- **CopyKAT** 和 **CaSpER** 总体最优
- 批次效应严重：跨平台混合数据集的亚克隆识别全部失败
- 参考数据选择显著影响结果

### bioRxiv (Hou et al., 2026?) — 12 方法 × 28 数据集（最大规模）

**最终建议树：两条路**

```
有原始 BAM/FASTQ 文件?
  ├─ YES → Numbat (allele-aware, 总体最优)
  └─ NO  → CopyKAT 或 inferCNV 或 SCEVAN (expression-centric)
```

- **Numbat 是唯一能检测 CN-LOH 的同时维持高准确度的方法**
- **Numbat 不稳定**：在某些数据集上表现极差（F1 骤降），原因多为 SNP 覆盖不足
- SCEVAN 对**删除检测**最优，Numbat 对扩增检测最优
- 仿真实验：弱 CNV 信号下 Clonalscope > CopyKAT > inferCNV

---

## 3. 为什么你的场景如此困难？

| 挑战 | 原因 |
|---|---|
| **1–3 Mb 太小** | 这是 benchmark 定义的 "focal type 1" (<3 Mb)，所有方法均报告灵敏度极低。100 基因窗口覆盖 1–3 Mb 区间仅有 ~5–20 个基因，信号被窗口内非缺失基因稀释 |
| **杂合缺失（2 copies → 1 copy）** | 表达变化理论上只有 ~50%（基因剂量效应），且有剂量补偿（你的 E8 已验证）进一步抹平 |
| **胚系（所有细胞都有）** | 没有正常参照细胞在同一组织内 → 所有表达型方法都依赖"正常 vs 肿瘤"对照，你没有这个二分对照 |
| **非癌组织** | 所有方法都是为肿瘤 CNV 设计的，默认 CNV 是体细胞事件且覆盖大片区域 |

---

## 4. 四个可能方向的评估

| 方向 | 可行性 | 依据 |
|---|---|---|
| **Allele-aware 方法 (Numbat/XClone)** | 🟡 有理论优势但实际受限严重 | 需要原始 BAM + 足够的杂合 SNP + 群体单倍型。10x 3' 端测序覆盖基因 3' 端附近，SNP 密度远低于 Smart-seq2 全长转录本。BAF 信号对杂合缺失（0.5→0.5 还是 0.5→1.0？不对——杂合缺失的 BAF 是 0.5→0 或 1.0，但这需要缺失区间内确实有杂合 SNP） |
| **表达型方法的改进（更多方法对照）** | 🟡 能改进但有限 | CopyKAT 或 SCEVAN 可能比 infercnvpy 效果稍好，但根本性的表达×缺失信号弱问题无法绕过 |
| **ASE imbalance（等位基因特异性表达）** | 🟡 理论上最优但需要数据 | 需要患者在缺失区间内有杂合 SNP + 这些 SNP 在 scRNA-seq 中有足够 read coverage。你的 GSE283473 是否满足？需要实测 |
| **放弃从 scRNA-seq 寻找缺失区间** | 🟢 最省力的路径 | 已知临床区间坐标 + 基因型（CNV 芯片/WGS）永远是金标准。scRNA-seq 的角色应是验证层（该基因在脑组织中表达吗？缺失后表达变化了吗？），而不是发现层 |

---

## 5. 对你当前管线的建议

1. **已知区间基因提取**（当前做法）是正确的策略，不需要改成"自动发现缺失区间"
2. 如果一定要补自动发现，**Numbat** 是当前最佳选择（但需要原始 BAM + 足够的杂合 SNP 密度），且对 1–3 Mb 的检出率预期要设得很低
3. **ASE imbalance 方向值得做一个快速的可行性评估**：统计 GSE283473 WBS 区间内的已知杂合 SNP 覆盖情况。如果根本覆盖不到几个 SNP，就可以直接排除这条路
4. scRNA-seq 的真正价值在管线里的位置应该是 **L3 验证层**（基因在脑组织中的表达 QC、患者 vs 对照的 log2FC），而不是 CNV 发现层

---

## 参考文献

1. Schmid KT et al. *Benchmarking scRNA-seq copy number variation callers.* Nature Communications, 2025. DOI: 10.1038/s41467-025-62359-9
2. Chen X et al. *A benchmarking study of copy number variation inference methods using single-cell RNA-sequencing data.* Precision Clinical Medicine, 2025. DOI: 10.1093/pcmedi/pbaf011
3. Hou W et al. *Benchmarking scRNA-seq Copy Number Inference.* bioRxiv, 2026. PMC13105003
4. Gao T et al. *Haplotype-aware analysis of somatic copy number variations from single-cell transcriptomes.* Nature Biotechnology, 2023. DOI: 10.1038/s41587-022-01468-y (Numbat)
5. Huang R et al. *Robust analysis of allele-specific copy number alterations from scRNA-seq data with XClone.* Nature Communications, 2024. DOI: 10.1038/s41467-024-51026-0 (XClone)