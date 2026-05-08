"""Tests for check_filter_chips_config.py — run with:
   python3 -m unittest tools/test_check_filter_chips_config.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_filter_chips_config as lint  # noqa: E402


GARDEN_NOTE = """\
---
title: "Salience and memory"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
tags: ["memory", "narrative"]
---

Body.
"""

ESSAY_NOTE = """\
---
title: "Example essay"
date: 2026-01-01
lastmod: 2026-01-01
draft: false
summary: "x"
tags: ["example-tag-a", "example-tag-b"]
series: ""
series_order: 0
toc: false
has_sidenotes: false
has_citations: false
has_footnotes: false
has_math: false
has_widgets: false
has_video_sync: false
---

Body.
"""


class TempRepo:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        (self.root / "content" / "garden").mkdir(parents=True)
        (self.root / "content" / "essays").mkdir(parents=True)
        (self.root / "data").mkdir(parents=True)

    def write_garden(self, slug: str, body: str = GARDEN_NOTE) -> None:
        d = self.root / "content" / "garden" / slug
        d.mkdir(exist_ok=True)
        (d / "index.md").write_text(body)

    def write_essay(self, slug: str, body: str = ESSAY_NOTE) -> None:
        d = self.root / "content" / "essays" / slug
        d.mkdir(exist_ok=True)
        (d / "index.md").write_text(body)

    def write_config(self, content: str) -> None:
        (self.root / "data" / "filter-chips.yaml").write_text(content)

    def cleanup(self) -> None:
        shutil.rmtree(self.root)


class FilterChipsLinterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    # --- happy paths ---

    def test_no_config_file_passes(self) -> None:
        # Auto-fallback applies at build time; absence is not an error.
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_config_with_no_sections_passes(self) -> None:
        self.repo.write_config("# empty\n")
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_garden_curation_passes(self) -> None:
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["memory", "narrative"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_top_k_override_passes(self) -> None:
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: 8\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_empty_primary_tags_passes(self) -> None:
        # Empty list means auto-fallback at build time.
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: []\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_section_not_in_config_passes(self) -> None:
        # essays section absent from config → auto-fallback applies.
        self.repo.write_garden("salience-and-memory")
        self.repo.write_essay("essay-1")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["memory"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    # --- failures ---

    def test_stale_garden_tag_fails(self) -> None:
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["memory", "ghost-tag"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        joined = "\n".join(errors)
        self.assertIn("ghost-tag", joined)
        self.assertIn("garden", joined)

    def test_stale_essay_tag_fails(self) -> None:
        self.repo.write_essay("essay-1")
        self.repo.write_config(
            'essays:\n'
            '  primary_tags: ["nope"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("nope" in e and "essays" in e for e in errors))

    def test_draft_only_tag_does_not_count(self) -> None:
        # A tag that appears only on drafts must not satisfy primary_tags.
        draft = GARDEN_NOTE.replace("draft: false", "draft: true").replace(
            '["memory", "narrative"]', '["draft-only"]'
        )
        self.repo.write_garden("draft-note", draft)
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["draft-only"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("draft-only" in e for e in errors))

    def test_invalid_top_k_string_fails(self) -> None:
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: "ten"\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("primary_top_k" in e for e in errors))

    def test_invalid_top_k_zero_fails(self) -> None:
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: 0\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("primary_top_k" in e for e in errors))

    def test_invalid_top_k_negative_fails(self) -> None:
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: -1\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("primary_top_k" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
