"""Offline R09 path contracts; no real data, network, models or browser needed."""
import ast
import contextlib
import io
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
WILLIAMS = ROOT / "02_disease-williams/02_scripts"


class HistoricalPathTests(unittest.TestCase):
    def test_all_historical_scripts_parse_and_are_indexed(self):
        for directory, scripts in ((ROOT / "01_disease-22q11.2", ROOT / "01_disease-22q11.2"),
                                   (WILLIAMS.parent, WILLIAMS)):
            readme = (directory / "README.md").read_text()
            for script in scripts.glob("*.py"):
                with self.subTest(script=script.name):
                    ast.parse(script.read_text(), filename=str(script))
                    self.assertIn(f"`{script.name}`", readme)

    def test_preprocess_write_creates_missing_directory_and_allows_existing(self):
        script = WILLIAMS / "preprocess.py"
        tree = ast.parse(script.read_text())
        # Execute only the real output tail after the final sanity-check loop.
        # The scientific preprocessing steps are deliberately not executed.
        last_loop = max(i for i, node in enumerate(tree.body) if isinstance(node, ast.For))
        code = compile(ast.Module(body=tree.body[last_loop + 1:], type_ignores=[]), str(script), "exec")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "clean clone/02_disease-williams"
            output = base / "03_intermediate/processed.h5ad"

            def write(path):
                self.assertEqual(path, output)
                if not path.parent.is_dir():
                    raise FileNotFoundError(path.parent)

            adata = SimpleNamespace(write=MagicMock(side_effect=write), shape=(2, 3))
            for _ in range(2):
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(code, {"BASE": base, "adata": adata})
            self.assertEqual(adata.write.call_count, 2)



class PDFToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.source = self.base / "报告 #1.html"
        self.source.write_text("<h1>test</h1>")
        self.sync = MagicMock()
        self.browser = self.sync.return_value.__enter__.return_value.chromium.launch.return_value
        self.page = self.browser.new_page.return_value

    def run_cli(self, args, missing_dependency=False):
        module = SimpleNamespace(sync_playwright=self.sync, Error=RuntimeError)
        modules = {"playwright": MagicMock(), "playwright.sync_api": module}
        if missing_dependency:
            modules = {"playwright": None, "playwright.sync_api": None}
        stderr = io.StringIO()
        with contextlib.chdir(self.base), patch.dict(sys.modules, modules), \
             patch.object(sys, "argv", ["html2pdf.py", *args]), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            try:
                runpy.run_path(str(WILLIAMS / "html2pdf.py"), run_name="__main__")
            except SystemExit as exc:
                return exc.code, stderr.getvalue()
        return 0, stderr.getvalue()

    def test_relative_and_absolute_input_use_encoded_file_uri(self):
        for source in (self.source.name, str(self.source)):
            with self.subTest(source=source):
                status, error = self.run_cli([source, "new dir/report.pdf"])
                self.assertEqual(status, 0, error)
                self.page.goto.assert_called_with(self.source.as_uri(), wait_until="networkidle")
                self.assertEqual(Path(self.page.pdf.call_args.kwargs["path"]),
                                 self.base / "new dir/report.pdf")
                self.assertTrue((self.base / "new dir").is_dir())
                self.browser.close.assert_called()

    def test_invalid_arguments_fail_before_browser_start(self):
        for args in ([], ["missing.html", "report.pdf"], [self.source.name, self.source.name]):
            with self.subTest(args=args):
                status, error = self.run_cli(args)
                self.assertEqual(status, 2)
                self.assertTrue(error)
                self.sync.assert_not_called()
        self.assertEqual(self.source.read_text(), "<h1>test</h1>")

    def test_missing_dependency_is_an_actionable_nonzero_error(self):
        status, error = self.run_cli([self.source.name, "report.pdf"], missing_dependency=True)
        self.assertEqual(status, 2)
        self.assertIn("Playwright", error)
        self.assertIn("README", error)

    def test_missing_browser_is_an_actionable_nonzero_error(self):
        self.sync.return_value.__enter__.return_value.chromium.launch.side_effect = RuntimeError("missing browser")
        status, error = self.run_cli([self.source.name, "report.pdf"])
        self.assertEqual(status, 2)
        self.assertIn("missing browser", error)
        self.assertIn("Chromium", error)

    def test_render_failure_closes_browser_and_does_not_report_success(self):
        self.page.pdf.side_effect = RuntimeError("render failed")
        status, error = self.run_cli([self.source.name, "report.pdf"])
        self.assertEqual(status, 2)
        self.assertIn("render failed", error)
        self.browser.close.assert_called_once()

    def test_output_directory_error_fails_before_browser_start(self):
        (self.base / "blocked").write_text("not a directory")
        status, error = self.run_cli([self.source.name, "blocked/report.pdf"])
        self.assertEqual(status, 2)
        self.assertIn("PDF", error)
        self.sync.assert_not_called()

    def test_help_works_without_optional_dependencies(self):
        status, error = self.run_cli(["--help"], missing_dependency=True)
        self.assertEqual(status, 0, error)
        self.sync.assert_not_called()

    def test_real_cli_rejects_missing_input_without_traceback(self):
        result = subprocess.run([sys.executable, str(WILLIAMS / "html2pdf.py"),
                                 str(self.base / "missing.html"), str(self.base / "report.pdf")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("HTML", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
