# 微缺失主效基因筛选 — 共识排名 (consensus v2)

Pipeline mode: **Mode D · 探索性粗筛** · Normalization: **rank** · 19 genes

## Weights used

| evidence | weight (default) | weight (used) | coverage |
|---|---|---|---|
| clinGen_hi_score | 3 | 3 | 21% |
| gnomad_LOEUF | 2 | 2 | 95% |
| gnomad_pLI | 2 | 2 | 95% |
| DeepLOF_score | 1 | 1 | 79% |

⚠️ evidence columns absent or all-missing (0 contribution): DosaCNV_score, DeepGenePrior_score

HPA penalty: per-organ -2 above expr>1.0, capped at -4

## ⚠️ 探索模式声明 (Mode D)

本区间无可信人工金标准（ClinGen 覆盖低）或已知主效基因。以下排名为**探索性粗筛**：只表示群体约束 + 表达可行性的初步排序，**不构成确定性靶点结论**。建议补充文献/实验正对照后再读此排名。

## Top 10

| rank | hgnc_id | symbol | score | borda_rank |
|---|---|---|---|---|
| 1 | HGNC:12766 | NSD2 | 3.889 | 1 |
| 2 | HGNC:26742 | NAT8L | 1.978 | 4 |
| 3 | HGNC:16822 | FAM193A | 0.600 | 2 |
| 4 | HGNC:51180 | CFAP99 | 0.200 | 13 |
| 5 | HGNC:18870 | POLN | 0.178 | 19 |
| 6 | HGNC:10067 | RNF4 | -0.311 | 6 |
| 7 | HGNC:243   | ADD1 | -0.556 | 5 |
| 8 | HGNC:13906 | MXD4 | -0.600 | 7 |
| 9 | HGNC:29334 | ZFYVE28 | -0.733 | 9 |
| 10 | HGNC:19118 | TNIP2 | -1.756 | 11 |

Additive-rank vs Borda-rank Spearman ρ = **0.479** (>0.8: the two aggregation schemes largely agree)
(Borda aggregates evidence columns only; HPA penalty is additive-only.)

## 数据源校验
```
checksums shown in outputs/audit/data_checksums.txt
```

## 🧪 实验验证建议
