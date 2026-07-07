import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_helpers import TempRepo
import check_recipes_fixtures as mod

VALID = """---
title: "Example Recipe One"
date: 2026-07-06
lastmod: 2026-07-06
draft: false
summary: "Dummy."
servings: 4
sources:
  - { name: "Example", url: "https://example.com/x" }
ingredients:
  - { qty: 2, unit: tbsp, item: "olive oil" }
  - { qty: null, unit: null, item: "salt", note: "to taste" }
steps:
  - "Do the thing."
---
Body.
"""


class T(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_valid_passes(self):
        self.repo.write("content/recipes/ex/index.md", VALID)
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_missing_required(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('servings: 4\n', ''))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("servings" in e for e in errs))

    def test_unknown_field(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('servings: 4', 'servings: 4\nbogus: 1'))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("bogus" in e for e in errs))

    def test_ingredient_missing_item(self):
        bad = VALID.replace('{ qty: 2, unit: tbsp, item: "olive oil" }',
                            '{ qty: 2, unit: tbsp }')
        self.repo.write("content/recipes/ex/index.md", bad)
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("item" in e for e in errs))

    def test_servings_non_positive(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('servings: 4', 'servings: 0'))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)

    def test_source_missing_name(self):
        bad = VALID.replace('{ name: "Example", url: "https://example.com/x" }',
                            '{ url: "https://example.com/x" }')
        self.repo.write("content/recipes/ex/index.md", bad)
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("name" in e for e in errs))

    def test_bad_timecode(self):
        bad = VALID.replace('"Do the thing."', '"[99:99] bad marker step."')
        self.repo.write("content/recipes/ex/index.md", bad)
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
