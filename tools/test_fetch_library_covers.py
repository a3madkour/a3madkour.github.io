from __future__ import annotations
import hashlib
import io
import json
import sys
import tempfile
import unittest
import unittest.mock
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


class CoverUrlDispatchTests(unittest.TestCase):
    def test_downloads_to_slug_jpg(self):
        body = b"\xff\xd8\xff\xd9fake-jpeg"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        with unittest.mock.patch("urllib.request.urlopen", return_value=mock_resp) as urlopen, \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_cover_url(slug="wizard-of-oz",
                                            url="https://example.com/x.jpg",
                                            covers_dir=covers,
                                            ua="test-ua/0.1 (test@example.com)",
                                            timeout_s=10)
            self.assertEqual(result.kind, "cover_url")
            self.assertTrue(result.cached)
            self.assertEqual(result.path, covers / "wizard-of-oz.jpg")
            self.assertEqual(result.path.read_bytes(), body)
            # Verify UA header was set
            request = urlopen.call_args.args[0]
            self.assertEqual(request.get_header("User-agent"), "test-ua/0.1 (test@example.com)")
            self.assertEqual(result.sha256, hashlib.sha256(body).hexdigest())

    def test_4xx_returns_error_no_write(self):
        from urllib.error import HTTPError
        err = HTTPError("u", 404, "nf", {}, None)
        with unittest.mock.patch("urllib.request.urlopen", side_effect=err), \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_cover_url(slug="x", url="https://e/x.jpg",
                                            covers_dir=covers,
                                            ua="ua", timeout_s=10)
            self.assertFalse(result.cached)
            self.assertIn("404", result.error)
            self.assertFalse((covers / "x.jpg").exists())

    def test_5xx_retries_once_then_succeeds(self):
        from urllib.error import HTTPError
        body = b"ok"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        err = HTTPError("u", 503, "x", {}, None)
        with unittest.mock.patch("urllib.request.urlopen", side_effect=[err, mock_resp]) as urlopen, \
             unittest.mock.patch("time.sleep") as sleep, \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_cover_url(slug="x", url="https://e/x.jpg",
                                            covers_dir=covers, ua="ua", timeout_s=10)
            self.assertTrue(result.cached)
            self.assertEqual(urlopen.call_count, 2)
            sleep.assert_called()  # 2s backoff between attempts

    def test_5xx_retries_once_then_fails(self):
        from urllib.error import HTTPError
        err = HTTPError("u", 503, "x", {}, None)
        with unittest.mock.patch("urllib.request.urlopen", side_effect=[err, err]) as urlopen, \
             unittest.mock.patch("time.sleep"), \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_cover_url(slug="x", url="https://e/x.jpg",
                                            covers_dir=covers, ua="ua", timeout_s=10)
            self.assertFalse(result.cached)
            self.assertEqual(urlopen.call_count, 2)
            self.assertIn("503", result.error)


class OpenLibraryDispatchTests(unittest.TestCase):
    def test_isbn_url_construction(self):
        url = fc.openlibrary_url("9780486291161")
        self.assertEqual(url, "https://covers.openlibrary.org/b/isbn/9780486291161-L.jpg")

    def test_dispatch_isbn_downloads(self):
        body = b"jpeg-bytes"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        with unittest.mock.patch("urllib.request.urlopen", return_value=mock_resp) as urlopen, \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_isbn(slug="x", isbn="9780486291161",
                                       covers_dir=covers, ua="ua", timeout_s=10)
            self.assertTrue(result.cached)
            self.assertEqual(result.kind, "isbn")
            self.assertEqual(result.path, covers / "x.jpg")
            self.assertIn("9780486291161-L.jpg", urlopen.call_args.args[0].full_url)


class CoverArtArchiveDispatchTests(unittest.TestCase):
    def test_mbid_url_construction(self):
        url = fc.coverart_archive_url("abc-123-def")
        self.assertEqual(url, "https://coverartarchive.org/release-group/abc-123-def/front-500")

    def test_dispatch_mbid_downloads(self):
        body = b"jpeg-bytes"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        with unittest.mock.patch("urllib.request.urlopen", return_value=mock_resp), \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_mbid(slug="x", mbid="abc-123",
                                      covers_dir=covers, ua="ua", timeout_s=10)
            self.assertTrue(result.cached)
            self.assertEqual(result.kind, "mbid")


if __name__ == "__main__":
    unittest.main()
