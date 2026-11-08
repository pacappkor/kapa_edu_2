# SPDX-License-Identifier: GPL-3.0-only
"""Run the actual CI discovery script against package and non-package fixtures."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('ci_tests.sh')


class DiscoveryTests(unittest.TestCase):
    def run_fixture(self, source):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / 'tools' / 'pipeline'
            nested.mkdir(parents=True)
            (nested / 'test_nested.py').write_text(source, encoding='utf-8')
            return subprocess.run(
                ['bash', str(SCRIPT)], cwd=root, capture_output=True, text=True,
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})

    def run_package_fixture(self, broken=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'tools' / 'pkg'
            nested = package / 'nested'
            nested.mkdir(parents=True)
            # Exercise walking through more than one package directory.
            (root / 'tools' / '__init__.py').write_text('', encoding='utf-8')
            for folder in (package, nested):
                (folder / '__init__.py').write_text('', encoding='utf-8')
            (package / 'helper.py').write_text('VALUE = 42\n', encoding='utf-8')
            source = ('from ..helper import VALUE\nimport unittest\n'
                      'class Package(unittest.TestCase):\n'
                      '    def test_package_marker(self):\n'
                      '        self.assertEqual(VALUE, 42)\n')
            if broken:
                source = 'from .missing_helper import VALUE\n'
            (nested / 'test_relative.py').write_text(source, encoding='utf-8')
            # A test in the parent package must not rediscover the nested file.
            (package / 'test_parent.py').write_text(
                'import unittest\nclass Parent(unittest.TestCase):\n'
                '    def test_parent_marker(self):\n        self.assertTrue(True)\n',
                encoding='utf-8')
            return subprocess.run(
                ['bash', str(SCRIPT)], cwd=root, capture_output=True, text=True,
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})

    def test_same_named_parent_and_package_tests_run_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / 'tools' / 'pipeline'
            package = parent / 'pkg'
            package.mkdir(parents=True)
            (package / '__init__.py').write_text('', encoding='utf-8')
            for folder in (parent, package):
                (folder / 'test_same.py').write_text(
                    'from pathlib import Path\nimport unittest\n'
                    'class Same(unittest.TestCase):\n'
                    '    def test_marker(self):\n'
                    '        marker = Path(__file__).with_suffix(".marker")\n'
                    '        with marker.open("a", encoding="utf-8") as stream:\n'
                    '            stream.write("run\\n")\n', encoding='utf-8')
            result = subprocess.run(
                ['bash', str(SCRIPT)], cwd=root, capture_output=True, text=True,
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.assertEqual(result.returncode, 0, result.stderr)
            for folder in (parent, package):
                self.assertEqual(
                    (folder / 'test_same.marker').read_text(encoding='utf-8'),
                    'run\n', result.stderr)

    def test_namespace_parent_relative_and_sibling_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'tools' / 'pkg'
            package.mkdir(parents=True)
            (package / '__init__.py').write_text('', encoding='utf-8')
            (root / 'tools' / 'helper.py').write_text('VALUE = 42\n', encoding='utf-8')
            (package / 'sibling.py').write_text('VALUE = 43\n', encoding='utf-8')
            (package / 'test_namespace.py').write_text(
                'from ..helper import VALUE\nimport sibling\nimport unittest\n'
                'class Namespace(unittest.TestCase):\n'
                '    def test_values(self):\n'
                '        self.assertEqual((VALUE, sibling.VALUE), (42, 43))\n',
                encoding='utf-8')
            result = subprocess.run(
                ['bash', str(SCRIPT)], cwd=root, capture_output=True, text=True,
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('tools.pkg.test_namespace', result.stderr)

    def test_package_relative_import_runs_once(self):
        result = self.run_package_fixture()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr.count('test_package_marker ('), 1, result.stderr)
        self.assertEqual(result.stderr.count('test_parent_marker ('), 1, result.stderr)
        self.assertIn('tools.pkg.nested.test_relative', result.stderr)

    def test_package_import_failure_is_fatal(self):
        result = self.run_package_fixture(broken=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing_helper', result.stderr)

    def test_nested_test_runs_without_package(self):
        result = self.run_fixture(
            'import unittest\nclass Nested(unittest.TestCase):\n'
            '    def test_nested_marker(self):\n        self.assertTrue(True)\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('test_nested_marker', result.stderr)
        self.assertIn('Ran 1 test', result.stderr)

    def test_nested_test_failure_is_fatal(self):
        result = self.run_fixture(
            'import unittest\nclass Nested(unittest.TestCase):\n'
            '    def test_failure(self):\n        self.fail("nested failure")\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('nested failure', result.stderr)

    def test_nested_import_failure_is_fatal(self):
        result = self.run_fixture('raise ImportError("nested import failure")\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('nested import failure', result.stderr)


if __name__ == '__main__':
    unittest.main()
