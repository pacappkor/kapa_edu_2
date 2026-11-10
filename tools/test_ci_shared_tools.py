# SPDX-License-Identifier: GPL-3.0-only
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
if __package__:
    from . import ci_shared_tools
else:
    import ci_shared_tools


class SharedToolTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'tools').mkdir()
        self.tool = self.root / 'tools/example.py'
        self.tool.write_bytes(b'original\n')
        manifest = {
            'canonical_owner': 'kapa_edu_1',
            'sha256': {'tools/example.py': hashlib.sha256(self.tool.read_bytes()).hexdigest()},
        }
        (self.root / 'tools/shared_tools.json').write_text(json.dumps(manifest), encoding='utf-8')

    def test_match(self):
        self.assertEqual(ci_shared_tools.check(self.root), [])
        with patch.object(ci_shared_tools, 'ROOT', self.root):
            self.assertEqual(ci_shared_tools.main(), 0)

    def test_mismatch(self):
        self.tool.write_bytes(b'changed\n')
        errors = ci_shared_tools.check(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn('tools/example.py: SHA-256 mismatch', errors[0])
        with patch.object(ci_shared_tools, 'ROOT', self.root):
            self.assertEqual(ci_shared_tools.main(), 1)

    def test_missing(self):
        self.tool.unlink()
        self.assertIn('tools/example.py: cannot read file', ci_shared_tools.check(self.root)[0])

    def test_invalid_manifest(self):
        (self.root / 'tools/shared_tools.json').write_text('{', encoding='utf-8')
        with patch.object(ci_shared_tools, 'ROOT', self.root):
            self.assertEqual(ci_shared_tools.main(), 1)
