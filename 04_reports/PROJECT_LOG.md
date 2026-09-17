# 项目日志 — 染色体微缺失主效基因筛选管线

> 项目代号：iGEM SINEUP Microdeletion Gene Prioritization Pipeline
> 关联文档：`架构设计_v2.md` · `工程化指导书 v1.md` · `管线现状与Williams主效基因筛选实验总结_2026-09-05.md` · `derived/tools/VirtualCellTool/docs/HANDOFF_v3.md`
> 维护规则：每次重大决策/转折/里程碑追加一条目。时间倒序。不删除历史条目。

---

## 条目 #17 — 2026-09-14（管线 v2.2 架构文档 — 补上缺失的实施文档）

### 背景

用户问「像 `架构设计_v2_通用微缺失主效基因筛选管线.md` 这样的管线文档，有没有更新后的版本」。核查结论：**没有**——最新架构文档停留在 v2.0（2026-09-07），而代码已到 v2.2，中间存在**双向脱节**。

### 脱节清单（写作前逐项核对代码）

**v2.0 描述了但从未实现（9 项）**
`src/extract_genes.py`（Module A 区间→基因）· `config/intervals.yaml` · `config/known_drivers.yaml` · `src/phenotype_grouper.py`（表型分组）· `src/report.py` · `outputs/candidates_by_phenotype/` · 五维证据面板与证据等级（★★★/★★☆/★☆☆/⚠️）· HPA 双重角色标签（`hpa_target_support`/`hpa_safety_flag`）· `tests/test_extract_genes.py`、`test_phenotype_grouper.py`

**关键冲突**：v2.0 §4.4 声明「v2 不再产出单一的 `consensus_score` 排名」——实际 `ranked_wbs_modeC.csv` 中 `consensus_score` 列仍在，且无任何 phenotype 列。即核心设计变更未落地。

**已实现但 v2.0 未记录（v2.1/v2.2）**
`compensation.py`（mRNA 补偿）· `filter_recessive.py`（隐性基因过滤）· ClinGen 三值标注 · 权重敏感性分析 `--sensitivity` · 四 mode 真实行为化 · 正对照检验表 · 稀疏性警告 `--warnings` · HPA 惩罚权重置 0 · normalize 改 raw · 实验建议生成器

### 新文档

**`outputs/reports/管线文档/架构设计_v2.2_通用微缺失主效基因筛选管线.md`**（513 行）

结构：0 与 v2.0 的关系（先读）· 1 设计原则（9 条，逐条附实现状态）· 2 实际数据流架构图 · 3 模块详解（L0/L1/L2/L3 + 补偿 + 隐性过滤 + CNV）· 4 配置参考（逐键表）· 5 输出与字段解读 · 6 运行模式（**实际行为**）· 7 版本变更记录 · 8 未实现清单（9 项，标注是否仍需）· 9 为什么机制层不能回补排序 · 10 已知限制与待办 · 附录 ABC

**每节标注实现状态**：✅已实现 / ⚠️部分实现 / ❌未实现。

### 写作中澄清的两处实现真相（v2.0 描述有误）

1. **`auto` 不会自动解析成 A/B/C/D**。实际含义 = 「正对照检验 + 稀疏警告」，是一组独立行为，不是"数据丰富度自动检测"（v2.0 §2/§8 描述不符）。
2. **Mode C（`full`）与 Mode B（`rank`）当前行为相同**，仅报告标签不同。补偿集成靠 `--compensation` 参数启用，**不由 mode 决定**。

### 验证（文档内命令全部实测）

| 文档 §6 示例 | 实测结果 |
|---|---|
| Mode B（`--mode rank --controls --sensitivity`） | 35 行；报告含正对照检验表（命中 **4/4**）+ 权重敏感性段落 |
| Mode C（`--mode full --compensation`） | 35 行；报告含补偿状态段 |
| Mode A（WHS `--mode validate`） | 19 行；**NSD2 #1**；验证结论「✓ 通过 — 已知主效基因满足 SINEUP 靶向条件」 |

另核对：DeepLOF 覆盖 28/35、ClinGen 覆盖 14%（5/35）、测试 20 passed / 1 skipped、HPA 实际只 pivot 出 liver/kidney 两列（脑列未映射，列为**高优先级待修**）。

### 处置

- 新文档写入 `管线文档/`
- v2.0 文档**保留不删**，头部加"已被取代"说明指向新文档（遵循"不删除历史"惯例）
- §8 保留全部未实现设计待决策；§10.3 列出 7 项工程待办并标优先级

**产出**：新增 `outputs/reports/管线文档/架构设计_v2.2_通用微缺失主效基因筛选管线.md`；修改 `架构设计_v2_通用微缺失主效基因筛选管线.md`（加取代说明）

---

## 条目 #16 — 2026-09-14（iGEM wiki 大纲：Model 页 + Document 页）

### 背景

用户在完成 #15 的一致性对齐后，要求起草 iGEM wiki 两页的**大纲**（正文后续填充），并明确项目仍处于未完全开发状态。

### 产出

`outputs/reports/wiki/`（.md + .html 成对落盘）：

**`wiki_Model_页面大纲.md`** — 筛选项目的**原理与开发过程**，10 节：
0. 页面定位 · 1. 问题定义 · 2. **为什么必须建专用管线而不是跑现成 AI**（用项目自身负结果论证）· 3. **四层证据金字塔原理** · 4. **开发过程：DBTL 七轮循环** · 5. 验证（正/负对照）· 6. 与湿实验/治疗设计的接口 · 7. 局限与未来工作 · 8. 可复现性 · 9. 图表清单 · 10. 待补清单

**`wiki_Document_页面大纲.md`** — 工具**说明书**（README 风格），15 节：
概览 · 系统要求与**已知陷阱表** · 安装启动 · 快速上手 · 输入准备 · **配置参考表** · 运行模式 · **输出字段解读** · **VirtualCellTool 使用手册（含 8 类图表读法）** · 端到端示例 · 故障排查 · 版本与变更 · 归属与引用 · 附录 · 待补清单

### 起草时的关键设计决定

1. **每节标注完成度**（【✓可落笔】/【◐待整理】/【○待补】），使大纲同时充当进度表——用户明确要求"只需大纲"，因此把"哪些能直接写、哪些还缺素材"显式标出。
2. **Model 页把负结果放在核心位置**（§2）：r=0.02、GEARS 4/41 覆盖、Nature Methods 2025 基线——用这些论证"为什么自建管线"，而非作为需要隐藏的失败。这与项目一贯的**负结果叙事**一致。
3. **Document 页重点写"最容易误读的地方"**：LOEUF 低才对、ws/ms 的"细胞类型"实为病健分组、IG 归因正负号只表方向——这些是 #14/#15 实际踩过的解读陷阱。
4. **两页都建议正文用英文**（iGEM 评审为英文），中文作为草稿语言。
5. **显式记录未完成项**：对外发布方式（仓库/许可证/DOI）、截图、权重来源依据、英文翻译——列入各页"待补清单"。

### 状态

大纲阶段，正文待填充。写作顺序建议已附在各文件末尾（先写素材最全的节）。

**产出**：`outputs/reports/wiki/wiki_Model_页面大纲.{md,html}`、`wiki_Document_页面大纲.{md,html}`

---

## 条目 #15 — 2026-09-14（文档/代码/日志一致性审计 — 12 处不一致 + 修正）

### 背景

用户观察到「项目中的文档、代码和日志不匹配」，要求对齐。逐文件核对 `derived/tools/VirtualCellTool/`（代码 853 行 app.py + 976 行 index.html）与 `outputs/igem_gene_pipeline/`（代码 + config + tests），并以**实际运行**验证日志中的数值声明。

### 审计发现的 12 处不一致

**VirtualCellTool（8 处）**

| # | 位置 | 文档/日志说法 | 代码实际 | 处理 |
|---|---|---|---|---|
| A1 | `web/app.py` docstring | "v2.2 单服务多数据集"，只列 6 个端点 | v3.3，19 个端点 | ✅ 已改：完整端点分组 + 版本锚点 |
| A2 | `web/index.html` | 版本标签 `v3`、注释 "v3.1 前端" | v3.3 | ✅ 已改为 v3.3 |
| A3 | `README.md` | 只描述 v1 三个功能；「升级路径：GEARS 两段式架构」；目录结构缺 4 个引擎文件；快速开始用 `pip install` | 5 引擎 + 19 端点 + 8 处图表；GEARS 已是**负对照** | ✅ 全量重写 |
| A4 | `docs/ARCHITECTURE_v3.md` | "8 个端点"、"app.py 380 行 8 个路由组"、缓存 "192MB" | 19 端点、853 行、105/104/12MB | ✅ 全量重写为 v3.3 |
| A5 | `docs/HANDOFF_v3.md` §4.4 | 列 11 个端点 | 19 个（缺 search_genes/cell_gene_expr/gene_expr/gene_in_cipher/gene_expr_map/attribution_map 等） | ✅ 补齐 |
| A6 | `docs/HANDOFF_v3.md` §4.5 | 描述 `renderHeatmap()`/`renderCellTypes()`/`renderSummary()` | 这三个函数**已不存在**（v3.1 重写为 `renderPerturbFigure` + 标签页） | ✅ 改流程 + 加警示 |
| A7 | `docs/HANDOFF_v3.md` §7 待完成 | 3 项已完成仍列为待办 | GEARS 负对照标注、Williams 实测、图表持久化**均已完成** | ✅ 移入已完成 |
| A8 | `docs/HANDOFF_v3.md` §6.2 | 缓存 "~138MB"、删除后重建 "0.3s" | 实测 105/104/12MB；字段数也少写 | ✅ 更正 |

**igem_gene_pipeline（4 处）**

| # | 位置 | 说法 | 实际 | 处理 |
|---|---|---|---|---|
| B1 | 本日志条目 #13 | 「确认管线为 **v2.1**」 | 代码自述 **v2.2**（`consensus_v2.py`） | ✅ 见下方更正 |
| B2 | 管线 `README.md` 快速开始 | 产出写 `outputs/candidates_ranked.csv` + `outputs/report.md`（根目录） | 实际产物按主题归档到 `outputs/{wbs,whs,mode,cnv}/`，根目录无此文件 | ✅ 改为归档路径 + 说明 |
| B3 | 本日志条目 #1 | "tests/（**27+ 测试**）" | 实际 pytest 收集 **21** 个（20 passed / 1 skipped） | ✅ 见下方更正 |
| B4 | 本日志条目 #2 | "CNV 工作流 **22/22** 测试通过" | 实际 **20 passed, 1 skipped**（21 收集） | ✅ 见下方更正 |

### 已实施的修正

**代码（行为不变）**
- `web/app.py` docstring 更新为 v3.3 + 完整端点分组
- `web/index.html` 版本标签 → v3.3
- `src/consensus_v2.py` `--mode` 帮助文本补上漏掉的 `full`（Mode C）

**文档**
- `VirtualCellTool/README.md`：全量重写（5 引擎矩阵、3 数据集与分组语义、8 类图表、局限声明、版本锚点表）
- `docs/ARCHITECTURE_v3.md`：全量重写（19 端点全表、标签页渲染流程、缓存实测大小、**九、关键约束**章节汇总 6 条踩过的坑）
- `docs/HANDOFF_v3.md`：标题→v3.3；新增「0.2 v3.2/v3.3 记录」；§4.4/4.5/6.2/7 全部对齐
- `igem_gene_pipeline/README.md`：版本声明 v2.2、产物归档路径、四 mode 表、`uv add --dev pytest`、注明本目录无独立 git tag

**环境**
- `igem_gene_pipeline` 补装 `pytest`（dev 依赖）。此前 README 声称有 pytest 测试但环境里根本没装——`uv run pytest` 直接失败

### 日志自身更正（本条生效，历史条目不改写）

- 条目 #1 的「27+ 测试」→ **21 个用例**（20 passed / 1 skipped）
- 条目 #2 的「22/22 测试通过」→ **20 passed / 1 skipped**
- 条目 #13 及 #14 中的「管线 v2.1」→ **v2.2**（config 注释仍写 v2.1，代码自述 v2.2；以代码为准）

### 待用户决策（未擅自改动）

| 项 | 问题 | 风险 |
|---|---|---|
| `consensus_v2.py` 回退默认值 | 代码第 60 行硬编码 `"normalize": "rank"`，但 config 已按 #3/#13 决策改为 `raw` | **配置键缺失时会静默回退到有 bug 的 rank 归一化**（正是 #2/#3 记录过的伪影来源）。建议改为 `raw`，但属科学默认值变更，等确认 |
| 两个孤立端点 | `/api/celltype_response`、`/api/perturb_baseline` 前端未调用（功能被 `perturb_summary`/`perturb_compare` 覆盖） | 保留供 CLI 使用已在文档标注；若确定不用可删 |

### 验证

- `uv run pytest tests/ -q` → **20 passed, 1 skipped**
- VirtualCellTool 端到端（Playwright 15 项断言）→ 全绿、零控制台错误
- 端点实测：19 个端点中 17 个前端在用，2 个标注为 CLI 专用

**产出**：修改 `derived/tools/VirtualCellTool/{README.md, web/app.py, web/index.html, docs/ARCHITECTURE_v3.md, docs/HANDOFF_v3.md}`、`outputs/igem_gene_pipeline/{README.md, src/consensus_v2.py, pyproject.toml}`

---

## 条目 #14 — 2026-09-13（VirtualCellTool 修复 — 从不可启动到全结果可视化）

### 背景

用户要求打开 iGEM 项目的 VirtualCellTool，随后指出「用 kdense 改过这个工具，但最终前端没有很好的效果」，要求依据 `derived/tools/VirtualCellTool/docs/HANDOFF_v3.md` 修复。实测发现问题比「前端效果不好」严重得多：**工具根本无法启动**——进程加载默认数据集后无限卡死，前端看到的自然只有白屏。

分三轮完成（v3.1 修复 → v3.2 位移可视化 → v3.3 全结果可视化），每轮均以 Playwright 真实浏览器端到端测试验证。

### 第一轮 v3.1 — 四个致命 bug（工具不可用）

| # | 问题 | 根因 | 修复 |
|---|---|---|---|
| F1 | **启动无限卡死** | `_load_dataset` 用 `X.toarray()` 稠密化；ws = 96969×28231 float64 ≈ **21.9 GB**，直接打爆内存进 swap | 全程保持 CSR 稀疏（float32），新增 `_sparse_col_var()` / `_row()` 稀疏工具函数；仅在 5000 HVG 子矩阵上稠密化（~2 GB） |
| F2 | CIPHER 缓存永远失效 | 写盘只存 `gene_list/ctrl_mean/Sigma`，读取却访问 `c["hvg_idx"]` → KeyError → 每次启动全量重算 | 缓存补存 `hvg_idx` + `full_mean`；识别旧格式自动重建 |
| F3 | 缓存加载后仍重算 | 缓存分支末尾**缺 `return`**，继续往下执行全量拟合 | 加载成功立即返回 |
| F4 | 多数据集结果互相污染 | `cipher_eng` / `baseline_eng` 是模块级**全局单例**，切数据集时后加载的覆盖先加载的协方差矩阵 | 改为 `_CIPHER_ENGINES[ds]` / `_BASELINE_ENGINES[ds]` 按数据集独立实例 |

**前端 bug（「效果不好」的直接原因）**：所有 `fetch` 不带 `ds` 参数（切数据集后仍打默认库）；切数据集靠整页跳转导致状态全丢；图表容器运行时 `createElement` 插进 330px 侧边栏被挤成一条；每点新基因旧图被 `newPlot` 覆盖无法对比；基因不在 HVG 集时只回干巴巴的 400。→ 重构为「左控制栏 + 右工作区」+ 标签页系统，统一 `api(path, params)` 自动注入 `ds`。

**方法学修复（让图表有判别力）**：细胞类型响应排序原用「该类型 Top500 高表达基因的 |Δ| 均值」，但各类型高表达基因几乎都是核糖体/管家基因、高度重叠，导致所有类型得分几乎相同（MS4A1 敲低时 B 细胞只排第 3，与第 1 名差距 <5%）。改为**类型特异谱与扰动效应谱的余弦对齐度**：

```
w_ct[g] = max(0, expr_ct[g] − mean_over_celltypes[g])       # 类型特异富集量
response = Σ w_ct[g]·|Δ[g]| / (‖w_ct‖·‖|Δ|‖)                # 余弦对齐
```

两个关键细节：基准用**各类型均值的均值**而非全体细胞均值（否则最大细胞群——PBMC 里 T 细胞占 45%——会把基准拉向自己）；用**余弦**而非加权均值（否则本身高表达的类型如单核细胞 LYZ/S100A9 在任何扰动下都拿最高分）。

**实测**（PBMC 12 个标志物基因敲低，看最敏感类型是否命中已知归属）：Top1 命中率 **~2/12 → 10/12**，平均排名 ~3.0/5 → **1.33/5**。未命中的 CD3D/CD3E 是 CIPHER 线性响应的固有局限（PBMC 中表达稀疏、协方差信号弱），非代码 bug，已在文档标注。

**数据语义修正**：ws/ms 的 `meta.cell_type` 列装的其实是**病健分组**（WS vs CTRL / MS vs normal）而非细胞类型。新增 `DATASETS[ds]["group_label"]` 显式声明，前端图表标题与按钮文案自动跟随，避免把「病健分组响应」误标成「细胞类型响应」。

**默认数据集** `ws` → `pbmc`（2700 细胞秒开），ws/ms 懒加载。**冷启动从无限卡死变 6.2 s；Williams 96,969 细胞加载 5 s。**

### 第二轮 v3.2 — 反事实位移可视化

用户反馈「反事实扰动的前后对比不够明显」。初判为视觉问题，排查后发现是**计算层 bug**：`_FakeReducer` 用 **k=1 最近邻**反查 UMAP 坐标，坐标被「吸附」到某个已有细胞上——只要扰动后嵌入的最近邻没换人，输出坐标与扰动前**完全相同**。对照实验（人为施加不同量级位移）：

| 施加位移 | k=1 最近邻（旧） | kNN 插值（新） |
|---|---|---|
| 0.01 | Δ=0.00000 | 0.01057 |
| 0.024 | Δ=0.00000 | 0.05033 |
| 0.1 | Δ=0.00000 | 0.18683 |
| 0.3 | **Δ=0.00000** | 0.24272 |

即使 0.3 量级位移仍纹丝不动。**修复**：改为 k=15 反距离加权插值，坐标连续可微。实测 MS4A1 敲低 UMAP 位移 0 → **0.0451**；Top5 联合 → **0.1093**；GTF2I(ws) 过表达 → **0.2983**。

> 自我更正：v3.1 阶段我曾加过一句「扰动幅度不足以在 UMAP 上移动」的提示——那是在为 bug 辩解，不是物理限制。

**可视化**：新增 `_zoom_window()`（按位移长度自适应的局部视窗）与 `_local_neighbors()`（邻域背景细胞作参照系），前端 `showMove` 重写为**全景 + 放大镜双视图**——左侧全景定位并画取景框，右侧放大到视窗（单基因 0.70 单位 / 联合 1.31 / GTF2I 3.58），含「⚫扰动前 → ⭐扰动后」标注与迁移箭头。

### 第三轮 v3.3 — 把剩余文字结果全部可视化

用户问「能否把其他不是反事实扰动的结果也可视化」。盘点后发现四类结果只有文字：

1. **🎨 基因表达分布图**（新增端点 `/api/gene_expr_map`）：左=UMAP 按表达量热力着色，右=各分组表达水平 + 表达细胞百分比。**对全部 28231 个基因可用，不受 CIPHER 仅覆盖 5000 HVG 的限制**——建议作为分析第一步先确认基因在该组织是否表达。
2. **📊 归因结果图**（新增端点 `/api/attribution_map`）：左=IG 归因强度，右=该细胞 vs 全体均值表达对比（蓝条远高于灰条 = 特异富集），替代侧栏挤不下的小表格。
3. **🎯 质心距离图**：联合扰动的细胞身份归属，扰动前/后分组对比条形，原为状态栏纯文本。
4. **🧪 GEARS 因果预测图**：上调/下调条形，图上直接标注「训练自 Norman/K562，对非造血细胞为域外推断」的负对照定位。

**解读陷阱修正（重要）**：归因图中 MS4A1（B 细胞标志物）显示为**负值**，而旧标注写「模型认为哪些基因**定义了**这个细胞」、红色表负值——这个组合几乎必然被误读成「MS4A1 是负面因素」。查证 `attribute.py` 确认：IG 归因目标是 `embedding.sum()`，**正负号只表示把嵌入分量推高还是推低，与「是否标志基因」无关**，排序用的是 `|IG|`。已改为橙/紫配色（红绿对色盲不友好且红=负易误读）+ 标注「重要性看条形长度，颜色仅表方向」+ 状态栏明示「B 细胞标志物出现负号是正常的」。此类符号误读若带进答辩会很被动。

### 与筛选管线的衔接（实测验证）

管线 `outputs/mode/ranked_wbs_modeC.csv` 的 WBS Top12 中，**10 个**在 Williams 类器官数据集可被 CIPHER 预测（VPS37D、POM121 不在 HVG 集）。在 ws 上按 SINEUP 方向（`direction=oe`）实测：

| 基因 | 管线排名 | \|Δ\|max | 受影响最大的基因 | 解读 |
|---|---|---|---|---|
| GTF2I | #9 | **10.08** | SYT1, IGFBPL1, BCL11A, STMN2, NRXN1, CNTNAP2 | 效应量远超排名且**全打在神经发育/突触基因**上；WS 核心表型正是神经认知障碍 → 优先级建议上调 |
| BAZ1B | #4 | 2.63 | HMGN2, GOLGA4, APP | 效应真实，方向偏染色质/细胞器 |
| STX1A | **#1** | 1.00 | STMN2, GRIA2, SYT1 | 排名第一但效应中等，靶向突触 |
| ELN | #3 | **0.006** | SOX2, ID4, TTYH1 | 脑内对照表达仅 0.042，**比 GTF2I 小三个数量级**——ELN 负责主动脉瓣上狭窄（心血管表型），本就不在脑表达 |

**两点可直接进 Model 页面的发现**：
- **管线排名 ≠ 组织内效应量**。GTF2I 的排名分歧（#9 vs 效应量第一）是两条互相独立的证据链（数据库遗传学证据 vs 单细胞共表达）产生的有意义不一致，值得单独论证。
- **ELN 的负结果是工具诚实性的体现**，不是失败：它正确识别出组织特异性，提示研究 ELN 必须换心血管/成纤维细胞数据集。暴露了「组织选择」这一常被忽略的实验设计维度。
- 补充：GTF2I 过表达时 **CTRL 响应 0.45 vs WS 0.27**，患者细胞对该信号的响应能力更弱，提示 SINEUP 干预可能存在**时间窗**（假设，未验证）。

### 验证与版本

Playwright 真实浏览器端到端测试 **15 项断言全绿、零控制台错误**（选细胞→归因→CIPHER 敲低/过表达→线性基线→反事实位移→切数据集）。测试脚本落库 `tests_e2e_playwright.py`，后续改动可直接回归。

git tag：`v3.1-fixed`（可启动 + 前端可用 + 响应排序有判别力）、`v3.2-zoom`（位移双视图）、`v3.3-viz`（全结果可视化）。历史锚点 `v1.0-scimilarity` / `v2.0-gears` 保留。

**性能对比**：冷启动 无限卡死 → **6.2 s**；Williams 96,969 细胞 OOM → **5 s**；CIPHER 预测 0.02–0.1 s；二次启动从「每次全量重算协方差」→ 缓存真正生效。

**产出**：修改 `derived/tools/VirtualCellTool/web/app.py`（新增 `/api/gene_expr_map`、`/api/attribution_map`、`/api/gene_in_cipher`）、`web/index.html`（全量重写）、`src/linear_baseline.py`（新增 `fit_stats()` 免持有大矩阵）、`启动VirtualCellTool.command`；新增 `tests_e2e_playwright.py`；`docs/HANDOFF_v3.md` 新增第 0 节修复记录。

**待办**：CD3D/CD3E 未命中的方法学边界需在汇报中如实标注；CellOracle Web 集成、pertpy 可视化、decoupler 通路富集仍未接入（沿用 HANDOFF_v3 待办清单）。

---

## 条目 #13 — 2026-09-13（六 mode 实证 — 正对照全通过 + config 修正 + 归档）

### 重新跑 WBS/WHS 验证四个 mode 是否都有用

**背景**：用户问「管线是否 v2.1？能否重跑 WBS+WHS 看三个 mode 是否都有用」。确认管线为 v2.1 后，用户批准：按架构四模式全测（WBS A/B/C、WHS A/B/D），且先实现 mode 差异再跑。

**mode 差异实现**（`consensus_v2.py`）：`--mode` 从纯元数据标记升级为真实行为差异——validate 输出验证报告面板（已知主效基因 ClinGen/pLI/SINEUP 靶向条件表）；rank 输出正对照检验表；exploratory 输出探索声明且不给实验建议；正对照检查（in_candidates/rank/top10/共识/证据）全 mode 通用。

**WHS 结果（19 基因 chr4:1.8–3.0Mb）**：A/B/D 三 mode 全部 NSD2 #1（score 3.889，领先第2名 1.91）——清晰通过。

**WBS 初始失败（正对照 1/4）→ 定位到两个 config 未落实的设计修正**：
1. **HPA 器官惩罚错杀正对照**：pipeline.yaml 仍保留 -2/organ 惩罚，STX1A/ELN/GTF2I 等因 liver/kidney 高表达被罚 -4，低表达噪声（FZD9/FKBP6）不罚 → v2.1 设计「HPA 从惩罚层改为双重角色」本已决定移除，config 未跟进 → **修复**：`consensus_v2.hpa_penalty` 权重置 0
2. **rank 归一化伪影**（FZD9 pLI=0.002→#1 再现）：PROJECT_LOG #3 已记录 rank→raw 修正，config 仍为 rank → **修复**：`consensus_v2.normalize = raw`

**修复后 WBS 三 mode 全部 6/6 正对照命中**：STX1A #1、ELN #3、BAZ1B #4、CLIP2 #5、LIMK1 #8、GTF2I #9（Top5 仅 VPS37D 一个非正对照，pLI=0.92 合理次优非伪影）。

**关键副产物**：
- **ELN gnomAD pLI=2.14e-14 是数据原始值**——经典单倍剂量不足基因 pLI 被低估（CNV 机制不敏感），ClinGen HI=3 才是主证据；Mode A 面板诚实并排「HI✓ pLI✗」双信号
- **WBS 补偿状态实证**：35 基因 17+ overcompensated、ELN ratio=3.138（此前仅测 GTF2I=0.995 等少数）——新观察，建议后续专项核对

**归档**：outputs/ 按主题重组为 `wbs/`（v2/v2.1 主实验）、`whs/`（WHS 实证）、`mode/`（六 mode 验证 + `diagnostics/` 中间产物，保留不删）、`cnv/`（config 引用路径不动）；新增 `outputs/README.md` 索引；`docs/ARCHIFY_流程讲解.md`、集成文档中的文件引用同步更新。

**产出**：`outputs/mode/report_{wbs,whs}_mode{...}.md`（六份）、`outputs/mode/compensation_wbs.csv`、`outputs/mode/evidence_wbs_modeA.parquet`；修改 `src/consensus_v2.py`、`config/pipeline.yaml`（备份 `/tmp/pipeline.yaml.bak`）

---

## 条目 #12 — 2026-09-12（虚拟细胞工具选型 — 决策）

### 基于四份调研文档的工具组合推荐

**背景**：用户完成四份调研（AI 虚拟细胞扰动预测工具 / 单细胞扰动可视化 / 选型建议 / 知乎 scPerturBench 基线解读），要求据调研判断 iGEM 项目的最佳工具组合。

**推荐组合**：
1. **预测/假设层（L3）**：CellOracle（保留，VCT 资产）+ CIPHER（新增，仅需未扰动控制细胞、支持 CRISPRa 激活方向、AUROC 0.92）+ linearModel（强制对照，呼应 Ahlmann-Eltze 基准）
2. **GEARS 转为负对照**：项目已证明 4/41 疾病基因覆盖失败，保留为「我们测试过」的叙事证据
3. **可视化层**：pertpy（Mixscape/Augur/CINEMA-OT/扰动空间）+ Scanpy + CELLxGENE（全程 h5ad）+ decoupler（通路）
4. **明确不选**：State/Stack（2026 preprint 需 GPU）、CellFlow/PerturbNet（需配对扰动数据）、Geneformer（输出排序≈归因路线）、PerturbDiff（无代码）、Squidiff

**选型三过滤器**：F1 数据现实（无扰动训练集、WHS 零 scRNA-seq）→ 只选仅需未扰动数据的；F2 治疗方向（SINEUP=激活+翻译层）→ 优先 CRISPRa 支持；F3 领域铁律（深度未超线性基线）→ 强制对照 + 负对照叙事。

**必须标注的风险**：翻译层盲区（CIPHER 对补偿基因 GTF2I/NSD2 可能隐身）；激活预测 ≠ 蛋白恢复；定位 = L3 假设 + 演示，不进 L1 排序。

**产出**：`outputs/reports/虚拟细胞/虚拟细胞工具组合推荐_igem决策_2026-09-12.md`（note: user has not yet reviewed/confirmed this recommendation）

---

## 条目 #11 — 2026-09-12（WHS 实证运行 — 正对照检验 + 管线修复）

### WHS 数据跑管线：发现并修复符号别名缺口，NSD2 升至 #1

**背景**：用户要求用 WHS 数据实测管线能否输出文献主效基因 NSD2。

**执行**（用户批准参数：跑两次对比、v2 注册区间 chr4:1.8–3.0Mb 共 19 基因、rank 模式不告知 NSD2）：
- **Run A（原样）**：NSD2 排 **#5/19**——发现管线 bug：gnomAD 表用旧符号 *WHSC1* 存 NSD2 数据（pLI=1.0、LOEUF=0.119），`merge_evidence.py` 的 gnomAD 分支按 input_symbol 精确匹配（NSD2#≠WHSC1）→ 最强约束证据被静默丢弃（匹配率 17/19，无人察觉）
- **修复**：merge_evidence gnomAD 分支改为先用 hgnc_aliases（含 prev_symbol/alias）把符号解析为 HGNC ID 再按 hgnc_id 合并（18651/19704 解析成功）；另修复 normalize/merge 对带空白列名别名表的读取（项目重建后文件与代码脱节）
- **Run B（修复后）**：NSD2 **#1/19**，consensus=3.889 vs 第2名 1.978（领先 1.91），Borda rank 一致；纯 L1 无 AI 亦 #1（2.889 vs 1.111）

**发现**：
1. 管线不会虚报——缺证据时 NSD2 只排第 5，修复后升顶；
2. 正对照检验真实有效——文献已知的 NSD2 成为管线标尺，这正是 Mode B 正对照设计（TBX1/ELN/KCTD13/RAI1）的实证；
3. 副产物：rank 归一化小样本伪影再现（FAM193A pLI=0.999 无 AI 时掉到第 5）；HPA 只用了 liver/kidney 两器官（脑组织列名未进器官清单）。

**产出**：`input/candidates_whs.csv`、`outputs/candidates_ranked_whs_{A,B,B_noai}.csv`、`outputs/report_whs_B.md`、修改 `src/merge_evidence.py`、`src/normalize.py`

---

## 条目 #10 — 2026-09-12（WHS/NSD2 证据链核实 — 叙事支撑）

### NSD2 主效基因确立过程 + 三处引文修正

**背景**：用户提问「文献如何确定 NSD2 是 WHS 主效基因」（WBS 开发管线、WHS 湿实验验证需要叙事一致性）。

**证据链**（6 步，DOI 全部核实）：
1. 历史临界区映射（WHSCR ~165kb / WHSCR-2 300–600kb）→ 候选基因缩到几个
2. Andersen et al. 2014：WHSC1(NSD2)+LETM1 缺失「必要不充分」（doi:10.1038/ejhg.2013.192）
3. Barrie et al. 2019：3 例 de novo LOF 单基因患者呈现 WHS 子集表型（doi:10.1101/mcs.a004044）——转折点
4. Genet Med 2021：18 新 + 10 既往患者，NSD2 变异→H3K36 甲基化活性降低（doi:10.1038/s41436-021-01158-1）
5. Cortellazzo Wiel et al. 2022：「shifting paradigm」综述（doi:10.1186/s13052-022-01267-w）
6. Kinoshita et al. 2024：Nsd2 KO 小鼠突触基因失调 + H3K36me2 重分布（doi:10.3389/fgene.2024.1308234）

**重要修正（叙事严谨性）**：NSD2 不是 WHS「唯一」主效基因，而是拿到「单基因变异+功能+小鼠模型」三重证据的主效基因；WHS 整体是连续基因综合征（Cortellazzo Wiel 2022 原文确认）。此前的「单基因功能缺失→完整核心表型」「唯一主效基因」表述过强。**另更正三处引文作者错误**：Tassano E→**Cortellazzo Wiel L 等**；Kimura S→**Kinoshita S 等**；Zanoni P→**Barrie ES 等**。

**产出**：`outputs/reports/管线文档/WHS主效基因NSD2证据链与叙事指南_2026-09-12.md`（含 WBS 开发/WHS 湿实验分工叙事 + 答辩要点）

---

## 条目 #9 — 2026-09-12（虚拟细胞文献调研）

### 虚拟细胞能否承担药物效应模拟与基因扰动——文献综述与可行性判定

**背景**：用户问「这一块工作有没有可能用虚拟细胞做」，要求调研虚拟细胞在药物效应模拟与基因扰动方面的文献并生成报告。

**核心结论**：
1. 领域自我证伪：Nature Methods 2025 基准——5 个 foundation models + 2 DL 模型在基因扰动转录预测上均未超过简单线性基线，且存在 mean collapse（动脉本文 doi:10.1038/s41592-025-02772-6）——与项目 E3/E4 (r=0.02)、E11 (GEARS 4/41) 负结果同构，即「计算筛选不可靠」是领域级事实而非团队方法学失误
2. 药物效应：chemCPA/CPA 有剂量-响应能力但限训练分布内；AetherCell/TwinCell/StateXDiff 为 2026 preprint；ProteinTalks（蛋白层，Nature 2026）是唯一触及翻译层盲区的虚拟细胞
3. 机制全细胞模型（Karr 式）只适用于细菌/酵母，人类细胞不可操作
4. SINEUP 治疗场景（胚系杂合缺失 + RNA binder 翻译层上调）在公开 perturb-seq 数据中不存在 → OOD 最困难情形

**判定**：虚拟细胞定位 = L3 机制假设生成器 + iGEM 演示层 + 旁路毒理筛查（VCell/VCBA）；不上移进 L1 发现/排序。推荐低成本「基准对比小实验」把负结果转化为贡献叙事。

**产出**：`outputs/reports/管线文档/文献调研_虚拟细胞药物效应与基因扰动_2026-09-12.md`、`outputs/literature/bibliography/virtual_cell_review_bibliography.md`（24 条 DOI 状态标注）

---

## 条目 #8 — 2026-09-12（VCT 定位 — 决策）

### VirtualCellTool 最终定位：L3 机制假设 + 交互可视化交付层

**背景**：用户询问「先前的 VirtualCellTool 工具，最终在我们的管线中的定位怎样比较合适」。

**定位结论**：VCT = **L3 机制假设 + 决策支持可视化/演示层**，严格单向位于 L1（遗传学证据层）和 v2.1 新增的「mRNA 补偿状态」维度之下游。

**排除的候选位置**（依据项目自身实验证据）：
- ❌ 发现引擎/候选生成器：E3/E4 (r=0.02)、E11 (GEARS 4/41) → VCT 永远不能回补候选
- ❌ L2 验证门/acceptance gate：E8 mRNA 隐身、归因≠因果 → VCT 裁决无效力
- ❌ 与 L1 并列的证据维度：信息源与转录组重叠，重新引入 E3/E8 偏倚
- ✅ L3 机制假设 + 可视化交付：遗传学先验 → 机制后果 what-if 反注，VCT 唯一不可替代的能力

**四个落点**：① 单向输入契约（L1 candidates_ranked.csv + compensation_status 作数据源，旧 Δattr/DE 路径废弃或 legacy）；② 机制反注输出（标注「未验证假设」）；③ SINEUP 靶向决策面板（补偿状态 × L1 证据 × 机制假设三列可视化）；④ iGEM 交付/演示层（7GB 交互 demo 重新定位为沟通工具）。

**产出**：定位建议已记录 notebook；尚未落档 ADR（用户后续在 #12 提供调研文档后推荐了具体工具组合）

---

## 条目 #7 — 2026-09-07（DBTL Cycle 4 — Build）

### 管线 v2.1 代码实施

基于质询回答中的六项优化，在现有代码基础上实施了管线 v2.1：

1. **`src/filter_recessive.py`**（新模块）— OMIM 隐性致病基因过滤器
2. **`src/compensation.py`**（新模块）— mRNA 补偿状态分析
3. **`src/merge_evidence.py`** — ClinGen 三值标注（保留原始分数，30/40/null→中性不扣分）
4. **`src/consensus_v2.py`** — 权重敏感性 + 补偿集成 + 实验建议生成 + `--mode` 四种模式 + `--warnings`
5. **`config/pipeline.yaml`** — v2.1 新增配置段

**产出**: `src/filter_recessive.py`, `src/compensation.py`; 修改 `merge_evidence.py`, `consensus_v2.py`, `pipeline.yaml`

---

## 条目 #6 — 2026-09-07（DBTL Cycle 4 — Learn → Design）

### 质询回答 + DE 分析验证 + 管线 v2.1 优化

**背景**：
上午提出了八个质询问题（#0-#7），随后通过四个并行任务系统推进：
1. 重新审阅项目先前的"剂量补偿"结论——发现证据链薄弱（N=1, GTF2I Δattr≈0，DE≈0 是推断而非直接测量）
2. 在 GSE283473 脑类器官上直接跑 DE 分析——验证了 GTF2I mRNA ratio = 0.995（确实被补偿），并发现逐基因补偿状态可变
3. 文献调研确认了微缺失病中剂量补偿的存在性和翻译后缓冲的广泛性
4. 回答了全部八个质询，在此基础上提出了 v2.1 的六项优化

**关键发现**：

1. **GTF2I mRNA ratio WS/CTRL = 0.995**——直接测量确认了转录层面的完美补偿。但这个"补偿"之前只是基于 Δattr≈0 的推断（而非直接测量）
2. **补偿状态是逐基因可变的**：GTF2I 0.995、EIF4H 0.994、BAZ1B 0.991、LIMK1 0.947、STX1A 0.976——不是一个全或无的现象
3. **文献支持翻译后缓冲**：肿瘤蛋白质组学数据 (CPTAC) 显示 23-33% 的蛋白质通过降解来缓冲 CNV 效应；蛋白质复合物亚基尤为突出
4. **Down 综合征中几乎不存在转录补偿**：补偿不是微缺失病的自然后果——在某些场景下是真实的，在某些场景下是工具偏倚

**决策**：
- scRNA-seq 的角色从"发现引擎"明确降格为"辅助验证层"——提供 mRNA 补偿状态信息
- 六个管线优化：mRNA 补偿状态维度 + 隐性致病基因过滤器 + ClinGen 三值标注 + 权重敏感性分析 + 实验建议生成器 + Mode D 稀疏性警告
- DBTL Cycle 记录更新至 Cycle 4

**产出**：
- `管线架构预审_质询回答与管线优化_2026-09-07.md`（含全部 8 个质询的回答 + 6 项优化 + Cycle 记录）
- `scRNA-seq_drug_target_discovery_landscape.md`
- `wbs_interval_de_analysis.csv`（完整 DE 结果）

---

## 条目 #5 — 2026-09-07

### 从 WS 管线到通用管线：架构重新设计

**背景**：
用户提问"WHS 的 scRNA-seq 数据有哪些？"触发了一次系统调研。调研结果揭示：WHS 目前没有任何公开的 scRNA-seq 数据，且 WHS 的主效基因格局与 WS 截然不同——NSD2 已被确认为核心因果基因，不需要"多基因排序"。

**发现**：
1. WHS 无任何公开 scRNA-seq 数据集（仅有的公开数据是 Nsd2 KO 小鼠 bulk RNA-seq，GSE232564）
2. NSD2 单基因功能缺失即可产生整体 WHS 核心表型（Italian J Pediatrics, 2022——"shifting paradigm"）
3. WHS 在疾病模型构建阶段比 WS 晚了约 5 年
4. 当前管线（v1）的隐含假设——scRNA-seq 数据存在 + 多基因需要排序——在 WHS 上完全不成立

**决策**：重新设计管线架构为"通用模式"，根据输入数据丰富度自动选择运行模式：

| Mode | 场景 | 输入 | 输出 |
|---|---|---|---|
| A (验证) | 主效基因已确定 | 区间 + 已知基因 | 验证报告 |
| B (增强筛选) | 有争议候选 | 区间 + 正对照 | 排序+验证 |
| C (全栈筛选) | 多基因/多表型 | 区间 + scRNA-seq | 分层排序+表型分组 |
| D (探索) | 全新 CNV/未知 | 仅区间坐标 | 粗筛+低置信警告 |

**关键设计变更**：
1. 基因提取独立化：缺失区间坐标 + GTF → 基因列表（无 scRNA-seq 依赖）
2. scRNA-seq 从"前提条件"降格为"可选增强层"
3. 输出从"唯一排名"改为"按表型分组 + 证据分层"
4. HPA 从"惩罚层"改为双重角色（靶组织可行性 + 安全性警告）
5. 新增`phenotype_grouper.py`按 HPO/ClinGen 表型分组

**产出**：
- `架构设计_v2_通用微缺失主效基因筛选管线.md`
- `WHS_scRNA-seq_data_survey.md`

**依据**：
- WHS 文献调研：NSD2 单基因功能缺失→完整核心表型 (Italian J Pediatrics, 2022; CSH Mol Case Studies, 2019)
- Schmid et al. 2025 benchmark：所有 scRNA-seq CNV caller 对 <3Mb focal CNV 灵敏度极低
- WS 项目自身负结果：E8 mRNA 隐身、E6 TBX1 0.16% 表达、GEARS 覆盖盲区

---

## 条目 #4 — 2026-09-07

### scRNA-seq CNV 方法调研：确定"从 scRNA-seq 自动发现缺失区间"在当前不可行

**背景**：
用户问"除了 infercnvpy 还有没有其他从 scRNA-seq 提取缺失区间基因的方法？"

**方法**：
系统调研 3 篇主要 benchmark（Schmid et al. 2025 Nature Comms; Chen et al. 2025 Prec Clin Med; Hou et al. 2026 bioRxiv）+ 2 篇方法论文（Numbat Nature Biotech 2023; XClone Nature Comms 2024）

**发现**：
1. **所有方法对 <3Mb focal CNV 灵敏度极低**："all scRNA-seq callers are, in general, not suitable for identifying them"（Schmid et al.）
2. Allele-aware 方法（Numbat）总体最优但需要原始 BAM + 足够杂合 SNP 密度。10x 3' 端测序 SNP 覆盖不足
3. 没有任何工具是专门为胚系杂合微缺失设计的
4. 表达型方法之间的相关性有时超过它们各自与 DNA 金标准的相关性——存在系统性转录组偏差
5. 最终建议：**已知临床区间→基因提取（当前做法）是正确的策略**。scRNA-seq 的角色应是验证层而非发现层

**决策**：不在 CNV 工作流中增加额外的自动发现方法（ASE/Numbat/CopyKAT）。接受"已知区间坐标 + 基因型"作为基因来源的金标准。

**产出**：`benchmark_scrnaseq_cnv_callers_2025.md`

---

## 条目 #3 — 2026-09-06

### DeepLOF AI 层接入 + v2 consensus 排序修正

**背景**：
前天（09-05）的 WBS 35 基因全流程实验中，consensus_v2 的 rank 归一化在小样本下产生严重伪影（FZD9/FKBP6 被错误排到 #1），加性排序 vs Borda 排序 Spearman ρ = 0.23。

**修正**：
1. `normalize` 从 `rank` 改为 `raw` → Spearman ρ 从 0.23 跃升至 0.71
2. DeepLOF 正式接入（19,197 基因官方分数，CC BY 4.0），覆盖 28/35 WBS 基因（80%）
3. **发现 DeepLOF 官方数据盲区**：GTF2I 在 19,197 行评分中缺失——不是管线 bug，是 DeepLOF 训练时部分特征缺失被过滤

**结果**（raw 归一化 + DeepLOF）：
| # | 基因 | 剂量敏感性 | 说明 |
|---|---|---|---|
| 1 | BAZ1B | pLI=1.0, LOEUF=0.109 | 染色质重塑，WBS 颅面/神经候选 |
| 2 | CLIP2 | pLI=1.0, LOEUF=0.196 | 微管结合，神经发育 |
| 3 | STX1A | pLI=0.98, LOEUF=0.293 | 突触 SNARE 蛋白 |
| 4 | ELN | ClinGen HI=3 | WBS 心血管经典主效基因 |

**产出**：`AI辅助层接入_DeepLOF_结果报告_2026-09-06.md`

---

## 条目 #2 — 2026-09-05

### WBS 35 基因全流程端到端验证完成 + 管线现状总结

**背景**：
这是管线搭建完成后首次在真实数据上运行完整流程。选择 WBS (Williams 综合征 7q11.23 区间) 作为验证案例。

**流程**：
scRNA-seq (GSE283473) → CNV 工作流 → 35 基因 candidates.csv → L0 normalize → L1 merge_evidence → L3 consensus_v2 --tune

**核心产出**：
1. CNV 工作流 22/22 测试通过，GSE283473 端到端验证
2. L1 修复了 5 个真实数据格式问题（ClinGen 注释行/skiprows、列名 # 前缀、符号映射、重复列、30/40 分数→NaN）
3. 连接率诊断：ClinGen HI 14% (5/35)、gnomAD 77% (27/35)、HPA 97% (34/35)
4. WBS 区间内 ClinGen 覆盖极低——这是微缺失病的普遍问题
5. **共识排序有严重配置问题**：FZD9(pLI=0.002) 被 rank 归一化扭曲到 #1

**诚实结论**：
> 证据层（原始数据）比共识层（当前配置）更可信。90% 的有效信号来自"ClinGen ELN=3 + gnomAD 高 pLI/低 LOEUF 六个基因"这一小撮证据。

**六条升级建议**：
1. normalize 从 rank → raw（**次日实施**）
2. HPA 惩罚降权或高 pLI 基因豁免
3. LOO 调权在对照数<3 时直接报"无效"
4. 补 HPA 全组织版本（含脑表达）
5. AI 层试点（**次日实施**）
6. 补全 8 病区间表

**产出**：`管线现状与Williams主效基因筛选实验总结_2026-09-05.md`

---

## 条目 #1 — 2026-09-01（估计）

### 管线骨架搭建完成

**内容**：
1. 四层架构：normalize.py → merge_evidence.py → (AI 层可选) → consensus.py
2. CNV 工作流 (src/cnv/)：infercnv → segments → extract-genes，还未在真实数据上验证
3. 配置驱动：pipeline.yaml + sources.json
4. 测试体系：tests/（27+ 测试）

**产出**：`工程化指导书_微缺失主效基因筛选管线.md`

**踩坑记录**：
- ClinGen TSV 解析：5 行 # 注释、列名前缀 #、重复 PMID 列——这些是在 L1 真实数据接入时才暴露的（见条目 #2）
- `outputs/igem_gene_pipeline/` 曾丢失过一次，从存储内容重建（见 notebook:chatcmpl-tool-b7c0a6fa2a4b072c）

---

## 条目 #0 — 2026-09-01（估计）

### 项目初始化：从"找靶点"到"建管线"

**背景**：
本项目起源于 iGEM 团队之前 5 个月的干实验工作（2026-07 → 2026-08），核心产出是 VirtualCellTool 和 Williams 综合征的五步计算通路。关键发现（PROJECT_PROGRESS_REPORT.md）：

1. **SIGnature 归因 ≠ 因果预测**：归因分数与真实扰动效应 r=0.02 (p=0.83)
2. **GEARS 结构性不适用**：Perturb-seq 数据集是癌细胞系，41 个微缺失主效基因只有 4 个在训练图中
3. **E8: mRNA 隐身**：删失基因稳态 mRNA 不能被归因检测到（Δattr≈0）
4. **三个天花板**：翻译层盲区、单基因 vs 多基因错配、mRNA 隐身
5. **方向收敛**：从"AI 筛选靶点"转向"证据金字塔+正对照验证"

**本管线（v1）的设计逻辑**：
接管"候选基因排序"这一步骤，用 ClinGen/gnomAD/HPA 作为 L1 基线证据，AI 作为可选增强层。不再依赖归因或扰动模型来"发现"靶点。

---

## 快速索引

| 主题 | 条目 |
|---|---|
| VCT 定位 | #8 (L3 机制假设+演示层), #12 (工具组合推荐) |
| VCT 工程修复 | #14 (不可启动→可用；稀疏化/缓存/单例三类 bug) |
| VCT 可视化 | #14 (CIPHER 双子图、位移双视图、表达分布、归因图、质心图、GEARS 图) |
| VCT↔管线衔接 | #14 (WBS Top12 有 10 个可预测；GTF2I 排名分歧、ELN 组织特异性负结果) |
| 虚拟细胞调研 | #9 (文献综述+可行性判定) |
| WHS/NSD2 证据链 | #10 (叙事指南+引文修正) |
| WHS 实证运行 | #11 (NSD2 #1/19 + 符号别名缺口修复) |
| 架构设计 | #5 (v2 通用架构), #1 (v1 四层架构), #0 (起源) |
| scRNA-seq 方法 | #4 (CNV caller 调研结论) |
| 数据源覆盖 | #2 (ClinGen 14% 覆盖 WBS), #5 (WHS 无数据) |
| 排序算法问题 | #2 (rank 归一化伪影), #3 (raw 归一化修正), #14 (细胞类型响应无判别力→余弦对齐) |
| AI 层 | #3 (DeepLOF 接入 + GTF2I 盲区) |
| HPA 设计 | #5 (从惩罚到双重角色) |
| 表型分组 | #5 (HPO/ClinGen 表型映射) |
| WHS 疾病 | #5 (核心因果基因 NSD2), #10 (证据链) |
| WS 疾病 | #2, #3 (WBS 35 基因全流程) |
| 管线修复 | #11 (gnomAD 符号别名解析), #13 (HPA 惩罚移除 + raw 归一化落实) |
| 六 mode 实证 | #13 (WBS 正对照 6/6、WHS NSD2 全 mode #1；outputs/ 归档) |
| 解读陷阱 | #14 (IG 归因正负号只表方向不表重要性；ws/ms 的 cell_type 实为病健分组) |
| 负结果资产 | #0 (r=0.02 / GEARS 4/41), #9 (Nat Methods 2025 基准), #14 (ELN 脑内无效应) |
| 文档一致性 | #15 (12 处不一致审计：VCT 版本/端点/缓存大小；管线版本号与测试数更正) |
| 日志数值更正 | #15 (测试数 27+/22/22 → 21 用例；管线 v2.1 → v2.2) |
| 待决策项 | #15 (consensus_v2 回退默认 normalize="rank" vs config 的 raw) |
| iGEM wiki 大纲 | #16 (Model 页 10 节：原理+DBTL 七轮；Document 页 15 节：说明书+图表读法) |
| 管线架构文档 | #17 (v2.2 实施文档，替代 v2.0；9 项未实现清单 + auto/Mode C 行为澄清) |

---

*最后更新：2026-09-14*
