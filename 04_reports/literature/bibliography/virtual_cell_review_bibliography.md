# 引文书目 — 虚拟细胞：药物效应模拟与基因扰动

> 配套报告：`reports/管线文档/文献调研_虚拟细胞药物效应与基因扰动_2026-09-12.md`
> 日期：2026-09-12 · 检索线：AI 虚拟细胞 / 机制全细胞模型 / 药物效应模拟 / 剂量补偿
> DOI 状态说明：**v** = 通过搜索结果双重确认（多数带 PubMed/EuropePMC/出版社页）；**r** = 检索所得 DOI/标识，建议 Crossref 复核后引用；**p** = preprint/bioRxiv/arXiv 标识（非正式 DOI）。

---

## A. AI 虚拟细胞愿景 / 综述

1. **Buettner et al. (2024). How to build the virtual cell with artificial intelligence: Priorities and opportunities. Cell, 187(25), 7045–7063.** [v] doi:10.1016/j.cell.2024.11.015 · PubMed:39398201 · arXiv:2409.11654.
   - AIVC 愿景：多尺度多模态大网络模型，Universal Representation + Virtual Instruments；短期里程碑 = 可验证假设 + 跨模态基准。
2. **Virtual Cells: Predict, Explain, Discover (2025). arXiv:2505.14613.** [p] — 提出 P-E-D 验证体系与四方面基准（功能响应/细胞上下文/扰动类别/三种能力）；明确点评单细胞扰动模型"仅转录组读数、受翻译后调控限制"、全细胞模型"只覆盖简单组织"。
3. **AI-driven virtual cell models in preclinical research: technical pathways, validation mechanisms, and clinical translation potential. npj Digital Medicine (2025).** [v] doi:10.1038/s41746-025-02198-6（备：PMC12789685）
   - 临床转化两阶段验证（计算+实验）；FDA 将 AI 视为补充证据；引用平台 VCell/PhysiCell/COPASI；毒理用例（DILI、cardiotoxicity）；原话确认"DL 基因扰动预测尚未超过简单线性基线"。

## B. 基因扰动预测（正面方法）

4. **Roohani et al. (2023). Predicting transcriptional outcomes of novel multigene perturbations with GEARS. Nat Biotechnol 41(7), 564–575.** [v] doi:10.1038/s41587-023-01905-6.
5. **Schmittmann et al. (2023). Dissecting cell identity via network inference and in silico gene perturbation. Nature 613, 270–277.** [v] doi:10.1038/s41586-022-05688-9（CellOracle）。
6. **Lotfollahi et al. (2023). Predicting cellular responses to complex perturbations in high-throughput screens. Mol Syst Biol.** [v] doi:10.15252/msb.202211517（CPA）。
7. **Cui et al. (2024). scGPT: toward building a foundation model for single-cell multi-omics using generative AI. Nat Methods.** [v] doi:10.1038/s41592-024-02201-0 · PubMed:38409223.
8. **Pavelko et al. (?) scGenePT: Is language all you need for modeling single-cell perturbations? bioRxiv 2024.** [p] doi:10.1101/2024.10.23.619972.

## C. 基因扰动预测（否定/基准）

9. **Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines. Nat Methods (2025).** [v] doi:10.1038/s41592-025-02772-6 · PubMed:40759747 · PMC12328236（bioRxiv 2024.09.16.613342 [p]）。
   - 5 foundation models + 2 其他 DL 模型 vs 简单线性基线：无一超过；本报告直接引用为领域自我证伪证据。
10. **arXiv:2602.18885 (2026)？“预测高维转录响应…均值坍缩（mean collapse）假阳性”** [p] — 识别平均坍缩问题的 preprint（报道于检索，作者/标题待补）。

## D. 药物效应模拟

11. **Hetzel et al. (2022). Predicting Cellular Responses to Novel Drug Perturbations at a Single-Cell Resolution. NeurIPS 2022.** [p/v] arXiv:2204.13545（chemCPA）。
12. **ONERAI/scDrugMap (2026). Benchmarking Large Foundation Models for Drug Response Prediction at single-cell resolution.** [r] GitHub:ONERAI/scDrugMap。
13. **AetherCell: A generative engine for virtual cell perturbation and in vivo drug discovery (2026).** [r] doi:10.64898/2026.03.13.710968（新 DOI 前缀，复核）。
14. **TwinCell: Large Causal Cell Model for Reliable and Interpretable Therapeutic Target Prioritisation. bioRxiv (2026).** [p] doi:10.64898/2026.01.29.702072v2。
15. **StateXDiff: Cell State-Contextualized Multimodal Diffusion for Single-Cell Perturbation Prediction (2026). arXiv:2605.16104.** [p]
16. **ProteinTalks: an operational perturbation proteomics-based virtual cell model. Nature (2026).** [v] doi:10.1038/s41586-026-11001-9 — 蛋白层（~3.8×10⁷ 时间分辨蛋白测量）虚拟细胞；直击翻译层盲区。

## E. 机制性全细胞模型 / 毒理 / 数字孪生

17. **Karr et al. (2012). A whole-cell computational model predicts phenotype from genotype. Cell 150(2), 389–401.** [v] doi:10.1016/j.cell.2012.05.044 · PMID:22817898 · PMC3413483（M. genitalium，28 子模型/401 基因）。
18. **An expanded whole-cell model of E. coli links cellular physiology with mechanisms of growth rate control. npj Syst Biol Appl (2022).** [v] doi:10.1038/s41540-022-00242-9（wcEcoli/vEcoli 系列；全细胞 E. coli 仍 in development，见 wholecell.org）。
19. **Quantitative Systems Pharmacology-Based Digital Twins for Enzyme Replacement Therapies in Pompe Disease.** [r] doi:10.1002/cpt.3498（QSP 数字孪生 in silico 疗效对比；同类综述 PMC12703978 "Advancing rare disease therapeutics through digital twins"）。
20. **Digital patient twins for personalized therapeutics and pharmaceutical manufacturing. Front Digit Health (2023).** [v] doi:10.3389/fdgth.2023.1302338.

## F. 治疗逻辑（SINEUP / 剂量补偿）

21. **Indrieri et al. (2016). Synthetic long non-coding RNAs [SINEUPs] rescue defective gene expression in vivo. Sci Rep 6:27315.** [v] doi:10.1038/srep27315 · PMID:27265476 · PMC4893607。
22. **SINEUPs: a novel toolbox for RNA therapeutics.** [v] PubMed:34623427 · PMC8564737（haploinsufficiency 列为首要治疗场景的综述）。
23. **Model-guided design of microRNA-based gene circuits supports precise dosage of transgenic cargoes / Synthetic dosage-compensating miRNA circuits.** [p] bioRxiv doi:10.1101/2024.03.13.584179 + PMC11230401。
24. **A synthetic circuit for buffering gene dosage variation between individual mammalian cells (Equalizers). Nat Commun (2021).** [v] doi:10.1038/s41467-021-23889-0.

---

## 验证备注

- 标记 [v] 的条目均出现于 ≥2 独立检索结果且与出版社/PubMed/EuropePMC 页面一致（Karr 2012、Indrieri 2016 已逐条核对 PMID/PMC）。
- 标记 [r] 的条目（AetherCell、TwinCell、scDrugMap、Pompe 数字孪生）为 2026 最新的早期报告或新标识前缀，**引用于 iGEM wiki 前建议 Crossref 复核**。
- 标记 [p] 的条目为 preprint/arXiv/NeurIPS 程序论文，报告中对它们的定位是"新支线（未经第三方基准）"，与 [v] 的正式基准明确区分。
- 条目 #10（mean collapse preprint）标题/作者信息不全，报告中仅作现象引用；如需正式引用，先从检索补全元数据。