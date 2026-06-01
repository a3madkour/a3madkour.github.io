"""Tests for check_citations.py — run with:
   python3 -m unittest tools/test_check_citations.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_citations as lint  # noqa: E402


GARDEN_NOTE_PUBLISHED = """\
---
title: "Story atoms"
draft: false
last_modified: 2026-04-22
growth_stage: budding
---

Body.
"""

GARDEN_NOTE_DRAFT = """\
---
title: "Draft note"
draft: true
last_modified: 2026-04-22
growth_stage: seedling
---

Body.
"""


class CitationLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.garden = self.tmp / "content" / "garden"
        self.garden.mkdir(parents=True)
        self.data = self.tmp / "data"
        self.data.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write_garden(self, slug: str, body: str = GARDEN_NOTE_PUBLISHED) -> None:
        d = self.garden / slug
        d.mkdir()
        (d / "index.md").write_text(body)

    def _write_citations(self, yaml_text: str) -> Path:
        p = self.data / "citations.yaml"
        p.write_text(yaml_text)
        return p

    def test_happy_path_passes(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["Lastname, F."]
    year: 2020
    title: "Lorem ipsum"
    venue: "Journal of Examples"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(errors, [])

    def test_missing_authors_fails(self):
        self._write_citations("""\
citations:
  source-1:
    year: 2020
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("authors", errors[0])

    def test_missing_year_fails(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("year", errors[0])

    def test_missing_title_fails(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("title", errors[0])

    def test_missing_venue_fails(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("venue", errors[0])

    def test_empty_authors_list_rejected(self):
        self._write_citations("""\
citations:
  source-1:
    authors: []
    year: 2020
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("authors", errors[0])

    def test_year_as_string_rejected(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: "2020"
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("year", errors[0])

    def test_year_too_low_rejected(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 1499
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("year", errors[0])

    def test_year_too_high_rejected(self):
        from datetime import date
        too_high = date.today().year + 3
        self._write_citations(f"""\
citations:
  source-1:
    authors: ["A"]
    year: {too_high}
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("year", errors[0])

    def test_non_http_url_rejected(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    url: "ftp://example.invalid/x"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("url", errors[0])

    def test_unknown_field_rejected(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    year_published: 2020
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("year_published", errors[0])

    def test_bad_key_format_rejected(self):
        self._write_citations("""\
citations:
  Bad_Key:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("Bad_Key", errors[0])

    def test_notes_ref_resolved_passes(self):
        self._write_garden("story-atoms")
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    notes_ref: story-atoms
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(errors, [])

    def test_notes_ref_to_missing_slug_fails(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    notes_ref: does-not-exist
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("does-not-exist", errors[0])

    def test_notes_ref_to_draft_fails(self):
        self._write_garden("drafty", GARDEN_NOTE_DRAFT)
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    notes_ref: drafty
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("drafty", errors[0])
        self.assertIn("draft", errors[0].lower())

    def test_empty_notes_ref_ignored(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    notes_ref: ""
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(errors, [])

    def test_optional_doi_passes(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    doi: "10.1234/example"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(errors, [])

    def test_optional_type_passes(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    type: "book"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(errors, [])

    def test_all_new_optional_fields_pass(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    doi: "10.1234/example"
    publisher: "Acme Press"
    volume: "12"
    issue: "3"
    pages: "45-67"
    isbn: "978-0-123456-78-9"
    type: "inproceedings"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(errors, [])

    def test_unknown_field_still_fails(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    made_up_key: "x"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertTrue(any("made_up_key" in e for e in errors))


class TestKeyRegexLoosenedForBBT(unittest.TestCase):
    """F Task 1: KEY_RE must accept BBT-style camelCase keys like
    abelaConstructiveApproachGeneration2015 while still rejecting underscores
    and leading hyphens."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp())
        (self._tmp / "data").mkdir()
        (self._tmp / "content" / "garden").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self._tmp)

    def _write_yaml(self, key: str) -> Path:
        path = self._tmp / "data" / "citations.yaml"
        path.write_text(
            "citations:\n"
            f"  {key}:\n"
            '    authors: ["Lastname, F."]\n'
            "    year: 2020\n"
            '    title: "T"\n'
            '    venue: "V"\n'
        )
        return path

    def test_camel_case_bbt_key_accepted(self) -> None:
        p = self._write_yaml("abelaConstructiveApproachGeneration2015")
        errors = lint.lint_citations(p, self._tmp / "content" / "garden")
        self.assertEqual(errors, [], f"camelCase key wrongly rejected: {errors}")

    def test_underscore_key_rejected(self) -> None:
        p = self._write_yaml("bad_underscore_key")
        errors = lint.lint_citations(p, self._tmp / "content" / "garden")
        self.assertTrue(any("must match" in e for e in errors),
                        f"underscore key wrongly accepted: {errors}")

    def test_leading_hyphen_key_rejected(self) -> None:
        p = self._write_yaml("-leading-hyphen")
        errors = lint.lint_citations(p, self._tmp / "content" / "garden")
        self.assertTrue(any("must match" in e for e in errors),
                        f"leading-hyphen key wrongly accepted: {errors}")


if __name__ == "__main__":
    unittest.main()
