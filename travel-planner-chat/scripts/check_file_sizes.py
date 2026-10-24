"""Enforce readable, small handwritten project files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {'node_modules', 'dist', '__pycache__', 'data', '.git'}
IGNORED_FILES = {'package-lock.json'}
TEXT_SUFFIXES = {'.py', '.js', '.css', '.html', '.json', '.md'}


def oversized_files(root=ROOT, limit=150):
    result = []
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if (not path.is_file() or IGNORED_PARTS.intersection(relative.parts)
                or path.name in IGNORED_FILES or path.suffix not in TEXT_SUFFIXES):
            continue
        count = len(path.read_text(encoding='utf-8').splitlines())
        if count > limit:
            result.append((relative, count))
    return result


if __name__ == '__main__':
    failures = oversized_files()
    for path, count in failures:
        print(f'{path}: {count} lines (maximum 150)')
    if failures:
        raise SystemExit(1)
    print('All handwritten project files are within 150 lines.')
