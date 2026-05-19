"""Tests for check_poetry_synced.py — run with:
   python3 -m unittest tools/test_check_poetry_synced.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_poetry_synced as lint  # noqa: E402  # pyright: ignore[reportMissingImports]


def poem(body: str, *, audio_url: str | None = None, draft: bool = False) -> str:
    fm = [
        "---",
        'title: "Synced"',
        "date: 2026-05-18",
        "lastmod: 2026-05-18",
        f"draft: {'true' if draft else 'false'}",
        "lines: 4",
    ]
    if audio_url is not None:
        fm.append(f'audio_url: "{audio_url}"')
    fm.append("---")
    return "\n".join(fm) + "\n\n" + body


HAPPY = poem("[00:01]Lorem ipsum dolor\n[00:04]sit amet consectetur\n")
MIDLINE = poem("[00:01]Sed do [00:02]eiusmod [00:03]tempor\nincididunt ut labore\n")


class TempRepo:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())

    def write(self, slug: str, text: str, *, asset: str | None = None) -> Path:
        d = self.root / "content" / "works" / "poetry" / slug
        d.mkdir(parents=True)
        p = d / "index.md"
        p.write_text(text)
        if asset is not None:
            (d / asset).write_bytes(b"\x00")
        return p

    def cleanup(self) -> None:
        shutil.rmtree(self.root)


class CheckPoetrySyncedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    # --- happy path ---

    def test_happy_path_passes(self) -> None:
        p = self.repo.write("happy", HAPPY)
        errs, warns = lint.lint_file(p)
        self.assertEqual(errs, [])
        self.assertEqual(warns, [])

    def test_midline_markers_pass(self) -> None:
        p = self.repo.write("midline", MIDLINE)
        errs, warns = lint.lint_file(p)
        self.assertEqual(errs, [])

    def test_poem_without_markers_is_skipped(self) -> None:
        p = self.repo.write("plain", poem("Lorem ipsum\ndolor sit amet\n"))
        errs, warns = lint.lint_file(p)
        self.assertEqual(errs, [])
        self.assertEqual(warns, [])

    # --- (1) marker shape ---

    def test_seconds_over_59_fails(self) -> None:
        p = self.repo.write("badsec", poem("[00:60]Lorem ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("[00:60]" in e and "seconds" in e for e in errs), errs)

    def test_seconds_must_be_two_digits(self) -> None:
        p = self.repo.write("shortsec", poem("[03:5]Lorem ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("[03:5]" in e for e in errs), errs)

    def test_fractional_max_two_digits(self) -> None:
        p = self.repo.write("longfrac", poem("[00:03.123]Lorem ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("[00:03.123]" in e for e in errs), errs)

    def test_fractional_one_or_two_digits_ok(self) -> None:
        p = self.repo.write("frac", poem("[00:03.5]Lorem\n[00:04.50]ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertEqual(errs, [])

    # --- (2) placement ---

    def test_embedded_marker_without_separator_fails(self) -> None:
        p = self.repo.write("embedded", poem("Lorem[00:03]ipsum dolor\n"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("placement" in e.lower() or "whitespace" in e.lower() for e in errs), errs)

    def test_leading_whitespace_marker_ok(self) -> None:
        p = self.repo.write("indent", poem("   [00:03]Lorem ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertEqual(errs, [])

    # --- (3) audio-url validity ---

    def test_absolute_audio_url_ok(self) -> None:
        p = self.repo.write("abs", poem("[00:01]Lorem\n", audio_url="https://example.com/r.mp3"))
        errs, _ = lint.lint_file(p)
        self.assertEqual(errs, [])

    def test_absolute_audio_url_malformed_fails(self) -> None:
        p = self.repo.write("badabs", poem("[00:01]Lorem\n", audio_url="ftp://example.com/r.mp3"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("audio_url" in e for e in errs), errs)

    def test_relative_audio_url_missing_file_fails(self) -> None:
        p = self.repo.write("relmiss", poem("[00:01]Lorem\n", audio_url="reading.mp3"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("audio_url" in e and "reading.mp3" in e for e in errs), errs)

    def test_relative_audio_url_present_file_ok(self) -> None:
        p = self.repo.write("relok", poem("[00:01]Lorem\n", audio_url="reading.mp3"), asset="reading.mp3")
        errs, _ = lint.lint_file(p)
        self.assertEqual(errs, [])

    # --- (4) escape round-trip ---

    def test_escaped_marker_not_counted_and_not_shape_checked(self) -> None:
        # \[00:99] is escaped → literal text, must NOT trip shape (seconds>59)
        # and must NOT alone make the poem "synced".
        p = self.repo.write("esc", poem("Lorem ipsum \\[00:99] dolor sit amet\n"))
        errs, warns = lint.lint_file(p)
        self.assertEqual(errs, [])
        self.assertEqual(warns, [])

    def test_escaped_marker_alongside_real_marker(self) -> None:
        p = self.repo.write("escmix", poem("[00:01]Lorem \\[00:99] ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertEqual(errs, [])

    # --- (5) monotonic ordering (warning only) ---

    def test_non_monotonic_warns_but_passes(self) -> None:
        p = self.repo.write("nonmono", poem("[00:10]Lorem ipsum\n[00:04]dolor sit\n"))
        errs, warns = lint.lint_file(p)
        self.assertEqual(errs, [])
        self.assertTrue(any("monoton" in w.lower() for w in warns), warns)

    # --- (6) non-empty poem ---

    def test_empty_poem_fails(self) -> None:
        p = self.repo.write("empty", poem("[00:01]\n"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("no content" in e.lower() or "empty" in e.lower() for e in errs), errs)

    # --- runner ---

    def test_run_aggregates_and_returns_rc(self) -> None:
        self.repo.write("ok", HAPPY)
        self.repo.write("bad", poem("[00:60]Lorem ipsum\n"))
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(errors)

    def test_run_passes_clean_tree(self) -> None:
        self.repo.write("ok", HAPPY)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0)
        self.assertEqual(errors, [])

    def test_run_empty_section_passes(self) -> None:
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0)
        self.assertEqual(errors, [])

    def test_draft_poem_still_linted(self) -> None:
        # synced markup must be valid even in drafts (they ship in dev server).
        p = self.repo.write("draftbad", poem("[00:60]Lorem ipsum\n", draft=True))
        errs, _ = lint.lint_file(p)
        self.assertTrue(errs)


if __name__ == "__main__":
    unittest.main()
