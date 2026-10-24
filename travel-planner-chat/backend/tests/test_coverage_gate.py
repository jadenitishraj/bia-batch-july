import json
import os
import runpy
import tempfile
import unittest
from pathlib import Path

from check_coverage import check_coverage

ROOT = Path(__file__).resolve().parents[1]


def report(lines=90, branches=90):
    return {'totals': {'num_statements': 100, 'covered_lines': lines,
                       'num_branches': 100, 'covered_branches': branches}}


class CoverageGateTests(unittest.TestCase):
    def test_requires_both_metrics_independently(self):
        self.assertTrue(check_coverage(report()))
        self.assertFalse(check_coverage(report(lines=89)))
        self.assertFalse(check_coverage(report(branches=89)))
        self.assertTrue(check_coverage({'totals': {
            'num_statements': 0, 'covered_lines': 0, 'num_branches': 0, 'covered_branches': 0}}))

    def test_command_reads_report_and_fails_below_threshold(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                Path('coverage.json').write_text(json.dumps(report()))
                runpy.run_path(str(ROOT / 'check_coverage.py'), run_name='__main__')
                Path('coverage.json').write_text(json.dumps(report(branches=89)))
                with self.assertRaises(SystemExit):
                    runpy.run_path(str(ROOT / 'check_coverage.py'), run_name='__main__')
            finally:
                os.chdir(original)
