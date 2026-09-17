# 微缺失主效基因筛选 — 共识排名 (consensus v2)

Pipeline mode: **Mode B · 增强筛选（排序 + 正对照检验）** · Normalization: **raw** · 35 genes

## Weights used

| evidence | weight (default) | weight (used) | coverage |
|---|---|---|---|
| DeepLOF_score | 1 | 1 | 46% |
| clinGen_hi_score | 3 | 3 | 14% |
| gnomad_LOEUF | 2 | 2 | 86% |
| gnomad_pLI | 2 | 2 | 86% |

⚠️ evidence columns absent or all-missing (0 contribution): DeepGenePrior_score, DosaCNV_score

HPA penalty: per-organ -2 above expr>1.0, capped at -4

## 正对照检验（已知主效基因位置）

| gene | in candidates | rank | top-10 | consensus | ClinGen | pLI | 补偿 |
|---|---|---|---|---|---|---|---|
| ELN | ✓ | 6 | ✓ | 0.113 | 3.0 | 2.1429e-14 | — |
| GTF2I | ✓ | 18 | ✗ | -1.696 | — | 9.9592e-01 | — |
| BAZ1B | ✓ | 11 | ✗ | 0.000 | nan | 1.0000e+00 | — |
| LIMK1 | ✓ | 17 | ✗ | -1.636 | — | 9.9937e-01 | — |

正对照 top-10 命中率: **1/4**

## Top 10

| rank | hgnc_id | symbol | score | borda_rank |
|---|---|---|---|---|
| 1 | HGNC:4047  | FZD9 | 1.160 | 20 |
| 2 | HGNC:3722  | FKBP6 | 0.927 | 30 |
| 3 | HGNC:11433 | STX1A | 0.743 | 4 |
| 4 | HGNC:18287 | VPS37D | 0.307 | 7 |
| 5 | HGNC:23018 | TMEM270 | 0.220 | 34 |
| 6 | HGNC:3327  | ELN | 0.113 | 11 |
| 7 | HGNC:33771 | SPDYE8 | 0.000 | 21 |
| 8 | HGNC:45034 | SPDYE9 | 0.000 | 21 |
| 9 | HGNC:51506 | SPDYE10 | 0.000 | 21 |
| 10 | HGNC:51507 | SPDYE11 | 0.000 | 21 |

Additive-rank vs Borda-rank Spearman ρ = **0.265** (>0.8: the two aggregation schemes largely agree)
(Borda aggregates evidence columns only; HPA penalty is additive-only.)

## 数据源校验
```
checksums shown in outputs/audit/data_checksums.txt
```

## 🧪 实验验证建议

### 第一候选验证路径: FZD9
**证据**: gnomad_LOEUF=8.3400e-01, gnomad_pLI=1.9309e-03

**补偿状态**: 未评估 (无scRNA-seq数据)

建议验证步骤:
1. qPCR 确认缺失断点包含 {sym}（在患者 gDNA 上）
2. Western blot 确认蛋白质是否不足（翻译层未补偿）
3. 如果蛋白不足 → 设计 SINEUP-FZD9 → 细胞模型测试蛋白恢复
4. 如果蛋白正常 → 切换到备选基因（见下）

### 切换策略
如果 FZD9 的蛋白质正常（翻译也补偿了），切换到以下备选:
- FKBP6
- STX1A
- VPS37D

切换标准: ≥1 项正交证据（pLI/ClinGen/表达）独立于 FZD9

### 排名不确定时的建议
前几个候选的证据等级相近。建议不直接靶向单一基因，而是先在患者细胞系中做 shRNA rescue 实验:
- 恢复每个候选基因的表达
- 看哪个恢复表型最好
- 用这个正对照结果更新管线的权重
