#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Select offline CI checks from native git diffs; unknown inputs fail open."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
GROUPS = ('validate', 'tests', 'build')


def classify(paths, all_checks=False):
    flags = dict.fromkeys(GROUPS, all_checks)
    for path in paths:
        if path.startswith(('.github/workflows/', 'tools/')):
            return dict.fromkeys(GROUPS, True)
        if path.endswith('.md'):
            # validate.py combines structure and prose checks in one entry point.
            flags['validate'] = True
        elif path.startswith('latex/'):
            flags['build'] = True
        elif path == 'subjects.json':
            flags['validate'] = True
        elif len(path.split('/')) >= 3 and path.split('/')[1].isdigit():
            # Validators walk every subject/round, including unlisted subjects.
            flags['validate'] = True
        elif path in ('docs/status.json',):
            flags['validate'] = True
        else:
            return dict.fromkeys(GROUPS, True)
    return flags


def main():
    event = os.environ.get('CI_EVENT', '')
    base = os.environ.get('CI_BASE', '')
    before = os.environ.get('CI_BEFORE', '')
    all_checks = event != 'pull_request'
    paths = []
    if event in ('pull_request', 'push'):
        start = base if event == 'pull_request' else before
        if start and set(start) != {'0'}:
            separator = '...' if event == 'pull_request' else '..'
            try:
                subprocess.run(
                    ['git', 'rev-parse', '--verify', '--quiet', f'{start}^{{commit}}'],
                    cwd=ROOT, check=True, capture_output=True)
                result = subprocess.run(
                    ['git', 'diff', '--no-renames', '--name-only', '-z', f'{start}{separator}HEAD'],
                    cwd=ROOT, check=True, capture_output=True)
                paths = result.stdout.decode('utf-8').rstrip('\0').split('\0') if result.stdout else []
            except (OSError, subprocess.CalledProcessError, UnicodeError):
                all_checks = True
        else:
            all_checks = True
    flags = classify(paths, all_checks)
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
        for group, enabled in flags.items():
            output.write(f'{group}={str(enabled).lower()}\n')
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as summary:
        summary.write('## CI check selection\n\n')
        for group, enabled in flags.items():
            summary.write(f'- {group}: {"selected" if enabled else "skipped"}\n')
        summary.write('- whitespace: always selected\n')
    print(flags)


if __name__ == '__main__':
    main()
