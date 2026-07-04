#!/usr/bin/env python3
"""Tests for check_css_refs.py (R2.3)."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_css_refs as lint  # noqa: E402


class ExtractClassesTest(unittest.TestCase):
    def test_extracts_from_selectors_only(self):
        css = (
            ".alpha { color: red; }\n"
            ".beta .gamma { gap: 0.5rem; }\n"          # 0.5 must NOT become a class
            ".delta:hover, .delta::before { top: .3s; }\n"  # pseudos stripped; .3s ignored
            "@media (min-width: 900px) { .epsilon[hidden] { display: none; } }\n"
        )
        self.assertEqual(
            lint.extract_class_selectors(css),
            {"alpha", "beta", "gamma", "delta", "epsilon"},
        )

    def test_ignores_comment_bodies(self):
        css = "/* .commented is not a real selector */\n.real { color: red; }\n"
        self.assertEqual(lint.extract_class_selectors(css), {"real"})


class ReferenceTest(unittest.TestCase):
    def test_substring_is_not_a_reference(self):
        # `.btn` must not be counted as referenced by `btn-primary`.
        self.assertFalse(lint.is_referenced("btn", 'class="btn-primary"'))
        self.assertTrue(lint.is_referenced("btn", 'class="btn primary"'))

    def test_hyphenated_class_referenced(self):
        self.assertTrue(lint.is_referenced("graph-legend", "classList.add('graph-legend')"))


class RunTest(unittest.TestCase):
    def _repo(self, css: str, template: str = "", js: str = "", allow: str | None = None) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "assets" / "css").mkdir(parents=True)
        (root / "layouts").mkdir(parents=True)
        (root / "assets" / "js").mkdir(parents=True)
        (root / "content").mkdir(parents=True)
        (root / "assets" / "css" / "main.css").write_text(css, encoding="utf-8")
        if template:
            (root / "layouts" / "x.html").write_text(template, encoding="utf-8")
        if js:
            (root / "assets" / "js" / "x.js").write_text(js, encoding="utf-8")
        if allow is not None:
            (root / "tools").mkdir(parents=True, exist_ok=True)
            (root / "tools" / "css-refs-allowlist.txt").write_text(allow, encoding="utf-8")
        return root

    def test_dead_class_flagged(self):
        root = self._repo(".used { a: 1; }\n.dead { b: 2; }\n", template='<div class="used">')
        try:
            rc, errors = lint.run(root)
            self.assertEqual(rc, 1)
            self.assertTrue(any("dead" in e for e in errors))
            self.assertFalse(any("used" in e for e in errors))
        finally:
            shutil.rmtree(root)

    def test_class_referenced_in_js_is_live(self):
        root = self._repo(".spin { a: 1; }\n", js="el.classList.add('spin')")
        try:
            self.assertEqual(lint.run(root), (0, []))
        finally:
            shutil.rmtree(root)

    def test_allowlist_suppresses(self):
        root = self._repo(".poem-audio-pill { a: 1; }\n", allow="poem-audio-pill\n")
        try:
            self.assertEqual(lint.run(root), (0, []))
        finally:
            shutil.rmtree(root)

    def test_hugo_interpolated_prefix_counts_as_reference(self):
        # class="stage-{{ .growth_stage }}" constructs stage-budding at render.
        root = self._repo(".stage-budding { a: 1; }\n",
                          template='<div class="stage-{{ .growth_stage }}">')
        try:
            self.assertEqual(lint.run(root), (0, []))
        finally:
            shutil.rmtree(root)

    def test_printf_interpolated_prefix_counts_as_reference(self):
        root = self._repo(".type-badge--music { a: 1; }\n",
                          template='{{ printf "type-badge--%s" $medium }}')
        try:
            self.assertEqual(lint.run(root), (0, []))
        finally:
            shutil.rmtree(root)

    def test_unrelated_prefix_still_flags(self):
        # A dynamic site for `stage-` must NOT rescue an unrelated `widget-dead`.
        root = self._repo(".stage-budding { a: 1; }\n.widget-dead { b: 2; }\n",
                          template='<div class="stage-{{ .x }}">')
        try:
            rc, errors = lint.run(root)
            self.assertEqual(rc, 1)
            self.assertTrue(any("widget-dead" in e for e in errors))
            self.assertFalse(any("stage-budding" in e for e in errors))
        finally:
            shutil.rmtree(root)


class RealRepoTest(unittest.TestCase):
    def test_repo_has_no_unallowlisted_dead_classes(self):
        repo_root = Path(__file__).resolve().parent.parent
        rc, errors = lint.run(repo_root)
        self.assertEqual((rc, errors), (0, []),
                         msg=f"dead CSS classes (add to allowlist or delete): {errors}")


if __name__ == "__main__":
    unittest.main()
