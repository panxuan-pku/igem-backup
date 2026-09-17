# Outputs 索引

本项目所有生成文件的统一入口。上游项目文档见根目录 `AGENTS.md`；用户上传的原始文件仍在 `user_data/`。

## 目录

- `data/` — 分析产出的数据表（CSV）
  - `microdeletion_birth_prevalence.csv` — 14 个微缺失综合征出生患病率（含 CI/范围与来源）
  - `microdeletion_denovo_fraction.csv` — 各综合征 de novo 比例

- `scripts/` — 分析与构建脚本（可复现）
  - `microdeletion_prevalence.py` — 生成全部流行病学图与数据表（输出到 `figures/` 与 `data/`）

- `figures/` — 图表（每张含 PNG / PDF / SVG 三格式）
  - `microdeletion_birth_prevalence.*` — 出生患病率汇总柱状图
  - `22q11_2_forest.*` — 22q11.2 多研究森林图（含发病率）
  - `microdeletion_denovo_fraction.*` — de novo 比例图
  - `microdeletion_birth_vs_adult.*` — 出生 vs 成人患病率对比

- `reports/` — 汇报与报告（Markdown / Word）
  - `microdeletion_prevalence_report.md` — 微缺失流行病学数据报告（含来源与注意事项）
  - `微缺失主效基因筛选方法汇报.docx`（Word 汇报，~8 页）
  - `工程化指导书_微缺失主效基因筛选管线.md`（工程化实施文档）
  - `集成方案_L1证据层与现有平台融合.md`（L1–VCT 集成方案）
  - 其余管线/平台总结报告见目录内文件名
  - `管线文档/文献调研_虚拟细胞药物效应与基因扰动_2026-09-12.md`（虚拟细胞能否承担药物效应/基因扰动模拟的可行性判定）
  - `管线文档/WHS主效基因NSD2证据链与叙事指南_2026-09-12.md`（WHS→NSD2 确立过程的证据链 + WBS/WHS 分工叙事指南 + 引文修正）

- `literature/` — 文献笔记与书目
  - `paper_summaries/` — 论文结构化摘要（DeepLOF、GETgene-AI 等）
  - `bibliography/` — 文献检索书目（30 篇，DOI 均验证；`virtual_cell_review_bibliography.md` — 虚拟细胞调研书目，DOI 状态逐条标注）

- `deliverables/` — 可直接交付的成品
  - `igem_epidemiology_package/` — iGEM wiki 自包含页面（内嵌 SVG + 表格 + 参考文献），见包内 `README.md`
  - `igem_epidemiology_package.zip` — 上述打包的 zip

- `igem_gene_pipeline/` — iGEM 筛选管线工程骨架（Python 包，内部结构不变）
  - `README.md` / `config/` / `src/` / `tests/` / `docs/` / `data/` / `outputs/`

## 使用习惯

新的分析/汇报文件不要直接放 `outputs/` 根目录；放入对应子目录（`data/`、`scripts/`、`figures/`、`reports/`、`literature/`、`deliverables/`）并更新本索引。用户新上传的文件仍进入 `user_data/`。