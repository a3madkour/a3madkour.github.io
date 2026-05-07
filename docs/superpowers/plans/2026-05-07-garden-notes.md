# Garden Notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Garden section of the personal site — `/garden/` index with multi-dimension AND filter chips + topic-map sections + "Other notes" catch-all, single-template note pages with flavor-routed metadata strip (concept / media / reference), `topic_map:` frontmatter facet, hand-authored SVG growth-stage glyphs, working `<details>`-based spoiler shortcode, per-section RSS, 14 fixture notes, and the essays-side refactor that migrates both pages onto a shared filter-chips module in AND mode.

**Architecture:** Hugo static site, hand-rolled CSS (extends `assets/css/main.css` with new sections 19–23, generalizes §16), one shared `filter-chips.js` ES module added to the bundle, plus a small `garden.js` page-level entry. Note flavor (concept/media/reference) is derived at render time from `media_type`. Topic maps are an optional frontmatter facet (`topic_map: [slug, ...]`), not a separate URL — one canonical URL per idea at `/garden/<slug>/`. Spoiler runtime uses the native `<details>` element. Fixtures are lorem-ipsum / "Example N" filler only.

**Tech Stack:** Hugo extended ≥0.148.0, Python 3 (linter — stdlib only), vanilla JS (ES modules, esbuild via Hugo's `js.Build`), CSS (Grid + custom properties).

**Spec:** `docs/superpowers/specs/2026-05-07-garden-notes-design.md`. Read it before starting any task.

**Spec amendment carried by this slice:** Parent spec §4.9 specified topic maps at `/garden/topics/<slug>/`. This slice supersedes that — topic maps are a facet of any note (`:TOPIC_MAP:` org property → `topic_map:` markdown field). Single canonical URL per idea.

**Existing reusable components (don't reimplement):**
- `tools/check_fixtures.py` exposes `parse_frontmatter`, `parse_scalar`, and `FRONTMATTER_RE` at module level. The new linter imports these — same YAML-subset parser, no third-party deps.
- `assets/css/main.css` defines all colour/typography tokens. New CSS reuses them; never hardcode colour values except for the new `--color-green` token added in §20.
- `layouts/partials/header.html` already switches the RSS button URL based on URL prefix (essays → essays feed). The same pattern extends to garden in Task 13.
- `assets/js/essay.js` currently contains `setupFilterChips`. The new shared module replaces it; this slice deletes the inline copy.

**Verification model:**
- Python linter: real unit tests via stdlib `unittest`.
- Hugo templates / shortcodes / CSS: TDD-as-fixture — fixture exercising the feature exists or is added; `hugo --minify` build is run; visual inspection in `hugo server` is the assertion. Each task ends with explicit build success + browser check at the affected URL.
- Final task: full manual walkthrough checklist plus the regression check on `/essays/`.

**Working assumption:** Run `hugo server --buildDrafts` continuously in a separate terminal during implementation; inspect at `http://localhost:1313/`.

---

## Task 1: Garden fixture frontmatter linter (`tools/check_garden_fixtures.py`)

**Files:**
- Create: `tools/check_garden_fixtures.py`
- Create: `tools/test_check_garden_fixtures.py`

The linter walks `content/garden/<slug>/index.md` (skipping `_index.md`), parses YAML frontmatter, and validates the per-flavor schema from spec §5.1. Stdlib only — imports the YAML-subset parser from `tools/check_fixtures.py` so we share one parser across both linters.

- [ ] **Step 1: Write the failing tests**

Create `tools/test_check_garden_fixtures.py`:

```python
"""Tests for check_garden_fixtures.py — run with:
   python3 -m unittest tools/test_check_garden_fixtures.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_garden_fixtures as lint  # noqa: E402


CONCEPT_NOTE = """\
---
title: "Salience and memory"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
tags: ["memory", "narrative"]
---

Lorem ipsum dolor sit amet.
"""

CONCEPT_TOPIC_MAP_NOTE = """\
---
title: "Procedural narrative"
draft: false
last_modified: 2026-04-25
growth_stage: budding
tags: ["narrative", "games"]
topic_map: ["surprise-budget", "salience-and-memory"]
---

Framing prose.
"""

MEDIA_NOTE = """\
---
title: "Invisible Cities"
draft: false
last_modified: 2026-04-30
growth_stage: budding
media_type: book
status: reading
creator: "Italo Calvino"
year: 1972
started: 2025-12-15
spoiler_level: light
original_url: "https://example.invalid/book"
tags: ["reading", "calvino"]
---

Body.
"""

REFERENCE_NOTE = """\
---
title: "Games as art"
draft: false
last_modified: 2026-04-12
growth_stage: evergreen
media_type: paper
creator: "Nguyen, C. T."
year: 2020
original_url: "https://doi.org/10.1234/abc"
tags: ["games", "aesthetics"]
---

Body.
"""


class TempRepo:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        (self.root / "content" / "garden").mkdir(parents=True)

    def write_note(self, slug: str, body: str) -> None:
        d = self.root / "content" / "garden" / slug
        d.mkdir(exist_ok=True)
        (d / "index.md").write_text(body)

    def cleanup(self) -> None:
        shutil.rmtree(self.root)


class GardenLinterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    # --- happy paths ---

    def test_valid_concept_note_passes(self) -> None:
        self.repo.write_note("salience-and-memory", CONCEPT_NOTE)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_media_note_passes(self) -> None:
        self.repo.write_note("invisible-cities", MEDIA_NOTE)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_reference_note_passes(self) -> None:
        self.repo.write_note("nguyen-2020", REFERENCE_NOTE)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_topic_map_resolves(self) -> None:
        self.repo.write_note("surprise-budget", CONCEPT_NOTE.replace(
            'title: "Salience and memory"', 'title: "Surprise budget"'
        ))
        self.repo.write_note("salience-and-memory", CONCEPT_NOTE)
        self.repo.write_note("procedural-narrative", CONCEPT_TOPIC_MAP_NOTE)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_empty_garden_passes(self) -> None:
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0)

    # --- required-field failures ---

    def test_missing_title_fails(self) -> None:
        broken = CONCEPT_NOTE.replace('title: "Salience and memory"\n', "")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("title" in e for e in errors))

    def test_missing_growth_stage_fails(self) -> None:
        broken = CONCEPT_NOTE.replace("growth_stage: seedling\n", "")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("growth_stage" in e for e in errors))

    def test_media_missing_status_fails(self) -> None:
        broken = MEDIA_NOTE.replace("status: reading\n", "")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("status" in e for e in errors))

    def test_media_missing_creator_fails(self) -> None:
        broken = MEDIA_NOTE.replace('creator: "Italo Calvino"\n', "")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("creator" in e for e in errors))

    def test_reference_missing_creator_fails(self) -> None:
        broken = REFERENCE_NOTE.replace('creator: "Nguyen, C. T."\n', "")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("creator" in e for e in errors))

    # --- forbidden-field failures ---

    def test_concept_with_status_fails(self) -> None:
        broken = CONCEPT_NOTE.replace(
            "growth_stage: seedling\n",
            "growth_stage: seedling\nstatus: reading\n",
        )
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("status" in e and "concept" in e for e in errors))

    def test_concept_with_started_fails(self) -> None:
        broken = CONCEPT_NOTE.replace(
            "growth_stage: seedling\n",
            "growth_stage: seedling\nstarted: 2026-01-01\n",
        )
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("started" in e for e in errors))

    def test_reference_with_status_fails(self) -> None:
        broken = REFERENCE_NOTE.replace(
            "growth_stage: evergreen\n",
            "growth_stage: evergreen\nstatus: reading\n",
        )
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("status" in e and "reference" in e for e in errors))

    # --- enum-validation failures ---

    def test_invalid_growth_stage_fails(self) -> None:
        broken = CONCEPT_NOTE.replace("growth_stage: seedling", "growth_stage: enormous")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("growth_stage" in e and "enormous" in e for e in errors))

    def test_invalid_status_fails(self) -> None:
        broken = MEDIA_NOTE.replace("status: reading", "status: pondering")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("status" in e and "pondering" in e for e in errors))

    def test_invalid_media_type_fails(self) -> None:
        broken = MEDIA_NOTE.replace("media_type: book", "media_type: scroll")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("media_type" in e and "scroll" in e for e in errors))

    def test_invalid_spoiler_level_fails(self) -> None:
        broken = MEDIA_NOTE.replace("spoiler_level: light", "spoiler_level: extreme")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("spoiler_level" in e for e in errors))

    # --- date validation ---

    def test_future_last_modified_fails(self) -> None:
        broken = CONCEPT_NOTE.replace("last_modified: 2026-04-22", "last_modified: 2099-01-01")
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("last_modified" in e and "future" in e for e in errors))

    # --- topic_map resolution ---

    def test_topic_map_unresolved_fails(self) -> None:
        broken = CONCEPT_TOPIC_MAP_NOTE.replace(
            'topic_map: ["surprise-budget", "salience-and-memory"]',
            'topic_map: ["does-not-exist"]',
        )
        self.repo.write_note("procedural-narrative", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("does-not-exist" in e for e in errors))

    def test_topic_map_to_draft_fails(self) -> None:
        draft_note = CONCEPT_NOTE.replace("draft: false", "draft: true")
        self.repo.write_note("draft-target", draft_note)
        owner = CONCEPT_TOPIC_MAP_NOTE.replace(
            'topic_map: ["surprise-budget", "salience-and-memory"]',
            'topic_map: ["draft-target"]',
        )
        self.repo.write_note("procedural-narrative", owner)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("draft" in e for e in errors))

    # --- url validation ---

    def test_invalid_original_url_scheme_fails(self) -> None:
        broken = MEDIA_NOTE.replace(
            'original_url: "https://example.invalid/book"',
            'original_url: "ftp://example.invalid/book"',
        )
        self.repo.write_note("broken", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("original_url" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail (no module yet)**

Run: `python3 -m unittest tools/test_check_garden_fixtures.py -v`
Expected: ImportError / ModuleNotFoundError on `import check_garden_fixtures`.

- [ ] **Step 3: Implement `tools/check_garden_fixtures.py`**

```python
#!/usr/bin/env python3
"""Garden note fixture frontmatter linter.

Walks `content/garden/<slug>/index.md` (skips `_index.md`), validates
flavor-specific frontmatter per spec §5.1, and verifies that every
`topic_map:` entry resolves to an existing non-draft note.

Exits 0 on all-pass, 1 on any violation. Stdlib only — imports the YAML
parser from check_fixtures so both linters share one parser.
"""
from __future__ import annotations

import sys
from datetime import date as Date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

# --- contract ---

ALWAYS_REQUIRED = {"title", "draft", "last_modified", "growth_stage"}

GROWTH_STAGES = {"seedling", "budding", "evergreen"}
STATUSES = {"reading", "finished", "abandoned", "queued"}
SPOILER_LEVELS = {"none", "light", "heavy"}

MEDIA_TYPES = {"book", "album", "track", "game", "film", "series"}
REFERENCE_TYPES = {"paper", "video", "article", "talk"}
ALL_MEDIA_TYPES = MEDIA_TYPES | REFERENCE_TYPES

# Fields permitted on each flavor (anything else is forbidden)
CONCEPT_FIELDS = ALWAYS_REQUIRED | {"tags", "summary", "topic_map", "roam_refs", "year"}
MEDIA_FIELDS = ALWAYS_REQUIRED | {
    "media_type", "status", "creator",
    "tags", "summary", "topic_map", "roam_refs", "year",
    "original_url", "started", "finished", "spoiler_level",
}
REFERENCE_FIELDS = ALWAYS_REQUIRED | {
    "media_type", "creator",
    "tags", "summary", "topic_map", "roam_refs", "year",
    "original_url",
}

MEDIA_REQUIRED_EXTRA = {"media_type", "status", "creator"}
REFERENCE_REQUIRED_EXTRA = {"media_type", "creator"}


def derive_flavor(fm: dict[str, object]) -> str:
    media_type = fm.get("media_type")
    if not media_type:
        return "concept"
    if media_type in MEDIA_TYPES:
        return "media"
    if media_type in REFERENCE_TYPES:
        return "reference"
    return "unknown"


def lint_note(note_dir: Path) -> tuple[list[str], dict[str, object] | None]:
    """Return (errors, parsed_frontmatter_or_None) for a single note dir."""
    errors: list[str] = []
    md = note_dir / "index.md"
    if not md.exists():
        return [f"{note_dir}: no index.md"], None
    text = md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md}: no frontmatter"], None

    # Always-required fields
    for field in sorted(ALWAYS_REQUIRED - fm.keys()):
        errors.append(f"{md}: missing required field '{field}'")

    # Enum: growth_stage
    stage = fm.get("growth_stage")
    if stage and stage not in GROWTH_STAGES:
        errors.append(
            f"{md}: growth_stage='{stage}' not in {sorted(GROWTH_STAGES)}"
        )

    # Date: last_modified
    lm = fm.get("last_modified")
    if isinstance(lm, Date) and lm > Date.today():
        errors.append(f"{md}: last_modified {lm} is in the future")

    # Flavor-specific
    flavor = derive_flavor(fm)
    if flavor == "unknown":
        errors.append(
            f"{md}: media_type='{fm.get('media_type')}' "
            f"not in {sorted(ALL_MEDIA_TYPES)}"
        )
        return errors, fm

    if flavor == "concept":
        allowed = CONCEPT_FIELDS
    elif flavor == "media":
        allowed = MEDIA_FIELDS
        for f in sorted(MEDIA_REQUIRED_EXTRA - fm.keys()):
            errors.append(f"{md}: '{f}' is required for media notes")
    else:  # reference
        allowed = REFERENCE_FIELDS
        for f in sorted(REFERENCE_REQUIRED_EXTRA - fm.keys()):
            errors.append(f"{md}: '{f}' is required for reference notes")

    for f in sorted(set(fm.keys()) - allowed):
        errors.append(f"{md}: '{f}' not permitted on {flavor} notes")

    # Enum checks for media-only fields
    if flavor == "media":
        status = fm.get("status")
        if status and status not in STATUSES:
            errors.append(
                f"{md}: status='{status}' not in {sorted(STATUSES)}"
            )
        spl = fm.get("spoiler_level")
        if spl and spl not in SPOILER_LEVELS:
            errors.append(
                f"{md}: spoiler_level='{spl}' not in {sorted(SPOILER_LEVELS)}"
            )

    # URL scheme check
    url = fm.get("original_url")
    if url and not (str(url).startswith("http://") or str(url).startswith("https://")):
        errors.append(f"{md}: original_url must be http(s)")

    return errors, fm


def run(repo_root: Path) -> tuple[int, list[str]]:
    garden_dir = repo_root / "content" / "garden"
    errors: list[str] = []

    if not garden_dir.exists():
        return 0, []

    # Pass 1: lint each note, build the slug → frontmatter index
    notes: dict[str, dict[str, object]] = {}
    for entry in sorted(garden_dir.iterdir()):
        if not entry.is_dir():
            continue
        slug = entry.name
        if slug.startswith("_"):
            continue
        note_errors, fm = lint_note(entry)
        errors.extend(note_errors)
        if fm is not None:
            notes[slug] = fm

    # Pass 2: validate every topic_map entry resolves to an existing
    # non-draft note in the index
    for slug, fm in notes.items():
        topic_map = fm.get("topic_map")
        if not isinstance(topic_map, list):
            continue
        for i, entry_slug in enumerate(topic_map):
            target = notes.get(str(entry_slug))
            owner_md = garden_dir / slug / "index.md"
            if target is None:
                errors.append(
                    f"{owner_md}: topic_map[{i}]='{entry_slug}' "
                    f"does not resolve to an existing note"
                )
                continue
            if target.get("draft") is True:
                errors.append(
                    f"{owner_md}: topic_map[{i}]='{entry_slug}' "
                    f"is a draft; drafts cannot be in published topic maps"
                )

    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        print("Garden fixture lint failures:")
        for e in errors:
            print(f"  {e}")
    else:
        print("All garden fixtures pass linter.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tools/test_check_garden_fixtures.py -v`
Expected: 18 tests, all pass.

- [ ] **Step 5: Run the linter against the current repo (no garden fixtures yet)**

Run: `python3 tools/check_garden_fixtures.py`
Expected: `All garden fixtures pass linter.` (trivially passes — no fixtures yet).

- [ ] **Step 6: Commit**

```bash
git add tools/check_garden_fixtures.py tools/test_check_garden_fixtures.py
git commit -m "Add garden fixture frontmatter linter"
```

---

## Task 2: Wire `check_garden_fixtures.py` into CI

**Files:**
- Modify: `.github/workflows/hugo.yaml` (add two steps after the existing essay linter steps, before the Build step)

- [ ] **Step 1: Add the workflow steps**

In `.github/workflows/hugo.yaml`, find:
```yaml
      - name: Run linter unit tests
        run: python3 -m unittest tools/test_check_fixtures.py -v
      - name: Build with Hugo
```

Replace with:
```yaml
      - name: Run linter unit tests
        run: python3 -m unittest tools/test_check_fixtures.py -v
      - name: Verify garden fixtures
        run: python3 tools/check_garden_fixtures.py
      - name: Run garden linter unit tests
        run: python3 -m unittest tools/test_check_garden_fixtures.py -v
      - name: Build with Hugo
```

- [ ] **Step 2: Run the full CI gate set locally**

Run:
```bash
python3 tools/check-contrast.py && \
python3 tools/check_fixtures.py && \
python3 -m unittest tools/test_check_fixtures.py -v && \
python3 tools/check_garden_fixtures.py && \
python3 -m unittest tools/test_check_garden_fixtures.py -v
```
Expected: every step succeeds. Final line: `All garden fixtures pass linter.`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "Wire garden fixture linter into Pages workflow"
```

---

## Task 3: Stage glyph partial + stage colour CSS

**Files:**
- Create: `layouts/partials/garden/stage-glyph.html`
- Modify: `assets/css/main.css` — append section §19 token additions (just `--color-green` for now; full sections come later)

The partial emits inline SVG with `currentColor` stroke. The consumer sets stroke colour via a `.stage-{seedling,budding,evergreen}` class on a wrapping element.

- [ ] **Step 1: Add `--color-green` to the token blocks**

In `assets/css/main.css`, find the `:root {` block (light mode tokens, around line 17). Inside, after `--color-steel:    #1e4060;`, add:
```css
  --color-green:    #2d5a3d;
```

In the dark-mode override block (`:root[data-theme="dark"]`, around line 46) and the dark-mode media-query block (`@media (prefers-color-scheme: dark) :root:not([data-theme])`, around line 59), add the same line in each (use the dark variant `#7eafd0`'s analogous lightened green — `#86c099`):
```css
  --color-green:    #86c099;
```

Confirm: each of the three token blocks now declares `--color-green`.

- [ ] **Step 2: Verify contrast still passes**

Run: `python3 tools/check-contrast.py`
Expected: pass (the existing checked pairings are unchanged; we just added a new token).

- [ ] **Step 3: Create the stage-glyph partial**

Create `layouts/partials/garden/stage-glyph.html`:

```go-html-template
{{- /* Inputs:
       .stage  — "seedling" | "budding" | "evergreen"
       .size   — "lg" | "sm" | "xs" (default "sm")
   Returns inline SVG; stroke is currentColor so consumers control colour.
*/ -}}
{{- $stage := .stage -}}
{{- $size  := .size | default "sm" -}}
{{- $px    := 14 -}}
{{- $sw    := "1.6" -}}
{{- if eq $size "lg" -}}{{- $px = 20 -}}{{- $sw = "1.6" -}}{{- end -}}
{{- if eq $size "xs" -}}{{- $px = 11 -}}{{- $sw = "1.8" -}}{{- end -}}
<svg class="stage-glyph stage-glyph-{{ $size }}"
     width="{{ $px }}" height="{{ $px }}"
     viewBox="0 0 24 24"
     fill="none"
     stroke="currentColor"
     stroke-width="{{ $sw }}"
     stroke-linecap="round"
     aria-hidden="true">
  {{- if eq $stage "seedling" -}}
  <path d="M12 21 V13"/>
  <path d="M12 15 C9 14 7 11 7 8 C10 8 12 11 12 14"/>
  <path d="M3 21 H21"/>
  {{- else if eq $stage "budding" -}}
  <path d="M12 21 V11"/>
  <path d="M12 14 C8 13 6 10 6 7 C9 7 11 9 12 12"/>
  <path d="M12 13 C15 12 17 9 17 6 C14 6 12 8 12 11"/>
  {{- else if eq $stage "evergreen" -}}
  <path d="M12 4 L7 12 H10 L7 18 H17 L14 12 H17 Z"/>
  <path d="M12 18 V21"/>
  {{- end -}}
</svg>
```

- [ ] **Step 4: Run Hugo build to confirm template parses**

Run: `hugo --minify`
Expected: success (no template errors). Partial isn't called from any page yet, so no visual change.

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/garden/stage-glyph.html assets/css/main.css
git commit -m "Add garden stage-glyph partial and --color-green token"
```

---

## Task 4: Note tile partial + tile CSS (§21)

**Files:**
- Create: `layouts/partials/garden/note-tile.html`
- Modify: `assets/css/main.css` — append §19 placeholder + §21 (note tile)

The tile is a single card used by topic-section grids and by the `/garden/` index "Other notes" list. It emits a `.garden-tile` anchor with `data-tags`/`data-flavor`/`data-stage` attributes that drive the filter JS later.

- [ ] **Step 1: Create `layouts/partials/garden/note-tile.html`**

```go-html-template
{{- /* Inputs:
       .page  — a *hugolib.Page, the target garden note
   Renders a single tile. Adds data-* attrs for the filter JS.
*/ -}}
{{- $page := .page -}}
{{- $stage := $page.Params.growth_stage | default "seedling" -}}
{{- $mediaType := $page.Params.media_type -}}
{{- $flavor := "concept" -}}
{{- if $mediaType -}}
  {{- if in (slice "book" "album" "track" "game" "film" "series") $mediaType -}}
    {{- $flavor = "media" -}}
  {{- else -}}
    {{- $flavor = "reference" -}}
  {{- end -}}
{{- end -}}
{{- $tags := delimit ($page.Params.tags | default slice) " " -}}
<a class="garden-tile stage-{{ $stage }}"
   href="{{ $page.RelPermalink }}"
   data-tags="{{ $tags }}"
   data-flavor="{{ $flavor }}"
   data-stage="{{ $stage }}">
  <div class="tile-stage">
    {{ partial "garden/stage-glyph.html" (dict "stage" $stage "size" "sm") }}
    <span class="tile-stage-label">{{ title $stage }}</span>
  </div>
  <p class="tile-title">{{ $page.Title }}</p>
  <div class="tile-meta">
    {{- with $page.Params.last_modified -}}
      tended {{ partial "garden/relative-date.html" (dict "date" .) }}
    {{- end -}}
  </div>
</a>
```

- [ ] **Step 2: Create the relative-date helper partial**

Create `layouts/partials/garden/relative-date.html`:

```go-html-template
{{- /* Input: .date — a time.Time (or YAML date)
   Output: "Nd ago" / "N days ago" / "today" / "yesterday" — short form.
*/ -}}
{{- $now := now -}}
{{- $then := .date -}}
{{- $diff := math.Floor (div (sub $now.Unix $then.Unix) 86400) -}}
{{- if le $diff 0 -}}today
{{- else if eq $diff 1.0 -}}yesterday
{{- else if lt $diff 30.0 -}}{{ int $diff }}d ago
{{- else if lt $diff 365.0 -}}{{ math.Floor (div $diff 30) }}mo ago
{{- else -}}{{ math.Floor (div $diff 365) }}y ago
{{- end -}}
```

- [ ] **Step 3: Append §19 placeholder + §21 (note tile) to `assets/css/main.css`**

After the existing `/* 18. Homepage essays strip */` block (ends around line 668), append:

```css

/* ------------------------------------------------------------------
 * 19. Garden index (placeholder — full styles in Task 9)
 * ------------------------------------------------------------------ */
.garden-grid { /* deferred to Task 9 */ }

/* ------------------------------------------------------------------
 * 20. Garden note header strip + status pill (placeholder — Task 6)
 * ------------------------------------------------------------------ */
.garden-note-header { /* deferred to Task 6 */ }

/* ------------------------------------------------------------------
 * 21. Garden note tile
 * ------------------------------------------------------------------ */
.garden-tile {
  display: block;
  background: var(--color-tile);
  border: 1px solid var(--color-rule);
  border-radius: 6px;
  padding: 0.6rem 0.75rem;
  text-decoration: none;
  color: var(--color-ink);
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.garden-tile:hover {
  border-color: var(--color-burgundy);
  transform: translateY(-1px);
}
.garden-tile.stage-seedling { color: var(--color-burgundy); }
.garden-tile.stage-budding  { color: var(--color-steel); }
.garden-tile.stage-evergreen { color: var(--color-green); }

.garden-tile .tile-stage {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: currentColor;
  margin-bottom: 0.25rem;
}
.garden-tile .stage-glyph { color: currentColor; }
.garden-tile .tile-stage-label { color: var(--color-ink-soft); }

.garden-tile .tile-title {
  margin: 0;
  font-family: var(--font-body);
  font-weight: 600;
  font-size: var(--text-base);
  line-height: 1.25;
  color: var(--color-ink);
}
.garden-tile .tile-meta {
  margin-top: 0.35rem;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-fade);
}

/* Hidden by filter (no display:none, so layout shifts are minimal) */
.garden-tile[hidden] { display: none; }
```

- [ ] **Step 4: Build Hugo to confirm CSS parses + partial parses**

Run: `hugo --minify`
Expected: success.

- [ ] **Step 5: Run contrast check**

Run: `python3 tools/check-contrast.py`
Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add layouts/partials/garden/note-tile.html layouts/partials/garden/relative-date.html assets/css/main.css
git commit -m "Add garden note-tile partial, relative-date helper, tile CSS (§21)"
```

---

## Task 5: Topic-section partial

**Files:**
- Create: `layouts/partials/garden/topic-section.html`

Renders a single topic-map section: H2 link to the topic-map note, italic framing paragraph, then a tile grid resolved from the note's `topic_map:` array.

- [ ] **Step 1: Create the partial**

```go-html-template
{{- /* Inputs:
       .context  — the topic-map note (a *hugolib.Page with .Params.topic_map set)
       .heading  — optional heading text override (defaults to .context.Title)
       .framing  — optional framing override (defaults to first paragraph of body)
       .linkHeading  — bool, true to wrap heading in an anchor to context (default true)
*/ -}}
{{- $ctx := .context -}}
{{- $heading := .heading | default $ctx.Title -}}
{{- $framing := .framing -}}
{{- $linkHeading := true -}}
{{- if isset . "linkHeading" -}}{{- $linkHeading = .linkHeading -}}{{- end -}}
{{- if not $framing -}}{{- $framing = $ctx.Params.summary -}}{{- end -}}
{{- if not $framing -}}
  {{- $plain := $ctx.Plain -}}
  {{- $first := index (split $plain "\n\n") 0 -}}
  {{- $framing = $first | strings.TrimSpace -}}
{{- end -}}
<section class="garden-topic" data-garden-section="topic" data-topic-slug="{{ path.Base $ctx.File.Dir }}">
  <h2 class="garden-topic-heading">
    {{- if $linkHeading -}}
    <a href="{{ $ctx.RelPermalink }}">{{ $heading }}</a>
    {{- else -}}
    {{ $heading }}
    {{- end -}}
  </h2>
  {{- with $framing -}}
  <p class="garden-topic-framing">{{ . }}</p>
  {{- end -}}
  <div class="garden-tiles">
    {{- range $ctx.Params.topic_map -}}
      {{- $slug := . -}}
      {{- with $.Site.GetPage (printf "/garden/%s/" $slug) -}}
        {{ partial "garden/note-tile.html" (dict "page" .) }}
      {{- else -}}
        {{- errorf "topic_map entry %q on %q does not resolve" $slug $ctx.RelPermalink -}}
      {{- end -}}
    {{- end -}}
  </div>
</section>
```

- [ ] **Step 2: Append topic-section CSS to §19 placeholder**

Replace the §19 placeholder line (`.garden-grid { /* deferred to Task 9 */ }`) in `assets/css/main.css` with:

```css
.garden-topic { margin: 2rem 0 0; }
.garden-topic-heading {
  font-family: var(--font-body);
  font-weight: 600;
  font-size: var(--text-lg);
  margin: 0 0 0.25rem;
  color: var(--color-ink);
}
.garden-topic-heading a {
  color: var(--color-ink);
  text-decoration: none;
  border-bottom: 1px dotted var(--color-burgundy);
}
.garden-topic-heading a:hover { color: var(--color-burgundy); }
.garden-topic-framing {
  font-family: var(--font-body);
  font-style: italic;
  color: var(--color-ink-soft);
  font-size: var(--text-sm);
  margin: 0 0 0.75rem;
  max-width: 60ch;
  line-height: 1.5;
}
.garden-tiles {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.6rem;
}
/* When a topic section has no visible tiles (filter applied), hide it */
.garden-topic[hidden] { display: none; }
```

- [ ] **Step 3: Build Hugo to confirm**

Run: `hugo --minify`
Expected: success.

- [ ] **Step 4: Commit**

```bash
git add layouts/partials/garden/topic-section.html assets/css/main.css
git commit -m "Add garden topic-section partial and topic-grid CSS"
```

---

## Task 6: Note header partial + header CSS (§20)

**Files:**
- Create: `layouts/partials/garden/note-header.html`
- Modify: `assets/css/main.css` — replace §20 placeholder with full styles

The note header is a flex strip with: stage glyph + label · tended date · (media-only: status pill, started date, spoiler-level warning) · (reference-only: uppercase media-type label).

- [ ] **Step 1: Create the partial**

```go-html-template
{{- /* Inputs:
       . — a Hugo Page (the note being rendered)
   Output: the metadata strip above the title.
*/ -}}
{{- $stage := .Params.growth_stage | default "seedling" -}}
{{- $mediaType := .Params.media_type -}}
{{- $flavor := "concept" -}}
{{- if $mediaType -}}
  {{- if in (slice "book" "album" "track" "game" "film" "series") $mediaType -}}
    {{- $flavor = "media" -}}
  {{- else -}}
    {{- $flavor = "reference" -}}
  {{- end -}}
{{- end -}}
<div class="garden-note-header stage-{{ $stage }}">
  <span class="stage">
    {{ partial "garden/stage-glyph.html" (dict "stage" $stage "size" "lg") }}
    <span class="stage-label">{{ title $stage }}</span>
  </span>
  <span class="meta-sep" aria-hidden="true">·</span>
  {{- with .Params.last_modified -}}
  <span class="tended">tended {{ partial "garden/relative-date.html" (dict "date" .) }}</span>
  {{- end -}}

  {{- if eq $flavor "media" -}}
    {{- with .Params.status -}}
    <span class="meta-sep" aria-hidden="true">·</span>
    <span class="status-pill status-{{ . }}" aria-label="status: {{ . }}">
      {{- if eq . "reading" -}}
      <svg viewBox="0 0 9 9" aria-hidden="true"><circle cx="4.5" cy="4.5" r="3" fill="currentColor"/></svg>
      {{- else if eq . "finished" -}}
      <svg viewBox="0 0 9 9" aria-hidden="true"><path d="M2 5 L4 7 L7 3" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
      {{- else if eq . "abandoned" -}}
      <svg viewBox="0 0 9 9" aria-hidden="true"><path d="M2 2 L7 7 M7 2 L2 7" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>
      {{- else if eq . "queued" -}}
      <svg viewBox="0 0 9 9" aria-hidden="true"><path d="M4.5 7 V2 M2.5 4 L4.5 2 L6.5 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
      {{- end -}}
      <span>{{ title . }}</span>
    </span>
    {{- end -}}
    {{- with .Params.started -}}
    <span class="meta-sep" aria-hidden="true">·</span>
    <span class="started">started {{ . | dateFormat "2 Jan 2006" }}</span>
    {{- end -}}
    {{- with .Params.finished -}}
    <span class="meta-sep" aria-hidden="true">·</span>
    <span class="finished">finished {{ . | dateFormat "2 Jan 2006" }}</span>
    {{- end -}}
    {{- $sl := .Params.spoiler_level | default "none" -}}
    {{- if or (eq $sl "light") (eq $sl "heavy") -}}
    <span class="meta-sep" aria-hidden="true">·</span>
    <span class="spoiler-warning" role="note">⚠ {{ $sl }} spoilers</span>
    {{- end -}}
  {{- else if eq $flavor "reference" -}}
    <span class="meta-sep" aria-hidden="true">·</span>
    <span class="ref-type">{{ upper $mediaType }}</span>
  {{- end -}}
</div>
```

- [ ] **Step 2: Replace §20 placeholder in `assets/css/main.css`**

Find:
```css
/* ------------------------------------------------------------------
 * 20. Garden note header strip + status pill (placeholder — Task 6)
 * ------------------------------------------------------------------ */
.garden-note-header { /* deferred to Task 6 */ }
```

Replace with:
```css
/* ------------------------------------------------------------------
 * 20. Garden note header strip + status pill
 * ------------------------------------------------------------------ */
.garden-note-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--color-rule);
  margin-bottom: 0.9rem;
}
.garden-note-header .meta-sep { color: var(--color-ink-fade); }
.garden-note-header .stage {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.garden-note-header.stage-seedling .stage { color: var(--color-burgundy); }
.garden-note-header.stage-budding  .stage { color: var(--color-steel); }
.garden-note-header.stage-evergreen .stage { color: var(--color-green); }
.garden-note-header .stage-glyph { color: currentColor; }
.garden-note-header .stage-label {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-ink-soft);
}

.garden-note-header .tended,
.garden-note-header .started,
.garden-note-header .finished,
.garden-note-header .ref-type { color: var(--color-ink-soft); }
.garden-note-header .ref-type {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-ink-fade);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.1rem 0.55rem;
  border-radius: 999px;
  border: 1px solid currentColor;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: var(--text-xs);
}
.status-pill svg { width: 0.7em; height: 0.7em; }
.status-pill.status-reading   { color: var(--color-steel); }
.status-pill.status-finished  { color: var(--color-green); }
.status-pill.status-abandoned { color: var(--color-burgundy); }
.status-pill.status-queued    { color: var(--color-warn, #a05a1a); }

.spoiler-warning {
  color: var(--color-burgundy);
  font-weight: 600;
}
```

Note: `--color-warn` is referenced as a fallback. Add it to the token blocks too — in the `:root {` block (light mode) add:
```css
  --color-warn:     #a05a1a;
```
And in both dark blocks (`:root[data-theme="dark"]` and `@media (prefers-color-scheme: dark) :root:not([data-theme])`) add:
```css
  --color-warn:     #d4a060;
```

- [ ] **Step 3: Verify contrast still passes**

Run: `python3 tools/check-contrast.py`
Expected: pass.

- [ ] **Step 4: Build Hugo**

Run: `hugo --minify`
Expected: success.

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/garden/note-header.html assets/css/main.css
git commit -m "Add garden note-header partial and §20 (header strip + status pill)"
```

---

## Task 7: Spoiler shortcode runtime + spoiler CSS (§22)

**Files:**
- Modify: `layouts/shortcodes/spoiler.html` (currently a no-op `<span data-spoiler>` stub)
- Modify: `assets/css/main.css` — append §22

Replace the stub with a `<details>`-based click-to-reveal block. Native semantics, no JS, accessible by default.

- [ ] **Step 1: Replace `layouts/shortcodes/spoiler.html`**

Current content is a single line: `<span data-spoiler>{{ .Inner | markdownify }}</span>`. Replace with:

```go-html-template
{{- /* spoiler shortcode (replaces the no-op stub from the essays slice).
       Authoring form:
         {{< spoiler summary="chapter ending" level="light|heavy" >}}…{{< /spoiler >}}
       Click-to-reveal via native <details>. No JS. Reduced-motion respected
       by default (no transitions defined).
*/ -}}
{{- $level := .Get "level" | default "light" -}}
{{- $summary := .Get "summary" | default "spoiler" -}}
<details class="spoiler" data-spoiler-level="{{ $level }}">
  <summary>{{ $summary }}</summary>
  <div class="spoiler-body">{{ .Inner | markdownify }}</div>
</details>
```

- [ ] **Step 2: Append §22 to `assets/css/main.css`**

After §21 (note tile), append:

```css

/* ------------------------------------------------------------------
 * 22. Spoiler runtime (details-based)
 * ------------------------------------------------------------------ */
details.spoiler {
  margin: 0.75rem 0;
  padding: 0.5rem 0.85rem;
  border: 1px solid var(--color-rule);
  border-left: 3px solid var(--color-burgundy);
  border-radius: 4px;
  background: var(--color-tile);
}
details.spoiler[open] { padding-bottom: 0.7rem; }
details.spoiler > summary {
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-burgundy);
  list-style: none; /* hide default disclosure triangle */
}
details.spoiler > summary::-webkit-details-marker { display: none; }
details.spoiler > summary::before { content: "▸ "; margin-right: 0.1rem; }
details.spoiler[open] > summary::before { content: "▾ "; }
details.spoiler > summary:focus-visible {
  outline: 2px solid var(--color-burgundy);
  outline-offset: 2px;
  border-radius: 2px;
}
details.spoiler .spoiler-body {
  margin-top: 0.4rem;
  font-family: var(--font-body);
  font-size: var(--text-base);
  color: var(--color-ink);
}
details.spoiler[data-spoiler-level="heavy"] { border-left-width: 5px; }
```

- [ ] **Step 3: Build Hugo + check contrast**

Run: `hugo --minify && python3 tools/check-contrast.py`
Expected: both succeed.

- [ ] **Step 4: Commit**

```bash
git add layouts/shortcodes/spoiler.html assets/css/main.css
git commit -m "Replace spoiler shortcode stub with <details> runtime + §22 CSS"
```

---

## Task 8: Garden single template (`layouts/garden/single.html`)

**Files:**
- Create: `layouts/garden/single.html`

Single template for all flavors. Calls `note-header` partial, then title, then optional creator/media-meta, then body, then optional topic-map tile section.

- [ ] **Step 1: Create the template**

```go-html-template
{{ define "main" }}
<article class="reading-column garden-note">
  <p class="crumb"><a href="{{ "/garden/" | relURL }}">Garden</a> ›</p>

  {{ partial "garden/note-header.html" . }}

  <h1 class="garden-note-title">{{ .Title }}</h1>

  {{- $mediaType := .Params.media_type -}}
  {{- $isMedia := and $mediaType (in (slice "book" "album" "track" "game" "film" "series") $mediaType) -}}
  {{- $isReference := and $mediaType (in (slice "paper" "video" "article" "talk") $mediaType) -}}

  {{- if or $isMedia $isReference -}}
    {{- with .Params.creator -}}
    <p class="garden-creator">by {{ . }}{{ with $.Params.year }} · {{ . }}{{ end }}</p>
    {{- end -}}
    <div class="garden-media-meta">
      {{- with .Params.original_url -}}
      <a class="original-link" href="{{ . }}" rel="noopener noreferrer">→ original</a>
      {{- end -}}
      {{- with $mediaType -}}
      <span class="media-type-meta">{{ . }}</span>
      {{- end -}}
    </div>
  {{- end -}}

  <div class="garden-note-body essay-body">
    {{ .Content }}
  </div>

  {{- with .Params.topic_map -}}
  {{ partial "garden/topic-section.html" (dict
      "context" $
      "heading" "Notes in this topic"
      "framing" "Curated reading order, not chronological."
      "linkHeading" false
  ) }}
  {{- end -}}
</article>
{{ end }}
```

- [ ] **Step 2: Append note-page styles to §19 in `assets/css/main.css`**

After the `.garden-tiles { … }` block from Task 5, append:

```css

/* Garden single-note page elements */
.garden-note { max-width: 720px; }
.garden-note .crumb {
  font-family: var(--font-body);
  font-size: var(--text-xs);
  color: var(--color-ink-fade);
  margin: 0 0 0.5rem;
}
.garden-note .crumb a {
  color: var(--color-burgundy);
  text-decoration: none;
  border-bottom: 1px dotted currentColor;
}
.garden-note-title {
  font-family: var(--font-body);
  font-weight: 700;
  font-size: var(--text-2xl);
  line-height: 1.18;
  margin: 0.4rem 0 0.4rem;
  color: var(--color-ink);
}
.garden-creator {
  font-family: var(--font-body);
  font-style: italic;
  color: var(--color-ink-soft);
  font-size: var(--text-base);
  margin: 0 0 0.75rem;
}
.garden-media-meta {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  margin: 0 0 1.1rem;
}
.garden-media-meta a.original-link {
  color: var(--color-burgundy);
  text-decoration: none;
  border-bottom: 1px dotted currentColor;
}
.garden-media-meta .media-type-meta {
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-ink-fade);
}
.garden-note-body { margin-top: 0.75rem; }

/* Topic section nested inside a single note (not the index) */
.garden-note .garden-topic { margin-top: 2.5rem; padding-top: 1.25rem; border-top: 1px solid var(--color-rule); }
```

- [ ] **Step 3: Build + serve**

Run: `hugo --minify`
Expected: success. No garden notes exist yet, so no individual page renders, but the template parses.

Run `hugo server --buildDrafts` and visit `http://localhost:1313/garden/`. The existing `_index.md` should render with the (still-default) list template (no garden list.html yet).

- [ ] **Step 4: Commit**

```bash
git add layouts/garden/single.html assets/css/main.css
git commit -m "Add garden/single.html template and note-page CSS"
```

---

## Task 9: Shared filter-chips partial + JS module + CSS §16 generalization

**Files:**
- Create: `layouts/partials/filter-chips.html`
- Create: `assets/js/filter-chips.js`
- Modify: `assets/css/main.css` — generalize §16 to multi-dim chips (existing essay-specific selectors generalized to `.filter-chips` + `[data-dim]`)

Build the new shared partial and JS module first; then later tasks migrate essays + introduce the garden index. The partial supports both `mode: single` (transitional, used by essays during the migration window — Task 10) and `mode: and` (default for garden, post-refactor essays).

- [ ] **Step 1: Create `layouts/partials/filter-chips.html`**

```go-html-template
{{- /* Shared multi-dimension filter chip strip.
   Inputs:
     dimensions  — slice of dicts: { key, label, values }
                   key:    machine name (used as data-dim, e.g. "tag")
                   label:  display label (e.g. "Tag")
                   values: slice of strings (the chip values)
     mode        — "single" (legacy, single chip active across all dims)
                 — "and"    (default, per-dim active state, AND combined)
   Suppression rule: dimensions with len(values) < 2 are not rendered.
*/ -}}
{{- $mode := .mode | default "and" -}}
{{- $dims := .dimensions | default slice -}}
{{- $renderable := slice -}}
{{- range $dims -}}
  {{- if ge (len .values) 2 -}}
    {{- $renderable = $renderable | append . -}}
  {{- end -}}
{{- end -}}
{{- if $renderable -}}
<nav class="filter-chips" data-filter-mode="{{ $mode }}" aria-label="Filters">
  {{- range $renderable -}}
    {{- $key := .key -}}
    <div class="filter-dimension" data-dim="{{ $key }}">
      <span class="filter-label">{{ .label }}</span>
      <button type="button" class="filter-chip is-active" data-dim="{{ $key }}" data-key="all">All</button>
      {{- range .values -}}
        <button type="button" class="filter-chip" data-dim="{{ $key }}" data-key="{{ . }}">{{ . }}</button>
      {{- end -}}
    </div>
  {{- end -}}
</nav>
{{- end -}}
```

- [ ] **Step 2: Create `assets/js/filter-chips.js`**

```javascript
// Multi-dimension filter chip strip.
// Used by both /essays/ and /garden/ (and any future filtered list).
//
// HTML contract (rendered by partials/filter-chips.html):
//   <nav class="filter-chips" data-filter-mode="and|single">
//     <div class="filter-dimension" data-dim="tag">
//       <button class="filter-chip is-active" data-dim="tag" data-key="all">All</button>
//       <button class="filter-chip" data-dim="tag" data-key="memory">memory</button>
//       …
//     </div>
//   </nav>
//
// Cards are any element matching `[data-dim-target]` (each grid passes its
// own selector). Each card declares its values as data-{dim} attributes.
// data-tags is space-separated; other dims are single-valued.

export function setupFilterChips({
  containerSelector = '.filter-chips',
  cardSelector,
  sectionSelector,
  emptyStateSelector,
} = {}) {
  const container = document.querySelector(containerSelector);
  if (!container) return;
  if (!cardSelector) {
    console.warn('setupFilterChips: cardSelector is required');
    return;
  }

  const mode = container.getAttribute('data-filter-mode') || 'and';
  // state: { [dim]: activeKey }, all initialized to "all"
  const state = {};
  container.querySelectorAll('.filter-dimension').forEach((dimEl) => {
    const dim = dimEl.getAttribute('data-dim');
    if (dim) state[dim] = 'all';
  });

  function cardMatches(card) {
    if (mode === 'single') {
      // Single-active legacy: at most one dim has a non-"all" active key.
      // A card matches iff that single active dim's value is satisfied.
      let activeDim = null;
      let activeKey = 'all';
      for (const dim in state) {
        if (state[dim] !== 'all') { activeDim = dim; activeKey = state[dim]; break; }
      }
      if (!activeDim) return true;
      return cardHasValue(card, activeDim, activeKey);
    }
    // and mode: every non-"all" dim must match
    for (const dim in state) {
      if (state[dim] === 'all') continue;
      if (!cardHasValue(card, dim, state[dim])) return false;
    }
    return true;
  }

  function cardHasValue(card, dim, key) {
    const attr = card.getAttribute(`data-${dim === 'tag' ? 'tags' : dim}`) || '';
    if (dim === 'tag' || dim === 'tags') {
      return attr.split(/\s+/).filter(Boolean).includes(key);
    }
    return attr === key;
  }

  function applyFilters() {
    const cards = document.querySelectorAll(cardSelector);
    let visibleCount = 0;
    cards.forEach((card) => {
      const visible = cardMatches(card);
      if (visible) {
        card.removeAttribute('hidden');
        visibleCount += 1;
      } else {
        card.setAttribute('hidden', '');
      }
    });

    if (sectionSelector) {
      document.querySelectorAll(sectionSelector).forEach((section) => {
        const anyVisible = section.querySelector(`${cardSelector}:not([hidden])`);
        if (anyVisible) {
          section.removeAttribute('hidden');
        } else {
          section.setAttribute('hidden', '');
        }
      });
    }

    if (emptyStateSelector) {
      const empty = document.querySelector(emptyStateSelector);
      if (empty) {
        if (visibleCount === 0) {
          empty.removeAttribute('hidden');
        } else {
          empty.setAttribute('hidden', '');
        }
      }
    }
  }

  container.querySelectorAll('.filter-chip').forEach((chip) => {
    chip.addEventListener('click', (e) => {
      e.preventDefault();
      const dim = chip.getAttribute('data-dim');
      const key = chip.getAttribute('data-key') || 'all';
      if (!dim) return;

      if (mode === 'single') {
        // Clear every dim back to "all" first
        for (const d in state) state[d] = 'all';
        state[dim] = key;
      } else {
        state[dim] = key;
      }

      // Reflect active state on chip elements
      container.querySelectorAll('.filter-dimension').forEach((dimEl) => {
        const dDim = dimEl.getAttribute('data-dim');
        if (!dDim) return;
        dimEl.querySelectorAll('.filter-chip').forEach((c) => {
          const cKey = c.getAttribute('data-key');
          c.classList.toggle('is-active', cKey === state[dDim]);
        });
      });

      applyFilters();
    });
  });

  applyFilters();
}
```

- [ ] **Step 3: Generalize §16 in `assets/css/main.css`**

Replace the existing `/* 16. Filter strip (essays index) */` block with:

```css
/* ------------------------------------------------------------------
 * 16. Filter chips (multi-dim, shared by essays + garden)
 * ------------------------------------------------------------------ */
.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  margin: 1rem 0 2rem;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
}
.filter-dimension {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
}
.filter-label {
  color: var(--color-ink-fade);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-right: 0.25rem;
}
.filter-chip {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  border: 1px solid var(--color-rule);
  border-radius: 999px;
  color: var(--color-ink-soft);
  background: transparent;
  text-decoration: none;
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
}
.filter-chip:hover { border-color: var(--color-burgundy); color: var(--color-burgundy); }
.filter-chip.is-active {
  background: var(--color-burgundy);
  color: var(--color-stone);
  border-color: var(--color-burgundy);
}
.filter-chip:focus-visible {
  outline: 2px solid var(--color-burgundy);
  outline-offset: 2px;
}

/* Legacy alias — old essay markup uses .filter-strip; keep it pointing at
 * the new selectors for one slice while migrating. Removed in follow-up. */
.filter-strip { /* deprecated; will be removed alongside .filter-strip markup in essays */ }
```

- [ ] **Step 4: Build + check contrast**

Run: `hugo --minify && python3 tools/check-contrast.py`
Expected: success. Essays page still works because the existing `.filter-strip` markup uses identical chip / dimension class names — those generalize cleanly. Old `essay.js#setupFilterChips` is still wired and still works.

In `hugo server`, visit `http://localhost:1313/essays/` and confirm chips still render and clicking one filters as before.

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/filter-chips.html assets/js/filter-chips.js assets/css/main.css
git commit -m "Add shared filter-chips partial + JS module; generalize §16 CSS"
```

---

## Task 10: Migrate essays to the shared filter-chips partial in AND mode

**Files:**
- Modify: `layouts/essays/list.html`
- Modify: `assets/js/essay.js` (delete the inline `setupFilterChips`, import the shared module)
- Modify: `assets/js/index.js`

After this task, `/essays/` uses the shared partial and AND-composing filter logic. Tag + series chip combination now narrows to intersection (was previously single-active).

- [ ] **Step 1: Replace the chip strip in `layouts/essays/list.html`**

In `layouts/essays/list.html`, replace the entire `<nav class="filter-strip" …>…</nav>` block (currently around lines 26–54) with:

```go-html-template
    {{ $dims := slice }}
    {{ if ge (len $tags) 2 }}
      {{ $dims = $dims | append (dict "key" "tag" "label" "Tag" "values" $tags) }}
    {{ end }}
    {{ if ge (len $seriesList) 2 }}
      {{ $dims = $dims | append (dict "key" "series" "label" "Series" "values" $seriesList) }}
    {{ end }}
    {{ if ge (len $years) 2 }}
      {{ $dims = $dims | append (dict "key" "year" "label" "Year" "values" $years) }}
    {{ end }}
    {{ partial "filter-chips.html" (dict "dimensions" $dims "mode" "and") }}
```

The surrounding loops that build `$tags`, `$seriesList`, `$years` (lines 11–24) stay untouched.

- [ ] **Step 2: Each essay card needs `data-tags`, `data-series`, `data-year`**

Read `layouts/partials/essay-card.html` and `layouts/partials/essay-card-featured.html`. Confirm both currently emit a `<li>` with `data-*` attributes. If they already include `data-tags`, `data-series`, `data-year`, no change needed. If any are missing, add them on the outer `<li>` element. The card's outer element must be selectable as a card (we'll use `.essay-card` as the selector in step 3).

(Inspection step — no code change unless an attribute is missing.)

- [ ] **Step 3: Replace `essay.js`'s inline filter logic with shared module**

Open `assets/js/essay.js`. Make three changes:

a) At the top of the file (after the existing comment header), add:
```javascript
import { setupFilterChips } from './filter-chips.js';
```

b) Delete the entire `function setupFilterChips() { … }` block (currently lines 76–126).

c) In `init()`, replace the existing `setupFilterChips();` call (which referenced the deleted local function) with:
```javascript
  setupFilterChips({
    containerSelector: '.filter-chips',
    cardSelector: '.essay-card',
  });
```

The final `init()` function should read:
```javascript
function init() {
  if (!document.querySelector('.essay-body') && !document.querySelector('.essay-grid')) return;
  setupSidenotePopups();
  setupTocSmoothScroll();
  setupCitationHook();
  setupFilterChips({
    containerSelector: '.filter-chips',
    cardSelector: '.essay-card',
  });
}
```

- [ ] **Step 4: Verify `assets/js/index.js` still imports correctly**

Open `assets/js/index.js`. It currently is:
```javascript
import './toggle-theme.js';
import './nav.js';
import './essay.js';
```

`filter-chips.js` is imported via `essay.js`, so no change needed yet. (Garden will add its own import in Task 12.)

- [ ] **Step 5: Build + visual confirm**

Run: `hugo --minify`
Expected: success.

Run `hugo server --buildDrafts`. Visit `http://localhost:1313/essays/`. Confirm:
- Chips render
- Clicking a tag chip filters cards
- Clicking a series chip while a tag is active narrows to intersection (this is the behavior change)
- Clicking "All" in any dimension resets that dim only

- [ ] **Step 6: Commit**

```bash
git add layouts/essays/list.html assets/js/essay.js
git commit -m "Migrate essays filter chips to shared module in AND mode"
```

---

## Task 11: Garden index template (`layouts/garden/list.html`)

**Files:**
- Create: `layouts/garden/list.html`
- Modify: `content/garden/_index.md` (replace the "(Coming soon.)" placeholder with a proper lede)
- Modify: `assets/css/main.css` — append §23 (empty-state placeholder)

Renders the garden index: lede + filter strip + topic-map sections (one per page with `topic_map:` set) + "Other notes" catch-all + empty-state element.

- [ ] **Step 1: Replace `content/garden/_index.md`**

Current content is "(Coming soon.)". Replace with:

```markdown
---
title: 'Garden'
description: 'A knowledge garden — concept and media notes, growing over time.'
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
```

- [ ] **Step 2: Create `layouts/garden/list.html`**

```go-html-template
{{ define "main" }}
<section class="garden-grid reading-column">
  <header class="garden-hero">
    <h1>{{ .Title }}</h1>
    {{ with .Content }}<div class="framing">{{ . }}</div>{{ end }}
  </header>

  {{- $pages := where .Site.RegularPages "Section" "garden" -}}
  {{- if eq (len $pages) 0 -}}
    <p class="garden-empty-static">No notes yet — check back soon.</p>
  {{- else -}}

    {{- /* ----- Build dimension value sets for the filter strip ----- */ -}}
    {{- $tags := slice -}}
    {{- $flavors := slice -}}
    {{- $stages := slice -}}
    {{- range $pages -}}
      {{- range .Params.tags -}}
        {{- if not (in $tags .) -}}{{- $tags = $tags | append . -}}{{- end -}}
      {{- end -}}
      {{- $mt := .Params.media_type -}}
      {{- $f := "concept" -}}
      {{- if $mt -}}
        {{- if in (slice "book" "album" "track" "game" "film" "series") $mt -}}
          {{- $f = "media" -}}
        {{- else -}}
          {{- $f = "reference" -}}
        {{- end -}}
      {{- end -}}
      {{- if not (in $flavors $f) -}}{{- $flavors = $flavors | append $f -}}{{- end -}}
      {{- $st := .Params.growth_stage | default "seedling" -}}
      {{- if not (in $stages $st) -}}{{- $stages = $stages | append $st -}}{{- end -}}
    {{- end -}}

    {{- $dims := slice -}}
    {{- if ge (len $tags) 2 -}}
      {{- $dims = $dims | append (dict "key" "tag" "label" "Tag" "values" $tags) -}}
    {{- end -}}
    {{- if ge (len $flavors) 2 -}}
      {{- $dims = $dims | append (dict "key" "flavor" "label" "Flavor" "values" $flavors) -}}
    {{- end -}}
    {{- if ge (len $stages) 2 -}}
      {{- $dims = $dims | append (dict "key" "stage" "label" "Stage" "values" $stages) -}}
    {{- end -}}
    {{ partial "filter-chips.html" (dict "dimensions" $dims "mode" "and") }}

    {{- /* ----- Pass 1: build the set of slugs referenced by any topic_map ----- */ -}}
    {{- $referenced := slice -}}
    {{- range $pages -}}
      {{- range .Params.topic_map -}}
        {{- if not (in $referenced .) -}}{{- $referenced = $referenced | append . -}}{{- end -}}
      {{- end -}}
    {{- end -}}

    {{- /* ----- Pass 2a: render topic-map sections in weight, then alphabetical ----- */ -}}
    {{- $topicMapPages := where $pages "Params.topic_map" "ne" nil -}}
    {{- range $topicMapPages.ByWeight -}}
      {{ partial "garden/topic-section.html" (dict "context" .) }}
    {{- end -}}

    {{- /* ----- Pass 2b: render "Other notes" — pages neither referenced nor topic-map owners ----- */ -}}
    {{- $others := slice -}}
    {{- range $pages -}}
      {{- $slug := path.Base .File.Dir -}}
      {{- $isOwner := .Params.topic_map -}}
      {{- $isReferenced := in $referenced $slug -}}
      {{- if and (not $isOwner) (not $isReferenced) -}}
        {{- $others = $others | append . -}}
      {{- end -}}
    {{- end -}}
    {{- if $others -}}
    <section class="garden-topic" data-garden-section="other">
      <h2 class="garden-topic-heading">Other notes</h2>
      <p class="garden-topic-framing">Notes not yet placed in a topic map.</p>
      <div class="garden-tiles">
        {{- range (sort $others "Params.last_modified" "desc") -}}
          {{ partial "garden/note-tile.html" (dict "page" .) }}
        {{- end -}}
      </div>
    </section>
    {{- end -}}

    {{- /* ----- Empty-state for filter combinations with zero matches ----- */ -}}
    <p class="garden-empty" hidden>No notes match these filters yet.</p>

  {{- end -}}
</section>
{{ end }}
```

- [ ] **Step 3: Append §23 (empty-state) to `assets/css/main.css`**

After §22, append:

```css

/* ------------------------------------------------------------------
 * 23. Garden empty-state placeholder
 * ------------------------------------------------------------------ */
.garden-empty,
.garden-empty-static {
  font-family: var(--font-body);
  font-style: italic;
  color: var(--color-ink-soft);
  padding: 2rem 1rem;
  text-align: center;
  border: 1px dashed var(--color-rule);
  border-radius: 6px;
  margin: 1.5rem 0;
}
.garden-hero { margin-bottom: 0.5rem; }
.garden-hero h1 {
  font-family: var(--font-body);
  font-weight: 700;
  font-size: var(--text-2xl);
  margin: 0 0 0.25rem;
}
.garden-hero .framing {
  font-family: var(--font-body);
  font-style: italic;
  color: var(--color-ink-soft);
  max-width: 60ch;
}
```

- [ ] **Step 4: Build + check contrast**

Run: `hugo --minify && python3 tools/check-contrast.py`
Expected: success.

- [ ] **Step 5: Visual check**

Run `hugo server --buildDrafts` and visit `http://localhost:1313/garden/`. Expected: the page renders the lede + an "All notes — check back soon" empty-state-static (no fixtures yet, so `len $pages == 0` branch).

- [ ] **Step 6: Commit**

```bash
git add layouts/garden/list.html content/garden/_index.md assets/css/main.css
git commit -m "Add garden/list.html with topic sections + Other notes + filter strip"
```

---

## Task 12: Garden JS entry + bundle wiring

**Files:**
- Create: `assets/js/garden.js`
- Modify: `assets/js/index.js`

`garden.js` is the page-level entry: it guards on garden markup being present, then calls the shared filter-chips module with garden-specific selectors.

- [ ] **Step 1: Create `assets/js/garden.js`**

```javascript
// Garden page-level enhancements.
// - Multi-dimension AND filter chips on /garden/
// (Spoilers are CSS+native <details>; citations deferred.)
import { setupFilterChips } from './filter-chips.js';

function init() {
  if (!document.querySelector('.garden-grid') && !document.querySelector('.garden-note')) return;
  if (document.querySelector('.garden-grid .filter-chips')) {
    setupFilterChips({
      containerSelector: '.garden-grid .filter-chips',
      cardSelector: '.garden-tile',
      sectionSelector: '.garden-grid [data-garden-section]',
      emptyStateSelector: '.garden-empty',
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
```

- [ ] **Step 2: Add `garden.js` to the JS bundle**

Update `assets/js/index.js` to:
```javascript
import './toggle-theme.js';
import './nav.js';
import './essay.js';
import './garden.js';
```

- [ ] **Step 3: Build**

Run: `hugo --minify`
Expected: success. JS bundle should re-fingerprint.

- [ ] **Step 4: Commit**

```bash
git add assets/js/garden.js assets/js/index.js
git commit -m "Wire garden.js into the JS bundle"
```

---

## Task 13: Garden RSS feed + header partial RSS conditional

**Files:**
- Create: `layouts/garden/rss.xml`
- Modify: `layouts/partials/header.html` (extend the existing essays-prefix RSS switch to handle garden too)

- [ ] **Step 1: Create `layouts/garden/rss.xml`**

```go-html-template
{{- $pctx := . -}}
{{- if .IsHome -}}{{ $pctx = .Site }}{{- end -}}
{{- $pages := slice -}}
{{- if or $.IsHome $.IsSection -}}{{ $pages = $pctx.RegularPages -}}{{- else -}}{{ $pages = $pctx.Pages -}}{{- end -}}
{{- $limit := .Site.Config.Services.RSS.Limit -}}
{{- if ge $limit 1 -}}{{ $pages = $pages | first $limit -}}{{- end -}}
{{- printf "<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>" | safeHTML }}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Garden — {{ .Site.Author.name | default "Abdelrahman Madkour" }}</title>
    <link>{{ .Permalink }}</link>
    <description>{{ with .Description }}{{ . }}{{ else }}Concept and media notes from a3madkour's garden.{{ end }}</description>
    <generator>Hugo</generator>
    <language>{{ .Site.Language.Lang }}</language>
    <lastBuildDate>{{ now.Format "Mon, 02 Jan 2006 15:04:05 -0700" | safeHTML }}</lastBuildDate>
    <atom:link href="{{ .Permalink }}index.xml" rel="self" type="application/rss+xml" />
    {{ range $pages }}
    {{- if not .Draft -}}
    <item>
      <title>{{ .Title }}</title>
      <link>{{ .Permalink }}</link>
      <pubDate>{{ ($.Params.last_modified | default .Date).Format "Mon, 02 Jan 2006 15:04:05 -0700" | safeHTML }}</pubDate>
      <guid>{{ .Permalink }}</guid>
      <description>{{ with .Params.summary }}{{ . | html }}{{ else }}{{ .Summary | plainify | html }}{{ end }}</description>
    </item>
    {{- end -}}
    {{ end }}
  </channel>
</rss>
```

- [ ] **Step 2: Update `layouts/partials/header.html` RSS switch**

Find:
```go-html-template
    {{- $rssHref := "/index.xml" -}}
    {{- $rssLabel := "Site RSS feed" -}}
    {{- if hasPrefix .RelPermalink "/essays/" -}}
      {{- $rssHref = "/essays/index.xml" -}}
      {{- $rssLabel = "Essays RSS feed" -}}
    {{- end -}}
```

Replace with:
```go-html-template
    {{- $rssHref := "/index.xml" -}}
    {{- $rssLabel := "Site RSS feed" -}}
    {{- if hasPrefix .RelPermalink "/essays/" -}}
      {{- $rssHref = "/essays/index.xml" -}}
      {{- $rssLabel = "Essays RSS feed" -}}
    {{- else if hasPrefix .RelPermalink "/garden/" -}}
      {{- $rssHref = "/garden/index.xml" -}}
      {{- $rssLabel = "Garden RSS feed" -}}
    {{- end -}}
```

- [ ] **Step 3: Build + visual check**

Run: `hugo --minify`
Expected: success. With no garden fixtures yet, `/garden/index.xml` will exist but contain no `<item>` elements.

In `hugo server`, visit `http://localhost:1313/garden/`. Confirm the RSS button in the top nav now points at `/garden/index.xml` (right-click → Copy Link Address).

- [ ] **Step 4: Commit**

```bash
git add layouts/garden/rss.xml layouts/partials/header.html
git commit -m "Add garden RSS feed and per-section RSS button switching"
```

---

## Task 14: Concept fixtures — 7 plain notes (#3–#9)

**Files (create all):**
- `content/garden/surprise-budget/index.md`
- `content/garden/salience-and-memory/index.md`
- `content/garden/emergence-vs-design/index.md`
- `content/garden/story-atoms/index.md`
- `content/garden/sleep-and-consolidation/index.md`
- `content/garden/recall-vs-replay/index.md`
- `content/garden/the-save-game/index.md`

Per spec §8 fixture table. Bodies are lorem ipsum; the few specific shortcode hooks called for in §8 are exercised exactly where the table specifies (sidenote in #3, figure in #6, body link from #3 → #4 to seed the future backlinks feature).

- [ ] **Step 1: Create `content/garden/surprise-budget/index.md` (#3 — exercises sidenote + body link to #4)**

```markdown
---
title: "Surprise budget"
draft: false
last_modified: 2026-04-25
growth_stage: budding
tags: ["narrative"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. {{< sidenote >}}Example sentence with a sidenote.{{< /sidenote >}} Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

This note links to [salience and memory](/garden/salience-and-memory/) — the back-target for future Phase 4 backlink rendering.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
```

- [ ] **Step 2: Create `content/garden/salience-and-memory/index.md` (#4 — back-target)**

```markdown
---
title: "Salience and memory"
draft: false
last_modified: 2026-05-01
growth_stage: seedling
tags: ["memory", "narrative"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet. Example sentence about salience as a narrative resource.

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium.
```

- [ ] **Step 3: Create `content/garden/emergence-vs-design/index.md` (#5)**

```markdown
---
title: "Emergence vs design"
draft: false
last_modified: 2026-04-05
growth_stage: evergreen
tags: ["narrative"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Example sentence one about the line between emergent and authored systems.

Example sentence two. Example sentence three.
```

- [ ] **Step 4: Create `content/garden/story-atoms/index.md` (#6 — exercises figure)**

```markdown
---
title: "Story atoms"
draft: false
last_modified: 2026-04-29
growth_stage: budding
tags: ["narrative"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet. Example sentence one.

{{< figure src="figure-placeholder.svg" caption="Filler caption — story atoms diagram" >}}

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam.
```

Also create the placeholder SVG in the page bundle: `content/garden/story-atoms/figure-placeholder.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 240" width="400" height="240">
  <rect x="0" y="0" width="400" height="240" fill="#fdfcf8" stroke="#d8d4cc" stroke-width="1"/>
  <circle cx="100" cy="120" r="32" fill="none" stroke="#1e4060" stroke-width="2"/>
  <circle cx="200" cy="120" r="32" fill="none" stroke="#1e4060" stroke-width="2"/>
  <circle cx="300" cy="120" r="32" fill="none" stroke="#1e4060" stroke-width="2"/>
  <line x1="132" y1="120" x2="168" y2="120" stroke="#6b1f2c" stroke-width="2"/>
  <line x1="232" y1="120" x2="268" y2="120" stroke="#6b1f2c" stroke-width="2"/>
</svg>
```

- [ ] **Step 5: Create `content/garden/sleep-and-consolidation/index.md` (#7)**

```markdown
---
title: "Sleep and consolidation"
draft: false
last_modified: 2026-05-04
growth_stage: seedling
tags: ["memory"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet. Example sentence about consolidation during sleep.

Example sentence two.
```

- [ ] **Step 6: Create `content/garden/recall-vs-replay/index.md` (#8)**

```markdown
---
title: "Recall vs replay"
draft: false
last_modified: 2026-04-19
growth_stage: budding
tags: ["memory", "play"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet. Example sentence one about replay as recall.

Sed ut perspiciatis. Example sentence two.
```

- [ ] **Step 7: Create `content/garden/the-save-game/index.md` (#9)**

```markdown
---
title: "The save game"
draft: false
last_modified: 2026-03-08
growth_stage: evergreen
tags: ["memory", "games"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet. Example sentence about the save game as a memory artifact.

Example sentence two.
```

- [ ] **Step 8: Run linter + build**

Run: `python3 tools/check_garden_fixtures.py`
Expected: `All garden fixtures pass linter.`

Run: `hugo --minify`
Expected: success.

- [ ] **Step 9: Visual check**

In `hugo server`, visit:
- `http://localhost:1313/garden/` — empty-state-static is gone; "Other notes" section now lists all 7 with stage glyphs (no topic-map sections yet because no `topic_map:` declared yet)
- `http://localhost:1313/garden/surprise-budget/` — concept-flavor header (stage + tended), title, body with sidenote, internal link to salience-and-memory

- [ ] **Step 10: Commit**

```bash
git add content/garden/surprise-budget content/garden/salience-and-memory content/garden/emergence-vs-design content/garden/story-atoms content/garden/sleep-and-consolidation content/garden/recall-vs-replay content/garden/the-save-game
git commit -m "Add 7 plain concept garden fixtures (#3-#9)"
```

---

## Task 15: Topic-map concept fixtures (#1 procedural-narrative, #2 memory-in-play)

**Files:**
- Create: `content/garden/procedural-narrative/index.md`
- Create: `content/garden/memory-in-play/index.md`

These fixtures declare `topic_map:` referencing the 7 plain concepts from Task 14. After this task, the index renders 2 topic-map sections (PN with 4 tiles + MIP with 3 tiles); "Other notes" is omitted entirely because every concept is now categorized and no media/reference fixtures exist yet. The 5 media + reference fixtures land in Tasks 16–17 and populate "Other notes" once they're added.

- [ ] **Step 1: Create `content/garden/procedural-narrative/index.md`**

```markdown
---
title: "Procedural narrative"
draft: false
last_modified: 2026-04-25
growth_stage: budding
weight: 1
tags: ["narrative", "games"]
summary: "How systems generate meaning when a player walks through them."
topic_map: ["surprise-budget", "salience-and-memory", "emergence-vs-design", "story-atoms"]
---

How systems generate meaning when a player walks through them. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Example sentence with a [linked note](/garden/salience-and-memory/) inline.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
```

- [ ] **Step 2: Create `content/garden/memory-in-play/index.md`**

```markdown
---
title: "Memory in play"
draft: false
last_modified: 2026-05-05
growth_stage: budding
weight: 2
tags: ["memory", "play"]
summary: "What survives a session, and what does the player rebuild from scratch."
topic_map: ["sleep-and-consolidation", "recall-vs-replay", "the-save-game"]
---

What survives a session, and what does the player rebuild from scratch. Lorem ipsum dolor sit amet, consectetur adipiscing elit.

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
```

- [ ] **Step 3: Run linter + build**

Run: `python3 tools/check_garden_fixtures.py && hugo --minify`
Expected: linter pass (`All garden fixtures pass linter.`); Hugo build success.

- [ ] **Step 4: Visual check**

In `hugo server`, visit:
- `http://localhost:1313/garden/` — now shows 2 topic-map sections in weight order (Procedural narrative first, Memory in play second), each with its tile grid; Other notes section is omitted (empty)
- `http://localhost:1313/garden/procedural-narrative/` — concept header, body, then "Notes in this topic" tile grid below body with 4 tiles in declared order
- `http://localhost:1313/garden/memory-in-play/` — same shape, 3 tiles

Click a tile from the topic-map note's grid → navigates to that note. Confirm the back link in the crumb works.

Filter chips: try clicking "memory" tag chip → only memory-tagged tiles visible; the "Procedural narrative" section should remain visible (it has 1 memory-tagged child: salience-and-memory). Click "narrative" tag instead → "Procedural narrative" has 4, "Memory in play" has 0 (collapses).

- [ ] **Step 5: Commit**

```bash
git add content/garden/procedural-narrative content/garden/memory-in-play
git commit -m "Add 2 topic-map concept garden fixtures (procedural-narrative, memory-in-play)"
```

---

## Task 16: Media fixtures (#10–#13)

**Files:**
- Create: `content/garden/invisible-cities/index.md` (book — reading + light spoiler)
- Create: `content/garden/koyaanisqatsi-soundtrack/index.md` (album — finished)
- Create: `content/garden/severance-s2/index.md` (series — abandoned + 3 heavy spoiler blocks)
- Create: `content/garden/outer-wilds/index.md` (game — queued)

After this task, all four status pills + all three spoiler-levels are exercised.

- [ ] **Step 1: Create `content/garden/invisible-cities/index.md`**

```markdown
---
title: "Invisible Cities"
draft: false
last_modified: 2026-05-01
growth_stage: budding
media_type: book
status: reading
creator: "Italo Calvino"
year: 1972
started: 2025-12-15
spoiler_level: light
original_url: "https://example.invalid/invisible-cities"
roam_refs: "@calvino1972cities"
tags: ["reading", "calvino"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Example sentence about Calvino's nested-list structure.

{{< spoiler summary="chapter ending" level="light" >}}
Filler placeholder revealing how the framing device resolves at the end. (Hidden by default — click to expand.)
{{< /spoiler >}}

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium. Example sentence two.
```

- [ ] **Step 2: Create `content/garden/koyaanisqatsi-soundtrack/index.md`**

```markdown
---
title: "Koyaanisqatsi soundtrack"
draft: false
last_modified: 2026-02-12
growth_stage: evergreen
media_type: album
status: finished
creator: "Philip Glass"
year: 1983
finished: 2026-02-10
original_url: "https://example.invalid/koyaanisqatsi"
tags: ["listening", "glass"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet. Example sentence about minimalism and pacing.

Example sentence two. Example sentence three.
```

- [ ] **Step 3: Create `content/garden/severance-s2/index.md`** (3 heavy spoiler blocks)

```markdown
---
title: "Severance — Season 2"
draft: false
last_modified: 2026-04-15
growth_stage: budding
media_type: series
status: abandoned
creator: "Dan Erickson"
year: 2025
started: 2025-01-20
finished: 2026-03-30
spoiler_level: heavy
original_url: "https://example.invalid/severance"
tags: ["series", "mystery"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet. Example sentence one about the show's premise.

{{< spoiler summary="episode 1 ending" level="heavy" >}}
Filler placeholder for first heavy spoiler.
{{< /spoiler >}}

Example sentence two. Example sentence three.

{{< spoiler summary="midseason twist" level="heavy" >}}
Filler placeholder for second heavy spoiler.
{{< /spoiler >}}

Example sentence four.

{{< spoiler summary="finale" level="heavy" >}}
Filler placeholder for third heavy spoiler.
{{< /spoiler >}}

Example sentence five.
```

- [ ] **Step 4: Create `content/garden/outer-wilds/index.md`**

```markdown
---
title: "Outer Wilds"
draft: false
last_modified: 2026-05-06
growth_stage: seedling
media_type: game
status: queued
creator: "Mobius Digital"
year: 2019
original_url: "https://example.invalid/outer-wilds"
tags: ["playing", "games"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet. Example sentence about queued status.

Example sentence two.
```

- [ ] **Step 5: Run linter + build**

Run: `python3 tools/check_garden_fixtures.py && hugo --minify`
Expected: pass + build success.

- [ ] **Step 6: Visual check**

In `hugo server`, visit each media note and confirm:
- `/garden/invisible-cities/` — header strip shows: 🌱 Budding · tended Nd ago · ◉ Reading pill (steel) · started 15 Dec 2025 · ⚠ light spoilers. Body has one closed `<details>` block (click → reveals).
- `/garden/koyaanisqatsi-soundtrack/` — header: Evergreen · tended · ✓ Finished pill (green) · finished 10 Feb 2026. No spoiler warning, no spoiler blocks.
- `/garden/severance-s2/` — header: Budding · tended · ✕ Abandoned pill (burgundy) · started/finished · ⚠ heavy spoilers. Body has three `<details>` blocks.
- `/garden/outer-wilds/` — header: Seedling · tended · ↑ Queued pill (warn). No spoiler warning, no blocks.

Visit `/garden/` — confirm all 4 now appear in "Other notes" with the right stage tile colors.

- [ ] **Step 7: Commit**

```bash
git add content/garden/invisible-cities content/garden/koyaanisqatsi-soundtrack content/garden/severance-s2 content/garden/outer-wilds
git commit -m "Add 4 media garden fixtures covering all statuses + spoiler levels"
```

---

## Task 17: Reference fixture (#14)

**Files:**
- Create: `content/garden/nguyen-2020-games-as-art/index.md`

- [ ] **Step 1: Create the fixture**

```markdown
---
title: "Games as art: the aesthetic potential of digital games"
draft: false
last_modified: 2026-04-12
growth_stage: evergreen
media_type: paper
creator: "Nguyen, C. T."
year: 2020
original_url: "https://example.invalid/nguyen-2020"
roam_refs: "@nguyen2020games-as-art"
tags: ["games", "aesthetics"]
summary: "Lorem ipsum placeholder summary."
---

Lorem ipsum dolor sit amet. Example sentence one about the aesthetic potential of games.

Example sentence two. Example sentence three.
```

- [ ] **Step 2: Run linter + build**

Run: `python3 tools/check_garden_fixtures.py && hugo --minify`
Expected: linter pass + build success.

- [ ] **Step 3: Visual check**

In `hugo server`, visit:
- `/garden/nguyen-2020-games-as-art/` — header shows: 🌳 Evergreen · tended · PAPER label. Below title: italic creator line "by Nguyen, C. T. · 2020". Below: media-meta row with `→ original` link + "paper" type. No status pill, no started/finished, no spoiler-level — all forbidden on reference flavor.

Visit `/garden/` — "Other notes" now lists 5 tiles (4 media + 1 reference).

- [ ] **Step 4: Commit**

```bash
git add content/garden/nguyen-2020-games-as-art
git commit -m "Add reference fixture (nguyen-2020-games-as-art)"
```

---

## Task 18: Final manual walkthrough + CLAUDE.md update

**Files:**
- Modify: `CLAUDE.md` (update Project status section)

The implementation is functionally complete. This task does the full manual walkthrough from spec §7.2, then documents the slice in CLAUDE.md so future sessions have current context.

- [ ] **Step 1: Run all CI gates locally**

Run:
```bash
python3 tools/check-contrast.py && \
python3 tools/check_fixtures.py && \
python3 -m unittest tools/test_check_fixtures.py -v && \
python3 tools/check_garden_fixtures.py && \
python3 -m unittest tools/test_check_garden_fixtures.py -v && \
hugo --minify
```
Expected: every step succeeds.

- [ ] **Step 2: Filter chip walkthrough (per spec §7.2)**

Start `hugo server --buildDrafts`. Visit `http://localhost:1313/garden/` and verify:

- [ ] Click each tag chip in isolation — only matching tiles visible; sections without matches collapse
- [ ] Click `flavor: media` — only the 4 media tiles visible, "Procedural narrative" + "Memory in play" topic sections collapse, "Other notes" stays
- [ ] Click `stage: evergreen` while `flavor: all` — only 4 evergreen tiles visible (emergence-vs-design, the-save-game, koyaanisqatsi-soundtrack, nguyen-2020)
- [ ] Click `tag: memory` AND `stage: budding` — AND intersection: only `recall-vs-replay`
- [ ] Click `flavor: reference` AND `stage: seedling` — empty intersection: empty-state message visible, all sections collapsed
- [ ] Click "All" in any single dim — that dim resets but other active filters remain
- [ ] Click "All" in every dim — full grid restored

- [ ] **Step 3: Spoiler walkthrough**

- [ ] Visit `/garden/invisible-cities/` — click the spoiler block, content reveals; click again, hides; press Tab to focus the summary, Enter to toggle
- [ ] Visit `/garden/severance-s2/` — open and close all 3 blocks independently

- [ ] **Step 4: Theme walkthrough**

- [ ] On `/garden/`, cycle theme system → light → dark → system using the toggle. Confirm: stage glyph colours change appropriately (burgundy/steel/green tokens swap their light/dark variants), filter chips render in both modes, status pill colours legible in both
- [ ] Repeat on `/garden/procedural-narrative/`, `/garden/invisible-cities/`, `/garden/nguyen-2020-games-as-art/`

- [ ] **Step 5: Responsive walkthrough**

In Chromium devtools, set viewport to:
- [ ] 480px (phone) — filter chips wrap, tile grid collapses to 1 column, header strip wraps
- [ ] 768px (tablet) — tile grid is 2 columns, header strip stays mostly inline
- [ ] 1200px (desktop) — tile grid is 3–4 columns

- [ ] **Step 6: Keyboard + screen reader**

- [ ] Tab from the page header through the filter chips: every chip is reachable, focus ring visible, Enter activates
- [ ] Tab through tile grid: each tile is one Tab stop, follows visual order
- [ ] Open a spoiler with keyboard: Tab to summary, Enter — opens; Enter again — closes
- [ ] If VoiceOver / NVDA available: confirm chip dimension labels announced, stage glyph has aria-label of stage name (note: the partial uses `aria-hidden="true"` on the SVG; the text label `<span class="stage-label">Seedling</span>` is the accessible name)

- [ ] **Step 7: Essay regression check**

- [ ] Visit `http://localhost:1313/essays/` — chips render, clicking a tag chip filters as before
- [ ] Click a tag chip then a series chip — AND intersection now (was single-active before; this is the intentional behaviour change)
- [ ] Open an essay post — sidenotes, citation hooks, TOC, series nav still work

- [ ] **Step 8: RSS check**

- [ ] Visit `http://localhost:1313/garden/index.xml` directly — well-formed RSS XML, 14 items
- [ ] On any `/garden/...` page, the top-nav RSS button points at `/garden/index.xml`
- [ ] On any `/essays/...` page, the RSS button points at `/essays/index.xml`
- [ ] On `/`, points at `/index.xml`

- [ ] **Step 9: Update CLAUDE.md**

Open `CLAUDE.md`. Find the section that begins:

```
## Project status (2026-05-05)

**Phase 0+1 complete.** ...
**Phase 2 — essays slice complete.** ...
```

Replace the title `## Project status (2026-05-05)` with `## Project status (2026-05-07)` and add a new paragraph after the `**Phase 2 — essays slice complete.**` paragraph, before the `**Phase 2 — remaining slices (not started).**` paragraph:

```markdown
**Phase 2 — garden notes slice complete.** Single note template for concept/media/reference flavors with metadata-routed header strip (status pill + dates + spoiler-level + creator + "→ original"); `topic_map:` frontmatter facet (any concept note can declare an ordered slug list and renders a curated tile grid below the body — supersedes parent spec §4.9, no `/garden/topics/` URL); garden index with topic-map sections + "Other notes" catch-all + multi-dimension AND filter chips; hand-authored SVG growth-stage glyphs (seedling sprout / budding two-leaf / evergreen tree); native `<details>` spoiler runtime (replaces the no-op stub); per-section RSS feed; 14-fixture set covering every status / stage / spoiler-level. Filter chips refactored: shared `assets/js/filter-chips.js` module, both essays and garden now use AND-composition.
```

Also update the bullet list under `**Phase 2 — remaining slices (not started).**`: delete the line "Garden notes (single template + index + topic maps) — Phase 4 adds the graph view + stacked-column retrieval." (since the slice now exists). Phase 4 still adds graph + stacked columns; that text moves up into a new bullet under the appropriate phase if needed (it's already covered in the existing CLAUDE.md "Deferred features still in plan" table).

Also update the `### CSS pipeline` section's listing of CSS sections — append `, 19 garden index, 20 note header + status pill, 21 note tile, 22 spoiler runtime, 23 empty-state placeholder` to the list of numbered sections.

Also update the `## Reference docs` section, append:
- `- **Phase 2 garden slice spec**: docs/superpowers/specs/2026-05-07-garden-notes-design.md`
- `- **Phase 2 garden slice plan**: docs/superpowers/plans/2026-05-07-garden-notes.md`

- [ ] **Step 10: Final commit**

```bash
git add CLAUDE.md
git commit -m "Update CLAUDE.md for Phase 2 garden slice"
```

- [ ] **Step 11: Push (only when all steps verified)**

```bash
git push origin master
```

---

## Self-review checklist

When this plan is executed, the following spec requirements should all be covered:

- [x] §1.1 Garden note page (Tasks 8, 11)
- [x] §1.2 `topic_map:` facet (Tasks 5, 8, 11; fixture #1, #2)
- [x] §1.3 Garden index with topic + Other sections (Task 11)
- [x] §1.4 Multi-dimension AND filter chips (Tasks 9, 11, 12)
- [x] §1.5 Hand-authored SVG glyphs (Task 3)
- [x] §1.6 Spoiler `<details>` runtime (Task 7; fixtures #10, #12)
- [x] §1.7 Per-section RSS at /garden/index.xml (Task 13)
- [x] §1.8 Essays migrated to shared filter chips in AND mode (Task 10)
- [x] §1.9 14-note fixture set + linter (Tasks 1, 14, 15, 16, 17)
- [x] §1.10 CSS sections 19–23 + §16 generalization (Tasks 3, 4, 5, 6, 7, 9, 11)
- [x] §3.1 File inventory (every file appears in some task)
- [x] §4.3 Status pill: 4 shapes for CB-safety (Task 6)
- [x] §5.1 Frontmatter contract (Task 1 linter; Tasks 14–17 exercise it)
- [x] §5.3 Garden index aggregation (two-pass) (Task 11)
- [x] §6.1 Build-time linter failures (Task 1 tests cover each)
- [x] §7.1 CI gates wired (Task 2)
- [x] §7.2 Manual walkthrough (Task 18)
- [x] §7.3 Essay regression check (Task 18 step 7)
- [x] §8 14-fixture coverage matrix (Tasks 14–17)

*End of plan.*
