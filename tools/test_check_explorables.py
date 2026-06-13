"""Tests for check_explorables.py — run with:
   python3 -m unittest tools/test_check_explorables.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_explorables as lint  # noqa: E402


class ExplorablesLinterScaffold(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "content" / "essays").mkdir(parents=True)
        (self.tmp / "assets" / "js" / "explorables").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def test_empty_tree_no_errors(self) -> None:
        errors = lint.lint_explorables(self.tmp)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
