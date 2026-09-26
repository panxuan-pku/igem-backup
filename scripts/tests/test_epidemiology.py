"""R10 figure/data contracts; run with the pipeline environment, entirely offline."""
import contextlib
import io
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "06_epidemiology"
SCRIPT = MODULE / "scripts/microdeletion_prevalence.py"
FIGURES = ("microdeletion_birth_prevalence", "22q11_2_forest",
           "microdeletion_denovo_fraction", "microdeletion_birth_vs_adult")


class EpidemiologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.base = Path(cls.tmp.name).resolve()
        cls.module = cls.base / "clone/06_epidemiology"
        cls.script = cls.module / "scripts/microdeletion_prevalence.py"
        cls.script.parent.mkdir(parents=True)
        shutil.copyfile(SCRIPT, cls.script)
        cls.cwd = cls.base / "unrelated working directory"
        # Let the old version reach plotting, so mapping failures are visible too.
        for name in ("data", "figures"):
            (cls.cwd / "outputs" / name).mkdir(parents=True)
        cls.figures = {}

        def capture(figure, path, **kwargs):
            if Path(path).suffix == ".png":
                cls.figures[Path(path).stem] = figure

        with contextlib.chdir(cls.cwd), patch.object(sys, "argv", [str(cls.script)]), \
             patch.object(Figure, "savefig", autospec=True, side_effect=capture), \
             contextlib.redirect_stdout(io.StringIO()):
            cls.state = runpy.run_path(str(cls.script), run_name="__main__")

    def test_default_output_uses_script_directory(self):
        self.assertEqual(Path(self.state["DATA_DIR"]), self.module / "data")
        self.assertEqual(Path(self.state["FIG_DIR"]), self.module / "figures")

    def test_forest_labels_points_and_annotations_share_rows(self):
        ax = self.figures["22q11_2_forest"].axes[0]
        labels = dict(zip(ax.get_yticks(), (text.get_text() for text in ax.get_yticklabels())))
        points = [line for line in ax.lines if line.get_marker() == "o"]
        self.assertEqual(len(points), 5)
        for (_, row), point in zip(self.state["qdf"].iterrows(), points):
            y = point.get_ydata()[0]
            with self.subTest(study=row["label"]):
                self.assertEqual(labels[y], row["label"])
                self.assertAlmostEqual(point.get_xdata()[0], row["pt"])
                self.assertTrue(any(text.xy == (row["pt"], y) and
                                    text.get_text() == f"{row['pt']:.2f}" for text in ax.texts))

    def test_forest_errorbars_match_estimates(self):
        ax = self.figures["22q11_2_forest"].axes[0]
        rows = self.state["qdf"].dropna(subset=["lo", "hi"])
        self.assertEqual(len(ax.collections), len(rows))
        for (i, row), collection in zip(rows.iterrows(), ax.collections):
            np.testing.assert_allclose(collection.get_segments()[0],
                                       [[row["lo"], i], [row["hi"], i]])
        self.assertTrue(ax.yaxis_inverted())

    def test_forest_table_keeps_counts_units_and_missing_ci(self):
        table = pd.read_csv(self.module / "data/22q11_2_forest.csv")
        pd.testing.assert_frame_equal(table, self.state["qdf"], check_dtype=False)
        self.assertEqual(table["n_cases"].dropna().tolist(), [156, 7, 1, 14])
        self.assertEqual(table["n_total"].dropna().tolist(), [1111336, 25704, 12252, 30074])
        self.assertTrue(table.loc[1, ["lo", "hi", "n_cases", "n_total"]].isna().all())
        self.assertTrue((table["unit"] == "per 10,000 live births").all())
        self.assertTrue((table["src"] == table["label"]).all())

    def test_explanatory_notes_do_not_cover_plot_area(self):
        for name in ("22q11_2_forest", "microdeletion_birth_vs_adult"):
            figure = self.figures[name]
            figure.canvas.draw()
            self.assertTrue(figure.texts)
            for note in figure.texts:
                with self.subTest(figure=name, note=note.get_text()):
                    self.assertFalse(note.get_window_extent().overlaps(figure.axes[0].bbox))

    def test_comparison_table_matches_bars_and_preserves_unknown_source(self):
        table = pd.read_csv(self.module / "data/microdeletion_birth_vs_adult.csv")
        np.testing.assert_allclose(table["birth_pt"], [4.66, 2.94])
        np.testing.assert_allclose(table["adult_pt"], np.array([5, 44]) / 151659 * 10000)
        self.assertEqual(table["adult_n_cases"].tolist(), [5, 44])
        self.assertEqual(table["adult_n_total"].tolist(), [151659, 151659])
        self.assertTrue(pd.isna(table.loc[1, "birth_src"]))
        self.assertEqual(table.loc[1, "birth_source_status"], "unverified")
        self.assertTrue((table["unit"] == "per 10,000").all())
        bars = self.figures["microdeletion_birth_vs_adult"].axes[0].patches
        np.testing.assert_allclose([bar.get_height() for bar in bars],
                                   table["birth_pt"].tolist() + table["adult_pt"].tolist())

    def test_existing_tables_keep_exact_values(self):
        for name in (FIGURES[0], FIGURES[2]):
            self.assertEqual((self.module / f"data/{name}.csv").read_bytes(),
                             (MODULE / f"data/{name}.csv").read_bytes())

    def test_denovo_labels_start_after_errorbars(self):
        ax = self.figures["microdeletion_denovo_fraction"].axes[0]
        labels = [text for text in ax.texts if text.get_text().endswith("%")]
        self.assertEqual(len(labels), len(self.state["dn"]))
        for (_, row), label in zip(self.state["dn"].iterrows(), labels):
            self.assertEqual(label.get_text(), f"{int(row['v'])}%")
            self.assertGreaterEqual(label.xy[0], row["hi"] if np.isfinite(row["hi"]) else row["v"])

    def test_cli_creates_complete_outputs_and_repeats_from_other_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            module = base / "06_epidemiology"
            script = module / "scripts" / SCRIPT.name
            script.parent.mkdir(parents=True)
            shutil.copyfile(SCRIPT, script)
            unrelated = base / "unrelated"
            unrelated.mkdir()
            expected = {f"data/{name}.csv" for name in FIGURES} | {
                f"figures/{name}.{ext}" for name in FIGURES for ext in ("png", "pdf", "svg")}
            for cwd in (unrelated, base):
                result = subprocess.run([sys.executable, str(script)], cwd=cwd,
                                        capture_output=True, text=True, timeout=90)
                self.assertEqual(result.returncode, 0, result.stderr)
                actual = {str(p.relative_to(module)) for d in ("data", "figures")
                          for p in (module / d).iterdir()}
                self.assertEqual(actual, expected)
                self.assertFalse((cwd / "outputs").exists())
                for name in expected:
                    self.assertGreater((module / name).stat().st_size, 20)
            preview = base / "preview"
            result = subprocess.run([sys.executable, str(script), "--output-dir", str(preview)],
                                    cwd=unrelated, capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in FIGURES:
                self.assertEqual((module / f"data/{name}.csv").read_bytes(),
                                 (preview / f"data/{name}.csv").read_bytes())

    def test_package_copies_all_tables_and_refreshes_html_and_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "06_epidemiology"
            package = module / "deliverables/igem_epidemiology_package"
            shutil.copytree(MODULE / "deliverables/igem_epidemiology_package", package)
            for directory in ("data", "figures"):
                (module / directory).mkdir()
            for name in FIGURES:
                (module / f"data/{name}.csv").write_text("value\n1\n")
                (module / f"figures/{name}.svg").write_text(f'<svg><text>{name}</text></svg>')
                (module / f"figures/{name}.png").write_bytes(b"test png")
            result = subprocess.run([sys.executable, str(package / "build.py")], cwd=tmp,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            html = (package / "index.html").read_text()
            with zipfile.ZipFile(package.with_suffix(".zip")) as archive:
                for name in FIGURES:
                    self.assertIn((module / f"figures/{name}.svg").read_text(), html)
                    self.assertIn(f'data/{name}.csv', html)
                    for relative in (f"data/{name}.csv", f"figures/{name}.svg", f"figures/{name}.png"):
                        self.assertEqual((package / relative).read_bytes(), (module / relative).read_bytes())
                        self.assertEqual(archive.read(f"{package.name}/{relative}"), (module / relative).read_bytes())
                self.assertEqual(archive.read(f"{package.name}/index.html"), (package / "index.html").read_bytes())
            self.assertNotIn("outputs/scripts", html)


if __name__ == "__main__":
    unittest.main()
