"""Tests for check_garden_links.py — run with:
   python3 -m unittest tools/test_check_garden_links.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_garden_links as lint  # noqa: E402


CONCEPT_NOTE_NO_LINKS = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Lorem ipsum dolor sit amet.
"""

CONCEPT_NOTE_TO_B = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Lorem ipsum [b](/garden/note-b/) dolor sit amet.
"""

CONCEPT_NOTE_TO_MISSING = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Lorem ipsum [missing](/garden/does-not-exist/).
"""

CONCEPT_NOTE_DRAFT = """\
---
title: "Note B"
draft: true
last_modified: 2026-04-22
growth_stage: seedling
---

Body.
"""

CONCEPT_NOTE_PUBLISHED_B = """\
---
title: "Note B"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Body.
"""

CONCEPT_NOTE_SELF_REF = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Self-link [a](/garden/note-a/).
"""

CONCEPT_NOTE_MULTIPLE_TARGETS = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

[b](/garden/note-b/) and [c](/garden/note-c/) and [b again](/garden/note-b/).
"""

CONCEPT_NOTE_NON_GARDEN_LINK = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Outside the section: [essay](/essays/some-essay/).
"""


class GardenLinksLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.garden = self.tmp / "content" / "garden"
        self.garden.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, slug: str, body: str) -> None:
        d = self.garden / slug
        d.mkdir()
        (d / "index.md").write_text(body)

    def test_no_links_passes(self):
        self._write("note-a", CONCEPT_NOTE_NO_LINKS)
        errors, warnings = lint.lint_garden_links(self.garden)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_resolved_link_passes(self):
        self._write("note-a", CONCEPT_NOTE_TO_B)
        self._write("note-b", CONCEPT_NOTE_PUBLISHED_B)
        errors, warnings = lint.lint_garden_links(self.garden)
        self.assertEqual(errors, [])

    def test_missing_target_fails(self):
        self._write("note-a", CONCEPT_NOTE_TO_MISSING)
        errors, _ = lint.lint_garden_links(self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("does-not-exist", errors[0])
        self.assertIn("note-a", errors[0])

    def test_draft_target_fails(self):
        self._write("note-a", CONCEPT_NOTE_TO_B)
        self._write("note-b", CONCEPT_NOTE_DRAFT)
        errors, _ = lint.lint_garden_links(self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("draft", errors[0].lower())

    def test_self_reference_warns_does_not_fail(self):
        self._write("note-a", CONCEPT_NOTE_SELF_REF)
        errors, warnings = lint.lint_garden_links(self.garden)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("note-a", warnings[0])

    def test_multiple_targets_in_one_file(self):
        self._write("note-a", CONCEPT_NOTE_MULTIPLE_TARGETS)
        self._write("note-b", CONCEPT_NOTE_PUBLISHED_B)
        # note-c is missing → 1 error; note-b appears twice but should only error/pass once
        errors, _ = lint.lint_garden_links(self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("note-c", errors[0])

    def test_non_garden_link_ignored(self):
        self._write("note-a", CONCEPT_NOTE_NON_GARDEN_LINK)
        errors, warnings = lint.lint_garden_links(self.garden)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
