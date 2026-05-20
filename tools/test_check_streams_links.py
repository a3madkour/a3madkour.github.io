"""Tests for check_streams_links.py — run with:
   python3 -m unittest tools/test_check_streams_links.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_streams_links as lint  # noqa: E402


def _md(fm: dict) -> str:
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append("Body.")
    return "\n".join(lines) + "\n"


class StreamsLinksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.content = self.tmp / "content"
        for path in [
            "streams", "essays", "garden",
            "research/themes", "research/questions",
            "works/games", "works/music", "works/poetry",
        ]:
            (self.content / path).mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, rel: str, fm: dict) -> Path:
        d = self.content / rel
        d.mkdir(parents=True, exist_ok=True)
        p = d / "index.md"
        p.write_text(_md(fm))
        return p

    def test_symmetric_passes(self):
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["example-essay-one"],
        })
        self._write("essays/example-essay-one", {
            "title": "E1", "date": "2026-01-01", "draft": "false",
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_forward_edge_dangling(self):
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["nonexistent-essay"],
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("nonexistent-essay" in e for e in errs))

    def test_forward_edge_to_draft_fails(self):
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["draft-essay"],
        })
        self._write("essays/draft-essay", {
            "title": "D", "date": "2026-01-01", "draft": "true",
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("draft" in e.lower() for e in errs))

    def test_asymmetric_forward_only_fails(self):
        # Stream points at essay, but essay does NOT point back.
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["example-essay-one"],
        })
        self._write("essays/example-essay-one", {
            "title": "E1", "date": "2026-01-01", "draft": "false",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("asymmetric" in e.lower() or "source_stream" in e for e in errs))

    def test_back_edge_dangling_stream(self):
        # Essay has source_stream pointing at a stream that doesn't exist.
        self._write("essays/example-essay-one", {
            "title": "E1", "date": "2026-01-01", "draft": "false",
            "source_stream": "2026-04-10-nonexistent",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("2026-04-10-nonexistent" in e for e in errs))

    def test_back_edge_present_but_stream_doesnt_list_us(self):
        # Stream exists, essay points back, but stream's related_essays does NOT include the essay.
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["some-other-essay"],
        })
        self._write("essays/some-other-essay", {
            "title": "Other", "date": "2026-01-01", "draft": "false",
            "source_stream": "2026-04-10-s1",
        })
        self._write("essays/example-essay-one", {
            "title": "E1", "date": "2026-01-01", "draft": "false",
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("example-essay-one" in e and "related_essays" in e for e in errs))

    def test_all_four_back_edges(self):
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["e1"],
            "related_garden": ["g1"],
            "related_research": ["q1"],
            "related_works": ["w1"],
        })
        self._write("essays/e1", {"title": "E1", "date": "2026-01-01", "draft": "false", "source_stream": "2026-04-10-s1"})
        self._write("garden/g1", {"title": "G1", "draft": "false", "last_modified": "2026-01-01", "growth_stage": "budding", "source_stream": "2026-04-10-s1"})
        self._write("research/questions/q1", {"title": "Q1", "theme": "x", "status": "active", "last_modified": "2026-01-01", "description": "d", "source_stream": "2026-04-10-s1"})
        self._write("works/games/w1", {
            "title": "W1", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "status": "playable", "game_kind": "full-release",
            "tagline": "t", "year": 2026,
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_related_works_resolves_across_three_sub_sections(self):
        # related_works slug can resolve under games/, music/, OR poetry/.
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "creative",
            "archive_status": "archived", "vod_url": "x",
            "related_works": ["m1", "p1"],
        })
        self._write("works/music/m1", {
            "title": "M1", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "format": "track", "year": 2026,
            "source_stream": "2026-04-10-s1",
        })
        self._write("works/poetry/p1", {
            "title": "P1", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "lines": 8,
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_research_back_edge_can_be_theme(self):
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "research",
            "archive_status": "archived", "vod_url": "x",
            "related_research": ["t1"],
        })
        self._write("research/themes/t1", {
            "title": "T1", "status": "active", "tags": "[memory]",
            "last_modified": "2026-01-01", "description": "d", "weight": 10,
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_empty_tree_passes(self):
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
