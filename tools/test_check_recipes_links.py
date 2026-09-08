import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_helpers import TempRepo
import check_recipes_links as mod

BASE = """---
title: "Ex"
date: 2026-07-06
lastmod: 2026-07-06
draft: false
summary: "d"
servings: 4
sources:
  - {{ name: "Ex", url: "{url}" }}
ingredients:
  - {{ qty: 1, unit: null, item: "x" }}
steps:
  - "s"
video: "{video}"
---
"""


class T(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_good(self):
        self.repo.write("content/recipes/ex/index.md",
                        BASE.format(url="https://example.com/x", video="dQw4w9WgXcQ"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_bad_url(self):
        self.repo.write("content/recipes/ex/index.md",
                        BASE.format(url="notaurl", video="dQw4w9WgXcQ"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("url" in e for e in errs))

    def test_bad_video(self):
        self.repo.write("content/recipes/ex/index.md",
                        BASE.format(url="https://example.com/x", video="short"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("video" in e for e in errs))


    def _with_raw_image(self, raw_line):
        """Append a verbatim `image:` line — for shapes quoting would destroy."""
        base = BASE.format(url="https://example.com/x", video="dQw4w9WgXcQ")
        return base.replace('video: "dQw4w9WgXcQ"',
                            f'video: "dQw4w9WgXcQ"\n{raw_line}')

    def _with_image(self, value):
        return self._with_raw_image(f'image: "{value}"')

    def test_missing_bundle_image_rejected(self):
        self.repo.write("content/recipes/ex/index.md", self._with_image("nope.svg"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("image" in e for e in errs), errs)

    def test_present_bundle_image_passes(self):
        self.repo.write("content/recipes/ex/index.md", self._with_image("hero.svg"))
        self.repo.write("content/recipes/ex/hero.svg", "<svg/>")
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_absolute_image_url_passes(self):
        self.repo.write("content/recipes/ex/index.md",
                        self._with_image("https://example.com/a.png"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_malformed_absolute_image_url_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        self._with_image("https://ex ample.com/a.png"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("image" in e for e in errs), errs)

    def test_missing_root_relative_image_rejected(self):
        self.repo.write("content/recipes/ex/index.md", self._with_image("/img/nope.png"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("static/" in e for e in errs), errs)

    def test_present_root_relative_image_passes(self):
        self.repo.write("content/recipes/ex/index.md", self._with_image("/img/hero.png"))
        self.repo.write("static/img/hero.png", "x")
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)


    # --- fix round 1: divergences probed against the merged schema-recipe.html ---

    def test_empty_image_is_skipped(self):
        # Hugo's `with` treats "" as falsy and emits no image key; skip to match.
        self.repo.write("content/recipes/ex/index.md", self._with_image(""))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_root_relative_image_tolerates_query_string(self):
        self.repo.write("content/recipes/ex/index.md", self._with_image("/img/h.png?v=2"))
        self.repo.write("static/img/h.png", "x")
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_bundle_image_tolerates_query_and_fragment(self):
        self.repo.write("content/recipes/ex/index.md", self._with_image("hero.svg?v=2#top"))
        self.repo.write("content/recipes/ex/hero.svg", "<svg/>")
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_query_string_does_not_mask_a_missing_file(self):
        self.repo.write("content/recipes/ex/index.md", self._with_image("/img/nope.png?v=2"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("static/" in e for e in errs), errs)

    def test_protocol_relative_image_rejected_by_name(self):
        self.repo.write("content/recipes/ex/index.md",
                        self._with_image("//cdn.example.com/a.png"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("protocol-relative" in e for e in errs), errs)

    def test_data_uri_image_rejected_by_scheme(self):
        self.repo.write("content/recipes/ex/index.md",
                        self._with_raw_image("image: data:image/png;base64,AAAA"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("scheme" in e for e in errs), errs)

    def test_uppercase_scheme_rejected_by_scheme(self):
        self.repo.write("content/recipes/ex/index.md",
                        self._with_image("HTTPS://example.com/a.png"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("scheme" in e for e in errs), errs)

    def test_list_valued_image_rejected_without_a_repr_leak(self):
        self.repo.write("content/recipes/ex/index.md",
                        self._with_raw_image('image: ["hero.svg", "b.svg"]'))
        self.repo.write("content/recipes/ex/hero.svg", "<svg/>")
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("single string" in e for e in errs), errs)
        # The Python repr must not reach the author.
        self.assertFalse(any("['hero.svg'" in e for e in errs), errs)

    def test_overlong_bundle_path_rejects_cleanly_not_crashes(self):
        """A >255-byte component makes Path.exists() raise OSError (ENAMETOOLONG).

        pathlib swallows a fixed errno set and re-raises the rest, so this used
        to surface as a traceback rather than the clean rejection the linter
        gives at 250 chars — the least diagnosable possible output (RF2.2).
        """
        self.repo.write("content/recipes/ex/index.md", self._with_image("a" * 300 + ".png"))
        rc, errs = mod.run(self.repo.root)   # must not raise
        self.assertEqual(rc, 1)
        self.assertTrue(any("not found in the page bundle" in e for e in errs), errs)

    def test_overlong_root_relative_path_rejects_cleanly_not_crashes(self):
        self.repo.write("content/recipes/ex/index.md", self._with_image("/" + "a" * 300 + ".png"))
        rc, errs = mod.run(self.repo.root)   # must not raise
        self.assertEqual(rc, 1)
        self.assertTrue(any("not found under static/" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
