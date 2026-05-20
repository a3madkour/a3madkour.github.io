"""Unit tests for tools/check_page_weights.py.

Tests run against synthetic HTML strings + tempfile-backed public/ dirs,
not against a real Hugo build.
"""

from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import check_page_weights as cpw


class TestBudgetFor(unittest.TestCase):
    def test_homepage_exact_match(self):
        self.assertEqual(cpw.budget_for("/"), 500_000)

    def test_default_fallthrough(self):
        self.assertEqual(cpw.budget_for("/unmapped-path/"), 100_000)

    def test_essay_post_at_essays_tier(self):
        self.assertEqual(cpw.budget_for("/essays/example-1/"), 200_000)

    def test_garden_index_is_graph_bearing(self):
        self.assertEqual(cpw.budget_for("/garden/"), 600_000)

    def test_garden_graph_is_graph_bearing(self):
        self.assertEqual(cpw.budget_for("/garden/graph/"), 600_000)

    def test_research_graph_is_graph_bearing(self):
        self.assertEqual(cpw.budget_for("/research/graph/"), 600_000)

    def test_works_umbrella_is_graph_bearing(self):
        self.assertEqual(cpw.budget_for("/works/"), 600_000)

    def test_works_graph_is_graph_bearing(self):
        self.assertEqual(cpw.budget_for("/works/graph/"), 600_000)

    def test_music_page_is_media_heavy(self):
        self.assertEqual(
            cpw.budget_for("/works/music/example-album/"), 500_000
        )

    def test_music_index_is_media_heavy(self):
        # /works/music/ matches the /works/music/ prefix before /works/.
        self.assertEqual(cpw.budget_for("/works/music/"), 500_000)

    def test_essays_index_at_essays_tier(self):
        self.assertEqual(cpw.budget_for("/essays/"), 200_000)

    def test_research_index_is_graph_bearing(self):
        # /research/ inlines the research-graph JS bundle.
        self.assertEqual(cpw.budget_for("/research/"), 600_000)

    def test_library_umbrella_is_media_heavy(self):
        self.assertEqual(cpw.budget_for("/library/"), 900_000)

    def test_library_leaf_is_media_heavy(self):
        self.assertEqual(cpw.budget_for("/library/reading/"), 900_000)

    def test_streams_item_tier(self):
        self.assertEqual(cpw.budget_for("/streams/2026-04-10-example-live-coding-stream/"), 300_000)

    def test_streams_index_at_streams_tier(self):
        # BUDGETS_PREFIX cannot distinguish index from item; the section index
        # inherits the /streams/ 300KB tier. Spec §13's 100KB index ideal is
        # subsumed (the index is empty enough to land well under 300KB).
        self.assertEqual(cpw.budget_for("/streams/"), 300_000)


class TestExtractRefs(unittest.TestCase):
    def test_extracts_link_stylesheet(self):
        html = '<html><head><link rel="stylesheet" href="/css/main.abc.css"></head></html>'
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(css, ["/css/main.abc.css"])
        self.assertEqual(js, [])
        self.assertEqual(img, [])

    def test_extracts_script_src(self):
        html = '<html><body><script src="/js/core.def.js"></script></body></html>'
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(js, ["/js/core.def.js"])

    def test_extracts_img_src(self):
        html = '<img src="/images/x.svg" alt="">'
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(img, ["/images/x.svg"])

    def test_skips_external_urls(self):
        html = (
            '<link rel="stylesheet" href="https://fonts.googleapis.com/x">'
            '<script src="//cdn.example.com/y.js"></script>'
            '<img src="https://example.com/z.png">'
        )
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(css, [])
        self.assertEqual(js, [])
        self.assertEqual(img, [])

    def test_skips_inline_script_without_src(self):
        html = '<script>const x = 1;</script>'
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(js, [])

    def test_ignores_non_stylesheet_links(self):
        html = (
            '<link rel="icon" href="/favicon.ico">'
            '<link rel="alternate" type="application/rss+xml" href="/index.xml">'
        )
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(css, [])


class TestSumAssetBytes(unittest.TestCase):
    def test_sums_local_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            (public / "css").mkdir()
            (public / "css" / "main.css").write_bytes(b"x" * 1000)
            (public / "js").mkdir()
            (public / "js" / "core.js").write_bytes(b"y" * 500)
            total = cpw.sum_asset_bytes(public, ["/css/main.css", "/js/core.js"])
            self.assertEqual(total, 1500)

    def test_missing_asset_contributes_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            total = cpw.sum_asset_bytes(public, ["/missing.css"])
            self.assertEqual(total, 0)


class TestAuditPage(unittest.TestCase):
    def _write(self, public: Path, url: str, html: str) -> Path:
        rel = url.strip("/")
        target = public / rel / "index.html" if rel else public / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        return target

    def test_page_under_budget_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            self._write(public, "/unmapped-path/", "<html><body>" + "x" * 1000 + "</body></html>")
            result = cpw.audit_page(public / "unmapped-path" / "index.html", public)
            self.assertEqual(result.budget, 100_000)
            self.assertLess(result.total, 100_000)
            self.assertFalse(result.over_budget)

    def test_page_over_budget_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            # default budget = 100_000; write 200KB of HTML
            self._write(
                public, "/big/", "<html><body>" + "x" * 200_000 + "</body></html>"
            )
            result = cpw.audit_page(public / "big" / "index.html", public)
            self.assertTrue(result.over_budget)
            self.assertEqual(result.budget, 100_000)


if __name__ == "__main__":
    unittest.main()
