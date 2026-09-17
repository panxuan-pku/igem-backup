# scRNA-seq → 缺失区间基因 工作流

> 位置：`src/cnv/` · 配置：`config/cnv.yaml` · 演示验证：GSE283473（Williams 综合征脑类器官）
> 状态：已在真实数据上端到端验证（2026-09-05）。AC-CNV-2 PASS；AC-CNV-1 FAIL 为**预期内负结果**（见下）。

## 目的与边界

从病人单细胞 RNA-seq 数据中产出**微缺失区间内的基因清单**，作为 L1 遗传学管线（`src/consensus*.py`）的输入。

**适用边界（重要）**：

- 缺失区间的**权威来源是基因型**（CNV 芯片 / WGS / MLPA / 临床报告）。表达型 CNV 推断（infercnvpy）只是**没有基因型时的回退路径**。
- 胚系杂合微缺失（典型 1–3 Mb）**处于表达型推断的分辨率极限**：窗口平滑（25–100 基因）会稀释 25–60 基因的缺失信号，且稳态 mRNA 剂量补偿会进一步抹平信号（本项目 E8 已观察到"mRNA 隐身"）。**自动发现的片段一律标记为探索性，必须正交验证。**
- 已知临床区间的基因提取**不依赖表达信号**，永远可靠（只要坐标版本匹配）。

## 架构

```
10x mtx（patient + reference 样本）
   │
stage-samples     整理成 scanpy 可读的 per-sample 目录（GEO 文件名 → 10x 标准名，2列 genes.tsv → 3列 features.tsv）
   │
prepare-order     GENCODE GTF → 蛋白编码基因排序表（gene_order_tsv）
   │
infercnv          加载→QC(min_genes/线粒体)→降采样→normalize_total+log1p→按基因组坐标排序
                  → infercnvpy 两档分辨率（standard 100/10, fine 25/5）→ 每窗口信号表 + 热图 + cnv_input.h5ad
   │
call-segments     robust z(median/MAD) → 连续低信号窗口段 → 大小过滤(≤10Mb，去着丝粒伪影)
   │
extract-genes     已知临床区间 + 自动片段 → 基因清单
                  ├─ candidates.csv            ← L1 管线输入（默认仅已知区间）
                  ├─ candidates_all.csv        ← 已知+自动并集
                  ├─ auto_segment_genes.csv    ← 仅自动片段（探索性）
                  ├─ interval_gene_expression_qc.csv  ← 每基因表达 QC（防 E6 型 pivot）
                  ├─ validation_known_intervals.csv   ← AC 判定
                  └─ cnv_report.md
```

## 快速开始

```bash
cd 03_pipeline

# 0) 先在仓库根目录运行 bash scripts/setup_envs.sh，并安装可选 CNV 依赖：
../.venv/pipeline/bin/python -m pip install -r requirements-cnv.txt
# GENCODE v44 GTF 随仓库交付；两样本的六个 GEO 原始压缩文件须
# 先按本文件附录下载到 data/scrna/GSE283473/。旧绝对路径链接不属于发布内容。

# 1) 整理样本目录 + 基因排序表（轻量，无 scanpy 依赖）
../.venv/pipeline/bin/python -m src.cnv.workflow stage-samples --config config/cnv.yaml
../.venv/pipeline/bin/python -m src.cnv.workflow prepare-order --config config/cnv.yaml

# 2) inferCNV（重步骤：scanpy + infercnvpy；16k 细胞 ≈ 几分钟）
../.venv/pipeline/bin/python -m src.cnv.workflow infercnv --config config/cnv.yaml

# 3) 片段发现 + 基因提取
../.venv/pipeline/bin/python -m src.cnv.workflow call-segments --config config/cnv.yaml
../.venv/pipeline/bin/python -m src.cnv.workflow extract-genes --config config/cnv.yaml

# 或一步到位：all（= 1+2+3，不含 stage-samples）
```

新数据集接入：复制 `config/cnv.yaml`，改 `samples`（patient/reference）、`known_intervals`（临床确诊区间与坐标版本）、按需调 `resolutions`/`z_threshold`。

## 验收门槛（QC gates）

| Gate | 含义 | GSE283473 结果 |
|---|---|---|
| **AC-CNV-1** | 自动发现片段覆盖已知区间 ≥ 50% | **FAIL（预期内负结果）**：1.55 Mb 杂合缺失未被表达型推断恢复 |
| **AC-CNV-2** | 区间 marker 基因（ELN/GTF2I/LIMK1/CLIP2）在表达数据中检出 | **PASS**（首轮 FAIL 曾抓住配置坐标过窄的错误：GTF2I 位于 74.65–74.76 Mb，原 74.4 Mb 终点漏掉了它） |
| 大小过滤 | >10 Mb 的"片段"判为着丝粒/低可比对区伪影 | standard 19/27、fine 7/46 个片段被过滤 |
| 剂量 sanity | 已知区间基因平均 log2FC | ≈ 0.05（≈0 与 E8"mRNA 隐身"一致，不作为否定缺失的证据） |
| E6 风险 | 患者中表达 <5% 的区间基因列出 | ELN/FZD9/CLDN3/4 等 17 个（血管/上皮基因在脑类器官沉默，符合预期；GTF2I 正常表达） |

## 方法学注意事项

1. **chrX/chrY 从自动发现中排除**（`exclude_chromosomes`）：性染色体剂量差异会主导信号。已知区间在性染色体上时仍可提取基因，但不做表达型自动验证。
2. **细胞组成混杂**：patient 与 reference 的细胞类型比例差异会在表达信号上产生类 CNV 波动——这是自动片段假阳性的主要来源，也是"自动片段必须正交验证"的原因之一。
3. **窗口重建有硬断言**：`window_table()` 会校验重建的窗口数与 `X_cnv` 列数一致；infercnvpy 版本变更导致布局不匹配时会显式报错而非静默错位。
4. **坐标版本必须一致**：`known_intervals.genome_build` 与 GTF 必须同一版本；GSE283473 用 10x GRCh38 参考 + GENCODE v44。
5. 重复基因符号经 `var_names_make_unique` 处理；极少数基因可能因符号不唯一而无法匹配 GTF（见 QC 表 `found` 列）。

## 与 L1 管线集成

```bash
cp outputs/cnv/candidates.csv input/candidates.csv
python -m src.normalize --input input/candidates.csv --out data/normalized.csv --hgnc-alias data/hgnc_aliases.tsv
python -m src.merge_evidence --normalized data/normalized.csv --config config/pipeline.yaml --out outputs/evidence.parquet --audit outputs/audit
python -m src.consensus_v2 --evidence outputs/evidence.parquet --config config/pipeline.yaml --out outputs/candidates_ranked_v2.csv --report outputs/report_v2.md --tune
```

`candidates.csv` 的 `source`/`deletion_id` 列保留来源信息；`normalize.py` 只读取 `gene_symbol` 列，兼容。

## 测试

```bash
../.venv/pipeline/bin/python -m pytest tests/ -q
# 22 个测试：GTF 解析/区间映射、片段发现（纯逻辑）、表达 QC、
# infercnvpy 端到端合成数据（植入缺失 → 恢复）、consensus/consensus_v2 回归
```

## 附录：GSE283473 数据下载

```bash
mkdir -p data/scrna/GSE283473
base="https://ftp.ncbi.nlm.nih.gov/geo/samples"
for s in GSM8663068_CTRL1 GSM8663071_WS1; do
  gsm="${s%_*}"; dir="${gsm:0:7}nnn"
  for f in barcodes.tsv.gz genes.tsv.gz matrix.mtx.gz; do
    curl -fL --retry 3 -o "data/scrna/GSE283473/${s}_${f}" "${base}/${dir}/${gsm}/suppl/${s}_${f}"
    gzip -t "data/scrna/GSE283473/${s}_${f}"
  done
done
# GENCODE v44 GTF 已随 Git/LFS 交付；不必再次下载。
```
