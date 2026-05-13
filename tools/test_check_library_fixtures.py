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


if __name__ == "__main__":
    unittest.main()
