"""Unit tests for tools/check_pagefind_meta.py.

The linter validates that each rendered HTML page under public/ has:
  1. data-pagefind-body on the <main> element.
  2. data-pagefind-meta="section:..." on SOME element (one pair per element,
     multiple elements allowed — all are collected into one dict).
  3. The 'section' value matches the page's URL prefix (essays, garden,
     research, works, library, about, home).
  4. At least one data-pagefind-filter="section:..." element so the search
     modal's section filter chips work.

Tests run against synthetic HTML strings, not a real public/ directory.
"""

import unittest
from pathlib import Path
import tempfile

from check_pagefind_meta import (
    parse_meta,
    parse_filters,
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

    def test_blog(self):
        self.assertEqual(section_from_path("/blog/"), "blog")

    def test_credits(self):
        self.assertEqual(section_from_path("/credits/"), "credits")


class TestParseMeta(unittest.TestCase):
    def test_extracts_section_key_single_element(self):
        # Each element carries exactly one key:value pair (new contract).
        html = '<span data-pagefind-meta="section:essays" hidden></span>'
        meta = parse_meta(html)
        self.assertEqual(meta.get("section"), "essays")

    def test_collects_multiple_separate_elements(self):
        # Multiple elements — each with one pair — are all collected.
        html = (
            '<span data-pagefind-meta="section:essays" hidden></span>'
            '<span data-pagefind-meta="date:2026-01-01" hidden></span>'
        )
        meta = parse_meta(html)
        self.assertEqual(meta.get("section"), "essays")
        self.assertEqual(meta.get("date"), "2026-01-01")

    def test_missing_meta_returns_empty_dict(self):
        html = "<article>x</article>"
        self.assertEqual(parse_meta(html), {})

    def test_first_key_wins_on_collision(self):
        # If two elements carry the same key, first one wins.
        html = (
            '<span data-pagefind-meta="section:essays" hidden></span>'
            '<span data-pagefind-meta="section:garden" hidden></span>'
        )
        meta = parse_meta(html)
        self.assertEqual(meta.get("section"), "essays")

    def test_extracts_unquoted_value(self):
        # Hugo's minifier emits unquoted attrs for simple values:
        # data-pagefind-meta=section:home  (no surrounding quotes)
        html = '<span data-pagefind-meta=section:home hidden></span>'
        meta = parse_meta(html)
        self.assertEqual(meta.get("section"), "home")

    def test_multi_key_multi_element_unquoted(self):
        # Multiple unquoted single-key elements (minified HTML).
        html = (
            '<span data-pagefind-meta=section:works hidden></span>'
            '<span data-pagefind-meta=medium:game hidden></span>'
        )
        meta = parse_meta(html)
        self.assertEqual(meta.get("section"), "works")
        self.assertEqual(meta.get("medium"), "game")


class TestParseFilters(unittest.TestCase):
    def test_extracts_section_filter(self):
        html = '<span data-pagefind-filter="section:essays" hidden></span>'
        filters = parse_filters(html)
        self.assertIn("section:essays", filters)

    def test_extracts_multiple_filters(self):
        html = (
            '<span data-pagefind-filter="section:works" hidden></span>'
            '<span data-pagefind-filter="medium:game" hidden></span>'
        )
        filters = parse_filters(html)
        self.assertIn("section:works", filters)
        self.assertIn("medium:game", filters)

    def test_no_filters_returns_empty(self):
        html = "<article>x</article>"
        self.assertEqual(parse_filters(html), [])

    def test_extracts_unquoted_filter(self):
        html = '<span data-pagefind-filter=section:home hidden></span>'
        filters = parse_filters(html)
        self.assertIn("section:home", filters)


class TestValidatePage(unittest.TestCase):
    def _write_html(self, dirpath: Path, url: str, html: str) -> Path:
        # url like "/essays/example-1/" → file at <dirpath>/essays/example-1/index.html
        rel = url.strip("/")
        target = dirpath / rel / "index.html" if rel else dirpath / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        return target

    def _valid_essay_html(self) -> str:
        # New contract: separate elements, one key each, plus a filter attr.
        return (
            "<html><body><main data-pagefind-body>"
            '<span data-pagefind-meta="section:essays" hidden></span>'
            '<span data-pagefind-meta="date:2026-01-01" hidden></span>'
            '<span data-pagefind-filter="section:essays" hidden></span>'
            "<article>body</article>"
            "</main></body></html>"
        )

    def test_valid_page_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            f = self._write_html(public, "/essays/example-1/", self._valid_essay_html())
            errs = validate_page(f, public)
            self.assertEqual(errs, [])

    def test_missing_pagefind_body_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            html = (
                "<html><body><main>"
                '<span data-pagefind-meta="section:essays" hidden></span>'
                '<span data-pagefind-filter="section:essays" hidden></span>'
                "<article>body</article>"
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
                '<span data-pagefind-meta="section:garden" hidden></span>'
                '<span data-pagefind-filter="section:garden" hidden></span>'
                "<article>body</article>"
                "</main></body></html>"
            )
            f = self._write_html(public, "/essays/example-1/", html)
            errs = validate_page(f, public)
            self.assertTrue(any("section mismatch" in e.lower() for e in errs))

    def test_missing_filter_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            # meta present but no filter attr
            html = (
                "<html><body><main data-pagefind-body>"
                '<span data-pagefind-meta="section:essays" hidden></span>'
                "<article>body</article>"
                "</main></body></html>"
            )
            f = self._write_html(public, "/essays/example-1/", html)
            errs = validate_page(f, public)
            self.assertTrue(any("pagefind-filter" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
