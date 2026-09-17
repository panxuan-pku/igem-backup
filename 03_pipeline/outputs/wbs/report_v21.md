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

⚠️ ClinGen 仅覆盖该区间 14% 的基因。以下排序主要依赖 gnomAD 约束分数——这可能偏向'群体遗传学上不耐受'的基因，漏掉'组织特异性但未被 Curators 研究过'的重要基因。

⚠️ 该区间基因数较多 (35) 且排名前 3 的证据分数差距较小 (gap=1.57, σ=1.63)。可能存在多个表型贡献基因。单一排名不应被解译为'唯一的因果基因'。建议对前 N 个候选进行正交验证。

## 数据源校验
```
checksums shown in outputs/audit/data_checksums.txt
```

## ⚖️ 权重敏感性分析

- 8 次权重扰动测试 (±1 每个证据列)
- 最大排名偏移: 10 位
- 扰动导致 Top-3 变化的次数: 5/8
- 排名稳健性: **low**

> ⚠️ 排名对权重选择敏感。建议考虑前 N 个候选进行正交验证而非直接选择排名 #1 作为唯一靶点。

## 🧪 实验验证建议

### 第一候选验证路径: FZD9
**证据**: gnomad_LOEUF=8.3400e-01, gnomad_pLI=1.9309e-03, DeepLOF_score=0.51

**补偿状态**: 未评估 (无scRNA-seq数据)

建议验证步骤:
1. qPCR 确认缺失断点包含 {sym}（在患者 gDNA 上）
2. Western blot 确认蛋白质是否不足（翻译层未补偿）
3. 如果蛋白不足 → 设计 SINEUP-FZD9 → 细胞模型测试蛋白恢复
4. 如果蛋白正常 → 切换到备选基因（见下）

### 切换策略
如果 FZD9 的蛋白质正常（翻译也补偿了），切换到以下备选:
- FKBP6
- BAZ1B
- CLIP2

切换标准: ≥1 项正交证据（pLI/ClinGen/表达）独立于 FZD9

### 排名不确定时的建议
前几个候选的证据等级相近。建议不直接靶向单一基因，而是先在患者细胞系中做 shRNA rescue 实验:
- 恢复每个候选基因的表达
- 看哪个恢复表型最好
- 用这个正对照结果更新管线的权重
