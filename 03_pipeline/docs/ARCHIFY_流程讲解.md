# igem_gene_pipeline — 项目结构与流程讲解

> 配套文件：`igem_gene_pipeline.dataflow.html`（Archify 交互式数据流图，浏览器打开）
> 图谱源文件：`igem_gene_pipeline.dataflow.json`
> 本文讲解项目结构、两条子管线与图中的每个节点，内容来自 `README.md`、`docs/cnv_workflow.md`、`outputs/wbs/report_v2.md`、`outputs/cnv/cnv_report.md`。

---

## 一、项目结构

```
igem_gene_pipeline/
├── README.md                  # 管线总览 + 快速上手（uv 环境 + 四步命令）
├── config/                    # 全部参数集中在此，改配置不动代码
│   ├── pipeline.yaml          # L1 管线：证据阈值（pLI/LOEUF/HPA）、共识权重
│   ├── cnv.yaml               # CNV 工作流：样本、分辨率阶梯、片段阈值、已知区间
│   └── sources.json           # 数据源清单（ClinGen/gnomAD/HPA/HGNC 的 URL 与校验）
├── data/                      # 下载的数据（不入 git，只存 checksum）
│   ├── clinGen_gene_curation_list_GRCh38.tsv   # ClinGen 单倍剂量不足评分
│   ├── gnomad_constraint.tsv                   # gnomAD pLI / LOEUF 约束指标
│   ├── hpa_rna_expression_consensus.tsv        # HPA 51 组织 RNA 表达共识
│   ├── hgnc_aliases.tsv                        # HGNC 别名表（符号解析用）
│   ├── gencode.v44.basic.annotation.gtf.gz     # GENCODE v44 蛋白编码基因注释
│   ├── gencode_v44_gene_order.tsv              # GTF 派生的基因排序表
│   └── scrna/GSE283473/                        # 病人 WS1 + 对照 CTRL1 的 10x 矩阵
├── input/candidates.csv       # L1 管线入口：候选基因符号（可由 CNV 工作流产出生成）
├── src/                       # 代码
│   ├── normalize.py           # L1 第 1 步：符号 → HGNC ID 主键（ADR-001）
│   ├── merge_evidence.py      # L1 第 2 步：整合 ClinGen/gnomAD/HPA → evidence.parquet
│   ├── consensus.py           # L1 第 3 步 v1：加权投票排名
│   ├── consensus_v2.py        # L1 第 3 步 v2：归一化加权 + Borda 对照 + LOO 调权
│   └── cnv/                   # CNV 工作流（scRNA-seq → 缺失区间基因）
│       ├── workflow.py        # CLI 编排器：5 个子命令（stage-samples 等）
│       ├── infercnv.py        # 加载 → QC → 归一化 → infercnvpy 推断
│       ├── segments.py        # robust z 片段发现 + 大小过滤
│       ├── gene_order.py      # GTF 解析 + 区间基因提取
│       └── expression_qc.py   # 区间基因表达 QC（防 E6 型 pivot）
├── outputs/
│   ├── evidence.parquet       # merge_evidence 产物
│   ├── candidates_ranked_v2.csv  # 最终 top-N 排名（consensus_v2 产物）
│   ├── report_v2.md           # iGEM 汇报报告
│   └── cnv/                   # CNV 工作流产物
│       ├── candidates.csv         # ← L1 管线输入（仅已知区间，35 基因）
│       ├── candidates_all.csv     # 已知+自动片段并集（2488 基因）
│       ├── auto_segment_genes.csv # 仅自动片段（探索性）
│       ├── cnv_input.h5ad         # 中间表达矩阵
│       ├── window_signal_*.tsv    # 两档分辨率的窗口信号
│       ├── segments_*.csv         # 缺失片段表
│       ├── heatmap_patient.png    # 患者染色体热图
│       ├── validation_known_intervals.csv  # AC 判定
│       └── cnv_report.md          # 工作流报告
├── docs/
│   ├── cnv_workflow.md        # scRNA → 缺失区间基因工作流文档（含验收门槛）
│   ├── decisions/ADR-001-hgnc-indexing.md  # 架构决策：HGNC ID 为主键
│   └── api/                   # 外部 AI 评分服务契约
└── tests/                     # pytest（22 个测试：GTF 解析、片段发现、合成 CNV 恢复、共识回归）
```

**两条子管线的关系**：CNV 工作流产出 `outputs/cnv/candidates.csv`，`cp` 到 `input/candidates.csv` 后即成为 L1 管线的入口 —— 这是图里标为「CNV → L1 交接」的那条 `candidates.csv` 边。

---

## 二、流程讲解（对应图中的 5 个阶段）

### 阶段 ① 数据源（灰框）

| 节点 | 内容 | 用途 |
|---|---|---|
| scRNA-seq 原始 | GEO **GSE283473** 的 10x 矩阵，WS1（Williams 综合征病人）vs CTRL1（对照） | CNV 工作流的表达数据 |
| GENCODE v44 | 蛋白编码基因注释 GTF（GRCh38） | 派生基因排序表，供区间提取 |
| 参考数据库 | **ClinGen**（单倍剂量不足 HI 评分）、**gnomAD**（pLI/LOEUF）、**HPA**（组织表达）、**HGNC**（别名表） | L1 管线的四条证据源 |

### 阶段 ② 整理（CNV 预处理）

- **stage-samples**：把 GEO 的 GSM 文件整理成 scanpy 可读的 per-sample 10x 目录（2 列 genes.tsv → 3 列 features.tsv）。
- **prepare-order**：GTF → 蛋白编码基因排序表（基因名 → 染色体坐标）。

### 阶段 ③ 推断

- **infercnv**（tag：回退路径）：加载两样本 → QC（min_genes≥200、线粒体≤20%）→ 降采样 → normalize_total+log1p → 按基因组坐标排序 → **infercnvpy** 两档分辨率推断（standard 100/10、fine 25/5）→ 每窗口信号表 + 热图 + cnv_input.h5ad。
  - 图上 `prepare-order` 从下方汇入：推断必须按基因组坐标排序，排序表是它的第二个输入。

### 阶段 ④ 提取 · 整合 · 共识（两条子管线在此汇合）

**CNV 支（上方）**：

- **call-segments · extract-genes**（tag：仅已知区间）：robust z（median/MAD，阈值 1.5）→ 连续低信号窗口段 → 大小过滤（>10Mb 判为着丝粒伪影）→ 从**已知临床区间**（Williams 7q11.23）和自动片段提取基因清单。默认 `candidates.csv` 只含已知区间的 35 个基因（**不依赖表达信号，永远可靠**）；自动片段单独存为探索性候选。

**L1 支（下方）**：

- **normalize · merge_evidence**（tag：ADR-001）：基因符号经 HGNC 别名映射 → **HGNC ID 主键**（架构决策 ADR-001，数据源变动不影响重跑）→ 与 ClinGen/gnomAD/HPA 按 HGNC ID join → `evidence.parquet`。
- **consensus_v2**：归一化加权（rank 归一化 + 证据权重）+ **Borda 对照**（校验两种聚合方式是否一致）+ 可选 **LOO 调权**（leave-one-out，用正对照基因调权重）→ top-N 排名。

### 阶段 ⑤ 产出 · 下游

- **candidates_ranked_v2**（紫框 = 数据产物）：top-N 排名表 + `report_v2.md`（iGEM 汇报）。
- **L3 扰动工具**（下游消费方）：VirtualCellTool / CellOracle 等基因扰动工具，接收 top-N 候选做因果验证。

---

## 三、关键结果（来自 report_v2.md 与 cnv_report.md）

### 验收门槛（GSE283473 真实数据）

| Gate | 判定 | 说明 |
|---|---|---|
| **AC-CNV-2** 区间 marker 基因检出 | ✅ PASS | ELN / GTF2I / LIMK1 / CLIP2 均在表达数据中检出（首轮 FAIL 曾抓住配置坐标过窄的 bug：GTF2I 位于 74.65–74.76 Mb，原 74.4 Mb 终点漏掉了它） |
| **AC-CNV-1** 自动发现覆盖已知区间 | ❌ FAIL（**预期内负结果**） | 1.55 Mb 胚系杂合缺失处于表达型推断的分辨率极限；区间基因平均 log2FC ≈ 0.05，与 E8「**mRNA 隐身**」（剂量补偿吸收稳态 mRNA 差异）一致 |
| 大小过滤 | 生效 | standard 19/27、fine 7/46 个 >10Mb 伪影片段被过滤 |

> 负结果的定位：AC-CNV-1 的 FAIL 不否定缺失存在，也不影响 `candidates.csv`（只依赖已知区间坐标）。这正是本项目 E8 实验「mRNA 隐身」的机制印证 —— 表达型 CNV 推断注定是**回退路径**，权威来源是基因型（CNV 芯片 / WGS / MLPA）。

### consensus_v2 Top 10（35 基因，rank 归一化）

| rank | 基因 | 得分 | Borda |
|---|---|---|---|
| 1 | FZD9 | 1.926 | 15 |
| 2 | FKBP6 | 1.037 | 31 |
| 3-8 | TMEM270 / SPDYE8-11 / ENSG… | 0.000 | 19 |
| 9 | ELN | -0.037 | 8 |
| 10 | BAZ1B | -0.074 | 4 |

- 证据覆盖率：gnomAD pLI/LOEUF 77%，clinGen 14%（其余证据列缺失时中性处理）。
- Additive-rank 与 Borda-rank 的 Spearman ρ = 0.234（两种聚合方式分歧较大，图上以 Borda 作为对照正是为此设计）。
- LOO 调权：对照基因 ELN/GTF2I 未进入 top-N（LOO hit rate 0%），提示当前证据组合对「mRNA 隐身」的区间基因不敏感 —— 这是待改进点，不是管线 bug。

---

## 四、如何阅读 Archify 图

- **5 列 = 5 个阶段**，从左到右是数据流向；**行 = 并行支流**（上方 CNV 支、下方 L1 支）。
- **绿箭头 = 主要数据**（样本矩阵、candidates.csv、evidence.parquet 等），**灰箭头 = 一般数据流**（注释、证据源），**紫框 = 数据存储产物**，**灰框 = 外部源/外部工具**。
- 节点上的小标签（tag）标注关键约束：`回退路径`（infercnv）、`仅已知区间`（candidates.csv 来源）、`ADR-001`（HGNC ID 主键决策）。
- 两条关键边：
  - **candidates.csv（CNV → L1 交接）**：把 CNV 工作流的产物接到 L1 管线入口；
  - **证据源**：四条外部数据库直接汇入证据整合。
- 图内置功能：右上角可切换浅色/深色主题、演示模式、导出 PNG/SVG；底部工具栏支持路径追踪、搜索、聚焦。
