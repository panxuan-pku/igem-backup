# VirtualCellTool v3.3 架构文档

> 最后更新：2026-09-14
> 对应代码：`derived/tools/VirtualCellTool/`（app.py 853 行 · index.html 976 行 · 19 个端点）
> 版本锚点：`v1.0-scimilarity` · `v2.0-gears` · `v3.1-fixed` · `v3.2-zoom` · `v3.3-viz`

---

## 一、全景架构

```
                    ┌──────────────────────────────────────────┐
  浏览器              │         VirtualCellTool v3.3            │
  (Plotly)           │                                          │
    │                │  ┌──────────────────────────────────┐   │
    │  HTTP          │  │      web/app.py (FastAPI)          │   │
    ├───────────────►│  │                                    │   │
    │                │  │  数据集  /api/data  /api/search_genes │   │
    │  19 个端点      │  │         /api/gene_expr              │   │
    │                │  │  归因    /api/attribute             │   │
    │                │  │         /api/attribution_map  (图)  │   │
    │                │  │  反事实  /api/perturb(_multi)       │   │
    │                │  │  表达图  /api/gene_expr_map   (图)   │   │
    │                │  │  因果    /api/gene_coverage         │   │
    │                │  │         /api/perturb_causal  负对照  │   │
    │                │  │  线性响应 /api/perturb_summary (主力) │   │
    │                │  │         /api/celltype_response      │   │
    │                │  │  基线    /api/perturb_compare       │   │
    │                │  └──────────┬───────────────────────┘   │
    │                │             │                            │
    │                │    ┌────────┴────────────────────────┐  │
    │                │    │          5 个扰动引擎             │  │
    │                │    │                                  │  │
    │                │    │  perturb.py       v1 反事实      │  │
    │                │    │  attribute.py     v1 IG 归因     │  │
    │                │    │  gears_engine.py  v2 GEARS 负对照 │  │
    │                │    │  cipher_engine.py v3 CIPHER ★    │  │
    │                │    │  linear_baseline.py v3 基线 ★    │  │
    │                │    └──────────┬────────────────────┘   │
    │                │               │                          │
    │                │    ┌──────────┴────────────────────┐   │
    │                │    │  数据层（3 数据集懒加载缓存）     │   │
    │                │    │  {ds}_expr.npz (CSR 稀疏!) +    │   │
    │                │    │  {ds}_embeddings + {ds}_umap +  │   │
    │                │    │  {ds}_meta + cipher_{ds}.npz    │   │
    │                │    └───────────────────────────────┘   │
    └──────────────────────────────────────────────────────────┘
```

## 二、引擎矩阵

| # | 引擎 | 文件 | 原理 | 输入 | 输出 | 速度 | 基因覆盖 |
|---|---|---|---|---|---|---|---|
| 1 | Attribution | `src/attribute.py` | Integrated Gradients (Captum)，对 embedding 求和归因 | 细胞表达向量 x | Top K 基因归因分数 | ~0.1s | 28231 |
| 2 | Perturb (v1) | `src/perturb.py` | SCimilarity 编码器反事实 | x + 基因名 + 新值 | embedding 位移 | ~0.9s | 28231 |
| 3 | GEARS (v2) | `src/gears_engine.py` | GNN + GO 知识图谱 | 训练图内基因名 | 全转录组预测 | ~60s | 3127（仅 K562）**负对照** |
| 4 | **CIPHER (v3)** | `src/cipher_engine.py` | 线性响应 Δx=Σu | 对照细胞协方差 + 基因名 | 全转录组 Δx | ~0.1s | 5000 HVG |
| 5 | **线性基线 (v3)** | `src/linear_baseline.py` | control-mean / additive | 基因名 | 零效应 / 自身 LFC | <1ms | 28231 |

## 三、API 端点（19 个，含首页）

### 数据集与浏览
| 端点 | 参数 | 返回 |
|---|---|---|
| `GET /` | — | `index.html`（Cache-Control: no-store） |
| `GET /api/data` | ds | UMAP 坐标、分组标签、候选基因、`group_label` |
| `GET /api/search_genes` | q=`FOXP3` | 全基因空间（28231）匹配的基因列表 |
| `GET /api/gene_expr` | ds, gene | 该基因的 max / mean |

### 归因
| 端点 | 参数 | 返回 |
|---|---|---|
| `GET /api/attribute` | ds, cell, k | 归因排序基因列表 |
| `GET /api/attribution_map` | ds, cell, k | 归因分数 + 该细胞/全体表达对比（**v3.3 归因图**） |

### v1 反事实扰动
| 端点 | 参数 | 返回 |
|---|---|---|
| `GET /api/perturb` | ds, cell, gene, value | UMAP 新旧坐标、位移、`zoom` 视窗、`neighbors` 邻域 |
| `GET /api/perturb_multi` | ds, cell, genes, value | 同上 + 细胞类型重判 + 质心距离 |
| `GET /api/cell_gene_expr` | ds, cell, gene | 该细胞该基因的表达值 |

### v2 GEARS 因果（负对照）
| 端点 | 参数 | 返回 |
|---|---|---|
| `GET /api/gene_coverage` | gene | 是否在训练图内 |
| `GET /api/perturb_causal` | gene | GEARS 预测全转录组 |

### v3 CIPHER + 基线（可视化核心）
| 端点 | 参数 | 返回 |
|---|---|---|
| `GET /api/cipher_status` | ds | CIPHER 是否就绪 + HVG 数 |
| `GET /api/gene_in_cipher` | ds, gene | 该基因是否可预测 + 对照表达 |
| `GET /api/perturb_summary` | ds, gene, direction | **热图数据 + 分组响应（主力端点）** |
| `GET /api/perturb_compare` | ds, gene, direction | **CIPHER vs 基线对照数据** |
| `GET /api/celltype_response` | ds, gene, direction | 仅分组响应排序 |
| `GET /api/perturb_cipher` | ds, gene, direction | 轻量 Δx 摘要 |
| `GET /api/perturb_baseline` | ds, gene, method | 线性基线结果 |

### v3.3 表达分布
| 端点 | 参数 | 返回 |
|---|---|---|
| `GET /api/gene_expr_map` | ds, gene | 逐细胞表达值 + 分组统计（**表达分布图**） |

> ⚠️ `celltype_response` 与 `perturb_baseline` 当前**未被前端调用**（前端分别用 `perturb_summary` 与 `perturb_compare` 覆盖），保留供 CLI / 外部脚本使用。

## 四、前端渲染流程（标签页式工作区）

```
用户点击 UMAP 上的细胞
  → selectCell(i) → GET /api/attribute → 侧栏归因表
  → 点归因表里一个基因 → pickGene() → 查 CIPHER 覆盖性 + 滑杆同步

用户点 📉 CIPHER 敲低 / 📈 过表达
  → doCipher(dir) → GET /api/perturb_summary
  → openTab("cipher_{gene}_{dir}_{ds}") → renderPerturbFigure()
       左子图: Top30 |Δ| 基因（红=目标, 绿=上调, 蓝=下调）
       右子图: 分组响应（橙=最敏感）+ 驱动基因标注

用户点 📏 对比线性基线
  → doBaseline() → GET /api/perturb_compare → openTab("base_...") 叠加图

用户点 🎨 看表达分布（任意基因可用，不受 HVG 限制）
  → doExprMap() → GET /api/gene_expr_map → openTab("expr_...")
       左: UMAP 按表达量着色（带色阶条）  右: 各分组平均表达 + 表达%

用户点 📊 归因结果出图
  → doAttrFigure() → GET /api/attribution_map → openTab("attr_...")
       左: IG 强度（橙/紫=方向）  右: 该细胞 vs 全体均值

用户点 🚀 模拟单基因扰动 / TopN 联合扰动
  → doPerturb() / doMultiPerturb() → GET /api/perturb(_multi)
  → openTab("move") → showMove() 全景+放大双视图（kNN 插值坐标）
  → renderCentroidFigure() 质心距离图（联合扰动时）

用户点 🧪 因果预测
  → doCausal() → GET /api/perturb_causal → renderGearsFigure()（负对照标注）
```

**标签页系统**：`openTab(key,title,render)` / `activateTab` / `closeTab`，key 含 `ds` 与基因名，
多个结果并存可对比，切换时 `Plotly.Plots.resize()`。

## 五、CIPHER 引擎原理

```
拟合阶段（每数据集一次，缓存到磁盘）:
┌──────────────────────────────────────────────────┐
│  对照细胞 X[n_cells × n_genes]  ← CSR 稀疏，不稠密化 │
│      │                                              │
│      ▼ 稀疏逐列方差 → 选 Top 5000 HVG（方差最大）      │
│  X_hvg[n_cells × 5000]  （仅此处稠密化，~2GB 上限）    │
│      │                                              │
│      ▼ 算基因-基因协方差 + 岭正则化                    │
│  Σ = (Xcᵀ Xc)/(n-1) + λ·diag_mean·I                │
│      │                                              │
│      ▼ 存盘: cipher_{ds}.npz                         │
│        含 gene_list / ctrl_mean / Sigma /            │
│           hvg_idx / full_mean  ← 缺任一项会失效重算   │
└──────────────────────────────────────────────────┘

预测阶段（每次 0.02–0.1s）:
┌──────────────────────────────────────────────────┐
│  输入: gene=MS4A1, direction=ko                    │
│      │                                              │
│      ▼ 构建扰动向量 u                                │
│  u[MS4A1_idx] = 0 - ctrl_mean[MS4A1]  (敲低→0)     │
│      │                                              │
│      ▼ 线性响应                                     │
│  Δx = Σ @ u      (5000 维向量)                      │
│      │                                              │
│      ▼ 排序 |Δx| → Top 30 基因                       │
│      ▼ 分组响应 = 余弦对齐度（类型特异谱 vs |Δx|）      │
│      ▼ 输出                                         │
└──────────────────────────────────────────────────┘
```

**分组响应公式**（v3.1 方法学修复，判别力 2/12 → 10/12）：

```
w_ct[g] = max(0, expr_ct[g] − mean_over_celltypes[g])   # 类型特异富集量
response = Σ w_ct[g]·|Δ[g]| / (‖w_ct‖·‖|Δ|‖)            # 余弦对齐度
```

## 六、数据流

```
启动时（默认 pbmc，6.2s）:
  1. 加载 SCimilarity 模型（117MB）
  2. 加载数据集（CSR 稀疏 X + embeddings + meta）
  3. 加载缓存 UMAP（存在则直接用，不重算）
  4. 加载/拟合 CIPHER 协方差 → data/cipher_{ds}.npz
  5. 服务就绪（其余数据集懒加载，切换时才加载）

运行时:
  用户请求 → FastAPI 路由 → _require_cipher(ds)（必要时自动加载）→ engine.predict() → JSON → Plotly
```

**缓存文件与实测大小**：`cipher_pbmc.npz` 105M · `cipher_ms.npz` 104M · `cipher_ws.npz` 12M
（ws 稀疏度高，压缩后反而最小）

## 七、文件清单

```
VirtualCellTool/
├── web/
│   ├── app.py              # FastAPI 主服务（853 行，19 个端点）
│   ├── index.html          # 前端（976 行，标签页工作区 + 8 处 Plotly 图表）
│   └── plotly.min.js       # Plotly 库
├── src/
│   ├── paths.py            # 集中路径管理（禁止硬编码）
│   ├── prepare_*.py        # 各数据集预处理（pbmc/ms/ws）
│   ├── attribute.py        # IG 归因引擎
│   ├── perturb.py          # v1 反事实扰动引擎
│   ├── gears_engine.py     # v2 GEARS 因果引擎（负对照）
│   ├── cipher_engine.py    # v3 CIPHER 线性响应引擎 ★
│   ├── linear_baseline.py  # v3 线性基线引擎 ★
│   ├── viz_perturbation.py # CLI 出图脚本 ★
│   └── ... (其他已有脚本)
├── tests_e2e_playwright.py # 浏览器端到端回归（15 项断言）
├── data/                   # 中间数据 + UMAP 缓存 + CIPHER 缓存
├── docs/                   # 工程/设计/交接文档
├── gears_data/             # GEARS 训练数据
└── gears_ckpt/             # GEARS 模型权重
```

## 八、启动命令

```bash
# Web 交互（推荐：启动脚本，默认 pbmc）
cd derived/tools/VirtualCellTool
./启动VirtualCellTool.command
# → http://127.0.0.1:8377

# 或手动指定数据集
VCT_DATASET=pbmc ../SIGnature/.venv/bin/python web/app.py
# 数据集也可在网页顶部下拉切换（懒加载，无需重启）

# 端到端回归测试
~/ReactionSeek/.venv/bin/python tests_e2e_playwright.py

# CLI 出图（出版物用）
../SIGnature/.venv/bin/python src/viz_perturbation.py \
    --gene GTF2I --direction oe --dataset ws --output outputs/figures/
# → SVG 热图 + 分组响应 + 基线对照 + JSON 数据
```

## 九、关键约束（踩过的坑）

| 约束 | 原因 |
|---|---|
| **表达式矩阵必须保持 CSR 稀疏** | ws 稠密化 = 96969×28231 float64 ≈ 21.9GB，直接 OOM |
| **CIPHER 引擎按数据集独立实例** | 全局单例会在切数据集时互相覆盖协方差矩阵 |
| **缓存必须存 hvg_idx + full_mean** | 缺任一字段 → KeyError → 每次启动全量重算 |
| **UMAP 坐标用 kNN 插值，不用 k=1** | k=1 会把坐标吸附到已有细胞，任何位移都输出 Δ=0 |
| **分组响应用余弦，不用加权均值** | 否则最大细胞群/高表达类型在任何扰动下都排第一 |
| **不要用系统 Python / pip install / uv** | 解释器固定为 `../SIGnature/.venv/bin/python` |