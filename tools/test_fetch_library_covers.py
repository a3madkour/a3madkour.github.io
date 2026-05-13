from __future__ import annotations
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import fetch_library_covers as fc

class CliTests(unittest.TestCase):
    def test_default_medium_is_all(self):
        args = fc.parse_args([])
        self.assertEqual(args.medium, "all")
        self.assertFalse(args.force)
        self.assertFalse(args.dry_run)

    def test_medium_flag(self):
        args = fc.parse_args(["--medium", "book"])
        self.assertEqual(args.medium, "book")

    def test_force_flag(self):
        args = fc.parse_args(["--force"])
        self.assertTrue(args.force)

    def test_dry_run_flag(self):
        args = fc.parse_args(["--dry-run"])
        self.assertTrue(args.dry_run)

if __name__ == "__main__":
    unittest.main()
