from pathlib import Path
import importlib.util
import tempfile
import unittest

script = Path(__file__).resolve().parents[2] / 'scripts' / 'check_file_sizes.py'
spec = importlib.util.spec_from_file_location('file_sizes', script)
file_sizes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(file_sizes)


class FileSizeTests(unittest.TestCase):
    def test_project_files_are_small(self):
        self.assertEqual(file_sizes.oversized_files(), [])

    def test_limit_counts_blank_lines_and_ignores_generated_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'small.py').write_text('\n' * 150)
            (root / 'large.py').write_text('\n' * 151)
            (root / 'package-lock.json').write_text('\n' * 500)
            (root / 'node_modules').mkdir()
            (root / 'node_modules' / 'vendor.js').write_text('\n' * 500)
            self.assertEqual(file_sizes.oversized_files(root), [(Path('large.py'), 151)])
