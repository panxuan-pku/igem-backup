"""VirtualCellTool 前端端到端验证（真实 Chromium 渲染 + 点击交互）"""
import os, sys, json, time
from pathlib import Path
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(Path(__file__).resolve().parent / ".playwright-browsers"))
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8377/"
errs, fails = [], []

with sync_playwright() as p:
    browser_executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    b = p.chromium.launch(headless=True, executable_path=browser_executable)
    pg = b.new_page(viewport={"width": 1500, "height": 950})
    pg.on("console", lambda m: errs.append(f"[{m.type}] {m.text}") if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(f"[pageerror] {e}"))
    pg.on("response", lambda r: errs.append(f"[http {r.status}] {r.url}") if r.status >= 400 else None)

    pg.goto(URL, wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(3500)

    def chk(name, cond, detail=""):
        print(("✅ " if cond else "❌ ") + name + (f"  {detail}" if detail else ""))
        if not cond: fails.append(name)

    # 1) 数据集就绪
    st = pg.inner_text("#dsState")
    chk("数据集加载", "✓" in st, st.strip())

    # 2) UMAP 画出来了（canvas 或 svg 存在）
    has_plot = pg.evaluate("""() => {
        const e = document.getElementById('plot_umap');
        if (!e) return false;
        return !!(e.querySelector('canvas') || e.querySelector('.main-svg'));
    }""")
    chk("UMAP 渲染", has_plot)

    # 3) 点 UMAP 上一个点 → 触发选细胞 + 归因
    pg.evaluate("selectCell(0)")
    pg.wait_for_timeout(2500)
    ci = pg.inner_text("#cellInfo")
    chk("选细胞+归因", "✓" in ci, ci.strip()[:70])
    nrows = pg.evaluate("document.querySelectorAll('.geneRow').length")
    chk("归因表有行", nrows > 0, f"{nrows} 行")

    # 4) 点归因表第一个基因
    if nrows:
        pg.click(".geneRow")
        pg.wait_for_timeout(1800)
        gh = pg.inner_text("#cipherHint")
        chk("CIPHER 覆盖性提示", "可预测" in gh or "不在" in gh, gh.strip()[:70])

    # 5) 选一个确定可用的基因跑 CIPHER 敲低
    pg.evaluate("pickGene('MS4A1')")
    pg.wait_for_timeout(1800)
    ko_enabled = pg.evaluate("!document.getElementById('cipherKoBtn').disabled")
    chk("CIPHER 敲低按钮可用", ko_enabled)

    if ko_enabled:
        pg.click("#cipherKoBtn")
        pg.wait_for_timeout(3500)
        tabs = pg.evaluate("[...document.querySelectorAll('.tab')].map(t=>t.innerText.trim())")
        chk("新开图表标签页", len(tabs) >= 2, str(tabs))
        drew = pg.evaluate("""() => {
            const v=[...document.querySelectorAll('.view')].find(v=>v.classList.contains('on'));
            if(!v) return false;
            const b=v.querySelector('.plotbox');
            return !!(b && (b.querySelector('.main-svg')||b.querySelector('canvas')));
        }""")
        chk("CIPHER 图表渲染", drew)
        stat = pg.inner_text("#status")
        chk("状态栏有结果", "上调" in stat, stat.replace("\n", " ")[:110])

    # 6) 过表达 → 应新开一个标签页，不覆盖前一个
    pg.click("#cipherOeBtn"); pg.wait_for_timeout(3000)
    tabs2 = pg.evaluate("[...document.querySelectorAll('.tab')].map(t=>t.innerText.trim())")
    chk("图表不被覆盖（多标签共存）", len(tabs2) >= 3, str(tabs2))

    # 7) 线性基线
    pg.click("#baselineBtn"); pg.wait_for_timeout(3000)
    stat = pg.inner_text("#status")
    chk("线性基线对照", "基线" in stat, stat.replace("\n"," ")[:90])

    # 8) 反事实位移（UMAP 箭头）
    pg.evaluate("selectCell(0)"); pg.wait_for_timeout(2000)
    pg.evaluate("pickGene('MS4A1')"); pg.wait_for_timeout(1500)
    pg.click("#goBtn"); pg.wait_for_timeout(3000)
    stat = pg.inner_text("#status")
    chk("反事实扰动", "位移" in stat, stat.replace("\n"," ")[:90])

    # 9) 切数据集（关键回归：必须带 ds 参数且原地重载）
    pg.select_option("#dsSel", "ms")
    pg.wait_for_timeout(1000)
    for _ in range(60):
        if "✓" in pg.inner_text("#dsState"): break
        pg.wait_for_timeout(2000)
    st2 = pg.inner_text("#dsState")
    chk("切换到 MS 数据集", "✓" in st2, st2.strip())
    ds_in_api = pg.evaluate("DS")
    chk("前端 DS 变量已更新", ds_in_api == "ms", ds_in_api)
    ncells = pg.evaluate("DATA.n_cells")
    chk("MS 数据集细胞数正确", ncells == 17799, str(ncells))

    artifacts = Path(__file__).resolve().parent / "test_artifacts"
    artifacts.mkdir(exist_ok=True)
    pg.screenshot(path=str(artifacts / "vct_verify.png"), full_page=False)
    b.close()

print("\n=== 控制台错误 ===")
for e in errs[:12]: print(" ", e)
if not errs: print("  无")
if errs: fails.append("浏览器控制台或 HTTP 错误")
print(f"\n结果: {'全部通过 ✅' if not fails else '失败项: ' + str(fails)}")
sys.exit(1 if fails else 0)
