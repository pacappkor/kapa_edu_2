#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""한글 LaTeX 사전 검사 자체 테스트: python tools/test_build.py (TeX 불필요)."""
import contextlib
import io
import pathlib
import subprocess
import unittest
from unittest.mock import patch
import tempfile

if __package__:
    from . import build
else:
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
        self.targets = build.preflight_files()
        self.stack.enter_context(patch.object(build, 'preflight_files', return_value=self.targets))
        self.stack.enter_context(patch.object(build, 'ROOT', pathlib.Path('/work/kapa_edu')))
        self.which = self.stack.enter_context(patch.object(build.shutil, 'which', return_value='kpsewhich'))
        self.run = self.stack.enter_context(patch.object(
            build.subprocess, 'run', side_effect=lambda cmd, **kw: subprocess.CompletedProcess(
                cmd, 0, '\n'.join('/texlive/' + name for name in cmd[1:]), '')))

    def test_all_resources_found(self):
        self.assertTrue(build.preflight())
        self.run.assert_called_once_with(['kpsewhich', *self.targets], capture_output=True,
                                         text=True, encoding='utf-8', errors='replace', timeout=10)
        self.assertIn(f'{len(self.targets)}개 파일 확인', self.out.getvalue())
        self.assertEqual(self.err.getvalue(), '')

    def test_each_missing_resource_and_empty_output(self):
        for name in self.targets:
            for code in (0, 1):
                with self.subTest(name=name, returncode=code):
                    self.err.seek(0)
                    self.err.truncate()
                    self.run.side_effect = lambda cmd, **kw: subprocess.CompletedProcess(
                        cmd, code if name in cmd[1:] else 0,
                        '\n'.join('/texlive/' + item for item in cmd[1:] if item != name), '')
                    self.assertFalse(build.preflight())
                    self.assertIn(name, self.err.getvalue())
                    self.assertIn('개발 환경 (한글 LaTeX)', self.err.getvalue())
                    self.assertIn('tlmgr install', self.err.getvalue())
                    self.assertIn('scheme-full', self.err.getvalue())

    def test_batch_falls_back_to_individual_probes(self):
        self.run.side_effect = lambda cmd, **kw: subprocess.CompletedProcess(
            cmd, 0, '/texlive/' + cmd[1], '')
        self.assertTrue(build.preflight())
        self.assertEqual([call.args[0] for call in self.run.call_args_list],
                         [['kpsewhich', *self.targets]] +
                         [['kpsewhich', name] for name in self.targets[1:]])
        self.assertTrue(all(call.kwargs['timeout'] == 10 for call in self.run.call_args_list))

    def test_missing_resource_package_hints(self):
        self.run.side_effect = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, '', '')
        self.assertFalse(build.preflight())
        expected = {
            'UnBatang.ttf': 'unfonts-core', 'UnDotum.ttf': 'unfonts-core',
            'batang.ttf': 'baekmuk', 'lmroman10-regular.otf': 'lm', 'kotex.sty': 'kotex-utf',
            'iftex.sty': 'iftex', 'fontspec.sty': 'fontspec',
            'newunicodechar.sty': 'newunicodechar', 'amsmath.sty': 'amsmath',
            'amssymb.sty': 'amsfonts', 'graphicx.sty': 'graphics', 'import.sty': 'import',
            'array.sty': 'tools', 'tabularx.sty': 'tools', 'multirow.sty': 'multirow',
            'makecell.sty': 'makecell', 'longtable.sty': 'tools', 'booktabs.sty': 'booktabs',
            'enumitem.sty': 'enumitem', 'tikz.sty': 'pgf', 'pgfplots.sty': 'pgfplots',
            'xcolor.sty': 'xcolor', 'tcolorbox.sty': 'tcolorbox', 'ulem.sty': 'ulem',
            'needspace.sty': 'needspace',
        }
        for name, package in expected.items():
            with self.subTest(name=name):
                self.assertIn(f'{name} → tlmgr install {package}', self.err.getvalue())
        self.assertNotIn('<package>', self.err.getvalue())

    def test_unknown_resource_lookup_hint(self):
        for name in ('unknown.sty', 'AZaz09._-'):
            with self.subTest(name=name), patch.object(build, 'preflight_files', return_value=(name,)):
                self.err.seek(0)
                self.err.truncate()
                self.run.side_effect = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, '', '')
                self.assertFalse(build.preflight())
                self.assertIn(f'{name} → tlmgr search --global --file /{name}.', self.err.getvalue())
                self.assertNotIn('<package>', self.err.getvalue())

    def test_unsafe_resource_lookup_is_instruction_only(self):
        for name in ('a+b.sty', 'unknown file.sty', '$HOME.sty', '`whoami`.sty',
                     'unknown(1).sty', '한글.sty', 'line' + chr(10) + 'break.sty'):
            with self.subTest(name=name), patch.object(build, 'preflight_files', return_value=(name,)):
                self.err.seek(0)
                self.err.truncate()
                self.run.side_effect = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, '', '')
                self.assertFalse(build.preflight())
                message = self.err.getvalue()
                self.assertIn(repr(name), message)
                self.assertIn('이 파일 이름으로 tlmgr search --global --file 을 사용해 제공 패키지를 찾으세요', message)
                self.assertNotIn('→ tlmgr search', message)
                self.assertNotIn('tlmgr search --global --file /', message)
                self.assertNotIn('tlmgr search --global --file "', message)

    def test_missing_kpsewhich(self):
        self.which.return_value = None
        self.assertFalse(build.preflight())
        self.run.assert_not_called()
        self.assertIn('README.md', self.err.getvalue())

    def test_probe_errors(self):
        for error in (OSError('cannot execute'), subprocess.TimeoutExpired('kpsewhich', 10)):
            with self.subTest(error=error):
                self.err.seek(0)
                self.err.truncate()
                self.run.side_effect = error
                self.assertFalse(build.preflight())
                self.assertIn('README.md', self.err.getvalue())

    def test_path_warnings_do_not_fail(self):
        for path in ('/work/한글', '/work/with space', '/work/café'):
            with self.subTest(path=path), patch.object(build, 'ROOT', pathlib.Path(path)):
                self.err.seek(0)
                self.err.truncate()
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


class TargetListTests(unittest.TestCase):
    def test_style_dependencies_are_parsed_at_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            (root / 'latex').mkdir()
            style = root / 'latex' / 'kapa-exam.sty'
            style.write_text(r"""
% \RequirePackage{ignored}
\\% \RequirePackage{ignored2}
\% \RequirePackage{kept}
\RequirePackage [most] {tcolorbox, pgfplots}
\usepackage
 [option=value]
 {alpha, beta}
\RequirePackage{alpha} % duplicate
\RequirePackage[label={a]b}]{braced}
\usepackageX{notpkg}
""", encoding='utf-8')
            with patch.object(build, 'ROOT', root):
                self.assertEqual(build.preflight_files(), build.PREFLIGHT_FILES +
                                 ('kept.sty', 'tcolorbox.sty', 'pgfplots.sty', 'alpha.sty', 'beta.sty', 'braced.sty'))
                style.write_text(r'\usepackage{added}', encoding='utf-8')
                self.assertEqual(build.preflight_files(), build.PREFLIGHT_FILES + ('added.sty',))

    def test_tex_token_boundaries(self):
        cases = (
            (r'\\% \RequirePackage{ignored}', ()),
            (r'\% \RequirePackage{kept}', ('kept',)),
            (r'\\RequirePackage{optional}', ()),
            (r'\string\RequirePackage{example}', ()),
            (r'\noexpand\RequirePackage{example}', ()),
            (r'\detokenize\RequirePackage{example}', ()),
            (r'\detokenize{\RequirePackage{example}\usepackage{other}}', ()),
            (r'\RequirePackage[label={a]b}]{braced}', ('braced',)),
            (r'\RequirePackage[key=\}]{real}', ('real',)),
            (r'\RequirePackage[label={a\}b}]{foo}', ('foo',)),
            (r'\RequirePackage[key=\{]{real}', ('real',)),
            (r'\usepackageX{notpkg}', ()),
            (r'\RequirePackageExtra{notpkg}', ()),
            (r'\RequirePackageWithOptions{foo}', ('foo',)),
            (r'\RequirePackageWithOptions[option]{foo}', ('foo',)),
            (r'\RequirePackageWithOptionsX{bar}', ()),
            ('\\usepackage % comment\n [key=value]\n {alpha, beta}', ('alpha, beta',)),
            ('\\usepackage{al% comment\npha}', ('alpha',)),
            (r'\usepackage{a\}b,c}', (r'a\}b,c',)),
            (r'\usepackage[unfinished', ()),
            (r'\usepackage{unfinished', ()),
        )
        for style, expected in cases:
            with self.subTest(style=style):
                self.assertEqual(tuple(build._package_groups(style)), expected)

    def test_real_style_includes_direct_dependencies(self):
        # 스타일을 독립적으로 대조한 전체 목록: 순서·누락·중복까지 고정한다.
        expected = (
            'UnBatang.ttf', 'UnDotum.ttf', 'batang.ttf', 'lmroman10-regular.otf',
            'kotex.sty', 'iftex.sty', 'fontspec.sty', 'newunicodechar.sty',
            'amsmath.sty', 'amssymb.sty', 'graphicx.sty', 'import.sty',
            'array.sty', 'tabularx.sty', 'multirow.sty', 'makecell.sty',
            'longtable.sty', 'booktabs.sty', 'enumitem.sty', 'tikz.sty',
            'pgfplots.sty', 'xcolor.sty', 'tcolorbox.sty', 'ulem.sty', 'needspace.sty',
        )
        self.assertEqual(build.preflight_files(), expected)


if __name__ == '__main__':
    unittest.main()
