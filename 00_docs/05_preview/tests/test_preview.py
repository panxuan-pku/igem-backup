"""Read-only documentation preview contracts, without starting the scientific tools."""
import importlib.util
from pathlib import Path
from http.server import ThreadingHTTPServer
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MODULE = Path(__file__).resolve().parents[1] / "serve.py"
spec = importlib.util.spec_from_file_location("documentation_preview", MODULE)
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), preview.Handler)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()

    def request(self, path, method="GET"):
        return urlopen(Request(self.base + path, method=method), timeout=5)

    def test_new_organization_pages_are_readable(self):
        for path in ("/04_reports/index.html", "/05_virtual_cell/docs/index.html",
                     "/00_docs/01_guides/VCT_SETUP.html", "/06_epidemiology/docs/index.html",
                     "/03_pipeline/outputs/cnv/index.html", "/scripts/index.html"):
            with self.subTest(path=path), self.request(path) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get_content_type(), "text/html")

    def test_home_and_head(self):
        with self.request("/") as response:
            self.assertIn("项目资料导航".encode(), response.read())
        with self.request("/", "HEAD") as response:
            self.assertEqual(response.read(), b"")
            self.assertGreater(int(response.headers["Content-Length"]), 100)

    def test_reviewed_figure_has_image_type_and_policy(self):
        with self.request("/06_epidemiology/figures/22q11_2_forest.png") as response:
            self.assertEqual(response.headers.get_content_type(), "image/png")
            self.assertIn("img-src 'self' data:", response.headers["Content-Security-Policy"])
            self.assertIn("default-src 'none'", response.headers["Content-Security-Policy"])

    def test_unlisted_source_data_and_traversal_are_denied(self):
        for path in ("/scripts/setup_envs.sh", "/05_virtual_cell/web/app.py",
                     "/05_virtual_cell/data/meta.csv", "/.git/config",
                     "/03_pipeline/outputs/", "/00_docs/%2e%2e/.git/config"):
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                self.request(path)
            self.assertEqual(error.exception.code, 404)

    def test_post_is_denied(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/", "POST")
        self.assertEqual(error.exception.code, 501)


if __name__ == "__main__":
    unittest.main()
