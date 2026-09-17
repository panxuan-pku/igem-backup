# 微缺失主效基因筛选 — 共识排名 (consensus v2)

Normalization: **rank** · 19 genes

## Weights used

| evidence | weight (default) | weight (used) | coverage |
|---|---|---|---|
| clinGen_hi_score | 3 | 3 | 21% |
| gnomad_LOEUF | 2 | 2 | 89% |
| gnomad_pLI | 2 | 2 | 89% |
| DeepLOF_score | 1 | 1 | 79% |

⚠️ evidence columns absent or all-missing (0 contribution): DosaCNV_score, DeepGenePrior_score

HPA penalty: per-organ -2 above expr>1.0, capped at -4

## Top 10

| rank | hgnc_id | symbol | score | borda_rank |
|---|---|---|---|---|
| 1 | HGNC:26742 | NAT8L | 2.161 | 4 |
| 2 | HGNC:16822 | FAM193A | 0.816 | 1 |
| 3 | HGNC:51180 | CFAP99 | 0.200 | 14 |
| 4 | HGNC:18870 | POLN | 0.184 | 19 |
| 5 | HGNC:12766 | NSD2 | 0.000 | 3 |
| 6 | HGNC:10067 | RNF4 | -0.141 | 6 |
| 7 | HGNC:243   | ADD1 | -0.353 | 5 |
| 8 | HGNC:13906 | MXD4 | -0.443 | 7 |
| 9 | HGNC:29334 | ZFYVE28 | -0.576 | 9 |
| 10 | HGNC:19118 | TNIP2 | -1.651 | 11 |

Additive-rank vs Borda-rank Spearman ρ = **0.395** (>0.8: the two aggregation schemes largely agree)
(Borda aggregates evidence columns only; HPA penalty is additive-only.)

## 数据源校验
```
checksums shown in outputs/audit/data_checksums.txt
```

## 🧪 实验验证建议

### 第一候选验证路径: NAT8L
**证据**: gnomad_LOEUF=4.5700e-01, gnomad_pLI=8.6458e-01, DeepLOF_score=0.88

**补偿状态**: 未评估 (无scRNA-seq数据)

建议验证步骤:
1. qPCR 确认缺失断点包含 {sym}（在患者 gDNA 上）
2. Western blot 确认蛋白质是否不足（翻译层未补偿）
3. 如果蛋白不足 → 设计 SINEUP-NAT8L → 细胞模型测试蛋白恢复
4. 如果蛋白正常 → 切换到备选基因（见下）

### 切换策略
如果 NAT8L 的蛋白质正常（翻译也补偿了），切换到以下备选:
- FAM193A
- CFAP99
- POLN

切换标准: ≥1 项正交证据（pLI/ClinGen/表达）独立于 NAT8L

### 排名不确定时的建议
前几个候选的证据等级相近。建议不直接靶向单一基因，而是先在患者细胞系中做 shRNA rescue 实验:
- 恢复每个候选基因的表达
- 看哪个恢复表型最好
- 用这个正对照结果更新管线的权重
