"""Tests for check_works_fixtures.py — run with:
   python3 -m unittest tools/test_check_works_fixtures.py -v
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_works_fixtures as lint  # noqa: E402
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

# Minimal valid game fixture with status: playable — used by the shared-vocab
# tests below, where TempRepo writes it at an arbitrary path (not necessarily
# "ok") rather than through self._write's games/<slug> convention.
GAME_MD_PLAYABLE = GAME_VALID

REPO_ROOT = Path(__file__).resolve().parent.parent

# Vocab threaded explicitly into every direct lint_file() call in this file.
# lint_file() takes it as a required argument with no fallback
# (check_works_fixtures.py deliberately has no "read the live repo's own
# data/works-vocab.json if omitted" path).
#
# The ENUM values below are hand-written: a test asserting that "shipped" is
# rejected must control the set it is rejected against, or a later addition to
# the real vocabulary would quietly change what the test means.
#
# The FIELD SETS are deliberately NOT written out here. data/works-vocab.json
# is their single home, shared with the elisp normalizer's allowed-key filter,
# and a transcription in this file would be exactly the third copy that made
# the old elisp `-key-set-matches-contract` tests vacuous. They are loaded
# through the same loader the linter uses, so adding an optional key to the
# JSON is picked up here, in the linter and in the publisher at once.
VOCAB = dict(lint.load_vocab(REPO_ROOT))
VOCAB.update({
    "game_statuses": {"playable", "in-progress", "archived"},
    "game_kinds": {"full-release", "jam", "research-prototype", "experiment"},
    "music_formats": {"album", "track", "experiment", "live"},
    "platform_kinds": {"bandcamp", "soundcloud", "youtube"},
})

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

_LIVE = {
    k: sorted(v) for k, v in lint.load_vocab(REPO_ROOT).items()
}


def _vocab_json(**overrides) -> str:
    """The live vocabulary with named lists replaced — a fixture, not a copy.

    Tests that mutate the contract override exactly the list under test and
    inherit the rest, so none of them restates the field sets.
    """
    data = dict(_LIVE)
    data.update(overrides)
    return json.dumps(data)


class WorksFixturesLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.works = self.tmp / "content" / "works"
        for sub in ("games", "music", "poetry"):
            (self.works / sub).mkdir(parents=True)
        # lint.run() fails closed on a missing vocab file (see
        # test_missing_vocab_fails_closed below); seed a real one here so
        # every pre-existing test that goes through run() (test_runner_*)
        # keeps passing. Direct lint_file() calls elsewhere in this file
        # thread the module-level VOCAB constant explicitly instead — they
        # never touch this tempdir's copy or the live repo's.
        (self.tmp / "data").mkdir(parents=True)
        shutil.copyfile(
            REPO_ROOT / lint.VOCAB_REL, self.tmp / "data" / "works-vocab.json"
        )

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
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    def test_game_missing_status(self):
        body = GAME_VALID.replace("status: playable\n", "")
        p = self._write("games", "missing-status", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("missing required field 'status'" in e for e in errs))

    def test_game_bad_status_enum(self):
        body = GAME_VALID.replace("status: playable", "status: shipped")
        p = self._write("games", "bad-status", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("status='shipped'" in e for e in errs))

    def test_game_bad_kind_enum(self):
        body = GAME_VALID.replace("game_kind: full-release", "game_kind: walking-sim")
        p = self._write("games", "bad-kind", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("game_kind='walking-sim'" in e for e in errs))

    def test_game_year_not_int(self):
        body = GAME_VALID.replace("year: 2026", "year: 'twenty-six'")
        p = self._write("games", "bad-year", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("year" in e and "integer" in e for e in errs))

    def test_game_unknown_field(self):
        body = GAME_VALID.replace("year: 2026\n", "year: 2026\nrarity: 99\n")
        p = self._write("games", "extra-field", body)
        errs = lint.lint_file(p, VOCAB)
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
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    # --- music contract ---

    def test_music_valid_passes(self):
        p = self._write("music", "ok", MUSIC_VALID)
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    def test_music_missing_format(self):
        body = MUSIC_VALID.replace("format: album\n", "")
        p = self._write("music", "missing-format", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("missing required field 'format'" in e for e in errs))

    def test_music_bad_format_enum(self):
        body = MUSIC_VALID.replace("format: album", "format: cassette")
        p = self._write("music", "bad-format", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("format='cassette'" in e for e in errs))

    def test_music_platform_embed_bad_kind(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            "year: 2026\nplatform_embed: { kind: spotify, url: 'https://example.com' }\n",
        )
        p = self._write("music", "bad-embed-kind", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("platform_embed.kind='spotify'" in e for e in errs))

    def test_music_platform_embed_missing_url(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            "year: 2026\nplatform_embed: { kind: bandcamp }\n",
        )
        p = self._write("music", "embed-no-url", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("platform_embed.url" in e and "missing" in e for e in errs))

    def test_music_tracks_shape(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            'year: 2026\ntracks:\n  - { title: "Track 1", duration: "3:14" }\n  - { title: "Track 2", duration: "4:20" }\n',
        )
        p = self._write("music", "good-tracks", body)
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    def test_music_track_missing_duration(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            'year: 2026\ntracks:\n  - { title: "Track 1" }\n',
        )
        p = self._write("music", "bad-track", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("tracks[0]" in e for e in errs))

    def test_music_unknown_field(self):
        body = MUSIC_VALID.replace("year: 2026\n", "year: 2026\nbpm: 128\n")
        p = self._write("music", "extra-field", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("unknown field 'bpm'" in e for e in errs))

    # --- poetry contract ---

    def test_poem_valid_passes(self):
        p = self._write("poetry", "ok", POEM_VALID)
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    def test_poem_missing_lines(self):
        body = POEM_VALID.replace("lines: 14\n", "")
        p = self._write("poetry", "missing-lines", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("missing required field 'lines'" in e for e in errs))

    def test_poem_lines_not_int(self):
        body = POEM_VALID.replace("lines: 14", "lines: 'fourteen'")
        p = self._write("poetry", "bad-lines", body)
        errs = lint.lint_file(p, VOCAB)
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
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    def test_poem_accepts_audio_url(self):
        body = POEM_VALID.replace(
            "lines: 14\n",
            'lines: 14\naudio_url: "https://example.com/reading.mp3"\n',
        )
        p = self._write("poetry", "with-audio", body)
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    def test_poem_audio_url_relative_accepted_by_fixture_linter(self):
        # check_works_fixtures only validates *shape* (unknown-field gate);
        # path/URL validity is the synced-poetry linter's job (Task 2).
        body = POEM_VALID.replace(
            "lines: 14\n",
            'lines: 14\naudio_url: reading.mp3\n',
        )
        p = self._write("poetry", "with-audio-rel", body)
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    # --- umbrella (Bento grid) fields ---

    def test_game_accepts_tile_size_featured_hero(self):
        body = GAME_VALID.replace(
            "year: 2026\n",
            "year: 2026\ntile_size: large\nfeatured: true\nhero: true\n",
        )
        p = self._write("games", "with-umbrella", body)
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    def test_music_accepts_tile_size_featured_hero(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            "year: 2026\ntile_size: small\nfeatured: true\nhero: false\n",
        )
        p = self._write("music", "with-umbrella", body)
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    def test_poem_accepts_tile_size_featured_hero(self):
        body = POEM_VALID.replace(
            "lines: 14\n",
            "lines: 14\ntile_size: medium\nfeatured: false\nhero: true\n",
        )
        p = self._write("poetry", "with-umbrella", body)
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    def test_tile_size_must_be_in_enum(self):
        body = GAME_VALID.replace(
            "year: 2026\n",
            "year: 2026\ntile_size: huge\n",
        )
        p = self._write("games", "bad-tile-size", body)
        errs = lint.lint_file(p, VOCAB)
        self.assertTrue(any("tile_size='huge'" in e for e in errs), errs)

    # --- source_stream (streams-section back-edge) ---

    def test_game_accepts_source_stream(self):
        body = GAME_VALID.replace(
            "year: 2026\n",
            "year: 2026\nsource_stream: 2026-04-10-example-live-coding-stream\n",
        )
        p = self._write("games", "with-source-stream", body)
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    def test_music_accepts_source_stream(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            "year: 2026\nsource_stream: 2026-04-22-example-music-jam-stream\n",
        )
        p = self._write("music", "with-source-stream", body)
        self.assertEqual(lint.lint_file(p, VOCAB), [])

    def test_poem_accepts_source_stream(self):
        body = POEM_VALID.replace(
            "lines: 14\n",
            "lines: 14\nsource_stream: 2026-04-22-example-music-jam-stream\n",
        )
        p = self._write("poetry", "with-source-stream", body)
        self.assertEqual(lint.lint_file(p, VOCAB), [])

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

    # --- shared enum vocabulary (single-sourced with the elisp linter) ---

    def test_vocab_is_single_source(self):
        """Mutating the vocab file must change what the linter accepts."""
        repo = TempRepo()
        try:
            repo.write("data/works-vocab.json", _vocab_json(
                game_statuses=["playible"],             # deliberate typo
            ))
            repo.write("content/works/games/g/index.md", GAME_MD_PLAYABLE)
            code, errs = lint.run(repo.root)
            self.assertEqual(code, 1)
            self.assertTrue(any("status='playable'" in e for e in errs), errs)
        finally:
            repo.cleanup()

    def test_missing_vocab_fails_closed(self):
        """A missing vocab file must fail, never fall back to a hardcoded copy.

        Reported through the uniform `(rc, errs)` seam rather than by
        `sys.exit` from inside `run()`: an aggregator importing this module
        must not have the process pulled out from under it.
        """
        repo = TempRepo()
        try:
            repo.write("content/works/games/g/index.md", GAME_MD_PLAYABLE)
            code, errs = lint.run(repo.root)
            self.assertEqual(code, 1)
            self.assertEqual(len(errs), 1)
            self.assertIn("vocabulary not found at", errs[0])
        finally:
            repo.cleanup()

    def test_poetry_only_tree_still_requires_the_vocabulary(self):
        """A works tree with no games/music still reads the vocabulary.

        `run()` used to load it lazily, only on reaching a games/music
        fixture, so a poetry-only site root needed no vocabulary file at all.
        That laziness stopped being correct when `umbrella_optional` moved
        into the vocabulary: `poem_fields()` composes from it. The consequence
        is load-bearing for a caller outside this file —
        `tools/test_publish_integration.py`'s `TestPoetryPublishDeliberate`
        builds a poetry-only site root and asserts `run(...) == 0`, and it had
        to start seeding `data/works-vocab.json` in `setUp`. Pinned here
        because that integration test needs a subprocess `emacs --batch` and
        can be skipped or environment-blocked, so it is not a reliable guard
        for this contract.
        """
        repo = TempRepo()
        try:
            repo.write("content/works/poetry/p/index.md", POEM_VALID)
            code, errs = lint.run(repo.root)
            self.assertEqual(code, 1)
            self.assertIn("vocabulary not found at", errs[0])
            # ...and with the file present it is clean again.
            repo.write("data/works-vocab.json", _vocab_json())
            self.assertEqual(lint.run(repo.root), (0, []))
        finally:
            repo.cleanup()

    def test_run_never_exits_the_process_on_a_bad_vocab(self):
        """Malformed JSON is a returned error too, not a SystemExit."""
        repo = TempRepo()
        try:
            repo.write("data/works-vocab.json", "{ not json")
            repo.write("content/works/games/g/index.md", GAME_MD_PLAYABLE)
            code, errs = lint.run(repo.root)
            self.assertEqual(code, 1)
            self.assertIn("is not valid JSON", errs[0])
        finally:
            repo.cleanup()

    # --- the field-set contract is vocabulary-owned, not hardcoded here ---

    def test_field_sets_come_from_the_vocabulary_file(self):
        """Dropping an optional key from the JSON must make it an unknown field.

        This is what makes data/works-vocab.json the single home of the
        emitted-key contract that the elisp normalizer filters against. If
        this module ever re-hardcodes GAME_FIELDS, the fixture below keeps
        passing and the guard is gone.
        """
        repo = TempRepo()
        try:
            repo.write("data/works-vocab.json", _vocab_json(
                game_optional=[k for k in _LIVE["game_optional"] if k != "length"],
            ))
            repo.write(
                "content/works/games/g/index.md",
                GAME_VALID.replace("year: 2026\n", "year: 2026\nlength: '2 hours'\n"),
            )
            code, errs = lint.run(repo.root)
            self.assertEqual(code, 1)
            self.assertTrue(any("unknown field 'length'" in e for e in errs), errs)
        finally:
            repo.cleanup()

    def test_required_sets_come_from_the_vocabulary_file(self):
        """A key promoted to required in the JSON is demanded by the linter."""
        repo = TempRepo()
        try:
            repo.write("data/works-vocab.json", _vocab_json(
                game_required=sorted(set(_LIVE["game_required"]) | {"itch_url"}),
            ))
            repo.write("content/works/games/g/index.md", GAME_VALID)
            code, errs = lint.run(repo.root)
            self.assertEqual(code, 1)
            self.assertTrue(
                any("missing required field 'itch_url'" in e for e in errs), errs
            )
        finally:
            repo.cleanup()

    def test_umbrella_optional_is_shared_by_all_three_sub_sections(self):
        """One `umbrella_optional` list feeds games, music AND poetry."""
        repo = TempRepo()
        try:
            repo.write("data/works-vocab.json", _vocab_json(umbrella_optional=[]))
            for sub, body in (
                ("games", GAME_VALID), ("music", MUSIC_VALID), ("poetry", POEM_VALID),
            ):
                repo.write(
                    f"content/works/{sub}/x/index.md",
                    body.replace("---\n\nBody.", "tile_size: large\n---\n\nBody."),
                )
            code, errs = lint.run(repo.root)
            self.assertEqual(code, 1)
            self.assertEqual(
                sum(1 for e in errs if "unknown field 'tile_size'" in e), 3, errs
            )
        finally:
            repo.cleanup()


if __name__ == "__main__":
    unittest.main()
