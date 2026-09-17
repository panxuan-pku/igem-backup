# GitLab 发布前独立使用验收

日期：2026-09-16。验收对象：`08_gitlab_export/`，由项目内 `scripts/export_gitlab.sh` 从原目录导出；它不含旧 `.venv`、嵌套 `.git`、指向旧沙盒的六个 CNV 样本链接或旧验证副本。该目录内重新创建了两套虚拟环境，运行时的项目源码、模型和输入数据均来自导出目录。第三方 Python 包从包索引安装；系统 Python 和 Chrome 仅作为运行环境。

## 结论

**本地独立导出验收通过：筛选管线和 VirtualCellTool 都能在新环境正常产出。尚不能据此开始删除旧项目副本。** 本机没有 `git lfs`，尚未把导出内容实际提交、上传到 GitLab 并从 GitLab 全新克隆。GitLab 的 LFS 对象、配额、下载与数据许可仍待发布者确认。清理门槛见 `00_docs/清理候选清单.md`。

## 环境与实测

macOS 26.6.2 arm64；Python 3.11.15；pip 24.0。管线环境的 numpy 2.4.6、pandas 2.3.3、pyarrow 25.0.1、pytest 9.1.1；虚拟工具的 torch 2.13.0、fastapi 0.141.1、scanpy 1.11.5。以下命令均从导出目录执行，除特别注明外未使用原目录的旧环境。

| 验收项 | 命令与输出摘要 |
|---|---|
| 发布内容 | `python3 scripts/check_release.py` → **49 个关键文件齐全**，无 Git LFS pointer、越界链接或嵌套 Git 元数据。原项目目录直接运行此检查会指出两个嵌套 `.git` 和六个旧越界链接，故不能直接将原目录当成发布目录。 |
| 新环境 | `bash scripts/setup_envs.sh` 从 requirements 新建 `.venv/pipeline`、`.venv/vct`；两环境 `python -m pip check` 均为 `No broken requirements found`。不引用旧 SIGnature editable 安装。 |
| 管线测试 | 导出副本 `../.venv/pipeline/bin/python -m pytest tests/ -q`：基础环境 **22 passed, 1 skipped**。安装可选 `requirements-cnv.txt` 后，`infercnvpy==0.6.1` 可导入，合成 CNV 用例 **2 passed**，全套 **24 passed**。 |
| WBS/WHS 三段管线 | `python -m src.normalize` → WBS 35 基因（2.9% unresolved）、WHS 19 基因（0%）；`python -m src.merge_evidence` → 35/19 行证据表及审计 checksum；`python -m src.consensus_v2 --mode rank --sensitivity` → 两组排名 CSV 和 Markdown 报告均生成于 `03_pipeline/outputs_repro/`。三个 CLI 在空白导出目录会自动建立输出父目录。 |
| 六 mode | 在导出副本对 WBS 运行 `validate/rank/full`、对 WHS 运行 `validate/rank/exploratory`，均退出 0 并生成 35/19 行 CSV 与报告。WBS 当前正对照 **Top10 4/4**，Top 3 为 STX1A、VPS37D、ELN；WHS 的 NSD2 在三个模式均为 #1。旧文档的 6/6 和旧 WHS 逐值输出不应视作现行配置基准。 |
| VirtualCellTool | 导出目录 `../../.venv/vct/bin/python web/app.py` 可加载本地 SIGnature 编码器、PBMC 和预计算 CIPHER；`../../.venv/vct/bin/python tests_api.py` → **18/18 API + 首页通过**，三个数据集分别为 2,700/17,799/96,969 细胞，切换后 PBMC 重算数值不变。 |
| 扰动结果 | CIPHER 敲低的 `|Δ|max`：PBMC/MS4A1 **0.28199**、MS/MOBP **1.67955**、Williams/GTF2I **10.07913**。PBMC 表达阳性 B 细胞 MS4A1→0 的反事实位移非零；GEARS/CEBPA 用项目内检查点产出 **5,045 基因**、`|Δ|max=5.7275`。 |
| 浏览器 | 使用安装在本机的 Chrome 作为 Playwright 运行时执行 `tests_e2e_playwright.py`：全部断言通过，UMAP、归因、CIPHER 敲低/过表达、基线、反事实图与 MS 切换正常，**控制台错误为零**。手动浏览器复核 B 细胞 MS4A1 3.25→0：嵌入位移 0.013、UMAP 位移 0.022。 |

## 未完成的发布门槛

1. 这台机器的 `git lfs version` 返回“not a git command”。须先安装 Git LFS，再从 `08_gitlab_export/` 建立 GitLab 仓库；提交前确认 `git lfs ls-files` 列出二进制数据与模型，并核对 GitLab 的容量、单文件限制、许可和隐私要求。
2. 实际推送后，在另一个全新目录克隆并 `git lfs pull`，重复 `check_release.py`、新环境安装、管线排名和 `tests_api.py`/浏览器测试。只有完成这一轮，才能说“GitLab 用户可独立使用”。本地导出不是远端克隆的替代品。
3. 可选的真实 GSE283473 CNV 全流程这轮未重跑；仅验证了依赖安装与合成用例。它不是候选基因筛选和虚拟扰动两项核心验收的前置条件。Linux、其他 Python 版本也未验证。
4. 原目录的 01/02 疾病研究脚本虽已将主要输入路径改为项目相对路径，但未作为本轮两个核心工具逐一实跑；旧历史输出、WHS 旧配置快照也未重建。
5. 浏览器切换数据集后会保留此前的结果标签页，标签仅显示基因/扰动方式而不标明原数据集。这可能是有意保留跨数据集比较，也可能使读者误认旧图属于当前数据集；本轮未擅自改变产品行为，需团队决定保留并标注来源，还是切换时清空。

本轮**没有删除、移动或覆盖任何历史实验数据**。`07_independent_reproduction_20260916/` 与 `08_gitlab_export/` 都是大型本地副本；在新 GitLab 克隆验收前，尤其不要删除 08 或据此清理外部旧项目目录。
