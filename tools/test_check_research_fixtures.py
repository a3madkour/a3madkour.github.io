"""Tests for check_research_fixtures.py — run with:
   python3 -m unittest tools/test_check_research_fixtures.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_research_fixtures as lint  # noqa: E402
from check_research_fixtures import validate_unique_theme_weights  # noqa: E402


THEME_OK = """\
---
title: "Memory and play"
status: active
tags: [memory, play]
last_modified: 2026-05-11
description: "Theme framing."
weight: 10
---

Body.
"""

THEME_MISSING_REQUIRED = """\
---
title: "Memory and play"
last_modified: 2026-05-11
description: "Theme framing."
weight: 10
---
"""

THEME_BAD_STATUS = """\
---
title: "Memory and play"
status: pondering
tags: [memory]
last_modified: 2026-05-11
description: "Theme framing."
weight: 10
---
"""

THEME_FORBIDDEN_PARENT_QUESTION = """\
---
title: "Memory and play"
status: active
tags: [memory]
last_modified: 2026-05-11
description: "Theme framing."
weight: 10
parent_question: some-question
---
"""

THEME_BAD_WEIGHT = """\
---
title: "Memory and play"
status: active
tags: [memory]
last_modified: 2026-05-11
description: "Theme framing."
weight: high
---
"""


QUESTION_OK = """\
---
title: "How do readers form narrative?"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "Question framing."
supporting_notes: [story-atoms]
outputs:
  - { kind: paper, title: "Paper", url: "https://x", year: 2025 }
---

Body.
"""

QUESTION_MISSING_THEME = """\
---
title: "Q"
status: active
last_modified: 2026-05-11
description: "..."
---
"""

QUESTION_BAD_OUTPUT_KIND = """\
---
title: "Q"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
outputs:
  - { kind: poster, title: "X", url: "https://x", year: 2025 }
---
"""

QUESTION_BAD_OUTPUT_YEAR = """\
---
title: "Q"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
outputs:
  - { kind: paper, title: "X", url: "https://x", year: "2025" }
---
"""

QUESTION_UNKNOWN_FIELD = """\
---
title: "Q"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
nonsense: yes
---
"""


def _write(parent: Path, name: str, body: str) -> None:
    d = parent / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.md").write_text(body)


class LintThemeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_valid_theme_no_errors(self):
        _write(self.tmp, "memory-and-play", THEME_OK)
        self.assertEqual([], lint.lint_theme(self.tmp / "memory-and-play"))

    def test_missing_required_fields(self):
        _write(self.tmp, "memory-and-play", THEME_MISSING_REQUIRED)
        errs = lint.lint_theme(self.tmp / "memory-and-play")
        joined = "\n".join(errs)
        self.assertIn("missing required field 'status'", joined)
        self.assertIn("missing required field 'tags'", joined)

    def test_bad_status_enum(self):
        _write(self.tmp, "memory-and-play", THEME_BAD_STATUS)
        errs = lint.lint_theme(self.tmp / "memory-and-play")
        self.assertTrue(any("status='pondering'" in e for e in errs))

    def test_forbidden_field_parent_question(self):
        _write(self.tmp, "memory-and-play", THEME_FORBIDDEN_PARENT_QUESTION)
        errs = lint.lint_theme(self.tmp / "memory-and-play")
        self.assertTrue(any("forbidden field 'parent_question'" in e for e in errs))

    def test_bad_weight_type(self):
        _write(self.tmp, "memory-and-play", THEME_BAD_WEIGHT)
        errs = lint.lint_theme(self.tmp / "memory-and-play")
        self.assertTrue(any("weight must be an integer" in e for e in errs))


class LintQuestionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_valid_question_no_errors(self):
        _write(self.tmp, "q-slug", QUESTION_OK)
        self.assertEqual([], lint.lint_question(self.tmp / "q-slug"))

    def test_missing_theme(self):
        _write(self.tmp, "q-slug", QUESTION_MISSING_THEME)
        errs = lint.lint_question(self.tmp / "q-slug")
        self.assertTrue(any("missing required field 'theme'" in e for e in errs))

    def test_bad_output_kind(self):
        _write(self.tmp, "q-slug", QUESTION_BAD_OUTPUT_KIND)
        errs = lint.lint_question(self.tmp / "q-slug")
        self.assertTrue(any("outputs[0].kind='poster'" in e for e in errs))

    def test_bad_output_year_type(self):
        _write(self.tmp, "q-slug", QUESTION_BAD_OUTPUT_YEAR)
        errs = lint.lint_question(self.tmp / "q-slug")
        self.assertTrue(any("outputs[0].year must be a 4-digit int" in e for e in errs))

    def test_unknown_field(self):
        _write(self.tmp, "q-slug", QUESTION_UNKNOWN_FIELD)
        errs = lint.lint_question(self.tmp / "q-slug")
        self.assertTrue(any("unknown field 'nonsense'" in e for e in errs))


class ValidateUniqueThemeWeightsTests(unittest.TestCase):
    def test_unique_theme_weights_detects_duplicate(self):
        """Two themes with the same weight should produce a linter error."""
        themes = [
            {'slug': 'theme-a', 'weight': 10, 'title': 'A', 'status': 'active', 'last_modified': '2026-05-11'},
            {'slug': 'theme-b', 'weight': 10, 'title': 'B', 'status': 'active', 'last_modified': '2026-05-11'},
        ]
        errors = validate_unique_theme_weights(themes)
        self.assertEqual(len(errors), 1)
        self.assertIn('weight 10 duplicated', errors[0])
        self.assertIn('theme-a', errors[0])
        self.assertIn('theme-b', errors[0])

    def test_unique_theme_weights_accepts_distinct(self):
        """Distinct weights produce no errors."""
        themes = [
            {'slug': 'theme-a', 'weight': 10},
            {'slug': 'theme-b', 'weight': 20},
            {'slug': 'theme-c', 'weight': 30},
        ]
        errors = validate_unique_theme_weights(themes)
        self.assertEqual(errors, [])

    def test_unique_theme_weights_skips_missing(self):
        """Themes without a weight field shouldn't crash the check (weight is required elsewhere)."""
        themes = [
            {'slug': 'theme-a'},
            {'slug': 'theme-b', 'weight': 20},
        ]
        errors = validate_unique_theme_weights(themes)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
