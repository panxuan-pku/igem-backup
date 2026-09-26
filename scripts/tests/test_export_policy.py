"""Export only public files, even before ignored files leave the Git index."""
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'export_github.sh'


class ExportPolicyTests(unittest.TestCase):
    def test_ignored_tracked_and_untracked_files_are_not_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'source'
            root.mkdir()
            (root / 'scripts').mkdir()
            script = root / 'scripts/export_github.sh'
            script.write_bytes(SCRIPT.read_bytes())
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'private.txt').write_text('local evidence')
            (root / 'public.txt').write_text('source')
            subprocess.run(['git', '-C', str(root), 'add', 'private.txt', 'public.txt'], check=True)
            (root / '.gitignore').write_text('private.txt\nmodels/\n')
            (root / 'models').mkdir()
            (root / 'models/weights.bin').write_bytes(b'weights')
            (root / 'new.html').write_text('<h1>Report</h1>')
            dest = Path(directory) / 'export'
            subprocess.run(['bash', str(script), str(dest)], check=True, capture_output=True)
            self.assertFalse((dest / 'private.txt').exists())
            self.assertFalse((dest / 'models').exists())
            self.assertFalse((dest / '.git').exists())
            self.assertEqual((dest / 'public.txt').read_text(), 'source')
            self.assertTrue((dest / 'new.html').is_file())
            self.assertTrue((root / 'private.txt').exists())
            self.assertNotEqual(subprocess.run(['bash', str(script), str(dest)], capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
