"""Tests for check_anchor_link.py — run with: python3 -m unittest tools/test_check_anchor_link.py -v"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_anchor_link as lint  # noqa: E402  # pyright: ignore[reportMissingImports]


def page(body_inside_main: str) -> str:
    return (
        "<!doctype html><html><head><title>X</title></head><body>"
        "<header>chrome</header>"
        "<main>" + body_inside_main + "</main>"
        "<footer>chrome</footer>"
        "</body></html>"
    )


GOOD = page(
    '<h2 id="thm-ivt">Section</h2>'
    '<a class="anchor-link" href="#thm-ivt" aria-label="Copy link to Section"'
    ' data-anchor-title="Section">§</a>'
    "<p>body</p>"
)
# Nested form — what the heading render hook (Task 4) actually emits:
# the <a class="anchor-link"> sits INSIDE the <hN>, not after it.
NESTED_GOOD = page(
    '<h2 id="thm-ivt">Section'
    '<a class="anchor-link" href="#thm-ivt" aria-label="Copy link to Section"'
    ' data-anchor-title="Section">§</a></h2>'
    "<p>body</p>"
)
MISSING_ANCHOR = page('<h2 id="orphan">Section</h2><p>body</p>')
WRONG_HREF = page(
    '<h2 id="thm-ivt">Section</h2>'
    '<a class="anchor-link" href="#somewhere-else">§</a>'
    "<p>body</p>"
)
OPT_OUT = page('<h2 id="modal-title" data-no-anchor-link>Cite</h2><p>body</p>')
ID_OUTSIDE_MAIN = (
    "<!doctype html><html><body>"
    "<header><h1 id=\"site-title\">Site</h1></header>"
    "<main><p>no ids here</p></main>"
    "</body></html>"
)
NO_MAIN = "<!doctype html><html><body><h2 id=\"x\">No main wrapper</h2></body></html>"

# Spec §1 narrowing: structural id-bearing elements inside <main> that are
# NOT reading-flow targets must be silently ignored (no anchor-link
# expected). These cover the categories surfaced during Task 8 dev:
# SVG <symbol>, graph-data <script>, sidenote <aside>, footnote <sup>/<li>.
STRUCTURAL_IDS_IGNORED = page(
    '<svg><symbol id="g-game"><path d="M0,0"/></symbol></svg>'
    '<script id="garden-graph-data" type="application/json">{}</script>'
    '<aside id="sn-1">side</aside>'
    '<sup id="fnref:1">1</sup>'
    '<li id="fn:1">fn body</li>'
    '<li id="ref-foo">ref body</li>'
    '<nav id="TableOfContents">toc</nav>'
    '<aside id="garden-graph-panel">panel</aside>'
)

# A reading-flow target with class="block-…" gets enforced.
BLOCK_GOOD = page(
    '<div class="block-theorem block-strong" id="thm-x">'
    '<h4 class="block-header">Theorem 1.</h4>'
    '<a class="anchor-link" href="#thm-x">§</a>'
    '<div class="block-body">body</div></div>'
)

# A reading-flow target with class="block-…" but missing the anchor-link
# should still fail (it's a real spec-coverage gap, not an "ignore me").
BLOCK_MISSING = page(
    '<div class="block-theorem block-strong" id="thm-x">'
    '<h4 class="block-header">Theorem 1.</h4>'
    '<div class="block-body">body</div></div>'
)


class TempPublic:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.public = self.root / "public"
        self.public.mkdir()

    def write(self, rel: str, html: str) -> None:
        f = self.public / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html)

    def cleanup(self) -> None:
        shutil.rmtree(self.root)


class CheckAnchorLinkTest(unittest.TestCase):
    def setUp(self) -> None:
        self.t = TempPublic()

    def tearDown(self) -> None:
        self.t.cleanup()

    def test_good_passes(self) -> None:
        self.t.write("essays/x/index.html", GOOD)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")
        self.assertEqual(errors, [])

    def test_nested_good_passes(self) -> None:
        # Verifies the render-hook emission form (anchor INSIDE the <hN>).
        self.t.write("essays/x/index.html", NESTED_GOOD)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")
        self.assertEqual(errors, [])

    def test_missing_anchor_fails(self) -> None:
        self.t.write("essays/x/index.html", MISSING_ANCHOR)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 1)
        self.assertTrue(any("orphan" in e for e in errors))

    def test_wrong_href_fails(self) -> None:
        self.t.write("essays/x/index.html", WRONG_HREF)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 1)
        self.assertTrue(any("thm-ivt" in e for e in errors))

    def test_opt_out_is_skipped(self) -> None:
        self.t.write("essays/x/index.html", OPT_OUT)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")

    def test_id_outside_main_is_ignored(self) -> None:
        self.t.write("essays/x/index.html", ID_OUTSIDE_MAIN)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")

    def test_page_with_no_main_is_ignored(self) -> None:
        self.t.write("essays/x/index.html", NO_MAIN)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")

    def test_structural_ids_in_main_are_silently_ignored(self) -> None:
        """SVG <symbol>, <script>, <aside>, <sup>, <li>, <nav> with ids inside
        <main> are NOT reading-flow targets per spec §1 — the linter must not
        flag them as missing anchor-links."""
        self.t.write("essays/x/index.html", STRUCTURAL_IDS_IGNORED)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")

    def test_block_class_element_with_anchor_passes(self) -> None:
        self.t.write("essays/x/index.html", BLOCK_GOOD)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")

    def test_block_class_element_missing_anchor_fails(self) -> None:
        self.t.write("essays/x/index.html", BLOCK_MISSING)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 1)
        self.assertTrue(any("thm-x" in e for e in errors))

    def test_empty_public_passes(self) -> None:
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
