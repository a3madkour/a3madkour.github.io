"""Tests for gen_lhci_urls.py — run with:
   python3 -m unittest tools/test_gen_lhci_urls.py -v
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_lhci_urls as gen  # noqa: E402


class Scaffold(unittest.TestCase):
    def test_module_imports(self) -> None:
        self.assertTrue(hasattr(gen, "run"))
        self.assertTrue(hasattr(gen, "main"))


if __name__ == "__main__":
    unittest.main()
