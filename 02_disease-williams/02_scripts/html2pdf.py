import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="将本地 HTML 导出为 PDF（需 Playwright / Chromium）")
    parser.add_argument("html_path", type=Path)
    parser.add_argument("pdf_path", type=Path)
    args = parser.parse_args()
    html_path = args.html_path.expanduser().resolve()
    pdf_path = args.pdf_path.expanduser().resolve()
    if not html_path.is_file():
        parser.error(f"HTML 输入文件不存在或不是文件: {html_path}")
    if html_path == pdf_path:
        parser.error("PDF 输出不能覆盖 HTML 输入文件")

    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError:
        parser.exit(2, "缺少 Playwright；请按 02_disease-williams/README.md 安装可选 PDF 依赖。\n")

    try:
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                page.goto(html_path.as_uri(), wait_until="networkidle")
                page.pdf(path=str(pdf_path), format="A4", print_background=True,
                         margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
            finally:
                browser.close()
    except (Error, OSError) as exc:
        parser.exit(2, f"PDF 导出失败: {exc}\n请确认 Chromium 已按 README 安装，且文件路径可读写。\n")
    print(f"PDF 已生成: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
