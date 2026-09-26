# 微缺失区间候选基因筛选管线

## 1. 阅读入口

- **负责人：** [流程、操作与文件盘点](docs/index.html)。编号章节先讲如何使用，技术细节按需展开。
- **工程验证：** [测试与技术参考](docs/reference/index.html)。

## 2. 唯一安装入口

在仓库根目录，准备 Python 3.11 后执行：

```bash
bash scripts/setup_envs.sh --pipeline-only
.venv/pipeline/bin/python scripts/test_pipeline.py
```

安装会清除并重建 `.venv/pipeline`，依赖只读取 `03_pipeline/requirements.txt`；`pyproject.toml` 的包依赖也引用同一文件。旧 `uv.lock` 已删除，历史 uv 安装/运行命令不再是当前入口。

接着按[数据准备与运行说明](../00_docs/01_guides/DATA_SETUP.html)执行三步筛选。新疾病需更换候选、显式控制基因（未设置时用 `[]` 或空控制文件）、独立输出目录；`config/pipeline.yaml` 的控制清单不能直接当作每个新疾病的控制基因。

已完成首批 12 项及源码 18 项整理。源码盘点见 Agent 记录（仅本地）及[阅读页第 5.2 节](docs/index.html#source-inventory)；测试 24 项已原位保留，见 Agent 测试盘点（仅本地）与[阅读页第 5.4 节](docs/index.html#tests-inventory)；数据 15 项已整理，见数据盘点（仅本地）和[阅读页第 5.5 节](docs/index.html#data-inventory)；输出和其余文档继续逐批盘点。旧版 `src.consensus` 已退役，当前评分入口为 `src.consensus_v2`。CNV 自动识别开发、项目合并及科学重跑继续暂停。

<a id="data-sources"></a>
## 3. 数据从哪里获得

**所有数据不入库，需从上游获取或自行生成。** 下表用于查找上游和准备新版本，不表示今天下载的数据与历史快照相同。文件放在 `03_pipeline/data/`；自备完整证据目录可用 `merge_evidence --data-dir` 指定。

| 数据 | 官方入口与获取方法 | 管线实际读取的文件名及要求 |
| --- | --- | --- |
| ClinGen 剂量敏感性 | [官方 FTP 目录](https://ftp.clinicalgenome.org/)：选择 `ClinGen_gene_curation_list_GRCh38.tsv` | 保存为 `clinGen_gene_curation_list_GRCh38.tsv`（注意本地名称大小写）；保留 `#Gene Symbol`、`Haploinsufficiency Score`、`Triplosensitivity Score` 表头及原始注释。 |
| gnomAD 约束指标 | [下载页](https://gnomad.broadinstitute.org/downloads) · [constraint 说明](https://gnomad.broadinstitute.org/help/constraint)：查找目标版本的基因约束表；当前配置注释使用 v2.1.1 | `gnomad_constraint.tsv`；需 `gene` 或 `gene_symbol`、`pLI`、`oe_lof_upper`。不能假定新版列名或统计口径兼容。 |
| HPA 组织 RNA | [官方下载页](https://www.proteinatlas.org/about/download)：选择 Tissue 下的 RNA expression (consensus)，下载并解压 | `rna_tissue_consensus.tsv`；需 `Gene name`、`Tissue`、`nTPM`。旧登记中的 `rna_expression_consensus.tsv` 不是当前读取名。 |
| HGNC 基因命名 | [官方自定义下载说明](https://www.genenames.org/help/custom-downloads/)：导出命名及历史别名字段的 TSV | `hgnc_aliases.tsv`；至少 `hgnc_id`、`symbol`，保留 `alias_symbol`、`prev_symbol`；DeepLOF 按编号转换还需要 `ensembl_gene_id`。下载字段名需核对是否符合此契约。 |

**核实边界（2026-09-25）：** 已查看 ClinGen 目录、HPA 下载页与 HGNC 字段说明；gnomAD 页面为动态页面，本次未能读取下载条目。未重新下载或替换数据，未证明本地快照与源站当前版本一致。HPA 当前页面标为 25.1；旧登记的 v23、基因数量和 `verified: 2025-09-01` 仅是历史文字，不作为核实证据。旧 ClinGen 校验和是占位符，不能用于校验。

准备新数据时，记录实际下载 URL、版本、日期和 SHA256，核对以上字段，再在独立输出目录验证；不要覆盖历史数据后仍声称复现原结果。运行审计的 `data_checksums.txt` / `run.json` 保存实际读取文件的校验和，这能追溯内容，但不能单独证明来源真实。

可选 DeepLOF 的来源与身份检查见 [技术参考中的 AI 分数契约](docs/reference/index.html)；正式替换仍暂停。可选 CNV 的 GEO / GENCODE 输入见 [技术参考中的 CNV 工作流](docs/reference/index.html)，不属于核心筛选必需下载。

旧 `config/sources.json` 已退出配置目录：内容整合到本节，原文仅在 冻结来源（仅本地）保留，运行程序不读取该登记表。

## 4. 可选扩展与 CNV 决策

DeepLOF 已有预计算分数转换与评分读取接口，但正式数据替换和科学核验仍暂停；不等于已运行 DeepLOF 模型。表达比较和遗传方式注释脚本保留，未来可评估结合到管线中，本轮未自动接入。

我们曾尝试从单细胞表达自动发现缺失区间，但真实数据未通过“找回已知区间”的检查；因此核心采用候选列表或已知区间提取。自动 CNV 开发暂停，代码保留，未来可能作为 DBTL 的探索与检验环节。原因、证据和边界见[阅读页第 5.3 节](docs/index.html#cnv-decision)。

历史标准化表已归入 `outputs/history/normalized_legacy/`，仅供追溯。新运行将标准化结果写入独立输出目录；不要写回 `data/` 或覆盖归档。核心参考表及其配置路径保持原位。
