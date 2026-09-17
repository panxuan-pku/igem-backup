import sys
from playwright.sync_api import sync_playwright

html_path = sys.argv[1]
pdf_path = sys.argv[2]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"file://{html_path}", wait_until="networkidle")
    page.pdf(path=pdf_path, format="A4", print_background=True,
             margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
    browser.close()
print(f"PDF 已生成: {pdf_path}")
