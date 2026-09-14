"""Scan a directory tree for .py files containing null bytes (UTF-16 corruption)."""
import os
import sys

root = sys.argv[1] if len(sys.argv) > 1 else '.'
root = os.path.abspath(root)

hits = []
for dirpath, dirnames, filenames in os.walk(root):
    # Skip noise
    dirnames[:] = [d for d in dirnames if d not in ('__pycache__', '.git', '.venv', 'venv', 'env', 'node_modules')]
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        path = os.path.join(dirpath, fn)
        try:
            with open(path, 'rb') as f:
                data = f.read()
        except OSError as e:
            print(f'  [error reading] {path}: {e}')
            continue
        if b'\x00' in data:
            hits.append(path)
            print(f'NULL BYTES: {path}')

print()
print(f'Scanned under: {root}')
print(f'Corrupt files found: {len(hits)}')