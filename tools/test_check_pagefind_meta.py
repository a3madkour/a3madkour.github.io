"""Unit tests for tools/check_pagefind_meta.py.

The linter validates that each rendered HTML page under public/ has:
  1. data-pagefind-body on the <main> element.
  2. data-pagefind-meta="section:..." on some element inside <main>.
  3. The 'section' value matches the page's URL prefix (essays, garden,
     research, works, library, about, home).

Tests run against synthetic HTML strings, not a real public/ directory.
"""

import unittest
from pathlib import Path
import tempfile

from check_pagefind_meta import (
    parse_meta,
    section_from_path,
    validate_page,
)


class TestSectionFromPath(unittest.TestCase):
    def test_homepage(self):
        self.assertEqual(section_from_path("/"), "home")

    def test_essays_index(self):
        self.assertEqual(section_from_path("/essays/"), "essays")

    def test_essay_post(self):
        self.assertEqual(section_from_path("/essays/example-1/"), "essays")

    def test_garden_note(self):
        self.assertEqual(section_from_path("/garden/example-2/"), "garden")

    def test_research_theme(self):
        self.assertEqual(
            section_from_path("/research/themes/example-theme/"), "research"
        )

    def test_works_game(self):
        self.assertEqual(
            section_from_path("/works/games/example-game/"), "works"
        )

    def test_library_leaf(self):
        self.assertEqual(section_from_path("/library/reading/"), "library")

    def test_about(self):
        self.assertEqual(section_from_path("/about/"), "about")


class TestParseMeta(unittest.TestCase):
    def test_extracts_section_key(self):
        html = '<article data-pagefind-meta="section:essays,date:2026-01-01">x</article>'
        meta = parse_meta(html)
        self.assertEqual(meta.get("section"), "essays")
        self.assertEqual(meta.get("date"), "2026-01-01")

    def test_missing_meta_returns_empty_dict(self):
        html = "<article>x</article>"
        self.assertEqual(parse_meta(html), {})

    def test_handles_whitespace_in_values(self):
        html = '<article data-pagefind-meta="section: essays , medium: book ">x</article>'
        meta = parse_meta(html)
        self.assertEqual(meta.get("section"), "essays")
        self.assertEqual(meta.get("medium"), "book")


class TestValidatePage(unittest.TestCase):
    def _write_html(self, dirpath: Path, url: str, html: str) -> Path:
        # url like "/essays/example-1/" → file at <dirpath>/essays/example-1/index.html
        rel = url.strip("/")
        target = dirpath / rel / "index.html" if rel else dirpath / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        return target

    def test_valid_page_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            html = (
                "<html><body><main data-pagefind-body>"
                '<article data-pagefind-meta="section:essays,date:2026-01-01">body</article>'
                "</main></body></html>"
            )
            f = self._write_html(public, "/essays/example-1/", html)
            errs = validate_page(f, public)
            self.assertEqual(errs, [])

    def test_missing_pagefind_body_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            html = (
                "<html><body><main>"
                '<article data-pagefind-meta="section:essays">body</article>'
                "</main></body></html>"
            )
            f = self._write_html(public, "/essays/example-1/", html)
            errs = validate_page(f, public)
            self.assertTrue(any("data-pagefind-body" in e for e in errs))

    def test_missing_section_meta_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            html = (
                "<html><body><main data-pagefind-body>"
                "<article>body without meta</article>"
                "</main></body></html>"
            )
            f = self._write_html(public, "/essays/example-1/", html)
            errs = validate_page(f, public)
            self.assertTrue(any("section" in e for e in errs))

    def test_section_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            html = (
                "<html><body><main data-pagefind-body>"
                '<article data-pagefind-meta="section:garden">body</article>'
                "</main></body></html>"
            )
            f = self._write_html(public, "/essays/example-1/", html)
            errs = validate_page(f, public)
            self.assertTrue(any("section mismatch" in e.lower() for e in errs))


if __name__ == "__main__":
    unittest.main()
