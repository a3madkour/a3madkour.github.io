"""Tests for check_citations.py — run with:
   python3 -m unittest tools/test_check_citations.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_citations as lint  # noqa: E402


GARDEN_NOTE_PUBLISHED = """\
---
title: "Story atoms"
draft: false
last_modified: 2026-04-22
growth_stage: budding
---

Body.
"""

GARDEN_NOTE_DRAFT = """\
---
title: "Draft note"
draft: true
last_modified: 2026-04-22
growth_stage: seedling
---

Body.
"""


class CitationLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.garden = self.tmp / "content" / "garden"
        self.garden.mkdir(parents=True)
        self.data = self.tmp / "data"
        self.data.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write_garden(self, slug: str, body: str = GARDEN_NOTE_PUBLISHED) -> None:
        d = self.garden / slug
        d.mkdir()
        (d / "index.md").write_text(body)

    def _write_citations(self, yaml_text: str) -> Path:
        p = self.data / "citations.yaml"
        p.write_text(yaml_text)
        return p


if __name__ == "__main__":
    unittest.main()
