#!/usr/bin/env python3
"""Tests for check_breakpoints.py (R6.2)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_breakpoints as lint  # noqa: E402
from test_helpers import TempRepo  # noqa: E402


class CssCheckTest(unittest.TestCase):
    def test_canonical_ok(self):
        for v in (480, 600, 720, 960, 1100, 1280):
            css = f"@media (max-width: {v}px) {{ .a {{ gap: 0; }} }}\n"
            self.assertEqual(lint.check_css(css), [], msg=str(v))

    def test_min_width_canonical_ok(self):
        for v in (960, 1100, 1280):
            css = f"@media (min-width: {v}px) {{ .a {{ gap: 0; }} }}\n"
            self.assertEqual(lint.check_css(css), [], msg=str(v))

    def test_allowlist_ok(self):
        for v in (800, 900, 1140, 1219):
            css = f"@media (max-width: {v}px) {{ .a {{ gap: 0; }} }}\n"
            self.assertEqual(lint.check_css(css), [], msg=str(v))

    def test_seam_partner_ok(self):
        # 1099 = 1100 - 1 accepted for max-width
        self.assertEqual(
            lint.check_css("@media (max-width: 1099px) { .a { gap: 0; } }\n"), []
        )

    def test_seam_rule_is_max_only(self):
        # min-width:1099 is NOT a valid seam (seam applies to max-width only)
        errs = lint.check_css("@media (min-width: 1099px) { .a { gap: 0; } }\n")
        self.assertEqual(len(errs), 1)

    def test_noncanonical_flagged(self):
        errs = lint.check_css("@media (max-width: 905px) { .a { gap: 0; } }\n")
        self.assertEqual(len(errs), 1)
        self.assertIn("905px", errs[0])

    def test_element_minmax_width_ignored(self):
        # min/max-width as element PROPERTIES are not breakpoints
        css = ".hero { max-width: 640px; min-width: 320px; }\n"
        self.assertEqual(lint.check_css(css), [])

    def test_prefers_query_without_width_ignored(self):
        css = "@media (prefers-color-scheme: dark) { :root { color: red; } }\n"
        self.assertEqual(lint.check_css(css), [])

    def test_combined_query_flags_only_bad_feature(self):
        css = "@media (min-width: 720px) and (max-width: 905px) { .a { gap: 0; } }\n"
        errs = lint.check_css(css)
        self.assertEqual(len(errs), 1)
        self.assertIn("905px", errs[0])

    def test_comment_media_ignored(self):
        css = "/* @media (max-width: 905px) legacy */\n.a { color: red; }\n"
        self.assertEqual(lint.check_css(css), [])


class JsCheckTest(unittest.TestCase):
    def test_breakpoint_const_canonical_ok(self):
        self.assertEqual(
            lint.check_js_text("essay.js", "const RAIL_BREAKPOINT = 1100;\n"), []
        )

    def test_breakpoint_const_noncanonical_flagged(self):
        errs = lint.check_js_text("essay.js", "const RAIL_BREAKPOINT = 1099;\n")
        self.assertEqual(len(errs), 1)
        self.assertIn("1099", errs[0])

    def test_matchmedia_canonical_ok(self):
        self.assertEqual(
            lint.check_js_text("g.js", "matchMedia('(max-width: 720px)')\n"), []
        )

    def test_matchmedia_css_allowlist_value_flagged_in_js(self):
        # 900 is CSS-allowlisted but JS must be strict-canonical
        errs = lint.check_js_text("g.js", "matchMedia('(max-width: 900px)')\n")
        self.assertEqual(len(errs), 1)

    def test_unrelated_numbers_ignored(self):
        js = "const VIEWPORT_PAD = 12;\nconst w = window.innerWidth * 0.8;\n"
        self.assertEqual(lint.check_js_text("c.js", js), [])

    def test_commented_breakpoint_ignored(self):
        js = "// matchMedia('(max-width: 905px)')\nconst x = 1;\n"
        self.assertEqual(lint.check_js_text("c.js", js), [])


class RunTest(unittest.TestCase):
    def setUp(self):
        self.repo = None

    def tearDown(self):
        if self.repo:
            self.repo.cleanup()

    def _repo(self, css="", js_files=None):
        self.repo = TempRepo()
        self.repo.write("assets/css/main.css", css)
        for name, txt in (js_files or {}).items():
            self.repo.write(f"assets/js/{name}", txt)
        return self.repo.root

    def test_run_green(self):
        root = self._repo(
            "@media (max-width: 720px) { .a { gap: 0; } }\n",
            {"essay.js": "const RAIL_BREAKPOINT = 1100;\n"},
        )
        self.assertEqual(lint.run(root), (0, []))

    def test_run_red_css(self):
        root = self._repo("@media (max-width: 905px) { .a { gap: 0; } }\n")
        rc, errs = lint.run(root)
        self.assertEqual(rc, 1)
        self.assertEqual(len(errs), 1)

    def test_run_skips_vendor(self):
        root = self._repo(
            "@media (max-width: 720px) { .a { gap: 0; } }\n",
            {"vendor/d3.js": "matchMedia('(max-width: 905px)')\n"},
        )
        self.assertEqual(lint.run(root), (0, []))

    def test_run_missing_css(self):
        self.repo = TempRepo()
        rc, errs = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(errs)


if __name__ == "__main__":
    unittest.main()
