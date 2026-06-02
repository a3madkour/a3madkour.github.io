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
        errors = lint.lint_math(self.essays)
        self.assertEqual(errors, [])

    def test_has_math_false_no_markers_passes(self):
        self._write_essay("two", ESSAY_NO_MATH)
        errors = lint.lint_math(self.essays)
        self.assertEqual(errors, [])

    def test_has_math_true_without_markers_fails(self):
        self._write_essay("three", ESSAY_HAS_MATH_TRUE_BUT_NO_MARKERS)
        errors = lint.lint_math(self.essays)
        self.assertEqual(len(errors), 1)
        self.assertIn("no math markers", errors[0])

    def test_has_math_false_with_markers_fails(self):
        self._write_essay("four", ESSAY_HAS_MATH_FALSE_BUT_MARKERS_PRESENT)
        errors = lint.lint_math(self.essays)
        self.assertEqual(len(errors), 1)
        self.assertIn("math markers found", errors[0])

    def test_has_math_missing_with_markers_fails(self):
        self._write_essay("five", ESSAY_NO_HAS_MATH_FIELD_BUT_MARKERS)
        errors = lint.lint_math(self.essays)
        self.assertEqual(len(errors), 1)
        self.assertIn("math markers found", errors[0])

    def test_math_in_code_fence_ignored(self):
        self._write_essay("six", ESSAY_MATH_INSIDE_CODE_FENCE)
        errors = lint.lint_math(self.essays)
        self.assertEqual(errors, [])

    def test_dollar_signs_in_prose_dont_trip_inline_dollar(self):
        self._write_essay("seven", ESSAY_DOLLAR_IN_PROSE)
        errors = lint.lint_math(self.essays)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
