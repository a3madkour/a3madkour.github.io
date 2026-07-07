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


if __name__ == "__main__":
    unittest.main()
