import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_helpers import TempRepo  # noqa: E402
import check_meta_description as mod  # noqa: E402

PAGE = '<html><head><meta name="description" content="{c}"></head><body></body></html>'
OG = '<html><head><meta property="og:description" content="{c}"></head><body></body></html>'
MINIFIED = "<html><head><meta name=description content=\"{c}\"></head><body></body></html>"


class T(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_flat_prose_passes(self):
        self.repo.write("public/a.html", PAGE.format(c="A clean one-line summary."))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_markup_is_rejected(self):
        """The real defect: .Summary is rendered HTML when no summary is declared."""
        self.repo.write("public/a.html", PAGE.format(c='<h2 id="tldr">TLDR</h2>'))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("HTML markup" in e for e in errs), errs)

    def test_anchor_glyph_is_rejected(self):
        self.repo.write("public/a.html", PAGE.format(c="TLDR§ some prose"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("anchor-link glyph" in e for e in errs), errs)

    def test_leading_whitespace_is_rejected(self):
        self.repo.write("public/a.html", PAGE.format(c=" leading space"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("whitespace" in e for e in errs), errs)

    def test_og_description_is_checked_too(self):
        self.repo.write("public/a.html", OG.format(c="<p>markup</p>"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("HTML markup" in e for e in errs), errs)

    def test_minified_unquoted_attribute_is_seen(self):
        self.repo.write("public/a.html", MINIFIED.format(c="<p>markup</p>"))
        rc, _ = mod.run(self.repo.root)
        self.assertEqual(rc, 1)

    def test_prose_angle_brackets_are_not_markup(self):
        """Fixture text like <TODO> is content; flagging it would be a false reject."""
        self.repo.write("public/a.html", PAGE.format(c="This is an index note. <TODO> fill this in."))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_absent_public_skips_cleanly(self):
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0)
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
