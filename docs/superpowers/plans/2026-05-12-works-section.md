# Works section — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Works umbrella + games/music/poetry indexes + per-item page templates with 12 fixtures and two new CI gates. Runtime-heavy pieces (iframes, custom audio widget, synced-lyrics playback) stay as `data-pending` stubs and ship in follow-up slices.

**Architecture:** Three new Hugo type-discriminated layout trees (`works-games`, `works-music`, `works-poetry`) plus an umbrella `works` list layout. Eight new partials under `partials/works/`. One no-op shortcode (`lyrics`). Four new CSS sections (§32–§35, ~380 lines) appended to `assets/css/main.css`. Two new stdlib-only Python linters (`check_works_fixtures.py` + `check_works_links.py`) wired as CI gates with companion unit-test suites.

**Tech Stack:** Hugo extended (≥ 0.148.0), hand-rolled CSS (single `main.css`, numbered sections), Python 3 stdlib (linters + tests). One tiny JS module (`works.js`, ~0.5 KB) wires the shared `filter-chips.js` to the three Works index pages; deferred-runtime stubs (iframes, audio player, synced-lyrics player) ship without JS.

**Spec:** `docs/superpowers/specs/2026-05-12-works-section-design.md` (commit `ea3f7af`).

---

## Task 1: Branch + sub-section _index.md scaffolding

**Why first:** Subsequent tasks need the section structure to exist so Hugo can resolve types correctly. Also creates the branch on master.

**Files:**
- Create: `content/works/games/_index.md`
- Create: `content/works/music/_index.md`
- Create: `content/works/poetry/_index.md`
- Modify: `content/works/_index.md`

- [ ] **Step 1: Create the working branch**

```bash
git checkout -b slice/works-section
```

Expected: `Switched to a new branch 'slice/works-section'`

- [ ] **Step 2: Write `content/works/games/_index.md`**

```yaml
---
title: 'Games'
description: 'Games I have made.'
type: works-games
cascade:
  type: works-games
---
```

- [ ] **Step 3: Write `content/works/music/_index.md`**

```yaml
---
title: 'Music'
description: 'Music I have made.'
type: works-music
cascade:
  type: works-music
---
```

- [ ] **Step 4: Write `content/works/poetry/_index.md`**

```yaml
---
title: 'Poetry'
description: 'Poems I have written.'
type: works-poetry
cascade:
  type: works-poetry
---
```

- [ ] **Step 5: Update `content/works/_index.md` to remove "Coming soon."**

Replace the entire file with:

```yaml
---
title: 'Works'
description: 'Games, music, and poetry.'
---
```

- [ ] **Step 6: Commit the scaffolding**

```bash
git add content/works/
git commit -m "$(cat <<'EOF'
works: scaffold sub-section _index files

games/music/poetry each set type: + cascade.type: so the bare section
URLs resolve to layouts/works-<sub>/list.html and per-item pages
resolve to layouts/works-<sub>/single.html. Umbrella _index loses
'Coming soon.' placeholder body.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Linter A (fixtures) — test scaffold

**Why:** TDD for the linter. Write tests against a not-yet-existent `check_works_fixtures.py`; import will fail until Task 4 lands.

**Files:**
- Create: `tools/test_check_works_fixtures.py`

- [ ] **Step 1: Write the test harness file**

```python
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
```

- [ ] **Step 2: Run the file to confirm import-time failure**

```bash
python3 -m unittest tools/test_check_works_fixtures.py -v
```

Expected: `ModuleNotFoundError: No module named 'check_works_fixtures'`

- [ ] **Step 3: Commit the scaffold**

```bash
git add tools/test_check_works_fixtures.py
git commit -m "$(cat <<'EOF'
test: scaffold check_works_fixtures test harness

Helpers + base class. Fails at import time until check_works_fixtures.py lands.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Linter A — full test coverage (games + music + poetry contracts)

**Files:**
- Modify: `tools/test_check_works_fixtures.py`

- [ ] **Step 1: Append all test methods to the class body**

Insert the following methods inside `class WorksFixturesLinterTests:` (above the `if __name__` block):

```python
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

    def test_game_bad_type_enum(self):
        body = GAME_VALID.replace("type: full-release", "type: walking-sim")
        p = self._write("games", "bad-type", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("type='walking-sim'" in e for e in errs))

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
type: research-prototype
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

    def test_music_tracks_shape(self):
        body = MUSIC_VALID + """tracks:
  - { title: "Track 1", duration: "3:14" }
  - { title: "Track 2", duration: "4:20" }
"""
        p = self._write("music", "good-tracks", body)
        self.assertEqual(lint.lint_file(p), [])

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
```

- [ ] **Step 2: Run the tests to verify all fail (still no `check_works_fixtures.py`)**

```bash
python3 -m unittest tools/test_check_works_fixtures.py -v
```

Expected: `ModuleNotFoundError: No module named 'check_works_fixtures'` (immediate at import).

- [ ] **Step 3: Commit the test cases**

```bash
git add tools/test_check_works_fixtures.py
git commit -m "$(cat <<'EOF'
test: check_works_fixtures spec — games + music + poetry contracts

19 test cases across all three contracts plus runner aggregation.
Required-field detection, enum validation, integer typing, unknown-
field rejection, and the all-optionals happy path each get one test.
Still fails at import time until the linter lands.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Linter A — implementation

**Files:**
- Create: `tools/check_works_fixtures.py`

- [ ] **Step 1: Write the linter**

```python
#!/usr/bin/env python3
"""Works fixture frontmatter linter.

Walks `content/works/{games,music,poetry}/<slug>/index.md`, validates
per-type contracts (see docs/superpowers/specs/2026-05-12-works-section-design.md).

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

# --- contracts ---

GAME_REQUIRED = {"title", "date", "lastmod", "draft", "status", "type", "tagline", "year"}
GAME_OPTIONAL = {
    "tags", "summary", "hero", "embed_url", "source_url", "itch_url",
    "collaborators", "tech_stack", "length", "screenshots",
    "research_questions", "related_essays", "related_notes",
}
GAME_FIELDS = GAME_REQUIRED | GAME_OPTIONAL
GAME_STATUSES = {"playable", "in-progress", "archived"}
GAME_TYPES = {"full-release", "jam", "research-prototype", "experiment"}

MUSIC_REQUIRED = {"title", "date", "lastmod", "draft", "format", "year"}
MUSIC_OPTIONAL = {
    "tags", "summary", "tagline", "cover", "duration",
    "tracks", "platform_embed", "audio_url", "lyrics_poem",
    "related_works", "related_essays", "made_with", "collaborators",
}
MUSIC_FIELDS = MUSIC_REQUIRED | MUSIC_OPTIONAL
MUSIC_FORMATS = {"album", "track", "experiment", "live"}
PLATFORM_KINDS = {"bandcamp", "soundcloud", "youtube"}

POEM_REQUIRED = {"title", "date", "lastmod", "draft", "lines"}
POEM_OPTIONAL = {"tags", "collection", "set_to_music", "summary"}
POEM_FIELDS = POEM_REQUIRED | POEM_OPTIONAL


def lint_file(md: Path) -> list[str]:
    """Return a list of error strings for a single fixture index.md.

    Sub-section is derived from the path: content/works/<sub>/<slug>/index.md.
    """
    parts = md.parts
    try:
        works_idx = parts.index("works")
        sub = parts[works_idx + 1]
    except (ValueError, IndexError):
        return [f"{md}: cannot determine sub-section from path"]

    if not md.exists():
        return [f"{md}: file does not exist"]

    text = md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md}: no frontmatter"]

    if sub == "games":
        return _lint_game(md, fm)
    if sub == "music":
        return _lint_music(md, fm)
    if sub == "poetry":
        return _lint_poem(md, fm)
    return [f"{md}: unknown works sub-section '{sub}'"]


def _lint_game(md: Path, fm: dict[str, object]) -> list[str]:
    errs: list[str] = []
    for f in sorted(GAME_REQUIRED - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - GAME_FIELDS):
        errs.append(f"{md}: unknown field '{f}'")

    status = fm.get("status")
    if status is not None and status not in GAME_STATUSES:
        errs.append(f"{md}: status='{status}' not in {sorted(GAME_STATUSES)}")

    gtype = fm.get("type")
    if gtype is not None and gtype not in GAME_TYPES:
        errs.append(f"{md}: type='{gtype}' not in {sorted(GAME_TYPES)}")

    year = fm.get("year")
    if year is not None and not isinstance(year, int):
        errs.append(f"{md}: year must be an integer, got {type(year).__name__}")

    screenshots = fm.get("screenshots")
    if screenshots is not None and not isinstance(screenshots, list):
        errs.append(f"{md}: screenshots must be a list of strings")

    return errs


def _lint_music(md: Path, fm: dict[str, object]) -> list[str]:
    errs: list[str] = []
    for f in sorted(MUSIC_REQUIRED - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - MUSIC_FIELDS):
        errs.append(f"{md}: unknown field '{f}'")

    fmt = fm.get("format")
    if fmt is not None and fmt not in MUSIC_FORMATS:
        errs.append(f"{md}: format='{fmt}' not in {sorted(MUSIC_FORMATS)}")

    year = fm.get("year")
    if year is not None and not isinstance(year, int):
        errs.append(f"{md}: year must be an integer, got {type(year).__name__}")

    tracks = fm.get("tracks")
    if tracks is not None:
        if not isinstance(tracks, list):
            errs.append(f"{md}: tracks must be a list")
        else:
            for i, t in enumerate(tracks):
                if not isinstance(t, dict):
                    errs.append(f"{md}: tracks[{i}] must be a dict")
                    continue
                if "title" not in t or "duration" not in t:
                    errs.append(f"{md}: tracks[{i}] requires title + duration")

    pe = fm.get("platform_embed")
    if pe is not None:
        if not isinstance(pe, dict):
            errs.append(f"{md}: platform_embed must be a dict")
        else:
            kind = pe.get("kind")
            if kind is None:
                errs.append(f"{md}: platform_embed.kind missing")
            elif kind not in PLATFORM_KINDS:
                errs.append(f"{md}: platform_embed.kind='{kind}' not in {sorted(PLATFORM_KINDS)}")
            if "url" not in pe:
                errs.append(f"{md}: platform_embed.url missing")

    return errs


def _lint_poem(md: Path, fm: dict[str, object]) -> list[str]:
    errs: list[str] = []
    for f in sorted(POEM_REQUIRED - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - POEM_FIELDS):
        errs.append(f"{md}: unknown field '{f}'")

    lines = fm.get("lines")
    if lines is not None and not isinstance(lines, int):
        errs.append(f"{md}: lines must be an integer, got {type(lines).__name__}")

    return errs


def run(repo_root: Path) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    works = repo_root / "content" / "works"
    if not works.exists():
        return 0, []
    for sub in ("games", "music", "poetry"):
        sub_dir = works / sub
        if not sub_dir.exists():
            continue
        for child in sorted(sub_dir.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            if not md.exists():
                continue
            all_errs.extend(lint_file(md))
    return (1 if all_errs else 0), all_errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_works_fixtures: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the tests to verify all pass**

```bash
python3 -m unittest tools/test_check_works_fixtures.py -v
```

Expected: 19 tests, all OK.

- [ ] **Step 3: Run the linter against the current (empty) content tree**

```bash
python3 tools/check_works_fixtures.py
```

Expected: `check_works_fixtures: OK` (no fixtures exist yet — empty pass is correct).

- [ ] **Step 4: Commit**

```bash
git add tools/check_works_fixtures.py
git commit -m "$(cat <<'EOF'
tools: add check_works_fixtures linter

Validates per-type contracts under content/works/{games,music,poetry}.
Required/optional/forbidden field enforcement, enum validation for
status/type/format/platform_embed.kind, integer typing for year/lines,
list-of-dict shape check for tracks. Reuses shared parse_frontmatter
from check_fixtures.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Linter B (links) — test scaffold

**Files:**
- Create: `tools/test_check_works_links.py`

- [ ] **Step 1: Write the harness**

```python
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
```

- [ ] **Step 2: Run to confirm import-time failure**

```bash
python3 -m unittest tools/test_check_works_links.py -v
```

Expected: `ModuleNotFoundError: No module named 'check_works_links'`

- [ ] **Step 3: Commit**

```bash
git add tools/test_check_works_links.py
git commit -m "$(cat <<'EOF'
test: scaffold check_works_links test harness

Helpers + base class with all relevant content sub-trees pre-created.
Fails at import time until check_works_links.py lands.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Linter B — full test coverage

**Files:**
- Modify: `tools/test_check_works_links.py`

- [ ] **Step 1: Append test methods inside `WorksLinksLinterTests:`**

```python
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
            "draft": "false", "status": "playable", "type": "full-release",
            "tagline": "ok", "year": 2026,
            "research_questions": ["/research/questions/q-a/"],
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_game_research_questions_dangling_fails(self):
        self._write("works/games/game-a", {
            "title": "Game A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "status": "playable", "type": "full-release",
            "tagline": "ok", "year": 2026,
            "research_questions": ["/research/questions/missing/"],
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("missing" in e for e in errs))

    def test_game_related_essays_dangling_fails(self):
        self._write("works/games/game-a", {
            "title": "Game A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "status": "playable", "type": "full-release",
            "tagline": "ok", "year": 2026,
            "related_essays": ["/essays/nonexistent/"],
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("/essays/nonexistent/" in e for e in errs))

    def test_game_related_notes_dangling_fails(self):
        self._write("works/games/game-a", {
            "title": "Game A", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "status": "playable", "type": "full-release",
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
            "draft": "false", "status": "playable", "type": "full-release",
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
```

- [ ] **Step 2: Run tests to confirm import failure still surfaces**

```bash
python3 -m unittest tools/test_check_works_links.py -v
```

Expected: `ModuleNotFoundError: No module named 'check_works_links'`

- [ ] **Step 3: Commit**

```bash
git add tools/test_check_works_links.py
git commit -m "$(cat <<'EOF'
test: check_works_links spec — round-trip + cross-section refs

10 test cases covering lyrics ↔ set_to_music round-trip enforcement,
dangling targets for music/poetry/games refs, draft-target rejection,
and empty-tree pass. Still fails at import time.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Linter B — implementation

**Files:**
- Create: `tools/check_works_links.py`

- [ ] **Step 1: Write the linter**

```python
#!/usr/bin/env python3
"""Works cross-reference linter.

Resolves every cross-reference field on content/works/* fixtures against
the live content tree:

  - music.lyrics_poem → content/works/poetry/<slug>/index.md (non-draft)
  - poetry.set_to_music → content/works/music/<slug>/index.md (non-draft)
  - Round-trip: music[M].lyrics_poem == P  ⟹  poetry[P].set_to_music == M
  - games.research_questions[*] → content/research/questions/<slug>/index.md
  - games.related_essays[*]     → content/essays/<slug>/index.md
  - games.related_notes[*]      → content/garden/<slug>/index.md
  - music.related_essays[*]     → content/essays/<slug>/index.md
  - music.related_works[*]      → content/works/<sub>/<slug>/index.md

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


PATH_STRIP_RE = re.compile(r"^/+|/+$")


def _resolve_to_index(content_root: Path, rel_url: str) -> Path:
    """Map a Hugo-style URL like '/essays/foo/' to a filesystem index.md path."""
    stripped = PATH_STRIP_RE.sub("", rel_url)
    return content_root / stripped / "index.md"


def _is_draft(md: Path) -> bool:
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return False
    return bool(fm.get("draft"))


def _load_fm(md: Path) -> dict[str, object] | None:
    if not md.exists():
        return None
    return parse_frontmatter(md.read_text())


def lint_cross_refs(content_root: Path) -> list[str]:
    errs: list[str] = []

    music_dir = content_root / "works" / "music"
    poetry_dir = content_root / "works" / "poetry"
    games_dir = content_root / "works" / "games"

    music_fms: dict[str, dict[str, object]] = {}
    if music_dir.exists():
        for child in sorted(music_dir.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            fm = _load_fm(md)
            if fm is not None:
                music_fms[child.name] = fm

    poetry_fms: dict[str, dict[str, object]] = {}
    if poetry_dir.exists():
        for child in sorted(poetry_dir.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            fm = _load_fm(md)
            if fm is not None:
                poetry_fms[child.name] = fm

    games_fms: dict[str, dict[str, object]] = {}
    if games_dir.exists():
        for child in sorted(games_dir.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            fm = _load_fm(md)
            if fm is not None:
                games_fms[child.name] = fm

    # music.lyrics_poem resolution + round-trip
    for slug, fm in music_fms.items():
        target = fm.get("lyrics_poem")
        if target is None:
            continue
        target_str = str(target)
        if target_str not in poetry_fms:
            errs.append(f"works/music/{slug}: lyrics_poem='{target_str}' does not resolve to an existing poem")
            continue
        if poetry_fms[target_str].get("draft"):
            errs.append(f"works/music/{slug}: lyrics_poem='{target_str}' targets a draft poem")
            continue
        back = poetry_fms[target_str].get("set_to_music")
        if str(back) != slug:
            errs.append(
                f"works/music/{slug}: asymmetric round-trip — "
                f"music.lyrics_poem='{target_str}' but poetry/{target_str}.set_to_music='{back}'"
            )

    # poetry.set_to_music resolution
    for slug, fm in poetry_fms.items():
        target = fm.get("set_to_music")
        if target is None:
            continue
        target_str = str(target)
        if target_str not in music_fms:
            errs.append(f"works/poetry/{slug}: set_to_music='{target_str}' does not resolve to an existing music piece")
            continue
        if music_fms[target_str].get("draft"):
            errs.append(f"works/poetry/{slug}: set_to_music='{target_str}' targets a draft music piece")

    # games cross-section refs
    for slug, fm in games_fms.items():
        for field, label in [
            ("research_questions", "research_questions"),
            ("related_essays", "related_essays"),
            ("related_notes", "related_notes"),
        ]:
            refs = fm.get(field)
            if not refs:
                continue
            if not isinstance(refs, list):
                continue
            for ref in refs:
                _validate_url_ref(content_root, f"works/games/{slug}", label, str(ref), errs)

    # music cross-section refs
    for slug, fm in music_fms.items():
        for field, label in [
            ("related_essays", "related_essays"),
            ("related_works", "related_works"),
        ]:
            refs = fm.get(field)
            if not refs:
                continue
            if not isinstance(refs, list):
                continue
            for ref in refs:
                _validate_url_ref(content_root, f"works/music/{slug}", label, str(ref), errs)

    return errs


def _validate_url_ref(content_root: Path, source: str, field: str, ref: str, errs: list[str]) -> None:
    md = _resolve_to_index(content_root, ref)
    if not md.exists():
        errs.append(f"{source}: {field} ref '{ref}' does not resolve to an existing page")
        return
    if _is_draft(md):
        errs.append(f"{source}: {field} ref '{ref}' targets a draft page")


def run(repo_root: Path) -> tuple[int, list[str]]:
    content_root = repo_root / "content"
    if not content_root.exists():
        return 0, []
    errs = lint_cross_refs(content_root)
    return (1 if errs else 0), errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_works_links: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the test suite**

```bash
python3 -m unittest tools/test_check_works_links.py -v
```

Expected: 10 tests, all OK.

- [ ] **Step 3: Run the linter against the (still empty) content tree**

```bash
python3 tools/check_works_links.py
```

Expected: `check_works_links: OK` (no works fixtures yet).

- [ ] **Step 4: Commit**

```bash
git add tools/check_works_links.py
git commit -m "$(cat <<'EOF'
tools: add check_works_links linter

Resolves every cross-reference field on content/works/* fixtures and
enforces round-trip symmetry between music.lyrics_poem and the
corresponding poetry.set_to_music. Targets drafts treated as missing.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Game fixtures (4 + 7 SVGs)

**Files:**
- Create: `content/works/games/example-playable-full-release/index.md`
- Create: `content/works/games/example-playable-full-release/hero.svg`
- Create: `content/works/games/example-playable-full-release/screen-1.svg`
- Create: `content/works/games/example-playable-full-release/screen-2.svg`
- Create: `content/works/games/example-playable-full-release/screen-3.svg`
- Create: `content/works/games/example-playable-jam/index.md`
- Create: `content/works/games/example-playable-jam/hero.svg`
- Create: `content/works/games/example-in-progress-research-prototype/index.md`
- Create: `content/works/games/example-in-progress-research-prototype/hero.svg`
- Create: `content/works/games/example-archived-experiment/index.md`
- Create: `content/works/games/example-archived-experiment/hero.svg`

- [ ] **Step 1: Write `example-playable-full-release/index.md`**

```markdown
---
title: "Example Playable Full Release"
date: 2026-03-01
lastmod: 2026-03-02
draft: false
status: playable
type: full-release
tagline: "Example tagline — lorem ipsum dolor sit amet."
year: 2026
tags: [example, demo]
summary: "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
hero: hero.svg
embed_url: "https://example.itch.io/embed"
source_url: "https://github.com/example/repo"
itch_url: "https://example.itch.io"
collaborators: [Alice Example, Bob Example]
tech_stack: [Godot, GDScript]
length: "2 hours"
screenshots: [screen-1.svg, screen-2.svg, screen-3.svg]
research_questions: [/research/questions/example-active-q-1/]
related_essays: [/essays/example-essay-one/]
related_notes: [/garden/story-atoms/]
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

## About

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

## Design intent

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
```

- [ ] **Step 2: Write the four hero SVGs and three screenshot SVGs**

Each SVG follows the pattern of `content/essays/example-essay-one/hero.svg` — 16:9 viewBox, geometric primitives in palette colors. Write them as:

`content/works/games/example-playable-full-release/hero.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder hero illustration">
  <rect width="800" height="450" fill="#fdfcf8"/>
  <rect x="200" y="120" width="400" height="210" fill="none" stroke="#6b1f2c" stroke-width="3"/>
  <circle cx="280" cy="225" r="40" fill="#6b1f2c"/>
  <circle cx="520" cy="225" r="40" fill="none" stroke="#1e4060" stroke-width="3"/>
  <line x1="100" y1="380" x2="700" y2="380" stroke="#1e4060" stroke-width="2" stroke-dasharray="6 8"/>
</svg>
```

`content/works/games/example-playable-full-release/screen-1.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 225" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder screenshot">
  <rect width="400" height="225" fill="#fdfcf8"/>
  <rect x="50" y="50" width="300" height="125" fill="none" stroke="#6b1f2c" stroke-width="2"/>
  <circle cx="200" cy="112" r="30" fill="#6b1f2c" opacity="0.5"/>
</svg>
```

`content/works/games/example-playable-full-release/screen-2.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 225" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder screenshot">
  <rect width="400" height="225" fill="#fdfcf8"/>
  <path d="M 50 175 Q 200 25 350 175" fill="none" stroke="#1e4060" stroke-width="3"/>
  <circle cx="200" cy="100" r="20" fill="none" stroke="#6b1f2c" stroke-width="2"/>
</svg>
```

`content/works/games/example-playable-full-release/screen-3.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 225" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder screenshot">
  <rect width="400" height="225" fill="#fdfcf8"/>
  <rect x="100" y="80" width="80" height="80" fill="#6b1f2c" opacity="0.6"/>
  <rect x="220" y="80" width="80" height="80" fill="none" stroke="#1e4060" stroke-width="3"/>
</svg>
```

`content/works/games/example-playable-jam/hero.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder hero illustration">
  <rect width="800" height="450" fill="#fdfcf8"/>
  <polygon points="400,80 600,370 200,370" fill="none" stroke="#6b1f2c" stroke-width="3"/>
  <circle cx="400" cy="280" r="40" fill="#1e4060" opacity="0.5"/>
</svg>
```

`content/works/games/example-in-progress-research-prototype/hero.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder hero illustration">
  <rect width="800" height="450" fill="#fdfcf8"/>
  <circle cx="200" cy="225" r="90" fill="none" stroke="#1e4060" stroke-width="3" stroke-dasharray="6 8"/>
  <circle cx="400" cy="225" r="60" fill="none" stroke="#6b1f2c" stroke-width="3"/>
  <circle cx="600" cy="225" r="30" fill="#6b1f2c" opacity="0.5"/>
</svg>
```

`content/works/games/example-archived-experiment/hero.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder hero illustration">
  <rect width="800" height="450" fill="#fdfcf8"/>
  <line x1="100" y1="100" x2="700" y2="350" stroke="#6b1f2c" stroke-width="3" opacity="0.6"/>
  <line x1="100" y1="350" x2="700" y2="100" stroke="#1e4060" stroke-width="3" opacity="0.6"/>
  <circle cx="400" cy="225" r="50" fill="#fdfcf8" stroke="#6b1f2c" stroke-width="3"/>
</svg>
```

- [ ] **Step 3: Write `example-playable-jam/index.md`**

```markdown
---
title: "Example Playable Jam"
date: 2026-02-10
lastmod: 2026-02-11
draft: false
status: playable
type: jam
tagline: "Lorem ipsum dolor sit amet."
year: 2026
hero: hero.svg
itch_url: "https://example.itch.io/jam-game"
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
```

- [ ] **Step 4: Write `example-in-progress-research-prototype/index.md`**

```markdown
---
title: "Example In-Progress Research Prototype"
date: 2026-04-05
lastmod: 2026-04-08
draft: false
status: in-progress
type: research-prototype
tagline: "Example Two — lorem ipsum."
year: 2026
hero: hero.svg
research_questions: [/research/questions/example-active-q-1/, /research/questions/example-sub-q-1/]
tags: [example, prototype]
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
```

- [ ] **Step 5: Write `example-archived-experiment/index.md`**

```markdown
---
title: "Example Archived Experiment"
date: 2024-06-15
lastmod: 2024-06-15
draft: false
status: archived
type: experiment
tagline: "Lorem ipsum — early experiment."
year: 2024
hero: hero.svg
itch_url: "https://example.itch.io/old-experiment"
source_url: "https://github.com/example/old-repo"
tags: [example, archive]
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
```

- [ ] **Step 6: Run the fixtures linter**

```bash
python3 tools/check_works_fixtures.py
```

Expected: `check_works_fixtures: OK`

- [ ] **Step 7: Run the links linter**

```bash
python3 tools/check_works_links.py
```

Expected: `check_works_links: OK`

- [ ] **Step 8: Commit**

```bash
git add content/works/games/
git commit -m "$(cat <<'EOF'
fixtures: 4 game fixtures + hero/screenshot SVGs

example-playable-full-release: the 'everything filled in' fixture
(embed_url, screenshots, research_questions + related_essays +
related_notes cross-refs). Others test minimal / in-progress /
archived paths. All 3 status × 4 type values covered.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Music fixtures (4 + 4 SVGs)

**Files:**
- Create: `content/works/music/example-album-with-tracks/index.md`
- Create: `content/works/music/example-album-with-tracks/cover.svg`
- Create: `content/works/music/example-track-with-lyrics/index.md`
- Create: `content/works/music/example-track-with-lyrics/cover.svg`
- Create: `content/works/music/example-experiment-minimal/index.md`
- Create: `content/works/music/example-experiment-minimal/cover.svg`
- Create: `content/works/music/example-live-session/index.md`
- Create: `content/works/music/example-live-session/cover.svg`

- [ ] **Step 1: Write `example-album-with-tracks/index.md`**

```markdown
---
title: "Example Album With Tracks"
date: 2026-02-20
lastmod: 2026-02-25
draft: false
format: album
year: 2026
tagline: "Lorem ipsum dolor sit amet."
cover: cover.svg
duration: "42:18"
tracks:
  - { title: "Lorem One", duration: "3:14" }
  - { title: "Lorem Two", duration: "4:20" }
  - { title: "Lorem Three", duration: "5:05" }
  - { title: "Lorem Four", duration: "3:45" }
  - { title: "Lorem Five", duration: "6:18" }
  - { title: "Lorem Six", duration: "4:32" }
platform_embed: { kind: bandcamp, url: "https://example.bandcamp.com/album/example" }
tags: [example, ambient]
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
```

- [ ] **Step 2: Write `example-track-with-lyrics/index.md`**

```markdown
---
title: "Example Track With Lyrics"
date: 2026-03-10
lastmod: 2026-03-12
draft: false
format: track
year: 2026
tagline: "Lorem ipsum — set to a poem."
cover: cover.svg
duration: "4:12"
audio_url: "/audio/example-track.mp3"
platform_embed: { kind: soundcloud, url: "https://soundcloud.com/example/track" }
lyrics_poem: example-poem-with-lyrics
tags: [example, lyric]
---

Lorem ipsum dolor sit amet.
```

- [ ] **Step 3: Write `example-experiment-minimal/index.md`**

```markdown
---
title: "Example Experiment Minimal"
date: 2025-09-01
lastmod: 2025-09-01
draft: false
format: experiment
year: 2025
cover: cover.svg
---

Lorem ipsum.
```

- [ ] **Step 4: Write `example-live-session/index.md`**

```markdown
---
title: "Example Live Session"
date: 2026-01-15
lastmod: 2026-01-15
draft: false
format: live
year: 2026
tagline: "Lorem ipsum — a live take."
cover: cover.svg
duration: "22:45"
tracks:
  - { title: "Live One", duration: "6:30" }
  - { title: "Live Two", duration: "7:55" }
  - { title: "Live Three", duration: "8:20" }
platform_embed: { kind: youtube, url: "https://youtube.com/watch?v=example" }
made_with: [Guitar, "DI box", Ableton]
collaborators: [Alice Example]
tags: [example, live]
---

Lorem ipsum dolor sit amet.
```

- [ ] **Step 5: Write the four cover SVGs**

Each is a square viewBox geometric placeholder. Write:

`content/works/music/example-album-with-tracks/cover.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder cover art">
  <rect width="400" height="400" fill="#fdfcf8"/>
  <circle cx="200" cy="200" r="120" fill="none" stroke="#6b1f2c" stroke-width="3"/>
  <circle cx="200" cy="200" r="60" fill="#1e4060" opacity="0.4"/>
</svg>
```

`content/works/music/example-track-with-lyrics/cover.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder cover art">
  <rect width="400" height="400" fill="#fdfcf8"/>
  <path d="M 80 200 Q 200 80 320 200 Q 200 320 80 200 Z" fill="none" stroke="#6b1f2c" stroke-width="3"/>
  <line x1="200" y1="80" x2="200" y2="320" stroke="#1e4060" stroke-width="2" stroke-dasharray="4 6"/>
</svg>
```

`content/works/music/example-experiment-minimal/cover.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder cover art">
  <rect width="400" height="400" fill="#fdfcf8"/>
  <rect x="100" y="100" width="200" height="200" fill="none" stroke="#6b1f2c" stroke-width="3" stroke-dasharray="8 6"/>
  <circle cx="200" cy="200" r="20" fill="#1e4060"/>
</svg>
```

`content/works/music/example-live-session/cover.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder cover art">
  <rect width="400" height="400" fill="#fdfcf8"/>
  <polygon points="200,100 280,300 120,300" fill="none" stroke="#1e4060" stroke-width="3"/>
  <circle cx="200" cy="200" r="40" fill="#6b1f2c" opacity="0.5"/>
</svg>
```

- [ ] **Step 6: Run both linters**

```bash
python3 tools/check_works_fixtures.py && python3 tools/check_works_links.py
```

Expected: both print OK. (`lyrics_poem` on `example-track-with-lyrics` is dangling until Task 10 lands the poem — see Step 7.)

- [ ] **Step 7: If the links linter fails because the lyrics_poem target doesn't exist yet, that is expected — proceed to Task 10 immediately and the round-trip will close.**

If you got an "lyrics_poem='example-poem-with-lyrics' does not resolve" error, that's the expected intermediate state. Do not commit yet — let Task 10 add the poem first.

If the error did not surface (e.g. because the round-trip check requires both sides), commit now:

```bash
git add content/works/music/
git commit -m "$(cat <<'EOF'
fixtures: 4 music fixtures + cover SVGs

example-album-with-tracks: tracks + bandcamp embed. example-track-with-
lyrics: round-trip pair with example-poem-with-lyrics (Task 10 closes
the pair). example-experiment-minimal: minimal path. example-live-
session: tracks + youtube embed + made_with + collaborators. All 4
format values covered.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

If you did NOT commit (because the linter is failing), proceed to Task 10 first and commit the music + poetry fixtures together at the end of Task 10.

---

## Task 10: Poetry fixtures (4)

**Files:**
- Create: `content/works/poetry/example-poem-with-lyrics/index.md`
- Create: `content/works/poetry/example-poem-collected/index.md`
- Create: `content/works/poetry/example-poem-tagged/index.md`
- Create: `content/works/poetry/example-poem-minimal/index.md`

- [ ] **Step 1: Write `example-poem-with-lyrics/index.md`**

```markdown
---
title: "Example Poem With Lyrics"
date: 2026-03-08
lastmod: 2026-03-08
draft: false
lines: 12
collection: greenhouse-demos
set_to_music: example-track-with-lyrics
tags: [example, lyric]
---

Lorem ipsum dolor sit amet,
consectetur adipiscing elit.

Sed do eiusmod tempor incididunt
ut labore et dolore magna aliqua.

Ut enim ad minim veniam,
quis nostrud exercitation ullamco.

Duis aute irure dolor
in reprehenderit in voluptate.

Excepteur sint occaecat cupidatat
non proident sunt in culpa.

Qui officia deserunt mollit
anim id est laborum.
```

- [ ] **Step 2: Write `example-poem-collected/index.md`**

```markdown
---
title: "Example Poem Collected"
date: 2026-02-14
lastmod: 2026-02-14
draft: false
lines: 8
collection: greenhouse-demos
tags: [example, collected]
---

Lorem ipsum dolor sit amet,
consectetur adipiscing elit.

Sed do eiusmod tempor
incididunt ut labore et dolore.

Ut enim ad minim
veniam quis nostrud.

Duis aute irure dolor
in reprehenderit voluptate.
```

- [ ] **Step 3: Write `example-poem-tagged/index.md`**

```markdown
---
title: "Example Poem Tagged"
date: 2026-04-01
lastmod: 2026-04-01
draft: false
lines: 6
tags: [example, standalone]
---

Lorem ipsum dolor sit amet,
consectetur adipiscing elit.

Sed do eiusmod tempor incididunt,
ut labore et dolore magna aliqua.

Ut enim ad minim veniam,
quis nostrud exercitation ullamco.
```

- [ ] **Step 4: Write `example-poem-minimal/index.md`**

```markdown
---
title: "Example Poem Minimal"
date: 2025-12-01
lastmod: 2025-12-01
draft: false
lines: 4
---

Lorem ipsum dolor sit amet,
consectetur adipiscing elit.

Sed do eiusmod tempor
incididunt ut labore.
```

- [ ] **Step 5: Run both linters**

```bash
python3 tools/check_works_fixtures.py && python3 tools/check_works_links.py
```

Expected: both print OK. Round-trip between music and poetry now resolves.

- [ ] **Step 6: Commit poetry (and music if it was held)**

```bash
git add content/works/poetry/ content/works/music/
git commit -m "$(cat <<'EOF'
fixtures: 4 poetry fixtures + music round-trip

example-poem-with-lyrics: round-trip pair with example-track-with-
lyrics. example-poem-collected: shares collection so the dim has ≥2
values. example-poem-tagged: standalone with tags. example-poem-
minimal: required-fields-only.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Works umbrella layout + section-card partial

**Files:**
- Create: `layouts/works/list.html`
- Create: `layouts/partials/works/section-card.html`

- [ ] **Step 1: Write the section-card partial**

`layouts/partials/works/section-card.html`:

```html
{{- /* Renders one of three umbrella cards (games / music / poetry). */ -}}
{{- $sub := .sub -}}
{{- $section := site.GetPage (printf "/works/%s" $sub) -}}
{{- if $section -}}
  {{- $items := $section.Pages.ByDate.Reverse -}}
  <article class="works-section-card">
    <header class="works-section-card-header">
      <h2><a href="{{ $section.RelPermalink }}">{{ $section.Title }}</a></h2>
      <span class="works-section-card-count">{{ len $items }} item{{ if ne (len $items) 1 }}s{{ end }}</span>
    </header>
    {{- if gt (len $items) 0 }}
    <ul class="works-section-card-list">
      {{- range first 3 $items }}
      <li><a href="{{ .RelPermalink }}">{{ .Title }}</a></li>
      {{- end }}
    </ul>
    {{- end }}
    <a class="works-section-card-all" href="{{ $section.RelPermalink }}">All {{ lower $section.Title }} →</a>
  </article>
{{- end -}}
```

- [ ] **Step 2: Write the umbrella layout**

`layouts/works/list.html`:

```html
{{ define "main" }}
<article class="page works-umbrella">
  <header class="page-header">
    <h1>{{ .Title }}</h1>
    {{ with .Description }}<p class="page-description">{{ . }}</p>{{ end }}
  </header>

  {{ .Content }}

  <section class="works-umbrella-grid">
    {{ partial "works/section-card.html" (dict "sub" "games") }}
    {{ partial "works/section-card.html" (dict "sub" "music") }}
    {{ partial "works/section-card.html" (dict "sub" "poetry") }}
  </section>
</article>
{{ end }}
```

- [ ] **Step 3: Verify the build succeeds**

```bash
hugo --quiet
```

Expected: no errors. (Pages render unstyled — that lands with CSS in Task 19.)

- [ ] **Step 4: Spot-check the umbrella renders the three cards**

```bash
grep -c "works-section-card" public/works/index.html
```

Expected: at least 3 matches.

- [ ] **Step 5: Commit**

```bash
git add layouts/works/list.html layouts/partials/works/section-card.html
git commit -m "$(cat <<'EOF'
layouts: works umbrella + section-card partial

Three-card overview at /works/ — each card shows its sub-section's
title, count, first 3 recent entries, and an 'All X →' link.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Games index + game-card + status-pill partials

**Files:**
- Create: `layouts/works-games/list.html`
- Create: `layouts/partials/works/game-card.html`
- Create: `layouts/partials/works/status-pill.html`

- [ ] **Step 1: Write the status-pill partial**

`layouts/partials/works/status-pill.html`:

```html
{{- /* Renders a works status pill. Expects .status (one of: playable, in-progress, archived). */ -}}
{{- $status := .status | default "playable" -}}
<span class="works-status-pill" data-status="{{ $status }}">{{ humanize $status }}</span>
```

- [ ] **Step 2: Write the game-card partial**

`layouts/partials/works/game-card.html`:

```html
{{- /* Renders one card for the /works/games/ index. */ -}}
{{- $hero := "" -}}
{{- with .Params.hero -}}
  {{- $heroRes := $.Resources.Get . -}}
  {{- if $heroRes -}}{{- $hero = $heroRes.RelPermalink -}}{{- end -}}
{{- end -}}
<article class="works-game-card"
         data-status="{{ .Params.status }}"
         data-type="{{ .Params.type }}"
         data-tags="{{ delimit (.Params.tags | default slice) "," }}">
  <a class="works-game-card-link" href="{{ .RelPermalink }}">
    <div class="works-game-card-preview">
      {{- if $hero }}<img src="{{ $hero }}" alt="" loading="lazy">{{- end }}
      {{- if .Params.embed_url }}<span class="works-game-card-embed-pill">▶ Play in browser</span>{{- end }}
      <span class="works-game-card-status-badge">
        <span class="works-game-card-year">{{ .Params.year }}</span>
        <span class="works-game-card-type">{{ humanize .Params.type }}</span>
      </span>
    </div>
    <div class="works-game-card-body">
      <h3 class="works-game-card-title">{{ .Title }}</h3>
      {{- with .Params.tagline }}<p class="works-game-card-tagline">{{ . }}</p>{{- end }}
      <p class="works-game-card-meta">
        {{ partial "works/status-pill.html" (dict "status" .Params.status) }}
        {{- with .Params.tech_stack }}<span class="works-game-card-tech">{{ delimit . " · " }}</span>{{- end }}
      </p>
      {{- with .Params.tags }}<p class="works-game-card-tags">{{ range . }}<span class="works-game-card-tag">{{ . }}</span>{{ end }}</p>{{- end }}
    </div>
  </a>
</article>
```

- [ ] **Step 3: Write the games index layout**

The filter-chips partial expects each dim's `values` to be a pre-collected slice of distinct values across all pages — not the params of a single page. Build the sets explicitly (same idiom as `layouts/garden/list.html`).

`layouts/works-games/list.html`:

```html
{{ define "main" }}
<article class="page works-games-index">
  <header class="page-header">
    <h1>{{ .Title }}</h1>
    {{ with .Description }}<p class="page-description">{{ . }}</p>{{ end }}
  </header>

  {{ .Content }}

  {{ $items := .Pages.ByDate.Reverse }}

  {{- /* ----- Build dimension value sets ----- */ -}}
  {{- $statuses := slice -}}
  {{- $types := slice -}}
  {{- $tagCounts := dict -}}
  {{- range $items -}}
    {{- $s := .Params.status -}}
    {{- if and $s (not (in $statuses $s)) -}}{{- $statuses = $statuses | append $s -}}{{- end -}}
    {{- $t := .Params.type -}}
    {{- if and $t (not (in $types $t)) -}}{{- $types = $types | append $t -}}{{- end -}}
    {{- range .Params.tags -}}
      {{- $cur := index $tagCounts . | default 0 -}}
      {{- $tagCounts = merge $tagCounts (dict . (add $cur 1)) -}}
    {{- end -}}
  {{- end -}}

  {{- /* Rank tags by count desc, alphabetical for ties */ -}}
  {{- $tagPairs := slice -}}
  {{- range $name, $count := $tagCounts -}}
    {{- $tagPairs = $tagPairs | append (dict "name" $name "count" $count) -}}
  {{- end -}}
  {{- $tags := slice -}}
  {{- range (sort (sort $tagPairs "name" "asc") "count" "desc") -}}
    {{- $tags = $tags | append .name -}}
  {{- end -}}

  {{- $dims := slice -}}
  {{- if ge (len $statuses) 2 -}}
    {{- $dims = $dims | append (dict "key" "status" "label" "Status" "values" $statuses) -}}
  {{- end -}}
  {{- if ge (len $types) 2 -}}
    {{- $dims = $dims | append (dict "key" "type" "label" "Type" "values" $types) -}}
  {{- end -}}
  {{- if ge (len $tags) 2 -}}
    {{- $dims = $dims | append (dict "key" "tag" "label" "Tag" "values" $tags) -}}
  {{- end -}}

  {{ partial "filter-chips.html" (dict "dimensions" $dims "section" "games") }}

  <section class="works-games-grid">
    {{- range $items }}
      {{- partial "works/game-card.html" . }}
    {{- end }}
  </section>
</article>
{{ end }}
```

- [ ] **Step 4: Verify the build succeeds**

```bash
hugo --quiet
```

Expected: no errors.

- [ ] **Step 5: Spot-check the cards render**

```bash
grep -c "works-game-card" public/works/games/index.html
```

Expected: at least 4 matches (one per game fixture).

- [ ] **Step 6: Commit**

```bash
git add layouts/works-games/list.html layouts/partials/works/
git commit -m "$(cat <<'EOF'
layouts: games index + game-card + status-pill partials

2-col card grid with shared filter-chips strip (status, type, tag).
Cards carry data-status/data-type/data-tags for the chip JS to filter
client-side.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Game single layout + connections partial

**Files:**
- Create: `layouts/works-games/single.html`
- Create: `layouts/partials/works/connections.html`

- [ ] **Step 1: Write the connections partial**

`layouts/partials/works/connections.html`:

```html
{{- /* Two-column connections block: research/essays/notes/works refs.
       Expects a `.page` (passed via dict) or `.` for current page. */ -}}
{{- $p := .page | default . -}}
{{- $research := $p.Params.research_questions | default slice -}}
{{- $essays := $p.Params.related_essays | default slice -}}
{{- $notes := $p.Params.related_notes | default slice -}}
{{- $works := $p.Params.related_works | default slice -}}
{{- if or (gt (len $research) 0) (gt (len $essays) 0) (gt (len $notes) 0) (gt (len $works) 0) -}}
<section class="works-connections">
  <h2>Connections</h2>
  <div class="works-connections-grid">
    {{- if gt (len $research) 0 }}
    <div class="works-connections-col">
      <h3>Research questions</h3>
      <ul>
        {{- range $research }}
          {{- $page := site.GetPage . }}
          <li>{{ if $page }}<a href="{{ $page.RelPermalink }}">{{ $page.Title }}</a>{{ else }}<span>{{ . }}</span>{{ end }}</li>
        {{- end }}
      </ul>
    </div>
    {{- end }}
    {{- if or (gt (len $essays) 0) (gt (len $notes) 0) }}
    <div class="works-connections-col">
      <h3>Essays & notes</h3>
      <ul>
        {{- range $essays }}
          {{- $page := site.GetPage . }}
          <li>{{ if $page }}<a href="{{ $page.RelPermalink }}">{{ $page.Title }}</a>{{ else }}<span>{{ . }}</span>{{ end }}</li>
        {{- end }}
        {{- range $notes }}
          {{- $page := site.GetPage . }}
          <li>{{ if $page }}<a href="{{ $page.RelPermalink }}">{{ $page.Title }}</a>{{ else }}<span>{{ . }}</span>{{ end }}</li>
        {{- end }}
      </ul>
    </div>
    {{- end }}
    {{- if gt (len $works) 0 }}
    <div class="works-connections-col">
      <h3>Related works</h3>
      <ul>
        {{- range $works }}
          {{- $page := site.GetPage . }}
          <li>{{ if $page }}<a href="{{ $page.RelPermalink }}">{{ $page.Title }}</a>{{ else }}<span>{{ . }}</span>{{ end }}</li>
        {{- end }}
      </ul>
    </div>
    {{- end }}
  </div>
</section>
{{- end -}}
```

- [ ] **Step 2: Write the game single layout**

`layouts/works-games/single.html`:

```html
{{ define "main" }}
<article class="page works-game-page">
  {{- $hero := "" -}}
  {{- with .Params.hero -}}
    {{- $heroRes := $.Resources.Get . -}}
    {{- if $heroRes -}}{{- $hero = $heroRes.RelPermalink -}}{{- end -}}
  {{- end -}}

  <header class="works-game-hero">
    {{ if $hero }}<div class="works-game-hero-art"><img src="{{ $hero }}" alt=""></div>{{ end }}
    <div class="works-game-hero-meta">
      <h1>{{ .Title }}</h1>
      {{- with .Params.tagline }}<p class="works-game-tagline">{{ . }}</p>{{- end }}
      <p class="works-game-meta-row">
        {{ partial "works/status-pill.html" (dict "status" .Params.status) }}
        <span class="works-game-year">{{ .Params.year }}</span>
        <span class="works-game-type">{{ humanize .Params.type }}</span>
        {{- with .Params.length }}<span class="works-game-length">{{ . }}</span>{{- end }}
      </p>
      {{- with .Params.collaborators }}<p class="works-game-collaborators">with {{ delimit . ", " }}</p>{{- end }}
      {{- with .Params.tech_stack }}<p class="works-game-tech">{{ delimit . " · " }}</p>{{- end }}
    </div>
  </header>

  <section class="works-game-embed">
    {{- if .Params.embed_url }}
    <a class="works-embed-stub" data-pending href="{{ .Params.embed_url }}">→ Play in browser</a>
    {{- end }}
    {{- if .Params.itch_url }}
    <a class="works-game-external" href="{{ .Params.itch_url }}">Open on itch.io</a>
    {{- end }}
    {{- if .Params.source_url }}
    <a class="works-game-external" href="{{ .Params.source_url }}">Source on GitHub</a>
    {{- end }}
  </section>

  <section class="works-game-about">
    {{ .Content }}
  </section>

  {{- with .Params.screenshots }}
  <section class="works-game-screens">
    <h2>Screens</h2>
    <div class="works-game-screens-grid">
      {{- range . }}
        {{- $res := $.Resources.Get . }}
        {{- if $res }}<img src="{{ $res.RelPermalink }}" alt="" loading="lazy">{{- end }}
      {{- end }}
    </div>
  </section>
  {{- end }}

  {{ partial "works/connections.html" (dict "page" .) }}

  {{- if or .Params.itch_url .Params.source_url .Params.tech_stack }}
  <section class="works-game-credits">
    <h2>Credits & links</h2>
    {{- with .Params.tech_stack }}<p><strong>Made with:</strong> {{ delimit . ", " }}</p>{{- end }}
    {{- with .Params.itch_url }}<p><a href="{{ . }}">itch.io</a></p>{{- end }}
    {{- with .Params.source_url }}<p><a href="{{ . }}">GitHub</a></p>{{- end }}
  </section>
  {{- end }}
</article>
{{ end }}
```

- [ ] **Step 3: Verify the build succeeds**

```bash
hugo --quiet
```

Expected: no errors. All four game pages render.

- [ ] **Step 4: Spot-check the everything-fixture page**

```bash
grep -c "works-embed-stub\|works-game-screens" public/works/games/example-playable-full-release/index.html
```

Expected: at least 2 matches.

- [ ] **Step 5: Commit**

```bash
git add layouts/works-games/single.html layouts/partials/works/connections.html
git commit -m "$(cat <<'EOF'
layouts: game single + connections partial

Hero (title + tagline + status pill + year + collaborators + tech) →
embed-or-play stub block → about body → 3-up screens grid (only if
screenshots set) → connections (research / essays / notes / works) →
credits & links. Stub anchors carry data-pending for future runtime
swap-in.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Music index + music-row partial

**Files:**
- Create: `layouts/works-music/list.html`
- Create: `layouts/partials/works/music-row.html`

- [ ] **Step 1: Write the music-row partial**

`layouts/partials/works/music-row.html`:

```html
{{- /* One row in the /works/music/ list. */ -}}
{{- $cover := "" -}}
{{- with .Params.cover -}}
  {{- $coverRes := $.Resources.Get . -}}
  {{- if $coverRes -}}{{- $cover = $coverRes.RelPermalink -}}{{- end -}}
{{- end -}}
<article class="works-music-row"
         data-format="{{ .Params.format }}"
         data-tags="{{ delimit (.Params.tags | default slice) "," }}">
  <a class="works-music-row-link" href="{{ .RelPermalink }}">
    <div class="works-music-row-cover">
      {{- if $cover }}<img src="{{ $cover }}" alt="" loading="lazy">{{- end }}
    </div>
    <div class="works-music-row-body">
      <h3 class="works-music-row-title">{{ .Title }}</h3>
      <p class="works-music-row-meta">
        <span class="works-music-row-format">{{ humanize .Params.format }}</span>
        {{- with .Params.duration }} · <span class="works-music-row-duration">{{ . }}</span>{{- end }}
        · <span class="works-music-row-year">{{ .Params.year }}</span>
      </p>
      {{- with .Params.tagline }}<p class="works-music-row-tagline">{{ . }}</p>{{- end }}
    </div>
  </a>
</article>
```

- [ ] **Step 2: Write the music index layout**

Same value-collection idiom as the games index — collect distinct format + tags values across all music pages, suppress dims with <2 values.

`layouts/works-music/list.html`:

```html
{{ define "main" }}
<article class="page works-music-index">
  <header class="page-header">
    <h1>{{ .Title }}</h1>
    {{ with .Description }}<p class="page-description">{{ . }}</p>{{ end }}
  </header>

  {{ .Content }}

  {{ $items := .Pages.ByDate.Reverse }}

  {{- $formats := slice -}}
  {{- $tagCounts := dict -}}
  {{- range $items -}}
    {{- $f := .Params.format -}}
    {{- if and $f (not (in $formats $f)) -}}{{- $formats = $formats | append $f -}}{{- end -}}
    {{- range .Params.tags -}}
      {{- $cur := index $tagCounts . | default 0 -}}
      {{- $tagCounts = merge $tagCounts (dict . (add $cur 1)) -}}
    {{- end -}}
  {{- end -}}

  {{- $tagPairs := slice -}}
  {{- range $name, $count := $tagCounts -}}
    {{- $tagPairs = $tagPairs | append (dict "name" $name "count" $count) -}}
  {{- end -}}
  {{- $tags := slice -}}
  {{- range (sort (sort $tagPairs "name" "asc") "count" "desc") -}}
    {{- $tags = $tags | append .name -}}
  {{- end -}}

  {{- $dims := slice -}}
  {{- if ge (len $formats) 2 -}}
    {{- $dims = $dims | append (dict "key" "format" "label" "Format" "values" $formats) -}}
  {{- end -}}
  {{- if ge (len $tags) 2 -}}
    {{- $dims = $dims | append (dict "key" "tag" "label" "Tag" "values" $tags) -}}
  {{- end -}}

  {{ partial "filter-chips.html" (dict "dimensions" $dims "section" "music") }}

  <section class="works-music-list">
    {{- range $items }}
      {{- partial "works/music-row.html" . }}
    {{- end }}
  </section>
</article>
{{ end }}
```

- [ ] **Step 3: Verify the build**

```bash
hugo --quiet
```

Expected: no errors.

- [ ] **Step 4: Spot-check**

```bash
grep -c "works-music-row" public/works/music/index.html
```

Expected: at least 4 matches.

- [ ] **Step 5: Commit**

```bash
git add layouts/works-music/list.html layouts/partials/works/music-row.html
git commit -m "$(cat <<'EOF'
layouts: music index + music-row partial

List rows (cover thumb + title + format/length/year + tagline) with
shared filter-chips strip (format, tag).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 15: Music single + audio-link partial + lyrics shortcode

**Files:**
- Create: `layouts/works-music/single.html`
- Create: `layouts/partials/works/audio-link.html`
- Create: `layouts/shortcodes/lyrics.html`

- [ ] **Step 1: Write the audio-link partial**

`layouts/partials/works/audio-link.html`:

```html
{{- /* Renders a "Listen on <kind>" link from a music page's platform_embed dict. */ -}}
{{- $pe := .platform_embed -}}
{{- if $pe -}}
  {{- $kind := index $pe "kind" -}}
  {{- $url := index $pe "url" -}}
  {{- if and $kind $url -}}
    <a class="works-audio-link" href="{{ $url }}">Listen on {{ humanize $kind }}</a>
  {{- end -}}
{{- end -}}
```

- [ ] **Step 2: Write the lyrics shortcode (no-op stub)**

`layouts/shortcodes/lyrics.html`:

```html
{{- /* Synced-lyrics shortcode stub. Future runtime parses [mm:ss] timestamps
       and binds to an <audio> element via timeupdate. For now, emits a styled
       block with raw line text and the data-pending marker so fixtures exercise
       the shape end-to-end. */ -}}
<div class="synced-lyrics-stub" data-pending>{{ .Inner | safeHTML }}</div>
```

- [ ] **Step 3: Write the music single layout**

`layouts/works-music/single.html`:

```html
{{ define "main" }}
<article class="page works-music-page">
  {{- $cover := "" -}}
  {{- with .Params.cover -}}
    {{- $coverRes := $.Resources.Get . -}}
    {{- if $coverRes -}}{{- $cover = $coverRes.RelPermalink -}}{{- end -}}
  {{- end -}}

  <header class="works-music-hero">
    {{ if $cover }}<div class="works-music-hero-art"><img src="{{ $cover }}" alt=""></div>{{ end }}
    <div class="works-music-hero-meta">
      <h1>{{ .Title }}</h1>
      {{- with .Params.tagline }}<p class="works-music-tagline">{{ . }}</p>{{- end }}
      <p class="works-music-meta-row">
        <span class="works-music-format">{{ humanize .Params.format }}</span>
        {{- with .Params.duration }} · <span class="works-music-duration">{{ . }}</span>{{- end }}
        · <span class="works-music-year">{{ .Params.year }}</span>
        {{- with .Params.collaborators }} · <span class="works-music-collaborators">with {{ delimit . ", " }}</span>{{- end }}
      </p>
    </div>
  </header>

  <section class="works-music-player">
    {{- if .Params.platform_embed }}
      {{ partial "works/audio-link.html" (dict "platform_embed" .Params.platform_embed) }}
    {{- else if .Params.audio_url }}
      <div class="works-player-stub" data-pending>→ Listen (player coming soon)</div>
    {{- end }}
  </section>

  <section class="works-music-about">
    {{ .Content }}
  </section>

  {{- with .Params.tracks }}
  <section class="works-music-tracks">
    <h2>Tracks</h2>
    <ol class="works-music-tracks-list">
      {{- range . }}
      <li><span class="works-music-track-title">{{ index . "title" }}</span>{{ with index . "duration" }}<span class="works-music-track-duration">{{ . }}</span>{{ end }}</li>
      {{- end }}
    </ol>
  </section>
  {{- end }}

  {{- with .Params.lyrics_poem }}
    {{- $poem := site.GetPage (printf "/works/poetry/%s" .) }}
    {{- if $poem }}
    <section class="works-music-lyrics">
      <h2>Lyrics</h2>
      <div class="synced-lyrics-stub" data-pending>Lyrics: <a href="{{ $poem.RelPermalink }}">{{ $poem.Title }}</a></div>
    </section>
    {{- end }}
  {{- end }}

  {{- with .Params.made_with }}
  <section class="works-music-made-with">
    <h2>Made with</h2>
    <p>{{ delimit . ", " }}</p>
  </section>
  {{- end }}

  {{ partial "works/connections.html" (dict "page" .) }}
</article>
{{ end }}
```

- [ ] **Step 4: Verify the build**

```bash
hugo --quiet
```

Expected: no errors. All four music pages render.

- [ ] **Step 5: Spot-check the lyrics stub appears on the lyrics fixture**

```bash
grep -c "synced-lyrics-stub" public/works/music/example-track-with-lyrics/index.html
```

Expected: at least 1 match.

- [ ] **Step 6: Commit**

```bash
git add layouts/works-music/single.html layouts/partials/works/audio-link.html layouts/shortcodes/lyrics.html
git commit -m "$(cat <<'EOF'
layouts: music single + audio-link + lyrics shortcode stub

Hero (cover + meta) → player frame (stub: text link from platform_embed
OR 'player coming soon' from audio_url) → about → tracks (numbered plain
list) → lyrics block (stub linking to poem) → made_with → connections.
lyrics.html shortcode stub mirrors math/video-sync/widget pattern.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 16: Poetry index + poem-row partial

**Files:**
- Create: `layouts/works-poetry/list.html`
- Create: `layouts/partials/works/poem-row.html`

- [ ] **Step 1: Write the poem-row partial**

`layouts/partials/works/poem-row.html`:

```html
{{- /* One row in the /works/poetry/ list. */ -}}
<article class="works-poem-row"
         data-collection="{{ .Params.collection | default "" }}"
         data-tags="{{ delimit (.Params.tags | default slice) "," }}">
  <a class="works-poem-row-link" href="{{ .RelPermalink }}">
    <h3 class="works-poem-row-title">{{ .Title }}</h3>
    <p class="works-poem-row-meta">
      <time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date.Format "Jan 2006" }}</time>
      {{- with .Params.collection }} · <span class="works-poem-row-collection">{{ . }}</span>{{- end }}
      {{- if .Params.set_to_music }} · <span class="works-poem-row-music">set to music</span>{{- end }}
    </p>
  </a>
</article>
```

- [ ] **Step 2: Write the poetry index layout**

Same value-collection idiom — collect distinct collections + tags across all poem pages.

`layouts/works-poetry/list.html`:

```html
{{ define "main" }}
<article class="page works-poetry-index">
  <header class="page-header">
    <h1>{{ .Title }}</h1>
    {{ with .Description }}<p class="page-description">{{ . }}</p>{{ end }}
  </header>

  {{ .Content }}

  {{ $items := .Pages.ByDate.Reverse }}

  {{- $collections := slice -}}
  {{- $tagCounts := dict -}}
  {{- range $items -}}
    {{- $c := .Params.collection -}}
    {{- if and $c (not (in $collections $c)) -}}{{- $collections = $collections | append $c -}}{{- end -}}
    {{- range .Params.tags -}}
      {{- $cur := index $tagCounts . | default 0 -}}
      {{- $tagCounts = merge $tagCounts (dict . (add $cur 1)) -}}
    {{- end -}}
  {{- end -}}

  {{- $tagPairs := slice -}}
  {{- range $name, $count := $tagCounts -}}
    {{- $tagPairs = $tagPairs | append (dict "name" $name "count" $count) -}}
  {{- end -}}
  {{- $tags := slice -}}
  {{- range (sort (sort $tagPairs "name" "asc") "count" "desc") -}}
    {{- $tags = $tags | append .name -}}
  {{- end -}}

  {{- $dims := slice -}}
  {{- if ge (len $collections) 2 -}}
    {{- $dims = $dims | append (dict "key" "collection" "label" "Collection" "values" $collections) -}}
  {{- end -}}
  {{- if ge (len $tags) 2 -}}
    {{- $dims = $dims | append (dict "key" "tag" "label" "Tag" "values" $tags) -}}
  {{- end -}}

  {{ partial "filter-chips.html" (dict "dimensions" $dims "section" "poetry") }}

  <section class="works-poetry-list">
    {{- range $items }}
      {{- partial "works/poem-row.html" . }}
    {{- end }}
  </section>
</article>
{{ end }}
```

- [ ] **Step 3: Verify the build**

```bash
hugo --quiet
```

Expected: no errors.

- [ ] **Step 4: Spot-check**

```bash
grep -c "works-poem-row" public/works/poetry/index.html
```

Expected: at least 4 matches.

- [ ] **Step 5: Commit**

```bash
git add layouts/works-poetry/list.html layouts/partials/works/poem-row.html
git commit -m "$(cat <<'EOF'
layouts: poetry index + poem-row partial

Narrow column rows: title + date + collection badge + 'set to music'
badge. Shared filter chips (collection, tag).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 17: Poetry single + audio-pill partial

**Files:**
- Create: `layouts/works-poetry/single.html`
- Create: `layouts/partials/works/audio-pill.html`

- [ ] **Step 1: Write the audio-pill partial**

`layouts/partials/works/audio-pill.html`:

```html
{{- /* Pill linking from a poem to its music piece when set_to_music is present. */ -}}
{{- $music := site.GetPage (printf "/works/music/%s" .) -}}
{{- if $music -}}
<a class="works-audio-pill" href="{{ $music.RelPermalink }}">
  <span class="works-audio-pill-dot"></span>
  Set to music — listen on “{{ $music.Title }}”
</a>
{{- end -}}
```

- [ ] **Step 2: Write the poem single layout**

`layouts/works-poetry/single.html`:

```html
{{ define "main" }}
<article class="page works-poem-page">
  <header class="works-poem-header">
    <h1>{{ .Title }}</h1>
    <p class="works-poem-meta">
      <time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date.Format "Jan 2006" }}</time>
      {{- with .Params.collection }} · <span class="works-poem-collection">{{ . }}</span>{{- end }}
    </p>
    {{- with .Params.set_to_music }}
      {{ partial "works/audio-pill.html" . }}
    {{- end }}
  </header>

  <section class="works-poem-body">
    {{ .Content }}
  </section>
</article>
{{ end }}
```

- [ ] **Step 3: Verify the build**

```bash
hugo --quiet
```

Expected: no errors. All four poem pages render.

- [ ] **Step 4: Spot-check the audio pill on the lyrics fixture**

```bash
grep -c "works-audio-pill" public/works/poetry/example-poem-with-lyrics/index.html
```

Expected: at least 1 match.

- [ ] **Step 5: Commit**

```bash
git add layouts/works-poetry/single.html layouts/partials/works/audio-pill.html
git commit -m "$(cat <<'EOF'
layouts: poem single + audio-pill partial

Narrow-column title + date + collection meta + (if set_to_music)
audio pill linking to the music page. Body renders the poem text via
.Content. No pulse animation yet — that's a polish-pass deferral.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 18: Works JS bundle (filter-chips wiring)

**Why:** The shared `filter-chips.html` partial renders the chip strip, but without JS the chips are inert — clicks won't filter. Wire `setupFilterChips()` to each of the three Works index pages via a tiny module + multi-entry bundle, page-scoped to `.Section == "works"` (same pattern as `entry-garden.js`).

**Files:**
- Create: `assets/js/works.js`
- Create: `assets/js/entry-works.js`
- Modify: `layouts/partials/scripts.html`

- [ ] **Step 1: Write `assets/js/works.js`**

```javascript
// Works page-level enhancements.
// - Multi-dimension AND filter chips on the three works index pages.
import { setupFilterChips } from './filter-chips.js';

function init() {
  // Games index
  if (document.querySelector('.works-games-index .filter-chips')) {
    setupFilterChips({
      containerSelector: '.works-games-index .filter-chips',
      cardSelector: '.works-game-card',
    });
  }
  // Music index
  if (document.querySelector('.works-music-index .filter-chips')) {
    setupFilterChips({
      containerSelector: '.works-music-index .filter-chips',
      cardSelector: '.works-music-row',
    });
  }
  // Poetry index
  if (document.querySelector('.works-poetry-index .filter-chips')) {
    setupFilterChips({
      containerSelector: '.works-poetry-index .filter-chips',
      cardSelector: '.works-poem-row',
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
```

- [ ] **Step 2: Write `assets/js/entry-works.js`**

```javascript
// Works-section entry — loaded only on /works/ (umbrella + 3 indexes + per-item pages).
// works.js owns its own selector guards, so per-item pages safely no-op.
import './works.js';
```

- [ ] **Step 3: Add a new `.Section == "works"` block to `scripts.html`**

Open `layouts/partials/scripts.html` and insert a new `if` block after the research block (between line 32 and the closing of the template):

```html
{{- if eq .Section "works" }}
{{- $worksOpts := dict "targetPath" "js/works.js" "minify" true -}}
{{- $works := resources.Get "js/entry-works.js" | js.Build $worksOpts | fingerprint }}
<script src="{{ $works.RelPermalink }}" integrity="{{ $works.Data.Integrity }}" defer></script>
{{- end }}
```

- [ ] **Step 4: Verify the build emits the works bundle**

```bash
hugo --quiet
ls public/js/ | grep ^works
```

Expected: `works.<hash>.js` is present.

- [ ] **Step 5: Spot-check the bundle is referenced from a works index page**

```bash
grep -c "js/works\." public/works/games/index.html
```

Expected: at least 1 match.

- [ ] **Step 6: Spot-check the bundle is NOT referenced from a non-works page**

```bash
grep -c "js/works\." public/essays/index.html
```

Expected: 0.

- [ ] **Step 7: Commit**

```bash
git add assets/js/works.js assets/js/entry-works.js layouts/partials/scripts.html
git commit -m "$(cat <<'EOF'
js: works section bundle (filter-chips wiring)

New entry-works.js → works.<hash>.js, loaded only on /works/. works.js
calls setupFilterChips() with appropriate container + card selectors
for each of the three index pages. Per-item pages no-op via the
selector guards. Adds the 5th multi-entry bundle in scripts.html.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 19: CSS §32 — Works shared chrome

**Files:**
- Modify: `assets/css/main.css`

- [ ] **Step 1: Append §32 to `assets/css/main.css`**

Find the end of §31 (research graph) and append:

```css

/* =========================================================
 * §32 Works — shared chrome
 * Status pill, audio pill, data-pending stub anchors,
 * connections block. Used by all three sub-section pages.
 * ========================================================= */

.works-status-pill {
  display: inline-block;
  padding: 0.15em 0.6em;
  border-radius: 999px;
  font-family: var(--font-ui);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  background: var(--color-ink-soft);
  color: var(--color-stone);
}
.works-status-pill[data-status="playable"]   { background: var(--color-burgundy); }
.works-status-pill[data-status="in-progress"] { background: var(--color-warn); color: var(--color-ink); }
.works-status-pill[data-status="archived"]   { background: var(--color-ink-soft); }

/* Stub anchors: italic + dotted underline + ink-soft.
   Same convention as .placeholder from §29. */
.works-embed-stub,
.works-player-stub,
.synced-lyrics-stub {
  display: inline-block;
  font-style: italic;
  color: var(--color-ink-soft);
  text-decoration: underline;
  text-decoration-style: dotted;
  text-underline-offset: 0.2em;
}
.works-player-stub,
.synced-lyrics-stub {
  display: block;
  padding: 0.6em 0.9em;
  border: 1px dashed var(--color-ink-soft);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.02);
}
.synced-lyrics-stub a {
  font-style: normal;
  color: var(--color-burgundy);
}

/* Audio pill on poem pages */
.works-audio-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5em;
  padding: 0.4em 0.9em;
  border-radius: 999px;
  background: var(--color-burgundy);
  color: var(--color-stone);
  text-decoration: none;
  font-family: var(--font-ui);
  font-size: 0.88rem;
}
.works-audio-pill-dot {
  width: 0.5em;
  height: 0.5em;
  border-radius: 50%;
  background: var(--color-stone);
}
.works-audio-pill:hover {
  filter: brightness(1.05);
}

/* Connections block (game + music pages) */
.works-connections {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-ink-soft);
}
.works-connections h2 {
  font-family: var(--font-body);
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
}
.works-connections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
}
.works-connections-col h3 {
  font-family: var(--font-ui);
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-ink-soft);
  margin: 0 0 0.5rem 0;
}
.works-connections-col ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.works-connections-col li {
  margin-bottom: 0.4em;
}
```

- [ ] **Step 2: Verify the build**

```bash
hugo --quiet
```

Expected: no errors.

- [ ] **Step 3: Run the contrast checker**

```bash
python3 tools/check-contrast.py
```

Expected: PASS (no new token pairings introduced).

- [ ] **Step 4: Commit**

```bash
git add assets/css/main.css
git commit -m "$(cat <<'EOF'
css §32: works shared chrome

Status pill (3 colors via existing tokens), audio pill, data-pending
stub styles (mirroring .placeholder from §29), and connections block.
Reused by all three works sub-sections.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 20: CSS §33 — Works umbrella + games

**Files:**
- Modify: `assets/css/main.css`

- [ ] **Step 1: Append §33**

After §32, append:

```css

/* =========================================================
 * §33 Works — umbrella + games
 * /works/ overview cards; /works/games/ grid; per-game page.
 * ========================================================= */

/* Umbrella */
.works-umbrella-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}
.works-section-card {
  padding: 1.5rem;
  border: 1px solid var(--color-ink-soft);
  border-radius: 6px;
  background: var(--color-stone);
}
.works-section-card-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.works-section-card-header h2 {
  margin: 0;
  font-family: var(--font-body);
}
.works-section-card-header h2 a {
  color: var(--color-ink);
  text-decoration: none;
}
.works-section-card-count {
  font-family: var(--font-ui);
  font-size: 0.85rem;
  color: var(--color-ink-soft);
}
.works-section-card-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1rem 0;
}
.works-section-card-list li {
  font-style: italic;
  margin-bottom: 0.3em;
}
.works-section-card-list a {
  color: var(--color-ink);
}
.works-section-card-all {
  font-family: var(--font-ui);
  font-size: 0.85rem;
  color: var(--color-burgundy);
}

/* Games index */
.works-games-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}
@media (max-width: 720px) {
  .works-games-grid { grid-template-columns: 1fr; }
}
.works-game-card {
  border: 1px solid var(--color-ink-soft);
  border-radius: 6px;
  overflow: hidden;
  background: var(--color-stone);
}
.works-game-card[hidden] { display: none; }
.works-game-card-link {
  display: block;
  color: inherit;
  text-decoration: none;
}
.works-game-card-preview {
  position: relative;
  aspect-ratio: 16 / 9;
  background: var(--color-ink-soft);
  overflow: hidden;
}
.works-game-card-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.works-game-card-embed-pill {
  position: absolute;
  top: 0.7em;
  right: 0.7em;
  padding: 0.25em 0.7em;
  border-radius: 999px;
  background: var(--color-burgundy);
  color: var(--color-stone);
  font-family: var(--font-ui);
  font-size: 0.78rem;
  font-weight: 600;
}
.works-game-card-status-badge {
  position: absolute;
  bottom: 0.7em;
  left: 0.7em;
  display: inline-flex;
  gap: 0.4em;
  padding: 0.2em 0.6em;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.55);
  color: var(--color-stone);
  font-family: var(--font-ui);
  font-size: 0.78rem;
}
.works-game-card-body {
  padding: 1rem 1.2rem 1.2rem 1.2rem;
}
.works-game-card-title {
  font-family: var(--font-body);
  margin: 0 0 0.25em 0;
}
.works-game-card-tagline {
  font-style: italic;
  color: var(--color-ink-soft);
  margin: 0 0 0.6em 0;
}
.works-game-card-meta {
  display: flex;
  align-items: center;
  gap: 0.6em;
  flex-wrap: wrap;
  font-family: var(--font-ui);
  font-size: 0.82rem;
  color: var(--color-ink-soft);
  margin: 0 0 0.6em 0;
}
.works-game-card-tag {
  display: inline-block;
  padding: 0.1em 0.5em;
  margin-right: 0.4em;
  background: rgba(107, 31, 44, 0.08);
  border-radius: 3px;
  color: var(--color-burgundy);
  font-family: var(--font-ui);
  font-size: 0.78rem;
}

/* Game single page */
.works-game-hero {
  display: grid;
  grid-template-columns: minmax(0, 400px) 1fr;
  gap: 2rem;
  align-items: start;
  margin-bottom: 2rem;
}
@media (max-width: 720px) {
  .works-game-hero { grid-template-columns: 1fr; }
}
.works-game-hero-art {
  aspect-ratio: 16 / 9;
  overflow: hidden;
  border-radius: 6px;
}
.works-game-hero-art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.works-game-tagline {
  font-style: italic;
  color: var(--color-ink-soft);
  margin: 0 0 1em 0;
}
.works-game-meta-row {
  display: flex;
  gap: 0.6em;
  flex-wrap: wrap;
  align-items: center;
  font-family: var(--font-ui);
  font-size: 0.88rem;
  color: var(--color-ink-soft);
  margin: 0 0 0.5em 0;
}
.works-game-embed {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 2rem;
}
.works-game-external {
  font-family: var(--font-ui);
  font-size: 0.9rem;
}
.works-game-screens-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.8rem;
  margin-top: 0.8rem;
}
@media (max-width: 720px) {
  .works-game-screens-grid { grid-template-columns: 1fr; }
}
.works-game-screens-grid img {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 4px;
  display: block;
}
.works-game-credits {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-ink-soft);
}
.works-game-credits h2 {
  font-family: var(--font-body);
  font-size: 1.4rem;
  margin: 0 0 0.6rem 0;
}
```

- [ ] **Step 2: Verify the build**

```bash
hugo --quiet
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add assets/css/main.css
git commit -m "$(cat <<'EOF'
css §33: works umbrella + games

3-card overview grid for /works/. Card grid + hero/screens/credits
chrome for /works/games/ and /works/games/<slug>/. Hidden-data-attr
respect for filter-chip toggles.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 21: CSS §34 — Works music

**Files:**
- Modify: `assets/css/main.css`

- [ ] **Step 1: Append §34**

```css

/* =========================================================
 * §34 Works — music
 * Music index list rows + per-music page.
 * ========================================================= */

.works-music-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1.5rem;
}
.works-music-row {
  border: 1px solid var(--color-ink-soft);
  border-radius: 6px;
  background: var(--color-stone);
  overflow: hidden;
}
.works-music-row[hidden] { display: none; }
.works-music-row-link {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 1rem;
  padding: 0.8rem;
  align-items: center;
  color: inherit;
  text-decoration: none;
}
.works-music-row-cover {
  aspect-ratio: 1 / 1;
  overflow: hidden;
  border-radius: 4px;
  background: var(--color-ink-soft);
}
.works-music-row-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.works-music-row-title {
  font-family: var(--font-body);
  margin: 0 0 0.2em 0;
}
.works-music-row-meta {
  font-family: var(--font-ui);
  font-size: 0.82rem;
  color: var(--color-ink-soft);
  margin: 0 0 0.3em 0;
}
.works-music-row-tagline {
  font-style: italic;
  color: var(--color-ink-soft);
  margin: 0;
}

/* Music single */
.works-music-hero {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 1.5rem;
  align-items: start;
  margin-bottom: 1.5rem;
}
@media (max-width: 600px) {
  .works-music-hero { grid-template-columns: 1fr; }
}
.works-music-hero-art {
  aspect-ratio: 1 / 1;
  overflow: hidden;
  border-radius: 4px;
}
.works-music-hero-art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.works-music-tagline {
  font-style: italic;
  color: var(--color-ink-soft);
  margin: 0 0 0.6em 0;
}
.works-music-meta-row {
  font-family: var(--font-ui);
  font-size: 0.88rem;
  color: var(--color-ink-soft);
  margin: 0;
}
.works-music-player {
  margin: 1.5rem 0;
}
.works-audio-link {
  display: inline-block;
  font-family: var(--font-ui);
  font-size: 0.9rem;
  padding: 0.4em 0.9em;
  border: 1px solid var(--color-burgundy);
  color: var(--color-burgundy);
  text-decoration: none;
  border-radius: 999px;
}
.works-audio-link:hover {
  background: var(--color-burgundy);
  color: var(--color-stone);
}
.works-music-tracks-list {
  font-family: var(--font-ui);
  padding-left: 1.5em;
}
.works-music-tracks-list li {
  display: flex;
  justify-content: space-between;
  gap: 1em;
  padding: 0.3em 0;
}
.works-music-track-duration {
  color: var(--color-ink-soft);
  font-variant-numeric: tabular-nums;
}
.works-music-lyrics,
.works-music-made-with {
  margin-top: 2rem;
}
.works-music-lyrics h2,
.works-music-made-with h2 {
  font-family: var(--font-body);
  font-size: 1.4rem;
  margin: 0 0 0.6rem 0;
}
```

- [ ] **Step 2: Verify the build**

```bash
hugo --quiet
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add assets/css/main.css
git commit -m "$(cat <<'EOF'
css §34: works music

List rows (80px cover + meta) for /works/music/ index. Hero (200px
cover + meta strip), player frame (audio-link pill or stub), tracks
list (monospace-aligned), lyrics-stub block for music pages.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 22: CSS §35 — Works poetry

**Files:**
- Modify: `assets/css/main.css`

- [ ] **Step 1: Append §35**

```css

/* =========================================================
 * §35 Works — poetry
 * Narrow-column index rows + poem page.
 * ========================================================= */

.works-poetry-index .page-header,
.works-poetry-index .filter-chips,
.works-poetry-list {
  max-width: 720px;
  margin-left: auto;
  margin-right: auto;
}
.works-poetry-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  margin-top: 1.5rem;
}
.works-poem-row {
  padding: 0.6em 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.works-poem-row[hidden] { display: none; }
.works-poem-row-link {
  display: block;
  color: inherit;
  text-decoration: none;
}
.works-poem-row-title {
  font-family: var(--font-body);
  font-style: italic;
  font-weight: 400;
  font-size: 1.2rem;
  margin: 0 0 0.2em 0;
}
.works-poem-row-meta {
  font-family: var(--font-ui);
  font-size: 0.82rem;
  color: var(--color-ink-soft);
  margin: 0;
}
.works-poem-row-collection,
.works-poem-row-music {
  display: inline-block;
  margin-left: 0.2em;
}
.works-poem-row-music {
  color: var(--color-burgundy);
}

/* Poem single */
.works-poem-page {
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}
.works-poem-header h1 {
  font-family: var(--font-body);
  font-style: italic;
  font-weight: 400;
  font-size: 2rem;
  margin: 0 0 0.3em 0;
}
.works-poem-meta {
  font-family: var(--font-ui);
  font-size: 0.85rem;
  color: var(--color-ink-soft);
  margin: 0 0 1rem 0;
}
.works-poem-body {
  font-family: var(--font-body);
  font-size: 1.1rem;
  line-height: 2.1;
  margin-top: 1.5rem;
}
.works-poem-body p {
  margin: 0 0 1.3em 0;
}
```

- [ ] **Step 2: Verify the build**

```bash
hugo --quiet
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add assets/css/main.css
git commit -m "$(cat <<'EOF'
css §35: works poetry

Narrow-column index rows (Petrona italic title + meta + collection +
'set to music' badge). Poem page narrow column (~600px, line-height
~2.1, generous spacing). Audio-pill chrome lives in §32.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 23: Filter-chips config + CI workflow updates

**Files:**
- Modify: `data/filter-chips.yaml`
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Append three new sections to `data/filter-chips.yaml`**

Add after the existing `garden:` block:

```yaml
games:
  primary_tags: [example, demo, prototype]
  primary_top_k: 10

music:
  primary_tags: [example, ambient, lyric]
  primary_top_k: 10

poetry:
  primary_tags: [example, lyric, collected]
  primary_top_k: 10
```

- [ ] **Step 2: Verify the filter-chips config linter still passes**

```bash
python3 tools/check_filter_chips_config.py
python3 -m unittest tools/test_check_filter_chips_config.py -v
```

Expected: both pass.

- [ ] **Step 3: Add four new CI workflow steps**

Open `.github/workflows/hugo.yaml` and find the step "Run citation linter unit tests". Immediately after it, insert:

```yaml
      - name: Verify works fixtures
        run: python3 tools/check_works_fixtures.py

      - name: Run works fixture linter unit tests
        run: python3 -m unittest tools/test_check_works_fixtures.py -v

      - name: Verify works links
        run: python3 tools/check_works_links.py

      - name: Run works links linter unit tests
        run: python3 -m unittest tools/test_check_works_links.py -v
```

- [ ] **Step 4: Verify the YAML is well-formed**

```bash
python3 -c "import yaml, sys; yaml.safe_load(open('.github/workflows/hugo.yaml'))" 2>&1 || echo "(yaml module not stdlib; skip if it errors — CI will validate)"
```

If `yaml` isn't available, fall back to:

```bash
grep -c "^      - name:" .github/workflows/hugo.yaml
```

Expected: at least 15 steps named (was 11 before; +4 new).

- [ ] **Step 5: Commit**

```bash
git add data/filter-chips.yaml .github/workflows/hugo.yaml
git commit -m "$(cat <<'EOF'
ci: gate on check_works_fixtures + check_works_links + filter-chips config

4 new steps inserted after citation linter tests. data/filter-chips.yaml
gains games / music / poetry sections (curated primary tags + top_k
override) so the existing filter-chips config linter validates them.
Total Python gates: 15 → 19.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 24: CLAUDE.md update

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the "Commands" section to add the new linters**

Find the existing list of linter commands (around the existing citations check) and insert below the `check_citations` lines:

```markdown
- `python3 tools/check_works_fixtures.py` — works fixture frontmatter linter (CI gate)
- `python3 -m unittest tools/test_check_works_fixtures.py -v` — works linter unit tests (CI gate)
- `python3 tools/check_works_links.py` — works cross-reference linter (CI gate)
- `python3 -m unittest tools/test_check_works_links.py -v` — works links linter unit tests (CI gate)
```

- [ ] **Step 2: Add the four new CSS section numbers to the CSS pipeline description**

Find the `assets/css/main.css` paragraph that enumerates sections "1 reset → 2 tokens → ..." through "31 research graph". Append:

```
 → 32 works shared chrome (status pill, audio pill, data-pending stubs, connections block)
 → 33 works umbrella + games (overview cards, game index card grid, game page hero/screens/credits)
 → 34 works music (index list rows, music page hero/player/tracks/lyrics-stub)
 → 35 works poetry (narrow-column index rows, poem page narrow column)
```

- [ ] **Step 2b: Update the JS pipeline section to add the works bundle**

Find the "JS pipeline" section in CLAUDE.md (under "Architecture"). It currently describes four multi-entry bundles (core / essay / garden / research). Add a fifth entry to the bullet list:

```markdown
- `js/entry-works.js` → `js/works.<hash>.js` (~6 KB) — `works.js` (which imports `filter-chips.js`); loaded only on `.Section == "works"`. Per-item pages no-op via internal selector guards.
```

And update the paragraph that says "Each call to `js.Build` is independent — no code-split chunks. `filter-chips.js` is bundled into both the essay and the garden bundle (small duplication, ~8 KB)." to:

```markdown
Each call to `js.Build` is independent — no code-split chunks. `filter-chips.js` is bundled into the essay, garden, and works bundles (small duplication, ~8 KB).
```

- [ ] **Step 3: Add the new layouts to the "Layouts" subsection**

Inside the bulleted list of layouts, add:

```markdown
  - `layouts/works/list.html` — `/works/` umbrella (3-card overview).
  - `layouts/works-games/{list,single}.html` — `/works/games/` index (filter chips + 2-col card grid) and per-game page (hero + embed-stub + screens + connections + credits).
  - `layouts/works-music/{list,single}.html` — `/works/music/` index (filter chips + list rows) and per-music page (hero + player-stub + tracks + lyrics-stub + connections).
  - `layouts/works-poetry/{list,single}.html` — `/works/poetry/` index (filter chips + narrow-column list) and per-poem page (narrow column + optional audio pill).
```

- [ ] **Step 4: Add the new partials to the "Partials" subsection**

Inside the bulleted list of partials, add:

```markdown
  - `works/section-card.html` (umbrella card for one sub-section)
  - `works/game-card.html` (game-index card)
  - `works/music-row.html` (music-index row)
  - `works/poem-row.html` (poetry-index row)
  - `works/status-pill.html` (game status pill — three colors via existing tokens)
  - `works/audio-pill.html` (poem-page pill linking to a music piece)
  - `works/audio-link.html` (music-page "Listen on <platform>" link from `platform_embed`)
  - `works/connections.html` (shared two-column connections block — research/essays/notes/works refs)
```

- [ ] **Step 5: Add the new shortcode**

Inside the "Shortcodes" subsection, add:

```markdown
  - `lyrics.html` — **deferred-feature stub**: emits a `<div class="synced-lyrics-stub" data-pending>` container with raw inner text. Future synced-lyrics runtime parses `[mm:ss]` timestamps and binds to an `<audio>` element via `timeupdate`.
```

- [ ] **Step 6: Add the Phase 6 status entry under "Project status"**

Insert after the "Phase 3 — citation hover-card slice complete" paragraph:

```markdown
**Phase 6 — works section slice complete (2026-05-12).** Works umbrella (`/works/`), three sub-section indexes (`/works/games/`, `/works/music/`, `/works/poetry/`), and per-item page templates for all three. 12 fixtures (4 + 4 + 4) covering every status/type/format value, with a round-trip `lyrics_poem ↔ set_to_music` pair between music and poetry. Shared `partials/filter-chips.html` reused on all three indexes — games (status, type, tag), music (format, tag), poetry (collection, tag). CSS §32–§35 (~380 lines) appended; no new tokens. Two new CI gates: `tools/check_works_fixtures.py` (per-type frontmatter contract + enum + integer + list-of-dict validation) and `tools/check_works_links.py` (resolves every cross-ref against the live content tree; enforces music↔poetry round-trip symmetry; drafts treated as missing). Total Python gates: 15 → 19. **Amends parent spec §4.19:** poetry index uses shared filter chips instead of the originally-specified three view tabs.

**Runtime deferred (fixtures exercise the shape; stubs carry `data-pending` for future swap-in):**

- Game iframe embed (itch / Bitsy / WebGL) — `works-embed-stub` anchor
- Music platform iframe (Bandcamp / SoundCloud / YouTube) — `works-audio-link` text link only (no iframe)
- Music custom audio player — `works-player-stub` block
- Synced-lyrics runtime + two-column lyrics layout (parent §4.18) — `synced-lyrics-stub` block; `lyrics` shortcode is a no-op container
- Audio-pill pulse animation — pill renders without animation
- Gif-vs-hero toggle on game cards (parent §4.14) — hero SVG only
```

- [ ] **Step 7: Update the deferred-features table**

Find the table titled "Deferred features still in plan" and append four new rows:

```markdown
| Game iframe embed | Future works runtime slice | game fixture #1 `embed_url` |
| Music platform iframe + custom audio player | Future works runtime slice | music fixtures #1 / #2 / #4 |
| Synced-lyrics runtime | Future works runtime slice | music fixture #2 ↔ poem fixture #1 |
| Gif-vs-hero toggle on game cards | When real gif assets land | n/a (no fixture hook) |
```

- [ ] **Step 8: Update the Phase 6 entry in the "remaining slices" list**

Find the bullet `**Works** (games + music + poetry) — Phase 6` and replace with:

```markdown
- ~~Works (games + music + poetry) — Phase 6.~~ Complete (2026-05-12). Runtime-heavy pieces (iframes, custom audio widget, synced-lyrics playback) tracked separately as follow-up slices.
```

- [ ] **Step 9: Commit**

```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
CLAUDE.md: document works section slice (Phase 6)

New layouts (works umbrella + 3 sub-section indexes + 3 singles).
New partials (section-card, game-card, music-row, poem-row, status-
pill, audio-pill, audio-link, connections). New lyrics shortcode
stub. New CSS §32–§35. New CI gates (check_works_fixtures +
check_works_links). 12 new fixtures with round-trip music↔poetry pair.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 25: Final QA + dev-server walkthrough

**Files:** none modified — this is verification + decision.

- [ ] **Step 1: Run every CI gate locally in sequence**

```bash
python3 tools/check-contrast.py && \
python3 tools/check_fixtures.py && \
python3 -m unittest tools/test_check_fixtures.py && \
python3 tools/check_garden_fixtures.py && \
python3 -m unittest tools/test_check_garden_fixtures.py && \
python3 tools/check_garden_links.py && \
python3 -m unittest tools/test_check_garden_links.py && \
python3 tools/check_filter_chips_config.py && \
python3 -m unittest tools/test_check_filter_chips_config.py && \
python3 tools/check_research_fixtures.py && \
python3 -m unittest tools/test_check_research_fixtures.py && \
python3 tools/check_research_links.py && \
python3 -m unittest tools/test_check_research_links.py && \
python3 tools/check_citations.py && \
python3 -m unittest tools/test_check_citations.py && \
python3 tools/check_works_fixtures.py && \
python3 -m unittest tools/test_check_works_fixtures.py && \
python3 tools/check_works_links.py && \
python3 -m unittest tools/test_check_works_links.py
```

Expected: every command exits 0.

- [ ] **Step 2: Clean build with hugo extended**

Per the memory `reference_hugo_dev_server_gotcha.md`, kill any running dev server first, then:

```bash
rm -rf public/
hugo --minify
```

Expected: build success, no warnings. Spot-check `public/works/index.html`, `public/works/games/index.html`, `public/works/music/index.html`, `public/works/poetry/index.html` all exist, and `public/js/works.<hash>.js` exists.

- [ ] **Step 3: Start dev server for visual walkthrough**

```bash
hugo server --buildDrafts
```

Open in browser and eyeball each of:

1. `/works/` — three umbrella cards render with counts (4 / 4 / 4) and recent-3 titles
2. `/works/games/` — 4 game cards in 2-col grid; filter chips show status (3 values) + type (4 values) + tag dim; click "playable" → 2 cards remain; click "playable" again → all 4 return
3. `/works/games/example-playable-full-release/` — hero SVG renders, "Play in browser" stub link visible (italic + dotted), screens 3-up grid renders, connections block shows 3 columns
4. `/works/games/example-playable-jam/` — hero SVG only, no screens, no connections block (graceful empty)
5. `/works/music/` — 4 music rows render with cover thumbs and meta
6. `/works/music/example-track-with-lyrics/` — cover hero, "Listen on Soundcloud" pill, tracks section absent, lyrics-stub block links to the poem
7. `/works/music/example-album-with-tracks/` — 6 tracks render as numbered list
8. `/works/poetry/` — 4 rows in narrow column, "set to music" badge on the lyrics poem, collection badge on two poems
9. `/works/poetry/example-poem-with-lyrics/` — audio pill above body, body renders with generous leading
10. Theme toggle works on every page
11. Mobile (DevTools narrow): grids collapse to single column, music hero stacks vertically

- [ ] **Step 4: Surface the visual findings to the user**

Per memory `feedback_verify_before_merge`: offer a "what to eyeball" summary and wait for user authorization before merging. Mention:

- Anything that surprised you (rendering glitches, missing styles, contrast issues, broken links).
- Anything that LOOKS like it works but you couldn't verify without real content (e.g. behavior when many fixtures exist).
- Explicit confirmation that the seven deferred items are all present as stubs with `data-pending`.

- [ ] **Step 5: After user approval, merge to master**

```bash
git checkout master
git merge --no-ff slice/works-section -m "$(cat <<'EOF'
Merge slice/works-section: Phase 6 — works umbrella + games + music + poetry

Full surface, runtime deferred. 12 fixtures, 2 new CI gates, 4 new CSS
sections, 8 new partials, 1 new shortcode stub. Amends parent spec
§4.19: poetry uses filter chips instead of view tabs.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: Push (only after user explicit OK)**

```bash
git push origin master
```

Expected: master is now ahead of remote by N commits.
