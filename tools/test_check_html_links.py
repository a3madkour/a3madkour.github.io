#!/usr/bin/env python3
"""Tests for check_html_links.py (R6.3)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_html_links as lint  # noqa: E402
from test_helpers import TempRepo  # noqa: E402


class ParseTest(unittest.TestCase):
    def test_unquoted_minified_attrs(self):
        ids, hrefs = lint.parse_html("<a href=/essays/ id=nav>x</a>\n")
        self.assertEqual(hrefs, ["/essays/"])
        self.assertIn("nav", ids)

    def test_id_from_any_element_name_only_from_a(self):
        ids, _ = lint.parse_html(
            '<h2 id="sec">H</h2><input name="q"><a name="legacy"></a>'
        )
        self.assertIn("sec", ids)
        self.assertIn("legacy", ids)
        self.assertNotIn("q", ids)  # input name is not an anchor target

    def test_collects_only_a_hrefs(self):
        _, hrefs = lint.parse_html('<a href="/a/">x</a><link href="/main.css">')
        self.assertEqual(hrefs, ["/a/"])

    def test_ref_block_unresolved_href_skipped(self):
        # the site's documented marker for an intentionally-unresolved ref-block
        _, hrefs = lint.parse_html(
            '<a class="ref-block ref-block-unresolved" href="#thm-nope">x</a>'
        )
        self.assertEqual(hrefs, [])

    def test_script_json_not_parsed_as_tags(self):
        # hrefs inside <script> JSON must not be extracted
        _, hrefs = lint.parse_html('<script>var x = "<a href=/nope/>";</script>')
        self.assertEqual(hrefs, [])


class SkipTest(unittest.TestCase):
    def test_external_and_special_schemes_skipped(self):
        for h in ("https://other.com/x", "http://other.com", "mailto:a@b.c",
                  "tel:+1", "data:x", "javascript:void(0)", "//cdn.com/x", ""):
            self.assertTrue(lint.is_skip(h), msg=h)

    def test_internal_not_skipped(self):
        for h in ("/essays/", "#frag", "foo/", "../bar/",
                  "https://a3madkour.github.io/essays/"):
            self.assertFalse(lint.is_skip(h), msg=h)


class ResolveTest(unittest.TestCase):
    def test_root_relative(self):
        self.assertEqual(lint.resolve("/garden/x/", "/essays/a/"), ("/garden/x/", ""))

    def test_same_page_fragment(self):
        self.assertEqual(lint.resolve("#sec", "/essays/a/"), ("/essays/a/", "sec"))

    def test_relative_dotdot(self):
        self.assertEqual(lint.resolve("../b/", "/essays/a/"), ("/essays/b/", ""))

    def test_origin_stripped_and_query_dropped(self):
        self.assertEqual(
            lint.resolve("https://a3madkour.github.io/x/?q=1#f", "/a/"), ("/x/", "f")
        )


class ResolveFileTest(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.repo.write("index.html", "<html></html>")
        self.repo.write("essays/a/index.html", "<html></html>")
        self.repo.write("essays/index.xml", "<rss></rss>")
        self.repo.write("bare.html", "<html></html>")
        self.public = self.repo.root

    def tearDown(self):
        self.repo.cleanup()

    def test_root(self):
        self.assertEqual(lint.resolve_file("/", self.public), "index.html")

    def test_trailing_slash_dir(self):
        self.assertEqual(lint.resolve_file("/essays/a/", self.public), "essays/a/index.html")

    def test_no_slash_prefers_index_then_html(self):
        self.assertEqual(lint.resolve_file("/essays/a", self.public), "essays/a/index.html")
        self.assertEqual(lint.resolve_file("/bare", self.public), "bare.html")

    def test_asset_extension(self):
        self.assertEqual(lint.resolve_file("/essays/index.xml", self.public), "essays/index.xml")

    def test_missing(self):
        self.assertIsNone(lint.resolve_file("/nope/", self.public))


class UrlPathForTest(unittest.TestCase):
    def test_index_becomes_dir_url(self):
        self.assertEqual(lint.url_path_for("index.html"), "/")
        self.assertEqual(lint.url_path_for("essays/a/index.html"), "/essays/a/")
        self.assertEqual(lint.url_path_for("404.html"), "/404.html")


class RunTest(unittest.TestCase):
    def setUp(self):
        self.repo = None

    def tearDown(self):
        if self.repo:
            self.repo.cleanup()

    def _public(self, files: dict[str, str]) -> Path:
        self.repo = TempRepo()
        for rel, text in files.items():
            self.repo.write(rel, text)
        return self.repo.root

    def test_green_valid_links(self):
        public = self._public({
            "index.html": '<a href=/essays/a/>go</a><a href=#top>top</a>',
            "essays/a/index.html": '<h2 id=sec>H</h2><a href=#sec>self</a>'
                                   '<a href=/#>home</a><a href=mailto:x@y.z>mail</a>',
        })
        self.assertEqual(lint.run(public), (0, []))

    def test_broken_target_file(self):
        public = self._public({"index.html": '<a href=/gone/>x</a>'})
        rc, errs = lint.run(public)
        self.assertEqual(rc, 1)
        self.assertEqual(len(errs), 1)
        self.assertIn("/gone/", errs[0])

    def test_broken_anchor(self):
        public = self._public({
            "index.html": '<a href=/essays/a/#missing>x</a>',
            "essays/a/index.html": '<h2 id=present>H</h2>',
        })
        rc, errs = lint.run(public)
        self.assertEqual(rc, 1)
        self.assertIn("missing", errs[0])

    def test_valid_cross_page_anchor(self):
        public = self._public({
            "index.html": '<a href=/essays/a/#sec>x</a>',
            "essays/a/index.html": '<h2 id=sec>H</h2>',
        })
        self.assertEqual(lint.run(public), (0, []))

    def test_non_html_target_ignores_fragment(self):
        public = self._public({
            "index.html": '<a href=/feed.xml#anything>x</a>',
            "feed.xml": "<rss></rss>",
        })
        self.assertEqual(lint.run(public), (0, []))

    def test_missing_public(self):
        rc, errs = lint.run(Path("/nonexistent/public/xyz"))
        self.assertEqual(rc, 1)
        self.assertTrue(errs)


if __name__ == "__main__":
    unittest.main()
