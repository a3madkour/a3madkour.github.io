from __future__ import annotations
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import fetch_library_covers as fc

class CliTests(unittest.TestCase):
    def test_default_medium_is_all(self):
        args = fc.parse_args([])
        self.assertEqual(args.medium, "all")
        self.assertFalse(args.force)
        self.assertFalse(args.dry_run)

    def test_medium_flag(self):
        args = fc.parse_args(["--medium", "book"])
        self.assertEqual(args.medium, "book")

    def test_force_flag(self):
        args = fc.parse_args(["--force"])
        self.assertTrue(args.force)

    def test_dry_run_flag(self):
        args = fc.parse_args(["--dry-run"])
        self.assertTrue(args.dry_run)

class PickSourceTests(unittest.TestCase):
    def test_cover_file_wins(self):
        item = {"slug": "x", "media_type": "book",
                "extras": {"cover_file": "x.jpg", "cover_url": "https://e/x", "isbn": "9780000000002"}}
        s = fc.pick_source(item)
        self.assertEqual(s, ("cover_file", "x.jpg"))

    def test_cover_url_when_no_file(self):
        item = {"slug": "x", "media_type": "book",
                "extras": {"cover_url": "https://e/x", "isbn": "9780000000002"}}
        self.assertEqual(fc.pick_source(item), ("cover_url", "https://e/x"))

    def test_isbn_book(self):
        item = {"slug": "x", "media_type": "book", "extras": {"isbn": "9780000000002"}}
        self.assertEqual(fc.pick_source(item), ("isbn", "9780000000002"))

    def test_mbid_album(self):
        item = {"slug": "x", "media_type": "album",
                "extras": {"musicbrainz_release_group": "abc-123"}}
        self.assertEqual(fc.pick_source(item), ("mbid", "abc-123"))

    def test_igdb_game(self):
        item = {"slug": "x", "media_type": "game", "extras": {"igdb_id": 1942}}
        self.assertEqual(fc.pick_source(item), ("igdb_id", 1942))

    def test_tmdb_film(self):
        item = {"slug": "x", "media_type": "film", "extras": {"tmdb_id": 95396}}
        self.assertEqual(fc.pick_source(item), ("tmdb_id", 95396))

    def test_no_source_returns_none(self):
        item = {"slug": "x", "media_type": "book", "extras": {}}
        self.assertIsNone(fc.pick_source(item))

    def test_no_extras_returns_none(self):
        item = {"slug": "x", "media_type": "book"}
        self.assertIsNone(fc.pick_source(item))


class LoadLeafTests(unittest.TestCase):
    def test_loads_listening(self):
        items = fc.load_leaf("listening")
        self.assertTrue(len(items) >= 1)
        self.assertIn("slug", items[0])

    def test_loads_reading_with_extras(self):
        items = fc.load_leaf("reading")
        wizard = next((i for i in items if i.get("slug") == "wizard-of-oz"), None)
        self.assertIsNotNone(wizard)
        self.assertEqual(wizard["extras"]["isbn"], "9780486291161")


class CoverFileDispatchTests(unittest.TestCase):
    def test_existing_file_is_ok(self):
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            (covers / "wizard.jpg").write_bytes(b"\xff\xd8\xff\xd9")  # JPEG header
            result = fc.dispatch_cover_file(slug="wizard-of-oz",
                                            cover_file="wizard.jpg",
                                            covers_dir=covers)
            self.assertEqual(result.kind, "cover_file")
            self.assertEqual(result.path.name, "wizard.jpg")
            self.assertTrue(result.cached)

    def test_missing_file_is_error(self):
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_cover_file(slug="x",
                                            cover_file="missing.jpg",
                                            covers_dir=covers)
            self.assertEqual(result.kind, "cover_file")
            self.assertFalse(result.cached)
            self.assertIn("not found", result.error)


if __name__ == "__main__":
    unittest.main()
