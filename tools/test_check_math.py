"""Tests for check_math.py — run with:
   python3 -m unittest tools/test_check_math.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_math as lint  # noqa: E402


ESSAY_WITH_MATH = """\
---
title: "Example One"
date: 2026-04-12
draft: false
has_math: true
---

Lorem ipsum \\(\\alpha + \\beta\\) dolor.
"""

ESSAY_NO_MATH = """\
---
title: "Example Two"
date: 2026-04-13
draft: false
has_math: false
---

Lorem ipsum dolor sit amet.
"""

ESSAY_HAS_MATH_TRUE_BUT_NO_MARKERS = """\
---
title: "Example Three"
date: 2026-04-14
draft: false
has_math: true
---

Lorem ipsum dolor sit amet.
"""

ESSAY_HAS_MATH_FALSE_BUT_MARKERS_PRESENT = """\
---
title: "Example Four"
date: 2026-04-15
draft: false
has_math: false
---

Try \\(x = 1\\) here.
"""

ESSAY_NO_HAS_MATH_FIELD_BUT_MARKERS = """\
---
title: "Example Five"
date: 2026-04-16
draft: false
---

Try \\[E = mc^2\\] here.
"""

ESSAY_MATH_INSIDE_CODE_FENCE = """\
---
title: "Example Six"
date: 2026-04-17
draft: false
has_math: false
---

Lorem ipsum.

```python
# Example LaTeX in a code block — should NOT count:
# \\(x = 1\\)
```

Plain prose continues.
"""

ESSAY_DOLLAR_IN_PROSE = """\
---
title: "Example Seven"
date: 2026-04-18
draft: false
has_math: false
---

Costs $5 per month, $10/year. Discount of $100 for early signup.
"""

# `$$...$$` and single-`$...$` are NOT enabled as passthrough delimiters in
# hugo.yaml, so they render as literal text, not math — a page whose only
# math-looking content is dollars needs no KaTeX CSS and must stay has_math:false.
ESSAY_DOLLAR_MATH_DOESNT_RENDER = """\
---
title: "Example Eight"
date: 2026-04-19
draft: false
has_math: false
---

Block dollar $$x^2 + y^2 = z^2$$ and inline $a+b$ are literal text here.
"""

# A bare `\\begin{...}` environment not wrapped in `\\[...\\]` is not captured by
# the passthrough extension, so it renders as literal text — no CSS needed.
# (Canonical ox-hugo output wraps environments in `\\[...\\]`, which the `\\[`
# marker already covers.)
ESSAY_BARE_BEGIN_DOESNT_RENDER = """\
---
title: "Example Nine"
date: 2026-04-20
draft: false
has_math: false
---

An unwrapped \\begin{aligned} a &= b \\end{aligned} stays literal text.
"""


class MathCouplingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.essays = self.tmp / "content" / "essays"
        self.essays.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write_essay(self, slug: str, body: str) -> None:
        d = self.essays / slug
        d.mkdir()
        (d / "index.md").write_text(body)

    def test_has_math_true_with_markers_passes(self):
        self._write_essay("one", ESSAY_WITH_MATH)
        errors = lint.lint_coupling(self.essays)
        self.assertEqual(errors, [])

    def test_has_math_false_no_markers_passes(self):
        self._write_essay("two", ESSAY_NO_MATH)
        errors = lint.lint_coupling(self.essays)
        self.assertEqual(errors, [])

    def test_has_math_true_without_markers_fails(self):
        self._write_essay("three", ESSAY_HAS_MATH_TRUE_BUT_NO_MARKERS)
        errors = lint.lint_coupling(self.essays)
        self.assertEqual(len(errors), 1)
        self.assertIn("no math markers", errors[0])

    def test_has_math_false_with_markers_fails(self):
        self._write_essay("four", ESSAY_HAS_MATH_FALSE_BUT_MARKERS_PRESENT)
        errors = lint.lint_coupling(self.essays)
        self.assertEqual(len(errors), 1)
        self.assertIn("math markers found", errors[0])

    def test_has_math_missing_with_markers_fails(self):
        self._write_essay("five", ESSAY_NO_HAS_MATH_FIELD_BUT_MARKERS)
        errors = lint.lint_coupling(self.essays)
        self.assertEqual(len(errors), 1)
        self.assertIn("math markers found", errors[0])

    def test_math_in_code_fence_ignored(self):
        self._write_essay("six", ESSAY_MATH_INSIDE_CODE_FENCE)
        errors = lint.lint_coupling(self.essays)
        self.assertEqual(errors, [])

    def test_dollar_signs_in_prose_dont_trip_inline_dollar(self):
        self._write_essay("seven", ESSAY_DOLLAR_IN_PROSE)
        errors = lint.lint_coupling(self.essays)
        self.assertEqual(errors, [])

    def test_dollar_math_not_counted_as_math(self):
        # $$...$$ / $...$ are not enabled delimiters — they don't render, so
        # has_math:false with only dollar math must pass (not flagged).
        self._write_essay("eight", ESSAY_DOLLAR_MATH_DOESNT_RENDER)
        errors = lint.lint_coupling(self.essays)
        self.assertEqual(errors, [])

    def test_bare_begin_environment_not_counted_as_math(self):
        # Unwrapped \begin{...} isn't captured by passthrough; it doesn't render.
        self._write_essay("nine", ESSAY_BARE_BEGIN_DOESNT_RENDER)
        errors = lint.lint_coupling(self.essays)
        self.assertEqual(errors, [])


class CodeFenceStrippingTests(unittest.TestCase):
    """R2.7: indented and ~~~ fences must also shield math markers."""

    def test_math_in_indented_backtick_fence_ignored(self):
        body = "prose\n\n    ```\n    \\(x^2\\)\n    ```\n\nmore prose\n"
        self.assertFalse(lint._body_has_math(body))

    def test_math_in_tilde_fence_ignored(self):
        body = "prose\n\n~~~\n\\[y = mx + b\\]\n~~~\n\nmore prose\n"
        self.assertFalse(lint._body_has_math(body))

    def test_math_outside_fences_still_detected(self):
        self.assertTrue(lint._body_has_math("some \\(z\\) inline math\n"))


class PairedDelimiterTests(unittest.TestCase):
    """Detection requires MATCHED delimiters, mirroring what passthrough
    captures — unpaired look-alikes must not count as math."""

    def test_unpaired_open_bracket_not_math(self):
        # The poems' \[00:99] synced-lyric timestamp: \[ with no closing \].
        self.assertFalse(lint._body_has_math("[00:18]ut \\[00:99] [00:20]minim\n"))

    def test_unpaired_open_paren_not_math(self):
        self.assertFalse(lint._body_has_math("a stray \\( with no close\n"))

    def test_math_shortcode_detected(self):
        self.assertTrue(lint._body_has_math("before {{< math >}}\\(x\\){{< /math >}} after\n"))


class MathScopeTests(unittest.TestCase):
    """Math is essays-only: rendered-math markers outside content/essays/ fail."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.content = self.tmp / "content"
        self.content.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, relpath: str, body: str) -> None:
        p = self.content / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)

    def test_math_in_essays_allowed(self):
        self._write("essays/one/index.md", "---\nhas_math: true\n---\nMath \\(x\\) here.\n")
        self.assertEqual(lint.lint_scope(self.content), [])

    def test_math_in_garden_flagged(self):
        self._write("garden/note/index.md", "---\ntitle: n\n---\nStray \\(x^2\\) math.\n")
        errors = lint.lint_scope(self.content)
        self.assertEqual(len(errors), 1)
        self.assertIn("outside essays", errors[0])

    def test_math_shortcode_in_works_flagged(self):
        self._write("works/games/g/index.md", "---\ntitle: g\n---\n{{< math >}}\\(x\\){{< /math >}}\n")
        errors = lint.lint_scope(self.content)
        self.assertEqual(len(errors), 1)
        self.assertIn("outside essays", errors[0])

    def test_poem_timestamp_not_flagged(self):
        # Regression: \[00:99] is an unpaired synced-lyric marker, not math.
        self._write(
            "works/poetry/p/index.md",
            "---\ntitle: p\n---\n[00:18]ut [00:19]enim \\[00:99] [00:20]minim\n",
        )
        self.assertEqual(lint.lint_scope(self.content), [])

    def test_non_math_section_clean(self):
        self._write("garden/note/index.md", "---\ntitle: n\n---\nNo math here.\n")
        self.assertEqual(lint.lint_scope(self.content), [])


if __name__ == "__main__":
    unittest.main()
