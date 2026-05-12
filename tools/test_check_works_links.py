"""Tests for check_works_links.py — run with:
   python3 -m unittest tools/test_check_works_links.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_works_links as lint  # noqa: E402


def _md(fm: dict[str, object]) -> str:
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append("Body.")
    return "\n".join(lines) + "\n"


class WorksLinksLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.content = self.tmp / "content"
        for path in [
            "works/games", "works/music", "works/poetry",
            "essays", "garden", "research/questions",
        ]:
            (self.content / path).mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, rel: str, fm: dict[str, object]) -> Path:
        d = self.content / rel
        d.mkdir(parents=True, exist_ok=True)
        p = d / "index.md"
        p.write_text(_md(fm))
        return p


if __name__ == "__main__":
    unittest.main()
