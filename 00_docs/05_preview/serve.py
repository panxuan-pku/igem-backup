"""Read-only loopback preview for the reviewed documentation and its references."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "00_docs"
SUFFIXES = {".html", ".md", ".rst", ".yaml", ".json", ".csv", ".txt", ".png", ".svg", ".pdf", ".docx"}
EXTRA = set()
MANIFEST = Path(__file__).with_name("DOCUMENT_PREVIEW_FILES.json")
EXTRA.update((ROOT / name).resolve() for name in json.loads(MANIFEST.read_text())["files"])
HOME = "/00_docs/01_guides/PROJECT_INDEX.html"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.respond()

    def do_HEAD(self):
        self.respond(head_only=True)

    def respond(self, head_only=False):
        path = unquote(urlsplit(self.path).path)
        if path == "/":
            path = HOME
        target = (ROOT / path.lstrip("/")).resolve()
        allowed = target.is_relative_to(ROOT) and (target.is_relative_to(DOCS) or target in EXTRA)
        if not allowed or target.suffix not in SUFFIXES or not target.is_file():
            self.send_error(404, "Document not available")
            return
        try:
            content = target.read_bytes()
        except OSError:
            self.send_error(404, "Document not available")
            return
        self.send_response(200)
        kind = {".html": "text/html; charset=utf-8", ".png": "image/png",
                ".svg": "image/svg+xml", ".pdf": "application/pdf",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}.get(
                    target.suffix, "text/plain; charset=utf-8")
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.end_headers()
        if not head_only:
            self.wfile.write(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"文档预览：http://127.0.0.1:{server.server_port}{HOME}", flush=True)
        print("仅本机只读文档；Ctrl+C 停止。", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
