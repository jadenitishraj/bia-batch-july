"""Enforce statements and branches separately from coverage.py's JSON report."""
import json
from pathlib import Path


def check_coverage(report, minimum=90):
    totals = report['totals']
    statements = totals['num_statements']
    branches = totals['num_branches']
    line_percent = 100 * totals['covered_lines'] / statements if statements else 100
    branch_percent = 100 * totals['covered_branches'] / branches if branches else 100
    print(f'Python statements/lines: {line_percent:.2f}%; branches: {branch_percent:.2f}%')
    return line_percent >= minimum and branch_percent >= minimum


if __name__ == '__main__':
    if not check_coverage(json.loads(Path('coverage.json').read_text())):
        raise SystemExit('Backend statements/lines and branches must each reach 90%.')
