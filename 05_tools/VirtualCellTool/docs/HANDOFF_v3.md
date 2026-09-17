# VirtualCellTool v3.3 — Agent 交接文档

> 版本锚点：`v1.0-scimilarity` · `v2.0-gears` · `v3.1-fixed` · `v3.2-zoom` · `v3.3-viz`
> 第 0 节记录 v3.1→v3.3 三轮修复；第 1–10 节为架构与操作说明。

> **给接手 Agent 的第一句话**：这是一个 iGEM 2026 项目的干实验工具。核心功能 = 在单细胞数据上预测基因扰动的转录组效应，并用交互式 Plotly 图表展示。代码在 `derived/tools/VirtualCellTool/`。先读这个文档，再读 `docs/ARCHITECTURE_v3.md`。

---

## 0. v3.1 修复记录（2026-09-13）

上一版交接时工具**无法启动**（默认加载 ws 数据集时进程无限卡死）。本次修复的问题：

### 致命 bug（工具完全不可用）

| # | 问题 | 根因 | 修复 |
|---|---|---|---|
| F1 | 启动无限卡死 | `_load_dataset` 用 `X.toarray()` 稠密化。ws = 96969×28231 float64 ≈ **21.9 GB**，直接打爆内存进 swap | 全程保持 CSR 稀疏（`float32`），新增 `_sparse_col_var()` / `_row()` 稀疏工具函数；只在 5000 HVG 子矩阵上稠密化（~2 GB） |
| F2 | CIPHER 缓存永远失效 | 缓存写盘时只存 `gene_list/ctrl_mean/Sigma`，读取时却访问 `c["hvg_idx"]` → KeyError → 每次启动全量重算 | 缓存补存 `hvg_idx` + `full_mean`；读到旧格式自动识别并重建 |
| F3 | 缓存加载后仍重算 | 缓存分支末尾**没有 `return`**，代码继续往下执行全量拟合 | 加载成功立即 `return` |
| F4 | 多数据集结果互相污染 | `cipher_eng` / `baseline_eng` 是模块级**全局单例**，切数据集时后加载的覆盖先加载的协方差矩阵 | 改为 `_CIPHER_ENGINES[ds]` / `_BASELINE_ENGINES[ds]` 按数据集独立实例 |

### 前端 bug（"效果不好"的直接原因）

| # | 问题 | 修复 |
|---|---|---|
| F5 | 所有 `fetch` 都不带 `ds` 参数 | 统一封装 `api(path, params)`，自动注入当前 `DS` |
| F6 | 切数据集靠 `location.href` 整页跳转，状态全丢 | 改为原地 `loadDataset(ds)` + `history.replaceState` |
| F7 | 图表容器运行时 `createElement` 塞进 340px 侧边栏，图挤成一条 | 重构为「左控制栏 + 右工作区」，图表在右侧大区域渲染 |
| F8 | 每点一次新基因，旧图表被 `Plotly.newPlot` 覆盖 | 标签页系统（`openTab/activateTab/closeTab`），多个结果并存可对比 |
| F9 | 基因不在 HVG 集时只回一句干巴巴的 400 | 后端返回 `reason` + `suggestions`（相近基因），前端展示可操作提示 |
| F10 | CIPHER 必须先手动访问 `/api/data` 才能用，否则 503 | `_require_cipher(ds)` 在数据集未加载时自动触发加载 |

### 方法学修复（图表有判别力）

**问题**：细胞类型响应排序几乎没有区分度——MS4A1（B 细胞标志物）敲低时 B 细胞只排第 3，与第 1 名差距 <5%。

**根因**：旧公式 = 「该类型 Top500 高表达基因上的 |Δ| 均值」。但各细胞类型的最高表达基因几乎都是核糖体/管家基因、彼此高度重叠，所以所有类型得分几乎相同。

**修复**：改为**类型特异谱 vs 扰动效应谱的余弦相似度**

```
w_ct[g] = max(0, expr_ct[g] - mean_over_celltypes[g])     # 该类型特异富集量
response = Σ w_ct[g]·|Δ[g]| / (‖w_ct‖·‖|Δ|‖)              # 余弦对齐度
```

两个关键细节：
- 基准用**各类型均值的均值**，不是全体细胞均值——否则最大的细胞群（PBMC 里 T 细胞占 45%）会把基准拉向自己，导致它在任何扰动下都排不上去。
- 用**余弦**而非加权均值——消除两侧幅度影响，否则本身高表达的类型（单核细胞 LYZ/S100A9）在任何扰动下都拿最高分。

**实测效果**（PBMC，12 个标志物基因敲低，看最敏感类型是否命中该基因的已知归属类型）：

| 方案 | Top1 命中 | 平均排名 |
|---|---|---|
| 旧（Top500 均值） | ~2/12 | ~3.0/5 |
| 新（余弦对齐） | **10/12** | **1.33/5** |

命中：MS4A1/CD79A/CD79B→B cell、IL7R→T cell、LYZ/CD14/S100A9→Monocyte、GNLY/NKG7→NK cell、FCER1A→Dendritic
未命中：CD3D、CD3E（→Dendritic）。这是 **CIPHER 线性响应的固有局限**，不是代码 bug：这两个基因在 PBMC 中表达稀疏、协方差信号弱。汇报时应如实标注。

### 数据语义修正

ws / ms 数据集的 `meta.cell_type` 列装的其实是**病健分组**（WS vs CTRL / MS vs normal），不是细胞类型。
`DATASETS[ds]["group_label"]` 现在显式声明这一点，前端图表标题、按钮文案自动跟随，避免把「病健分组响应」误标成「细胞类型响应」。

### 性能对比

| 场景 | 修复前 | 修复后 |
|---|---|---|
| 冷启动（默认数据集） | 无限卡死（ws 稠密化 OOM） | **6.2 s**（默认改 pbmc） |
| 加载 Williams 96,969 细胞 | 卡死 / swap | **5 s** |
| CIPHER 预测 | — | 0.02–0.1 s |
| 二次启动 | 每次全量重算协方差 | 秒级（缓存真正生效） |

### 验证方式

Playwright 真实浏览器端到端测试（15 项断言全绿，零控制台错误）：选细胞→归因→选基因→CIPHER 敲低/过表达→线性基线→反事实位移→切数据集。
脚本见 `/tmp/vct_e2e.py`（可复制进项目长期保留）。

### 默认数据集变更

`VCT_DATASET` 默认值从 `ws` 改为 **`pbmc`**（2700 细胞秒开）。ws / ms 懒加载，在网页下拉切换时才加载。

---

## 0.2 v3.2 / v3.3 记录（2026-09-13/14）

### v3.2 — 反事实位移可视化：修掉「坐标吸附」bug

**表面问题**：用户反馈「反事实扰动的前后对比不够明显」。
**真实根因**（计算层，不是视觉问题）：`_FakeReducer` 用 **k=1 最近邻**反查 UMAP 坐标，
坐标被「吸附」到某个已有细胞上——只要扰动后嵌入的最近邻没换人，输出坐标与扰动前**完全相同**。
对照实验（人为施加不同量级位移）证实：

| 施加位移 | k=1 最近邻（旧） | kNN 插值（新） |
|---|---|---|
| 0.01 | Δ=0.00000 | 0.01057 |
| 0.1 | Δ=0.00000 | 0.18683 |
| 0.3 | **Δ=0.00000** | 0.24272 |

**修复**：改为 **k=15 反距离加权插值**，坐标连续可微。实测 UMAP 位移：
MS4A1 敲低 0 → **0.0451**；Top5 联合 → **0.1093**；GTF2I(ws) 过表达 → **0.2983**。

> 自我更正：v3.1 阶段加过的「扰动幅度不足以在 UMAP 上移动」提示，是在为 bug 辩解而非物理限制。

**新增**：`_zoom_window()`（按位移自适应的局部视窗）+ `_local_neighbors()`（邻域背景细胞作参照），
前端 `showMove` 重写为**全景 + 放大镜双视图**（左定位+取景框，右放大前后对比+箭头）。

### v3.3 — 把剩余文字结果全部可视化

新增 2 个端点 + 4 类图表：

| 可视化 | 端点 | 说明 |
|---|---|---|
|  表达分布 | `/api/gene_expr_map` | 左=UMAP 按表达量着色，右=分组表达水平；**全 28231 基因可用** |
| 📊 归因图 | `/api/attribution_map` | 左=IG 强度，右=该细胞 vs 全体均值 |
| 🎯 质心距离图 | 复用 `/api/perturb_multi` | 联合扰动的身份归属，扰动前/后对比 |
| 🧪 GEARS 图 | 复用 `/api/perturb_causal` | 上下调条形 + 负对照定位标注 |

**解读陷阱修正（重要）**：归因图中 MS4A1 等标志基因显示为**负值**，旧标注写「定义了该细胞的基因」+ 红色表负值，
极易被误读为「负面因素」。查证 `src/attribute.py`：IG 目标是 `embedding.sum()`，
**正负号只表示把嵌入分量推高/推低，与是否标志基因无关**，排序用 `|IG|`。
已改橙/紫配色 + 标注「长度=重要性，颜色仅表方向」+ 状态栏说明。

---

## 1. 一句话概述

VirtualCellTool 是一个 **Web 交互工具**（FastAPI + Plotly），允许用户在 UMAP 上点选细胞 → 计算基因归因 → 选择基因 → 预测敲低/过表达后的全转录组变化 → 实时展示热图和细胞类型响应。

---

## 2. 目录结构（只列关键文件）

```
derived/tools/VirtualCellTool/
├── web/
│   ├── app.py              ← ★ FastAPI 主服务（23KB，所有端点+引擎初始化+数据加载）
│   ├── index.html          ← ★ 前端页面（Plotly UMAP + 按钮 + 图表渲染 JS）
│   └── plotly.min.js       ← Plotly 库（3.6MB）
├── src/
│   ├── paths.py            ← ★ 集中路径管理（所有路径从这里解析，不再硬编码）
│   ├── cipher_engine.py    ← ★ v3 CIPHER 线性响应引擎（核心新模块）
│   ├── linear_baseline.py  ← ★ v3 线性基线引擎（Nature Methods 2025 强制对照）
│   ├── perturb.py          ← v1 SCsimilarity 反事实扰动
│   ├── attribute.py        ← v1 IG 归因
│   ├── gears_engine.py     ← v2 GEARS 因果扰动（惰性加载）
│   ├── prepare_data.py     ← 数据管线（PBMC3k → SCsimilarity → UMAP）
│   ├── viz_perturbation.py ← CLI 出图脚本（出版物级 SVG/PNG）
│   └── validate.py         ← AC1/AC2 验证
├── data/
│   ├── embeddings.npy      ← PBMC 3k 的 128 维嵌入（1.3MB）
│   ├── expr_aligned.npz    ← PBMC 表达矩阵 2700×28231（4.7MB）
│   ├── meta.csv            ← 细胞元数据
│   ├── umap.npy            ← 预计算的 UMAP 坐标（缓存）
│   ├── cipher_pbmc.npz     ← CIPHER 协方差缓存（138MB，首次启动后生成）
│   ├── gene_order.txt      ← 28231 基因名列表
│   ├── ws_*                ← Williams 脑类器官数据（47MB embeddings + 27MB expr）
│   └── ms_*                ← MS 少突胶质细胞数据
├── docs/
│   ├── ARCHITECTURE_v3.md  ← ★ 架构文档（API 表、数据流、原理图）
│   ├── ENGINEERING.md      ← DBTL 循环记录
│   └── IGEM_ARCHITECTURE.md ← iGEM 架构规划
├── gears_data/             ← GEARS 训练数据（Norman Perturb-seq）
├── gears_ckpt/             ← GEARS 模型权重
└── ../SIGnature/           ← SIGnature 框架（.venv + SCimilarity 模型）
    ├── .venv/              ← Python 3.11 venv（所有依赖已装）
    └── model_files/model_files/scimilarity/  ← SCsimilarity 模型权重（117MB）
```

---

## 3. 如何启动

```bash
# 0. 杀旧进程
pkill -f "web/app.py"

# 1. 进入目录
cd derived/tools/VirtualCellTool

# 2. 启动（默认 PBMC 数据集）
PYTHON="../SIGnature/.venv/bin/python"
VCT_DATASET=pbmc "$PYTHON" web/app.py

# 3. 浏览器打开
# http://127.0.0.1:8377

# 其他数据集
VCT_DATASET=ws "$PYTHON" web/app.py     # Williams 脑类器官
VCT_DATASET=ms "$PYTHON" web/app.py     # MS 少突胶质细胞
```

**首次启动**：需要 ~20 秒（加载模型 + 首次计算 CIPHER 协方差缓存 + 首次 UMAP 缓存）。
**后续启动**：~5 秒（UMAP 和 CIPHER 都从磁盘缓存读取）。

---

## 4. 架构原理

### 4.1 服务启动流程

```
app.py 启动
  │
  ├─ 1. 导入引擎单例（PerturbEngine, AttributionEngine, CipherEngine, LinearBaseline）
  │      └─ PerturbEngine.__init__() 加载 SCsimilarity 模型（117MB）
  │
  ├─ 2. 加载默认数据集 _load_dataset(key)
  │      ├─ 读 embeddings.npy + expr_aligned.npz + meta.csv
  │      ├─ 读 umap.npy（缓存）或重算 UMAP（首次 + 缓存落盘）
  │      ├─ 算质心、候选基因列表
  │      └─ _fit_cipher_cached()  # 拟合 CIPHER 协方差
  │            ├─ 读 cipher_{ds}.npz（缓存）→ 恢复引擎状态
  │            └─ 或：选 Top5000 HVG → fit() → 存盘（首次 ~0.3s）
  │
  └─ 3. uvicorn.run() → http://127.0.0.1:8377
```

### 4.2 五个引擎

| 引擎 | 类 | 原理 | 速度 | 基因覆盖 | 定位 |
|---|---|---|---|---|---|
| IG 归因 | `AttributionEngine` | SCsimilarity + Captum IG | 0.1s | 28231 | 候选排序 |
| v1 反事实 | `PerturbEngine` | 编码器反事实外推 | 0.9s | 28231 | 交互 demo |
| v2 GEARS | `GearsEngine` | GNN + GO 图谱 + Perturb-seq | 60s | 3127 | **负对照** |
| v3 CIPHER | `CipherEngine` | Δx = Σu（协方差线性响应） | 0.1s | 5000 HVG | **假设生成** |
| v3 基线 | `LinearBaseline` | control-mean / additive | <1ms | 28231 | **强制对照** |

### 4.3 CIPHER 原理（核心新模块）

```
拟合：
  对照细胞 X[n×28231] → 选 Top5000 HVG → 算协方差 Σ[5000×5000]
  → 岭正则化 Σ += λ·diag_mean·I → 存盘 cipher_{ds}.npz

预测 (0.1s)：
  输入: gene, direction (ko=敲低→0, oe=过表达→2×ctrl)
  构建: u[gene_idx] = target - ctrl_mean
  计算: Δx = Σ @ u    （5000 维）
  排序: Top30 |Δx| → 分上调/下调
```

### 4.4 API 端点（19 个，含首页；完整表见 `docs/ARCHITECTURE_v3.md` 第三节）

| 端点 | 用途 |
|---|---|
| `GET /api/data?ds=pbmc` | UMAP 坐标 + 基因列表 + 分组标签（`group_label`） |
| `GET /api/search_genes?q=` | 全 28231 基因空间搜索 |
| `GET /api/gene_expr?gene=X` | 该基因 max/mean |
| `GET /api/attribute?cell=N&k=10` | IG 归因 Top K 基因 |
| `GET /api/attribution_map?cell=N&k=12` | **归因图数据**（归因分数 + 该细胞/全体表达对比） |
| `GET /api/perturb?cell=N&gene=X&value=V` | v1 反事实扰动（含 `zoom` 视窗 + `neighbors` 邻域） |
| `GET /api/perturb_multi?cell=N&genes=X,Y&value=V` | 多基因联合扰动 + 类型重判 |
| `GET /api/cell_gene_expr?cell=N&gene=X` | 该细胞该基因表达值 |
| `GET /api/gene_coverage?gene=X` | GEARS 覆盖查询（负对照） |
| `GET /api/perturb_causal?gene=X` | GEARS 因果预测（负对照） |
| `GET /api/cipher_status?ds=` | CIPHER 是否就绪 + HVG 数 |
| `GET /api/gene_in_cipher?ds=&gene=X` | 该基因是否在 CIPHER 覆盖内 |
| `GET /api/perturb_summary?gene=X&direction=ko\|oe` | **CIPHER 热图+分组响应**（主力端点） |
| `GET /api/perturb_compare?gene=X&direction=ko` | **CIPHER vs 基线** |
| `GET /api/celltype_response?gene=X&direction=ko` | 仅分组响应排序（前端未调用，供 CLI） |
| `GET /api/perturb_cipher?gene=X&direction=ko` | 轻量 Δx 摘要 |
| `GET /api/perturb_baseline?gene=X&method=both` | 线性基线结果（前端未调用，供 CLI） |
| `GET /api/gene_expr_map?ds=&gene=X` | **表达分布图数据**（逐细胞表达 + 分组统计） |

### 4.5 前端交互流程（v3.3 标签页式工作区）

```
用户点击 UMAP 上的细胞
  → selectCell(i) → fetch /api/attribute → 渲染侧栏归因表
  → 点击表里一个基因 → pickGene() → 查 CIPHER 覆盖性 + 滑杆同步该细胞表达值

用户点 📉 CIPHER 敲低 / 📈 过表达
  → doCipher(dir) → fetch /api/perturb_summary
  → openTab("cipher_{gene}_{dir}_{ds}") → renderPerturbFigure()
      左: Top30 |Δ| 基因（红=目标, 绿=上调, 蓝=下调）
      右: 分组响应（橙=最敏感）+ 驱动基因文字标注

用户点 📏 对比线性基线
  → doBaseline() → fetch /api/perturb_compare → openTab() 叠加图（灰竖线=control-mean）

用户点 🎨 看表达分布（任意基因可用，不受 HVG 限制）
  → doExprMap() → fetch /api/gene_expr_map → openTab("expr_...")
      左: UMAP 按表达量热力着色（带色阶条）  右: 各分组平均表达 + 表达%

用户点 📊 归因结果出图
  → doAttrFigure() → fetch /api/attribution_map → openTab("attr_...")
      左: IG 强度（橙=推高/紫=推低，长度=重要性）  右: 该细胞 vs 全体均值

用户点 🚀 模拟单基因扰动 / TopN 联合扰动
  → doPerturb() / doMultiPerturb() → fetch /api/perturb(_multi)
  → openTab("move") → showMove() 全景+放大双视图（kNN 插值坐标 + 箭头）
  → 联合扰动额外 renderCentroidFigure() 质心距离图

用户点 🧪 因果预测
  → doCausal() → fetch /api/perturb_causal → renderGearsFigure()（负对照标注）

标签页系统：openTab(key,title,render) / activateTab(key) / closeTab(key)
  key 含 ds 与基因名；多结果并存可对比；UMAP 主图不可关闭。
```

> ⚠️ 旧版文档提到的 `renderHeatmap()` / `renderCellTypes()` / `renderSummary()` 三个函数
> **已在 v3.1 前端重写时移除**，合并进 `renderPerturbFigure()`。若按旧文档找函数会找不到。

---

## 5. 路径管理规则（重要！）

**永远不要硬编码路径。** 所有路径通过 `src/paths.py` 解析：

```python
from paths import VCT_ROOT, DATA_DIR, SIG_DIR, MODEL_DIR, GEARS_DATA_DIR, GEARS_CKPT_DIR
```

- `VCT_ROOT` = VirtualCellTool 根目录（通过 `__file__` 自动检测）
- `SIG_DIR` = 同级 SIGnature 目录
- `MODEL_DIR` = SCimilarity 模型权重路径

导入模块时注意：
```python
# 在 src/ 下的文件
sys.path.insert(0, os.path.join(SIG_DIR, "src"))   # 导入 SIGnature
from paths import ...                                 # 导入路径常量

# 在 web/ 下的文件
sys.path.insert(0, os.path.join(ROOT, "src"))       # 导入 src 模块
```

---

## 6. 关键技术细节

### 6.1 Python 环境
- **解释器**：`derived/tools/SIGnature/.venv/bin/python` (Python 3.11)
- **关键依赖**：torch, captum, scanpy, anndata, scipy, numpy, fastapi, uvicorn, umap-learn, plotly
- **注意**：系统 Python 不可用；不要用 uv；不要 pip install

### 6.2 CIPHER 缓存
- 缓存文件：`data/cipher_{ds}.npz`（如 `cipher_pbmc.npz`）
- 内容：gene_list（5000 个 HVG 名）、ctrl_mean、Sigma（5000×5000 协方差）、**hvg_idx**、**full_mean**
- 实测大小：`cipher_pbmc.npz` **105M** · `cipher_ms.npz` **104M** · `cipher_ws.npz` **12M**
  （ws 稀疏度高，压缩后反而最小；旧文档写的 "~138MB" 与实际不符）
- 若删除缓存，下次启动自动重建（以 ws 为例：全量拟合约数秒～数十秒，视机器而定）
- ⚠️ **缓存的 5 个字段缺任何一个都会触发「加载失败 → 全量重算」**，写缓存时务必完整
- **CIPHER 只覆盖 5000 个 HVG**，不在 HVG 集中的基因返回 400 + `reason` + `suggestions`

### 6.3 UMAP 缓存
- 缓存文件：`data/umap.npy`、`data/ws_umap.npy`、`data/ms_umap.npy`
- 已存在（从 prepare_data.py 生成），不要删除
- 若缺失则自动重算并缓存

### 6.4 GEARS 惰性加载
- 首次调用 `/api/perturb_causal` 才加载模型（~30s）
- 如有缓存 `data/gears_pert_list.pkl`，秒级
- 微缺失病的 41 个基因中 0 个在训练图内

### 6.5 推理锁
- `web/app.py` 中有一个 `_inference_lock = threading.Lock()`
- 包围所有 PyTorch 推理调用（`attr_eng.top_genes()`, `perturb_eng.perturb()` 等）
- 防止并发请求导致线程爆炸

---

## 7. 当前状态：已完成 vs 待完成

### ✅ 已完成
- 5 个引擎全部可用（归因/反事实/GEARS/CIPHER/基线）
- Web 前端 v3.3：UMAP 主图 + 归因表 + 6 个按钮组 + **8 处 Plotly 图表**（标签页式工作区）
- **反事实位移可视化**：kNN 插值坐标 + 全景/放大双视图（v3.2）
- **全结果可视化**：表达分布图、归因图、质心距离图、GEARS 图（v3.3）
- **GEARS 前端标注"负对照"**（v3.1 完成，按钮与提示文案已改）
- **Williams 真实数据实测**（v3.1 完成：GTF2I |Δ|max=10.08、ELN 仅 0.006、分组响应 CTRL 0.45 vs WS 0.27）
- **前端图表持久化**（v3.1 完成：标签页系统，多结果并存可对比）
- CLI 出图：`src/viz_perturbation.py` 生成 SVG 出版物图
- 路径修复：全部移除硬编码路径
- CIPHER HVG + 磁盘缓存：三数据集缓存齐全，冷启动 6.2s
- UMAP 缓存：启动不再阻塞
- 3 个数据集：PBMC 2700 / MS 少突胶质 / Williams 脑类器官
- 端到端回归测试：`tests_e2e_playwright.py`（15 项断言全绿）

### ⬜ 待完成（来自 `outputs/reports/虚拟细胞/虚拟细胞工具组合推荐_igem决策_2026-09-12.md`）

| 项 | 说明 |
|---|---|
| CellOracle Web 集成 | 现有代码在 `02_disease-williams/` 的 CLI 脚本中，不在 VCT Web 里 |
| pertpy 全套可视化 | Mixscape 质控、扰动空间热图未接入 |
| decoupler 通路富集 | PROGENy/CollecTRI 通路活性变化未接入 |
| CIPHER 稀疏表达基因的局限 | CD3D/CD3E 等表达稀疏基因预测不敏感，需在汇报中如实标注 |
| 组织选择维度 | ELN 在脑类器官无效应，提示需心血管/成纤维细胞数据集（未接入） |

---

## 8. 常见问题排查

| 问题 | 原因 | 解决 |
|---|---|---|
| 页面白屏 | 服务器未就绪（UMAP/CIPHER 首次计算中） | 等 30s，观察终端输出 |
| `/api/data` 返回空 | UMAP 仍在计算 | 等终端打印 `[dataset] xxx 就绪` |
| CIPHER 返回 "未拟合" | 数据集未加载 | 先访问 `/api/data?ds=pbmc` 触发加载 |
| CIPHER 返回 "基因不在 HVG 集" | 该基因不属于 Top5000 高变基因 | 选其他基因（attribution Top 列表里的基因都在 HVG 内） |
| 端口 8377 被占用 | 旧进程未杀 | `pkill -f "web/app.py"` |
| Python 报 ModuleNotFound | 用了系统 Python | 必须用 `../SIGnature/.venv/bin/python` |

---

## 9. 测试命令

```bash
# 快速自测（不启动服务器）
cd derived/tools/VirtualCellTool
../SIGnature/.venv/bin/python -c "
import sys; sys.path.insert(0, 'src')
from cipher_engine import CipherEngine
from linear_baseline import LinearBaseline
from paths import DATA_DIR
import numpy as np, scipy.sparse as sp

# 加载 PBMC
X = sp.load_npz(DATA_DIR + '/expr_aligned.npz').toarray()
with open(DATA_DIR + '/gene_order.txt') as f:
    genes = f.read().strip().split('\n')
gvar = X.var(axis=0)
hvg = np.argsort(-gvar)[:5000]
Xh, gh = X[:, hvg], [genes[i] for i in hvg]

# CIPHER
ce = CipherEngine(0.1); ce.fit(Xh, gh)
r = ce.predict({'MS4A1': 0.0})
assert 'MS4A1' in ce._gene_idx
assert abs(r['delta'][gh.index('MS4A1')]) > 0.1
print('CIPHER: OK')

# Baseline
bl = LinearBaseline(); bl.fit(X, genes)
r = bl.predict_ctrl_mean()
assert r['method'] == 'control-mean'
print('Baseline: OK')
print('ALL TESTS PASSED')
"

# CLI 出图测试
../SIGnature/.venv/bin/python src/viz_perturbation.py \
    --gene MS4A1 --direction ko --dataset pbmc --output outputs/figures/
ls outputs/figures/MS4A1_ko_*.svg  # 应有 3 个 SVG
```

---

## 10. 一句话给下一位 Agent

> 这个工具的核心是 **CIPHER 线性响应引擎**（`src/cipher_engine.py`）——用未扰动对照细胞的基因-基因协方差矩阵预测任意基因敲低/过表达后的全转录组响应。它不需要任何扰动训练数据，天然支持激活方向（匹配 SINEUP）。Web 前端是 FastAPI + Plotly，所有路径通过 `src/paths.py` 集中管理，Python 环境在 `../SIGnature/.venv/bin/python`。先读 `docs/ARCHITECTURE_v3.md`，再看交接报告 `outputs/reports/虚拟细胞/虚拟细胞工具组合推荐_igem决策_2026-09-12.md` 了解设计决策背景。