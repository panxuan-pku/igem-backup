"""Resolve relocated VCT and external SIGnature without machine-local paths."""
import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class RelocatedPathsTests(unittest.TestCase):
    def test_default_and_override(self):
        with patch.dict(os.environ, {}, clear=True):
            paths = runpy.run_path(str(ROOT / 'src/paths.py'))
        self.assertEqual(Path(paths['VCT_ROOT']), ROOT)
        self.assertEqual(Path(paths['SIG_DIR']), ROOT.parent / '05_tools/SIGnature')
        self.assertEqual(Path(paths['DATA_DIR']), ROOT / 'data')
        with patch.dict(os.environ, {'SIGNATURE_DIR': str(ROOT / 'external-signature')}):
            paths = runpy.run_path(str(ROOT / 'src/paths.py'))
        self.assertEqual(Path(paths['MODEL_DIR']), ROOT / 'external-signature/model_files/model_files/scimilarity')

    def test_launcher_uses_conda_environment(self):
        launcher = (ROOT / '启动VirtualCellTool.command').read_text()
        self.assertIn('run --no-capture-output -n virtual-cell python', launcher)
        self.assertIn('"$VCT/src/web_launcher.py"', launcher)
        self.assertNotIn('.venv', launcher)
