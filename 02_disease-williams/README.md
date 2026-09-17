# CellOracle_Williams — WS 微缺失病主效基因筛选（GTF2I）

iGEM 项目：Williams 综合征 (7q11.23 微缺失) 单细胞数据上验证 **GTF2I 为剂量敏感主效基因**。
三条证据链：① SCimilarity + Integrated Gradients 差异归因；② CellOracle GRN 模拟 GTF2I KO/OE 对比真实疾病 DE；③ 复盘报告。

## 目录结构

```
01_rawdata/        10x 原始数据（CTRL1-3 / WS1-3，~668MB；GitHub 不收录）
02_scripts/        全部代码（按 01→05 顺序对应执行流程）
03_intermediate/   preprocess.py 产物 processed.h5ad（QC + HVG + 强制保留 7q11.23 基因）
04_results/        results.npz（CellOracle KO/OE shift + 真实 DE）
                   attribution_results.npz（IG 差异归因 + 对照 DE + 相关性）
05_report/         微缺失病计算通路复盘报告 (.md/.docx/.pdf) + report.css
```

## 执行流程

```bash
python 02_scripts/preprocess.py            # 6 样本合并 QC → 03_intermediate/processed.h5ad
python 02_scripts/attribution_analysis.py  # SIGnature SCimilarity + IG 归因 → 04_results
python 02_scripts/celloracle_run.py        # GTF2I KO/OE 模拟 vs 真实 DE → 04_results
python 02_scripts/html2pdf.py in.html out.pdf  # 报告排版用小工具
```

原始六样本来自 [NCBI GEO GSE283473](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE283473) 的 `GSE283473_RAW.tar`（GSM8663068–GSM8663073）。下载后需按上面的 `CTRL1`–`WS3` 目录整理为 10x 的 `matrix.mtx.gz`、`barcodes.tsv.gz`、三列 `features.tsv.gz`；GEO 原始 `genes.tsv.gz` 只有两列，不能直接替代现有 `features.tsv.gz`。此历史全样本分析尚未在 GitHub 克隆中重新验收。

依赖：scanpy, torch, captum, celloracle；`attribution_analysis.py` 使用同一仓库的 `05_tools/SIGnature` 源码与模型，不依赖旧桌面路径。
