# igem_gene_pipeline/outputs — 实验结果与报告索引

> 本目录为管线运行产物。按实验主题归档；**原始运行入口文件原地保留**（`evidence.parquet`、`ai_scores.csv`、`cnv/`、`audit/`），以便重新运行。

## 目录结构

```
outputs/
├── evidence.parquet        # WBS 主证据面板（L1 merge_evidence 输出，73 字段；程序入口，不移动）
├── ai_scores.csv           # DeepLOF 全基因预计算分数（19197 基因；可选 AI 层输入）
├── audit/                  # 主实验审计（data_checksums.txt + ai_scores_deeplof.json）
├── cnv/                    # CNV 工作流产物（GSE283473；config 引用路径，不移动）
│   ├── cnv_input.h5ad      #   16000×19669 处理矩阵
│   ├── segments_{standard,fine,all}.csv   # segment 发现结果
│   ├── interval_gene_expression_qc.csv    # 已知区间基因表达 QC
│   ├── candidates*.csv / auto_segment_genes.csv
│   └── cnv_report.md
├── wbs/                    # ★ WBS 主实验（williams_7q11.23, 35 基因）
│   ├── candidates_ranked_v2*.csv   # v2 排名（含 AI 变体）
│   ├── candidates_ranked_v21.csv   # v2.1 排名
│   └── report_v2*.md / report_v21.md
├── whs/                    # ★ WHS 实验（whs_4p16.3, 19 基因）
│   ├── evidence_whs_{A,B}.parquet   # A=修复前证据(NSD2 gnomAD 缺失) / B=修复后(HGNC 别名解析)
│   ├── candidates_ranked_whs_{A,B,B_noai}.csv
│   ├── report_whs_{A,B,B_noai}.md
│   └── audit_whs_{A,B}/             # 各次数据校验和
├── mode/                   # ★ 六 mode 验证（2026-09-13）
│   ├── evidence_wbs_modeA.parquet   # WBS 证据面板
│   ├── compensation_wbs.csv         # GSE283473 mRNA 补偿状态（33 基因）
│   ├── ranked_wbs_mode{A,B,C}.csv + report_wbs_mode{A,B,C}.md   # WBS: 验证/排序/全栈
│   ├── ranked_whs_mode{A,B,D}.csv + report_whs_mode{A,B,D}.md   # WHS: 验证/排序/探索
│   ├── audit_wbs_modeA/
│   └── diagnostics/                 # 中间诊断产物（raw 归一化 / 无 HPA 惩罚对照，保留不删除）
```

## 关键结果速览

| 实验 | 位置 | 关键结论 |
|---|---|---|
| WBS v2/v2.1 排名 | `wbs/` | BAZ1B/CLIP2/STX1A/ELN top；raw 归一化修正后正对照命中改善（PROJECT_LOG #2/#3） |
| WHS 实证（修复前→后） | `whs/` | NSD2 #5 → #1；gnomAD 符号别名缺口修复（PROJECT_LOG #11） |
| 六 mode 历史验证 | `mode/` | 当时报告 WBS 正对照 6/6；当前清单只有 4 个，独立复测为 Top10 4/4。WHS 的旧输出与现行配置不同；NSD2 全 mode #1（PROJECT_LOG #13） |

## 约定

- 重新生成：`python -m src.merge_evidence … --out outputs/evidence.parquet` 等命令详见上层 `README.md`。
- 新实验产物请放入对应主题子目录（或新建 `mode_*`），不要直接落在本目录根级，并更新本索引。
