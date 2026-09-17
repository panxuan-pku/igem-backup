# iGEM Wiki — Document 页面大纲（工具说明书）

> **页面主题**：筛选管线 + VirtualCellTool 的**使用说明书**（README 风格）
> **起草日期**：2026-09-14
> **项目状态**：未完全开发（本大纲标注每节的实际完成度）
> **读者假设**：会跑命令行、有单细胞/遗传学基础的下一位队员或外部复用者

**状态标记**

| 标记 | 含义 |
|---|---|
| 【✓ 照抄即可】 | 现有 README/文档已有可搬内容 |
| 【◐ 需重写】 | 有素材但需改写成说明文体/补步骤 |
| 【○ 待补】 | 功能未完成，先留占位 |

**语言建议**：iGEM 评审为英文，**正文最终需英文**。命令与参数名保持原样不译。

**重要前提**：说明书写给"没参与开发的人"。当他们卡住时，**文档的责任，不是他们的**。每步都要写"预期看到什么"。

---

## 0. 页面定位与结构

**建议英文标题**：`Documentation — Microdeletion Gene Prioritization Pipeline & VirtualCellTool`

**要写什么**
- 本页是**两个人的工具**的说明书：① 筛选管线（Python CLI）② VirtualCellTool（交互式网页）
- 两者的关系图：管线输出 `ranked_*.csv` → 作为 VirtualCellTool 的输入基因列表 → 输出机制假设 → 回到实验设计
- 导航：每节开头一句"读完这节你会得到什么"
- 版本对应关系（避免读者拿到不匹配的组合）

**状态**：【✓ 照抄即可】

---

## 1. 工具概览（TL;DR）

**建议英文标题**：`1. Overview`

**要写什么**

| | 筛选管线 | VirtualCellTool |
|---|---|---|
| 一句话 | 给一串基因，按遗传学证据排出优先级 | 给一个基因，预测扰动后的细胞反应 |
| 形态 | Python CLI（`python -m src.*`） | FastAPI 网页（localhost:8377） |
| 输入 | HGNC 基因符号列表 / 缺失区间坐标 | 基因名 + 数据集选择 |
| 输出 | `candidates_ranked*.csv` + `report*.md` | 交互图表（预测 / 对照组 / 位移） |
| 耗时 | 秒级 | 秒级（首次启动 6.2s） |
| 是否需要 GPU | 否 | 否（CPU 可跑） |

- **五分钟决策表**：你想做什么 → 用哪个工具 → 跳到第几节

**状态**：【✓ 照抄即可】

---

## 2. 系统要求与环境

**建议英文标题**：`2. Requirements`

**要写什么**

### 2.1 筛选管线
- Python 3.11；依赖通过 `uv` 管理（**不要用系统 Python，不要 pip install**）
- 依赖：pandas / pyarrow / pyyaml / numpy / requests；测试需 pytest
- 磁盘：数据源约数百 MB（`data/` 不入库）
- 无需网络（数据源预先下载）

### 2.2 VirtualCellTool
- 解释器固定为同级 SIGnature 项目的 venv：`derived/tools/SIGnature/.venv/bin/python`（Python 3.11 + torch/captum/scanpy/fastapi/umap-learn/plotly）
- 内存：**重要**——见下方"已知陷阱"
- 磁盘：CIPHER 缓存 `cipher_pbmc.npz` 105M / `cipher_ms.npz` 104M / `cipher_ws.npz` 12M
- 端口：8377

**要写的"已知陷阱"表（强烈建议保留，能救下一个人的一天）**

| 陷阱 | 后果 | 规避 |
|---|---|---|
| 表达式矩阵被稠密化 | ws 数据集 96969×28231 float64 ≈ **21.9 GB** → OOM/swap 卡死 | 全程保持 CSR 稀疏，只在 5000 HVG 子矩阵上 dense |
| 用系统 Python / pip | 依赖冲突/权限报错 | 只用指定 venv |
| CIPHER 缓存字段不全 | 每次启动全量重算（数秒～数十秒） | 缓存必须含 `gene_list/ctrl_mean/Sigma/hvg_idx/full_mean` |
| 用 `file://` 打开 index.html | 页面静默失败（API 不可用） | 必须经 `http://127.0.0.1:8377` |

**状态**：【✓ 照抄即可】（陷阱表来自实际踩坑记录）

---

## 3. 安装与启动

**建议英文标题**：`3. Installation & Startup`

**要写什么**

### 3.1 筛选管线
```bash
# 环境
cd 03_pipeline
uv init --python 3.11
uv add pandas pyarrow pyyaml numpy requests
uv add --dev pytest

# 数据源（见 config/sources.json）
#   ClinGen / gnomAD / HPA / HGNC 别名表 → data/

# 测试
uv run pytest tests/ -q        # 预期：20 passed, 1 skipped
```

### 3.2 VirtualCellTool
```bash
cd derived/tools/VirtualCellTool
./启动VirtualCellTool.command          # 或双击
# 预期输出：🚀 启动… / ✅ 服务已在运行 / 🌐 打开 http://127.0.0.1:8377
# 浏览器打开 http://127.0.0.1:8377
# 停止：pkill -f "web/app.py"
```

- **每步写"预期看到什么"**（成功信号 vs 失败信号）
- 冷启动 6.2s；切换数据集为懒加载（首次切 ws 约 5s）

**状态**：【✓ 照抄即可】

---

## 4. 快速上手（最小可行示例）

**建议英文标题**：`4. Quick Start — A Minimal Working Example`

**要写什么**：一条完整的端到端路径，读者照抄就能跑出结果。

```bash
# Step 1 准备候选（WBS 7q11.23 区间示例）
cd 03_pipeline
printf "STX1A\nELN\nBAZ1B\nGTF2I\n" > input/candidates.csv

# Step 2 归一化 + 合并证据
python -m src.normalize --input input/candidates.csv --out data/normalized.csv --hgnc-alias data/hgnc_aliases.tsv
python -m src.merge_evidence --normalized data/normalized.csv --config config/pipeline.yaml \
    --out outputs/<主题>/evidence.parquet --audit outputs/audit

# Step 3 排序
python -m src.consensus_v2 --evidence outputs/<主题>/evidence.parquet \
    --ai-scores outputs/ai_scores.csv --config config/pipeline.yaml --mode auto \
    --out outputs/<主题>/candidates_ranked_v2.csv --report outputs/<主题>/report_v2.md

# Step 4 看结果 → 预期：CSV 按 consensus_score 降序
# Step 5 用 VirtualCellTool 看机制 → 把基因名粘进网页搜索框
```

- 每步给出**预期输出片段**（复制真实输出，不要写"跑完即可"）
- 加入一个**截图占位**（`[Figure: 快速上手结果示例]`）

**状态**：【◐ 需重写】（命令已准确，需补预期输出与截图）

---

## 5. 输入准备

**建议英文标题**：`5. Preparing Your Inputs`

**要写什么**

### 5.1 候选基因列表
- 格式：每行一个 HGNC 基因符号（`input/candidates.csv`）
- 符号会自动经 HGNC 别名表解析为 HGNC ID 主键（**支持旧符号**，如 WHSC1→NSD2）
- 正对照文件：`input/controls_wbs.txt` / `controls_whs.txt`

### 5.2 缺失区间坐标（可选）
- 若只有区间坐标：用 `src/cnv/` 工作流从 GTF 提取区间内基因
- **重要限制**：scRNA-seq CNV caller 对 <3 Mb focal CNV 灵敏度极低 → 用已知临床区间提取基因是正确策略

### 5.3 数据源准备
- `config/sources.json` 列出 4 个源（ClinGen / gnomAD / HPA / HGNC 别名）的 URL 与 checksum
- checksum 校验步骤

**状态**：【✓ 照抄即可】

---

## 6. 配置参考

**建议英文标题**：`6. Configuration Reference`

**要写什么**：`config/pipeline.yaml` 的逐项说明表——**全项目最实用的一张表**。

| 配置项 | 取值 | 默认 | 含义 | 改它会怎样 |
|---|---|---|---|---|
| `consensus_v2.normalize` | `raw` / `rank` | `raw` | 证据归一化方式 | `rank` 在小样本下有伪影（曾让 pLI=0.002 的基因排 #1） |
| `consensus_v2.hpa_penalty`（cap / per_organ_weight） | 数值 | `0.0` | HPA 器官惩罚 | 非 0 会错杀正对照（STX1A/ELN/GTF2I） |
| `consensus_v2.evidence.*.weight` | 数值 | 见文件 | 各证据源权重 | 直接影响排名 |
| `pipeline_mode` | `auto` / 四 mode | `auto` | 运行模式 | 见 §7 |
| `tuning.enabled` | bool | `false` | LOO 权重调优 | 对照数 <3 时应保持关闭 |
| `tuning.positive_controls` | 基因列表 | TBX1/ELN… | 调优用的已知主效基因 | — |

- 每个权重的**来源依据**需注明（见图表/局限，属于待补项）

**状态**：【✓ 照抄即可】（需从 config 逐项抄写并补依据）

---

## 7. 运行模式

**建议英文标题**：`7. Running Modes`

**要写什么**：四种模式的"什么时候用哪个"决策表。

| Mode | 名称 | 场景 | 输出差异 |
|---|---|---|---|
| `validate` | A 验证 | 主效基因已确定（如 WHS 的 NSD2） | 验证报告面板（ClinGen/pLI/SINEUP 靶向条件表） |
| `rank` | B 增强筛选 | 有争议候选、有正对照 | 排序 + 正对照检验表 |
| `exploratory` | D 探索 | 全新 CNV、无任何证据 | 探索声明，**不给实验建议** |
| `auto` | 自动（默认） | 不确定时 | 按输入丰富度自动选择 |

- 每个 mode 给一条**完整命令** + 一段**真实输出节选**
- ⚠️ 注意：代码支持 `full`（Mode C 全栈筛选，排序 + 补偿集成），README 表中应包含

**状态**：【✓ 照抄即可】

---

## 8. 输出解读

**建议英文标题**：`8. Understanding the Output`

**要写什么**

### 8.1 产物位置
- 产物按主题归档：`outputs/{wbs,whs,mode,cnv}/`（**不在根目录**）
- 索引：`outputs/README.md`
- 审计：`outputs/audit/`（`run.json` + `data_checksums.txt`）

### 8.2 排名 CSV 字段表（逐列说明）

| 字段 | 含义 | 怎么读 |
|---|---|---|
| `rank` | 最终排名 | — |
| `hgnc_id` / `input_symbol` | 主键 / 输入符号 | — |
| `clinGen_hi_score` | 单倍剂量不足评分 | 3=明确、30=不确定、40=无证据 |
| `gnomad_pLI` | 功能缺失不耐受 | **高**=剂量敏感 |
| `gnomad_LOEUF` | 观察/期望 LOF 比 | **低**=剂量敏感（与 pLI 反直觉，重点说明） |
| `DeepLOF_score` | AI 层分数（可选） | 高=预测剂量敏感 |
| `compensation_ratio` / `compensation_class` | 患者/对照 mRNA 比 | >1=过补偿，`unreliable`=表达过低不可判 |
| `consensus_score` | 加权总分 | — |
| `contrib_*` | 各证据源贡献分解 | **排查"为什么它排第一"用这一列** |
| `hpa_penalty` | 惩罚项 | v2.2 起为 0 |
| `borda_score` / `borda_rank` | Borda 对照排名 | 与加性排序不一致时提示权重敏感 |

- 特别说明：**LOEUF 低才好**、**pLI 高才好**——这是最常被误读的一对

### 8.3 验证报告怎么看（Mode A/B）
- 正对照检查表的五个维度：in_candidates / rank / top10 / 共识 / 证据
- "正对照没进 Top10 意味着什么"

**状态**：【✓ 照抄即可】

---

## 9. VirtualCellTool 使用手册

**建议英文标题**：`9. VirtualCellTool — User Manual`

**要写什么**：按界面从上到下写，含每类图表的**读图方法**。

### 9.1 界面结构
- 顶栏：数据集下拉（3 个）+ 加载状态
- 左控制栏：① 选细胞 ② 归因 Top 基因 ③ 选基因 ④ CIPHER 扰动预测 ⑤ 反事实位移 ⑥ GEARS 因果
- 右工作区：标签页（UMAP 主图 + 各类结果图）
- 底部状态栏：统计摘要

### 9.2 三个数据集的语义（**最容易踩的坑**）
| key | 数据集 | 细胞数 | 分组语义 |
|---|---|---|---|
| `pbmc` | PBMC 2700 | 2,700 | **细胞类型**（B/T/NK/单核/树突） |
| `ms` | MS 少突胶质 | 17,799 | **病健分组**（MS / normal） |
| `ws` | Williams 脑类器官 | 96,969 | **病健分组**（WS / CTRL） |

> ⚠️ ws/ms 的"细胞类型"实际是**病健分组**——读图时别把"WS 响应第一"理解成"某种细胞类型"。

### 9.3 八类图表的读法

| 图 | 怎么读 | 常见误读 |
|---|---|---|
| UMAP 细胞图谱 | 点=细胞，近=状态相似；**坐标轴无物理意义** | 把簇间距当绝对距离 |
| CIPHER 双子图 | 左=转录组变化（红=目标/绿=上调/蓝=下调）；右=哪个分组最敏感（橙） | 把"上调/下调"当成好坏 |
| 线性基线对照 | 彩色条**超出灰线**的部分才是模型增量信号 | 忽略基线，直接信模型 |
| 反事实位移（双视图） | 左=全景定位+取景框；右=放大后 ⚫扰动前 → ⭐扰动后 | 以为位移小=没效果（实为 UMAP 尺度问题） |
| 质心距离图 | 灰色=扰动前，红=最近的类型；身份是否改变 | — |
| 表达分布图 | 左=UMAP 按表达着色（灰=不表达）；右=分组表达水平 | 拿它当"功能重要性" |
| 归因图 | **长度=重要性，颜色只表方向**（橙=推高/紫=推低嵌入） | **把负值当"负面基因"**（最严重的误读） |
| GEARS 图 | 负对照，标注了域外推断 | 把它当有效预测 |

### 9.4 推荐分析顺序（四步法）
1. 🎨 **表达分布** —— 先确认基因在该组织是否表达（**排除组织特异性问题**）
2. 📉/📈 **CIPHER** —— 转录组效应 + 最敏感分组
3. 📏 **线性基线** —— 诚实性对照
4. 🎯 **位移 + 质心** —— 细胞身份能否被推回对照状态

### 9.5 已知边界（写进说明书，避免误用）
- CIPHER 只覆盖 Top 5000 HVG；区间外基因按钮会灰掉并给出相近基因建议
- CIPHER 对表达稀疏基因不敏感（实测 CD3D/CD3E 未命中）
- GEARS 对微缺失候选基因 0 覆盖——仅作负对照

**状态**：【✓ 照抄即可】（来自 VirtualCellTool/README.md 与 ARCHITECTURE_v3.md）

---

## 10. 端到端示例（完整案例）

**建议英文标题**：`10. Worked Example — WBS 7q11.23`

**要写什么**：用一个真实案例串起两个工具。

1. 输入：WBS 区间 35 基因
2. 管线运行（命令 + 输出节选）
3. 结果解读：STX1A #1 / ELN #3 / GTF2I #9 …
4. 拿到 VirtualCellTool 里逐个查：
   - GTF2I 过表达 → |Δ|max = 10.08，全部落在神经发育/突触基因
   - ELN → |Δ|max = 0.006（脑内无效应，组织特异性）
5. 综合结论：GTF2I 优先级建议上调；ELN 需换组织验证
6. **明确写出这次分析得出了什么、没得出什么**

**状态**：【◐ 需重写】（数据齐全，需整理成叙事）

---

## 11. 故障排查

**建议英文标题**：`11. Troubleshooting`

**要写什么**：症状 → 原因 → 解决 三段式表格。

| 症状 | 原因 | 解决 |
|---|---|---|
| 启动卡住/无响应 | 大数据集被稠密化（内存不足） | 确认代码保持稀疏；默认用 pbmc |
| 页面白屏 | 服务未就绪或经 `file://` 打开 | 等就绪；改用 `http://127.0.0.1:8377` |
| 每次启动都很慢 | CIPHER 缓存字段不全 → 全量重算 | 检查缓存 5 个字段 |
| 切换数据集后结果像没变 | 前端请求未带 `ds` 参数 | 已在 v3.1 修复；确认版本 ≥ v3.1 |
| 基因按钮灰掉 | 不在 Top 5000 HVG | 用提示的相近基因，或换高变基因 |
| `uv run pytest` 报找不到 pytest | 未装 dev 依赖 | `uv add --dev pytest` |
| 排名与上次不同 | 配置被改（权重/归一化） | 对比 `config/pipeline.yaml` 与 audit 产物 |

**状态**：【✓ 照抄即可】（陷阱表已有）

---

## 12. 版本与变更记录

**建议英文标题**：`12. Versions & Changelog`

**要写什么**
- 两套工具的版本对应表（避免读者混用）
  - 筛选管线：**v2.2**（代码自述）
  - VirtualCellTool：**v3.3**，tag `v1.0-scimilarity` / `v2.0-gears` / `v3.1-fixed` / `v3.2-zoom` / `v3.3-viz`
- 完整变更史指向 `outputs/reports/PROJECT_LOG.md`（条目 #0–#15）
- **诚实标注**：筛选管线目录目前**不在任何 git 仓库跟踪范围内**，无独立 tag——引用版本时需写 v2.2 + 快照

**状态**：【✓ 照抄即可】

---

## 13. 归属与引用

**建议英文标题**：`13. Attribution & Citation`

**要写什么**
- 自有工作 vs 第三方依赖的明确分界（iGEM 归属要求）
  - 第三方：SCimilarity（Genentech）、Captum、GEARS、scipy/scanpy、ClinGen/gnomAD/HPA/DeepLOF 数据
  - 自有：管线四层架构与全部模块、CIPHER 引擎实现、VirtualCellTool 前端与 API、方法学修复（余弦对齐度公式等）
- 每条第三方依赖的许可证 + 原始文献 DOI
- 引用格式（可参考 `ATTRIBUTIONS.md`、`docs/api/ai_scores.md`）
- 【○ 待补】本项目的正式引用条目 / DOI / 代码仓库地址

**状态**：【◐ 需重写】（`ATTRIBUTIONS.md` 已有登记，需整理成表）

---

## 14. 附录

**建议英文标题**：`14. Appendix`

| 附录 | 内容 | 状态 |
|---|---|---|
| A | 数据源清单与 URL/checksum | 【✓】`config/sources.json` |
| B | 全参数默认值速查表 | 【◐】从 `pipeline.yaml` 抄 |
| C | 目录结构说明 | 【✓】两份 README |
| D | 术语表（pLI / LOEUF / HI / SINEUP / CIPHER / 补偿状态…） | 【◐】可参考 `outputs/reports/管线文档/名词解释_WBS筛选管线报告.md` |
| E | API 端点全表（19 个） | 【✓】`docs/ARCHITECTURE_v3.md` 第三节 |
| F | 测试与回归说明 | 【✓】`tests/` + `tests_e2e_playwright.py` |

**状态**：【◐ 待整理】

---

## 15. 待补清单（写正文前需先产出）

- 【○】对外发布方式（仓库地址、许可证、DOI）— 影响 §12/§13
- 【○】快速上手与端到端示例的**截图**（§4/§10）
- 【◐】每个配置权重的来源依据（§6）
- 【◐】把 `ATTRIBUTIONS.md` 整理成归属表（§13）
- 【○】英文翻译（全文）
- 【◐】确认是否有对外复用的使用者反馈/测试案例（iGEM 很看重"别人真的用了吗"）

---

## 附：写作顺序建议

1. **§2（环境与陷阱）+ §11（排查）** —— 最实用，也最容易写
2. **§6（配置）+ §8（输出解读）** —— 使用者真正要查的两张表
3. **§9（VirtualCellTool 手册）** —— 界面与 8 类图表读法
4. **§4 + §10（示例）** —— 依赖截图，稍后补
5. 最后 **§12/§13**（依赖对外发布方式）
