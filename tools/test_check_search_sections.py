import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_helpers import TempRepo  # noqa: E402
import check_search_sections as mod  # noqa: E402

SEARCH_JS = """\
const SECTION_ORDER = ['essays', 'garden', 'other'];
const SECTION_LABEL = {
  essays:   'Essays',
  garden:   'Garden',
  other:    'Other',
};
"""

PAGE = '<html><body><span data-pagefind-meta="section:{s}" hidden></span></body></html>'
MINIFIED = "<html><body><span data-pagefind-meta=section:{s} hidden></span></body></html>"


class T(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.repo.write("assets/js/search.js", SEARCH_JS)

    def tearDown(self):
        self.repo.cleanup()

    def test_all_emitted_sections_registered_passes(self):
        self.repo.write("public/a.html", PAGE.format(s="essays"))
        self.repo.write("public/b.html", PAGE.format(s="garden"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_emitted_but_unregistered_section_is_rejected(self):
        self.repo.write("public/a.html", PAGE.format(s="essays"))
        self.repo.write("public/tags.html", PAGE.format(s="tags"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("'tags'" in e and "SECTION_ORDER" in e for e in errs), errs)

    def test_minified_unquoted_attribute_is_seen(self):
        """The production build strips attribute quotes; the linter must still match."""
        self.repo.write("public/a.html", PAGE.format(s="essays"))
        self.repo.write("public/t.html", MINIFIED.format(s="tags"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("'tags'" in e for e in errs), errs)

    def test_filter_attribute_counts_too(self):
        self.repo.write("public/a.html", PAGE.format(s="essays"))
        self.repo.write(
            "public/s.html",
            '<html><body><span data-pagefind-filter="section:series"></span></body></html>',
        )
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("'series'" in e for e in errs), errs)

    def test_missing_label_is_rejected(self):
        js = SEARCH_JS.replace("  garden:   'Garden',\n", "")
        self.repo.write("assets/js/search.js", js)
        self.repo.write("public/a.html", PAGE.format(s="essays"))
        self.repo.write("public/b.html", PAGE.format(s="garden"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("SECTION_LABEL" in e for e in errs), errs)

    def test_stale_order_entry_is_rejected(self):
        """A section nothing emits is dead vocabulary — or a template regressed."""
        self.repo.write("public/a.html", PAGE.format(s="essays"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("'garden'" in e and "no built page" in e for e in errs), errs)

    def test_other_is_runtime_only_and_never_stale(self):
        """`other` is search.js's no-meta fallback; it is never emitted into HTML."""
        self.repo.write("public/a.html", PAGE.format(s="essays"))
        self.repo.write("public/b.html", PAGE.format(s="garden"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)
        self.assertFalse(any("'other'" in e for e in errs), errs)

    def test_absent_public_skips_cleanly(self):
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0)
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
