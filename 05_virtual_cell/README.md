# VirtualCellTool

单细胞虚拟扰动演示工具，包含 PBMC、MS 和 Williams 三个数据集。CIPHER 是未扰动对照细胞的线性响应近似；反事实嵌入保留为实验性的编码器敏感性探索，GEARS 为有限覆盖的对照，均不能视作临床或治疗效果预测。

## 从克隆目录启动

先按[数据和第三方接入指南](../00_docs/01_guides/VCT_SETUP.html)准备 SIGnature、模型、配套矩阵与注释；所有数据都不随 Git 交付。在仓库根目录执行 `conda env create --file environment-vct.yml` 创建独立环境，再执行 `conda activate virtual-cell`（Windows / macOS / Linux 相同，无需单独安装 Python；完整步骤见根目录 README）。之后每次使用只需激活该环境；本页所有 `python` 命令均在 `virtual-cell` 环境中执行。源码检查使用 `python scripts/check_release.py`。数据就绪后：

```bash
cd 05_virtual_cell
python web/app.py
```

打开 `http://127.0.0.1:8377/`；数据集在页面顶部切换，不需要多个服务实例。macOS 也可双击 `启动VirtualCellTool.command`，该启动器使用同一个仓库根目录环境。通过终端启动时按 Ctrl-C 停止，不要用宽泛的 `pkill` 命令。不要沿用 `SIGnature/.venv`：旧环境含绝对路径，不可搬迁。

启动器通过 `/api/health` 核对成功响应、VirtualCellTool 标识、当前工作目录和 PID；启动子进程还必须与响应 PID 相同，才报告就绪。端口被其他服务/工作树或无健康接口的旧版本占用时明确报错，不自动杀进程。自己的启动进程失败或超时会被清理；后台日志追加到 `vct_server.log`，成功启动记录在 `test_artifacts/server-<端口>.json`，不入库。PID 记录只是诊断记录，可能过期，不能据此直接停止进程。

后台服务需要停止时，先访问 `http://127.0.0.1:8377/api/health` 核对项目路径和 PID，再用 `lsof -nP -iTCP:8377 -sTCP:LISTEN`、`ps -p <PID> -o command=` 核对监听进程确为本项目，最后执行 `kill -TERM <PID>`；旧服务没有健康接口时仍须用进程命令和工作目录确认，不能按模糊名称批量停止。服务不会热重载 Python 后端；更新后端后需重启，刷新网页只能重新读取前端。

服务运行期间，另开终端运行 `python tests_api.py --skip-gears`，验收健康接口、三个数据集及不需要 Norman 数据的 17/19 项 API；按仓库根目录 README 下载并解压 Norman 数据后，去掉 `--skip-gears` 验收全部 19 项。测试包含 4xx 错误状态、坐标/标签/表达数量与有限值、数据来源、表达汇总/单细胞值的一致性，以及加载 MS/WS 前后的 PBMC 结果一致性；仍不是科学有效性验收。细胞数是当前交付数据的回归基准，主动更换数据时需同步核对测试预期，不能忽略失败。

启动器、API 测试和浏览器测试均读取 `VCT_PORT`（默认 8377）。使用非默认端口时，在服务与测试命令前均加上同一 `VCT_PORT=8399`，避免连到另一服务。

## 数据与测试

### SIGnature / SCimilarity 输入与输出约定

这套模型用于细胞编码、基因归因和实验性编码器敏感性探索，不是 `03_pipeline` 每次筛选疾病时自动运行的步骤，也不是 CIPHER / GEARS 的共同扰动引擎。表达来自输入单细胞数据；embedding 和归因才是模型计算结果。

| 本项目 Python 入口 | 输入结构 | 输出结构 |
|---|---|---|
| `PerturbEngine.embed(X)` | 稠密 NumPy 数组 `(n, G)`，`n >= 1` | 当前模型为 `(n, 128)` embedding |
| `perturb(x, gene, new_value)` / `perturb_multi(x, gene_values)` | 单细胞数组 `(G,)`；基因名及新表达值，多基因时为字典 | 修改前后 embedding、差值及位移 |
| `batch_perturb(X, gene, new_value)` | 数组 `(n, G)`，同一基因/数值作用于整批 | 修改后的 `(n, 128)` embedding |
| `AttributionEngine.attribute(x)` / `top_genes(x)` | 单细胞数组 `(G,)` | `(G,)` IG 归因 / 排序后的基因、归因与表达值 |

- **基因列**：`G` 以实际加载的 `wrapper.gene_order` 为准，当前为 **28,231**；每列必须严格按该顺序对应基因，不能按字母重排或直接传 HVG 子集。`data/gene_order.txt` 应与模型顺序一致。归因矩阵列顺序也按此定义，排序后的差异表不能代替它。
- **表达尺度**：传入已经按模型基因空间对齐、经 `lognorm_counts` 处理的表达，不是原始 counts、差异表达、归因分数或 embedding。基因标识转换、对齐和归一化由数据准备步骤负责，推理入口不自动猜测、补列、转置或归一化。
- **基本校验**：拒绝错误维度/宽度、空批次、列表和稀疏矩阵，以及字符串、object、布尔、复数、NaN/Inf 和超出 float32 范围的值；在调用上游模型前抛出 `ValueError`。实数数组按模型原有 float32 精度计算，不修改调用者数组；整数数组也会转换，避免小数扰动值被截断。类型可接受不代表原始计数可以直接推理。
- **扰动参数**：基因必须在模型基因表中，三个扰动入口统一明确报错；替换值必须是有限且在 float32 范围内的实数标量，尺度与输入一致，不接受字符串或单元素列表。
- **校验边界**：只凭无标签数组无法检查基因顺序是否真实正确、样本身份或归一化是否合理；这些仍由准备步骤和使用者核对。本项不是科学有效性检查，也没有新增整机内存预算或自动稠密化。

网页使用的文件均位于 `data/`；表达矩阵在磁盘上为 CSR `.npz`，网页取出单个细胞后才作为稠密向量调用上述模型入口。元数据、embedding 和 UMAP 必须与表达矩阵逐行对应，不能只因为行数相同就混用不同批次。

| 网页数据集 | 表达矩阵 | 已计算 embedding | 元数据 / UMAP |
|---|---|---|---|
| PBMC：2,700 细胞，早期工具可行性测试 | `expr_aligned.npz` | `embeddings.npy` | `meta.csv` / `umap.npy` |
| MS：17,799 个少突胶质细胞，MS/normal | `ms_expr.npz` | `ms_embeddings.npy` | `ms_web_meta.csv` / `ms_umap.npy` |
| WS：96,969 个 Williams 脑类器官细胞，WS/CTRL；不是 WHS | `ws_expr.npz` | `ws_embeddings.npy` | `ws_web_meta.csv` / `ws_umap.npy` |

以上为 2026-09-24 交付快照，表达宽度均为 28,231、embedding 宽度为 128，UMAP 为二维；元数据 `cell_type` 在 PBMC 表示细胞类型，在 MS/WS 表示病健分组。现有行序对应仍需要来源记录支持，维度核对不能倒推出完整历史谱系。网页归因和反事实结果现场计算返回，不自动保存成实验档案；已有 MS 差异归因表和 Williams 历史 NPZ 是另行保存的结果。归因解释的是编码器输出之和相对于零基线的贡献，不等于疾病因果重要性，编码位移不等于治疗效果。

### 离线与在线测试

无需启动服务、下载模型或读取患者表达矩阵的核心回归（在本目录运行；历史面板测试会读取仓库中的小型存档报告与结果）：

```bash
python -m unittest discover -s tests -v
```

此测试独立于下述 API/浏览器验收，覆盖引擎异常输入、基因名与返回数值对应、资源预检、归因输出保护、PBMC 注释对齐/完整发布、稀疏最大值格式、API 参数契约及初始化失败/并发，不代表真实疾病预测效果或全量模型验收。PBMC 合成数据流测试使用模型/UMAP 替身；API 测试执行实际路由与 FastAPI 校验，但跳过 app 导入时的模型启动；缓存读写用临时目录及真实小矩阵引擎。不加载真实模型或联网下载。使用现有 VCT 环境，不另加 Python 测试依赖。CIPHER 拟合至少需要两个细胞；baseline 可接受一个细胞。矩阵维度、基因名数量/唯一性及有限值必须有效；未知的返回子集基因会明确报错，不再静默过滤。

前端异步状态可另用 Node.js 内置测试器离线检查（需要支持 `node --test` 的 Node，无 npm 依赖；不是 Web 服务运行依赖）：

```bash
node --test tests/test_web_state.cjs
```

它执行实际页面脚本，控制 DOM/fetch/Plotly 替身，检查旧请求晚到、失败、快速切换、滑块/搜索及绘图快照，也检查历史入口与数据集隔离、缺失/损坏材料提示及接口失败后清空旧指标；不替代下面的真实浏览器点击验收。

Web 输入约定：省略 `ds` 仍默认 PBMC；数据集相关端点显式传未知键返回 400。`cell` 必须在当前数据集范围内，归因 `k` 为 1～100、搜索 `limit` 为 1～200，`direction` 只接受 `ko/oe`，基线 `method` 只接受 `ctrl_mean/additive/both`；非法值返回 422，页面显示具体原因。数量上限只限制返回结果，不裁剪输入矩阵。切换数据/选择时过期响应被忽略，已完成图表保留其来源；加载期间旧数据操作被禁用。同数据集在单服务进程内只初始化一次，失败不发布半成品、下次请求可重试；不提供跨进程锁、后台自动重试或整机内存限额。

三个数据集的表达矩阵、元数据、UMAP 缓存，以及 SIGnature 编码器和 GEARS 检查点均由用户另行获取或生成，不随 Git/LFS 交付。根目录 `.gitignore` 排除了较大的 `cipher_*.npz` 缓存、`ms_attribution_fp16.npy` 和 Norman 原始/解压数据；缓存首次使用时重算，WS 首次加载更耗时与内存。GEARS 原始数据来源是 [Zenodo 17252307](https://zenodo.org/records/17252307) 的 `norman.zip`；下载到 `gears_data/` 并解压后，`norman/data_pyg/cell_graphs.pkl` 会由 GEARS 从 `perturb_processed.h5ad` 生成。在 PBMC/MS/WS 配套数据及编码器已准备的前提下，未下载 Norman 时网页的三个核心模式仍可运行，但 GEARS 因果功能不可验收。

浏览器回归测试还需要可选依赖：

```bash
python -m pip install -r requirements-e2e.txt
PLAYWRIGHT_BROWSERS_PATH="$PWD/.playwright-browsers" python -m playwright install chromium
python tests_e2e_playwright.py
```

若已安装系统 Chrome，也可不下载 Playwright Chromium，设置 `PLAYWRIGHT_CHROMIUM_EXECUTABLE` 为 Chrome 可执行文件路径后运行同一测试。测试使用独立的无头浏览器，不操作个人资料或现有标签页。通过真实鼠标点击 UMAP、点击归因行、输入搜索/选择基因和按钮完成流程；只读取绘图坐标来定位鼠标，不调用页面内部选择函数。等待具体响应和界面状态，每步最长 180 秒，不用固定秒数猜测是否完成。测试仅检查反事实位移能计算/出图，不把非零位移当科学验收条件。

浏览器流程还会在 PBMC 与 MS 页面分别打开历史面板，检查固定来源、Williams 指标、缺图标识、旧图解释和三张存档图加载。测试截图存本目录 `test_artifacts/`（成功 `vct_verify.png`、失败且页面仍可访问时 `vct_failure.png`）；异常返回非零，缺少 Playwright 返回 2 而非跳过后假报成功。浏览器启动失败时可能没有截图。页面的 GEARS 覆盖性检查也会被触发，所以此浏览器测试需要相应数据可用，不能拿 API 的 `--skip-gears` 结果代替。浏览器下载目录和截图均不入库。

服务接口和数据加载逻辑见 `web/app.py`、`src/paths.py`。`src/paths.py` 按本目录位置解析本仓库内的数据、模型和仓库 `05_tools/SIGnature` 源码（可用 `SIGNATURE_DIR` 指定），不依赖旧工作站路径。

## 使用边界

### 离线 CLI 的资源与输出保护

`src/viz_perturbation.py` 在加载表达矩阵主体和转稠密前读取尺寸，估算表达副本和协方差工作内存。默认 `--max-memory-gib 2`（GiB）是保护预算，超预算退出 2，提示估算值/预算和矩阵尺寸，尚不创建输出目录。当前全基因 WS/PBMC 会被这一预算拦截；可考虑已有 Web HVG 工作流，或在确认机器内存足够后显式提高预算。程序不自动抽样或删基因。此估算不是操作系统硬限制，不覆盖其他进程、所有库内部峰值和强制杀进程；捕获到 MemoryError 会明确提示，但不能承诺绝不耗尽资源。Web 路径也不等于已完成所有设备上的资源验收。

`src/compute_ms_attribution.py` 将效应量排序和配套结果全部完成后，先写临时目录，再发布到新运行目录：

```bash
python src/compute_ms_attribution.py --output outputs/ms_run_001
```

省略 `--output` 时使用带时间戳的新目录；已有目标拒绝覆盖。结果包含归因矩阵、embedding、样本表、差异归因表以及矩阵列顺序 `gene_order.txt`（差异表按效应量排序，不能替代矩阵列顺序）。不会自动替换网页 `data/`，需核对整套结果后再决定如何更新展示数据。中途写入失败不发布半套运行目录，临时文件正常异常退出时清理；强制终止可能遗留临时目录。脚本仍是昂贵的全量归因，不应把这里的输出保护误认为适用于它的内存预算保护。

### PBMC 测试数据的安全重建

PBMC 是早期验证工具可行性的测试数据，不是本项目微缺失疾病的患者数据。直接使用现有网页数据不需要重建。需要重建时，在本目录运行：

```bash
python src/prepare_data.py \
  --metadata /path/to/approved_pbmc_labels.csv --output outputs/pbmc_run_001
```

`--metadata` 必须显式指定你认可来源的 CSV；`cell` 为原始 PBMC 的细胞 ID，`cell_type` 为已确认标签，`cluster` 可选且提供时原样保留。ID 必须唯一并与原始数据完整对应，程序按 ID 重排，不能仅凭行数相同。缺列/空标签先于数据读取失败，细胞不匹配先于模型加载失败；不自动读取旧 meta，不新增聚类或把聚类编号猜成细胞类型。现有注释是否适用于一次重建，仍需使用者确认。

省略 `--output` 会生成独立时间戳目录，已有目标拒绝覆盖。原始数据、对齐表达、embedding、注释、UMAP、基因列顺序和 `pbmc_info.json` 完整写入后才发布；信息文件记录测试用途及本次注释来源路径。失败不发布半套目录，强制终止可能遗留临时目录；本脚本不自动替换网页 `data/`。将新结果用于展示前还需核对兼容性和相关缓存，不能只换其中一个文件。实际运行仍需要现有模型及 PBMC 数据/下载条件，本轮没有进行全量重建验收。

MS/WS 准备脚本的 `gene_max.npy` 现在保存普通的一维数值向量，检查长度/有限性且禁用 pickle 保存；只展开稀疏最大值一行，不改变归一化。仓库已有的两份旧 object 文件保持不变，当前网页不读取它们；修复生成代码不等于历史文件已修复，也不要为了读旧文件开启 pickle。这两个脚本其余输出步骤仍保持原状，本次没有给它们增加整套输出保护或重新执行。

### 科学解释范围

- 网页「⑤ 编码器敏感性探索（实验性）」默认折叠，展开后仍可进行单/多基因输入修改与编码位移观察。它只改变指定输入、其他基因输入保持不变；最近参考质心变化不是细胞类型转化，位移大小不能直接认定主效基因或疗效。该入口保留早期探索与迭代证据，不作为核心生物学预测功能；原公式、接口和历史结果不变。
- CIPHER 使用线性响应近似，弱表达或稀疏信号的基因可能没有可靠预测。
- 反事实扰动和编码器位移不是因果治疗预测；大幅度扰动尤其需要谨慎。
- GEARS 的 Norman/K562 训练分布和微缺失疾病体系不同，主要用于覆盖性与方法对照。
- 转录组效应不能代表 SINEUP 介导的翻译层面干预效果。

### 历史实验与方法迭代（只读）

发布说明：下述为本地完整历史材料的能力。新克隆没有历史结果表，历史面板会显示缺失；独立 HTML 报告仍可阅读。

点击网页顶部的「历史实验与方法迭代」，或展开编码器探索后点击历史证据入口。面板作为独立标签打开，也可访问 `/web/history.html`。更新 Python 后端后需重启服务；仅刷新网页不能加载新增接口。

请通过服务地址打开，例如 `http://127.0.0.1:8377/web/history.html`，不要直接双击 `web/history.html`：本地 `file://` 模式无法读取历史接口，页面会明确提示并提供默认服务入口，不代表图片丢失。使用自定义 `VCT_PORT` 时，以启动日志的地址为准；页面不会自动启动服务或扫描端口。

面板按疾病 CellOracle 实验、v1 归因/编码探索、v2 GEARS/Tier 0、v3 CIPHER/基线整理现有证据，不声称存在已证实的直接替代链，也不进行跨背景性能排名。显示三张已有图：MS 归因、CEBPA/GEARS、PBMC/MS4A1 基线对照；旧图中“34 倍位移、互相印证”等解释已在图前明确修正，原文件不改写。

- Williams 3016 基因的 KO/OE Spearman 从保存的汇总向量复算；其余指标读取历史 JSON，均不等于重新运行实验。
- Williams、PBMC 编码探索和 Tier 0 的对应图片标为待补；22q/TBX1 仅有报告描述，未找到对应结果 NPZ/图。汇总向量不能还原逐细胞轨迹。以后补绘须注明“基于历史数据补绘”。
- Tier 0 的 A549 标签与其他 Norman/K562 记录的关系待核对，本轮没有擅自改标签或把它们视为同背景比较。
- `/api/history` 不接入当前疾病/细胞/基因状态；`/api/history/artifacts/{key}` 只提供 `src/history_panel.py` 明确列出的 14 份材料，拒绝未知键与逃逸仓库的路径。不会公开整个数据目录、加载 CellOracle 或触发模型计算。
- 缺失、损坏和非有限结果分别提示，不用零值代替；加载失败清空上次指标。文件路径与 SHA-256 可查，但仅核对当前文件，不补造历史运行来源。

这交付的是可核对的历史展示，不是历史复现环境。Williams 原始/中间输入和依赖、网络及参数版本仍需补齐；CR-033 保持待处理，不向主环境安装 CellOracle。

### 历史探索脚本与工程验收的区别

以下文件名保留以便追溯，但不是标准测试流程中的科学通过门槛；不要仅凭文件名含 `validate/test` 或退出码 0 判断假设成立。

| 脚本 | 探索报告（相对于本工具目录） |
|---|---|
| `src/validate.py` | `data/validation_results.json`；保留原 AC1/AC2 数值与历史 `pass` 字段 |
| `src/tier0_validate.py` | `data/tier0_validation.json`；保留原指标与表格 |
| `predictive_test.py` | `data/predictive_exploration.json`；方向比较与影响相关性 |
| `validate_attribution_vs_perturb.py` | `data/attribution_vs_perturb_exploration.json`；逐基因差分归因比较 |

报告标注 `report_type: exploration`、`completion_status: completed` 和解释边界。退出 0 仅表示计算及报告写入完成；阴性结果、负相关或历史 `pass: false` 不因此当作程序故障。原 `pass` 仅指原脚本设定的历史比较条件，不是科学有效性认证。缺输入、计算异常、空报告、不可序列化/非有限指标或写入失败会非零退出；未定义的统计量也不能伪装成完整报告，需要检查数据条件，不等同科学假设被否定。本次未增加科学阈值或改变指标公式。

这些脚本需正式数据/模型，部分包含全矩阵展开和大量推理，不属于轻量用户冒烟测试；本轮未重新运行或覆盖历史结果。手动重跑会写入上述路径，应先备份需要保留的历史报告。工程验证请使用前述 `tests/`、API 与浏览器流程。

架构与历史实验见 `docs/`、`ATTRIBUTIONS.md`；旧版本性能数字并非在所有新设备上的保证。
