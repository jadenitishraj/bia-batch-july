"""Package source only: no accounts, trips, login keys, caches or local settings."""
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = Path(sys.argv[1]).resolve()
    with tarfile.open(output, 'w:gz') as archive:
        for path in sorted((ROOT / 'backend').iterdir()):
            if path.is_file() and (path.suffix == '.py' or path.name == 'requirements.txt'):
                archive.add(path, arcname=path.name)
    print('Packaged backend source without local data or secrets.')


if __name__ == '__main__':
    main()
