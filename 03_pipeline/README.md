# 微缺失区间候选基因筛选管线

本目录包含可直接运行的 WBS/WHS 示例输入、证据表、配置、源码和测试。核心筛选不需要 GEO 单细胞原始文件；可选 CNV 工作流要按仓库根目录 README 下载 GSE283473。运行环境由仓库根目录的 `scripts/setup_envs.sh` 创建；旧 `.venv` 不属于交付内容。

## 从克隆目录运行

先在仓库根目录执行 `git lfs pull` 和 `bash scripts/setup_envs.sh`，再进入本目录：

```bash
cd 03_pipeline
../.venv/pipeline/bin/python -m pytest tests/ -q
../.venv/pipeline/bin/python -m src.normalize \
  --input input/candidates.csv --out outputs_repro/wbs_normalized.csv \
  --hgnc-alias data/hgnc_aliases.tsv
../.venv/pipeline/bin/python -m src.merge_evidence \
  --normalized outputs_repro/wbs_normalized.csv --config config/pipeline.yaml \
  --out outputs_repro/wbs_evidence.parquet --audit outputs_repro/wbs_audit
../.venv/pipeline/bin/python -m src.consensus_v2 \
  --evidence outputs_repro/wbs_evidence.parquet --ai-scores outputs/ai_scores.csv \
  --config config/pipeline.yaml --mode rank --controls input/controls_wbs.txt \
  --sensitivity --out outputs_repro/wbs_ranked.csv --report outputs_repro/wbs_report.md
```

WHS 用 `input/candidates_whs.csv`、同一个 `config/pipeline.yaml` 和对应输出路径重复这三步；`controls_whs.txt` 是否适用于该次排序应按研究目的选用。所有新输出写入 `outputs_repro/`，不会覆盖历史报告。`merge_evidence` 默认读本目录的 `data/`，也支持显式 `--data-dir`；缺少必需数据会失败，避免生成看似成功的空证据。

## 模式与解释

`src.consensus_v2` 支持 `auto`、`validate`、`rank`、`full`、`exploratory`。`rank` 用于有争议候选排序；`validate` 面向预先确定的基因；`full` 加入补偿状态集成；`exploratory` 面向未知区间，不给实验建议。配置权重在 `config/`。当前 WBS 正对照清单是 4 个，不是旧文档所写的 6 个；旧 WHS 输出使用过不同配置，不能当作当前配置的逐值基准。

AI 预评分文件 `outputs/ai_scores.csv` 是可选输入，不能替代 ClinGen、gnomAD、HPA 数据。CNV 单细胞工作流是可选上游功能，见 [`docs/cnv_workflow.md`](docs/cnv_workflow.md)；需要另装 `requirements-cnv.txt`，下载六个原始 GEO 文件，再由 `stage-samples` 重建样本布局。不要使用历史留下的、指向项目外部的样本符号链接。

实验归档与历史输出索引见 [`outputs/README.md`](outputs/README.md)。历史记录只说明当时运行条件，不保证与现行配置一致。
