# iGEM-Microdeletion — 染色体微缺失病计算通路（项目总目录）

> iGEM 2026「RNA binder 剂量补偿治疗染色体微缺失病」干实验部分。
> 复盘报告（五步通路全复盘）：`02_disease-williams/05_report/微缺失病计算通路复盘报告.md`

## 目录结构（对应报告五步通路）

```
iGEM-Microdeletion/
├── 01_disease-22q11.2/    第1步复盘：首个疾病案例（已废弃，保留作 pivot 证据）
│                          · TBX1 在脑不表达（15/9293 细胞）→ pivot 到 Williams
├── 02_disease-williams/   主战场：Williams + GTF2I 完整通路
│   ├── 01_rawdata/        10x 原始数据 CTRL1-3 / WS1-3（668MB）
│   ├── 02_scripts/        preprocess → attribution → celloracle（按序执行）
│   ├── 03_intermediate/   processed.h5ad
│   ├── 04_results/        results.npz + attribution_results.npz
│   └── 05_report/         ★复盘报告 md/docx/pdf
└── tools/                 通用工具
    ├── SIGnature/         SCimilarity/IG 归因框架（含 .venv、235MB 模型 model_files/model_files/）
    └── VirtualCellTool/   交互 demo（FastAPI 端口 8377，PBMC3k + MS 数据集，GEARS 权重+数据 ~7GB）
```

## 启动 / 执行

```bash
# Williams 主线
cd 02_disease-williams
python 02_scripts/preprocess.py            # → 03_intermediate
python 02_scripts/attribution_analysis.py  # 用 tools/SIGnature/.venv，→ 04_results
python 02_scripts/celloracle_run.py

# VirtualCellTool demo
cd tools/VirtualCellTool
../SIGnature/.venv/bin/python web/app.py   # → http://localhost:8377
```

依赖环境：`tools/SIGnature/.venv`（py3.11，scanpy/torch/captum/celloracle 已装）。

## 核心结论（详见复盘报告）

- **最硬结果**：SIGnature 归因与 CellOracle 扰动两独立方法收敛到同一候选集（NEUROD2/6、SOX5、NFIA、ZEB2、BCL11B）。
- **三个结构性不足**：翻译层盲区（RNA binder 打在蛋白层）、单基因 vs 多基因错配、删失基因在稳态 mRNA"隐身"。
