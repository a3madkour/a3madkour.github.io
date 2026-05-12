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

    def test_round_trip_lyrics_passes(self):
        self._write("works/music/track-a", {
            "title": "Track A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "format": "track", "year": 2026,
            "lyrics_poem": "poem-a",
        })
        self._write("works/poetry/poem-a", {
            "title": "Poem A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "lines": 8,
            "set_to_music": "track-a",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_round_trip_asymmetric_fails(self):
        self._write("works/music/track-a", {
            "title": "Track A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "format": "track", "year": 2026,
            "lyrics_poem": "poem-a",
        })
        self._write("works/poetry/poem-a", {
            "title": "Poem A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "lines": 8,
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("asymmetric" in e.lower() or "round-trip" in e.lower() for e in errs))

    def test_lyrics_poem_dangling_fails(self):
        self._write("works/music/track-a", {
            "title": "Track A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "format": "track", "year": 2026,
            "lyrics_poem": "nonexistent-poem",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("nonexistent-poem" in e for e in errs))

    def test_set_to_music_dangling_fails(self):
        self._write("works/poetry/poem-a", {
            "title": "Poem A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "lines": 8,
            "set_to_music": "nonexistent-track",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("nonexistent-track" in e for e in errs))

    def test_game_research_questions_resolved(self):
        self._write("research/questions/q-a", {
            "title": "Q A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false",
        })
        self._write("works/games/game-a", {
            "title": "Game A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "status": "playable", "kind": "full-release",
            "tagline": "ok", "year": 2026,
            "research_questions": ["/research/questions/q-a/"],
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_game_research_questions_dangling_fails(self):
        self._write("works/games/game-a", {
            "title": "Game A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "status": "playable", "kind": "full-release",
            "tagline": "ok", "year": 2026,
            "research_questions": ["/research/questions/missing/"],
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("missing" in e for e in errs))

    def test_game_related_essays_dangling_fails(self):
        self._write("works/games/game-a", {
            "title": "Game A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "status": "playable", "kind": "full-release",
            "tagline": "ok", "year": 2026,
            "related_essays": ["/essays/nonexistent/"],
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("/essays/nonexistent/" in e for e in errs))

    def test_game_related_notes_dangling_fails(self):
        self._write("works/games/game-a", {
            "title": "Game A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "status": "playable", "kind": "full-release",
            "tagline": "ok", "year": 2026,
            "related_notes": ["/garden/nonexistent/"],
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("/garden/nonexistent/" in e for e in errs))

    def test_draft_target_treated_as_missing(self):
        self._write("research/questions/draft-q", {
            "title": "Draft Q", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "true",
        })
        self._write("works/games/game-a", {
            "title": "Game A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "status": "playable", "kind": "full-release",
            "tagline": "ok", "year": 2026,
            "research_questions": ["/research/questions/draft-q/"],
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("draft" in e.lower() for e in errs))

    def test_empty_tree_passes(self):
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
