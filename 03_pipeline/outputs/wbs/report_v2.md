# 微缺失主效基因筛选 — 共识排名 (consensus v2)

Normalization: **rank** · 35 genes

## Weights used

| evidence | weight (default) | weight (used) | coverage |
|---|---|---|---|
| clinGen_hi_score | 3 | 3 | 14% |
| gnomad_LOEUF | 2 | 2 | 77% |
| gnomad_pLI | 2 | 2 | 77% |

⚠️ evidence columns absent or all-missing (0 contribution): DeepLOF_score, DosaCNV_score, DeepGenePrior_score

HPA penalty: per-organ -2 above expr>1.0, capped at -4

## Top 10

| rank | hgnc_id | symbol | score | borda_rank |
|---|---|---|---|---|
| 1 | HGNC:4047 | FZD9 | 1.926 | 15 |
| 2 | HGNC:3722 | FKBP6 | 1.037 | 31 |
| 3 | HGNC:23018 | TMEM270 | 0.000 | 19 |
| 4 | HGNC:33771 | SPDYE8 | 0.000 | 19 |
| 5 | HGNC:45034 | SPDYE9 | 0.000 | 19 |
| 6 | HGNC:51506 | SPDYE10 | 0.000 | 19 |
| 7 | HGNC:51507 | SPDYE11 | 0.000 | 19 |
| 8 | nan | ENSG00000289346 | 0.000 | 19 |
| 9 | HGNC:3327 | ELN | -0.037 | 8 |
| 10 | HGNC:961 | BAZ1B | -0.074 | 4 |

Additive-rank vs Borda-rank Spearman ρ = **0.234** (>0.8: the two aggregation schemes largely agree)
(Borda aggregates evidence columns only; HPA penalty is additive-only.)

## Leave-one-out weight tuning (positive controls)

Controls present: ELN, GTF2I (missing from candidates: TBX1, KCTD13, RAI1)

| held-out | rank | in top-N | train recall |
|---|---|---|---|
| ELN | 21 | ✗ | 1.00 |
| GTF2I | 21 | ✗ | 1.00 |

LOO hit rate: **0%** · final recall@N on all controls: 0.50

Final weights: clinGen_hi_score=3, gnomad_LOEUF=2, gnomad_pLI=2

## 数据源校验
```
checksums shown in outputs/audit/data_checksums.txt
```