"""Tests for check_explorables.py — run with:
   python3 -m unittest tools/test_check_explorables.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_explorables as lint  # noqa: E402


class ExplorablesLinterScaffold(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "content" / "essays").mkdir(parents=True)
        (self.tmp / "assets" / "js" / "explorables").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def test_empty_tree_no_errors(self) -> None:
        errors = lint.lint_explorables(self.tmp)
        self.assertEqual(errors, [])


ESSAY_WIDGET_TRUE_HAS_WIDGET = """\
---
title: "Has widget"
date: 2026-06-12
lastmod: 2026-06-12
draft: false
summary: "x"
tags: []
series: ""
series_order: 0
toc: true
has_sidenotes: false
has_citations: false
has_footnotes: false
has_math: false
has_widgets: true
has_video_sync: false
---

Body. {{< widget id="x" >}}
"""

ESSAY_WIDGET_FALSE_HAS_WIDGET = ESSAY_WIDGET_TRUE_HAS_WIDGET.replace(
    "has_widgets: true", "has_widgets: false"
)

ESSAY_WIDGET_TRUE_NO_WIDGET = ESSAY_WIDGET_TRUE_HAS_WIDGET.replace(
    'Body. {{< widget id="x" >}}', "Body, no widget."
)


class HasWidgetsCoupling(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.essays = self.tmp / "content" / "essays"
        self.essays.mkdir(parents=True)
        (self.tmp / "assets" / "js" / "explorables").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def _write_essay(self, slug: str, body: str) -> None:
        d = self.essays / slug
        d.mkdir()
        (d / "index.md").write_text(body, encoding="utf-8")

    def test_has_widgets_true_with_widget_ok(self) -> None:
        self._write_essay("ok", ESSAY_WIDGET_TRUE_HAS_WIDGET)
        (self.tmp / "assets" / "js" / "explorables" / "ok").mkdir()
        (self.tmp / "assets" / "js" / "explorables" / "ok" / "index.js").write_text(
            'registerWidget("x", () => {});\n', encoding="utf-8"
        )
        errors = lint.lint_explorables(self.tmp)
        # Other rules may add errors later; only check rule-1 cases don't appear.
        self.assertFalse(
            any("has_widgets" in e for e in errors),
            f"unexpected has_widgets error: {errors}",
        )

    def test_has_widgets_false_with_widget_fails(self) -> None:
        self._write_essay("flagged-false", ESSAY_WIDGET_FALSE_HAS_WIDGET)
        errors = lint.lint_explorables(self.tmp)
        self.assertTrue(
            any("flagged-false" in e and "has_widgets" in e and "false" in e for e in errors),
            f"expected has_widgets-false-but-body-has-widget error: {errors}",
        )

    def test_has_widgets_true_no_widget_fails(self) -> None:
        self._write_essay("flagged-true", ESSAY_WIDGET_TRUE_NO_WIDGET)
        errors = lint.lint_explorables(self.tmp)
        self.assertTrue(
            any("flagged-true" in e and "has_widgets" in e and "true" in e for e in errors),
            f"expected has_widgets-true-but-no-widget error: {errors}",
        )


ESSAY_NO_ID = ESSAY_WIDGET_TRUE_HAS_WIDGET.replace(
    'Body. {{< widget id="x" >}}',
    'Body. {{< widget >}}',
)

ESSAY_EMPTY_ID = ESSAY_WIDGET_TRUE_HAS_WIDGET.replace(
    'Body. {{< widget id="x" >}}',
    'Body. {{< widget id="" >}}',
)

ESSAY_WRONG_PARAM = ESSAY_WIDGET_TRUE_HAS_WIDGET.replace(
    'Body. {{< widget id="x" >}}',
    'Body. {{< widget src="x" >}}',
)


class WidgetIdRequired(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.essays = self.tmp / "content" / "essays"
        self.essays.mkdir(parents=True)
        (self.tmp / "assets" / "js" / "explorables").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def _write_essay(self, slug: str, body: str) -> None:
        d = self.essays / slug
        d.mkdir()
        (d / "index.md").write_text(body, encoding="utf-8")

    def test_widget_without_id_fails(self) -> None:
        self._write_essay("no-id", ESSAY_NO_ID)
        errors = lint.lint_explorables(self.tmp)
        self.assertTrue(
            any("no-id" in e and "id" in e for e in errors),
            f"expected missing-id error: {errors}",
        )

    def test_widget_with_empty_id_fails(self) -> None:
        self._write_essay("empty-id", ESSAY_EMPTY_ID)
        errors = lint.lint_explorables(self.tmp)
        self.assertTrue(
            any("empty-id" in e and "id" in e for e in errors),
            f"expected empty-id error: {errors}",
        )

    def test_widget_with_wrong_param_fails(self) -> None:
        self._write_essay("wrong-param", ESSAY_WRONG_PARAM)
        errors = lint.lint_explorables(self.tmp)
        self.assertTrue(
            any("wrong-param" in e and "id" in e for e in errors),
            f"expected wrong-param (no id=) error: {errors}",
        )


ESSAY_DUPLICATE_IDS = ESSAY_WIDGET_TRUE_HAS_WIDGET.replace(
    'Body. {{< widget id="x" >}}',
    'A: {{< widget id="x" >}} B: {{< widget id="x" >}}',
)


class WidgetIdsUniquePerPage(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.essays = self.tmp / "content" / "essays"
        self.essays.mkdir(parents=True)
        (self.tmp / "assets" / "js" / "explorables").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def _write_essay(self, slug: str, body: str) -> None:
        d = self.essays / slug
        d.mkdir()
        (d / "index.md").write_text(body, encoding="utf-8")

    def test_duplicate_ids_in_one_essay_fail(self) -> None:
        self._write_essay("dup", ESSAY_DUPLICATE_IDS)
        errors = lint.lint_explorables(self.tmp)
        self.assertTrue(
            any("dup" in e and "duplicate" in e.lower() and '"x"' in e for e in errors),
            f"expected duplicate-id error: {errors}",
        )


class PerEssayJsExists(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.essays = self.tmp / "content" / "essays"
        self.essays.mkdir(parents=True)
        (self.tmp / "assets" / "js" / "explorables").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def _write_essay(self, slug: str, body: str) -> None:
        d = self.essays / slug
        d.mkdir()
        (d / "index.md").write_text(body, encoding="utf-8")

    def test_missing_per_essay_js_fails(self) -> None:
        self._write_essay("missing-js", ESSAY_WIDGET_TRUE_HAS_WIDGET)
        # do NOT create assets/js/explorables/missing-js/index.js
        errors = lint.lint_explorables(self.tmp)
        self.assertTrue(
            any("missing-js" in e and "index.js" in e for e in errors),
            f"expected missing-js error: {errors}",
        )

    def test_per_essay_js_present_no_error(self) -> None:
        self._write_essay("present-js", ESSAY_WIDGET_TRUE_HAS_WIDGET)
        js_dir = self.tmp / "assets" / "js" / "explorables" / "present-js"
        js_dir.mkdir()
        (js_dir / "index.js").write_text(
            'registerWidget("x", () => {});\n', encoding="utf-8"
        )
        errors = lint.lint_explorables(self.tmp)
        self.assertFalse(
            any("index.js" in e and "present-js" in e for e in errors),
            f"unexpected per-essay-js error: {errors}",
        )


if __name__ == "__main__":
    unittest.main()
