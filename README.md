# iGEM 2026：候选基因筛选与虚拟扰动工具

**第一次使用：下载公开参考数据，完成一次 Williams 综合征已知区间的候选排名。** 不需要预先准备候选表、模型或单细胞矩阵。所有数据在运行时下载或生成，不随仓库交付。

## 1. 快速开始

准备 **Python 3.11、Git 和可访问公开数据网站的网络**。以下命令使用 macOS/Linux 的 Bash；目前实测平台为 macOS arm64。

```bash
git clone https://github.com/panxuan-pku/igem-backup.git
cd igem-backup
bash scripts/setup_envs.sh --pipeline-only
.venv/pipeline/bin/python scripts/run_quickstart.py
```

若已下载仓库，从仓库根目录执行后两条命令。安装只需做一次；安装脚本会重建 `.venv/pipeline`。Python 不在默认位置时，使用 `IGEM_PYTHON=/path/to/python3.11 bash scripts/setup_envs.sh --pipeline-only`。

运行过程会显示四步进度：**下载参考数据 → 生成区间候选 → 合并证据并排名 → 生成网页报告**。首次参考数据下载约 54 MiB；环境安装另需下载依赖。耗时取决于网络。环境安装后可以多次运行筛选，每次使用新目录，不覆盖旧结果。

## 2. 查看结果

成功后，终端会打印 `report.html` 的完整地址，用浏览器打开即可。所有本次文件保存在：

```text
03_pipeline/outputs_repro/quickstart_williams_<运行时间>/
├── report.html       ← 先看这里：候选排名、证据覆盖、阅读说明
├── ranked.csv        ← 完整排名与注释，可用表格软件打开
├── candidates.csv    ← 由本次公开注释生成的候选与来源
├── manifest.json     ← 下载地址、时间、SHA256、完成状态
├── config.yaml       ← 本次实际配置
├── downloads/        ← 新下载的原始参考文件
└── sources/          ← 解压后供管线使用的参考表
```

`rank` 越小越靠前，`consensus_score` 是配置下的相对得分，不是患病概率。空值表示缺少相应证据。**这一步完成研究候选排序，不代表基因因果验证或治疗效果预测。**

示例使用 [GeneReviews](https://www.ncbi.nlm.nih.gov/books/NBK1249/) 所列 GRCh38 chr7:73,330,452–74,728,172 区间，在 GENCODE v44 中提取有重叠的蛋白编码基因，用 HGNC 核对编号，以 ClinGen 和 gnomAD v2.1.1 证据排名；HPA v24.1 只提供表达注释。示例不运行 CNV 推断、AI 模型或 VCT；控制基因显式设为 `[]`。它采用特定区间和基因类型，不等于所有 Williams 相关基因，也不要求复现旧项目的候选清单。

HGNC / ClinGen 持续更新，候选数和排序可能随时间变化。gnomAD v2.1.1 只用于基因级约束值，不将其 GRCh37 坐标混入 GRCh38 区间提取。来源地址和本次文件校验值保存在 `manifest.json`；SHA256 用于追溯文件，不代表上游提供了固定版本校验承诺。

## 3. 遇到问题

- **找不到 Python 3.11 / 缺少依赖**：确认版本，完成安装后使用 `.venv/pipeline/bin/python`，不要直接用系统 Python 运行筛选。
- **下载失败**：确认能访问 HGNC、ClinGen、Google Cloud、HPA 和 EMBL-EBI。脚本自动重试；仍失败会返回错误并保留已下载文件。网络恢复后重新运行，会创建新目录并重新下载。
- **身份映射或数据格式报错**：查看终端指出的日志和 `manifest.json`。上游格式可能变化，脚本会停止，不跳过问题生成成功报告。
- **网页在 GitHub 中显示源码**：GitHub 不直接预览仓库中的 HTML。下载后用浏览器打开；项目指南也可按[本机预览说明](00_docs/05_preview/README.md)阅读。生成的结果网页直接本地打开即可。

## 4. 下一步与阅读入口

- [快速开始图解](00_docs/01_guides/QUICKSTART.html)：四步操作、结果解释与来源。
- [数据准备与自定义筛选](00_docs/01_guides/DATA_SETUP.html)：换成自己的候选列表或已知区间。
- [SIGnature 与 VCT 接入](00_docs/01_guides/VCT_SETUP.html)：独立的虚拟扰动工具；不影响首次筛选。
- [项目资料导航](00_docs/01_guides/PROJECT_INDEX.html) · [历史设计](00_docs/06_project_history/index.html) · [HTML 报告](04_reports/index.html)。历史材料不是首次运行的前置步骤。

## 5. 开发与发布说明

源码、配置、测试、用户指南和 HTML 历史报告入库。科学输入、模型、候选清单、结果表、Agent 文档、对话验收记录及旧原文不入库。第三方 `05_tools/` 整体忽略；自研 VCT 保留在 `05_virtual_cell/`。

工程检查（不代替上面的真实筛选）：

```bash
.venv/pipeline/bin/python scripts/test_pipeline.py
.venv/pipeline/bin/python -m pytest scripts/tests -q
python3 scripts/check_release.py
```

`bash scripts/export_github.sh /path/to/new-empty-directory` 可导出当前允许发布的文件，不含数据、环境或 Git 历史。默认发布检查只检查源码；它不证明数据已准备好。快速示例的参考表位于自己的运行目录，不写入通用 `03_pipeline/data/`。

当前不再通过 LFS 交付数据，**旧 Git/LFS 历史尚未清除**。提交当前整理后，远端最新文件树可以保持源码与指南为主，但普通 clone 仍可能下载历史 Git 对象。推送后应再做一次独立新克隆验证，然后决定是否清理本地旧资料。未接入的模型与缺少来源的历史实验不在首次示例的验收范围。
