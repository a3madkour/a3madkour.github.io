"""Tests for check_research_links.py — run with:
   python3 -m unittest tools/test_check_research_links.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_research_links as lint  # noqa: E402


THEME_OK = """\
---
title: "Memory and play"
status: active
tags: [memory]
last_modified: 2026-05-11
description: "..."
weight: 10
garden_topic_ref: memory-in-play
---
"""

THEME_NO_REF = """\
---
title: "Save-game as form"
status: answered
tags: [aesthetics]
last_modified: 2026-05-11
description: "..."
weight: 30
---
"""

GARDEN_TOPIC_MAP_NOTE = """\
---
title: "Memory in play"
draft: false
last_modified: 2026-05-11
growth_stage: evergreen
topic_map: [story-atoms]
---
"""

GARDEN_PLAIN_NOTE = """\
---
title: "Story atoms"
draft: false
last_modified: 2026-05-11
growth_stage: budding
---
"""

GARDEN_DRAFT_NOTE = """\
---
title: "Draft"
draft: true
last_modified: 2026-05-11
growth_stage: seedling
---
"""

QUESTION_OK = """\
---
title: "How do readers form narrative?"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
supporting_notes: [story-atoms]
---
"""

QUESTION_BAD_THEME = """\
---
title: "Q"
theme: nonexistent-theme
status: active
last_modified: 2026-05-11
description: "..."
---
"""

QUESTION_BAD_SUPPORTING = """\
---
title: "Q"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
supporting_notes: [does-not-exist]
---
"""

QUESTION_PARENT_WRONG_THEME = """\
---
title: "Q"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
parent_question: stranger-q
---
"""

QUESTION_STRANGER = """\
---
title: "Stranger"
theme: save-game-as-form
status: active
last_modified: 2026-05-11
description: "..."
---
"""


def _write(parent: Path, name: str, body: str) -> None:
    d = parent / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.md").write_text(body)


class CrossRefTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.themes = self.tmp / "themes"
        self.questions = self.tmp / "questions"
        self.garden = self.tmp / "garden"
        self.essays = self.tmp / "essays"
        for d in (self.themes, self.questions, self.garden, self.essays):
            d.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_valid_setup_no_errors(self):
        _write(self.themes, "memory-and-play", THEME_OK)
        _write(self.questions, "q-slug", QUESTION_OK)
        _write(self.garden, "memory-in-play", GARDEN_TOPIC_MAP_NOTE)
        _write(self.garden, "story-atoms", GARDEN_PLAIN_NOTE)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertEqual([], errs)

    def test_dangling_garden_topic_ref(self):
        _write(self.themes, "memory-and-play", THEME_OK)
        # no memory-in-play garden note created
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("garden_topic_ref='memory-in-play' does not resolve" in e for e in errs))

    def test_garden_topic_ref_without_topic_map(self):
        _write(self.themes, "memory-and-play", THEME_OK)
        # memory-in-play exists but has no topic_map declared
        _write(self.garden, "memory-in-play", GARDEN_PLAIN_NOTE)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("without topic_map" in e for e in errs))

    def test_garden_topic_ref_to_draft(self):
        _write(self.themes, "memory-and-play", THEME_OK)
        _write(self.garden, "memory-in-play", GARDEN_DRAFT_NOTE)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("resolves to a draft" in e for e in errs))

    def test_theme_no_ref_is_fine(self):
        _write(self.themes, "save-game-as-form", THEME_NO_REF)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertEqual([], errs)

    def test_question_bad_theme(self):
        _write(self.themes, "memory-and-play", THEME_NO_REF)
        _write(self.questions, "q-slug", QUESTION_BAD_THEME)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("theme='nonexistent-theme'" in e for e in errs))

    def test_question_bad_supporting_note(self):
        _write(self.themes, "memory-and-play", THEME_NO_REF)
        _write(self.questions, "q-slug", QUESTION_BAD_SUPPORTING)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("supporting_notes entry 'does-not-exist'" in e for e in errs))

    def test_parent_question_wrong_theme(self):
        _write(self.themes, "memory-and-play", THEME_NO_REF)
        _write(self.themes, "save-game-as-form", THEME_NO_REF)
        _write(self.questions, "q-slug", QUESTION_PARENT_WRONG_THEME)
        _write(self.questions, "stranger-q", QUESTION_STRANGER)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("is in theme 'save-game-as-form', not 'memory-and-play'" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
