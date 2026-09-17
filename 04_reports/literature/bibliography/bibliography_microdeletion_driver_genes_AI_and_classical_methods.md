# Literature Search: AI and non-AI methods for identifying the major-effect (driver) genes of chromosomal microdeletion syndromes

**Topic (translated):** AI tools or non-AI tools/methods for identifying the major-effect genes (主效基因) of chromosomal microdeletion disorders (染色体微缺失病).

**Scope & assumptions:**
- "主效基因 (major-effect gene)" is interpreted as the dosage-sensitive / haploinsufficient driver gene(s) within a microdeletion critical region that causally account for the core syndrome phenotype.
- The search covers two method families: (a) classical/non-AI approaches (smallest-region-of-overlap mapping, positional cloning, animal-model functional screens, population-genetic constraint scores, expert curation) and (b) AI/machine-learning approaches (haploinsufficiency prediction, CNV pathogenicity classification, network-based gene prioritization, LLM-assisted triage).
- Landmark syndrome-specific discoveries (22q11.2, 7q11.23, 16p11.2, 2p15p16.1) are included as examples of how driver genes were actually established.

**Search record (reproducibility):**
- Date: September 1, 2025.
- Databases/sources queried: web search aggregation over scholarly sources (PubMed/PMC, Springer Nature, ScienceDirect, Wiley, PLOS, Frontiers, bioRxiv, medRxiv); direct verification via **Crossref REST API**, **NCBI PubMed E-utilities**, **Europe PMC REST API**, and Semantic Scholar (rate-limited). Web of Science and Google Scholar were not directly queried (no API access in this environment); content from those indices was surfaced via the aggregated web search instead.
- Queries used (verbatim, 12 total): "chromosomal microdeletion syndrome driver gene prioritization machine learning"; "identifying dosage-sensitive genes within microdeletion syndromes computational methods"; "haploinsufficiency prediction gene 22q11.2 deletion syndrome critical region"; "minimal critical region mapping microdeletion syndrome candidate genes review"; "haploinsufficiency prediction machine learning HIPred Huang 2010 model genomic features"; "pLI LOEUF gnomAD gene constraint score dosage sensitivity landmark"; "16p11.2 deletion driver gene KCTD13 zebrafish mouse model"; "ClinGen dosage sensitivity curation workflow single gene dosage 2020"; "TBX1 DiGeorge syndrome 22q11 deletion major driver gene mouse knockout 2001"; "Deciphering Developmental Disorders exome haploinsufficiency DDG2P new genes Nature 2017"; "Williams-Beuren syndrome 7q11.23 elastin critical region gene discovery"; "deep learning copy number variant pathogenicity prediction 2024 CNV classification ACMG".
- All DOIs below were verified against Crossref or PubMed metadata on the search date; discrepancies found during verification are flagged in the notes.

---

## 1. Results by theme

### Theme A — Classical, non-AI identification of driver genes in microdeletion syndromes

**A1. Syndrome-specific landmark studies (primary research)**

1. **Ewart AK, Morris CA, Atkinson D, et al. (1993).** "Hemizygosity at the elastin locus in a developmental disorder, Williams syndrome." *Nature Genetics* 5:11–16. DOI: 10.1038/ng0993-11.
   - *Primary research.* Established the first driver gene (ELN) of a classical microdeletion syndrome by showing hemizygosity at the elastin locus in Williams syndrome and linking ELN to supravalvular aortic stenosis — the template for "candidate gene from deleted region + phenotype correlation."

2. **Osborne LR, Martindale D, Scherer SW, et al. (1996).** "Identification of genes from a 500-kb region at 7q11.23 that is commonly deleted in Williams syndrome patients." *Genomics* 35:328–337. DOI: 10.1006/geno.1996.0469.
   - *Primary research.* Positional cloning of the Williams-Beuren critical region; ELN accounted for vascular features while other genes (e.g., LIMK1) were proposed for cognitive features — illustrating the multi-gene reality of "contiguous gene" syndromes.

3. **Merscher S, Funke B, Epstein JA, et al. (2001).** "TBX1 is responsible for cardiovascular defects in velo-cardio-facial/DiGeorge syndrome." *Cell* 104:619–629. DOI: 10.1016/S0092-8674(01)00247-1.
   - *Primary research.* Using mouse genetic mapping (chromosomal deletions in the syntenic region), identified TBX1 as the major driver of cardiovascular defects in 22q11.2 deletion syndrome. **Note:** first author is Merscher, not Lindsay (a common miscitation; verified via Crossref).

4. **Jerome LA & Papaioannou VE (2001).** "DiGeorge syndrome phenotype in mice mutant for the T-box gene, Tbx1." *Nature Genetics* 27:286–291. DOI: 10.1038/85845.
   - *Primary research.* Complementary mouse knockout confirming Tbx1 haploinsufficiency reproduces the DiGeorge phenotype; with ref. 3, established TBX1 as the principal 22q11.2 driver gene.

5. **Lindsay EA, Vitelli F, Su H, et al. (2001).** "Tbx1 haploinsufficiency in the DiGeorge syndrome region causes aortic arch defects in mice." *Nature* 410:97–101. DOI: 10.1038/35065105.
   - *Primary research.* Independent confirmation of the TBX1 dosage mechanism via engineered mouse deletions — the classic "mouse-model narrowing of a critical region" strategy.

6. **Golzio C, Willer JR, Talkowski ME, et al. (2012).** "KCTD13 is a major driver of mirrored neuroanatomical phenotypes of the 16p11.2 copy number variant." *Nature* 485:363–367. DOI: 10.1038/nature11091.
   - *Primary research.* Overexpressed/knocked down each of the 29 genes in the 16p11.2 interval in zebrafish embryos; KCTD13 alone recapitulated the mirrored head-size phenotypes (microcephaly in duplication, macrocephaly in deletion) — the paradigm for high-throughput in vivo screening of an entire critical region.

7. **Bagheri H, Badduke C, Qiao Y, et al. (2016).** "Identifying candidate genes for 2p15p16.1 microdeletion syndrome using clinical, genomic, and functional analysis." *JCI Insight* 1:e85461. DOI: 10.1172/jci.insight.85461.
   - *Primary research.* Combined shortest-region-of-overlap mapping across patients with genomic and functional data to nominate candidate genes (BCL11A, REL, USP34, XPO1) — a modern, integrative version of the classical SRO method.

8. **Miceli M, Failla P, Saccuzzo L, et al. (2023).** "Trait-driven analysis of the 2p15p16.1 microdeletion syndrome suggests a complex pattern of interactions among candidate genes." *Genes & Genomics* 45:495–508. DOI: 10.1007/s13258-023-01369-7.
   - *Primary research/analysis.* Shows incomplete penetrance and multi-gene interactions complicate single-driver-gene attribution even after SRO refinement.

**A2. Population-genetic constraint scores as evidence for dosage sensitivity (primary/methods research)**

9. **Samocha KE, Robinson EB, Sanders SJ, et al. (2014).** "A framework for the interpretation of de novo mutation in human disease." *Nature Genetics* 46:944–950. DOI: 10.1038/ng.3050.
   - *Methods paper.* Introduced observed-vs-expected de novo mutation models (and missense z-scores) — a statistical foundation for gene-level intolerance inference.

10. **Lek M, Karczewski KJ, Minikel EV, et al. (Exome Aggregation Consortium) (2016).** "Analysis of protein-coding genetic variation in 60,706 humans." *Nature* 536:285–291. DOI: 10.1038/nature19057.
    - *Methods/resource.* Introduced pLI (probability of loss-of-function intolerance), widely used to prioritize haploinsufficient genes within microdeletion regions.

11. **Karczewski KJ, Francioli LC, Tiao G, et al. (2020).** "The mutational constraint spectrum quantified from variation in 141,456 humans." *Nature* 581:434–443. DOI: 10.1038/s41586-020-2308-7.
    - *Methods/resource.* gnomAD constraint metrics including LOEUF; LOEUF < 0.35 is a standard cut-off for LOF-intolerant genes and is incorporated in clinical CNV interpretation.

12. **Wright CF, Fitzgerald TW, Jones WD, et al. (DDD study) (2015).** "Genetic diagnosis of developmental disorders in the DDD study: a scalable analysis of genome-wide data." *The Lancet* 385:1305–1314. DOI: 10.1016/S0140-6736(14)61705-0.
    - *Primary research.* Scalable clinical-genomic pipeline diagnosing children with developmental disorders; demonstrated the complementarity of CNV and sequence-variant diagnosis. **Verified correction:** venue is The Lancet, not Nature Genetics.

13. **Deciphering Developmental Disorders Study (2017).** "Prevalence and architecture of de novo mutations in developmental disorders." *Nature* 542:433–438. DOI: 10.1038/nature21062.
    - *Primary research.* Exome meta-analysis (4,293 trios + 3,287 published) showing enrichment of damaging de novo mutations in developmentally important (haploinsufficient) genes — connects constraint metrics to disease-gene discovery.

**A3. Expert curation frameworks**

14. **ClinGen Dosage Sensitivity Working Group (ongoing; SOP v2).** ClinGen Dosage Sensitivity curation process for haploinsufficiency/triplosensitivity evidence. URL: https://clinicalgenome.org/docs/dosage-sensitivity-curation-sop-v2/
    - *Curated resource.* The reference standard for manual, evidence-based gene-level dosage-sensitivity classification (haploinsufficiency score 0–3); serves as the benchmark against which computational predictors are validated.

15. **McDonald-McGinn DM, et al. (1993–updated).** "22q11.2 Deletion Syndrome." *GeneReviews*. URL: https://www.ncbi.nlm.nih.gov/books/NBK1523/
    - *Expert review.* Canonical clinical summary; TBX1 as the principal driver for the core phenotype with modifier genes still debated.

### Theme B — AI / machine-learning methods

**B1. Predicting gene haploinsufficiency (the core computational task)**

16. **Huang N, Lee I, Marcotte EM, Hurles ME (2010).** "Characterising and predicting haploinsufficiency in the human genome." *PLoS Genetics* 6:e1001154. DOI: 10.1371/journal.pgen.1001154.
    - *Primary research.* Foundational ML model (logistic regression on genomic, evolutionary, functional, network features) trained on known HI vs. CNV-tolerant "haplosufficient" genes; the template for all later HI predictors.

17. **Shihab HA, Rogers MF, Campbell C, Gaunt TR (2017).** "HIPred: an integrative approach to predicting haploinsufficient genes." *Bioinformatics* 33:1751–1757. DOI: 10.1093/bioinformatics/btx028.
    - *Methods paper.* ML integration of Ensembl + ENCODE features; deliberately avoids PPI-network features to reduce study bias toward well-characterized genes.

18. **Liu Z & Huang YF (2023).** "Deep multiple-instance learning accurately predicts gene haploinsufficiency and deletion pathogenicity (DosaCNV)." *bioRxiv* preprint. DOI: 10.1101/2023.08.29.555384. PMCID: PMC10491176 (bioRxiv-in-PMC record).
    - *Methods paper (preprint).* Attention-based deep multiple-instance learning jointly predicts gene haploinsufficiency and deletion pathogenicity; claims superior short-deletion/gene-level resolution over single-evidence predictors. **Flag:** at the search date, PubMed/Europe PMC indexed only the bioRxiv preprint; a peer-reviewed version could not be verified — treat accordingly.

19. **Rahaie M, Rabiee R, Alinejad-Rokny H (2023).** "DeepGenePrior: A deep learning model for prioritizing genes affected by copy number variants." *PLOS Computational Biology* 19:e1011249. DOI: 10.1371/journal.pcbi.1011249.
    - *Methods paper.* Deep-learning gene prioritization for genes within CNVs, focused on brain disorders; addresses the gap that genome-wide prioritization is dominated by prior knowledge and false positives.

20. **LaPolice TM & Huang YF (2023).** "An unsupervised deep learning framework for predicting human essential genes from population and functional genomic data (DeepLOF)." *BMC Bioinformatics* 24:347. DOI: 10.1186/s12859-023-05481-z.
    - *Methods paper.* Bayesian deep model combining a feature-based beta prior with a gnomAD likelihood; unsupervised and specifically improves prediction for *short* genes — relevant to pinpointing driver genes in small microdeletions.

21. **Collins RL, Glessner JT, Porcu E, et al. (2022).** "A cross-disorder dosage sensitivity map of the human genome." *Cell* 185:3041–3055. DOI: 10.1016/j.cell.2022.06.036.
    - *Primary research (large-scale).* Meta-analysis of rare CNVs in ~1 million individuals; ensemble ML identified 3,635 highly dosage-sensitive genes and showed convergence of rare CNVs and damaging coding variants at dosage-sensitive loci — currently the largest genome-wide empirical dosage-sensitivity map.

**B2. ML/deep-learning CNV pathogenicity classification (variant-level tools)**

22. **Schuetz M, Ceyhan Ö, Antoniou K, et al. (2024).** "CNVoyant: a machine learning framework for accurate and explainable copy number variant classification." *Scientific Reports* 14:22038. DOI: 10.1038/s41598-024-72470-4.
    - *Methods paper.* Explainable multi-class ML classifier for CNV clinical significance aligned with ACMG-style categories.

23. **Sládeček T, Gažiová M, Kucharík M, et al. (2023).** "Combination of expert guidelines-based and machine learning-based approaches leads to superior accuracy of automated prediction of clinical effect of copy number variations (MarCNV)." *Scientific Reports* 13:9753. DOI: 10.1038/s41598-023-37352-1.
    - *Methods paper.* Hybrid ACMG-guideline + ML approach; reports better accuracy than either alone — evidence that rules-plus-ML hybrids outperform pure ML for clinical CNV triage.

24. **Lv H, Chen J, Xiong H, et al. (2023).** "dbCNV: deleteriousness-based model to predict pathogenicity of copy number variations." *BMC Genomics* 24:126. DOI: 10.1186/s12864-023-09225-4.
    - *Methods paper.* Aggregates per-gene/per-region deleteriousness into CNV scores; part of the ClassifyCNV/X-CNV/StrVCTVRE/dbCNV tool family for CNV prioritization.

25. **Middelkamp S, Vlaar JM, Giltay J, et al. (2019).** "Prioritization of genes driving congenital phenotypes of patients with de novo genomic structural variants." *Genome Medicine* 11:74. DOI: 10.1186/s13073-019-0692-0.
    - *Primary research.* Combined phenotype (HPO) matching, chromatin interaction data, and functional SV-effect prediction to nominate driver genes in 16/39 (41%) patients with de novo SVs — a phenotype-aware, computational-plus-curation workflow.

26. **Liu C, Chen X, Jiang Y, et al. (2026, online ahead).** "Tissue-specific gene dosage disruption is a key feature and pathogenic mechanism of structural variants in the human genome (PathoSV)." *Genome Medicine*. DOI: 10.1186/s13073-026-01653-7.
    - *Methods paper.* Introduces a Transcript Disruption Ratio to capture tissue-specific dosage effects of SVs. **Flag:** Crossref lists a 2026 publication year (ahead-of-print at the search date, Sept 2025); included because it represents the newest methodological direction but noted as very recent/early.

**B3. AI-assisted literature and knowledge triage**

27. **Gu A & Chen JY (2025).** "GETgene-AI: a framework for prioritizing actionable cancer drug targets." *Frontiers in Systems Biology* 5:1649758. DOI: 10.3389/fsysb.2025.1649758.
    - *Methods paper (adjacent field).* Although cancer-focused, it exemplifies the emerging pattern of coupling network-based gene prioritization with LLM (GPT-4o)-assisted literature triage — a template transferable to microdeletion driver-gene nomination. Included to represent the LLM-assisted prioritization direction.

### Theme C — Reviews and synthesis

28. **Watson CT, Marques-Bonet T, Sharp AJ, Mefford HC (2014).** "The genetics of microdeletion and microduplication syndromes: an update." *Annual Review of Genomics and Human Genetics* 15:215–244. DOI: 10.1146/annurev-genom-091212-153408.
    - *Review.* Comprehensive synthesis of how genomic technologies moved discovery from phenotype-driven karyotype/FISH to unbiased array/sequencing, and the shift from single-driver to multi-gene models of microdeletion syndromes.

29. **Motahari Z, Moody SA, Maynard TM, LaMantia AS (2019).** "In the line-up: deleted genes associated with DiGeorge/22q11.2 deletion syndrome: are they all suspects?" *Journal of Neurodevelopmental Disorders* 11:7. DOI: 10.1186/s11689-019-9267-z.
    - *Review.* Systematic appraisal of all ~40 protein-coding genes in the 22q11.2 deleted region; argues most phenotypes are polygenic within the interval, with TBX1 necessary but not sufficient.

30. **Goldenberg P (2018).** "An update on common chromosome microdeletion and microduplication syndromes." *Pediatric Annals* 47:e198–e203. DOI: 10.3928/19382359-20180419-01.
    - *Review (clinical).* Clinician-oriented overview of recurrent syndromes; useful for phenotypic scope but not method-focused.

---

## 2. Key findings per source — evidence level

- **Primary research** (experimental or large-cohort): refs 1–8, 12–13, 21, 25. These actually *demonstrated* driver genes (TBX1, ELN, KCTD13, BCL11A/REL/USP34/XPO1) or built empirical dosage maps.
- **Methods/tool papers** (primary research of a computational kind): refs 9–11, 16–20, 22–24, 26–27. These propose predictors whose claims rest on benchmarking, not new biological validation.
- **Reviews/curated resources**: refs 14–15, 28–30. Secondary sources used for consensus framing.

## 3. Major themes and points of consensus

1. **Microdeletion syndromes are mostly not single-gene disorders.** Across 22q11.2, 7q11.23, 16p11.2, and 2p15p16.1, the modern consensus is that one principal driver gene (TBX1, ELN, KCTD13) explains the core phenotype but that full expressivity involves additional genes in the interval (refs 2, 8, 28, 29).
2. **Population-genetic constraint is the de facto computational baseline.** pLI/LOEUF-style observed-vs-expected models (refs 9–11), plus the Collins et al. 2022 dosage map (ref 21), are the standard non-AI/statistical way to nominate dosage-sensitive genes genome-wide, and ClinGen dosage curation (ref 14) is the accepted human benchmark.
3. **ML predictors broadly agree with, and extend beyond, constraint scores.** HI predictors (refs 16–18, 20) reproduce known haploinsufficient genes and add functional annotation; newer deep models (refs 18–20) specifically claim better resolution for short genes and small deletions — precisely the regime relevant to microdeletions.
4. **Hybrid rules-plus-ML outperforms either alone for clinical CNV interpretation** (refs 23–25), and explainability is increasingly demanded (ref 22).

## 4. Controversies and conflicting evidence

- **Single-driver vs. oligogenic models.** Even for TBX1/22q11.2, reviews argue most phenotypes are polygenic within the interval (ref 29), and 2p15p16.1 studies show candidate-gene effects with incomplete penetrance and interaction (refs 7–8) — contradicting the simple "one driver gene per syndrome" framing.
- **Study bias in training data.** HIPred (ref 17) explicitly warns that network-based HI predictors perform best on well-studied genes; DeepGenePrior (ref 19) and DeepLOF (ref 20) echo that supervised models inherit label leakage and ascertainment bias — so reported accuracies are likely optimistic.
- **Publication/validation asymmetry for AI tools.** Several AI CNV tools are benchmarked against data that overlap their training/annotation sources; the MarCNV hybrid result (ref 23) suggests pure-ML superiority claims should be read skeptically.
- **Preprint maturity.** DosaCNV (ref 18) is a preprint at the search date; its deep multiple-instance-learning gains are not yet peer-reviewed.

## 5. Gaps in current knowledge

1. **Mechanism bridging:** computational scores (pLI/LOEUF/ML) nominate dosage-sensitive genes, but connecting a nominated driver gene to a specific syndrome trait still requires functional studies (zebrafish/mouse) — no validated end-to-end pipeline exists (refs 6–8).
2. **Tissue-specific dosage effects** are only now being modeled (PathoSV, ref 26); most HI scores are tissue-agnostic, while microdeletion phenotypes are tissue-specific.
3. **Regulatory/non-coding drivers** within microdeletions (enhancers, chromatin topology effects) are under-modeled; Middelkamp et al. (ref 25) is one of few phenotype-aware attempts.
4. **Evaluation standards:** no independent, held-out benchmark for driver-gene prioritization in microdeletions; most tools self-benchmark on overlapping public sets.
5. **LLM-assisted triage is immature** for this domain — demonstrated in cancer target prioritization (ref 27) but not yet systematically applied or validated for microdeletion driver genes.

---

## 6. Verification notes / caveats

- All DOIs verified against Crossref or PubMed metadata on 2025-09-01. Items with flags: DosaCNV (preprint only, ref 18); PathoSV (2026 ahead-of-print, ref 26); Merscher-not-Lindsay authorship correction (ref 3); Wright et al. 2015 venue is The Lancet, not Nature Genetics (ref 12).
- Web of Science and Google Scholar were not directly accessible in this environment; coverage from those indices was approximated via the aggregated scholarly web search. Citation counts were not systematically collected (ranking above reflects field-standing plus recency, not a formal bibliometric sort).
- This is a scoping-style search, not a full PRISMA systematic review: no dual screening, and result counts per database were not recorded for every query.
