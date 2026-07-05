"""Tests for check_filter_chips_config.py — run with:
   python3 -m unittest tools/test_check_filter_chips_config.py -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_filter_chips_config as lint  # noqa: E402
from test_helpers import TempRepo as _TempRepo  # noqa: E402


GARDEN_NOTE = """\
---
title: "Salience and memory"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
tags: ["memory", "narrative"]
---

Body.
"""

ESSAY_NOTE = """\
---
title: "Example essay"
date: 2026-01-01
lastmod: 2026-01-01
draft: false
summary: "x"
tags: ["example-tag-a", "example-tag-b"]
series: ""
series_order: 0
toc: false
has_sidenotes: false
has_citations: false
has_footnotes: false
has_math: false
has_widgets: false
has_video_sync: false
---

Body.
"""

GAME_NOTE = """\
---
title: "Example game"
date: 2026-01-01
lastmod: 2026-01-01
draft: false
status: playable
game_kind: full-release
tagline: "A game."
year: 2026
tags: ["example", "demo"]
---

Body.
"""

MUSIC_NOTE = """\
---
title: "Example album"
date: 2026-01-01
lastmod: 2026-01-01
draft: false
format: album
year: 2026
tags: ["example", "ambient"]
---

Body.
"""

POEM_NOTE = """\
---
title: "Example poem"
date: 2026-01-01
lastmod: 2026-01-01
draft: false
lines: 4
tags: ["example", "lyric"]
---

Body.
"""


READING_YAML_ITEM = """\
items:
  - slug: example-book
    title: Example Book
    creator: Author One
    year: 2024
    media_type: book
    status: finished
    finished: 2024-06-01
    last_modified: 2024-06-01
    tags: [fiction, non-fiction]
"""


class TempRepo(_TempRepo):
    def __init__(self) -> None:
        super().__init__()
        (self.root / "content" / "garden").mkdir(parents=True)
        (self.root / "content" / "essays").mkdir(parents=True)
        (self.root / "content" / "works" / "games").mkdir(parents=True)
        (self.root / "content" / "works" / "music").mkdir(parents=True)
        (self.root / "content" / "works" / "poetry").mkdir(parents=True)
        (self.root / "data").mkdir(parents=True)

    def write_garden(self, slug: str, body: str = GARDEN_NOTE) -> None:
        self.write(f"content/garden/{slug}/index.md", body)

    def write_essay(self, slug: str, body: str = ESSAY_NOTE) -> None:
        self.write(f"content/essays/{slug}/index.md", body)

    def write_game(self, slug: str, body: str = GAME_NOTE) -> None:
        self.write(f"content/works/games/{slug}/index.md", body)

    def write_music(self, slug: str, body: str = MUSIC_NOTE) -> None:
        self.write(f"content/works/music/{slug}/index.md", body)

    def write_poem(self, slug: str, body: str = POEM_NOTE) -> None:
        self.write(f"content/works/poetry/{slug}/index.md", body)

    def write_config(self, content: str) -> None:
        self.write("data/filter-chips.yaml", content)

    def write_library_yaml(self, fname: str, body: str = READING_YAML_ITEM) -> None:
        """Write a library data yaml file (e.g., 'reading.yaml') under data/."""
        self.write(f"data/{fname}", body)


class FilterChipsLinterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    # --- happy paths ---

    def test_no_config_file_passes(self) -> None:
        # Auto-fallback applies at build time; absence is not an error.
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_config_with_no_sections_passes(self) -> None:
        self.repo.write_config("# empty\n")
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_garden_curation_passes(self) -> None:
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["memory", "narrative"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_top_k_override_passes(self) -> None:
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: 8\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_empty_primary_tags_passes(self) -> None:
        # Empty list means auto-fallback at build time.
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: []\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_section_not_in_config_passes(self) -> None:
        # essays section absent from config → auto-fallback applies.
        self.repo.write_garden("salience-and-memory")
        self.repo.write_essay("essay-1")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["memory"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    # --- failures ---

    def test_stale_garden_tag_fails(self) -> None:
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["memory", "ghost-tag"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        joined = "\n".join(errors)
        self.assertIn("ghost-tag", joined)
        self.assertIn("garden", joined)

    def test_stale_essay_tag_fails(self) -> None:
        self.repo.write_essay("essay-1")
        self.repo.write_config(
            'essays:\n'
            '  primary_tags: ["nope"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("nope" in e and "essays" in e for e in errors))

    def test_draft_only_tag_does_not_count(self) -> None:
        # A tag that appears only on drafts must not satisfy primary_tags.
        draft = GARDEN_NOTE.replace("draft: false", "draft: true").replace(
            '["memory", "narrative"]', '["draft-only"]'
        )
        self.repo.write_garden("draft-note", draft)
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["draft-only"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("draft-only" in e for e in errors))

    def test_invalid_top_k_string_fails(self) -> None:
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: "ten"\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("primary_top_k" in e for e in errors))

    def test_invalid_top_k_zero_fails(self) -> None:
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: 0\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("primary_top_k" in e for e in errors))

    def test_invalid_top_k_negative_fails(self) -> None:
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: -1\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("primary_top_k" in e for e in errors))

    def test_indent_typo_fails(self) -> None:
        # 4-space indent silently skipped before fix; now emits a parse error.
        self.repo.write_config(
            'garden:\n'
            '    primary_tags: ["memory"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        joined = "\n".join(errors)
        self.assertIn("data/filter-chips.yaml", joined)
        self.assertTrue(any("unrecognized line" in e for e in errors))

    def test_unknown_key_fails(self) -> None:
        # `primary_tag` (singular) is a typo for `primary_tags`.
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_tag: ["memory"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(
            any("primary_tag" in e and "is not a recognized key" in e for e in errors)
        )

    # --- works subsection path mapping ---

    def test_valid_games_curation_passes(self) -> None:
        self.repo.write_game("example-game")
        self.repo.write_config(
            'games:\n'
            '  primary_tags: ["example", "demo"]\n'
            '  primary_top_k: 10\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_music_curation_passes(self) -> None:
        self.repo.write_music("example-album")
        self.repo.write_config(
            'music:\n'
            '  primary_tags: ["example", "ambient"]\n'
            '  primary_top_k: 10\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_poetry_curation_passes(self) -> None:
        self.repo.write_poem("example-poem")
        self.repo.write_config(
            'poetry:\n'
            '  primary_tags: ["example", "lyric"]\n'
            '  primary_top_k: 10\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_stale_games_tag_fails(self) -> None:
        self.repo.write_game("example-game")
        self.repo.write_config(
            'games:\n'
            '  primary_tags: ["example", "ghost-game-tag"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        joined = "\n".join(errors)
        self.assertIn("ghost-game-tag", joined)
        self.assertIn("games", joined)

    # --- works aggregation (games + music + poetry) ---

    def test_works_primary_resolves_against_all_three_subs(self) -> None:
        # The `works` key aggregates tags across games / music / poetry.
        self.repo.write_game("g1")  # has tags ["example", "demo"]
        self.repo.write_music("m1")  # has tags ["example", "ambient"]
        self.repo.write_poem("p1")  # has tags ["example", "lyric"]
        self.repo.write_config(
            'works:\n'
            '  primary_tags: ["demo", "ambient", "lyric"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_works_primary_rejects_tag_not_in_any_sub(self) -> None:
        # A tag that doesn't appear in any of the three sub-sections must fail.
        self.repo.write_game("g1")  # has tags ["example", "demo"]
        self.repo.write_music("m1")  # has tags ["example", "ambient"]
        self.repo.write_poem("p1")  # has tags ["example", "lyric"]
        self.repo.write_config(
            'works:\n'
            '  primary_tags: ["ghost-tag"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("ghost-tag" in e for e in errors), errors)

    # --- library yaml-source path ---

    def test_library_reading_valid_tag_passes(self) -> None:
        # Happy path: primary_tags entry present in data/reading.yaml.
        self.repo.write_library_yaml("reading.yaml")  # has tags [fiction, non-fiction]
        self.repo.write_config(
            'library-reading:\n'
            '  primary_tags: ["fiction"]\n'
            '  primary_top_k: 10\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_library_reading_missing_tag_fails(self) -> None:
        # Sad path: primary_tags entry not present in data/reading.yaml.
        self.repo.write_library_yaml("reading.yaml")  # has tags [fiction, non-fiction]
        self.repo.write_config(
            'library-reading:\n'
            '  primary_tags: ["missing-tag"]\n'
            '  primary_top_k: 10\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("missing-tag" in e for e in errors), errors)

    # --- streams section default path mapping ---

    def test_streams_section_default_path(self) -> None:
        # The default branch should map 'streams' → content/streams/ without
        # needing a SECTION_PATH_OVERRIDES entry.
        paths = lint._section_content_paths(self.repo.root, "streams")
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].name, "streams")
        self.assertEqual(paths[0].parent.name, "content")


if __name__ == "__main__":
    unittest.main()
