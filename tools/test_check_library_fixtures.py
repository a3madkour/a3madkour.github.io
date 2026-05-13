"""Tests for check_library_fixtures.py — run with:
   python3 -m unittest tools/test_check_library_fixtures.py -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_library_fixtures as lint  # noqa: E402


YAML_VALID = """\
items:
  - slug: invisible-cities
    title: Invisible Cities
    creator: Italo Calvino
    year: 1972
    media_type: book
    status: reading
    started: 2025-12-15
    finished: null
    spoiler_level: light
    last_modified: 2026-04-22
    cite_key: calvino1972cities
    canonical_url: "https://example.com/invisible-cities"
    note_slug: invisible-cities
    preview: "Re-reading for the procedural narrative paper."
    tags: [fiction, italian, procedural-narrative]
    extras:
      progress_pct: 51
      progress_label: "p. 84 / 165"
  - slug: another-book
    title: Another Book
    creator: Author Two
    year: 2020
    media_type: book
    status: finished
    finished: 2026-02-10
    last_modified: 2026-02-11
    note_slug: null
    tags: []
"""


class ParserTests(unittest.TestCase):
    def test_parse_returns_two_items(self):
        items = lint.parse_library_yaml(YAML_VALID)
        self.assertEqual(len(items), 2)

    def test_parse_first_item_fields(self):
        items = lint.parse_library_yaml(YAML_VALID)
        first = items[0]
        self.assertEqual(first["slug"], "invisible-cities")
        self.assertEqual(first["title"], "Invisible Cities")
        self.assertEqual(first["year"], 1972)
        self.assertIs(first["finished"], None)
        self.assertEqual(first["tags"], ["fiction", "italian", "procedural-narrative"])
        self.assertEqual(first["extras"], {"progress_pct": 51, "progress_label": "p. 84 / 165"})

    def test_parse_second_item_empty_tags(self):
        items = lint.parse_library_yaml(YAML_VALID)
        second = items[1]
        self.assertEqual(second["tags"], [])
        self.assertIs(second["note_slug"], None)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def _run(self, file_name: str, text: str) -> list[str]:
        return lint.lint_yaml_file(file_name, text)[0]

    def _run_with_warnings(self, file_name: str, text: str) -> tuple[list[str], list[str]]:
        return lint.lint_yaml_file(file_name, text)

    def test_valid_reading_passes(self):
        text = """\
items:
  - slug: invisible-cities
    title: Invisible Cities
    creator: Italo Calvino
    year: 1972
    media_type: book
    status: reading
    started: 2025-12-15
    last_modified: 2026-04-22
    tags: [fiction]
"""
        self.assertEqual(self._run("reading.yaml", text), [])

    def test_listening_rejects_book_media_type(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: finished
    finished: 2026-02-10
    last_modified: 2026-02-11
    tags: []
"""
        errs = self._run("listening.yaml", text)
        self.assertTrue(any("media_type='book' not allowed" in e for e in errs), errs)

    def test_playing_rejects_unknown_status(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: game
    status: bogus
    last_modified: 2026-02-11
    tags: []
"""
        errs = self._run("playing.yaml", text)
        self.assertTrue(any("status='bogus'" in e for e in errs), errs)

    def test_finished_status_requires_finished_date(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: finished
    last_modified: 2026-02-11
    tags: []
"""
        errs = self._run("reading.yaml", text)
        self.assertTrue(any("finished date required" in e for e in errs), errs)

    def test_progress_pct_out_of_range_rejected(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: reading
    started: 2025-12-15
    last_modified: 2026-02-11
    tags: []
    extras:
      progress_pct: 150
"""
        errs = self._run("reading.yaml", text)
        self.assertTrue(any("progress_pct" in e and "0..100" in e for e in errs), errs)

    def test_unknown_extras_key_rejected(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: reading
    started: 2025-12-15
    last_modified: 2026-02-11
    tags: []
    extras:
      bogus_key: 1
"""
        errs = self._run("reading.yaml", text)
        self.assertTrue(any("bogus_key" in e for e in errs), errs)

    def test_duplicate_slug_rejected(self):
        text = """\
items:
  - slug: dup
    title: A
    creator: X
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-02-11
    tags: []
  - slug: dup
    title: B
    creator: Y
    year: 2021
    media_type: book
    status: queued
    last_modified: 2026-02-11
    tags: []
"""
        errs = self._run("reading.yaml", text)
        self.assertTrue(any("duplicate slug" in e for e in errs), errs)

    def test_bad_date_format_rejected(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: queued
    last_modified: not-a-date
    tags: []
"""
        errs = self._run("reading.yaml", text)
        self.assertTrue(any("last_modified" in e and "YYYY-MM-DD" in e for e in errs), errs)
        # Field name should appear once, not twice (regression check).
        date_errs = [e for e in errs if "YYYY-MM-DD" in e]
        for e in date_errs:
            self.assertEqual(e.count("last_modified"), 1, f"field name doubled: {e!r}")

    def test_integer_slug_rejected(self):
        # Regression: int slug used to silently bypass all validation.
        text = """\
items:
  - slug: 123
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-02-11
    tags: []
"""
        errs = self._run("reading.yaml", text)
        self.assertTrue(any("slug must be a string" in e for e in errs), errs)

    def test_empty_value_field_parses_to_none(self):
        # Regression: bare `started:` used to produce {} (a nested dict)
        # because NESTED_HEADER_RE matched first. Now only `extras:` opens
        # a nested mapping; other empty values become None.
        items = lint.parse_library_yaml("""\
items:
  - slug: t
    title: T
    creator: X
    year: 2020
    media_type: book
    status: queued
    started:
    last_modified: 2026-04-22
    tags: []
""")
        self.assertEqual(len(items), 1)
        self.assertIs(items[0]["started"], None)
        self.assertEqual(items[0]["last_modified"].isoformat(), "2026-04-22")

    def test_active_count_over_3_emits_warning_not_error(self):
        # Spec §3.7: 4+ active is "not currently expected" but not a violation.
        text = """\
items:
  - slug: a
    title: A
    creator: X
    year: 2020
    media_type: book
    status: reading
    started: 2025-12-15
    last_modified: 2026-04-22
    tags: []
  - slug: b
    title: B
    creator: X
    year: 2020
    media_type: book
    status: reading
    started: 2025-12-15
    last_modified: 2026-04-22
    tags: []
  - slug: c
    title: C
    creator: X
    year: 2020
    media_type: book
    status: reading
    started: 2025-12-15
    last_modified: 2026-04-22
    tags: []
  - slug: d
    title: D
    creator: X
    year: 2020
    media_type: book
    status: reading
    started: 2025-12-15
    last_modified: 2026-04-22
    tags: []
"""
        errors, warnings = self._run_with_warnings("reading.yaml", text)
        self.assertEqual(errors, [])
        self.assertTrue(any("4 active items" in w for w in warnings), warnings)


if __name__ == "__main__":
    unittest.main()
