# SPDX-License-Identifier: GPL-3.0-only
"""Offline site generator contracts (no XeLaTeX or MkDocs dependency)."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('exam_site', Path(__file__).with_name('site.py'))
site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(site)


class SiteTests(unittest.TestCase):
    def test_attribution_boundaries(self):
        for rd in range(19, 25):
            self.assertIn('주장하지 않습니다', site.attribution(rd))
            self.assertNotIn('**공공누리 제1유형', site.attribution(rd))
        for rd in range(25, 38):
            self.assertIn('**공공누리 제1유형', site.attribution(rd))
        for rd in (18, 38):
            with self.assertRaises(ValueError):
                site.attribution(rd)

    def test_real_inventory_and_wrapper(self):
        records = site.discover()
        self.assertEqual({r['round'] for r in records}, set(range(19, 38)))
        self.assertEqual(len(records), len({r['path'] for r in records}))
        for rd in range(19, 38):
            selected = [r for r in records if r['round'] == rd]
            groups = [(r['period'], r['subject']) for r in selected]
            transitions = [g for i, g in enumerate(groups) if i == 0 or g != groups[i - 1]]
            self.assertEqual(len(transitions), len(set(transitions)))
        document = site.wrapper(records[:2])
        self.assertIn('\\usepackage[noanswers]{kapa-exam}', document)
        self.assertEqual(document.count('\\subimport'), 2)
        self.assertNotIn(str(site.ROOT), document)
        self.assertTrue(document.endswith('\\end{document}\n'))

    def test_footer_both_exams(self):
        for exam in (1, 2):
            text = site.footer(f'kapa_edu_{exam}', exam, [24, 25])
            self.assertIn('/discussions', text)
            self.assertIn('template=correction.md', text)
            self.assertIn('원본과 대조', text)
            self.assertEqual('공식 모범답안 없음' in text, exam == 2)
            self.assertIn('주장하지 않습니다', text)
            self.assertIn('**공공누리 제1유형', text)

    def test_failed_pdf_not_published_and_stale_removed(self):
        records = site.discover()[:1]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            docs = out / 'site-src'
            (docs / 'pdf').mkdir(parents=True)
            (out / 'paper.pdf').write_bytes(b'stale')
            with patch.object(site, 'OUT', out), patch.object(site, 'DOCS', docs), \
                    patch.object(site.build, 'compile_tex', return_value=(False, ['! failure'], [])):
                result = site.compile_document('paper', records)
            self.assertFalse(result['ok'])
            self.assertFalse((out / 'paper.pdf').exists())
            self.assertEqual(list((docs / 'pdf').iterdir()), [])
            self.assertNotIn('](pdf/', site.result_link(result))
            self.assertIn('조판 실패', site.result_link(result))

    def test_success_pdf_and_glyph_warning(self):
        records = site.discover()[:1]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            docs = out / 'site-src'
            (docs / 'pdf').mkdir(parents=True)
            def compile_fake(tex, cwd):
                tex.with_suffix('.pdf').write_bytes(b'PDF')
                return True, [], ['字']
            with patch.object(site, 'OUT', out), patch.object(site, 'DOCS', docs), \
                    patch.object(site.build, 'compile_tex', side_effect=compile_fake):
                result = site.compile_document('paper', records)
            self.assertEqual((docs / 'pdf/paper.pdf').read_bytes(), b'PDF')
            self.assertIn('글꼴 누락', site.result_link(result))

    def test_answer_rows_and_escaping(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'answers').mkdir()
            (root / 'answers/answers.csv').write_text(
                'round,period,form,subject,number,answer,note\n25,1,A,민법,1,3,a|<b>\n', encoding='utf-8')
            text = site.answer_table(25, root)
            self.assertIn('| 1 | A | 민법 | 1 | 3 | a&#124;&lt;b&gt; |', text)
            with self.assertRaises(ValueError):
                site.answer_table(24, root)


if __name__ == '__main__':
    unittest.main()
