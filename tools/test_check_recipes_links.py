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


    def _with_image(self, value):
        base = BASE.format(url="https://example.com/x", video="dQw4w9WgXcQ")
        return base.replace('video: "dQw4w9WgXcQ"',
                            f'video: "dQw4w9WgXcQ"\nimage: "{value}"')

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


if __name__ == "__main__":
    unittest.main()
