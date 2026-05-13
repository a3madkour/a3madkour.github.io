"""Tests for check_library_links.py — run with:
   python3 -m unittest tools/test_check_library_links.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_library_links as lint  # noqa: E402


GARDEN_NOTE = """\
---
title: "Test Note"
draft: false
last_modified: 2026-01-01
growth_stage: seedling
---

Body.
"""

CITATIONS_YAML = """\
citations:
  test-key:
    authors: ["Doe"]
    year: 2020
    title: "Test"
    venue: "Journal"
"""

LIB_VALID = """\
items:
  - slug: row-with-note
    title: A
    creator: X
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    note_slug: real-note
  - slug: row-with-citation
    title: B
    creator: Y
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    cite_key: test-key
  - slug: row-with-url
    title: C
    creator: Z
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    canonical_url: "https://example.com/c"
"""

LIB_BAD_NOTE = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    note_slug: nonexistent-note
"""

LIB_BAD_CITE = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    cite_key: missing-key
"""

LIB_BAD_URL = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    canonical_url: "http://insecure.example.com"
"""


class LinksLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "content" / "garden" / "real-note").mkdir(parents=True)
        (self.tmp / "content" / "garden" / "real-note" / "index.md").write_text(GARDEN_NOTE)
        (self.tmp / "data").mkdir()
        (self.tmp / "data" / "citations.yaml").write_text(CITATIONS_YAML)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, name: str, text: str):
        (self.tmp / "data" / name).write_text(text)

    def test_valid_links_pass(self):
        self._write("reading.yaml", LIB_VALID)
        rc, errs = lint.run(self.tmp)
        self.assertEqual(errs, [])
        self.assertEqual(rc, 0)

    def test_bad_note_slug_rejected(self):
        self._write("reading.yaml", LIB_BAD_NOTE)
        rc, errs = lint.run(self.tmp)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("nonexistent-note" in e for e in errs), errs)

    def test_missing_cite_key_rejected(self):
        self._write("reading.yaml", LIB_BAD_CITE)
        rc, errs = lint.run(self.tmp)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("missing-key" in e for e in errs), errs)

    def test_http_url_rejected(self):
        self._write("reading.yaml", LIB_BAD_URL)
        rc, errs = lint.run(self.tmp)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("canonical_url" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
