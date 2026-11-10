# SPDX-License-Identifier: GPL-3.0-only
"""Check shared tool bytes locally; no sibling checkout or network required."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def check(root):
    """Return diagnostics for missing files or SHA-256 mismatches."""
    manifest = json.loads((root / 'tools/shared_tools.json').read_text(encoding='utf-8'))
    errors = []
    for name, expected in manifest['sha256'].items():
        try:
            actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        except OSError as exc:
            errors.append(f'{name}: cannot read file ({exc.strerror})')
            continue
        if actual != expected:
            errors.append(f'{name}: SHA-256 mismatch: expected {expected}, got {actual}')
    return errors


def main():
    try:
        errors = check(ROOT)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f'Shared tool manifest error: {exc}', file=sys.stderr)
        return 1
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        print('Coordinate reviewed updates with the sibling repo; see tools/shared_tools.json.',
              file=sys.stderr)
        return 1
    print('Shared tool hashes match tools/shared_tools.json.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
