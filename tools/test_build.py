#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""한글 LaTeX 사전 검사 자체 테스트: python tools/test_build.py (TeX 불필요)."""
import contextlib
import io
import pathlib
import subprocess
import unittest
from unittest.mock import patch

import build


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.out = io.StringIO()
        self.stack.enter_context(patch.object(self.out, 'reconfigure', create=True))
        self.err = io.StringIO()
        self.stack.enter_context(contextlib.redirect_stdout(self.out))
        self.stack.enter_context(contextlib.redirect_stderr(self.err))
        self.stack.enter_context(patch.object(build, 'ROOT', pathlib.Path('/work/kapa_edu')))
        self.which = self.stack.enter_context(patch.object(build.shutil, 'which', return_value='kpsewhich'))
        self.run = self.stack.enter_context(patch.object(
            build.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '/texlive/file\n', '')))

    def test_all_resources_found(self):
        self.assertTrue(build.preflight())
        self.assertEqual([c.args[0] for c in self.run.call_args_list], [
            ['kpsewhich', 'UnBatang.ttf'], ['kpsewhich', 'UnDotum.ttf'], ['kpsewhich', 'batang.ttf'],
            ['kpsewhich', 'kotex.sty']])
        self.assertEqual(self.err.getvalue(), '')

    def test_each_missing_resource_and_empty_output(self):
        for name in build.PREFLIGHT_FILES:
            for code in (0, 1):
                with self.subTest(name=name, returncode=code):
                    self.err.seek(0)
                    self.err.truncate()
                    self.run.side_effect = lambda cmd, **kw: subprocess.CompletedProcess(
                        cmd, code if cmd[1] == name else 0, '' if cmd[1] == name else '/texlive/file', '')
                    self.assertFalse(build.preflight())
                    self.assertIn(name, self.err.getvalue())
                    self.assertIn('개발 환경 (한글 LaTeX)', self.err.getvalue())

    def test_missing_kpsewhich(self):
        self.which.return_value = None
        self.assertFalse(build.preflight())
        self.run.assert_not_called()
        self.assertIn('README.md', self.err.getvalue())

    def test_probe_errors(self):
        for error in (OSError('cannot execute'), subprocess.TimeoutExpired('kpsewhich', 10)):
            with self.subTest(error=error):
                self.run.side_effect = error
                self.assertFalse(build.preflight())
                self.assertIn('README.md', self.err.getvalue())

    def test_path_warnings_do_not_fail(self):
        for path in ('/work/한글', '/work/with space', '/work/café'):
            with self.subTest(path=path), patch.object(build, 'ROOT', pathlib.Path(path)):
                self.assertTrue(build.preflight())
                self.assertIn('KTUG', self.err.getvalue())

    def test_main_runs_preflight_before_build(self):
        with patch.object(build.sys, 'argv', ['build.py']), \
                patch.object(build, 'preflight', return_value=False) as check, \
                patch.object(build, 'load_subjects') as load:
            self.assertEqual(build.main(), 2)
            check.assert_called_once_with()
            load.assert_not_called()

    def test_skip_preflight_still_checks_xelatex(self):
        self.which.return_value = None
        with patch.object(build.sys, 'argv', ['build.py', '--skip-preflight']), \
                patch.object(build, 'preflight') as check:
            self.assertEqual(build.main(), 2)
            self.which.assert_called_once_with('xelatex')
            check.assert_not_called()

    def test_skip_preflight_compiles(self):
        rd = build.ROOT / 'subject' / '37'
        with patch.object(build.sys, 'argv', ['build.py', '--skip-preflight', 'subject/37']), \
                patch.object(build, 'preflight') as check, \
                patch.object(build, 'load_subjects'), \
                patch.object(build, 'question_dirs', return_value=[rd]), \
                patch.object(build, 'wrapper', return_value='wrapper'), \
                patch.object(build.pathlib.Path, 'mkdir'), \
                patch.object(build.pathlib.Path, 'write_text'), \
                patch.object(build, 'compile_tex', return_value=(True, [], [])) as compile_tex:
            self.assertEqual(build.main(), 0)
            check.assert_not_called()
            compile_tex.assert_called_once()


if __name__ == '__main__':
    unittest.main()
