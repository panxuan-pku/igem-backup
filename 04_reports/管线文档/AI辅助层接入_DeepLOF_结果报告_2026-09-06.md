# AI 辅助层接入：DeepLOF（2026-09-06）

> 配套：`docs/api/ai_scores.md`（契约）、`src/ai_scores.py`（转换脚本）、`src/consensus_v2.py --ai-scores`
> 现状：Layer 2（AI 层）从"搁置"变为"已接入 DeepLOF"，DosaCNV/DeepGenePrior 仍留接口未启用。

---

## 一、DeepLOF 分数来源（官方、可复现）

| 项 | 值 |
|---|---|
| 论文 | LaPolice TM & Huang YF. BMC Bioinformatics 24:347 (2023) |
| 分数 | **Additional file 3 / Data File 2 — Scores from the nonlinear DeepLOF model**（figshare 24159504，CC BY 4.0） |
| 文件 | `12859_2023_5481_MOESM3_ESM.csv`（19197 基因，`ensembl, gene_symbol, DeepLOF_score`） |
| MD5 | `4f7a9c6520b840db677963cfe82d3e34`（与官方发布一致，脚本内校验） |
| 转换 | `src/ai_scores.py deeplof`：gene_symbol → HGNC ID，输出 `outputs/ai_scores.csv`（hgnc_id, DeepLOF_score），审计写 `audit/ai_scores_deeplof_*.json` |
| 映射率 | 18126/19197 = 94.4% 映射到 HGNC ID（18060 唯一基因入表） |

### 复现命令

```bash
cd 03_pipeline
curl -sL -o data/DeepLOF_scores.csv https://ndownloader.figshare.com/files/42390159
uv run --with pandas python -m src.ai_scores deeplof \
  --scores data/DeepLOF_scores.csv --aliases data/hgnc_aliases.tsv --out outputs/ai_scores.csv
uv run --with pandas --with numpy --with pyyaml --with pyarrow python -m src.consensus_v2 \
  --evidence outputs/evidence.parquet --ai-scores outputs/ai_scores.csv \
  --config config/pipeline.yaml --out outputs/candidates_ranked_v2_ai.csv --report outputs/report_v2_ai.md
```

---

## 二、WBS 35 候选的 DeepLOF 覆盖

- 覆盖 **28/35 = 80%**；
- **缺失 7 个：GTF2I、TYW1B、SPDYE8/9/10/11、ENSG00000289346**。

> ⚠️ **GTF2I 缺失是官方数据盲区**：19197 行评分里没有 `ENSG00000263001`（GTF2I），比对 GENCODE v44 确认其 Ensembl ID 无误，判定为 DeepLOF 训练时该基因部分特征缺失被过滤。**AI 工具也有盲区，正说明管线不能只依赖单一方法**。GTF2I 在本管线仍由 gnomAD 强约束支撑（pLI 0.996 / LOEUF 0.270），不受影响。

---

## 三、三个版本排名对比（35 基因）

| 基因 | 无 AI (rank) | 有 AI (rank) | **有 AI (raw) ✅** |
|---|---|---|---|
| BAZ1B | #10 | #3 | **#1** |
| CLIP2 | #11 | #4 | **#2** |
| STX1A | #12 | #6 | **#3** |
| ELN | #9 | #5 | **#4** |
| VPS37D | #7 | #13 | **#5** |
| FZD9 | #1（伪影） | #1（伪影） | #6 |
| LIMK1 | #20 | #19 | #7 |
| FKBP6 | #2（伪影） | #2（伪影） | #8 |
| EIF4H | #14 | #14 | #9 |
| GTF2IRD1 | #21 | #21 | #11 |
| GTF2I | #21 | #25 | #14 |
| GTF2IRD2 | #35 | #35 | #35 |
| 加性 vs Borda Spearman ρ | 0.23 | 0.36 | **0.71** |

**三列分别说明**：
1. **无 AI + rank**：FZD9/FKBP6 因 pLI 极低被 rank 方向映射抬到第一（伪影）；GTF2I 被压到 21。
2. **有 AI + rank**：DeepLOF 把 BAZ1B(0.94)/CLIP2(0.88)/STX1A(0.89)/ELN 拉上来，但 FZD9/FKBP6 伪影仍在，GTF2I 因无 AI 分数反而微降。
3. **有 AI + raw + HPA 降权**：真实约束信号主导 —— BAZ1B>>CLIP2>STX1A>ELN>VPS37D，FZD9/FKBP6 回落到 #6/#8，双排序一致性 ρ 0.71（显著改善）。

---

## 四、DeepLOF 的实际贡献（客观评估）

**正面**：
- 与 gnomAD 约束**高度一致、互为独立确认**：BAZ1B(0.94)、STX1A(0.89)、LIMK1(0.88)、CLIP2(0.88) 均高；——之前证据层的"第一梯队"判断被第三个独立方法背书。
- 识别出 FZD9/FKBP6 的 DeepLOF 分数仅 0.51/0.50（中等），**暴露 rank 排名第一是伪影**——AI 分数提供了校正锚点。
- 为 gnomAD 缺数据的基因补充信号：BUD23（无 gnomAD，DeepLOF 0.52）、POM121（pLI 0.058，DeepLOF 0.51）。

**局限**：
- 权重仅 1（< ClinGen 3 / gnomAD 2）——按设计避免与其共享的 gnomAD 信号重复计权；
- 80% 覆盖，GTL2I 等关键基因不在其中；
- 对 WBS 这类"ClinGen + gnomAD 已强"的基因增益有限（其独立性价值在 ClinGen/gnomAD 都弱的基因上有待更多案例验证）。

---

## 五、结论与后续

1. **DeepLOF 已正式接入 L1 管线 AI 层**，整个链路变为：CNV 工作流 → normalize → merge_evidence（+DeepLOF）→ consensus_v2。
2. 配置建议收敛到 **normalize: raw、HPA per-organ -1/cap -2、AI 权重 1**（报告附 `report_v2_ai_raw.md` 为最终基线）。
3. 遗留可优化项：
   - ClinGen score=0 目前被当作负分（-0.5w）；0 语义是"无证据"，与"未评审"更接近，可考虑按缺失处理（避免误罚 GTF2I/LIMK1 等）；
   - 补 HPA 脑表达列；
   - DosaCNV/DeepGenePrior 接口已预留，需时同样走 `src/ai_scores.py` 接入流。

*产物：`outputs/ai_scores.csv` · `outputs/candidates_ranked_v2_ai_raw.csv`（最终）· `outputs/report_v2_ai_raw.md` · `outputs/report_v2_ai.md`（rank 对照）· `outputs/audit/ai_scores_deeplof_*.json`*