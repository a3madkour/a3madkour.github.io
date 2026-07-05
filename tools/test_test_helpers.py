"""Tests for test_helpers.TempRepo — run:
   python3 -m unittest tools/test_test_helpers.py -v"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_helpers import TempRepo  # noqa: E402


class TempRepoTest(unittest.TestCase):
    def test_write_creates_parents_and_returns_path(self) -> None:
        repo = TempRepo()
        try:
            p = repo.write("content/garden/x/index.md", "hello")
            self.assertTrue(p.exists())
            self.assertEqual(p.read_text(encoding="utf-8"), "hello")
            self.assertEqual(p, repo.root / "content/garden/x/index.md")
        finally:
            repo.cleanup()
        self.assertFalse(repo.root.exists())
