# iGEM 2026：筛选管线与虚拟扰动工具

本仓库包含微缺失区间候选基因筛选（`03_pipeline/`）和 VirtualCellTool 扰动模拟（`05_tools/VirtualCellTool/`）。**不需要旧工作站的 `.venv`、`~/Desktop/github` 或 Kady 沙盒。** GitHub 交付内容包括核心输入、三个网页演示数据集和模型；体积较大的公开原始数据与可重算缓存不提交，按下表下载或重建。因此，“从 GitHub 克隆即可启动核心功能”与“下载可选原始数据后重跑全部上游实验”是两种不同的验收范围。

## GitHub 发布与安装

- 已实测平台：macOS arm64、Python 3.11.15。Linux/Python 3.11 的依赖安装需要独立验证；其他 Python 版本尚未验证。
- 先安装 Git LFS；克隆后执行 `git lfs pull`。核心 HGNC 表和 SCimilarity 模型等仍由 LFS 交付，克隆到的指针文件不能代替真实数据。
- `07_independent_reproduction_20260916/` 是本机验证副本，不属于发布内容。原有子项目的 `.git` 元数据也不能作为普通目录嵌套提交；发布时应使用不含嵌套 `.git` 的导出副本。
- 不要把现有 `03_pipeline/.venv` 或 `05_tools/SIGnature/.venv` 上传；它们含旧绝对路径，不能搬迁。根目录 `.gitignore` 已排除。

发布者在原项目根目录运行 `bash scripts/export_github.sh`，从新建的 `09_github_export/` 建立 GitHub 仓库，**不要直接提交原项目目录或旧的 `08_gitlab_export/`**。导出脚本排除原始大数据、生成缓存、旧环境、嵌套 `.git` 和本机验证副本，并执行核心文件检查。在 `git add` **之前**运行 `git lfs install`；提交前检查 `git lfs ls-files` 包含 `hgnc_aliases.tsv` 和 `encoder.ckpt`，且普通 Git 中没有超过 100 MiB 的文件。2026-09-18 已从 GitHub 全新克隆提交 `ee37779` 并下载 33 个 LFS 对象：核心筛选测试 22 通过/1 跳过，WBS/WHS 排名与报告产出；加入本机保留的 GSE283473 和 Norman 数据后，CNV→筛选数据流及 VirtualCellTool 18/18 API 均通过。公开数据的下载链接已核对，但尚未从源站重新下载全部数据，也未做浏览器端到端验收。

新用户克隆后在仓库根目录运行：

```bash
git lfs pull
python3 scripts/check_release.py
python3.11 --version
bash scripts/setup_envs.sh
```

`check_release.py` 默认只检查核心运行文件；下载下表中的可选数据后可用 `--with-optional-data` 检查 CNV 和 GEARS 输入。脚本只验证文件存在、非空且不是 LFS 指针，不代替来源校验或实际运行测试。

## 不入库的大数据与缓存

以下路径已由 `.gitignore` 排除，**不会在 GitHub 克隆中自动出现**。下载前请核对源站许可和可用空间；不要将解压文件重新提交。表中链接是原始数据入口，不代表本项目预处理产物可从源站直接取得。

| 用途 | 来源与本地放置方式 | 是否为核心启动必需 |
|---|---|---|
| Williams CNV 原始 10x 文件（CTRL1、WS1） | [NCBI GEO GSE283473](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE283473)；按 [`03_pipeline/docs/cnv_workflow.md`](03_pipeline/docs/cnv_workflow.md) 附录的六文件下载命令保存至 `03_pipeline/data/scrna/GSE283473/` | 否，仅可选 CNV 上游流程 |
| Williams 六样本原始文件 | 同一 [GSE283473](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE283473) 的 `GSE283473_RAW.tar`（GSM8663068–GSM8663073）；按 [`02_disease-williams/README.md`](02_disease-williams/README.md) 的样本布局放入 `02_disease-williams/01_rawdata/` | 否，历史全样本分析用 |
| 22q11.2 原始数据 | [NCBI GEO GSE244005](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE244005) 的 GSM7804653（JS001，对照）与 GSM7804654（JS002，病例）；解压到 `01_disease-22q11.2/data/` 供 `preprocess.py` 使用 | 否，历史 22q11.2 分析用 |
| GEARS Norman 数据 | [Zenodo 17252307](https://zenodo.org/records/17252307) 的 `norman.zip`（源站 MD5 `cdc41d6050e619c37fd9dd44d440e2b4`）；下载到 `05_tools/VirtualCellTool/gears_data/norman.zip`，再在仓库根目录运行下方解压命令 | 否，只有 GEARS 因果/负对照和完整 18 路 API 验收需要 |
| 生成缓存与中间文件 | GEARS 的 `norman/data_pyg/cell_graphs.pkl`、VCT 的 `data/cipher_*.npz` 会在首次使用时重算；`ms_attribution_fp16.npy` 由 `src/compute_ms_attribution.py` 生成；`03_pipeline/outputs/cnv/cnv_input.h5ad`、`02_disease-williams/03_intermediate/processed.h5ad` 分别由各自上游流程生成 | 否；首次运行可能明显更慢且更耗内存 |

```bash
unzip 05_tools/VirtualCellTool/gears_data/norman.zip -d 05_tools/VirtualCellTool/gears_data/
python3 scripts/check_release.py --with-optional-data
```

GEARS 解压后应出现 `gears_data/norman/perturb_processed.h5ad`；不要把 2.23 GB 的解压文件或约 3.66 GB 的生成缓存提交到 GitHub。筛选使用的 `03_pipeline/data/hgnc_aliases.tsv` 和网页使用的 SCimilarity `encoder.ckpt` **不在排除清单中**，由 Git LFS 提供；其上游来源分别是 [HGNC](https://www.genenames.org/help/custom-downloads/) 和 [SIGnature Zenodo 17903196](https://zenodo.org/records/17903196)。

## 安装环境

脚本在仓库内创建 `.venv/pipeline`、`.venv/vct`，并从项目内的 requirements 文件安装第三方包。需要可访问 Python 包索引的网络连接。若要运行可选 CNV 工作流，另执行：

```bash
.venv/pipeline/bin/python -m pip install -r 03_pipeline/requirements-cnv.txt
```

## 筛选示例

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

核心筛选输入随 Git/LFS 提供，不必先下载上表的 GEO 原始数据。`merge_evidence` 默认使用自身所在 `03_pipeline/data/`；如需自备证据数据，可显式传 `--data-dir`。缺少任一必需文件会报错，而不是生成空证据表。WBS 当前正对照清单为 **4 个**，实测 Top 10 为 **4/4**；历史文档中“6/6”是过时说法。WHS 旧输出由旧 `rank`/HPA 惩罚配置生成，与现行 `raw`/无惩罚配置不可逐值比较。

更多输入格式和 mode 解释见 [`03_pipeline/README.md`](03_pipeline/README.md)。CNV 是可选上游工作流；它需要 `infercnvpy`，下载六个 GEO 文件后用 `stage-samples` 重建样本布局。旧样本目录的绝对符号链接不是发布输入。

## 虚拟扰动示例

```bash
cd 05_tools/VirtualCellTool
../../.venv/vct/bin/python web/app.py
```

在浏览器访问 `http://127.0.0.1:8377/`，可切换 PBMC、MS 和 Williams 数据集。三个核心数据集与 SCimilarity 模型随 Git/LFS 交付；CIPHER 缓存被忽略，首次加载会重算，WS 可能需要更多时间和内存。GEARS 因果/负对照功能需先下载上表 Norman 数据。浏览器测试另需 `requirements-e2e.txt` 和浏览器运行时；详见 [`05_tools/VirtualCellTool/README.md`](05_tools/VirtualCellTool/README.md)。

未下载 GEARS 数据时，服务运行期间可另开终端在 `05_tools/VirtualCellTool/` 执行 `../../.venv/vct/bin/python tests_api.py --skip-gears`，验收三个数据集和其余 16/18 项。下载并解压 Norman 数据后再去掉 `--skip-gears`，运行包含 GEARS 的全部 18 项验收。

## 发布前门槛

1. 在**不含 `.venv`、旧符号链接和嵌套 `.git`** 的 `09_github_export/` 中运行 `python3 scripts/check_release.py`；核对 LFS 规则和拟提交文件没有超过 GitHub 普通 Git 的 100 MiB 限制。
2. 从 GitHub 全新克隆、`git lfs pull`，用新环境从头生成 WBS/WHS 排名并启动 VirtualCellTool；按需下载 Norman/GEO 数据再跑完整 API 与 CNV 工作流。
3. 验证下载链接、数据许可/隐私、GitHub LFS 存储与带宽后再清理旧副本。原始实验输出与旧报告保留作历史，不把它们当作当前配置的逐值基准。

本机上一轮完整核验位于未发布的 `07_independent_reproduction_20260916/INDEPENDENT_VALIDATION_REPORT.md`；不要把该目录当作克隆用户的依赖。
