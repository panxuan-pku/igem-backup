# 微缺失主效基因筛选 — 共识排名 (consensus v2)

Normalization: **raw** · 35 genes

## Weights used

| evidence | weight (default) | weight (used) | coverage |
|---|---|---|---|
| clinGen_hi_score | 3 | 3 | 14% |
| gnomad_LOEUF | 2 | 2 | 77% |
| gnomad_pLI | 2 | 2 | 77% |
| DeepLOF_score | 1 | 1 | 80% |

⚠️ evidence columns absent or all-missing (0 contribution): DosaCNV_score, DeepGenePrior_score

HPA penalty: per-organ -1 above expr>1.0, capped at -2

## Top 10

| rank | hgnc_id | symbol | score | borda_rank |
|---|---|---|---|---|
| 1 | HGNC:961 | BAZ1B | 3.000 | 4 |
| 2 | HGNC:2586 | CLIP2 | 2.822 | 5 |
| 3 | HGNC:11433 | STX1A | 2.681 | 6 |
| 4 | HGNC:3327 | ELN | 2.450 | 11 |
| 5 | HGNC:18287 | VPS37D | 2.259 | 7 |
| 6 | HGNC:4047 | FZD9 | 1.650 | 15 |
| 7 | HGNC:6613 | LIMK1 | 1.292 | 1 |
| 8 | HGNC:3722 | FKBP6 | 1.253 | 30 |
| 9 | HGNC:12741 | EIF4H | 1.245 | 8 |
| 10 | HGNC:2045 | CLDN3 | 0.969 | 10 |

Additive-rank vs Borda-rank Spearman ρ = **0.711** (>0.8: the two aggregation schemes largely agree)
(Borda aggregates evidence columns only; HPA penalty is additive-only.)

## 数据源校验
```
checksums shown in outputs/audit/data_checksums.txt
```