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
        rc, _ = mod.run(self.repo.root)
        self.assertEqual(rc, 1)

    def test_servings_float_string(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('servings: 4', 'servings: 1.5'))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

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
        rc, _ = mod.run(self.repo.root)
        self.assertEqual(rc, 1)

    def test_zero_padded_minutes_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace("servings: 4", "servings: 4\nprep_minutes: 010"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("zero-padded" in e for e in errs), errs)

    def test_zero_padded_servings_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace("servings: 4", "servings: 08"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("zero-padded" in e for e in errs), errs)

    def test_zero_padded_qty_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace("{ qty: 2, unit: tbsp", "{ qty: 08, unit: tbsp"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("zero-padded" in e for e in errs), errs)

    def test_underscore_and_inf_rejected(self):
        for bad in ("1_0", "inf", "nan"):
            with self.subTest(bad=bad):
                self.repo.write("content/recipes/ex/index.md",
                                VALID.replace("servings: 4", f"servings: {bad}"))
                rc, errs = mod.run(self.repo.root)
                self.assertEqual(rc, 1, f"{bad} should be rejected")

    def test_zero_qty_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace("{ qty: 2, unit: tbsp", "{ qty: 0, unit: tbsp"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("qty" in e for e in errs), errs)

    def test_explicit_null_item_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('item: "olive oil"', "item: null"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("missing 'item'" in e for e in errs), errs)

    def test_explicit_null_source_name_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('{ name: "Example", url: "https://example.com/x" }',
                                      '{ name: null, url: "https://example.com/x" }'))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("missing 'name'" in e for e in errs), errs)

    # --- Fix round 1: the padded-numeric scan must be frontmatter-scoped and
    # value-positional, and _absent must know every YAML null spelling. ---

    def test_body_line_with_padded_key_ignored(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID + "\nservings: 010\n")
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_body_prose_with_qty_substring_ignored(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID + "\nEarlier drafts said qty: 08 which was a typo.\n")
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_body_fenced_yaml_block_ignored(self):
        doc = VALID + (
            "\n```yaml\n"
            "servings: 010\n"
            "prep_minutes: 08\n"
            "ingredients:\n"
            "  - { qty: 08, unit: tbsp, item: \"oil\" }\n"
            "```\n"
        )
        self.repo.write("content/recipes/ex/index.md", doc)
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_quoted_value_containing_padded_qty_ignored(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('note: "to taste"',
                                      'note: "was qty: 08 in the source"'))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_null_spellings_reject_missing_item(self):
        for spelling in ("~", "Null", "NULL", "null"):
            with self.subTest(spelling=spelling):
                self.repo.write("content/recipes/ex/index.md",
                                VALID.replace('item: "olive oil"',
                                              f"item: {spelling}"))
                rc, errs = mod.run(self.repo.root)
                self.assertEqual(rc, 1, f"item: {spelling} should be rejected")
                self.assertTrue(any("missing 'item'" in e for e in errs), errs)

    def test_null_spellings_accepted_for_qty(self):
        for spelling in ("~", "Null", "NULL", "null"):
            with self.subTest(spelling=spelling):
                self.repo.write("content/recipes/ex/index.md",
                                VALID.replace("{ qty: 2, unit: tbsp",
                                              f"{{ qty: {spelling}, unit: tbsp"))
                rc, errs = mod.run(self.repo.root)
                self.assertEqual(rc, 0, f"qty: {spelling} is legal YAML null: {errs}")


if __name__ == "__main__":
    unittest.main()
