#!/usr/bin/env python3
"""Tests for check_spacing_tokens.py (R6.1)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_spacing_tokens as lint  # noqa: E402
from test_helpers import TempRepo  # noqa: E402


class FindViolationsTest(unittest.TestCase):
    def test_bare_rem_in_gap_flagged(self):
        v = lint.find_violations(".a { gap: 0.5rem; }\n")
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0][1], "gap")
        self.assertEqual(v[0][2], "0.5")

    def test_tokenized_value_ok(self):
        self.assertEqual(lint.find_violations(".a { gap: var(--space-xs); }\n"), [])

    def test_allowlisted_micro_nudge_ok(self):
        # 0.02/0.05/0.1/0.125/0.15 stay literal
        for v in ("0.02", "0.05", "0.1", "0.125", "0.15"):
            self.assertEqual(
                lint.find_violations(f".a {{ padding: {v}rem; }}\n"), [],
                msg=f"{v}rem should be allowlisted",
            )

    def test_point_two_is_not_allowlisted(self):
        # 0.2 snaps to --space-3xs; a bare 0.2rem is a violation
        self.assertEqual(len(lint.find_violations(".a { margin: 0.2rem; }\n")), 1)

    def test_shorthand_flags_each_bare_component(self):
        # one tokenized + one bare → one violation for the bare one
        v = lint.find_violations(".a { padding: var(--space-xs) 1rem; }\n")
        self.assertEqual([(x[1], x[2]) for x in v], [("padding", "1")])

    def test_calc_negative_token_ok(self):
        css = ".a { margin: 0 calc(-1 * var(--space-2xs)); }\n"
        self.assertEqual(lint.find_violations(css), [])

    def test_out_of_scope_property_ignored(self):
        # font-size / border-radius / width etc. are not spacing rhythm
        css = ".a { font-size: 0.85rem; border-radius: 0.5rem; width: 20rem; }\n"
        self.assertEqual(lint.find_violations(css), [])

    def test_per_side_props_in_scope(self):
        for prop in ("padding-top", "margin-left", "row-gap", "column-gap"):
            css = f".a {{ {prop}: 0.7rem; }}\n"
            self.assertEqual(len(lint.find_violations(css)), 1, msg=prop)

    def test_zero_and_nonrem_ignored(self):
        css = ".a { margin: 0 auto; padding: 8px 50%; gap: 2ch; }\n"
        self.assertEqual(lint.find_violations(css), [])

    def test_comment_bodies_ignored(self):
        css = "/* gap: 0.5rem in prose */\n.a { color: red; }\n"
        self.assertEqual(lint.find_violations(css), [])


class RunTest(unittest.TestCase):
    def _repo(self, css: str) -> Path:
        self.repo = TempRepo()
        self.repo.write("assets/css/main.css", css)
        return self.repo.root

    def tearDown(self):
        if getattr(self, "repo", None):
            self.repo.cleanup()

    def test_run_green_on_tokenized_css(self):
        root = self._repo(".a { gap: var(--space-lg); padding: 0.1rem; }\n")
        rc, errs = lint.run(root)
        self.assertEqual(rc, 0)
        self.assertEqual(errs, [])

    def test_run_red_reports_lineno(self):
        root = self._repo(".a { gap: var(--space-lg); }\n.b { margin: 0.5rem; }\n")
        rc, errs = lint.run(root)
        self.assertEqual(rc, 1)
        self.assertEqual(len(errs), 1)
        self.assertIn(":2:", errs[0])
        self.assertIn("0.5rem", errs[0])

    def test_run_missing_css(self):
        root = TempRepo().root
        rc, errs = lint.run(root)
        self.assertEqual(rc, 1)
        self.assertTrue(errs)


if __name__ == "__main__":
    unittest.main()
