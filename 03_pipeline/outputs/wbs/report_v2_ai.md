# 微缺失主效基因筛选 — 共识排名 (consensus v2)

Normalization: **rank** · 35 genes

## Weights used

| evidence | weight (default) | weight (used) | coverage |
|---|---|---|---|
| clinGen_hi_score | 3 | 3 | 14% |
| gnomad_LOEUF | 2 | 2 | 77% |
| gnomad_pLI | 2 | 2 | 77% |
| DeepLOF_score | 1 | 1 | 80% |

⚠️ evidence columns absent or all-missing (0 contribution): DosaCNV_score, DeepGenePrior_score

HPA penalty: per-organ -2 above expr>1.0, capped at -4

## Top 10

| rank | hgnc_id | symbol | score | borda_rank |
|---|---|---|---|---|
| 1 | HGNC:4047 | FZD9 | 2.497 | 15 |
| 2 | HGNC:3722 | FKBP6 | 1.394 | 30 |
| 3 | HGNC:961 | BAZ1B | 0.926 | 4 |
| 4 | HGNC:2586 | CLIP2 | 0.671 | 5 |
| 5 | HGNC:3327 | ELN | 0.356 | 11 |
| 6 | HGNC:11433 | STX1A | 0.298 | 6 |
| 7 | HGNC:23018 | TMEM270 | 0.036 | 29 |
| 8 | HGNC:33771 | SPDYE8 | 0.000 | 20 |
| 9 | HGNC:45034 | SPDYE9 | 0.000 | 20 |
| 10 | HGNC:51506 | SPDYE10 | 0.000 | 20 |

Additive-rank vs Borda-rank Spearman ρ = **0.364** (>0.8: the two aggregation schemes largely agree)
(Borda aggregates evidence columns only; HPA penalty is additive-only.)

## 数据源校验
```
checksums shown in outputs/audit/data_checksums.txt
```