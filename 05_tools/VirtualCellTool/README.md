# VirtualCellTool

单细胞虚拟扰动演示工具，包含 PBMC、MS 和 Williams 三个数据集。CIPHER 是未扰动对照细胞的线性响应近似；反事实嵌入和 GEARS 分别是展示性外推与有限覆盖的对照，均不能视作临床或治疗效果预测。

## 从克隆目录启动

在仓库根目录运行 `git lfs pull`、`python3 scripts/check_release.py` 和 `bash scripts/setup_envs.sh`。随后：

```bash
cd 05_tools/VirtualCellTool
../../.venv/vct/bin/python web/app.py
```

打开 `http://127.0.0.1:8377/`；数据集在页面顶部切换，不需要多个服务实例。macOS 也可双击 `启动VirtualCellTool.command`，该启动器使用同一个仓库根目录环境。通过终端启动时按 Ctrl-C 停止，不要用宽泛的 `pkill` 命令。不要沿用 `SIGnature/.venv`：旧环境含绝对路径，不可搬迁。

服务运行期间，另开终端运行 `../../.venv/vct/bin/python tests_api.py --skip-gears`，先验收三个数据集及不需要 Norman 数据的 16/18 项；按仓库根目录 README 下载并解压 Norman 数据后，去掉 `--skip-gears` 验收包括 GEARS 在内的全部 18 项。

## 数据与测试

三个数据集的表达矩阵、元数据、UMAP 缓存，以及 SIGnature 编码器和 GEARS 检查点随 Git/LFS 交付。根目录 `.gitignore` 排除了较大的 `cipher_*.npz` 缓存、`ms_attribution_fp16.npy` 和 Norman 原始/解压数据；缓存首次使用时重算，WS 首次加载更耗时与内存。GEARS 原始数据来源是 [Zenodo 17252307](https://zenodo.org/records/17252307) 的 `norman.zip`；下载到 `gears_data/` 并解压后，`norman/data_pyg/cell_graphs.pkl` 会由 GEARS 从 `perturb_processed.h5ad` 生成。未下载时网页的 PBMC/MS/WS 核心模式仍可运行，但 GEARS 因果功能不可验收。

浏览器回归测试还需要可选依赖：

```bash
../../.venv/vct/bin/python -m pip install -r requirements-e2e.txt
PLAYWRIGHT_BROWSERS_PATH="$PWD/.playwright-browsers" ../../.venv/vct/bin/python -m playwright install chromium
../../.venv/vct/bin/python tests_e2e_playwright.py
```

若已安装系统 Chrome，也可不下载 Playwright Chromium，设置 `PLAYWRIGHT_CHROMIUM_EXECUTABLE` 为 Chrome 可执行文件路径后运行同一测试。测试截图存本目录 `test_artifacts/`；浏览器下载目录和截图均不入库。

服务接口和数据加载逻辑见 `web/app.py`、`src/paths.py`。`src/paths.py` 按本目录位置解析本仓库内的数据、模型和同级 `SIGnature` 源码，不依赖旧工作站路径。

## 使用边界

- CIPHER 使用线性响应近似，弱表达或稀疏信号的基因可能没有可靠预测。
- 反事实扰动和编码器位移不是因果治疗预测；大幅度扰动尤其需要谨慎。
- GEARS 的 Norman/K562 训练分布和微缺失疾病体系不同，主要用于覆盖性与方法对照。
- 转录组效应不能代表 SINEUP 介导的翻译层面干预效果。

架构与历史实验见 `docs/`、`ATTRIBUTIONS.md`；旧版本性能数字并非在所有新设备上的保证。
