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
kind: full-release
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


    # --- games contract ---

    def test_game_valid_passes(self):
        p = self._write("games", "ok", GAME_VALID)
        self.assertEqual(lint.lint_file(p), [])

    def test_game_missing_status(self):
        body = GAME_VALID.replace("status: playable\n", "")
        p = self._write("games", "missing-status", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'status'" in e for e in errs))

    def test_game_bad_status_enum(self):
        body = GAME_VALID.replace("status: playable", "status: shipped")
        p = self._write("games", "bad-status", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("status='shipped'" in e for e in errs))

    def test_game_bad_kind_enum(self):
        body = GAME_VALID.replace("kind: full-release", "kind: walking-sim")
        p = self._write("games", "bad-kind", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("kind='walking-sim'" in e for e in errs))

    def test_game_year_not_int(self):
        body = GAME_VALID.replace("year: 2026", "year: 'twenty-six'")
        p = self._write("games", "bad-year", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("year" in e and "integer" in e for e in errs))

    def test_game_unknown_field(self):
        body = GAME_VALID.replace("year: 2026\n", "year: 2026\nrarity: 99\n")
        p = self._write("games", "extra-field", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("unknown field 'rarity'" in e for e in errs))

    def test_game_with_all_optionals(self):
        body = """\
---
title: "Full Game"
date: 2026-01-01
lastmod: 2026-01-02
draft: false
status: in-progress
kind: research-prototype
tagline: "All the fields."
year: 2026
tags: [example, demo]
summary: "Summary."
hero: hero.svg
embed_url: "https://example.itch.io/embed"
source_url: "https://github.com/example/repo"
itch_url: "https://example.itch.io"
collaborators: [Alice, Bob]
tech_stack: [Godot, GDScript]
length: "2 hours"
screenshots: [s1.svg, s2.svg, s3.svg]
research_questions: [/research/questions/example-active-q-1/]
related_essays: [/essays/example-essay-one/]
related_notes: [/garden/story-atoms/]
---

Body.
"""
        p = self._write("games", "full", body)
        self.assertEqual(lint.lint_file(p), [])

    # --- music contract ---

    def test_music_valid_passes(self):
        p = self._write("music", "ok", MUSIC_VALID)
        self.assertEqual(lint.lint_file(p), [])

    def test_music_missing_format(self):
        body = MUSIC_VALID.replace("format: album\n", "")
        p = self._write("music", "missing-format", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'format'" in e for e in errs))

    def test_music_bad_format_enum(self):
        body = MUSIC_VALID.replace("format: album", "format: cassette")
        p = self._write("music", "bad-format", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("format='cassette'" in e for e in errs))

    def test_music_platform_embed_bad_kind(self):
        body = MUSIC_VALID + "platform_embed: { kind: spotify, url: 'https://example.com' }\n"
        p = self._write("music", "bad-embed-kind", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("platform_embed.kind='spotify'" in e for e in errs))

    def test_music_platform_embed_missing_url(self):
        body = MUSIC_VALID + "platform_embed: { kind: bandcamp }\n"
        p = self._write("music", "embed-no-url", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("platform_embed.url" in e and "missing" in e for e in errs))

    def test_music_tracks_shape(self):
        body = MUSIC_VALID + """tracks:
  - { title: "Track 1", duration: "3:14" }
  - { title: "Track 2", duration: "4:20" }
"""
        p = self._write("music", "good-tracks", body)
        self.assertEqual(lint.lint_file(p), [])

    def test_music_track_missing_duration(self):
        body = MUSIC_VALID + 'tracks:\n  - { title: "Track 1" }\n'
        p = self._write("music", "bad-track", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("tracks[0]" in e for e in errs))

    def test_music_unknown_field(self):
        body = MUSIC_VALID + "bpm: 128\n"
        p = self._write("music", "extra-field", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("unknown field 'bpm'" in e for e in errs))

    # --- poetry contract ---

    def test_poem_valid_passes(self):
        p = self._write("poetry", "ok", POEM_VALID)
        self.assertEqual(lint.lint_file(p), [])

    def test_poem_missing_lines(self):
        body = POEM_VALID.replace("lines: 14\n", "")
        p = self._write("poetry", "missing-lines", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'lines'" in e for e in errs))

    def test_poem_lines_not_int(self):
        body = POEM_VALID.replace("lines: 14", "lines: 'fourteen'")
        p = self._write("poetry", "bad-lines", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("lines" in e and "integer" in e for e in errs))

    def test_poem_with_optionals(self):
        body = """\
---
title: "Tagged Poem"
date: 2026-01-01
lastmod: 2026-01-02
draft: false
lines: 8
tags: [example, lyric]
collection: greenhouse-demos
set_to_music: some-music-slug
summary: "A summary."
---

Body.
"""
        p = self._write("poetry", "with-optionals", body)
        self.assertEqual(lint.lint_file(p), [])

    # --- runner ---

    def test_runner_walks_all_three_sub_sections(self):
        self._write("games", "g1", GAME_VALID)
        self._write("music", "m1", MUSIC_VALID)
        self._write("poetry", "p1", POEM_VALID)
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(errs, [])

    def test_runner_aggregates_errors(self):
        bad_game = GAME_VALID.replace("status: playable", "status: shipped")
        bad_poem = POEM_VALID.replace("lines: 14", "lines: 'fourteen'")
        self._write("games", "g1", bad_game)
        self._write("poetry", "p1", bad_poem)
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertEqual(len(errs), 2)


if __name__ == "__main__":
    unittest.main()
