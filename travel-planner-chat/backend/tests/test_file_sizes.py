import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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


class IgnoredDirectoryTests(unittest.TestCase):
    def test_generated_directories_are_not_traversed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            ignored = root / 'node_modules'
            ignored.mkdir()
            (ignored / 'large.js').write_text('\n' * 151)
            with patch('os.scandir', wraps=os.scandir) as scan:
                self.assertEqual(file_sizes.oversized_files(root), [])
            self.assertNotIn(str(ignored), [str(call.args[0]) for call in scan.call_args_list])
