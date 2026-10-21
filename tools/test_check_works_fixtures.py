"""Tests for check_works_fixtures.py — run with:
   python3 -m unittest tools/test_check_works_fixtures.py -v
"""
from __future__ import annotations

import copy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_works_fixtures as lint  # noqa: E402
import sections  # noqa: E402
from test_helpers import TempRepo  # noqa: E402


GAME_VALID = """\
---
title: "Example Game"
date: 2026-01-01
lastmod: 2026-01-02
draft: false
status: playable
game_kind: full-release
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

# Minimal valid game fixture with status: playable — used by the registry
# tests below, where TempRepo writes it at an arbitrary path (not necessarily
# "ok") rather than through self._write's games/<slug> convention.
GAME_MD_PLAYABLE = GAME_VALID

REPO_ROOT = Path(__file__).resolve().parent.parent

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


def _registry(**enum_overrides) -> dict:
    """The live registry with the works enums pinned — a fixture, not a copy.

    The ENUM values are hand-written: a test asserting that "shipped" is
    rejected must control the set it is rejected against, or a later addition
    to the real registry would quietly change what the test means. The FIELD
    SETS are deliberately NOT written out: data/sections.json is their single
    home, shared with the elisp normalizer's allowed-key filter, and a
    transcription here would be exactly the third copy that made the old
    elisp `-key-set-matches-contract` tests vacuous.
    """
    reg = copy.deepcopy(sections.load(REPO_ROOT))
    s = reg["sections"]
    enums = {
        ("works/games", "status"): ["playable", "in-progress", "archived"],
        ("works/games", "game_kind"): ["full-release", "jam", "research-prototype", "experiment"],
        ("works/music", "format"): ["album", "track", "experiment", "live"],
    }
    enums.update(enum_overrides.pop("enums", {}))
    for (sec, field), values in enums.items():
        s[sec]["fields"][field]["values"] = values
    s["works/music"]["fields"]["platform_embed"]["fields"]["kind"]["values"] = (
        enum_overrides.pop("platform_kinds", ["bandcamp", "soundcloud", "youtube"]))
    assert not enum_overrides, enum_overrides
    return reg


# Threaded explicitly into every direct lint_file() call in this file.
REG = _registry()


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
        self.assertEqual(lint.lint_file(p, REG), [])

    def test_game_missing_status(self):
        body = GAME_VALID.replace("status: playable\n", "")
        p = self._write("games", "missing-status", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("missing required field 'status'" in e for e in errs))

    def test_game_bad_status_enum(self):
        body = GAME_VALID.replace("status: playable", "status: shipped")
        p = self._write("games", "bad-status", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("status='shipped'" in e for e in errs))

    def test_game_bad_kind_enum(self):
        body = GAME_VALID.replace("game_kind: full-release", "game_kind: walking-sim")
        p = self._write("games", "bad-kind", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("game_kind='walking-sim'" in e for e in errs))

    def test_game_year_not_int(self):
        body = GAME_VALID.replace("year: 2026", "year: 'twenty-six'")
        p = self._write("games", "bad-year", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("year" in e and "integer" in e for e in errs))

    def test_game_unknown_field(self):
        body = GAME_VALID.replace("year: 2026\n", "year: 2026\nrarity: 99\n")
        p = self._write("games", "extra-field", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("unknown field 'rarity'" in e for e in errs))

    def test_game_with_all_optionals(self):
        body = """\
---
title: "Full Game"
date: 2026-01-01
lastmod: 2026-01-02
draft: false
status: in-progress
game_kind: research-prototype
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
        self.assertEqual(lint.lint_file(p, REG), [])

    # --- music contract ---

    def test_music_valid_passes(self):
        p = self._write("music", "ok", MUSIC_VALID)
        self.assertEqual(lint.lint_file(p, REG), [])

    def test_music_missing_format(self):
        body = MUSIC_VALID.replace("format: album\n", "")
        p = self._write("music", "missing-format", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("missing required field 'format'" in e for e in errs))

    def test_music_bad_format_enum(self):
        body = MUSIC_VALID.replace("format: album", "format: cassette")
        p = self._write("music", "bad-format", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("format='cassette'" in e for e in errs))

    def test_music_platform_embed_bad_kind(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            "year: 2026\nplatform_embed: { kind: spotify, url: 'https://example.com' }\n",
        )
        p = self._write("music", "bad-embed-kind", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("platform_embed.kind='spotify'" in e for e in errs))

    def test_music_platform_embed_missing_url(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            "year: 2026\nplatform_embed: { kind: bandcamp }\n",
        )
        p = self._write("music", "embed-no-url", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("platform_embed.url" in e and "missing" in e for e in errs))

    def test_music_tracks_shape(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            'year: 2026\ntracks:\n  - { title: "Track 1", duration: "3:14" }\n  - { title: "Track 2", duration: "4:20" }\n',
        )
        p = self._write("music", "good-tracks", body)
        self.assertEqual(lint.lint_file(p, REG), [])

    def test_music_track_missing_duration(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            'year: 2026\ntracks:\n  - { title: "Track 1" }\n',
        )
        p = self._write("music", "bad-track", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("tracks[0]" in e for e in errs))

    def test_music_unknown_field(self):
        body = MUSIC_VALID.replace("year: 2026\n", "year: 2026\nbpm: 128\n")
        p = self._write("music", "extra-field", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("unknown field 'bpm'" in e for e in errs))

    # --- poetry contract ---

    def test_poem_valid_passes(self):
        p = self._write("poetry", "ok", POEM_VALID)
        self.assertEqual(lint.lint_file(p, REG), [])

    def test_poem_missing_lines(self):
        body = POEM_VALID.replace("lines: 14\n", "")
        p = self._write("poetry", "missing-lines", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("missing required field 'lines'" in e for e in errs))

    def test_poem_lines_not_int(self):
        body = POEM_VALID.replace("lines: 14", "lines: 'fourteen'")
        p = self._write("poetry", "bad-lines", body)
        errs = lint.lint_file(p, REG)
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
        self.assertEqual(lint.lint_file(p, REG), [])

    def test_poem_accepts_audio_url(self):
        body = POEM_VALID.replace(
            "lines: 14\n",
            'lines: 14\naudio_url: "https://example.com/reading.mp3"\n',
        )
        p = self._write("poetry", "with-audio", body)
        self.assertEqual(lint.lint_file(p, REG), [])

    def test_poem_audio_url_relative_accepted_by_fixture_linter(self):
        # check_works_fixtures only validates *shape* (unknown-field gate);
        # path/URL validity is the synced-poetry linter's job (Task 2).
        body = POEM_VALID.replace(
            "lines: 14\n",
            'lines: 14\naudio_url: reading.mp3\n',
        )
        p = self._write("poetry", "with-audio-rel", body)
        self.assertEqual(lint.lint_file(p, REG), [])

    # --- umbrella (Bento grid) fields ---

    def test_game_accepts_tile_size_featured_hero(self):
        body = GAME_VALID.replace(
            "year: 2026\n",
            "year: 2026\ntile_size: large\nfeatured: true\nhero: true\n",
        )
        p = self._write("games", "with-umbrella", body)
        self.assertEqual(lint.lint_file(p, REG), [])

    def test_music_accepts_tile_size_featured_hero(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            "year: 2026\ntile_size: small\nfeatured: true\nhero: false\n",
        )
        p = self._write("music", "with-umbrella", body)
        self.assertEqual(lint.lint_file(p, REG), [])

    def test_poem_accepts_tile_size_featured_hero(self):
        body = POEM_VALID.replace(
            "lines: 14\n",
            "lines: 14\ntile_size: medium\nfeatured: false\nhero: true\n",
        )
        p = self._write("poetry", "with-umbrella", body)
        self.assertEqual(lint.lint_file(p, REG), [])

    def test_tile_size_must_be_in_enum(self):
        body = GAME_VALID.replace(
            "year: 2026\n",
            "year: 2026\ntile_size: huge\n",
        )
        p = self._write("games", "bad-tile-size", body)
        errs = lint.lint_file(p, REG)
        self.assertTrue(any("tile_size='huge'" in e for e in errs), errs)

    # --- source_stream (streams-section back-edge) ---

    def test_game_accepts_source_stream(self):
        body = GAME_VALID.replace(
            "year: 2026\n",
            "year: 2026\nsource_stream: 2026-04-10-example-live-coding-stream\n",
        )
        p = self._write("games", "with-source-stream", body)
        self.assertEqual(lint.lint_file(p, REG), [])

    def test_music_accepts_source_stream(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            "year: 2026\nsource_stream: 2026-04-22-example-music-jam-stream\n",
        )
        p = self._write("music", "with-source-stream", body)
        self.assertEqual(lint.lint_file(p, REG), [])

    def test_poem_accepts_source_stream(self):
        body = POEM_VALID.replace(
            "lines: 14\n",
            "lines: 14\nsource_stream: 2026-04-22-example-music-jam-stream\n",
        )
        p = self._write("poetry", "with-source-stream", body)
        self.assertEqual(lint.lint_file(p, REG), [])

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

    # --- the contract is the registry's (data/sections.json) ---

    def test_registry_is_single_source(self):
        """Mutating the registry must change what the linter accepts."""
        repo = TempRepo()
        try:
            repo.write("content/works/games/g/index.md", GAME_MD_PLAYABLE)
            reg = _registry(enums={("works/games", "status"): ["playible"]})  # deliberate typo
            code, errs = lint.run(repo.root, registry=reg)
            self.assertEqual(code, 1)
            self.assertTrue(any("status='playable'" in e for e in errs), errs)
        finally:
            repo.cleanup()

    def _run_against_registry_file(self, text: str | None) -> tuple[int, list[str]]:
        """run() over a one-game tree with this tree's registry replaced."""
        site, repo = TempRepo(), TempRepo()
        try:
            if text is not None:
                site.write("data/sections.json", text)
            repo.write("content/works/games/g/index.md", GAME_MD_PLAYABLE)
            with mock.patch.object(sections, "SITE_ROOT", site.root), \
                    mock.patch.object(sections, "_CACHE", {}):
                return lint.run(repo.root)
        finally:
            site.cleanup()
            repo.cleanup()

    def test_missing_registry_fails_closed(self):
        """A missing registry must fail, never fall back to a hardcoded copy.

        Reported through the uniform `(rc, errs)` seam rather than by
        `sys.exit` from inside `run()`: an aggregator importing this module
        must not have the process pulled out from under it.
        """
        code, errs = self._run_against_registry_file(None)
        self.assertEqual(code, 1)
        self.assertEqual(len(errs), 1)
        self.assertIn("registry not found at", errs[0])

    def test_run_never_exits_the_process_on_a_bad_registry(self):
        """Malformed JSON is a returned error too, not a SystemExit."""
        code, errs = self._run_against_registry_file("{ not json")
        self.assertEqual(code, 1)
        self.assertIn("is not valid JSON", errs[0])

    def test_poetry_only_tree_needs_no_seeded_registry(self):
        """The registry belongs to the code tree, not the content tree.

        data/works-vocab.json had to be seeded into every works-touching temp
        site root (tools/test_publish_integration.py's
        TestPoetryPublishDeliberate included). sections.json is read from this
        repository, so a bare poetry-only tree lints clean as-is.
        """
        repo = TempRepo()
        try:
            repo.write("content/works/poetry/p/index.md", POEM_VALID)
            self.assertEqual(lint.run(repo.root), (0, []))
        finally:
            repo.cleanup()

    def test_field_sets_come_from_the_registry(self):
        """Dropping an optional key from the registry makes it an unknown field.

        This is what makes data/sections.json the single home of the
        emitted-key contract that the elisp normalizer filters against. If
        this module ever re-hardcodes a field set, the fixture below keeps
        passing and the guard is gone.
        """
        repo = TempRepo()
        try:
            reg = _registry()
            del reg["sections"]["works/games"]["fields"]["length"]
            repo.write(
                "content/works/games/g/index.md",
                GAME_VALID.replace("year: 2026\n", "year: 2026\nlength: '2 hours'\n"),
            )
            code, errs = lint.run(repo.root, registry=reg)
            self.assertEqual(code, 1)
            self.assertTrue(any("unknown field 'length'" in e for e in errs), errs)
        finally:
            repo.cleanup()

    def test_required_sets_come_from_the_registry(self):
        """A key promoted to required in the registry is demanded by the linter."""
        repo = TempRepo()
        try:
            reg = _registry()
            reg["sections"]["works/games"]["fields"]["itch_url"]["required"] = True
            repo.write("content/works/games/g/index.md", GAME_VALID)
            code, errs = lint.run(repo.root, registry=reg)
            self.assertEqual(code, 1)
            self.assertTrue(
                any("missing required field 'itch_url'" in e for e in errs), errs
            )
        finally:
            repo.cleanup()

    def test_umbrella_fields_are_declared_per_sub_section(self):
        """tile_size / featured / hero are listed in each works section.

        works-vocab.json shared one `umbrella_optional` list; the registry has
        no inheritance (spec §4), so dropping tile_size from poetry alone
        rejects it on the poem and nowhere else.
        """
        repo = TempRepo()
        try:
            reg = _registry()
            del reg["sections"]["works/poetry"]["fields"]["tile_size"]
            for sub, body in (
                ("games", GAME_VALID), ("music", MUSIC_VALID), ("poetry", POEM_VALID),
            ):
                repo.write(
                    f"content/works/{sub}/x/index.md",
                    body.replace("---\n\nBody.", "tile_size: large\n---\n\nBody."),
                )
            code, errs = lint.run(repo.root, registry=reg)
            self.assertEqual(code, 1)
            self.assertEqual(
                [e for e in errs if "unknown field 'tile_size'" in e],
                [f"{repo.root}/content/works/poetry/x/index.md: unknown field 'tile_size'"],
            )
        finally:
            repo.cleanup()

    def test_platform_embed_sub_keys_are_closed(self):
        """platform_embed is a registry `object`: an unlisted sub-key now fails."""
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            "year: 2026\nplatform_embed: { kind: bandcamp, url: 'https://x', id: 3 }\n",
        )
        p = self._write("music", "embed-extra", body)
        self.assertEqual(lint.lint_file(p, REG),
                         [f"{p}: unknown field 'platform_embed.id'"])


if __name__ == "__main__":
    unittest.main()
