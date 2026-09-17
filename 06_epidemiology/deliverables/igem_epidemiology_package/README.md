# iGEM 网页数据包 — 使用说明

本文件夹是「染色体微缺失综合征流行病学数据」的 iGEM wiki 打包版，双语（英文为主 + 中文说明）。

## 内容

```
igem_epidemiology_package/
├── index.html     ← 自包含 HTML 页面（内嵌 SVG 图 + 表格 + 参考文献），可直接粘进 wiki
├── report.md      ← 双语 Markdown 报告（完整来源说明）
├── README.md      ← 本文件
├── figures/       ← 4 张图的 SVG（矢量，推荐） + PNG（预览）
│   ├── microdeletion_birth_prevalence.{svg,png}   出生患病率汇总
│   ├── 22q11_2_forest.{svg,png}                    22q11.2 多研究森林图
│   ├── microdeletion_denovo_fraction.{svg,png}     de novo 比例
│   └── microdeletion_birth_vs_adult.{svg,png}      出生 vs 成人患病率
└── data/          ← 两张 CSV 数据表
    ├── microdeletion_birth_prevalence.csv
    └── microdeletion_denovo_fraction.csv
```

## 如何放到 iGEM wiki

iGEM wiki 目前用 **HTML/CSS/JS 上传系统**（2024 年起的 wiki 编辑器）。两种方式：

### 方式 A（推荐）：上传整个 HTML 文件
1. 在 iGEM wiki 编辑器中，把 `index.html` 的**完整内容**复制粘贴进你目标页面（Background / Description 页）的 HTML 源码模式。
2. 因为图是**内嵌 SVG**，无需单独上传图片文件，整页即自包含。
3. 若编辑器不支持内嵌 SVG，改用方式 B。

### 方式 B：HTML + 单独上传图片
1. 新建页面，粘贴 `index.html` 正文（去掉 `<figure>` 里的内嵌 SVG 部分）。
2. 在 wiki 的「Upload Files」里上传 `figures/` 下的 4 张 **SVG**（矢量，缩放不糊，评委友好）。
3. 把 `<figure>` 里的内容替换成 `<img src="your-uploaded-filename.svg" alt="...">`。

### 建议
- **优先用 SVG**：矢量图在放大/缩放时清晰，适合评委在大屏查看。
- 参考文献（`index.html` 末尾的 References）已按期刊格式整理，**保留在页面上**（iGEM 评审重视可查证的引用）。
- 如需改图：编辑 `outputs/scripts/microdeletion_prevalence.py`，运行 `uv run python outputs/scripts/microdeletion_prevalence.py` 重新生成全部 PNG/PDF/SVG（输出到 `outputs/figures/` 与 `outputs/data/`）；重建本包用 `uv run python outputs/deliverables/igem_epidemiology_package/build.py`。

## 数据来源与注意事项（摘要）

- **无内置疾病数据库**，数据全部来自公开文献与人群队列，逐条标注来源（见 `report.md`）。
- 单位：**每 10,000 例活产**。计数来源用 Clopper–Pearson 精确 95% CI；文献来源给出的是已发表范围（非统计 CI）。
- 关键结论：
  1. 22q11.2 是最常见且数据最可靠的微缺失（主动筛查 **1/2,148**）。
  2. 成人患病率低于出生患病率（选择效应 + 早亡），22q11.2 约降 93%，16p11.2 几乎不变（不完全外显）。
  3. de novo 比例：重症缺失多新发，16p11.2/1q21.1 常遗传。
