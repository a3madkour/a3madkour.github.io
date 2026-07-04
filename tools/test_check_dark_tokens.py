#!/usr/bin/env python3
"""Tests for check_dark_tokens.py (R2.2)."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_dark_tokens as lint  # noqa: E402


def _repo_with_css(css: str) -> Path:
    root = Path(tempfile.mkdtemp())
    (root / "assets" / "css").mkdir(parents=True)
    (root / "assets" / "css" / "main.css").write_text(css, encoding="utf-8")
    return root


GOOD = """:root { --x: 1; }
:root[data-theme="dark"] {
  --color-ink:   #fff;
  --color-stone: #000;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    --color-ink:   #fff;
    --color-stone: #000;
  }
}
"""

VALUE_MISMATCH = GOOD.replace(
    "    --color-stone: #000;", "    --color-stone: #111;"
)

MISSING_IN_MEDIA = """:root[data-theme="dark"] {
  --color-ink:   #fff;
  --color-stone: #000;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    --color-ink:   #fff;
  }
}
"""


class DarkTokenEqualityTest(unittest.TestCase):
    def _run(self, css: str):
        root = _repo_with_css(css)
        try:
            return lint.run(root)
        finally:
            shutil.rmtree(root)

    def test_matching_blocks_pass(self):
        rc, errors = self._run(GOOD)
        self.assertEqual((rc, errors), (0, []))

    def test_value_mismatch_fails(self):
        rc, errors = self._run(VALUE_MISMATCH)
        self.assertEqual(rc, 1)
        self.assertTrue(any("--color-stone" in e for e in errors),
                        msg=f"expected --color-stone diff, got {errors}")

    def test_missing_token_fails(self):
        rc, errors = self._run(MISSING_IN_MEDIA)
        self.assertEqual(rc, 1)
        self.assertTrue(any("--color-stone" in e for e in errors),
                        msg=f"expected missing --color-stone, got {errors}")

    def test_missing_block_fails(self):
        rc, errors = self._run(":root[data-theme=\"dark\"] { --color-ink: #fff; }\n")
        self.assertEqual(rc, 1)


class RealMainCssTest(unittest.TestCase):
    def test_repo_main_css_dark_blocks_in_sync(self):
        repo_root = Path(__file__).resolve().parent.parent
        rc, errors = lint.run(repo_root)
        self.assertEqual((rc, errors), (0, []),
                         msg=f"live main.css dark blocks drifted: {errors}")


if __name__ == "__main__":
    unittest.main()
