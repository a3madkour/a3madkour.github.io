"""Tests for check_works_fixtures.py — run with:
   python3 -m unittest tools/test_check_works_fixtures.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_works_fixtures as lint  # noqa: E402


GAME_VALID = """\
---
title: "Example Game"
date: 2026-01-01
lastmod: 2026-01-02
draft: false
status: playable
type: full-release
tagline: "Example tagline."
year: 2026
---

Body.
"""

MUSIC_VALID = """\
---
title: "Example Album"
date: 2026-01-01
lastmod: 2026-01-02
draft: false
format: album
year: 2026
---

Body.
"""

POEM_VALID = """\
---
title: "Example Poem"
date: 2026-01-01
lastmod: 2026-01-02
draft: false
lines: 14
---

Body.
"""


class WorksFixturesLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.works = self.tmp / "content" / "works"
        for sub in ("games", "music", "poetry"):
            (self.works / sub).mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, sub: str, slug: str, body: str) -> Path:
        d = self.works / sub / slug
        d.mkdir()
        p = d / "index.md"
        p.write_text(body)
        return p


if __name__ == "__main__":
    unittest.main()
