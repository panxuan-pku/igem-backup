# iGEM 2026：缺失基因筛选与 RNA 设计候选

**输入具体缺失区间或基因列表，获得一份可追溯的研究排名与设计检查报告。** 合并后的流程使用一套核心评分，Open Targets 提供疾病注释，后接本项目的 3′UTR ≥30 bp 检查与固定模块预算选择。WHS 是当前 Wiki 展示疾病。

## 1. 第一次运行

准备 Python 3.11、Git 和可访问公开数据库的网络。以下命令适用于 macOS / Linux；已安装环境时跳过安装命令，安装脚本会重建 `.venv/pipeline`。

```bash
git clone https://github.com/panxuan-pku/igem-backup.git
cd igem-backup
bash scripts/setup_envs.sh --pipeline-only
.venv/pipeline/bin/python scripts/run_screening.py prepare \
  --references 03_pipeline/data/screening_refs
.venv/pipeline/bin/python scripts/run_screening.py run \
  --references 03_pipeline/data/screening_refs \
  --genes NSD2 LETM1 NELFA FGFR3 \
  --input-source "four-gene engineering demonstration"
```

这四个基因仅用于演示操作，**不是完整 WHS 缺失基因集合，也不是正式筛选结论**。首次参考下载约 617 MiB，环境安装另需下载依赖；之后可复用参考目录。失败后重新执行 `prepare` 可继续下载并核对已经完成的文件。

运行成功后，打开终端打印的 `report.html`。默认每次新建 `03_pipeline/outputs_repro/screening_时间/`，包含完整排名 `ranked.csv`、统一候选 `candidates.csv`、OT 响应快照、配置和运行清单。分数用于当前候选集合内的相对排序，不是致病或治疗成功概率；`selected` 表示通过长度与预算条件，不代表完成构建或实验验证。

## 2. 换成自己的输入

两种方式任选其一，不在同一次运行中混用：

```bash
# 文本文件每行一个基因，不带表头；支持 HGNC / Ensembl 编号或可唯一解析的符号。
.venv/pipeline/bin/python scripts/run_screening.py run \
  --references 03_pipeline/data/screening_refs \
  --gene-list /完整路径/genes.txt \
  --input-source "该列表的来源"

# 替换起点和终点占位符。GRCh38、1-based inclusive，无千位逗号。
.venv/pipeline/bin/python scripts/run_screening.py run \
  --references 03_pipeline/data/screening_refs \
  --interval 'chr4:起点-终点' \
  --input-source "区间的文献或样本来源"
```

程序不猜测通用 WHS 区间，不自动转换组装版本。区间入口提取重叠的蛋白编码基因，部分重叠另外标注。身份歧义或重复会明确报错。默认疾病为 WHS（`MONDO_0008684`）；其他疾病通过 `--disease-id` 设置 OT 对象。

## 3. 方法与复现

参考口径为 GRCh38 / GENCODE v44、gnomAD v4.1.1、HPA v24 下载入口、同次 HGNC / ClinGen 快照和 OT 26.09。唯一合并配置为 `03_pipeline/config/screening.yaml`，评分复用 `consensus_v2`。OT、IMPC 和 HPA 仅注释，不增加主分数；3′UTR 与模块预算决定设计选择状态，不删除排名行。

参考目录中的 `references.json` 记录来源、版本、下载时间和 SHA-256；运行前核对文件。严格重现还需复用 OT 快照：添加 `--ot-snapshot 旧结果目录/ot_snapshot.json`。HGNC / ClinGen 新下载内容和 OT 实时版本可能变化；OT 查询失败会显示注释缺口，不写成零分。没有提供 IMPC 补充表时明确标记未提供。

- [统一筛选操作指南](00_docs/01_guides/UNIFIED_SCREENING.html)：输入、结果解释、IMPC 补充表与错误处理。
- [Wiki：研究目的与总体方法](04_reports/wiki/WHS_purpose_methods.html)：合并后的研究框架与方法正文；正式结果待补。
- [SIGnature 与 VCT 接入](00_docs/01_guides/VCT_SETUP.html)：独立探索工具，尚未自动串接筛选，也不承诺 WHS 效果预测。
- [项目资料导航](00_docs/01_guides/PROJECT_INDEX.html) · [历史设计](00_docs/06_project_history/index.html) · [HTML 报告](04_reports/index.html)。

GitHub 文件页会显示 HTML 源码，下载后用浏览器打开；也可按[本机预览说明](00_docs/05_preview/README.md)阅读。旧 `run_quickstart.py` 的 Williams 示例及 `pipeline.yaml` 保留历史兼容用途；新用户使用上面的统一入口。

## 4. 开发与发布

源码、配置、测试和面向使用者的 HTML 入库；科学数据、模型、计算结果、Agent 记录和旧原文保留本地。第三方代码不随仓库交付；自研 VCT 在 `05_virtual_cell/`。最终 Wiki 结果发布前，需要确定正式 WHS 输入、外部快照归档，并完成对应版本的独立复现。

```bash
.venv/pipeline/bin/python scripts/test_pipeline.py
.venv/pipeline/bin/python -m pytest scripts/tests -q
python3 scripts/check_release.py
```

工程测试不代替科学验证。`bash scripts/export_github.sh /path/to/new-empty-directory` 导出允许发布的源码文件，不含数据、环境或 Git 历史。CNV 自动推断、DeepLOF 接入等暂缓事项不属于当前统一筛选的前置条件。
