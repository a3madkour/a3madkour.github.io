# Sub-project E (Explorables) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the explorables runtime + per-essay JS bundle convention + two library widget kinds + 28th linter pair + CSS §49 + a fixture, against the spec at [`docs/superpowers/specs/2026-06-12-sub-project-e-explorables-design.md`](../specs/2026-06-12-sub-project-e-explorables-design.md).

**Architecture:** Per-essay JS entries dynamically registered via a new loop in `layouts/partials/scripts.html`. Library kinds (ReactiveValue, ReactiveChart) live under `assets/js/explorables/lib/`. Imperative `registerWidget(id, fn)` runtime mounts on `DOMContentLoaded` by sweeping `[data-widget-id]`. Hand-rolled SVG charts — no d3, no npm. The `{{< widget >}}` shortcode upgrades from a 1-line stub to a server-rendered no-JS caption + mount target.

**Tech Stack:** Hugo extended 0.162.1, vanilla JS (esbuild via `js.Build`), Python 3 stdlib (linter), bare CSS (no preprocessor).

---

## File Map

**New files**
- `tools/check_explorables.py` — 28th linter (coupling, source-side)
- `tools/test_check_explorables.py` — sibling unit test
- `assets/js/explorables/runtime.js` — `registerWidget` + DOMContentLoaded sweep
- `assets/js/explorables/lib/_base.js` — internal helpers (buildControls, clamp, scale)
- `assets/js/explorables/lib/reactive-value.js` — `ReactiveValue` class
- `assets/js/explorables/lib/reactive-chart.js` — `ReactiveChart` class (hand-rolled SVG)
- `assets/js/explorables/example-explorables/index.js` — per-essay JS for the new fixture
- `assets/js/explorables/example-one/index.js` — per-essay JS for the migrated fixture
- `content/essays/example-explorables/index.md` — new fixture (one essay, three widgets)

**Modified files**
- `layouts/shortcodes/widget.html` — replace 1-line stub with full shortcode
- `layouts/partials/scripts.html` — append per-essay explorables dynamic loop
- `assets/css/main.css` — append §49 + update top-of-file section index
- `content/essays/example-one/index.md` — line 59 `src=` → `id=` (spec §3 option a)
- `tools/check_smoke.py` — add `/essays/example-explorables/` assertions
- `tools/ci-local.sh` — append linter + sibling-test invocations
- `.github/workflows/hugo.yaml` — add linter + sibling-test steps
- `CLAUDE.md` — add 13th row to JS pipeline table
- `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` — flip 8.1 ☐ → ✓ (after merge)

**Memory write (post-merge)**
- `.claude/memory/project_tier_8_1_complete.md` (link from `MEMORY.md`)

---

## Task 1: Linter scaffold — empty repo, no errors

**Files:**
- Create: `tools/check_explorables.py`
- Create: `tools/test_check_explorables.py`

The 28th linter pair starts as a passing no-op so subsequent rules can be added one TDD round at a time.

- [ ] **Step 1: Write the failing test (empty essays dir → no errors)**

```python
# tools/test_check_explorables.py
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to confirm it fails (import error — check_explorables doesn't exist)**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: ImportError / ModuleNotFoundError on `import check_explorables`.

- [ ] **Step 3: Write the minimal linter**

```python
# tools/check_explorables.py
#!/usr/bin/env python3
"""Explorables coupling linter.

Validates the round-trip between essay frontmatter (`has_widgets`), in-body
`{{< widget id="..." >}}` shortcodes, per-essay JS at
`assets/js/explorables/<slug>/index.js`, and `registerWidget("<id>", ...)`
calls in that JS.

Stdlib only.
Exits 0 on all-pass, 1 on any violation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


def lint_explorables(repo_root: Path) -> list[str]:
    """Return list of error strings. Empty list = all good."""
    return []


def run(repo_root: Path) -> tuple[int, list[str]]:
    """Programmatic entry point mirroring sibling linters. Returns (rc, errors)."""
    errors = lint_explorables(repo_root)
    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} explorables issue(s).", file=sys.stderr)
        return rc
    print("OK — explorables coupling validates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to confirm it passes**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: 1 test, PASS.

- [ ] **Step 5: Run the linter itself end-to-end**

Run: `python3 tools/check_explorables.py`
Expected: stdout `OK — explorables coupling validates.`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add tools/check_explorables.py tools/test_check_explorables.py
git commit -m "feat(linter): scaffold check_explorables (28th pair)"
```

---

## Task 2: Linter rule 1 — `has_widgets ↔ shortcode presence` coupling

The `has_widgets` frontmatter value must match whether the essay body actually contains a `{{< widget ... >}}` shortcode. Mirrors `check_math.py`'s `has_math` pattern.

**Files:**
- Modify: `tools/check_explorables.py`
- Modify: `tools/test_check_explorables.py`

- [ ] **Step 1: Add failing tests for rule 1**

Append to `tools/test_check_explorables.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm rule-1 ones fail**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: scaffold test PASS; three `HasWidgetsCoupling` tests FAIL (no rule logic yet).

- [ ] **Step 3: Implement rule 1 in `check_explorables.py`**

Replace `lint_explorables` body with:

```python
WIDGET_SHORTCODE_RE = re.compile(r"\{\{<\s*widget\b[^>]*>\}\}")


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2]
    return text


def _body_has_widget(body: str) -> bool:
    return WIDGET_SHORTCODE_RE.search(body) is not None


def lint_explorables(repo_root: Path) -> list[str]:
    errors: list[str] = []
    essays_dir = repo_root / "content" / "essays"
    if not essays_dir.is_dir():
        return errors

    for d in sorted(essays_dir.iterdir()):
        if not d.is_dir():
            continue
        index = d / "index.md"
        if not index.exists():
            continue
        text = index.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm is None:
            continue
        body = _strip_frontmatter(text)

        slug = d.name
        rel = f"content/essays/{slug}/index.md"
        has_widgets = bool(fm.get("has_widgets", False))
        body_has = _body_has_widget(body)

        # Rule 1: has_widgets ↔ shortcode presence
        if has_widgets and not body_has:
            errors.append(f"{rel}: has_widgets is true but no widget shortcodes found")
        elif not has_widgets and body_has:
            errors.append(f"{rel}: widget shortcodes found but has_widgets is false (or missing)")

    return errors
```

- [ ] **Step 4: Run tests to confirm all pass**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: 4 tests, PASS.

- [ ] **Step 5: Run linter against current repo**

Run: `python3 tools/check_explorables.py`
Expected: must FAIL — `content/essays/example-one/index.md` has `has_widgets: true` + `{{< widget src="example-widget" >}}`. The `src=` shortcode matches the regex (it's still a `{{< widget ... >}}` form), so rule 1 should pass on this essay. But subsequent rules (2: id required) will flag it. For now: rule 1 only — should print OK.

If rule 1 fires anyway, fix the regex.

- [ ] **Step 6: Commit**

```bash
git add tools/check_explorables.py tools/test_check_explorables.py
git commit -m "feat(linter): rule 1 — has_widgets ↔ shortcode coupling"
```

---

## Task 3: Linter rule 2 — widget `id` required + non-empty

Every `{{< widget ... >}}` must have a non-empty `id="..."` parameter.

**Files:**
- Modify: `tools/check_explorables.py`
- Modify: `tools/test_check_explorables.py`

- [ ] **Step 1: Add failing tests for rule 2**

Append to `tools/test_check_explorables.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm rule-2 ones fail**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: rule-1 + scaffold tests PASS; three `WidgetIdRequired` tests FAIL.

- [ ] **Step 3: Implement rule 2**

In `tools/check_explorables.py`, add module-level regex + extend the loop:

```python
# captures the whole shortcode call and (if present) the id="..." value
WIDGET_CALL_RE = re.compile(
    r"\{\{<\s*widget\b([^>]*?)\s*>\}\}"
)
ID_ATTR_RE = re.compile(r'\bid\s*=\s*"([^"]*)"')


def _extract_widget_ids(body: str) -> list[tuple[str, str | None]]:
    """Returns list of (raw_call, id_value or None). None = id attribute absent.
    Empty string = id="" present but empty."""
    out: list[tuple[str, str | None]] = []
    for m in WIDGET_CALL_RE.finditer(body):
        attrs = m.group(1)
        idm = ID_ATTR_RE.search(attrs)
        out.append((m.group(0), idm.group(1) if idm else None))
    return out
```

Then inside the `for d in essays_dir`, after the rule-1 block, add:

```python
        # Rule 2: id required + non-empty on every widget call
        calls = _extract_widget_ids(body)
        for raw, idv in calls:
            if idv is None:
                errors.append(f"{rel}: widget shortcode missing id attribute: {raw}")
            elif idv == "":
                errors.append(f"{rel}: widget shortcode has empty id: {raw}")
```

- [ ] **Step 4: Run tests to confirm all pass**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: 7 tests, PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/check_explorables.py tools/test_check_explorables.py
git commit -m "feat(linter): rule 2 — widget id attribute required + non-empty"
```

---

## Task 4: Linter rule 3 — widget ids unique per page

Within one essay, no two `{{< widget id="..." >}}` shortcodes share the same id.

**Files:**
- Modify: `tools/check_explorables.py`
- Modify: `tools/test_check_explorables.py`

- [ ] **Step 1: Add failing tests**

Append to `tools/test_check_explorables.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm the new one fails**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: dup test FAIL.

- [ ] **Step 3: Implement rule 3**

Inside the same loop, after rule 2:

```python
        # Rule 3: ids unique per page
        seen: set[str] = set()
        for raw, idv in calls:
            if idv and idv in seen:
                errors.append(f"{rel}: duplicate widget id \"{idv}\" on page")
            elif idv:
                seen.add(idv)
```

- [ ] **Step 4: Run tests to confirm all pass**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: 8 tests, PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/check_explorables.py tools/test_check_explorables.py
git commit -m "feat(linter): rule 3 — widget ids unique per page"
```

---

## Task 5: Linter rule 4 — per-essay JS file exists

Every essay with `has_widgets: true` must have a `assets/js/explorables/<slug>/index.js` file.

**Files:**
- Modify: `tools/check_explorables.py`
- Modify: `tools/test_check_explorables.py`

- [ ] **Step 1: Add failing test**

Append to `tools/test_check_explorables.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm missing-js one fails**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: `test_missing_per_essay_js_fails` FAIL.

- [ ] **Step 3: Implement rule 4**

Inside the same loop, after rule 3, add:

```python
        # Rule 4: per-essay JS exists when has_widgets is true
        if has_widgets:
            js_path = repo_root / "assets" / "js" / "explorables" / slug / "index.js"
            if not js_path.exists():
                errors.append(
                    f"{rel}: has_widgets is true but assets/js/explorables/{slug}/index.js is missing"
                )
```

- [ ] **Step 4: Run tests to confirm all pass**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: 10 tests, PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/check_explorables.py tools/test_check_explorables.py
git commit -m "feat(linter): rule 4 — per-essay JS file must exist"
```

---

## Task 6: Linter rules 5 + 6 — `registerWidget` ↔ shortcode id sync

Every widget id in markdown must have a `registerWidget("<id>", ...)` call in the per-essay JS; every `registerWidget` in the per-essay JS must correspond to a shortcode id on the page. Quote-agnostic (single or double).

**Files:**
- Modify: `tools/check_explorables.py`
- Modify: `tools/test_check_explorables.py`

- [ ] **Step 1: Add failing tests**

Append to `tools/test_check_explorables.py`:

```python
class RegisterWidgetIdSync(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.essays = self.tmp / "content" / "essays"
        self.essays.mkdir(parents=True)
        (self.tmp / "assets" / "js" / "explorables").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def _write(self, slug: str, body: str, js: str) -> None:
        d = self.essays / slug
        d.mkdir()
        (d / "index.md").write_text(body, encoding="utf-8")
        js_dir = self.tmp / "assets" / "js" / "explorables" / slug
        js_dir.mkdir()
        (js_dir / "index.js").write_text(js, encoding="utf-8")

    def test_widget_id_without_register_fails(self) -> None:
        self._write("orphan-shortcode", ESSAY_WIDGET_TRUE_HAS_WIDGET, 'console.log("nothing here");\n')
        errors = lint.lint_explorables(self.tmp)
        self.assertTrue(
            any("orphan-shortcode" in e and "registerWidget" in e and '"x"' in e for e in errors),
            f"expected missing-registerWidget error: {errors}",
        )

    def test_register_without_widget_id_fails(self) -> None:
        self._write("orphan-register", ESSAY_WIDGET_TRUE_HAS_WIDGET,
                    'registerWidget("x", () => {});\nregisterWidget("y", () => {});\n')
        errors = lint.lint_explorables(self.tmp)
        self.assertTrue(
            any("orphan-register" in e and "registerWidget" in e and '"y"' in e and "no" in e.lower() for e in errors),
            f"expected orphan-registerWidget error: {errors}",
        )

    def test_single_quote_register_recognized(self) -> None:
        self._write("single-quote", ESSAY_WIDGET_TRUE_HAS_WIDGET,
                    "registerWidget('x', () => {});\n")
        errors = lint.lint_explorables(self.tmp)
        self.assertFalse(
            any("registerWidget" in e for e in errors),
            f"single-quote register should be recognized: {errors}",
        )

    def test_register_in_line_comment_ignored(self) -> None:
        self._write("comment-strip", ESSAY_WIDGET_TRUE_HAS_WIDGET,
                    'registerWidget("x", () => {});\n// registerWidget("z", () => {});\n')
        errors = lint.lint_explorables(self.tmp)
        self.assertFalse(
            any('"z"' in e for e in errors),
            f"// commented registerWidget should be stripped: {errors}",
        )

    def test_register_in_block_comment_ignored(self) -> None:
        self._write("block-strip", ESSAY_WIDGET_TRUE_HAS_WIDGET,
                    'registerWidget("x", () => {});\n/* registerWidget("z", () => {}); */\n')
        errors = lint.lint_explorables(self.tmp)
        self.assertFalse(
            any('"z"' in e for e in errors),
            f"/* */ commented registerWidget should be stripped: {errors}",
        )
```

- [ ] **Step 2: Run tests to confirm the five new ones fail**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: rule 5/6 tests FAIL.

- [ ] **Step 3: Implement rules 5 + 6**

Add at module level:

```python
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
REGISTER_RE = re.compile(r"""registerWidget\s*\(\s*['"]([^'"]+)['"]""")


def _strip_js_comments(src: str) -> str:
    src = BLOCK_COMMENT_RE.sub("", src)
    src = LINE_COMMENT_RE.sub("", src)
    return src


def _registered_ids(js_text: str) -> list[str]:
    stripped = _strip_js_comments(js_text)
    return [m.group(1) for m in REGISTER_RE.finditer(stripped)]
```

Inside the loop, after rule 4 (still inside `if has_widgets:`), add:

```python
            js_text = ""
            if js_path.exists():
                js_text = js_path.read_text(encoding="utf-8")
            registered = set(_registered_ids(js_text))
            shortcode_ids = {idv for _, idv in calls if idv}

            # Rule 5: every shortcode id has a registerWidget call
            for sid in sorted(shortcode_ids - registered):
                errors.append(
                    f"{rel}: widget id \"{sid}\" has no registerWidget call in assets/js/explorables/{slug}/index.js"
                )

            # Rule 6: every registerWidget call has a corresponding shortcode
            for rid in sorted(registered - shortcode_ids):
                errors.append(
                    f"assets/js/explorables/{slug}/index.js: registerWidget(\"{rid}\", ...) has no matching widget shortcode on /essays/{slug}/"
                )
```

- [ ] **Step 4: Run tests to confirm all pass**

Run: `python3 -m unittest tools/test_check_explorables.py -v`
Expected: 15 tests, PASS.

- [ ] **Step 5: Run linter against current repo state**

Run: `python3 tools/check_explorables.py`
Expected: errors — `content/essays/example-one/` declares `has_widgets: true`, has a widget shortcode (with `src=` not `id=`), so rule 2 fires (missing id). Rule 4 also fires (no `assets/js/explorables/example-one/index.js`). These errors are expected at this point in the plan; Task 18 fixes them.

This is *acceptance proof* that the linter does detect real violations.

- [ ] **Step 6: Commit**

```bash
git add tools/check_explorables.py tools/test_check_explorables.py
git commit -m "feat(linter): rules 5+6 — registerWidget ↔ shortcode id sync"
```

---

## Task 7: Linter CI integration (`ci-local.sh` + workflow)

Wire the linter + sibling test into CI. The linter currently fires on `example-one`; **don't merge this commit until Task 18 fixes that** — but it's safe to keep the changes local for now.

**Files:**
- Modify: `tools/ci-local.sh`
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Append to `tools/ci-local.sh`**

Find the existing `check_anchor_link.py` block (around line 114):

```bash
python3 tools/check_anchor_link.py
python3 -m unittest tools/test_check_anchor_link.py -v 2>&1 | tail -3
```

Insert immediately after it (before the `check_lhci_urls.py` block):

```bash

python3 tools/check_explorables.py
python3 -m unittest tools/test_check_explorables.py -v 2>&1 | tail -3
```

- [ ] **Step 2: Append to `.github/workflows/hugo.yaml`**

Find the existing `check_anchor_link.py` step (around line 172):

```yaml
      - name: Verify anchor-link affordance present
        run: python3 tools/check_anchor_link.py
      - name: Run anchor-link linter unit tests
        run: python3 -m unittest tools/test_check_anchor_link.py -v
```

Insert immediately after it (before the `check_lhci_urls.py` step):

```yaml
      - name: Verify explorables coupling
        run: python3 tools/check_explorables.py
      - name: Run explorables linter unit tests
        run: python3 -m unittest tools/test_check_explorables.py -v
```

- [ ] **Step 3: Commit**

```bash
git add tools/ci-local.sh .github/workflows/hugo.yaml
git commit -m "ci: wire check_explorables into ci-local.sh + workflow"
```

---

## Task 8: Shortcode upgrade — `layouts/shortcodes/widget.html`

Replace the 1-line stub with the full shortcode that emits a no-JS caption and a mount target.

**Files:**
- Modify: `layouts/shortcodes/widget.html`

- [ ] **Step 1: Replace the file contents**

```go-html-template
{{- /* Explorable widget mount point. Runtime in assets/js/explorables/runtime.js
       removes data-widget-fallback on successful mount; CSS §49 hides the
       static caption once the attribute is gone. */ -}}
{{- $id := .Get "id" -}}
{{- $label := or (.Get "label") "Interactive figure" -}}
<div data-widget-id="{{ $id }}"
     data-widget-fallback
     role="figure"
     aria-label="{{ $label }}">
  <p class="widget-fallback">{{ $label }} — enable JavaScript to view.</p>
</div>
```

- [ ] **Step 2: Verify Hugo still builds (no widget-bearing essay tries to mount yet — fixture lands later)**

Run: `hugo --minify --quiet --renderToMemory && echo BUILD_OK`
Expected: `BUILD_OK`.

(Note: don't run with a dev server alive — [[reference_hugo_dev_server_gotcha]].)

- [ ] **Step 3: Commit**

```bash
git add layouts/shortcodes/widget.html
git commit -m "feat(shortcode): widget — server-rendered fallback + mount target"
```

---

## Task 9: Runtime — `assets/js/explorables/runtime.js`

The `registerWidget` registry + DOMContentLoaded sweep.

**Files:**
- Create: `assets/js/explorables/runtime.js`

- [ ] **Step 1: Write the runtime**

```js
// assets/js/explorables/runtime.js
//
// Explorables runtime. Per-essay modules import { registerWidget } from
// this file and call registerWidget(id, mountFn) at top level. On
// DOMContentLoaded, the runtime sweeps every [data-widget-id] in the
// document, looks up its mount fn, removes data-widget-fallback (so CSS
// hides the no-JS caption), and calls fn(el). Errors are isolated per
// widget — one broken mount doesn't break the page.

const registry = new Map();

export function registerWidget(id, mountFn) {
  if (registry.has(id)) {
    console.warn(`[explorables] duplicate registerWidget for id="${id}"`);
  }
  registry.set(id, mountFn);
}

document.addEventListener('DOMContentLoaded', () => {
  for (const el of document.querySelectorAll('[data-widget-id]')) {
    const id = el.getAttribute('data-widget-id');
    const fn = registry.get(id);
    if (!fn) {
      console.warn(`[explorables] no widget registered for id="${id}"`);
      continue;
    }
    el.removeAttribute('data-widget-fallback');
    try {
      fn(el);
    } catch (err) {
      console.error(`[explorables] mount failed for "${id}":`, err);
    }
  }
});
```

- [ ] **Step 2: Commit**

```bash
git add assets/js/explorables/runtime.js
git commit -m "feat(explorables): runtime — registerWidget + DOMContentLoaded sweep"
```

---

## Task 10: Library helpers — `assets/js/explorables/lib/_base.js`

Internal helpers shared between `ReactiveValue` and `ReactiveChart`.

**Files:**
- Create: `assets/js/explorables/lib/_base.js`

- [ ] **Step 1: Write the helpers**

```js
// assets/js/explorables/lib/_base.js
//
// Internal helpers shared by library widgets. Not part of the public API.

export function clamp(v, lo, hi) {
  return v < lo ? lo : v > hi ? hi : v;
}

export function scale(v, [inLo, inHi], [outLo, outHi]) {
  if (inHi === inLo) return outLo;
  const t = (v - inLo) / (inHi - inLo);
  return outLo + t * (outHi - outLo);
}

// Build a row of slider controls. Returns { controlsEl, getState }.
// inputs: [{ name, min, max, default, step? }, ...]
// onChange: () => void  (called on any slider input event)
export function buildControls(inputs, onChange) {
  const state = {};
  for (const i of inputs) state[i.name] = i.default;

  const controlsEl = document.createElement('div');
  controlsEl.className = 'explorable-controls';

  for (const i of inputs) {
    const label = document.createElement('label');

    const nameSpan = document.createElement('span');
    nameSpan.className = 'explorable-label';
    nameSpan.textContent = i.name;
    label.appendChild(nameSpan);

    const range = document.createElement('input');
    range.type = 'range';
    range.min = String(i.min);
    range.max = String(i.max);
    range.step = String(i.step ?? 1);
    range.value = String(i.default);
    label.appendChild(range);

    const output = document.createElement('output');
    output.setAttribute('aria-live', 'polite');
    output.textContent = String(i.default);
    label.appendChild(output);

    range.addEventListener('input', () => {
      const v = Number(range.value);
      state[i.name] = v;
      output.textContent = String(v);
      onChange();
    });

    controlsEl.appendChild(label);
  }

  return { controlsEl, getState: () => ({ ...state }) };
}
```

- [ ] **Step 2: Commit**

```bash
git add assets/js/explorables/lib/_base.js
git commit -m "feat(explorables): lib/_base — clamp, scale, buildControls"
```

---

## Task 11: Library kind — `ReactiveValue`

**Files:**
- Create: `assets/js/explorables/lib/reactive-value.js`

- [ ] **Step 1: Write the class**

```js
// assets/js/explorables/lib/reactive-value.js
import { buildControls } from './_base.js';

export class ReactiveValue {
  constructor(el, { inputs, render }) {
    el.classList.add('explorable', 'explorable-value');

    const out = document.createElement('p');
    out.className = 'explorable-output';
    out.setAttribute('aria-live', 'polite');

    const rerender = () => {
      out.textContent = render(getState());
    };

    const { controlsEl, getState } = buildControls(inputs, rerender);
    el.appendChild(controlsEl);
    el.appendChild(out);

    rerender();
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add assets/js/explorables/lib/reactive-value.js
git commit -m "feat(explorables): lib/ReactiveValue — sliders + reactive text output"
```

---

## Task 12: Library kind — `ReactiveChart`

Hand-rolled SVG plot with reactive sliders.

**Files:**
- Create: `assets/js/explorables/lib/reactive-chart.js`

- [ ] **Step 1: Write the class**

```js
// assets/js/explorables/lib/reactive-chart.js
import { buildControls, scale } from './_base.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

function svgEl(tag, attrs = {}) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}

export class ReactiveChart {
  constructor(el, opts) {
    const {
      inputs,
      fn,
      x: [xMin, xMax],
      y: [yMin, yMax],
      samples = 100,
      width = 480,
      height = 200,
      xLabel = 'x',
      yLabel = 'y',
    } = opts;

    el.classList.add('explorable', 'explorable-chart');

    const figure = document.createElement('figure');
    figure.className = 'explorable-figure';

    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      preserveAspectRatio: 'xMidYMid meet',
      role: 'img',
      'aria-label': `${yLabel} as a function of ${xLabel}`,
    });

    const PAD = 24;

    // Static axis chrome (drawn once)
    const axes = svgEl('g', { class: 'explorable-axes' });
    axes.appendChild(svgEl('line', {
      x1: PAD, y1: height - PAD, x2: width - PAD, y2: height - PAD,
    }));
    axes.appendChild(svgEl('line', {
      x1: PAD, y1: PAD, x2: PAD, y2: height - PAD,
    }));
    // 4 tick labels: x-min, x-mid, x-max; y-min, y-max
    const xMid = (xMin + xMax) / 2;
    const yMid = (yMin + yMax) / 2;
    const xTickPx = (vx) => scale(vx, [xMin, xMax], [PAD, width - PAD]);
    const yTickPx = (vy) => scale(vy, [yMin, yMax], [height - PAD, PAD]);

    for (const [vx, anchor] of [[xMin, 'start'], [xMid, 'middle'], [xMax, 'end']]) {
      const t = svgEl('text', {
        x: xTickPx(vx), y: height - PAD + 14,
        'text-anchor': anchor, class: 'explorable-tick',
      });
      t.textContent = String(vx);
      axes.appendChild(t);
    }
    for (const [vy, baseline] of [[yMin, 'auto'], [yMax, 'hanging']]) {
      const t = svgEl('text', {
        x: PAD - 6, y: yTickPx(vy),
        'text-anchor': 'end', 'dominant-baseline': baseline, class: 'explorable-tick',
      });
      t.textContent = String(vy);
      axes.appendChild(t);
    }
    svg.appendChild(axes);

    // Reactive path
    const path = svgEl('path', { class: 'explorable-line', fill: 'none' });
    svg.appendChild(path);

    figure.appendChild(svg);

    const caption = document.createElement('figcaption');
    caption.className = 'explorable-axes-caption';
    caption.textContent = `${xLabel}: ${xMin} to ${xMax}, ${yLabel}: ${yMin} to ${yMax}`;
    figure.appendChild(caption);

    const rerender = () => {
      const state = getState();
      let d = '';
      for (let i = 0; i < samples; i++) {
        const x = xMin + (i / (samples - 1)) * (xMax - xMin);
        const y = fn(x, state);
        const px = xTickPx(x);
        const py = yTickPx(y);
        d += (i === 0 ? 'M' : 'L') + px.toFixed(2) + ' ' + py.toFixed(2) + ' ';
      }
      path.setAttribute('d', d.trimEnd());
    };

    const { controlsEl, getState } = buildControls(inputs, rerender);
    el.appendChild(controlsEl);
    el.appendChild(figure);

    rerender();
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add assets/js/explorables/lib/reactive-chart.js
git commit -m "feat(explorables): lib/ReactiveChart — hand-rolled SVG with reactive plot"
```

---

## Task 13: `scripts.html` — dynamic loop for per-essay explorable bundles

Wires the per-essay bundle pipeline. Each essay with `has_widgets: true` gets its own `js.Build` call; the `<script>` only emits when the current page IS that essay.

**Files:**
- Modify: `layouts/partials/scripts.html`

- [ ] **Step 1: Append the loop**

Add at the end of `layouts/partials/scripts.html` (after the existing 12 entries):

```go-html-template

{{- /* Explorables: per-essay bundle. Each essay with has_widgets:true gets a
       dedicated js.Build entry from assets/js/explorables/<slug>/index.js.
       The <script> tag emits page-narrowly — only when the current page's
       File.ContentBaseName matches the iterated essay's slug. The runtime +
       library kinds are inlined per bundle (no shared chunk in v1; see
       spec §10 follow-up 6). */ -}}
{{- if and (eq .Section "essays") (eq .Kind "page") .Params.has_widgets -}}
{{-   $slug := .File.ContentBaseName -}}
{{-   with resources.Get (printf "js/explorables/%s/index.js" $slug) -}}
{{-     $opts := dict "targetPath" (printf "js/explorables-%s.js" $slug) "minify" true -}}
{{-     $bundle := . | js.Build $opts | fingerprint -}}
<script src="{{ $bundle.RelPermalink }}" integrity="{{ $bundle.Data.Integrity }}" defer></script>
{{-   end -}}
{{- end }}
```

- [ ] **Step 2: Verify Hugo still builds (no widget-bearing essay yet — loop doesn't fire)**

Wait — `content/essays/example-one/index.md` has `has_widgets: true`. The loop WILL try to load `assets/js/explorables/example-one/index.js`, which doesn't exist yet (lands in Task 18). The `{{- with ... }}` block skips silently when `resources.Get` returns nil, so build will pass. Verify:

Run: `hugo --minify --quiet --renderToMemory && echo BUILD_OK`
Expected: `BUILD_OK`.

If it errors, the `with` guard isn't catching the missing resource — adjust the predicate to use `resources.GetMatch` or wrap in `if (fileExists ...)`-equivalent (likely not needed; `with` + `resources.Get` returning nil is the standard Hugo idiom).

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/scripts.html
git commit -m "feat(scripts): per-essay explorables dynamic bundle loop"
```

---

## Task 14: CSS §49 — explorables

Append section §49 to `assets/css/main.css` and add a line to the top-of-file section index.

**Files:**
- Modify: `assets/css/main.css`

- [ ] **Step 1: Update the top-of-file section index**

Find the existing line listing §48 (anchor-link affordance — recent addition). Add `§49 — explorables` to the index header at the same level, immediately after §48.

(Exact line depends on current state of `main.css` — read the top 60 lines and follow the existing list format.)

- [ ] **Step 2: Append §49 to the end of the file**

```css

/* ============================================================
 * §49 — explorables
 *
 * Per-essay interactive widget chrome. Library kinds:
 * ReactiveValue (sliders + reactive text), ReactiveChart
 * (sliders + hand-rolled SVG plot). Bespoke per-essay
 * widgets reuse the same .explorable* classes when convenient.
 * ============================================================ */

.explorable {
  display: block;
  margin: var(--space-6) 0;
}

.explorable-controls {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
  font-family: var(--font-ui);
  font-size: 0.95rem;
  color: var(--color-ink-soft);
}

.explorable-controls label {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.explorable-label {
  min-width: 3.5rem;
  font-style: italic;
}

.explorable-controls input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  width: 9rem;
  cursor: pointer;
}

.explorable-controls input[type="range"]::-webkit-slider-runnable-track {
  height: 4px;
  background: var(--color-steel);
  border-radius: 2px;
}
.explorable-controls input[type="range"]::-moz-range-track {
  height: 4px;
  background: var(--color-steel);
  border-radius: 2px;
}

.explorable-controls input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  background: var(--color-burgundy);
  border: none;
  border-radius: 50%;
  margin-top: -6px;
  cursor: pointer;
}
.explorable-controls input[type="range"]::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: var(--color-burgundy);
  border: none;
  border-radius: 50%;
  cursor: pointer;
}

.explorable-controls input[type="range"]:focus-visible::-webkit-slider-thumb {
  outline: 2px solid var(--color-burgundy);
  outline-offset: 2px;
}
.explorable-controls input[type="range"]:focus-visible::-moz-range-thumb {
  outline: 2px solid var(--color-burgundy);
  outline-offset: 2px;
}

.explorable-controls output {
  font-family: var(--font-mono);
  min-width: 2.5rem;
  text-align: right;
}

.explorable-output {
  font-family: var(--font-mono);
  color: var(--color-ink-soft);
  padding: var(--space-2) var(--space-3);
  border-left: 2px solid var(--color-burgundy);
  margin: 0;
}

.explorable-figure {
  margin: 0;
}

.explorable-figure svg {
  width: 100%;
  height: auto;
  display: block;
}

.explorable-axes line {
  stroke: var(--color-steel);
  stroke-width: 1;
}

.explorable-tick {
  font-family: var(--font-mono);
  font-size: 11px;
  fill: var(--color-ink-soft);
}

.explorable-line {
  stroke: var(--color-burgundy);
  stroke-width: 1.5;
  fill: none;
}

.explorable-axes-caption {
  font-family: var(--font-ui);
  font-size: 0.85rem;
  color: var(--color-ink-soft);
  margin-top: var(--space-2);
}

.widget-fallback {
  font-style: italic;
  color: var(--color-ink-soft);
  padding: var(--space-3);
  border: 1px dashed var(--color-steel);
  border-radius: var(--radius-sm);
  text-align: center;
  margin: 0;
}

[data-widget-id]:not([data-widget-fallback]) .widget-fallback {
  display: none;
}
```

- [ ] **Step 3: Run contrast check**

Run: `python3 tools/check-contrast.py`
Expected: pass — no new color pairings introduced; all consumed tokens already validated.

- [ ] **Step 4: Verify Hugo build**

Run: `hugo --minify --quiet --renderToMemory && echo BUILD_OK`
Expected: `BUILD_OK`.

- [ ] **Step 5: Commit**

```bash
git add assets/css/main.css
git commit -m "feat(css): §49 — explorables chrome + slider cross-browser"
```

---

## Task 15: Fixture — `content/essays/example-explorables/`

The dedicated explorables fixture: three widgets exercising both library kinds + a bespoke widget. Filler-only per [[feedback-filler-text-only]].

**Files:**
- Create: `content/essays/example-explorables/index.md`
- Create: `assets/js/explorables/example-explorables/index.js`

- [ ] **Step 1: Write the fixture markdown**

```markdown
---
title: "Example: explorables"
date: 2026-06-12
lastmod: 2026-06-12
draft: false
summary: "Filler essay exercising the explorables runtime — two library widgets and one bespoke widget."
tags: [example, explorables]
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

## A reactive value

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
ut labore et dolore magna aliqua.

{{< widget id="k-square" label="Square of k" >}}

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
commodo consequat.

## A reactive chart

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat
nulla pariatur.

{{< widget id="gaussian" label="Gaussian curve" >}}

Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit
anim id est laborum.

## A bespoke widget

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque
laudantium.

{{< widget id="spinner" label="Rotating spinner" >}}

Totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae
vitae dicta sunt explicabo.
```

- [ ] **Step 2: Write the per-essay JS**

```js
// assets/js/explorables/example-explorables/index.js
import { registerWidget } from '../runtime.js';
import { ReactiveValue } from '../lib/reactive-value.js';
import { ReactiveChart } from '../lib/reactive-chart.js';

registerWidget('k-square', (el) =>
  new ReactiveValue(el, {
    inputs: [{ name: 'k', min: 0, max: 10, default: 2, step: 0.1 }],
    render: ({ k }) => `f(k) = ${(k * k).toFixed(2)}`,
  })
);

registerWidget('gaussian', (el) =>
  new ReactiveChart(el, {
    inputs: [
      { name: 'sigma', min: 0.1, max: 3, default: 1, step: 0.1 },
      { name: 'mu', min: -3, max: 3, default: 0, step: 0.1 },
    ],
    fn: (x, { sigma, mu }) =>
      Math.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) / (sigma * Math.sqrt(2 * Math.PI)),
    x: [-5, 5],
    y: [0, 0.8],
    xLabel: 'x',
    yLabel: 'p(x)',
  })
);

registerWidget('spinner', (el) => {
  const canvas = document.createElement('canvas');
  canvas.width = 200;
  canvas.height = 200;
  el.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  ctx.strokeStyle = getComputedStyle(document.documentElement)
    .getPropertyValue('--color-burgundy')
    .trim() || '#7a0f2d';
  ctx.lineWidth = 3;

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let t = 0;
  const tick = () => {
    ctx.clearRect(0, 0, 200, 200);
    ctx.beginPath();
    ctx.arc(100, 100, 60, t, t + Math.PI);
    ctx.stroke();
    t += 0.02;
    if (!reduced) requestAnimationFrame(tick);
  };
  tick();
});
```

- [ ] **Step 3: Run the existing fixture linter to confirm the new fixture is well-formed**

Run: `python3 tools/check_fixtures.py`
Expected: pass.

- [ ] **Step 4: Run the explorables linter — expect it to pass on the new fixture**

Run: `python3 tools/check_explorables.py`
Expected: still errors from `example-one` (Task 18 fixes those); NO errors mentioning `example-explorables`.

- [ ] **Step 5: Verify Hugo build**

Run: `hugo --minify --quiet --renderToMemory && echo BUILD_OK`
Expected: `BUILD_OK`. Check that `public/essays/example-explorables/index.html` exists and contains `data-widget-id="k-square"`, etc.

(If using `--renderToMemory`, can't grep `public/`. Drop the flag for this verification: `rm -rf public && hugo --minify --quiet && grep -l 'data-widget-id="k-square"' public/essays/example-explorables/index.html`.)

- [ ] **Step 6: Commit**

```bash
git add content/essays/example-explorables/ assets/js/explorables/example-explorables/
git commit -m "feat(fixture): example-explorables — 3 widgets exercising runtime + lib"
```

---

## Task 16: Update `example-one` per spec §3 option (a)

Migrate the existing fixture to the new shortcode contract + add its per-essay JS so the linter passes on it.

**Files:**
- Modify: `content/essays/example-one/index.md` (line 59)
- Create: `assets/js/explorables/example-one/index.js`

- [ ] **Step 1: Update the widget call in `example-one`**

In `content/essays/example-one/index.md`, find line 59:

```
{{< widget src="example-widget" >}}
```

Replace with:

```
{{< widget id="example-widget" label="Example widget" >}}
```

- [ ] **Step 2: Create the per-essay JS**

```js
// assets/js/explorables/example-one/index.js
//
// Minimal mount — example-one is a frontmatter-shape fixture; the widget
// itself just confirms the per-essay-JS authoring path round-trips
// through the linter.
import { registerWidget } from '../runtime.js';

registerWidget('example-widget', (el) => {
  const p = document.createElement('p');
  p.textContent = '[example widget mounted]';
  p.style.fontFamily = 'var(--font-mono)';
  p.style.color = 'var(--color-ink-soft)';
  el.appendChild(p);
});
```

- [ ] **Step 3: Run the explorables linter**

Run: `python3 tools/check_explorables.py`
Expected: `OK — explorables coupling validates.` (clean).

- [ ] **Step 4: Verify Hugo build**

Run: `hugo --minify --quiet --renderToMemory && echo BUILD_OK`
Expected: `BUILD_OK`.

- [ ] **Step 5: Commit**

```bash
git add content/essays/example-one/index.md assets/js/explorables/example-one/index.js
git commit -m "feat(fixture): example-one — migrate widget to id= + add per-essay JS"
```

---

## Task 17: Smoke test extension

Extend `tools/check_smoke.py` to assert the new fixture renders correctly.

**Files:**
- Modify: `tools/check_smoke.py`

- [ ] **Step 1: Read current smoke checks**

Run: `grep -n "essays/example" tools/check_smoke.py | head -20`
to find the existing essay assertions block.

- [ ] **Step 2: Add the example-explorables block**

Find the section where essay-specific assertions live (look for an existing block that GETs `/essays/example-five/` or similar). Insert an analogous block for `example-explorables`:

```python
    # example-explorables — verify shortcode emission + per-essay bundle
    body = _get(base_url + "/essays/example-explorables/")
    for needle in (
        b'data-widget-id="k-square"',
        b'data-widget-id="gaussian"',
        b'data-widget-id="spinner"',
        b'<script src="/js/explorables-example-explorables.',
    ):
        if needle not in body:
            errors.append(
                f"/essays/example-explorables/: smoke check failed — body missing {needle!r}"
            )
```

(The `_get` / `errors` / `base_url` variable names should mirror what `check_smoke.py` already uses — read the file first and align.)

- [ ] **Step 3: Verify a built site passes**

Run:
```bash
rm -rf public && hugo --minify --quiet
python3 -m http.server -d public 8123 &
sleep 1
python3 tools/check_smoke.py
SMOKE_RC=$?
kill %1
[ "$SMOKE_RC" = "0" ] && echo SMOKE_OK
```
Expected: `SMOKE_OK`.

(Adjust the http.server command to match how `check_smoke.py` expects to be invoked — it may have its own server fixture; read the file's `if __name__ == "__main__":` block to confirm.)

- [ ] **Step 4: Commit**

```bash
git add tools/check_smoke.py
git commit -m "test(smoke): assert example-explorables widgets + bundle render"
```

---

## Task 18: CLAUDE.md — add 13th row to the JS pipeline table

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Find the JS pipeline table**

Search for the line `| Entry | Output | Loaded on | Notes |` in `CLAUDE.md` — the multi-entry bundling table sits in the "JS pipeline" section.

- [ ] **Step 2: Append a 13th row**

After the existing 12 rows (the last is `entry-streams.js`), add:

```
| `js/explorables/<slug>/index.js` (dynamic loop) | `explorables-<slug>.<hash>.js` (~few KB) | `.Section == "essays"` AND `.Kind == "page"` AND `.Params.has_widgets` AND `.File.ContentBaseName == <slug>` | per-essay; inlines runtime + lib kinds; spec at `docs/superpowers/specs/2026-06-12-sub-project-e-explorables-design.md` |
```

- [ ] **Step 3: Bump the "twelve times" count in the table preamble**

Find the line that says "runs Hugo's `js.Build` (esbuild) twelve times" in CLAUDE.md and update to "thirteen+ times (twelve fixed + per-essay loop)".

- [ ] **Step 4: Update the linter pair count**

Search for "twenty-seven linter pairs" / "27th linter pair" / similar phrases. Update to "twenty-eight" / "28th" wherever the explorables linter pair affects the count.

(Confirm with: `grep -n "linter pair\|27th\|28th\|twenty-seven\|twenty-eight" CLAUDE.md`.)

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): add 13th JS bundle row + 28th linter pair"
```

---

## Task 19: Roadmap — flip Tier 8.1 ☐ → ✓

**Files:**
- Modify: `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md`

- [ ] **Step 1: Find row 8.1**

```bash
grep -n "^| 8.1 " docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md
```

- [ ] **Step 2: Update row 8.1**

Replace the row's ☐ with ✓ and append the project-memory link + the spec/plan paths. Match the format used for 8.2:

```markdown
| 8.1 | ✓ **Sub-project E — explorable explainables** (Phase 3 final piece). Per-page interactive widgets + per-page JS bundle convention. Shipped 2026-06-12 (site commits TBD-FILL-AFTER-MERGE). 28th linter pair + CSS §49 + 13th JS bundle (dynamic per-essay loop) + 2 library kinds (ReactiveValue, ReactiveChart) + 1 fixture + example-one migration. → [project-tier-8-1-complete](../../../.claude/memory/project_tier_8_1_complete.md) | `docs/superpowers/specs/2026-06-12-sub-project-e-explorables-design.md` + `docs/superpowers/plans/2026-06-12-sub-project-e-explorables.md` |
```

(Defer filling the commit-range until after `git log` is final — Task 21 patches it.)

- [ ] **Step 3: Update the closing note**

Search for "Tier 8 holds the large new scopes" in the roadmap and amend to reflect 8.1 closed: "Tier 8.1 closed 2026-06-12; only sub-project E follow-ups (org-side authoring, etc., per spec §10) remain."

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md
git commit -m "docs(roadmap): Tier 8.1 closed — sub-project E explorables shipped"
```

---

## Task 20: Memory entry — `project_tier_8_1_complete.md`

Write the topic file + add the index pointer.

**Files:**
- Create: `.claude/memory/project_tier_8_1_complete.md`
- Modify: `.claude/memory/MEMORY.md`

- [ ] **Step 1: Write the topic file**

```markdown
---
name: tier-8-1-complete
description: "Tier 8.1 (sub-project E — explorables) shipped 2026-06-12; runtime + 2 library kinds + 28th linter pair + CSS §49 + fixture"
metadata:
  node_type: memory
  type: project
---

**Shipped 2026-06-12.** Sub-project E (Phase 3 final piece per [[project-phase-3-decomposition]]); Tier 8.1 of the polish/bugfix roadmap.

Site commits: TBD-FILL-AFTER-PUSH.

What landed end-to-end:

- Runtime `assets/js/explorables/runtime.js` — `registerWidget(id, fn)` + DOMContentLoaded sweep + per-widget try/catch isolation.
- Two library widget classes in `assets/js/explorables/lib/`: `ReactiveValue` (sliders → reactive text) and `ReactiveChart` (sliders → hand-rolled SVG plot, no d3). Shared `_base.js` helpers (clamp, scale, buildControls).
- Per-essay JS bundle convention: each essay with `has_widgets: true` triggers a dynamic `js.Build` call in `layouts/partials/scripts.html` against `assets/js/explorables/<slug>/index.js`. Output `explorables-<slug>.<hash>.js`, page-narrow `<script>` emit (`File.ContentBaseName` match).
- Shortcode `{{< widget id="..." [label="..."] >}}` upgraded from 1-line stub to server-rendered no-JS caption + mount target with `role="figure"` + `aria-label`.
- CSS §49 — 30-ish selectors covering chrome, slider cross-browser (webkit + moz prefix pairs), focus ring, fallback caption. No new color tokens.
- 28th linter pair (`tools/check_explorables.py` + `tools/test_check_explorables.py`) — 6 coupling rules (has_widgets↔shortcode, id required, id unique per page, per-essay JS exists, registerWidget covers all ids, no orphan registerWidget). 15 unit tests.
- New fixture `content/essays/example-explorables/` with 3 widgets (one per library kind + one bespoke canvas).
- Migrated `content/essays/example-one/` from `src=` to `id=` shortcode; added minimal per-essay JS.
- Smoke test extended to GET `/essays/example-explorables/` and assert the 3 `data-widget-id` attrs + the per-essay `<script>` tag.

Spec: `docs/superpowers/specs/2026-06-12-sub-project-e-explorables-design.md`.
Plan: `docs/superpowers/plans/2026-06-12-sub-project-e-explorables.md`.

**Follow-ups (queued in spec §10):**
1. Org-side authoring (`#+begin_explorable` block in ox-hugo handler). Filed during section-1 review at author's request — trigger: first real explorable essay needs export.
2. Step-through animator (3rd library kind).
3. Multi-series ReactiveChart.
4. Static-screenshot fallback for PDF/Word.
5. ReactiveChart screen-reader text alternative.
6. Runtime split into shared bundle (when N>3 widget-bearing essays exist).
7. Cross-widget state coordination.
8. Render-time browserless paint check.
```

- [ ] **Step 2: Add pointer to `MEMORY.md`**

Find the existing `project_tier_*_complete` index entries (last is `project-tier-6-deferred`). Append:

```markdown
- [Tier 8.1 — sub-project E (explorables) shipped](project_tier_8_1_complete.md) — runtime + 2 lib kinds (ReactiveValue, ReactiveChart) + 28th linter pair + CSS §49 + fixture, 2026-06-12
```

- [ ] **Step 3: Commit**

```bash
git add .claude/memory/project_tier_8_1_complete.md .claude/memory/MEMORY.md
git commit -m "memory: Tier 8.1 (sub-project E explorables) complete"
```

---

## Task 21: End-to-end verification + commit-range backfill

The final pass: run `ci-local.sh`, spot-check in the browser, then patch the TBD-FILL placeholders with the actual commit range.

- [ ] **Step 1: Run full local CI**

Run: `bash tools/ci-local.sh`
Expected: all green. Watch for the new "explorables" step.

Per [[feedback-always-run-ci-locally]] — don't skip this.

- [ ] **Step 2: Manual browser spot-check**

```bash
hugo server --buildDrafts &
sleep 2
open http://localhost:1313/essays/example-explorables/
```

Eyeball checklist (per [[feedback-verify-before-merge]]):

1. **Three widgets render** — k-square value, gaussian chart, rotating spinner.
2. **No-JS fallback** disappears (open DevTools → Elements → confirm `data-widget-fallback` is gone after mount).
3. **Slider interaction** — drag k slider, value updates smoothly. Drag sigma/mu sliders, gaussian curve re-renders.
4. **Keyboard** — Tab to a slider, arrow keys nudge value, screen-reader announces (if available).
5. **At 960px half-screen** ([[feedback-test-at-half-screen-1080p]]) — chart SVG scales; sliders wrap to new lines if needed.
6. **Dark mode** — toggle theme; chart line stays burgundy, axis text stays legible.
7. **Reduced motion** — devtools → Rendering → emulate `prefers-reduced-motion: reduce`; reload; spinner stops animating after first frame.
8. **example-one** — visit `/essays/example-one/` and confirm `[example widget mounted]` appears where the widget shortcode was.

Stop `hugo server` (`kill %1`).

- [ ] **Step 3: Backfill the commit range in Task 19 + 20 outputs**

```bash
git log --oneline master..HEAD | tail -25  # confirm the range
```

Then edit:
- `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` row 8.1 — replace `TBD-FILL-AFTER-MERGE` with `<first>..<last>` (N commits).
- `.claude/memory/project_tier_8_1_complete.md` — replace `TBD-FILL-AFTER-PUSH` similarly.

- [ ] **Step 4: Commit the backfill**

```bash
git add docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md .claude/memory/project_tier_8_1_complete.md
git commit -m "docs: backfill Tier 8.1 commit range"
```

- [ ] **Step 5: Final review + offer to push**

Run: `git log --oneline master..HEAD`
Expected: ~20 commits, all green.

DO NOT push yourself — surface to the author for the merge-and-push decision per [[feedback-verify-before-merge]]. State explicitly: "Local CI green, dev-server spot-check eyeballed for the 8 items above. Ready for your push to origin when you're satisfied."

---

## Notes for the executor

- **Don't run `hugo --minify` with a dev server alive** — [[reference-hugo-dev-server-gotcha]]. The verification steps that run `hugo --minify --quiet` assume no server is up; the dev-server step in Task 21 starts a fresh one.
- **No npm.** Every JS task uses bare ES modules and `js.Build` only. Don't `npm install` anything; don't add a `package.json`.
- **The plan is `js.Build`-in-a-loop**. If the Task 13 verify step fails with a Hugo error about `resources.Get` returning nil, the `with` guard should handle it — re-check the predicate matches the existing `entry-poetry.js` pattern (line 94-98 of `scripts.html`).
- **Esbuild side-effects.** Top-level `registerWidget(...)` calls in the per-essay `index.js` are real side effects. Esbuild keeps them. Library kinds are imported + instantiated via `new`, also kept. If a future refactor moves library kinds behind a factory that *isn't* instantiated at top level, esbuild may tree-shake — verify a build at that point.
- **The example-one widget shortcode change is a real fixture edit** — make sure the rest of `example-one/index.md` (the other 14 frontmatter keys, body prose) stays byte-identical except line 59.
