# 微缺失主效基因筛选 — 共识排名 (consensus v2)

Pipeline mode: **Mode C · 全栈筛选（排序 + 补偿状态）** · Normalization: **raw** · 35 genes

## Weights used

| evidence | weight (default) | weight (used) | coverage |
|---|---|---|---|
| DeepLOF_score | 1 | 1 | 46% |
| clinGen_hi_score | 3 | 3 | 14% |
| gnomad_LOEUF | 2 | 2 | 86% |
| gnomad_pLI | 2 | 2 | 86% |

⚠️ evidence columns absent or all-missing (0 contribution): DeepGenePrior_score, DosaCNV_score

HPA penalty: per-organ 0.0 above expr>9999.0, capped at 0.0

## mRNA compensation status (scRNA-seq, when available)

| rank | gene | compensation ratio | class | SINEUP potential |
|---|---|---|---|---|
| 1 | STX1A | 0.856 | partial_high | ▲ partial |
| 2 | VPS37D | 1.123 | overcompensated | ✗ not compensated |
| 3 | ELN | 3.138 | overcompensated | ✗ not compensated |
| 4 | BAZ1B | 1.408 | overcompensated | ✗ not compensated |
| 5 | CLIP2 | 1.087 | overcompensated | ✗ not compensated |
| 6 | EIF4H | 1.302 | overcompensated | ✗ not compensated |
| 7 | MLXIPL | 0.619 | unreliable | ? unknown |
| 8 | LIMK1 | 0.961 | full | ★ ideal |
| 9 | GTF2I | 1.276 | overcompensated | ✗ not compensated |
| 10 | CLDN3 | 0.444 | unreliable | ? unknown |

## 正对照检验（已知主效基因位置）

| gene | in candidates | rank | top-10 | consensus | ClinGen | pLI | 补偿 |
|---|---|---|---|---|---|---|---|
| ELN | ✓ | 3 | ✓ | 4.113 | 3.0 | 2.1429e-14 | overcompensated |
| GTF2I | ✓ | 9 | ✓ | 2.304 | — | 9.9592e-01 | overcompensated |
| BAZ1B | ✓ | 4 | ✓ | 4.000 | nan | 1.0000e+00 | overcompensated |
| LIMK1 | ✓ | 8 | ✓ | 2.364 | — | 9.9937e-01 | full |

正对照 top-10 命中率: **4/4**

## Top 10

| rank | hgnc_id | symbol | score | borda_rank |
|---|---|---|---|---|
| 1 | HGNC:11433 | STX1A | 4.743 | 4 |
| 2 | HGNC:18287 | VPS37D | 4.307 | 7 |
| 3 | HGNC:3327  | ELN | 4.113 | 11 |
| 4 | HGNC:961   | BAZ1B | 4.000 | 5 |
| 5 | HGNC:2586  | CLIP2 | 3.899 | 6 |
| 6 | HGNC:12741 | EIF4H | 3.303 | 8 |
| 7 | HGNC:12744 | MLXIPL | 2.448 | 9 |
| 8 | HGNC:6613  | LIMK1 | 2.364 | 1 |
| 9 | HGNC:4659  | GTF2I | 2.304 | 2 |
| 10 | HGNC:2045  | CLDN3 | 2.293 | 12 |

Additive-rank vs Borda-rank Spearman ρ = **0.781** (>0.8: the two aggregation schemes largely agree)
(Borda aggregates evidence columns only; HPA penalty is additive-only.)

## 数据源校验
```
checksums shown in outputs/audit/data_checksums.txt
```

## 🧪 实验验证建议

### 第一候选验证路径: STX1A
**证据**: DeepLOF_score=0.89, gnomad_LOEUF=2.9300e-01, gnomad_pLI=9.7850e-01

**补偿状态**: partial_high

建议验证步骤:
1. qPCR 确认缺失断点包含 {sym}（在患者 gDNA 上）
2. Western blot 确认蛋白质是否不足（翻译层未补偿）
3. 如果蛋白不足 → 设计 SINEUP-STX1A → 细胞模型测试蛋白恢复
4. 如果蛋白正常 → 切换到备选基因（见下）

### 切换策略
如果 STX1A 的蛋白质正常（翻译也补偿了），切换到以下备选:
- VPS37D
- ELN
- BAZ1B

切换标准: ≥1 项正交证据（pLI/ClinGen/表达）独立于 STX1A

### 排名不确定时的建议
前几个候选的证据等级相近。建议不直接靶向单一基因，而是先在患者细胞系中做 shRNA rescue 实验:
- 恢复每个候选基因的表达
- 看哪个恢复表型最好
- 用这个正对照结果更新管线的权重
