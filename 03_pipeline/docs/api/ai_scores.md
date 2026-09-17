# AI Prescore — 外部服务契约 (可选)

DeepLOF / DosaCNV / DeepGenePrior 的分数都是**可选**输入；未运行时对相应基因的相应权重贡献 0（不参与 aggregate）。

## 接口（输入/输出）

**输入** — `outputs/evidence.parquet`（含 `hgnc_id`，供 AI 读取）  
**输出** — `outputs/ai_scores.csv`
- 列：`hgnc_id`, `DeepLOF_score`, `DosaCNV_score`, `DeepGenePrior_score`
- 缺失用 NaN/空

Pipeline 在每次 run 里读 `outputs/ai_scores.csv`，拼到 evidence 表。请确保 AI 分数键入 `hgnc_id`。

## 责任
- 服务运行环境（模型、依赖、GPU 等）在本工程外。
- 预计算也可以——团队内部把 AI 分数作为仅影响高权重项的输入。
