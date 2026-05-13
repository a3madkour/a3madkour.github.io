from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import check_library_covers as clc

class SchemaTests(unittest.TestCase):
    def test_valid_isbn_passes(self):
        errs, warns = clc.check_schema([{"slug":"x","media_type":"book",
                                         "extras":{"isbn":"9780000000002"}}])
        self.assertEqual(errs, [])

    def test_invalid_isbn_fails(self):
        errs, _ = clc.check_schema([{"slug":"x","media_type":"book",
                                      "extras":{"isbn":"abc"}}])
        self.assertTrue(any("isbn" in e for e in errs))

    def test_negative_igdb_fails(self):
        errs, _ = clc.check_schema([{"slug":"x","media_type":"game",
                                      "extras":{"igdb_id":-5}}])
        self.assertTrue(any("igdb_id" in e for e in errs))

    def test_cover_file_with_slash_fails(self):
        errs, _ = clc.check_schema([{"slug":"x","media_type":"book",
                                      "extras":{"cover_file":"../escape.jpg"}}])
        self.assertTrue(any("cover_file" in e for e in errs))

    def test_no_extras_passes_silently(self):
        errs, warns = clc.check_schema([{"slug":"lorem","media_type":"book"}])
        self.assertEqual((errs, warns), ([], []))

class CacheCoverageTests(unittest.TestCase):
    def test_missing_cache_file_warns(self):
        with tempfile.TemporaryDirectory() as td:
            items = [{"slug":"x","media_type":"book",
                      "extras":{"isbn":"9780000000002"}}]
            warns = clc.check_cache_coverage(items, covers_dir=Path(td))
            self.assertTrue(any("x" in w for w in warns))

    def test_cover_file_present_no_warning(self):
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            (covers / "x.jpg").write_bytes(b"j")
            items = [{"slug":"x","media_type":"book",
                      "extras":{"cover_file":"x.jpg"}}]
            self.assertEqual(clc.check_cache_coverage(items, covers_dir=covers), [])

    def test_no_identifier_passes_silently(self):
        with tempfile.TemporaryDirectory() as td:
            items = [{"slug":"lorem","media_type":"book"}]
            self.assertEqual(clc.check_cache_coverage(items, covers_dir=Path(td)), [])

class AuditConsistencyTests(unittest.TestCase):
    def test_sha_match_no_warning(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            body = b"abc"
            (covers / "x.jpg").write_bytes(body)
            audit = {"x":{"source_kind":"cover_url","source":"u","fetched_at":"2026-05-12T00:00:00Z","sha256":hashlib.sha256(body).hexdigest()}}
            self.assertEqual(clc.check_audit_consistency(audit, covers_dir=covers), [])

    def test_sha_mismatch_warns(self):
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            (covers / "x.jpg").write_bytes(b"abc")
            audit = {"x":{"source_kind":"cover_url","source":"u","fetched_at":"2026-05-12T00:00:00Z","sha256":"deadbeef"}}
            warns = clc.check_audit_consistency(audit, covers_dir=covers)
            self.assertTrue(any("sha" in w.lower() for w in warns))

    def test_orphan_audit_entry_warns(self):
        with tempfile.TemporaryDirectory() as td:
            audit = {"missing":{"source_kind":"cover_url","source":"u","fetched_at":"2026-05-12T00:00:00Z","sha256":"x"}}
            warns = clc.check_audit_consistency(audit, covers_dir=Path(td))
            self.assertTrue(any("missing" in w for w in warns))

class FreshnessTests(unittest.TestCase):
    def test_stale_entry_warns(self):
        audit = {"x":{"source_kind":"cover_url","source":"u",
                       "fetched_at":"2020-01-01T00:00:00Z","sha256":"x"}}
        warns = clc.check_freshness(audit, stale_days=365, now_iso="2026-05-12T00:00:00Z")
        self.assertTrue(any("stale" in w.lower() for w in warns))

    def test_fresh_entry_no_warning(self):
        audit = {"x":{"source_kind":"cover_url","source":"u",
                       "fetched_at":"2026-05-01T00:00:00Z","sha256":"x"}}
        warns = clc.check_freshness(audit, stale_days=365, now_iso="2026-05-12T00:00:00Z")
        self.assertEqual(warns, [])

if __name__ == "__main__":
    unittest.main()
