"""Tests for check_icon_attribution.py — run with:
   python3 -m unittest tools/test_check_icon_attribution.py -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_icon_attribution as lint  # noqa: E402


LUCIDE_HEADER = '<!-- Lucide v1.16.0 — book-open · ISC License · see /THIRD_PARTY.md -->\n'
GOOD_SVG = LUCIDE_HEADER + '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0"/></svg>\n'
NO_HEADER_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0"/></svg>\n'

THIRD_PARTY_GOOD = """# Third-party assets

## Icons

**Lucide** — https://lucide.dev — ISC License
"""

THIRD_PARTY_NO_LUCIDE = """# Third-party assets

## Icons

Hand-authored only.
"""

EXCEPTIONS_YAML = """exceptions:
  - file: custom-mark.svg
    provenance: "Hand-drawn by author 2026-05-14"
"""


def make_project(td: Path, *, third_party: str | None, icons: dict[str, str], exceptions: str | None) -> Path:
    """Build a synthetic project root inside td. Return the root path."""
    root = td / "project"
    (root / "assets" / "images" / "icons").mkdir(parents=True)
    (root / "tools").mkdir(parents=True)
    if third_party is not None:
        (root / "THIRD_PARTY.md").write_text(third_party)
    for name, body in icons.items():
        target = root / "assets" / "images" / "icons" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    if exceptions is not None:
        (root / "tools" / ".icon-attribution-exceptions.yaml").write_text(exceptions)
    return root


class IconAttributionTest(unittest.TestCase):

    def test_happy_path_all_have_headers(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(
                Path(td),
                third_party=THIRD_PARTY_GOOD,
                icons={"book-open.svg": GOOD_SVG, "music.svg": GOOD_SVG},
                exceptions=None,
            )
            errors = lint.lint_icon_attribution(root)
            self.assertEqual(errors, [])

    def test_missing_third_party_md(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), third_party=None, icons={"book-open.svg": GOOD_SVG}, exceptions=None)
            errors = lint.lint_icon_attribution(root)
            self.assertTrue(any("THIRD_PARTY.md" in e for e in errors))

    def test_third_party_lacks_lucide_mention(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), third_party=THIRD_PARTY_NO_LUCIDE, icons={"book-open.svg": GOOD_SVG}, exceptions=None)
            errors = lint.lint_icon_attribution(root)
            self.assertTrue(any("Lucide" in e for e in errors))

    def test_svg_without_header(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), third_party=THIRD_PARTY_GOOD, icons={"bad.svg": NO_HEADER_SVG}, exceptions=None)
            errors = lint.lint_icon_attribution(root)
            self.assertTrue(any("bad.svg" in e for e in errors))

    def test_svg_in_exceptions_passes(self):
        with tempfile.TemporaryDirectory() as td:
            exc = "exceptions:\n  - file: bad.svg\n    provenance: \"OK\"\n"
            root = make_project(Path(td), third_party=THIRD_PARTY_GOOD, icons={"bad.svg": NO_HEADER_SVG}, exceptions=exc)
            errors = lint.lint_icon_attribution(root)
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
