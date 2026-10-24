"""Enforce readable, small handwritten project files."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {'node_modules', 'dist', '__pycache__', 'data', '.git', '.venv', '.ruff_cache'}
IGNORED_FILES = {'package-lock.json'}
TEXT_SUFFIXES = {'.py', '.js', '.css', '.html', '.json', '.md'}


def oversized_files(root=ROOT, limit=150):
    result = []
    for directory, folders, filenames in os.walk(root):
        folders[:] = sorted(name for name in folders if name not in IGNORED_PARTS)
        for name in sorted(filenames):
            path = Path(directory) / name
            if name in IGNORED_FILES or path.suffix not in TEXT_SUFFIXES:
                continue
            count = len(path.read_text(encoding='utf-8').splitlines())
            if count > limit:
                result.append((path.relative_to(root), count))
    return result


if __name__ == '__main__':
    failures = oversized_files()
    for path, count in failures:
        print(f'{path}: {count} lines (maximum 150)')
    if failures:
        raise SystemExit(1)
    print('All handwritten project files are within 150 lines.')
