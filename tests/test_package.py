"""Static package checks; not an LLM quality benchmark."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        cls.cases = json.loads((ROOT / 'examples/cases.json').read_text(encoding='utf-8'))

    def test_frontmatter(self):
        self.assertTrue(self.skill.startswith('---\n'))
        header, body = self.skill[4:].split('\n---\n', 1)
        self.assertIn('name: humanizer-ko', header)
        self.assertIn('license: MIT', header)
        match = re.search(r'^description: (.+)$', header, re.M)
        assert match is not None, 'Missing description'
        description = match.group(1)
        self.assertLessEqual(len(description), 60)
        self.assertTrue(body.strip())

    def test_25_patterns(self):
        ids = re.findall(r'^### (\d+)\.', self.skill, re.M)
        self.assertEqual(ids, [str(i) for i in range(1, 26)])

    def test_license(self):
        license_text = (ROOT / 'LICENSE').read_text(encoding='utf-8')
        for required in ['MIT License', 'Copyright (c) 2025 Siqi Chen',
                         'Permission is hereby granted', 'THE SOFTWARE IS PROVIDED "AS IS"']:
            self.assertIn(required, license_text)
        notice = (ROOT / 'NOTICE.md').read_text(encoding='utf-8')
        self.assertIn('9862685f575c65a8247f90369951df1b3416e3d6', notice)
        self.assertIn('Copyright (c) 2026 simkoon', notice)

    def test_safeguards_documented(self):
        for required in ['불확실성', '역할 범위', '실행하지 않는다', '직접 인용',
                         '검토만', '높임', '발명하지 않는다', 'AI 탐지기 회피']:
            with self.subTest(required=required):
                self.assertIn(required, self.skill)

    def test_reference_cases(self):
        self.assertEqual(len(self.cases), 16)
        self.assertEqual(len({c['id'] for c in self.cases}), len(self.cases))
        for c in self.cases:
            with self.subTest(case=c['id']):
                self.assertTrue(c['input'])
                self.assertTrue(c['reference'])
                self.assertTrue(c['criterion'])
                for token in c['preserve']:
                    self.assertIn(token, c['reference'])
                for token in c['avoid']:
                    self.assertNotIn(token, c['reference'])
                # Protected code, URLs and numeric values must survive in fixtures.
                pattern = r'```[\s\S]*?```|`[^`\n]+`|https?://\S+|\d+(?:\.\d+)?'
                self.assertEqual(re.findall(pattern, c['input']),
                                 re.findall(pattern, c['reference']))

    def test_v02_minimal_edit_contract(self):
        self.assertIn('version: "0.2.0"', self.skill)
        self.assertEqual(self.skill.count('- 근거:'), 25)
        for text in ['최소 수정', '되돌린다', '탐지기 점수', '열거·삽입·대조']:
            self.assertIn(text, self.skill)
        cases = json.loads((ROOT / 'examples/minimal-edit.json').read_text(encoding='utf-8'))
        self.assertEqual(len(cases), 8)
        self.assertEqual(len({c['id'] for c in cases}), 8)
        for case in cases:
            with self.subTest(case=case['id']):
                self.assertTrue(case['criterion'])
                self.assertTrue(case['reference'])
                if case.get('unchanged'):
                    self.assertEqual(case['input'], case['reference'])
        self.assertEqual(sum(bool(c.get('unchanged')) for c in cases), 6)

    def test_local_markdown_links(self):
        for doc in ROOT.glob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
                if '://' not in link and not link.startswith('#'):
                    with self.subTest(doc=doc.name, link=link):
                        self.assertTrue((doc.parent / link.split('#')[0]).exists())

    def test_no_machine_local_paths(self):
        for doc in [ROOT / 'SKILL.md', ROOT / 'README.md', ROOT / 'NOTICE.md']:
            text = doc.read_text(encoding='utf-8')
            self.assertNotIn('/Users/', text)
            self.assertNotIn('/home/', text)


if __name__ == '__main__':
    unittest.main()
