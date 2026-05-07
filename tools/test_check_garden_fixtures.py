"""Tests for check_garden_fixtures.py — run with:
   python3 -m unittest tools/test_check_garden_fixtures.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_garden_fixtures as lint  # noqa: E402


CONCEPT_NOTE = """\
---
title: "Salience and memory"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
tags: ["memory", "narrative"]
---

Lorem ipsum dolor sit amet.
"""

CONCEPT_TOPIC_MAP_NOTE = """\
---
title: "Procedural narrative"
draft: false
last_modified: 2026-04-25
growth_stage: budding
tags: ["narrative", "games"]
topic_map: ["surprise-budget", "salience-and-memory"]
---

Framing prose.
"""

MEDIA_NOTE = """\
---
title: "Invisible Cities"
draft: false
last_modified: 2026-04-30
growth_stage: budding
media_type: book
status: reading
creator: "Italo Calvino"
year: 1972
started: 2025-12-15
spoiler_level: light
original_url: "https://example.invalid/book"
tags: ["reading", "calvino"]
---

Body.
"""

REFERENCE_NOTE = """\
---
title: "Games as art"
draft: false
last_modified: 2026-04-12
growth_stage: evergreen
media_type: paper
creator: "Nguyen, C. T."
year: 2020
original_url: "https://doi.org/10.1234/abc"
tags: ["games", "aesthetics"]
---

Body.
"""


class TempRepo:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        (self.root / "content" / "garden").mkdir(parents=True)

    def write_note(self, slug: str, body: str) -> None:
        d = self.root / "content" / "garden" / slug
        d.mkdir(exist_ok=True)
        (d / "index.md").write_text(body)

    def cleanup(self) -> None:
        shutil.rmtree(self.root)


class GardenLinterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    # --- happy paths ---

    def test_valid_concept_note_passes(self) -> None:
        self.repo.write_note("salience-and-memory", CONCEPT_NOTE)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_media_note_passes(self) -> None:
        self.repo.write_note("invisible-cities", MEDIA_NOTE)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_reference_note_passes(self) -> None:
        self.repo.write_note("nguyen-2020", REFERENCE_NOTE)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_topic_map_resolves(self) -> None:
        self.repo.write_note("surprise-budget", CONCEPT_NOTE.replace(
            'title: "Salience and memory"', 'title: "Surprise budget"'
        ))
        self.repo.write_note("salience-and-memory", CONCEPT_NOTE)
        self.repo.write_note("procedural-narrative", CONCEPT_TOPIC_MAP_NOTE)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_empty_garden_passes(self) -> None:
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0)

    # --- required-field failures ---

    def test_missing_title_fails(self) -> None:
        broken = CONCEPT_NOTE.replace('title: "Salience and memory"\n', "")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("title" in e for e in errors))

    def test_missing_growth_stage_fails(self) -> None:
        broken = CONCEPT_NOTE.replace("growth_stage: seedling\n", "")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("growth_stage" in e for e in errors))

    def test_media_missing_status_fails(self) -> None:
        broken = MEDIA_NOTE.replace("status: reading\n", "")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("status" in e for e in errors))

    def test_media_missing_creator_fails(self) -> None:
        broken = MEDIA_NOTE.replace('creator: "Italo Calvino"\n', "")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("creator" in e for e in errors))

    def test_reference_missing_creator_fails(self) -> None:
        broken = REFERENCE_NOTE.replace('creator: "Nguyen, C. T."\n', "")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("creator" in e for e in errors))

    # --- forbidden-field failures ---

    def test_concept_with_status_fails(self) -> None:
        broken = CONCEPT_NOTE.replace(
            "growth_stage: seedling\n",
            "growth_stage: seedling\nstatus: reading\n",
        )
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("status" in e and "concept" in e for e in errors))

    def test_concept_with_started_fails(self) -> None:
        broken = CONCEPT_NOTE.replace(
            "growth_stage: seedling\n",
            "growth_stage: seedling\nstarted: 2026-01-01\n",
        )
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("started" in e for e in errors))

    def test_reference_with_status_fails(self) -> None:
        broken = REFERENCE_NOTE.replace(
            "growth_stage: evergreen\n",
            "growth_stage: evergreen\nstatus: reading\n",
        )
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("status" in e and "reference" in e for e in errors))

    # --- enum-validation failures ---

    def test_invalid_growth_stage_fails(self) -> None:
        broken = CONCEPT_NOTE.replace("growth_stage: seedling", "growth_stage: enormous")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("growth_stage" in e and "enormous" in e for e in errors))

    def test_invalid_status_fails(self) -> None:
        broken = MEDIA_NOTE.replace("status: reading", "status: pondering")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("status" in e and "pondering" in e for e in errors))

    def test_invalid_media_type_fails(self) -> None:
        broken = MEDIA_NOTE.replace("media_type: book", "media_type: scroll")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("media_type" in e and "scroll" in e for e in errors))

    def test_invalid_spoiler_level_fails(self) -> None:
        broken = MEDIA_NOTE.replace("spoiler_level: light", "spoiler_level: extreme")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("spoiler_level" in e for e in errors))

    # --- date validation ---

    def test_future_last_modified_fails(self) -> None:
        broken = CONCEPT_NOTE.replace("last_modified: 2026-04-22", "last_modified: 2099-01-01")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("last_modified" in e and "future" in e for e in errors))

    # --- topic_map resolution ---

    def test_topic_map_unresolved_fails(self) -> None:
        broken = CONCEPT_TOPIC_MAP_NOTE.replace(
            'topic_map: ["surprise-budget", "salience-and-memory"]',
            'topic_map: ["does-not-exist"]',
        )
        self.repo.write_note("procedural-narrative", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("does-not-exist" in e for e in errors))

    def test_topic_map_to_draft_fails(self) -> None:
        draft_note = CONCEPT_NOTE.replace("draft: false", "draft: true")
        self.repo.write_note("draft-target", draft_note)
        owner = CONCEPT_TOPIC_MAP_NOTE.replace(
            'topic_map: ["surprise-budget", "salience-and-memory"]',
            'topic_map: ["draft-target"]',
        )
        self.repo.write_note("procedural-narrative", owner)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("draft" in e for e in errors))

    # --- url validation ---

    def test_invalid_original_url_scheme_fails(self) -> None:
        broken = MEDIA_NOTE.replace(
            'original_url: "https://example.invalid/book"',
            'original_url: "ftp://example.invalid/book"',
        )
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("original_url" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
