# Paper Summary: GETgene-AI — a framework for prioritizing actionable cancer drug targets

**Paper:** Gu A & Chen JY. "GETgene-AI: a framework for prioritizing actionable cancer drug targets." *Frontiers in Systems Biology* 5:1649758 (2025). DOI: 10.3389/fsysb.2025.1649758. Received 19 June 2025; accepted 15 Sep 2025; published 29 Sep 2025.

The PDF extracted cleanly and appears complete (16 pages, ~2.5 of which are references), so this summary is based on the full paper.

---

## 1. Research objective and hypothesis

**Objective:** Build a computational framework that prioritizes actionable cancer drug targets by combining network-based prioritization, auxiliary genomic modalities, and LLM-assisted literature review — overcoming three identified limitations of existing practice: (a) manual/static curation that does not scale to multi-omics data, (b) PPI-centrality-only methods that ignore tissue-specific genomic features, and (c) single-metric thresholds (fold change, mutation frequency) that are arbitrary and sample-biased.

**Hypothesis (the authors'):** The **G.E.T. strategy** — integrating mutation/genotype–phenotype evidence (**G List**), differential expression (**E List**), and known drug-target status (**T List**), then iteratively re-ranking via PPI-network expansion and augmenting with GPT-4o literature review — will systematically prioritize actionable therapeutic targets better than single-modality baselines. Pancreatic cancer (PDAC) serves as the case study.

## 2. Study design and methods

- **Initial lists.** G list: 2,493 genes from PAGER (nCoCo coherence 5–100, 844 genes), cBioPortal (CNA ≥ 8.2% or mutation ≥ 2.8%, 1,000 genes), and COSMIC (mutation ≥ 20%, 649 genes), unified. E list: top 2,504 genes with |logFC| > 0.25 from a GEO microarray of 45 tumor vs. 45 non-tumor PDAC samples (dataset cited inconsistently as **GSE29735 in §2.1.2 and GSE28735 in §3.2/Fig 2**; same 45/45 design — likely a typo, but not clarified). T list: 131 genes from DrugBank queries for drugs indicated in pancreatic cancer (manually filtered to exclude supportive-care agents).
- **Network expansion.** BEERE (Biological Entity Expansion and Ranking Engine; HAPPI-2.0 PPI nearest-neighbor expansion + PageRank/ant-colony ranking), run independently on the GET, GT (G∩T), and E lists, top 500 genes retained per iteration, 3 iterations, then merged into an Initial GET list and re-prioritized to a Final GET list. Independent expansion is justified as preventing dilution of modality-specific signal (example: MYC, TNF).
- **Figure 1 counts:** Initial G 2,493 / E 2,000 / T 131 genes (note: Methods say E list = 2,504 genes — another internal inconsistency).
- **GPT-4o literature assessment.** 5,091 PubMed abstracts (meta-analyses, clinical trials, systematic reviews only) uploaded to a custom GPT; a 400-point rubric (functional significance, research popularity, treatment effectiveness, protein structure; 100 each) yields a **GPT-4 score**. Citations manually verified; hallucination corrections re-prompted. **GPT-4 scores are not in the final RP score.**
- **RP score (final ranking).** Weighted sum of: GT list score (0.329), CNA TCGA (0.201), E list (0.088), GET list (0.085), mutation frequency TCGA (0.079), CNA UTSW (0.048), mutation frequency UTSW (−0.023), and organ-safety expression scores (brain −0.054, kidney −0.081, GI −0.095, liver −0.101). Weights were calibrated by Spearman correlation of each modality against two benchmarks on a separately compiled clinical-trial gene set (357 drugs / 253 genes): clinical-trial count (for genomic/network features) and adverse-event frequency (for tissue expression).
- **Benchmarking/diagnostics.** Compared against **GEO2R** (logFC ranking alone on the same GEO dataset) and **STRING** (degree centrality in KEGG hsa0512); headline validation metric = fraction of each method's top 50 genes **"experimentally validated"** (criteria not formally defined). Qualitative comparison to **Open Targets** (top-15 overlap). Sensitivity analysis with looser/tighter CNA/mutation cutoffs. Manual literature verification of the **top 250 RP-ranked genes**; authors report finding no false positives. RP-LIT and GPT-LIT = scores normalized by PubMed hit count for "Gene + Pancreatic Cancer."
- **Statistics.** Spearman correlations between GPT-4 and network rankings.

## 3. Key findings and results

**Evidence-backed (as reported in the paper):**

- **Top ranking (Table 2, RP score):** PIK3CA (34.8), MYC (30.1), SRC (20.0), EGFR (18.2), CDK1 (15.9), PRKCA (15.3), TNF, LCK, JAK2, MAPK1, AURKB, **KRAS only 12th (8.7)** — authors note KRAS's demotion to its low Expression score despite >90% PDAC mutation prevalence. GPT-4 score ordering differs (MYC #1, SRC #2, EGFR #3), and Spearman ρ between GPT-4 score and: weighted RP score = **0.291**; Expression list score = 0.478; combined BEERE scores = 0.457; GET list = 0.454; GT list = 0.444.
- **Benchmarking vs. alternatives (top-50 “experimental validation” rate):** GETgene-AI 49/50 vs. GEO2R 30/50 (authors call this "**38% improvement**") and vs. STRING 46/50 ("**6% improvement**"). Note: these are absolute percentage-point gains; the corresponding relative gains are ~63% and ~6.5%, so the "38%" headline mixes metrics. Top-15 validation: GETgene-AI 15/15, STRING 15/15, GEO2R 7/15 (Fig/Table 3).
- **Novelty claims (Table 5):** PIK3CA flagged as having PDAC clinical-trial involvement; PRKCA, LCK, MAPK8 marked as preclinical (in vitro/in vivo); **ITGA4, PRKCB, KCNA(1) marked "Novel and unstudied in PDAC"** — e.g., KCNA ranked 34th with, per the authors, zero PDAC PubMed articles and three in cancer broadly. LCK (rank 9) cited as having only four PDAC papers. RP-LIT/GPT-LIT normalizations surface under-studied high scorers (e.g., PRKCA RP-LIT 1.702, ITGA4 2.298).
- **GPT-4o contribution:** reported **~80% reduction in literature-review time** (self-reported, un-referenced); GPT-4 did not improve the experimental-validation rate; there are two **inconsistent correlation reports** for GPT-4 vs. weighted score (ρ = 0.291 in §2.7; the same table lists 0.457 as GPT-4 vs. *combined BEERE list scores* — and §3.3 restates GPT-4 vs. weighted score as +0.457).
- **Sensitivity analysis:** top-250 membership stable under ±cutoff shifts; only 11 genes (all ranked outside top 150; e.g., PLOD1–3, PAM, C1QA/B) changed.
- **False-positive handling:** genes without cancer functional relevance are systematically deprioritized; paper reports that none of the top 250 were judged false positives on manual review.

**Speculation/aspiration by the authors (flagged as such in the paper):**
- "GETgene-AI provides a versatile and robust platform for accelerating cancer drug discovery" and improves "patient outcomes" — not demonstrated beyond the computational benchmark.
- Adaptability to breast/lung cancer and non-cancer diseases (Alzheimer's, Parkinson's) — stated as future work/vision, not tested.
- The prioritized "novel" targets (ITGA4, PRKCB, KCNA1) "warrant further investigation" — consistent with their absence in PDAC literature, but no wet-lab validation is performed.
- Expectation that GPT-4o accuracy will improve with more training data — conjecture.

## 4. Limitations

**Acknowledged by the authors:**
- Top-ranked targets require experimental validation (none performed in this paper — named as the critical next step, e.g., CRISPR knockouts and in vitro drug-response assays).
- Reliance on public datasets may introduce biases from incomplete/inconsistent annotation.
- GPT-4o hallucination risk necessitated manual verification; the authors counsel cautious integration into automated pipelines.
- Manual literature verification is limited to the top 250; beyond that, manual burden becomes infeasible (an operational rather than principled bound).

**Additional limitations I notice (not raised in the paper):**
- **Circular/soft validation metric:** the headline "experimental validation of the top 50" is not operationalized (source/criteria unstated), and the validation set overlaps the very literature/databases (DrugBank, PubMed) used to construct the rankings. GEO2R is benchmarked on expression-only data — a comparison designed to be won by the richer framework.
- **KRAS at rank 12** in a PDAC prioritization could equally be construed as a construct-validity failure as a strength; the paper only presents the charitable reading.
- **Weight calibration circularity:** RP-score weights are tuned against clinical-trial counts/adverse events, which are themselves related to the T list and to the benchmark used for evaluation; no held-out validation.
- **Internal numerical inconsistencies** (noted above): GSE29735 vs. GSE28735 for the E-list dataset; E list size 2,504 (methods) vs. 2,000 (Fig. 1); GPT-4–RP correlation 0.291 vs 0.457 across sections. None change the qualitative claims, but they suggest loose review.
- **Minor pipeline/responsibility issues:** key cutoffs are explicitly heuristic (e.g., CNA 8.2% partly justified by "only 21 sets of CNA signatures in 97% of tumors"), and "empirically filtered to top 500" × 3 iterations is ad hoc; convergence rationale is post hoc.
- The 80% literature-review efficiency gain and "no false positives in top 250" are self-assessed without a measured comparator (no timed manual baseline; no independent reviewer).
- Comparison with Open Targets is qualitative (top-15 overlap narrative) rather than a controlled benchmark.
- GPT-4o input was restricted to meta-analyses/clinical trials/systematic reviews on PubMed — curated-serious-literature bias; abstracts only, no full text.

## 5. Conclusions and significance

The authors conclude that the modular G.E.T. design plus BEERE network refinement yields a robust, cancer-type-specific target-prioritization scheme that outranks expression-only (GEO2R) and PPI-only (STRING) baselines on their validation metric, and that GPT-4o safely accelerates (but does not replace) literature triage. The proposed significance is a scalable workflow bridging computation and translation; concrete candidate outputs for PDAC — floor-level rankings (PIK3CA, MYC, SRC, EGFR, CDK1, PRKCA) plus "novel" calls (ITGA4, PRKCB, KCNA1) — are offered as testable hypotheses rather than validated biology. Claims of "improved patient outcomes" or disease-general robustness exceed what the paper demonstrates; the demonstrated scope is a pancreatic-cancer in silico case study.

## 6. Fit within the broader field

GETgene-AI sits squarely in the network-medicine/gene-prioritization lineage: PPI propagation and expansion (BEERE from the same group's HAPPI/HAPPI-2.0 resources, kin to HotNet/network-propagation methods), multi-criteria integrative prioritization platforms (Open Targets), and single-dimension baselines (logFC/GEO2R; STRING degree centrality). Its incremental contributions are: (i) the explicit G/E/T three-stream design with *independent* modality expansion before merging (a sensible bias-control choice), (ii) an explicit **safety/opportunity filter via negative weights on organ-essential expression**, and (iii) early, bounded use of an LLM (GPT-4o) as a literature-triage front end with citation-verification — which keeps it outside the score, addressing hallucination concerns in a way most LLM-for-prioritization proposals do not. Against Open Targets, its claim is cancer-type specificity over general association breadth — plausible but demonstrated only qualitatively. The framework is best read as a well-organized *prioritization and triage workflow* (from a two-person group, one a mentored student club member) that consolidates known components, rather than a new algorithmic advance; its headline quantitative wins rest on a soft, circular validation metric and would need a controlled benchmark plus wet-lab follow-through (which the authors themselves identify as the next step) to substantiate.

---

*Summary prepared from the full text of the uploaded PDF; all numbers and claims refer to statements in the paper. Items flagged as authors' aspiration/speculation are labeled accordingly. Inconsistencies noted are between statements inside the paper itself, not external facts.*
