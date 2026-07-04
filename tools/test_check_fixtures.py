"""Tests for check_fixtures.py — run with: python3 -m unittest tools/test_check_fixtures.py -v"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_fixtures as lint  # noqa: E402  # pyright: ignore[reportMissingImports]


VALID_FRONTMATTER = """\
---
title: "Example essay one"
date: 2026-04-12
lastmod: 2026-04-20
draft: false
summary: "Lorem ipsum"
tags: ["a", "b"]
series: ""
series_order: 0
tile_size: large
featured: true
hero: hero.svg
toc: true
has_sidenotes: true
has_citations: true
has_footnotes: true
has_math: false
has_widgets: false
has_video_sync: false
---

Body. {{< cite "example-source-1" >}}
"""

VALID_CITATIONS = """\
citations:
  example-source-1:
    authors: ["Lastname"]
    year: 2020
    title: "x"
    venue: "y"
    url: "z"
    notes_ref: ""
"""


class TempRepo:
    """Minimal repo skeleton for testing the linter."""
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        (self.root / "data").mkdir()
        (self.root / "content" / "essays").mkdir(parents=True)

    def write_essay(self, slug: str, frontmatter_body: str, hero: bool = False) -> None:
        d = self.root / "content" / "essays" / slug
        d.mkdir(exist_ok=True)
        (d / "index.md").write_text(frontmatter_body)
        if hero:
            (d / "hero.svg").write_text("<svg/>")

    def write_citations(self, body: str) -> None:
        (self.root / "data" / "citations.yaml").write_text(body)

    def cleanup(self) -> None:
        shutil.rmtree(self.root)


class CheckFixturesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    def test_valid_fixture_passes(self) -> None:
        self.repo.write_essay("example-essay-one", VALID_FRONTMATTER, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected failures: {errors}")
        self.assertEqual(errors, [])

    def test_empty_essays_section_passes(self) -> None:
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0)
        self.assertEqual(errors, [])

    def test_missing_required_field_fails(self) -> None:
        broken = VALID_FRONTMATTER.replace('title: "Example essay one"\n', "")
        self.repo.write_essay("broken", broken)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("title" in e for e in errors))

    def test_invalid_tile_size_fails(self) -> None:
        broken = VALID_FRONTMATTER.replace("tile_size: large", "tile_size: huge")
        self.repo.write_essay("broken", broken, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("tile_size" in e for e in errors))

    def test_series_with_zero_order_fails(self) -> None:
        broken = VALID_FRONTMATTER.replace(
            'series: ""\nseries_order: 0',
            'series: "example-series"\nseries_order: 0',
        )
        self.repo.write_essay("broken", broken, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("series_order" in e for e in errors))

    def test_hero_declared_but_missing_fails(self) -> None:
        self.repo.write_essay("broken", VALID_FRONTMATTER, hero=False)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("hero.svg" in e for e in errors))

    def test_lastmod_before_date_fails(self) -> None:
        broken = VALID_FRONTMATTER.replace("lastmod: 2026-04-20", "lastmod: 2026-04-01")
        self.repo.write_essay("broken", broken, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("lastmod" in e for e in errors))

    def test_unknown_cite_key_fails(self) -> None:
        body = VALID_FRONTMATTER + '\n{{< cite "missing-key" >}}\n'
        self.repo.write_essay("broken", body, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("missing-key" in e for e in errors))

    def test_source_stream_accepted_on_essay(self) -> None:
        body = VALID_FRONTMATTER.replace(
            "has_video_sync: false\n",
            "has_video_sync: false\nsource_stream: 2026-04-10-example-live-coding-stream\n",
        )
        self.repo.write_essay("with-source-stream", body, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")


class FlowMappingDownloadsTest(unittest.TestCase):
    """Inline flow `downloads:' parses to a dict the validator can introspect."""

    def test_parses_inline_flow_downloads(self):
        fm = lint.parse_frontmatter(
            '---\n'
            'title: "X"\n'
            'multi_export: true\n'
            'downloads: {pdf: "x.pdf", word: "x.docx"}\n'
            '---\nbody\n'
        )
        self.assertIsInstance(fm, dict)
        self.assertEqual(fm.get("multi_export"), True)
        self.assertEqual(fm.get("downloads"), {"pdf": "x.pdf", "word": "x.docx"})

    def test_parses_pdf_only_downloads(self):
        fm = lint.parse_frontmatter(
            '---\n'
            'title: "X"\n'
            'multi_export: true\n'
            'downloads: {pdf: "x.pdf"}\n'
            '---\nbody\n'
        )
        self.assertEqual(fm.get("downloads"), {"pdf": "x.pdf"})


class MultiExportValidationTest(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def _fm_with(self, extra: str) -> str:
        return VALID_FRONTMATTER.replace(
            "has_video_sync: false\n",
            f"has_video_sync: false\n{extra}\n",
        )

    def test_multi_export_true_with_both_downloads_passes(self):
        body = self._fm_with(
            'multi_export: true\n'
            'downloads: {pdf: "example-essay-one.pdf", word: "example-essay-one.docx"}'
        )
        d = self.repo.root / "content" / "essays" / "example-essay-one"
        self.repo.write_essay("example-essay-one", body, hero=True)
        (d / "example-essay-one.pdf").write_bytes(b"%PDF-1.4 stub")
        (d / "example-essay-one.docx").write_bytes(b"PK stub")
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_multi_export_true_with_missing_pdf_fails(self):
        body = self._fm_with(
            'multi_export: true\n'
            'downloads: {pdf: "example-essay-one.pdf"}'
        )
        self.repo.write_essay("example-essay-one", body, hero=True)
        # Intentionally do NOT create the pdf file.
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("example-essay-one.pdf" in e for e in errors))

    def test_multi_export_true_without_downloads_fails(self):
        body = self._fm_with('multi_export: true')
        self.repo.write_essay("example-essay-one", body, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("downloads" in e for e in errors))

    def test_multi_export_false_passes(self):
        body = self._fm_with('multi_export: false')
        self.repo.write_essay("example-essay-one", body, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_unknown_downloads_key_fails(self):
        body = self._fm_with(
            'multi_export: true\n'
            'downloads: {epub: "x.epub"}'
        )
        self.repo.write_essay("example-essay-one", body, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("epub" in e for e in errors))


class ParseScalarQuotedCommaTest(unittest.TestCase):
    """R1.1: inline arrays must not split on commas inside quoted elements."""

    def test_single_quoted_element_with_comma_stays_one_item(self):
        # "Marquez, Gabriel" is ONE author, not two.
        self.assertEqual(
            lint.parse_scalar('["Marquez, Gabriel"]'),
            ["Marquez, Gabriel"],
        )

    def test_two_quoted_elements_one_containing_comma(self):
        self.assertEqual(
            lint.parse_scalar('["Lastname, F.", "Other"]'),
            ["Lastname, F.", "Other"],
        )

    def test_plain_unquoted_array_still_splits(self):
        # Regression: the simple case must keep working.
        self.assertEqual(lint.parse_scalar('["a", "b"]'), ["a", "b"])
        self.assertEqual(lint.parse_scalar("[TODO, DRAFT]"), ["TODO", "DRAFT"])

    def test_empty_array(self):
        self.assertEqual(lint.parse_scalar("[]"), [])


class ParseFrontmatterLineEndingTest(unittest.TestCase):
    """R1.1: CRLF and trailing-newline-free frontmatter must still parse
    (the ~14 linters that `if fm is None: continue` silently skip otherwise)."""

    def test_crlf_frontmatter_parses(self):
        fm = lint.parse_frontmatter("---\r\ntitle: X\r\ndraft: false\r\n---\r\nbody\r\n")
        self.assertIsInstance(fm, dict)
        self.assertEqual(fm.get("title"), "X")
        self.assertEqual(fm.get("draft"), False)

    def test_frontmatter_without_trailing_newline_parses(self):
        fm = lint.parse_frontmatter("---\ntitle: X\ndraft: false\n---")
        self.assertIsInstance(fm, dict)
        self.assertEqual(fm.get("title"), "X")


if __name__ == "__main__":
    unittest.main()
