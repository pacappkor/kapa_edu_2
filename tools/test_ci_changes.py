# SPDX-License-Identifier: GPL-3.0-only
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import ci_changes
from ci_changes import classify


class ChangeSelectionTests(unittest.TestCase):
    def test_readme(self):
        self.assertEqual(classify(['README.md']), dict(validate=True, tests=False, build=False))

    def test_content(self):
        self.assertEqual(classify(['appraisal_practice/37/01.tex']), dict(validate=True, tests=False, build=False))

    def test_tools_and_workflow(self):
        for path in ('tools/build.py', '.github/workflows/ci.yml', 'unknown.file'):
            self.assertTrue(all(classify([path]).values()))

    def test_latex(self):
        self.assertEqual(classify(['latex/kapa-exam.sty']), dict(validate=False, tests=False, build=True))

    def test_force_all(self):
        self.assertTrue(all(classify(['README.md'], all_checks=True).values()))

    def test_rename_tool_to_document(self):
        # Exercise main's actual git command, not just a hand-built path list.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root)

            git('init', '-q')
            git('config', 'user.email', 'test@example.invalid')
            git('config', 'user.name', 'CI test')
            git('config', 'diff.renames', 'true')
            (root / 'tools').mkdir()
            (root / 'tools/build.py').write_text('print("build")' + chr(10))
            git('add', '.')
            git('commit', '-qm', 'base')
            base = git('rev-parse', 'HEAD').decode().strip()
            (root / 'docs').mkdir()
            git('mv', 'tools/build.py', 'docs/build.md')
            git('commit', '-qm', 'rename')
            output = root / 'output'
            with patch.object(ci_changes, 'ROOT', root), patch.dict(os.environ, {
                'CI_EVENT': 'pull_request', 'CI_BASE': base,
                'GITHUB_OUTPUT': str(output),
                'GITHUB_STEP_SUMMARY': str(root / 'summary'),
            }):
                ci_changes.main()
            flags = dict(line.split('=') for line in output.read_text().splitlines())
            self.assertEqual(flags, dict.fromkeys(ci_changes.GROUPS, 'true'))
            self.assertEqual(flags['tests'], 'true')
            self.assertEqual(flags['build'], 'true')

    def test_missing_base_selects_all(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            for event in ('push', 'pull_request'):
                with self.subTest(event=event):
                    output = root / f'{event}-output'
                    with patch.object(ci_changes, 'ROOT', root), patch.dict(os.environ, {
                        'CI_EVENT': event, 'CI_BASE': 'f' * 40, 'CI_BEFORE': 'f' * 40,
                        'GITHUB_OUTPUT': str(output),
                        'GITHUB_STEP_SUMMARY': str(root / 'summary'),
                    }):
                        ci_changes.main()
                    flags = dict(line.split('=') for line in output.read_text().splitlines())
                    self.assertEqual(flags, dict.fromkeys(ci_changes.GROUPS, 'true'))
