"""Tests for check_library_shelves.py — run with:
   python3 -m unittest tools/test_check_library_shelves.py -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_library_shelves as lint  # noqa: E402


MEDIA_YAML_GOOD = """media:
  - key: reading
    label: "Reading"
    glyph: book-open
    cover_aspect: portrait
  - key: listening
    label: "Listening"
    glyph: music
    cover_aspect: square
"""

SHELVES_YAML_GOOD = """hero: invisible-cities

shelves:
  - title: "Recently finished"
    intro: "Things I closed the cover on."
    tag: finished
  - title: "Field of game design"
    intro: "Books and papers."
    items:
      - invisible-cities
      - lorem-ipsum-ii
"""

READING_YAML = """items:
  - slug: invisible-cities
    title: "Invisible Cities"
    creator: "Italo Calvino"
    year: 1972
    media_type: book
    status: reading
    last_modified: 2026-04-22
    tags: [fiction, finished]
  - slug: lorem-ipsum-ii
    title: "Lorem Ipsum II"
    creator: "Author II"
    year: 2024
    media_type: book
    status: finished
    last_modified: 2026-05-01
    tags: [non-fiction, finished]
"""

LISTENING_YAML = """items: []
"""


def make_project(td: Path, *, media: str | None, shelves: str | None,
                 reading: str | None, listening: str | None,
                 stubs: dict[str, str] | None = None) -> Path:
    root = td / "project"
    (root / "data").mkdir(parents=True)
    (root / "assets" / "images" / "icons").mkdir(parents=True)
    if media is not None:
        (root / "data" / "library-media.yaml").write_text(media)
    if shelves is not None:
        (root / "data" / "library-shelves.yaml").write_text(shelves)
    if reading is not None:
        (root / "data" / "reading.yaml").write_text(reading)
    if listening is not None:
        (root / "data" / "listening.yaml").write_text(listening)
    # Touch glyph files mentioned in media yaml
    for fname in ("book-open.svg", "music.svg"):
        (root / "assets" / "images" / "icons" / fname).write_text("<!-- stub -->")
    if stubs:
        for slug, body in stubs.items():
            path = root / "content" / "library" / "shelves" / slug / "_index.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
    return root


class LibraryShelvesTest(unittest.TestCase):

    def test_happy_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=SHELVES_YAML_GOOD,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            self.assertEqual(errors, [])

    def test_missing_media_yaml_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=None, shelves=SHELVES_YAML_GOOD,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            self.assertTrue(any("library-media" in e for e in errors))

    def test_missing_shelves_yaml_is_ok(self):
        """Shelves yaml is optional — soft fall-back is documented behaviour."""
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=None,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            self.assertEqual(errors, [])

    def test_shelf_with_both_tag_and_items_fails(self):
        bad = """hero: invisible-cities

shelves:
  - title: "Conflicted"
    intro: "Has both"
    tag: finished
    items:
      - invisible-cities
"""
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=bad,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            self.assertTrue(any("both tag and items" in e.lower() or "exactly one" in e.lower() for e in errors))

    def test_unresolved_hero_slug_warns(self):
        bad = """hero: nonexistent-slug

shelves:
  - title: "OK"
    intro: "Fine"
    tag: finished
"""
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=bad,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            self.assertTrue(any("nonexistent-slug" in e or "hero" in e.lower() for e in errors))

    def test_slug_list_with_bad_slug_fails(self):
        bad = """shelves:
  - title: "Bad"
    intro: "Has unresolvable slug"
    items:
      - does-not-exist
"""
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=bad,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            self.assertTrue(any("does-not-exist" in e for e in errors))

    def test_long_shelf_requires_stub(self):
        # 13-item slug list — stub required.
        slug_lines = "\n".join(f"      - lorem-ipsum-{n}" for n in range(13))
        bad = f"""shelves:
  - title: "Long shelf"
    intro: "Has 13 items"
    items:
{slug_lines}
"""
        # Provide a reading yaml that has those slugs so they resolve
        many_reading = "items:\n" + "\n".join(
            f"  - slug: lorem-ipsum-{n}\n    title: \"T{n}\"\n    creator: \"C\"\n    year: 2024\n    media_type: book\n    status: reading\n    last_modified: 2026-05-01\n    tags: [t]"
            for n in range(13)
        )
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=bad,
                                reading=many_reading, listening=LISTENING_YAML, stubs=None)
            errors = lint.lint_library_shelves(root)
            self.assertTrue(any("stub" in e.lower() and "long" in e.lower() or "_index.md" in e for e in errors))

    def test_orphan_stub_fails(self):
        # Stub exists for a shelf that doesn't appear in yaml
        stub = """---
title: "Orphan"
shelf: orphan
type: library-shelf
---
"""
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=SHELVES_YAML_GOOD,
                                reading=READING_YAML, listening=LISTENING_YAML,
                                stubs={"orphan": stub})
            errors = lint.lint_library_shelves(root)
            self.assertTrue(any("orphan" in e.lower() for e in errors))


if __name__ == "__main__":
    unittest.main()
