# Library section — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase-7 Library section: a `/library/` umbrella plus four list pages (`reading`, `listening`, `playing`, `watching`), all data-driven from fixture-shaped `data/*.yaml` files that the future elisp pipeline will round-trip.

**Architecture:** Mirror the works-section pattern — per-section content tree, per-section layouts dispatched via `cascade.type`, shared partials under `partials/library/`, two new linter pairs, one new ~5 KB JS entry guarded by `data-library-page`, one new CSS section `§37`.

**Tech Stack:** Hugo (extended), hand-rolled CSS, vanilla JS (esbuild via `js.Build`), Python stdlib for linters, hand-authored SVG.

**Spec:** `docs/superpowers/specs/2026-05-12-library-section-design.md`

---

## File map

**Created (new):**

- `assets/images/icons/library/book.svg`
- `assets/images/icons/library/clapper.svg`
- `assets/js/entry-library.js`
- `content/library/_index.md`
- `content/library/reading/_index.md`
- `content/library/listening/_index.md`
- `content/library/playing/_index.md`
- `content/library/watching/_index.md`
- `data/reading.yaml`
- `data/listening.yaml`
- `data/playing.yaml`
- `data/watching.yaml`
- `layouts/library/list.html`
- `layouts/library/reading/list.html`
- `layouts/library/listening/list.html`
- `layouts/library/playing/list.html`
- `layouts/library/watching/list.html`
- `layouts/partials/library/umbrella-card.html`
- `layouts/partials/library/currently-active.html`
- `layouts/partials/library/year-section.html`
- `layouts/partials/library/row.html`
- `layouts/partials/library/status-badge.html`
- `layouts/partials/library/type-glyph.html`
- `tools/check_library_fixtures.py`
- `tools/test_check_library_fixtures.py`
- `tools/check_library_links.py`
- `tools/test_check_library_links.py`

**Modified:**

- `assets/css/main.css` — add `--color-violet` to all three palette blocks (light, explicit-dark, system-dark); append CSS section `§37 Library` at end of file.
- `data/filter-chips.yaml` — add `library-reading`, `library-listening`, `library-playing`, `library-watching` sections.
- `layouts/partials/header.html` — insert `Library` between `Works` and `About` in the nav slice.
- `layouts/partials/scripts.html` — append a library-section predicate that loads `entry-library.js` on `.Section == "library"` and `.Kind != "section"` for the umbrella (umbrella has no chips, no rows).
- `.github/workflows/hugo.yaml` — append 4 new CI steps (2 linters + 2 sibling tests) before the Hugo build.
- `CLAUDE.md` — refresh project status + reference docs after merge.

---

## Phase A — foundation (token, glyphs, parser, linters, fixtures)

### Task A1: Add `--color-violet` token to all three palette blocks

**Files:**
- Modify: `assets/css/main.css:17-44` (light `:root`)
- Modify: `assets/css/main.css:47-58` (explicit dark)
- Modify: `assets/css/main.css:61-74` (system dark in `@media (prefers-color-scheme: dark)`)

- [ ] **Step 1: Add `--color-violet` to light `:root`**

After the existing `--color-warn:     #a05a1a;` line:

```css
  --color-violet:   #5d4a8a;
```

- [ ] **Step 2: Add `--color-violet` to explicit `:root[data-theme="dark"]`**

After the dark `--color-warn:     #d4a060;` line:

```css
  --color-violet:   #b8a6e0;
```

- [ ] **Step 3: Add `--color-violet` to `@media (prefers-color-scheme: dark)` block**

Same value as step 2 — duplicate to keep system-dark and explicit-dark in sync (per CLAUDE.md `--color-burgundy` pattern):

```css
    --color-violet:   #b8a6e0;
```

- [ ] **Step 4: Verify contrast pass still green**

Run: `python3 tools/check-contrast.py`
Expected: `OK — all pairings pass.` (Violet is glyph-block-only, white-on-violet, not in the audited pairings; the existing 4 pairings keep passing.)

- [ ] **Step 5: Commit**

```bash
git checkout -b slice/library-section
git add assets/css/main.css
git commit -m "css: add --color-violet token (glyph-block tint for /library/watching/)"
```

---

### Task A2: Author hand-drawn `book.svg` glyph

**Files:**
- Create: `assets/images/icons/library/book.svg`

- [ ] **Step 1: Create the icons/library/ directory**

Run: `mkdir -p assets/images/icons/library`
Expected: silent success.

- [ ] **Step 2: Write `book.svg`**

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M3 4.5 Q3 4 3.5 4 L11.5 4 Q12 4 12 4.5 L12 19.5 Q12 20 11.5 20 L3.5 20 Q3 20 3 19.5 Z"/>
  <path d="M12 4.5 Q12 4 12.5 4 L20.5 4 Q21 4 21 4.5 L21 19.5 Q21 20 20.5 20 L12.5 20 Q12 20 12 19.5 Z"/>
  <line x1="5" y1="8" x2="10" y2="8"/>
  <line x1="5" y1="11" x2="10" y2="11"/>
  <line x1="5" y1="14" x2="9" y2="14"/>
  <line x1="14" y1="8" x2="19" y2="8"/>
  <line x1="14" y1="11" x2="19" y2="11"/>
  <line x1="14" y1="14" x2="18" y2="14"/>
</svg>
```

Open book with two facing pages and three line marks per page. 24×24 viewbox matches existing glyphs (`assets/images/icons/glyph-game.svg`).

- [ ] **Step 3: Visual sanity via dev server**

Run dev server in a separate terminal: `hugo server --buildDrafts &`
Open: `http://localhost:1313/images/icons/library/book.svg` — confirm it renders as an open book.
Stop the dev server: `pkill -f "hugo server"`

(If you skip this step, the next dev-server check after templates will catch it.)

- [ ] **Step 4: Commit**

```bash
git add assets/images/icons/library/book.svg
git commit -m "svg: add book glyph for /library/reading/"
```

---

### Task A3: Author hand-drawn `clapper.svg` glyph

**Files:**
- Create: `assets/images/icons/library/clapper.svg`

- [ ] **Step 1: Write `clapper.svg`**

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <rect x="3" y="9.5" width="18" height="11" rx="0.5"/>
  <path d="M3 9.5 L5 5 L8 5 L6 9.5 Z" fill="currentColor"/>
  <path d="M8 9.5 L10 5 L13 5 L11 9.5 Z" fill="currentColor"/>
  <path d="M13 9.5 L15 5 L18 5 L16 9.5 Z" fill="currentColor"/>
  <path d="M18 9.5 L20 5 L21 5 Q21 5.5 21 6 L19.5 9.5 Z" fill="currentColor"/>
  <line x1="3" y1="9.5" x2="21" y2="9.5"/>
</svg>
```

Film clapper-board: lower rectangle (slate body) + 4 diagonal stripes on the upper hinged section. 24×24 viewbox.

- [ ] **Step 2: Commit**

```bash
git add assets/images/icons/library/clapper.svg
git commit -m "svg: add clapper glyph for /library/watching/"
```

---

### Task A4: TDD — write a YAML parser for library-shape data files

The library yaml has 4 indent levels (`items:`, `  - slug:`, `    field:`, `      nested-field:`). Existing `tools/check_fixtures.py:parse_frontmatter` parses 2-level mapping — it doesn't handle list-of-objects. We add a small library-specific parser inside `check_library_fixtures.py`. Stdlib only.

**Files:**
- Create: `tools/check_library_fixtures.py` (parser only at this stage)
- Create: `tools/test_check_library_fixtures.py` (parser tests at this stage)

- [ ] **Step 1: Write the failing parser test**

```python
"""Tests for check_library_fixtures.py — run with:
   python3 -m unittest tools/test_check_library_fixtures.py -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_library_fixtures as lint  # noqa: E402


YAML_VALID = """\
items:
  - slug: invisible-cities
    title: Invisible Cities
    creator: Italo Calvino
    year: 1972
    media_type: book
    status: reading
    started: 2025-12-15
    finished: null
    spoiler_level: light
    last_modified: 2026-04-22
    cite_key: calvino1972cities
    canonical_url: "https://example.com/invisible-cities"
    note_slug: invisible-cities
    preview: "Re-reading for the procedural narrative paper."
    tags: [fiction, italian, procedural-narrative]
    extras:
      progress_pct: 51
      progress_label: "p. 84 / 165"
  - slug: another-book
    title: Another Book
    creator: Author Two
    year: 2020
    media_type: book
    status: finished
    finished: 2026-02-10
    last_modified: 2026-02-11
    note_slug: null
    tags: []
"""


class ParserTests(unittest.TestCase):
    def test_parse_returns_two_items(self):
        items = lint.parse_library_yaml(YAML_VALID)
        self.assertEqual(len(items), 2)

    def test_parse_first_item_fields(self):
        items = lint.parse_library_yaml(YAML_VALID)
        first = items[0]
        self.assertEqual(first["slug"], "invisible-cities")
        self.assertEqual(first["title"], "Invisible Cities")
        self.assertEqual(first["year"], 1972)
        self.assertIs(first["finished"], None)
        self.assertEqual(first["tags"], ["fiction", "italian", "procedural-narrative"])
        self.assertEqual(first["extras"], {"progress_pct": 51, "progress_label": "p. 84 / 165"})

    def test_parse_second_item_empty_tags(self):
        items = lint.parse_library_yaml(YAML_VALID)
        second = items[1]
        self.assertEqual(second["tags"], [])
        self.assertIs(second["note_slug"], None)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test, confirm it fails (no module yet)**

Run: `python3 -m unittest tools/test_check_library_fixtures.py -v`
Expected: `ModuleNotFoundError: No module named 'check_library_fixtures'`

- [ ] **Step 3: Write the parser**

```python
#!/usr/bin/env python3
"""Library fixture frontmatter linter.

Validates `data/{reading,listening,playing,watching}.yaml` shape per
docs/superpowers/specs/2026-05-12-library-section-design.md §3.

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_scalar  # noqa: E402


ITEM_START_RE = re.compile(r"^  - ([a-zA-Z_]+):\s*(.*)$")
ITEM_FIELD_RE = re.compile(r"^    ([a-zA-Z_]+):\s*(.*)$")
NESTED_HEADER_RE = re.compile(r"^    ([a-zA-Z_]+):\s*$")
NESTED_FIELD_RE = re.compile(r"^      ([a-zA-Z_]+):\s*(.*)$")


def parse_library_yaml(text: str) -> list[dict[str, object]]:
    """Parse a library data yaml file into a list of item dicts.

    Format:
        items:
          - slug: foo
            title: Bar
            tags: [a, b]
            extras:
              progress_pct: 50

    `null`, ints, floats, bools, [a, b] inline arrays handled via parse_scalar.
    """
    items: list[dict[str, object]] = []
    in_items = False
    current: dict[str, object] | None = None
    nested_key: str | None = None
    nested: dict[str, object] | None = None

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw.startswith("items:"):
            in_items = True
            continue
        if not in_items:
            continue

        m = ITEM_START_RE.match(raw)
        if m:
            if current is not None:
                if nested_key is not None and nested is not None:
                    current[nested_key] = nested
                items.append(current)
            current = {}
            nested_key = None
            nested = None
            field, value = m.group(1), m.group(2).strip()
            current[field] = parse_scalar(value)
            continue

        m_nested_hdr = NESTED_HEADER_RE.match(raw)
        if m_nested_hdr and current is not None:
            if nested_key is not None and nested is not None:
                current[nested_key] = nested
            nested_key = m_nested_hdr.group(1)
            nested = {}
            continue

        m_nested = NESTED_FIELD_RE.match(raw)
        if m_nested and nested is not None:
            field, value = m_nested.group(1), m_nested.group(2).strip()
            nested[field] = parse_scalar(value)
            continue

        m_field = ITEM_FIELD_RE.match(raw)
        if m_field and current is not None:
            if nested_key is not None and nested is not None:
                current[nested_key] = nested
                nested_key = None
                nested = None
            field, value = m_field.group(1), m_field.group(2).strip()
            current[field] = parse_scalar(value)
            continue

    if current is not None:
        if nested_key is not None and nested is not None:
            current[nested_key] = nested
        items.append(current)

    return items


def main() -> int:
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test, confirm it passes**

Run: `python3 -m unittest tools/test_check_library_fixtures.py -v`
Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/check_library_fixtures.py tools/test_check_library_fixtures.py
git commit -m "tools: library yaml parser (stdlib, list-of-objects shape)"
```

---

### Task A5: TDD — `check_library_fixtures.py` validator

**Files:**
- Modify: `tools/check_library_fixtures.py` (append validation logic)
- Modify: `tools/test_check_library_fixtures.py` (append validator tests)

- [ ] **Step 1: Write failing validator tests**

Append to `tools/test_check_library_fixtures.py`:

```python
class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def _run(self, file_name: str, text: str) -> list[str]:
        return lint.lint_yaml_file(file_name, text)

    def test_valid_reading_passes(self):
        text = """\
items:
  - slug: invisible-cities
    title: Invisible Cities
    creator: Italo Calvino
    year: 1972
    media_type: book
    status: reading
    started: 2025-12-15
    last_modified: 2026-04-22
    tags: [fiction]
"""
        self.assertEqual(self._run("reading.yaml", text), [])

    def test_listening_rejects_book_media_type(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: finished
    finished: 2026-02-10
    last_modified: 2026-02-11
    tags: []
"""
        errs = self._run("listening.yaml", text)
        self.assertTrue(any("media_type='book' not allowed" in e for e in errs), errs)

    def test_playing_rejects_unknown_status(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: game
    status: bogus
    last_modified: 2026-02-11
    tags: []
"""
        errs = self._run("playing.yaml", text)
        self.assertTrue(any("status='bogus'" in e for e in errs), errs)

    def test_finished_status_requires_finished_date(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: finished
    last_modified: 2026-02-11
    tags: []
"""
        errs = self._run("reading.yaml", text)
        self.assertTrue(any("finished date required" in e for e in errs), errs)

    def test_progress_pct_out_of_range_rejected(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: reading
    started: 2025-12-15
    last_modified: 2026-02-11
    tags: []
    extras:
      progress_pct: 150
"""
        errs = self._run("reading.yaml", text)
        self.assertTrue(any("progress_pct" in e and "0..100" in e for e in errs), errs)

    def test_unknown_extras_key_rejected(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: reading
    started: 2025-12-15
    last_modified: 2026-02-11
    tags: []
    extras:
      bogus_key: 1
"""
        errs = self._run("reading.yaml", text)
        self.assertTrue(any("bogus_key" in e for e in errs), errs)

    def test_duplicate_slug_rejected(self):
        text = """\
items:
  - slug: dup
    title: A
    creator: X
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-02-11
    tags: []
  - slug: dup
    title: B
    creator: Y
    year: 2021
    media_type: book
    status: queued
    last_modified: 2026-02-11
    tags: []
"""
        errs = self._run("reading.yaml", text)
        self.assertTrue(any("duplicate slug" in e for e in errs), errs)

    def test_bad_date_format_rejected(self):
        text = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: queued
    last_modified: not-a-date
    tags: []
"""
        errs = self._run("reading.yaml", text)
        self.assertTrue(any("last_modified" in e and "YYYY-MM-DD" in e for e in errs), errs)
```

- [ ] **Step 2: Run validator tests, confirm they fail**

Run: `python3 -m unittest tools.test_check_library_fixtures.ValidatorTests -v`
Expected: 8 errors — `lint_yaml_file` does not exist.

- [ ] **Step 3: Implement validator in `tools/check_library_fixtures.py`**

Replace the `def main()` stub with the full validator. Insert before `def main()`:

```python
ALLOWED_MEDIA_TYPES = {
    "reading.yaml":   {"book"},
    "listening.yaml": {"album", "track"},
    "playing.yaml":   {"game"},
    "watching.yaml":  {"film", "series"},
}

ALLOWED_STATUSES = {
    "reading.yaml":   {"finished", "reading", "queued", "abandoned"},
    "listening.yaml": {"finished", "listening", "queued", "dropped"},
    "playing.yaml":   {"finished", "100pct", "playing", "queued", "dropped"},
    "watching.yaml":  {"finished", "watching", "queued", "dropped"},
}

ALLOWED_EXTRAS = {
    "book":   {"progress_pct", "progress_label"},
    "album":  set(),
    "track":  set(),
    "game":   {"hours_played", "platform"},
    "film":   {"runtime_min"},
    "series": {"episode_count", "current_episode", "current_season"},
}

REQUIRED_FIELDS = {"slug", "title", "creator", "year", "media_type", "status", "last_modified", "tags"}
ALLOWED_FIELDS = REQUIRED_FIELDS | {
    "started", "finished", "spoiler_level", "cite_key",
    "canonical_url", "note_slug", "preview", "extras",
}
SPOILER_LEVELS = {"none", "light", "heavy"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ACTIVE_STATUSES = {"reading", "listening", "playing", "watching"}


def _check_date(label: str, value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not DATE_RE.match(value):
        return f"{label}: not YYYY-MM-DD ('{value}')"
    return None


def lint_yaml_file(file_name: str, text: str) -> list[str]:
    errors: list[str] = []
    if file_name not in ALLOWED_MEDIA_TYPES:
        return [f"{file_name}: unknown library file"]

    media_allow = ALLOWED_MEDIA_TYPES[file_name]
    status_allow = ALLOWED_STATUSES[file_name]
    items = parse_library_yaml(text)

    if not items:
        return [f"{file_name}: no items parsed"]

    seen_slugs: set[str] = set()
    active_count = 0

    for idx, item in enumerate(items):
        prefix = f"{file_name}[{idx}]"

        # Required fields
        missing = REQUIRED_FIELDS - set(item.keys())
        for f in sorted(missing):
            errors.append(f"{prefix}: missing required field '{f}'")

        # Unknown fields
        unknown = set(item.keys()) - ALLOWED_FIELDS
        for f in sorted(unknown):
            errors.append(f"{prefix}: unknown field '{f}'")

        slug = item.get("slug")
        if isinstance(slug, str):
            if not SLUG_RE.match(slug):
                errors.append(f"{prefix}: slug '{slug}' not kebab-case")
            if slug in seen_slugs:
                errors.append(f"{prefix}: duplicate slug '{slug}'")
            seen_slugs.add(slug)

        year = item.get("year")
        if year is not None and not isinstance(year, int):
            errors.append(f"{prefix}: year must be int, got {type(year).__name__}")

        mt = item.get("media_type")
        if mt is not None and mt not in media_allow:
            errors.append(f"{prefix}: media_type='{mt}' not allowed in {file_name} (allowed: {sorted(media_allow)})")

        status = item.get("status")
        if status is not None and status not in status_allow:
            errors.append(f"{prefix}: status='{status}' not allowed in {file_name} (allowed: {sorted(status_allow)})")
        if status in ACTIVE_STATUSES:
            active_count += 1

        for date_field in ("started", "finished", "last_modified"):
            err = _check_date(f"{prefix}: {date_field}", item.get(date_field))
            if err:
                errors.append(err.replace("not YYYY-MM-DD", f"{date_field} not YYYY-MM-DD"))

        if status == "finished" and item.get("finished") in (None, ""):
            errors.append(f"{prefix}: finished date required when status='finished'")

        sl = item.get("spoiler_level")
        if sl is not None and sl not in SPOILER_LEVELS:
            errors.append(f"{prefix}: spoiler_level='{sl}' not in {sorted(SPOILER_LEVELS)}")

        url = item.get("canonical_url")
        if url is not None and not (isinstance(url, str) and url.startswith("https://")):
            errors.append(f"{prefix}: canonical_url must be https:// or null")

        tags = item.get("tags")
        if tags is None or not isinstance(tags, list):
            errors.append(f"{prefix}: tags must be a list (may be empty)")
        else:
            for t in tags:
                if not isinstance(t, str) or not SLUG_RE.match(t):
                    errors.append(f"{prefix}: tag '{t}' not slug-shaped")

        extras = item.get("extras")
        if extras is not None:
            if not isinstance(extras, dict):
                errors.append(f"{prefix}: extras must be a mapping")
            elif isinstance(mt, str):
                allowed = ALLOWED_EXTRAS.get(mt, set())
                for k, v in extras.items():
                    if k not in allowed:
                        errors.append(f"{prefix}: extras.{k} not allowed for media_type '{mt}'")
                if "progress_pct" in extras:
                    pct = extras["progress_pct"]
                    if not isinstance(pct, int) or not 0 <= pct <= 100:
                        errors.append(f"{prefix}: progress_pct must be int 0..100, got {pct}")
                if "current_episode" in extras and "episode_count" in extras:
                    ce = extras.get("current_episode")
                    ec = extras.get("episode_count")
                    if isinstance(ce, int) and isinstance(ec, int) and ce > ec:
                        errors.append(f"{prefix}: current_episode ({ce}) > episode_count ({ec})")

    if active_count > 3:
        errors.append(f"{file_name}: warning — {active_count} active items, expected ≤3 in currently-active highlight")

    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    data_dir = repo_root / "data"
    for fname in sorted(ALLOWED_MEDIA_TYPES.keys()):
        path = data_dir / fname
        if not path.exists():
            continue
        all_errs.extend(lint_yaml_file(fname, path.read_text()))
    return (1 if all_errs else 0), all_errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_library_fixtures: OK")
    return rc
```

- [ ] **Step 4: Run validator tests, confirm they pass**

Run: `python3 -m unittest tools.test_check_library_fixtures -v`
Expected: all 3 parser tests + 8 validator tests pass (11 total).

- [ ] **Step 5: Run the linter against the (still empty) data dir**

Run: `python3 tools/check_library_fixtures.py`
Expected: `check_library_fixtures: OK` (no yaml files yet, nothing to validate).

- [ ] **Step 6: Commit**

```bash
git add tools/check_library_fixtures.py tools/test_check_library_fixtures.py
git commit -m "tools: check_library_fixtures.py + 11 unit tests"
```

---

### Task A6: TDD — `check_library_links.py` cross-reference linter

**Files:**
- Create: `tools/check_library_links.py`
- Create: `tools/test_check_library_links.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for check_library_links.py — run with:
   python3 -m unittest tools/test_check_library_links.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_library_links as lint  # noqa: E402


GARDEN_NOTE = """\
---
title: "Test Note"
draft: false
last_modified: 2026-01-01
growth_stage: seedling
---

Body.
"""

CITATIONS_YAML = """\
citations:
  test-key:
    authors: ["Doe"]
    year: 2020
    title: "Test"
    venue: "Journal"
"""

LIB_VALID = """\
items:
  - slug: row-with-note
    title: A
    creator: X
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    note_slug: real-note
  - slug: row-with-citation
    title: B
    creator: Y
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    cite_key: test-key
  - slug: row-with-url
    title: C
    creator: Z
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    canonical_url: "https://example.com/c"
"""

LIB_BAD_NOTE = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    note_slug: nonexistent-note
"""

LIB_BAD_CITE = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    cite_key: missing-key
"""

LIB_BAD_URL = """\
items:
  - slug: x
    title: X
    creator: Y
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-01-01
    tags: []
    canonical_url: "http://insecure.example.com"
"""


class LinksLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "content" / "garden" / "real-note").mkdir(parents=True)
        (self.tmp / "content" / "garden" / "real-note" / "index.md").write_text(GARDEN_NOTE)
        (self.tmp / "data").mkdir()
        (self.tmp / "data" / "citations.yaml").write_text(CITATIONS_YAML)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, name: str, text: str):
        (self.tmp / "data" / name).write_text(text)

    def test_valid_links_pass(self):
        self._write("reading.yaml", LIB_VALID)
        rc, errs = lint.run(self.tmp)
        self.assertEqual(errs, [])
        self.assertEqual(rc, 0)

    def test_bad_note_slug_rejected(self):
        self._write("reading.yaml", LIB_BAD_NOTE)
        rc, errs = lint.run(self.tmp)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("nonexistent-note" in e for e in errs), errs)

    def test_missing_cite_key_rejected(self):
        self._write("reading.yaml", LIB_BAD_CITE)
        rc, errs = lint.run(self.tmp)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("missing-key" in e for e in errs), errs)

    def test_http_url_rejected(self):
        self._write("reading.yaml", LIB_BAD_URL)
        rc, errs = lint.run(self.tmp)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("canonical_url" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests, confirm they fail**

Run: `python3 -m unittest tools/test_check_library_links.py -v`
Expected: `ModuleNotFoundError: No module named 'check_library_links'`.

- [ ] **Step 3: Write the linker**

```python
#!/usr/bin/env python3
"""Library cross-reference linter.

Resolves cross-references on `data/{reading,listening,playing,watching}.yaml`:
  - note_slug → content/garden/<slug>/index.md (non-draft)
  - cite_key  → data/citations.yaml entry
  - canonical_url → must be HTTPS or null

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402
from check_citations import parse_citations_yaml  # noqa: E402
from check_library_fixtures import parse_library_yaml  # noqa: E402


LIBRARY_FILES = ["reading.yaml", "listening.yaml", "playing.yaml", "watching.yaml"]


def _garden_slugs(garden_dir: Path) -> set[str]:
    """Return slugs of non-draft garden notes."""
    out: set[str] = set()
    if not garden_dir.is_dir():
        return out
    for d in sorted(garden_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        md = d / "index.md"
        if not md.exists():
            continue
        fm = parse_frontmatter(md.read_text()) or {}
        if bool(fm.get("draft", False)):
            continue
        out.add(d.name)
    return out


def _citation_keys(citations_yaml: Path) -> set[str]:
    if not citations_yaml.exists():
        return set()
    return set(parse_citations_yaml(citations_yaml.read_text()).keys())


def lint_links(repo_root: Path) -> list[str]:
    errors: list[str] = []
    garden_dir = repo_root / "content" / "garden"
    citations = repo_root / "data" / "citations.yaml"
    data_dir = repo_root / "data"

    slugs = _garden_slugs(garden_dir)
    keys = _citation_keys(citations)

    for fname in LIBRARY_FILES:
        path = data_dir / fname
        if not path.exists():
            continue
        items = parse_library_yaml(path.read_text())
        for idx, item in enumerate(items):
            prefix = f"{fname}[{idx}]"
            ns = item.get("note_slug")
            if isinstance(ns, str) and ns and ns not in slugs:
                errors.append(f"{prefix}: note_slug '{ns}' does not resolve to a non-draft garden note")
            ck = item.get("cite_key")
            if isinstance(ck, str) and ck and ck not in keys:
                errors.append(f"{prefix}: cite_key '{ck}' missing from data/citations.yaml")
            url = item.get("canonical_url")
            if url is not None and not (isinstance(url, str) and url.startswith("https://")):
                errors.append(f"{prefix}: canonical_url must be https:// or null, got {url!r}")
    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    errs = lint_links(repo_root)
    return (1 if errs else 0), errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_library_links: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests, confirm they pass**

Run: `python3 -m unittest tools/test_check_library_links.py -v`
Expected: 4 tests pass.

- [ ] **Step 5: Run linker against the still-empty data dir**

Run: `python3 tools/check_library_links.py`
Expected: `check_library_links: OK`.

- [ ] **Step 6: Commit**

```bash
git add tools/check_library_links.py tools/test_check_library_links.py
git commit -m "tools: check_library_links.py + 4 unit tests"
```

---

### Task A7: Author `data/reading.yaml` fixture (~6 items)

**Files:**
- Create: `data/reading.yaml`

- [ ] **Step 1: Write the yaml**

```yaml
# Reading list — fixture seed for /library/reading/.
# Real data lands via the elisp pipeline (Phase 3); this round-trips the
# spec §10.4 schema. Filler is "Lorem Ipsum N" / "Author N" — never authored prose.
items:
  - slug: invisible-cities
    title: Invisible Cities
    creator: Italo Calvino
    year: 1972
    media_type: book
    status: reading
    started: 2025-12-15
    last_modified: 2026-04-22
    note_slug: invisible-cities
    canonical_url: "https://example.com/invisible-cities"
    preview: "Re-reading for the procedural narrative paper."
    tags: [fiction, italian, procedural-narrative]
    extras:
      progress_pct: 51
      progress_label: "p. 84 / 165"
  - slug: lorem-ipsum-ii
    title: Lorem Ipsum II
    creator: Author II
    year: 2024
    media_type: book
    status: reading
    started: 2026-04-02
    last_modified: 2026-05-01
    canonical_url: "https://example.com/lorem-ii"
    preview: "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    tags: [non-fiction, design]
    extras:
      progress_pct: 18
      progress_label: "p. 42 / 230"
  - slug: lorem-ipsum-iii
    title: Lorem Ipsum III
    creator: Author III
    year: 2019
    media_type: book
    status: finished
    started: 2026-01-15
    finished: 2026-02-10
    last_modified: 2026-02-11
    canonical_url: "https://example.com/lorem-iii"
    preview: "Lorem ipsum dolor sit amet."
    tags: [fiction, italian]
  - slug: lorem-ipsum-iv
    title: Lorem Ipsum IV
    creator: Author IV
    year: 2021
    media_type: book
    status: abandoned
    started: 2026-03-01
    finished: 2026-03-30
    last_modified: 2026-04-01
    canonical_url: "https://example.com/lorem-iv"
    preview: "Started but didn't click."
    tags: [non-fiction]
  - slug: lorem-ipsum-v
    title: Lorem Ipsum V
    creator: Author V
    year: 1995
    media_type: book
    status: finished
    started: 2025-09-01
    finished: 2025-11-04
    last_modified: 2025-11-05
    canonical_url: "https://example.com/lorem-v"
    preview: "Lorem ipsum dolor sit amet, consectetur."
    tags: [memoir, architecture]
  - slug: lorem-ipsum-vi
    title: Lorem Ipsum VI
    creator: Author VI
    year: 2023
    media_type: book
    status: queued
    last_modified: 2026-04-15
    tags: [fiction]
  - slug: lorem-ipsum-vii
    title: Lorem Ipsum VII
    creator: Author VII
    year: 2020
    media_type: book
    status: queued
    last_modified: 2026-03-20
    tags: [non-fiction, design]
```

- [ ] **Step 2: Run the linter, confirm no errors**

Run: `python3 tools/check_library_fixtures.py`
Expected: `check_library_fixtures: OK`

- [ ] **Step 3: Run the cross-link linter**

Run: `python3 tools/check_library_links.py`
Expected: `check_library_links: OK` (invisible-cities resolves; the other entries have no note_slug).

- [ ] **Step 4: Commit**

```bash
git add data/reading.yaml
git commit -m "fixtures: data/reading.yaml — 7 items exercising statuses + years + queue"
```

---

### Task A8: Author `data/listening.yaml` fixture

**Files:**
- Create: `data/listening.yaml`

- [ ] **Step 1: Write the yaml**

```yaml
# Listening list fixture. ≥1 track for format dim to render.
items:
  - slug: koyaanisqatsi-soundtrack
    title: Koyaanisqatsi
    creator: Philip Glass
    year: 1983
    media_type: album
    status: listening
    started: 2026-04-20
    last_modified: 2026-05-01
    note_slug: koyaanisqatsi-soundtrack
    canonical_url: "https://example.com/koyaanisqatsi"
    preview: "Re-listening after watching the film again."
    tags: [ambient, soundtrack]
  - slug: lorem-album-ii
    title: Lorem Album II
    creator: Artist II
    year: 2023
    media_type: album
    status: listening
    started: 2026-03-12
    last_modified: 2026-04-30
    canonical_url: "https://example.com/lorem-album-ii"
    preview: "Lorem ipsum dolor sit amet."
    tags: [ambient]
  - slug: lorem-album-iii
    title: Lorem Album III
    creator: Artist III
    year: 2021
    media_type: album
    status: finished
    started: 2026-01-05
    finished: 2026-02-28
    last_modified: 2026-03-01
    canonical_url: "https://example.com/lorem-album-iii"
    preview: "Lorem ipsum dolor sit amet."
    tags: [jazz, modal]
  - slug: lorem-track-iv
    title: Lorem Track IV
    creator: Artist IV
    year: 2025
    media_type: track
    status: finished
    finished: 2026-03-15
    last_modified: 2026-03-15
    canonical_url: "https://example.com/lorem-track-iv"
    preview: "One repeat-play single."
    tags: [pop]
  - slug: lorem-album-v
    title: Lorem Album V
    creator: Artist V
    year: 2018
    media_type: album
    status: dropped
    started: 2025-08-01
    finished: 2025-08-12
    last_modified: 2025-08-13
    canonical_url: "https://example.com/lorem-album-v"
    preview: "Lorem ipsum dolor sit amet."
    tags: [experimental]
  - slug: lorem-album-vi
    title: Lorem Album VI
    creator: Artist VI
    year: 2024
    media_type: album
    status: queued
    last_modified: 2026-05-02
    tags: [ambient]
```

- [ ] **Step 2: Linters pass**

Run: `python3 tools/check_library_fixtures.py && python3 tools/check_library_links.py`
Expected: both report OK.

- [ ] **Step 3: Commit**

```bash
git add data/listening.yaml
git commit -m "fixtures: data/listening.yaml — 6 items, includes 1 track for format dim"
```

---

### Task A9: Author `data/playing.yaml` fixture

**Files:**
- Create: `data/playing.yaml`

- [ ] **Step 1: Write the yaml**

```yaml
# Playing list fixture. Games only — films + series live on watching.yaml.
items:
  - slug: outer-wilds
    title: Outer Wilds
    creator: Mobius Digital
    year: 2019
    media_type: game
    status: playing
    started: 2026-04-10
    last_modified: 2026-05-01
    note_slug: outer-wilds
    canonical_url: "https://example.com/outer-wilds"
    spoiler_level: heavy
    preview: "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    tags: [puzzle, exploration]
    extras:
      hours_played: 22
      platform: PC
  - slug: lorem-game-ii
    title: Lorem Game II
    creator: Studio II
    year: 2022
    media_type: game
    status: finished
    started: 2025-08-01
    finished: 2025-09-12
    last_modified: 2025-09-13
    canonical_url: "https://example.com/lorem-game-ii"
    preview: "Lorem ipsum dolor sit amet."
    tags: [puzzle, indie]
    extras:
      hours_played: 8
      platform: PC
  - slug: lorem-game-iii
    title: Lorem Game III
    creator: Studio III
    year: 2021
    media_type: game
    status: 100pct
    started: 2025-06-10
    finished: 2025-07-02
    last_modified: 2025-07-03
    canonical_url: "https://example.com/lorem-game-iii"
    preview: "Lorem ipsum dolor sit amet."
    tags: [platformer, indie]
    extras:
      hours_played: 18
      platform: Switch
  - slug: lorem-game-iv
    title: Lorem Game IV
    creator: Studio IV
    year: 2024
    media_type: game
    status: dropped
    started: 2026-02-20
    finished: 2026-03-05
    last_modified: 2026-03-06
    canonical_url: "https://example.com/lorem-game-iv"
    preview: "Lorem ipsum dolor sit amet."
    tags: [rpg]
    extras:
      hours_played: 4
      platform: PS5
  - slug: lorem-game-v
    title: Lorem Game V
    creator: Studio V
    year: 2020
    media_type: game
    status: finished
    started: 2026-01-10
    finished: 2026-02-22
    last_modified: 2026-02-23
    canonical_url: "https://example.com/lorem-game-v"
    preview: "Lorem ipsum dolor sit amet."
    tags: [strategy]
    extras:
      hours_played: 30
      platform: PC
  - slug: lorem-game-vi
    title: Lorem Game VI
    creator: Studio VI
    year: 2025
    media_type: game
    status: queued
    last_modified: 2026-04-20
    tags: [adventure]
    extras:
      platform: Web
```

- [ ] **Step 2: Linters pass**

Run: `python3 tools/check_library_fixtures.py && python3 tools/check_library_links.py`
Expected: both OK.

- [ ] **Step 3: Commit**

```bash
git add data/playing.yaml
git commit -m "fixtures: data/playing.yaml — 6 games incl. 100pct + dropped status variety"
```

---

### Task A10: Author `data/watching.yaml` fixture

**Files:**
- Create: `data/watching.yaml`

- [ ] **Step 1: Write the yaml**

```yaml
# Watching list fixture. ≥1 film and ≥1 series for format dim to render.
items:
  - slug: lorem-series-i
    title: Lorem Series I
    creator: Network I
    year: 2025
    media_type: series
    status: watching
    started: 2026-05-01
    last_modified: 2026-05-10
    canonical_url: "https://example.com/lorem-series-i"
    spoiler_level: light
    preview: "Lorem ipsum dolor sit amet."
    tags: [drama]
    extras:
      episode_count: 8
      current_episode: 4
      current_season: 1
  - slug: severance-s2
    title: Severance S2
    creator: Apple TV+
    year: 2025
    media_type: series
    status: finished
    started: 2026-02-01
    finished: 2026-03-30
    last_modified: 2026-03-31
    note_slug: severance-s2
    canonical_url: "https://example.com/severance-s2"
    spoiler_level: light
    preview: "Lorem ipsum dolor sit amet."
    tags: [sci-fi, drama]
    extras:
      episode_count: 10
  - slug: lorem-film-iii
    title: Lorem Film III
    creator: Director III
    year: 2018
    media_type: film
    status: finished
    finished: 2026-01-08
    last_modified: 2026-01-09
    canonical_url: "https://example.com/lorem-film-iii"
    preview: "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    tags: [drama]
    extras:
      runtime_min: 124
  - slug: lorem-film-iv
    title: Lorem Film IV
    creator: Director IV
    year: 2022
    media_type: film
    status: finished
    finished: 2025-12-20
    last_modified: 2025-12-21
    canonical_url: "https://example.com/lorem-film-iv"
    preview: "Lorem ipsum dolor sit amet."
    tags: [documentary]
    extras:
      runtime_min: 96
  - slug: lorem-series-v
    title: Lorem Series V
    creator: Network V
    year: 2024
    media_type: series
    status: dropped
    started: 2025-11-01
    finished: 2025-11-15
    last_modified: 2025-11-16
    canonical_url: "https://example.com/lorem-series-v"
    preview: "Lorem ipsum dolor sit amet."
    tags: [horror]
    extras:
      episode_count: 6
      current_episode: 2
      current_season: 1
  - slug: lorem-film-vi
    title: Lorem Film VI
    creator: Director VI
    year: 2026
    media_type: film
    status: queued
    last_modified: 2026-05-02
    tags: [sci-fi]
```

- [ ] **Step 2: Linters pass**

Run: `python3 tools/check_library_fixtures.py && python3 tools/check_library_links.py`
Expected: both OK.

- [ ] **Step 3: Commit**

```bash
git add data/watching.yaml
git commit -m "fixtures: data/watching.yaml — 6 items, mix of films + series"
```

---

## Phase B — content + layouts

### Task B1: Author 5 `_index.md` content files

**Files:**
- Create: `content/library/_index.md`
- Create: `content/library/reading/_index.md`
- Create: `content/library/listening/_index.md`
- Create: `content/library/playing/_index.md`
- Create: `content/library/watching/_index.md`

- [ ] **Step 1: Create the directory tree**

Run: `mkdir -p content/library/{reading,listening,playing,watching}`
Expected: silent success.

- [ ] **Step 2: Write umbrella `_index.md`**

```markdown
---
title: 'Library'
description: 'Books, music, games, films and series I am spending time with.'
cascade:
  type: library
---

Books, music, games, films and series I am spending time with right now — and what I have finished.
```

- [ ] **Step 3: Write reading `_index.md`**

```markdown
---
title: 'Reading'
description: 'Books I am reading or have finished.'
cascade:
  type: library-reading
---

Books I am spending time with right now, and what I have finished.
```

- [ ] **Step 4: Write listening `_index.md`**

```markdown
---
title: 'Listening'
description: 'Albums and tracks on rotation.'
cascade:
  type: library-listening
---

Albums and tracks on rotation, and what I have set down.
```

- [ ] **Step 5: Write playing `_index.md`**

```markdown
---
title: 'Playing'
description: 'Games I am playing or have played.'
cascade:
  type: library-playing
---

Games I am playing or have played to credits.
```

- [ ] **Step 6: Write watching `_index.md`**

```markdown
---
title: 'Watching'
description: 'Films and series I have watched or am working through.'
cascade:
  type: library-watching
---

Films and series I have watched or am working through.
```

- [ ] **Step 7: Commit**

```bash
git add content/library
git commit -m "content: library section _index files (umbrella + 4 leaves)"
```

---

### Task B2: Shared partial — `partials/library/status-badge.html`

**Files:**
- Create: `layouts/partials/library/status-badge.html`

- [ ] **Step 1: Create directory + write partial**

```bash
mkdir -p layouts/partials/library
```

Write `layouts/partials/library/status-badge.html`:

```html
{{- /* Status badge: shape + color in row gutter.
       Input: . is the status string ('finished' | 'reading' | 'listening' |
       'playing' | 'watching' | 'queued' | 'abandoned' | 'dropped' | '100pct').
       Renders an aria-labelled span with a class for color and a glyph as text. */ -}}
{{- $glyph := "" -}}
{{- $cls := "" -}}
{{- $aria := . -}}
{{- if eq . "finished" -}}     {{- $glyph = "✓" -}}{{- $cls = "b-fin" -}}
{{- else if eq . "100pct" -}}  {{- $glyph = "★" -}}{{- $cls = "b-100" -}}{{- $aria = "100% complete" -}}
{{- else if or (eq . "reading") (eq . "listening") (eq . "playing") (eq . "watching") -}}
                               {{- $glyph = "▶" -}}{{- $cls = "b-act" -}}
{{- else if eq . "queued" -}}  {{- $glyph = "↑" -}}{{- $cls = "b-queue" -}}
{{- else if or (eq . "abandoned") (eq . "dropped") -}}
                               {{- $glyph = "✗" -}}{{- $cls = "b-aban" -}}
{{- end -}}
<span class="library-status-badge {{ $cls }}" aria-label="status: {{ $aria }}">{{ $glyph }}</span>
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/library/status-badge.html
git commit -m "partial: library status-badge (shape+color, CB-safe)"
```

---

### Task B3: Shared partial — `partials/library/type-glyph.html`

**Files:**
- Create: `layouts/partials/library/type-glyph.html`

- [ ] **Step 1: Write the partial**

```html
{{- /* Type glyph in tinted block. Inputs:
       .media_type — book | album | track | game | film | series
       .size       — "large" (highlight cards, 56×72) or "mini" (rows, 44×56)
       Reused SVGs from works for music + game. New SVGs for book + clapper. */ -}}
{{- $mt := .media_type -}}
{{- $size := .size | default "mini" -}}
{{- $cls := "library-glyph-block" -}}
{{- if eq $size "large" -}}{{- $cls = printf "%s is-large" $cls -}}{{- end -}}
{{- $modifier := "" -}}
{{- $iconPath := "" -}}
{{- if eq $mt "book" -}}
  {{- $modifier = "book" -}}{{- $iconPath = "images/icons/library/book.svg" -}}
{{- else if or (eq $mt "album") (eq $mt "track") -}}
  {{- $modifier = "music" -}}{{- $iconPath = "images/icons/glyph-music.svg" -}}
{{- else if eq $mt "game" -}}
  {{- $modifier = "game" -}}{{- $iconPath = "images/icons/glyph-game.svg" -}}
{{- else if or (eq $mt "film") (eq $mt "series") -}}
  {{- $modifier = "watching" -}}{{- $iconPath = "images/icons/library/clapper.svg" -}}
{{- end -}}
<span class="{{ $cls }} {{ $modifier }}" aria-hidden="true">
  {{- with resources.Get $iconPath -}}{{- .Content | safeHTML -}}{{- end -}}
</span>
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/library/type-glyph.html
git commit -m "partial: library type-glyph (book / music / game / clapper)"
```

---

### Task B4: Shared partial — `partials/library/row.html`

**Files:**
- Create: `layouts/partials/library/row.html`

- [ ] **Step 1: Write the partial**

```html
{{- /* One library row.
       Input: . is an item dict from data/<page>.yaml.
       Renders into a year section. */ -}}
{{- $item := . -}}
{{- $tags := delimit ($item.tags | default slice) " " -}}
<article class="library-row" data-status="{{ $item.status }}" data-media-type="{{ $item.media_type }}" data-tags="{{ $tags }}"{{ with $item.extras.platform }} data-platform="{{ . }}"{{ end }}>
  <div class="library-row-badge">{{ partial "library/status-badge.html" $item.status }}</div>
  {{ partial "library/type-glyph.html" (dict "media_type" $item.media_type "size" "mini") }}
  <div class="library-row-content">
    <h4 class="library-row-title">
      <span class="ttl">{{ $item.title }}</span>
      {{- with $item.tags }}<span class="library-row-tags">{{ delimit . " · " }}</span>{{ end -}}
    </h4>
    <div class="library-row-meta">
      {{ $item.creator }}{{ with $item.year }} · {{ . }}{{ end }}
      {{- with $item.extras.platform }} · {{ . }}{{ end -}}
      {{- with $item.extras.runtime_min }} · {{ . }} min{{ end -}}
      {{- with $item.extras.episode_count }} · {{ . }} ep{{ end -}}
      {{- with $item.extras.hours_played }} · {{ . }}h{{ end -}}
      {{- with $item.finished }} · finished {{ . }}{{ end -}}
      {{- if eq $item.spoiler_level "heavy" }} · <span class="library-spoiler-heavy">spoilers: heavy</span>{{ end -}}
      {{- if eq $item.spoiler_level "light" }} · <span class="library-spoiler-light">spoilers: light</span>{{ end -}}
    </div>
    {{- with $item.preview }}<p class="library-row-takeaway">{{ . }}</p>{{ end -}}
    <div class="library-row-links">
      {{- with $item.note_slug }}<a href="{{ printf "/garden/%s/" . | relURL }}">→ my notes</a>{{ end -}}
      {{- with $item.canonical_url }}<a href="{{ . }}">→ original</a>{{ end -}}
    </div>
  </div>
</article>
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/library/row.html
git commit -m "partial: library row (badge + glyph + meta + takeaway + links)"
```

---

### Task B5: Shared partial — `partials/library/year-section.html`

**Files:**
- Create: `layouts/partials/library/year-section.html`

- [ ] **Step 1: Write the partial**

```html
{{- /* One year section: rule + label + rows.
       Input: dict { year (string), items (slice of item dicts) }.
       year may be "Undated" for items with no `finished` date. */ -}}
{{- $year := .year -}}
{{- $items := .items -}}
<section class="library-year" data-year="{{ $year }}">
  <header class="library-year-rule">{{ $year }}</header>
  {{- range $items -}}
    {{ partial "library/row.html" . }}
  {{- end -}}
</section>
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/library/year-section.html
git commit -m "partial: library year-section (rule + rows)"
```

---

### Task B6: Shared partial — `partials/library/currently-active.html`

**Files:**
- Create: `layouts/partials/library/currently-active.html`

- [ ] **Step 1: Write the partial**

```html
{{- /* Currently-active highlight strip above year sections.
       Input: dict { items (active items, len 1..3) }.
       Layout: 1 → full width; 2-3 → 2-col grid (data-active-count). */ -}}
{{- $items := .items -}}
{{- if $items -}}
<section class="library-currently" data-active-count="{{ len $items }}">
  <header class="library-section-rule">Currently active</header>
  <div class="library-currently-grid">
    {{- range $items -}}
      {{- $item := . -}}
      <article class="library-curr-card" data-media-type="{{ $item.media_type }}">
        {{ partial "library/type-glyph.html" (dict "media_type" $item.media_type "size" "large") }}
        <div class="library-curr-content">
          <h3 class="library-curr-title">{{ $item.title }}</h3>
          <div class="library-curr-meta">
            {{ $item.creator }}{{ with $item.year }} · {{ . }}{{ end }}
            {{- with $item.extras.platform }} · {{ . }}{{ end -}}
            {{- with $item.extras.hours_played }} · {{ . }}h played{{ end -}}
            {{- if eq $item.spoiler_level "heavy" }} · <span class="library-spoiler-heavy">spoilers: heavy</span>{{ end -}}
            {{- if eq $item.spoiler_level "light" }} · <span class="library-spoiler-light">spoilers: light</span>{{ end -}}
          </div>
          {{- /* Progress bar: book uses extras.progress_pct;
                 series uses current_episode / episode_count. */ -}}
          {{- $pct := 0 -}}
          {{- $showBar := false -}}
          {{- $progLabel := "" -}}
          {{- if eq $item.media_type "book" -}}
            {{- with $item.extras.progress_pct }}{{- $pct = . -}}{{- $showBar = true -}}{{- end -}}
            {{- $progLabel = $item.extras.progress_label | default "" -}}
          {{- else if eq $item.media_type "series" -}}
            {{- $ce := $item.extras.current_episode | default 0 -}}
            {{- $ec := $item.extras.episode_count | default 0 -}}
            {{- if and (gt $ec 0) (gt $ce 0) -}}
              {{- $pct = mul (div (mul $ce 100) $ec) 1 -}}
              {{- $showBar = true -}}
              {{- $progLabel = printf "ep %d / %d" $ce $ec -}}
            {{- end -}}
          {{- end -}}
          {{- if $showBar -}}
            <div class="library-progress" role="progressbar" aria-valuenow="{{ $pct }}" aria-valuemin="0" aria-valuemax="100"><span style="width:{{ $pct }}%"></span></div>
            <div class="library-progress-meta">
              {{- with $item.started }}started {{ . }}{{ end -}}
              {{- if and $item.started $progLabel }} · {{ $progLabel }}{{ else }}{{ $progLabel }}{{ end -}}
            </div>
          {{- else -}}
            {{- with $item.started }}<div class="library-progress-meta">started {{ . }}</div>{{ end -}}
          {{- end -}}
          {{- with $item.preview }}<p class="library-curr-takeaway">{{ . }}</p>{{ end -}}
          <div class="library-row-links">
            {{- with $item.note_slug }}<a href="{{ printf "/garden/%s/" . | relURL }}">→ my notes</a>{{ end -}}
            {{- with $item.canonical_url }}<a href="{{ . }}">→ original</a>{{ end -}}
          </div>
        </div>
      </article>
    {{- end -}}
  </div>
</section>
{{- end -}}
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/library/currently-active.html
git commit -m "partial: library currently-active (1-up or 2-up grid + progress bar)"
```

---

### Task B7: Shared partial — `partials/library/umbrella-card.html`

**Files:**
- Create: `layouts/partials/library/umbrella-card.html`

- [ ] **Step 1: Write the partial**

```html
{{- /* One card on the /library/ umbrella.
       Input: dict { label, glyph_media_type, page_url, items }.
       Renders: title + glyph, stats line, top-3 (active or recent) items, "All X →" link. */ -}}
{{- $label := .label -}}
{{- $items := .items -}}
{{- $pageUrl := .page_url -}}
{{- $glyphMt := .glyph_media_type -}}
{{- $allItems := $items -}}

{{- /* Counts by status for the stats line */ -}}
{{- $finished := 0 -}}{{- $active := 0 -}}{{- $queued := 0 -}}{{- $other := 0 -}}
{{- range $items -}}
  {{- if eq .status "finished" -}}{{- $finished = add $finished 1 -}}
  {{- else if or (eq .status "reading") (eq .status "listening") (eq .status "playing") (eq .status "watching") -}}{{- $active = add $active 1 -}}
  {{- else if eq .status "queued" -}}{{- $queued = add $queued 1 -}}
  {{- else -}}{{- $other = add $other 1 -}}{{- end -}}
{{- end -}}

{{- /* Top 3: active first, then most-recent finished by last_modified desc. */ -}}
{{- $activeItems := slice -}}
{{- $finishedItems := slice -}}
{{- range $items -}}
  {{- if or (eq .status "reading") (eq .status "listening") (eq .status "playing") (eq .status "watching") -}}
    {{- $activeItems = $activeItems | append . -}}
  {{- else if eq .status "finished" -}}
    {{- $finishedItems = $finishedItems | append . -}}
  {{- end -}}
{{- end -}}
{{- $sortedFinished := sort $finishedItems "last_modified" "desc" -}}
{{- $top := $activeItems -}}
{{- if lt (len $top) 3 -}}{{- $top = $top | append $sortedFinished -}}{{- end -}}
{{- if gt (len $top) 3 -}}{{- $top = first 3 $top -}}{{- end -}}

<article class="library-um-card">
  <h3 class="library-um-card-title">
    {{ $label }}
    <span class="library-um-glyph" aria-hidden="true">
      {{- with resources.Get (printf "images/icons/%s" (cond (eq $glyphMt "book") "library/book.svg" (cond (eq $glyphMt "music") "glyph-music.svg" (cond (eq $glyphMt "game") "glyph-game.svg" "library/clapper.svg")))) -}}
        {{ .Content | safeHTML }}
      {{- end -}}
    </span>
  </h3>
  <p class="library-um-card-stats">{{ $finished }} finished · {{ $active }} active · {{ $queued }} queued</p>
  <ul class="library-um-card-list">
    {{- range $top -}}
      <li>
        {{ partial "library/status-badge.html" .status }}
        <span>
          <span class="ttl">{{ .title }}</span>
          <span class="creator">{{ .creator }}{{ with .year }} · {{ . }}{{ end }}</span>
        </span>
      </li>
    {{- end -}}
  </ul>
  <p class="library-um-card-link"><a href="{{ $pageUrl | relURL }}">All {{ $label | lower }} →</a></p>
</article>
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/library/umbrella-card.html
git commit -m "partial: library umbrella-card (counts + top-3 + link)"
```

---

### Task B8: Umbrella layout — `layouts/library/list.html`

**Files:**
- Create: `layouts/library/list.html`

- [ ] **Step 1: Write the layout**

```html
{{ define "main" }}
{{- $reading := (index site.Data "reading").items | default slice -}}
{{- $listening := (index site.Data "listening").items | default slice -}}
{{- $playing := (index site.Data "playing").items | default slice -}}
{{- $watching := (index site.Data "watching").items | default slice -}}
<main class="library-umbrella-page">
  <header class="library-page-header">
    <h1 class="library-page-title">{{ .Title }}</h1>
    {{- with .Content }}<div class="library-page-lede">{{ . }}</div>{{ end -}}
  </header>

  <div class="library-umbrella-grid">
    {{ partial "library/umbrella-card.html" (dict "label" "Reading"   "glyph_media_type" "book"  "page_url" "/library/reading/"   "items" $reading) }}
    {{ partial "library/umbrella-card.html" (dict "label" "Listening" "glyph_media_type" "music" "page_url" "/library/listening/" "items" $listening) }}
    {{ partial "library/umbrella-card.html" (dict "label" "Playing"   "glyph_media_type" "game"  "page_url" "/library/playing/"   "items" $playing) }}
    {{ partial "library/umbrella-card.html" (dict "label" "Watching"  "glyph_media_type" "film"  "page_url" "/library/watching/"  "items" $watching) }}
  </div>
</main>
{{ end }}
```

- [ ] **Step 2: Run dev server and visit `/library/`**

In a separate terminal:

```bash
hugo server --buildDrafts
```

Open: `http://localhost:1313/library/`
Expected: 4 cards visible, each with title + glyph + stats + 3 items + "All X →" link.

Stop the dev server when done: `pkill -f "hugo server"`

- [ ] **Step 3: Commit**

```bash
git add layouts/library/list.html
git commit -m "layout: library umbrella (4-card 2x2 grid)"
```

---

### Task B9: Build a `_buildLeaf` helper convention + `layouts/library/reading/list.html`

The 4 leaf layouts are nearly identical — they differ in (a) which yaml they read, (b) which `data-library-page` value they emit, (c) which "other" filter dim values they expose. Build the first leaf and the others mirror it.

**Files:**
- Create: `layouts/library/reading/list.html`

- [ ] **Step 1: Write the layout**

```html
{{ define "main" }}
{{- $items := (index site.Data "reading").items | default slice -}}

{{- /* Partition into active / finished-by-year / queued */ -}}
{{- $active := slice -}}{{- $byYear := dict -}}{{- $queued := slice -}}{{- $undated := slice -}}
{{- range $items -}}
  {{- if eq .status "reading" -}}{{- $active = $active | append . -}}
  {{- else if eq .status "queued" -}}{{- $queued = $queued | append . -}}
  {{- else -}}
    {{- $year := "Undated" -}}
    {{- with .finished -}}{{- $year = (substr . 0 4) -}}{{- end -}}
    {{- if eq $year "Undated" -}}
      {{- $undated = $undated | append . -}}
    {{- else -}}
      {{- $existing := index $byYear $year | default slice -}}
      {{- $byYear = merge $byYear (dict $year ($existing | append .)) -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{- /* Build sorted descending year list */ -}}
{{- $years := slice -}}
{{- range $k, $_ := $byYear -}}{{- $years = $years | append $k -}}{{- end -}}
{{- $years = sort $years "value" "desc" -}}

{{- /* Tag dim values across all items, ranked by count desc */ -}}
{{- $tagCount := dict -}}
{{- range $items -}}{{- range .tags -}}
  {{- $cur := index $tagCount . | default 0 -}}
  {{- $tagCount = merge $tagCount (dict . (add $cur 1)) -}}
{{- end -}}{{- end -}}
{{- $tagValues := slice -}}
{{- range $k, $_ := $tagCount -}}{{- $tagValues = $tagValues | append $k -}}{{- end -}}
{{- $tagValues = sort $tagValues "value" "asc" -}}

<main class="library-leaf-page" data-library-page="reading">
  <body data-library-page="reading"><!-- consumed in JS --></body>
  <header class="library-page-header">
    <nav class="library-breadcrumb"><a href="{{ "/library/" | relURL }}">Library</a> › Reading</nav>
    <h1 class="library-page-title">{{ .Title }}</h1>
    {{- with .Content }}<div class="library-page-lede">{{ . }}</div>{{ end -}}
  </header>

  {{- if $items -}}
    {{ partial "library/currently-active.html" (dict "items" $active) }}

    <p class="library-stats-line">{{ len $items }} total — partition counts shown via filter chips below.</p>
    <div class="library-chips" data-page="reading">
      {{ partial "filter-chips.html" (dict "section" "library-reading" "dimensions" (slice
        (dict "key" "status" "label" "Status" "values" (slice "finished" "reading" "queued" "abandoned"))
        (dict "key" "tag"    "label" "Tag"    "values" $tagValues)
      )) }}
    </div>

    {{- range $year := $years -}}
      {{ partial "library/year-section.html" (dict "year" $year "items" (index $byYear $year)) }}
    {{- end -}}
    {{- with $undated -}}
      {{ partial "library/year-section.html" (dict "year" "Undated" "items" .) }}
    {{- end -}}

    {{- with $queued -}}
      <section class="library-upnext">
        <header class="library-section-rule">Up next</header>
        {{- range . -}}
          <p class="library-upnext-row">↑ <span class="ttl">{{ .title }}</span> · {{ .creator }}{{ with .year }} · {{ . }}{{ end }}</p>
        {{- end -}}
      </section>
    {{- end -}}
  {{- else -}}
    <p class="library-empty">Nothing here yet.</p>
  {{- end -}}
</main>
{{ end }}
```

> The `<body data-library-page>` block inside `<main>` is intentional: it's consumed by `entry-library.js` via `document.body.dataset.libraryPage`. Hugo's `baseof.html` controls the real `<body>`; the inner element is a JS hook only. (Verify the inner `<body>` is acceptable in the rendered HTML; if it gets stripped or causes dev-tools warnings, switch to `<div data-library-page>` and update the JS selector.)

> **Note:** check `layouts/_default/baseof.html` first — if it already lets a layout set `data-library-page` on the real `<body>` via a block, prefer that. Fall back to the `<div data-library-page>` approach only if no clean hook exists.

- [ ] **Step 2: Inspect baseof.html for body-attr hook**

Run: `grep -n "<body" layouts/_default/baseof.html`
Expected: shows the body tag and any block hook around it.

If a `bodyAttrs` block or similar exists, update the layout to use it (write `{{ define "bodyAttrs" }}data-library-page="reading"{{ end }}` near the top of `list.html`) and **remove** the inner `<body>` element from the layout.

If no hook exists, replace the inner `<body data-library-page="reading">` with `<div data-library-page="reading" hidden></div>` and update the JS read in Task C2 to use `document.querySelector('[data-library-page]')?.dataset?.libraryPage`.

- [ ] **Step 3: Dev server check**

Open `http://localhost:1313/library/reading/`. Expected: page renders with 2 currently-reading cards (with progress bars), 2026 + 2025 year sections + Up next block. Filter chips strip visible (status row + tag row, "All" active).

- [ ] **Step 4: Commit**

```bash
git add layouts/library/reading/list.html
git commit -m "layout: /library/reading/ with currently-active + year sections + queue"
```

---

### Task B10: `layouts/library/listening/list.html`

**Files:**
- Create: `layouts/library/listening/list.html`

- [ ] **Step 1: Write the layout**

Mirror `reading/list.html` with two diffs:
- read `(index site.Data "listening").items`
- status partition uses "listening" as the active status; status chip values are `finished | listening | queued | dropped`
- add a `format` dim with values from item `media_type` (album, track) — only emit chips for distinct media_types present
- `data-library-page="listening"`, `section "library-listening"`

```html
{{ define "main" }}
{{- $items := (index site.Data "listening").items | default slice -}}
{{- $active := slice -}}{{- $byYear := dict -}}{{- $queued := slice -}}{{- $undated := slice -}}
{{- range $items -}}
  {{- if eq .status "listening" -}}{{- $active = $active | append . -}}
  {{- else if eq .status "queued" -}}{{- $queued = $queued | append . -}}
  {{- else -}}
    {{- $year := "Undated" -}}{{- with .finished -}}{{- $year = (substr . 0 4) -}}{{- end -}}
    {{- if eq $year "Undated" -}}{{- $undated = $undated | append . -}}
    {{- else -}}{{- $existing := index $byYear $year | default slice -}}{{- $byYear = merge $byYear (dict $year ($existing | append .)) -}}{{- end -}}
  {{- end -}}
{{- end -}}
{{- $years := slice -}}
{{- range $k, $_ := $byYear -}}{{- $years = $years | append $k -}}{{- end -}}
{{- $years = sort $years "value" "desc" -}}

{{- $formatValues := slice -}}
{{- range $items -}}
  {{- if not (in $formatValues .media_type) -}}{{- $formatValues = $formatValues | append .media_type -}}{{- end -}}
{{- end -}}
{{- $formatValues = sort $formatValues -}}

{{- $tagCount := dict -}}
{{- range $items -}}{{- range .tags -}}
  {{- $cur := index $tagCount . | default 0 -}}{{- $tagCount = merge $tagCount (dict . (add $cur 1)) -}}
{{- end -}}{{- end -}}
{{- $tagValues := slice -}}
{{- range $k, $_ := $tagCount -}}{{- $tagValues = $tagValues | append $k -}}{{- end -}}
{{- $tagValues = sort $tagValues "value" "asc" -}}

<main class="library-leaf-page" data-library-page="listening">
  <header class="library-page-header">
    <nav class="library-breadcrumb"><a href="{{ "/library/" | relURL }}">Library</a> › Listening</nav>
    <h1 class="library-page-title">{{ .Title }}</h1>
    {{- with .Content }}<div class="library-page-lede">{{ . }}</div>{{ end -}}
  </header>

  {{- if $items -}}
    {{ partial "library/currently-active.html" (dict "items" $active) }}

    <p class="library-stats-line">{{ len $items }} total.</p>
    <div class="library-chips" data-page="listening">
      {{ partial "filter-chips.html" (dict "section" "library-listening" "dimensions" (slice
        (dict "key" "status" "label" "Status" "values" (slice "finished" "listening" "queued" "dropped"))
        (dict "key" "format" "label" "Format" "values" $formatValues)
        (dict "key" "tag"    "label" "Tag"    "values" $tagValues)
      )) }}
    </div>

    {{- range $year := $years -}}
      {{ partial "library/year-section.html" (dict "year" $year "items" (index $byYear $year)) }}
    {{- end -}}
    {{- with $undated -}}
      {{ partial "library/year-section.html" (dict "year" "Undated" "items" .) }}
    {{- end -}}
    {{- with $queued -}}
      <section class="library-upnext">
        <header class="library-section-rule">Up next</header>
        {{- range . -}}<p class="library-upnext-row">↑ <span class="ttl">{{ .title }}</span> · {{ .creator }}{{ with .year }} · {{ . }}{{ end }}</p>{{- end -}}
      </section>
    {{- end -}}
  {{- else -}}
    <p class="library-empty">Nothing here yet.</p>
  {{- end -}}
</main>
{{ end }}
```

The `data-library-page="listening"` attribute on `<main>` must also propagate to the body — apply the same pattern from Task B9 step 2.

- [ ] **Step 2: Dev server check**

Open `http://localhost:1313/library/listening/`. Expected: 2 currently-listening cards (no progress bar), year sections, format chip dim shows `album` + `track` (2 chips), Up next block visible.

- [ ] **Step 3: Commit**

```bash
git add layouts/library/listening/list.html
git commit -m "layout: /library/listening/ with format dim (album/track)"
```

---

### Task B11: `layouts/library/playing/list.html`

**Files:**
- Create: `layouts/library/playing/list.html`

- [ ] **Step 1: Write the layout**

Same shape as listening with these diffs:
- partition active on `eq .status "playing"`
- status chip values: `finished | 100pct | playing | queued | dropped`
- replace format dim with platform dim from `extras.platform`
- `data-library-page="playing"`, section `library-playing`

```html
{{ define "main" }}
{{- $items := (index site.Data "playing").items | default slice -}}
{{- $active := slice -}}{{- $byYear := dict -}}{{- $queued := slice -}}{{- $undated := slice -}}
{{- range $items -}}
  {{- if eq .status "playing" -}}{{- $active = $active | append . -}}
  {{- else if eq .status "queued" -}}{{- $queued = $queued | append . -}}
  {{- else -}}
    {{- $year := "Undated" -}}{{- with .finished -}}{{- $year = (substr . 0 4) -}}{{- end -}}
    {{- if eq $year "Undated" -}}{{- $undated = $undated | append . -}}
    {{- else -}}{{- $existing := index $byYear $year | default slice -}}{{- $byYear = merge $byYear (dict $year ($existing | append .)) -}}{{- end -}}
  {{- end -}}
{{- end -}}
{{- $years := slice -}}
{{- range $k, $_ := $byYear -}}{{- $years = $years | append $k -}}{{- end -}}
{{- $years = sort $years "value" "desc" -}}

{{- $platValues := slice -}}
{{- range $items -}}
  {{- with .extras.platform -}}
    {{- if not (in $platValues .) -}}{{- $platValues = $platValues | append . -}}{{- end -}}
  {{- end -}}
{{- end -}}
{{- $platValues = sort $platValues -}}

{{- $tagCount := dict -}}
{{- range $items -}}{{- range .tags -}}
  {{- $cur := index $tagCount . | default 0 -}}{{- $tagCount = merge $tagCount (dict . (add $cur 1)) -}}
{{- end -}}{{- end -}}
{{- $tagValues := slice -}}
{{- range $k, $_ := $tagCount -}}{{- $tagValues = $tagValues | append $k -}}{{- end -}}
{{- $tagValues = sort $tagValues "value" "asc" -}}

<main class="library-leaf-page" data-library-page="playing">
  <header class="library-page-header">
    <nav class="library-breadcrumb"><a href="{{ "/library/" | relURL }}">Library</a> › Playing</nav>
    <h1 class="library-page-title">{{ .Title }}</h1>
    {{- with .Content }}<div class="library-page-lede">{{ . }}</div>{{ end -}}
  </header>

  {{- if $items -}}
    {{ partial "library/currently-active.html" (dict "items" $active) }}

    <p class="library-stats-line">{{ len $items }} total.</p>
    <div class="library-chips" data-page="playing">
      {{ partial "filter-chips.html" (dict "section" "library-playing" "dimensions" (slice
        (dict "key" "status"   "label" "Status"   "values" (slice "finished" "100pct" "playing" "queued" "dropped"))
        (dict "key" "platform" "label" "Platform" "values" $platValues)
        (dict "key" "tag"      "label" "Tag"      "values" $tagValues)
      )) }}
    </div>

    {{- range $year := $years -}}
      {{ partial "library/year-section.html" (dict "year" $year "items" (index $byYear $year)) }}
    {{- end -}}
    {{- with $undated -}}
      {{ partial "library/year-section.html" (dict "year" "Undated" "items" .) }}
    {{- end -}}
    {{- with $queued -}}
      <section class="library-upnext">
        <header class="library-section-rule">Up next</header>
        {{- range . -}}<p class="library-upnext-row">↑ <span class="ttl">{{ .title }}</span> · {{ .creator }}{{ with .year }} · {{ . }}{{ end }}</p>{{- end -}}
      </section>
    {{- end -}}
  {{- else -}}
    <p class="library-empty">Nothing here yet.</p>
  {{- end -}}
</main>
{{ end }}
```

The `partials/library/row.html` already emits `data-platform` from `extras.platform` so the platform chip filter will work without further row template changes.

- [ ] **Step 2: Dev server check**

`http://localhost:1313/library/playing/`. Expected: gamepad glyph throughout; 1 active "Outer Wilds" card; ★ status badge on the 100pct row; platform chip dim shows distinct platforms (PC / Switch / PS5 / Web).

- [ ] **Step 3: Commit**

```bash
git add layouts/library/playing/list.html
git commit -m "layout: /library/playing/ with platform dim (dynamic from extras)"
```

---

### Task B12: `layouts/library/watching/list.html`

**Files:**
- Create: `layouts/library/watching/list.html`

- [ ] **Step 1: Write the layout**

```html
{{ define "main" }}
{{- $items := (index site.Data "watching").items | default slice -}}
{{- $active := slice -}}{{- $byYear := dict -}}{{- $queued := slice -}}{{- $undated := slice -}}
{{- range $items -}}
  {{- if eq .status "watching" -}}{{- $active = $active | append . -}}
  {{- else if eq .status "queued" -}}{{- $queued = $queued | append . -}}
  {{- else -}}
    {{- $year := "Undated" -}}{{- with .finished -}}{{- $year = (substr . 0 4) -}}{{- end -}}
    {{- if eq $year "Undated" -}}{{- $undated = $undated | append . -}}
    {{- else -}}{{- $existing := index $byYear $year | default slice -}}{{- $byYear = merge $byYear (dict $year ($existing | append .)) -}}{{- end -}}
  {{- end -}}
{{- end -}}
{{- $years := slice -}}
{{- range $k, $_ := $byYear -}}{{- $years = $years | append $k -}}{{- end -}}
{{- $years = sort $years "value" "desc" -}}

{{- $formatValues := slice -}}
{{- range $items -}}
  {{- if not (in $formatValues .media_type) -}}{{- $formatValues = $formatValues | append .media_type -}}{{- end -}}
{{- end -}}
{{- $formatValues = sort $formatValues -}}

{{- $tagCount := dict -}}
{{- range $items -}}{{- range .tags -}}
  {{- $cur := index $tagCount . | default 0 -}}{{- $tagCount = merge $tagCount (dict . (add $cur 1)) -}}
{{- end -}}{{- end -}}
{{- $tagValues := slice -}}
{{- range $k, $_ := $tagCount -}}{{- $tagValues = $tagValues | append $k -}}{{- end -}}
{{- $tagValues = sort $tagValues "value" "asc" -}}

<main class="library-leaf-page" data-library-page="watching">
  <header class="library-page-header">
    <nav class="library-breadcrumb"><a href="{{ "/library/" | relURL }}">Library</a> › Watching</nav>
    <h1 class="library-page-title">{{ .Title }}</h1>
    {{- with .Content }}<div class="library-page-lede">{{ . }}</div>{{ end -}}
  </header>

  {{- if $items -}}
    {{ partial "library/currently-active.html" (dict "items" $active) }}

    <p class="library-stats-line">{{ len $items }} total.</p>
    <div class="library-chips" data-page="watching">
      {{ partial "filter-chips.html" (dict "section" "library-watching" "dimensions" (slice
        (dict "key" "status" "label" "Status" "values" (slice "finished" "watching" "queued" "dropped"))
        (dict "key" "format" "label" "Format" "values" $formatValues)
        (dict "key" "tag"    "label" "Tag"    "values" $tagValues)
      )) }}
    </div>

    {{- range $year := $years -}}
      {{ partial "library/year-section.html" (dict "year" $year "items" (index $byYear $year)) }}
    {{- end -}}
    {{- with $undated -}}
      {{ partial "library/year-section.html" (dict "year" "Undated" "items" .) }}
    {{- end -}}
    {{- with $queued -}}
      <section class="library-upnext">
        <header class="library-section-rule">Up next</header>
        {{- range . -}}<p class="library-upnext-row">↑ <span class="ttl">{{ .title }}</span> · {{ .creator }}{{ with .year }} · {{ . }}{{ end }}</p>{{- end -}}
      </section>
    {{- end -}}
  {{- else -}}
    <p class="library-empty">Nothing here yet.</p>
  {{- end -}}
</main>
{{ end }}
```

- [ ] **Step 2: Dev server check**

`http://localhost:1313/library/watching/`. Expected: clapper glyph; 1 currently-watching "Lorem Series I" card with progress bar (`ep 4/8`); year sections show film + series mixed; format chips render `film` + `series`.

- [ ] **Step 3: Commit**

```bash
git add layouts/library/watching/list.html
git commit -m "layout: /library/watching/ with format dim (film/series) + ep progress"
```

---

## Phase C — styling + JS

### Task C1: Append CSS section §37 Library

**Files:**
- Modify: `assets/css/main.css` — append at end (after current line 2811).

- [ ] **Step 1: Append the section to main.css**

```css

/* ------------------------------------------------------------------
 * 37. Library
 * ------------------------------------------------------------------ */

.library-page-header { margin-bottom: 2rem; }
.library-breadcrumb {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.4rem;
}
.library-breadcrumb a { color: inherit; text-decoration: none; }
.library-breadcrumb a:hover { color: var(--color-burgundy); }
.library-page-title {
  font-family: var(--font-body);
  font-weight: 700;
  font-size: var(--text-2xl);
  margin: 0 0 0.4rem;
  letter-spacing: -0.01em;
}
.library-page-lede {
  font-family: var(--font-body);
  font-style: italic;
  color: var(--color-ink-soft);
  margin-bottom: 1.5rem;
  max-width: 60ch;
}

/* Section rule (Currently / Up next / year headers) */
.library-section-rule,
.library-year-rule {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-ink-soft);
  margin: 1.75rem 0 0.875rem;
}
.library-section-rule::after,
.library-year-rule::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--color-rule);
}

/* Umbrella 2x2 grid */
.library-umbrella-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}
.library-um-card {
  border: 1px solid var(--color-rule);
  background: var(--color-tile);
  border-radius: 4px;
  padding: 1.125rem;
}
.library-um-card-title {
  font-family: var(--font-body);
  font-weight: 700;
  font-size: var(--text-md);
  margin: 0 0 0.4rem;
  display: flex;
  align-items: center;
  gap: 0.625rem;
}
.library-um-glyph {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.4rem;
  height: 1.4rem;
  color: var(--color-ink-soft);
}
.library-um-glyph svg { width: 100%; height: 100%; }
.library-um-card-stats {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  margin: 0 0 0.875rem;
}
.library-um-card-list {
  list-style: none;
  padding: 0;
  margin: 0 0 0.875rem;
}
.library-um-card-list li {
  display: grid;
  grid-template-columns: 1.125rem 1fr;
  gap: 0.5rem;
  padding: 0.5rem 0;
  border-top: 1px solid color-mix(in srgb, var(--color-rule) 40%, transparent);
  font-size: var(--text-sm);
  align-items: center;
}
.library-um-card-list li:first-child { border-top: 0; }
.library-um-card-list .ttl { font-style: italic; }
.library-um-card-list .creator {
  display: block;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  margin-top: 0.125rem;
  font-style: normal;
}
.library-um-card-link {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  margin: 0;
}
.library-um-card-link a { color: var(--color-burgundy); text-decoration: none; border-bottom: 1px dotted var(--color-burgundy); }

/* Status badge */
.library-status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-ui);
  font-size: var(--text-base);
  font-weight: 600;
}
.library-status-badge.b-fin   { color: var(--color-green); }
.library-status-badge.b-act   { color: var(--color-steel); }
.library-status-badge.b-queue { color: var(--color-ink-soft); }
.library-status-badge.b-aban  { color: var(--color-burgundy); }
.library-status-badge.b-100   { color: var(--color-warn); }

/* Glyph block (tinted square holding the type SVG) */
.library-glyph-block {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 3.5rem;
  border-radius: 3px;
  color: var(--color-tile);
  background: linear-gradient(180deg, var(--color-burgundy) 0%, color-mix(in srgb, var(--color-burgundy) 70%, black) 100%);
  flex-shrink: 0;
}
.library-glyph-block.is-large { width: 3.5rem; height: 4.5rem; }
.library-glyph-block svg { width: 60%; height: 60%; }
.library-glyph-block.book {} /* default burgundy */
.library-glyph-block.music   { background: linear-gradient(180deg, var(--color-steel) 0%, color-mix(in srgb, var(--color-steel) 70%, black) 100%); }
.library-glyph-block.game    { background: linear-gradient(180deg, var(--color-green) 0%, color-mix(in srgb, var(--color-green) 70%, black) 100%); }
.library-glyph-block.watching { background: linear-gradient(180deg, var(--color-violet) 0%, color-mix(in srgb, var(--color-violet) 70%, black) 100%); }

/* Currently-active highlight */
.library-currently-grid {
  display: grid;
  gap: 1rem;
}
.library-currently[data-active-count="1"] .library-currently-grid { grid-template-columns: 1fr; }
.library-currently[data-active-count="2"] .library-currently-grid,
.library-currently[data-active-count="3"] .library-currently-grid { grid-template-columns: 1fr 1fr; }

.library-curr-card {
  display: grid;
  grid-template-columns: 4rem 1fr;
  gap: 0.875rem;
  border: 1px solid var(--color-rule);
  background: var(--color-tile);
  border-radius: 4px;
  padding: 1.125rem;
}
.library-curr-title {
  font-family: var(--font-body);
  font-style: italic;
  font-size: var(--text-md);
  margin: 0;
  line-height: 1.2;
}
.library-curr-meta {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  margin: 0.125rem 0 0.625rem;
}
.library-progress {
  height: 0.5rem;
  background: color-mix(in srgb, var(--color-rule) 40%, transparent);
  border-radius: 0.25rem;
  overflow: hidden;
  margin: 0.375rem 0 0.25rem;
}
.library-progress > span {
  display: block;
  height: 100%;
  background: var(--color-steel);
}
.library-progress-meta {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  margin-bottom: 0.5rem;
}
.library-curr-takeaway {
  font-family: var(--font-body);
  font-style: italic;
  font-size: var(--text-sm);
  line-height: 1.5;
  margin: 0.5rem 0;
}

/* Year sections + rows */
.library-row {
  display: grid;
  grid-template-columns: 1.5rem 3.5rem 1fr;
  gap: 0.875rem;
  padding: 0.875rem 0;
  border-top: 1px solid color-mix(in srgb, var(--color-rule) 40%, transparent);
  align-items: start;
}
.library-row:first-of-type { border-top: 1px solid var(--color-rule); }
.library-row-badge {
  font-family: var(--font-ui);
  padding-top: 0.125rem;
}
.library-row-title {
  font-family: var(--font-body);
  font-style: italic;
  font-size: var(--text-base);
  margin: 0;
  line-height: 1.2;
}
.library-row-tags {
  float: right;
  font-family: var(--font-ui);
  font-style: normal;
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  text-transform: lowercase;
}
.library-row-meta {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  margin: 0.125rem 0 0.375rem;
}
.library-row-takeaway {
  font-family: var(--font-body);
  font-style: italic;
  font-size: var(--text-sm);
  line-height: 1.5;
  margin: 0.375rem 0;
}
.library-row-links {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
}
.library-row-links a {
  color: var(--color-burgundy);
  text-decoration: none;
  border-bottom: 1px dotted var(--color-burgundy);
  margin-right: 1rem;
}

.library-spoiler-heavy { color: var(--color-burgundy); }
.library-spoiler-light { color: var(--color-ink-soft); }

/* Up next */
.library-upnext-row {
  font-family: var(--font-body);
  padding: 0.375rem 0;
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
  margin: 0;
}
.library-upnext-row .ttl { font-style: italic; color: var(--color-ink); }

/* Stats line above chips */
.library-stats-line {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
  margin: 1.125rem 0 0.625rem;
}

/* Hidden by filter — UA `[hidden] { display:none }` is overridden by our
   grid display, so re-establish the rule for library rows + year sections. */
.library-row[hidden],
.library-year[hidden] { display: none; }

/* Empty state */
.library-empty {
  font-family: var(--font-body);
  font-style: italic;
  color: var(--color-ink-soft);
  margin-top: 2rem;
}

/* Responsive */
@media (max-width: 720px) {
  .library-umbrella-grid { grid-template-columns: 1fr; }
  .library-currently[data-active-count="2"] .library-currently-grid,
  .library-currently[data-active-count="3"] .library-currently-grid { grid-template-columns: 1fr; }
}
@media (max-width: 480px) {
  .library-row { grid-template-columns: 1.5rem 1fr; }
  .library-row .library-glyph-block { display: none; }
}
```

- [ ] **Step 2: Verify CI contrast still passes**

Run: `python3 tools/check-contrast.py`
Expected: `OK — all pairings pass.`

- [ ] **Step 3: Dev server pass**

Visit `/library/`, `/library/reading/`, `/library/listening/`, `/library/playing/`, `/library/watching/`. Confirm:
- Umbrella renders as 2×2 with proper card chrome.
- Glyph blocks tint per medium (book burgundy, music steel, game evergreen, watching violet).
- Currently-active grid switches between 1-up and 2-up depending on active count.
- Year sections render with rules.
- Status badges colored correctly per status.
- Mobile (resize browser to <720px): umbrella stacks; currently-active stacks; row glyphs hide at <480px.
- Theme toggle (light / dark / system): all elements legible.

- [ ] **Step 4: Commit**

```bash
git add assets/css/main.css
git commit -m "css: §37 Library — umbrella, currently-active, rows, badges, glyph blocks"
```

---

### Task C2: JS entry — `assets/js/entry-library.js`

**Files:**
- Create: `assets/js/entry-library.js`

- [ ] **Step 1: Write the entry**

If Task B9 step 2 used the `bodyAttrs` block successfully, use this version:

```js
// Library section entry — loaded only on /library/<leaf>/ pages.
import { setupFilterChips } from "./filter-chips.js";

const page = document.body.dataset.libraryPage;
if (page) {
  setupFilterChips({
    containerSelector: `.library-chips[data-page="${page}"]`,
    cardSelector: ".library-row",
    sectionSelector: ".library-year",
    emptyStateSelector: ".library-empty",
  });
}
```

If Task B9 step 2 used the `<div data-library-page>` fallback, use this version instead:

```js
// Library section entry — loaded only on /library/<leaf>/ pages.
import { setupFilterChips } from "./filter-chips.js";

const hook = document.querySelector("[data-library-page]");
const page = hook?.dataset?.libraryPage;
if (page) {
  setupFilterChips({
    containerSelector: `.library-chips[data-page="${page}"]`,
    cardSelector: ".library-row",
    sectionSelector: ".library-year",
    emptyStateSelector: ".library-empty",
  });
}
```

- [ ] **Step 2: Commit**

```bash
git add assets/js/entry-library.js
git commit -m "js: entry-library.js dispatches setupFilterChips per page"
```

---

### Task C3: Wire `partials/scripts.html` to load the library bundle

**Files:**
- Modify: `layouts/partials/scripts.html` — append after the works block (after current line 46).

- [ ] **Step 1: Append the dispatch**

Append before the final newline:

```go
{{- /* Library: load entry-library.js on leaf pages only.
       The umbrella (/library/) has no chips and no rows — skip it. */ -}}
{{- $isLibraryLeaf := and (eq .Section "library") (ne .RelPermalink "/library/") -}}
{{- if $isLibraryLeaf }}
{{- $libOpts := dict "targetPath" "js/library.js" "minify" true -}}
{{- $lib := resources.Get "js/entry-library.js" | js.Build $libOpts | fingerprint }}
<script src="{{ $lib.RelPermalink }}" integrity="{{ $lib.Data.Integrity }}" defer></script>
{{- end }}
```

- [ ] **Step 2: Dev server confirm**

Open DevTools Network tab. Visit `/library/` — no `library.<hash>.js` request. Visit `/library/reading/` — confirm `library.<hash>.js` loads. Click a status chip; rows filter correctly; "All" deselects.

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/scripts.html
git commit -m "scripts: load entry-library.js on /library/<leaf>/ pages only"
```

---

## Phase D — wiring (nav, filter-chips config, CI, CLAUDE.md)

### Task D1: Add Library to top nav

**Files:**
- Modify: `layouts/partials/header.html:5-11`

- [ ] **Step 1: Insert library nav item**

Replace lines 5-11:

```go
    {{ range slice
        (dict "url" "/essays/"  "label" "Essays")
        (dict "url" "/garden/"  "label" "Garden")
        (dict "url" "/research/" "label" "Research")
        (dict "url" "/works/"   "label" "Works")
        (dict "url" "/about/"   "label" "About")
    }}
```

with:

```go
    {{ range slice
        (dict "url" "/essays/"  "label" "Essays")
        (dict "url" "/garden/"  "label" "Garden")
        (dict "url" "/research/" "label" "Research")
        (dict "url" "/works/"   "label" "Works")
        (dict "url" "/library/" "label" "Library")
        (dict "url" "/about/"   "label" "About")
    }}
```

- [ ] **Step 2: Dev server check**

Visit any page. Confirm nav now shows Essays · Garden · Research · Works · Library · About. Click `Library` — navigates to `/library/`. Confirm `aria-current="page"` is set on Library when on `/library/*`.

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/header.html
git commit -m "nav: insert Library between Works and About (6 items)"
```

---

### Task D2: Extend `data/filter-chips.yaml`

**Files:**
- Modify: `data/filter-chips.yaml`

- [ ] **Step 1: Append library sections**

Append at the end of the file:

```yaml

library-reading:
  primary_tags: [fiction, non-fiction]
  primary_top_k: 10

library-listening:
  primary_tags: [ambient, jazz]
  primary_top_k: 10

library-playing:
  primary_tags: [puzzle, indie]
  primary_top_k: 10

library-watching:
  primary_tags: [drama, sci-fi]
  primary_top_k: 10
```

- [ ] **Step 2: Verify the existing filter-chips config linter still passes**

Run: `python3 tools/check_filter_chips_config.py`

If it errors that the curated tags aren't found, the linter likely walks `content/<section>/` for tag values — but library tags live in yaml, not content. Check `tools/check_filter_chips_config.py` to confirm: if it has section-aware overrides (per CLAUDE.md "section-path overrides for content/works/<sub>/"), follow that pattern; if not, add a guard so `library-*` keys are skipped from content-walk validation (since the source is yaml).

```bash
python3 tools/check_filter_chips_config.py
```

Expected: passes. If it fails, read `tools/check_filter_chips_config.py` — find where section keys are mapped to content paths, and add a clause that when key starts with `library-`, the source is `data/<page-suffix>.yaml` and validation walks the items' `tags` arrays via `parse_library_yaml`. Add unit test cases to its sibling test file.

- [ ] **Step 3: Commit**

```bash
git add data/filter-chips.yaml tools/check_filter_chips_config.py tools/test_check_filter_chips_config.py
git commit -m "filter-chips: add library-* sections; teach config linter the yaml-source path"
```

(If no changes were needed to the config linter, drop those two paths from the `git add`.)

---

### Task D3: Wire CI for both new linters

**Files:**
- Modify: `.github/workflows/hugo.yaml` — append after the works links steps (current line 86).

- [ ] **Step 1: Append the 4 new steps**

Insert before the `Build with Hugo` step:

```yaml
      - name: Verify library fixtures
        run: python3 tools/check_library_fixtures.py
      - name: Run library fixture linter unit tests
        run: python3 -m unittest tools/test_check_library_fixtures.py -v
      - name: Verify library links
        run: python3 tools/check_library_links.py
      - name: Run library links linter unit tests
        run: python3 -m unittest tools/test_check_library_links.py -v
```

- [ ] **Step 2: Run all linters locally as a sanity rehearsal**

```bash
python3 tools/check-contrast.py && \
python3 tools/check_fixtures.py && python3 -m unittest tools/test_check_fixtures.py -v && \
python3 tools/check_garden_fixtures.py && python3 -m unittest tools/test_check_garden_fixtures.py -v && \
python3 tools/check_garden_links.py && python3 -m unittest tools/test_check_garden_links.py -v && \
python3 tools/check_filter_chips_config.py && python3 -m unittest tools/test_check_filter_chips_config.py -v && \
python3 tools/check_research_fixtures.py && python3 -m unittest tools/test_check_research_fixtures.py -v && \
python3 tools/check_research_links.py && python3 -m unittest tools/test_check_research_links.py -v && \
python3 tools/check_citations.py && python3 -m unittest tools/test_check_citations.py -v && \
python3 tools/check_works_fixtures.py && python3 -m unittest tools/test_check_works_fixtures.py -v && \
python3 tools/check_works_links.py && python3 -m unittest tools/test_check_works_links.py -v && \
python3 tools/check_library_fixtures.py && python3 -m unittest tools/test_check_library_fixtures.py -v && \
python3 tools/check_library_links.py && python3 -m unittest tools/test_check_library_links.py -v
```

Expected: every step prints `OK` or test pass output. Bail at first failure.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "ci: gate library fixtures + cross-links (4 new steps)"
```

---

### Task D4: Update `CLAUDE.md` after slice ships

Defer to the wrap-up step in Phase E so the update reflects the merged state.

---

## Phase E — verification + wrap-up

### Task E1: Run a clean Hugo production build

**Files:** none

- [ ] **Step 1: Kill any running dev server**

Run: `pkill -f "hugo server"; sleep 1`
Expected: silent or "no process found" (both fine).

- [ ] **Step 2: Clean build**

Run: `rm -rf public/ resources/_gen/ && hugo --minify`
Expected: `Total in <time> ms` with no errors. (Per `[[reference_hugo_dev_server_gotcha]]`, never run `hugo --minify` with the dev server alive.)

- [ ] **Step 3: Confirm bundle size for library entry**

Run: `ls -lh public/js/library.*.js`
Expected: ~5 KB (filter-chips.js + tiny dispatcher).

- [ ] **Step 4: Confirm umbrella does NOT load library bundle**

Run: `grep -l "library\." public/library/index.html`
Expected: empty output (no match) — umbrella has no library.js script tag.

- [ ] **Step 5: Confirm leaf pages DO load it**

Run: `grep -lE "js/library\.[a-f0-9]+\.js" public/library/reading/index.html public/library/listening/index.html public/library/playing/index.html public/library/watching/index.html`
Expected: all 4 paths printed.

(No commit — verification only.)

---

### Task E2: Manual dev-server spot-check (per `[[feedback_verify_before_merge]]`)

- [ ] **Step 1: Restart dev server**

Run: `hugo server --buildDrafts`

- [ ] **Step 2: Spot-check checklist**

Open these in order; confirm each:

1. `/` — top nav now shows `Essays · Garden · Research · Works · Library · About`. No layout shift.
2. `/library/` — 4 cards in 2×2 grid (reading / listening / playing / watching). Each card has glyph + stats line + 3 items + "All X →" link. Clicking a link navigates to the correct leaf.
3. `/library/reading/` — currently-reading shows 2 cards with progress bars. Year sections 2026 + 2025 render. "Up next" block at bottom. Status chips filter correctly (single-active across status, AND with tag). Click "All" → all rows back. Click "✓ Finished" → only finished rows.
4. `/library/listening/` — eighth-note glyph (steel). 2 currently-listening cards (no progress bar). Format chip dim shows `album` + `track` (2 chips).
5. `/library/playing/` — gamepad glyph (evergreen). 1 currently-playing "Outer Wilds" card with spoilers:heavy tag. ★ status badge on the 100pct row. Platform chips populated dynamically.
6. `/library/watching/` — clapper glyph (violet). 1 currently-watching series card with progress bar (`ep 4/8`). Format chips show `film` + `series`. Series rows show ep count; film rows show runtime.
7. Cross-links: `/library/reading/` Invisible Cities row has "→ my notes" link (resolves to `/garden/invisible-cities/`). Other rows have only "→ original".
8. Theme toggle: cycle system → light → dark → system. All glyph blocks legible in both modes; status badge colors still distinguishable.
9. Narrow viewport (DevTools mobile): resize to ≤720px — umbrella stacks 1-col; currently-active stacks. Resize to ≤480px — row glyph blocks hide.
10. Disable JS: filter chips become inert (visible but no-op). Page content still renders correctly. Native `<details>` disclosure still opens for the tag dim.

- [ ] **Step 3: Stop the dev server**

Run: `pkill -f "hugo server"`

(No commit yet — fixes go into individual commits, then proceed to Task E3.)

---

### Task E3: Update `CLAUDE.md` to reflect shipped library section

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Refresh the project status block**

Find the "Project status (as of 2026-05-12)" header. Update the bulleted list to include library under shipped. The "Not started" list shrinks: drop "Phase 7 — Library", keep "Phase 7 — Homepage v3" and "Phase 8".

Add a new "Shipped" bullet:

```
- **Library** (Phase 7 first slice): umbrella + 4 list pages (reading / listening / playing / watching); fixture-shaped data/*.yaml per spec §10.4; 2 new hand-authored glyphs (book + clapper); shape+color status badges; per-page filter chips with status / format-or-platform / tag dims; nav adds Library as 6th item.
```

- [ ] **Step 2: Update the JS pipeline table**

Find the multi-entry table under "JS pipeline — multi-entry bundling". Add a row:

```
| `js/entry-library.js` | `library.<hash>.js` (~5 KB) | `.Section == "library"` AND NOT `/library/` | imports `filter-chips.js`; per-leaf pages only |
```

- [ ] **Step 3: Bump the linter pair count**

Find: "Nine linter pairs under `tools/check_*.py` + `tools/test_check_*.py` (CI runs each linter then its unit-test sibling): essay fixtures, garden fixtures, garden links, filter-chips config, research fixtures, research links, citations, works fixtures, works links."

Change to:

```
Eleven linter pairs under `tools/check_*.py` + `tools/test_check_*.py` (CI runs each linter then its unit-test sibling): essay fixtures, garden fixtures, garden links, filter-chips config, research fixtures, research links, citations, works fixtures, works links, library fixtures, library links.
```

- [ ] **Step 4: Add reference to library spec**

Under "Reference docs", add:

```
- **Library spec**: `docs/superpowers/specs/2026-05-12-library-section-design.md`. Phase 7 first slice.
```

- [ ] **Step 5: Add deferred-features rows for library**

Under the "Deferred features" table, add rows for cover thumbnails (target: future library runtime slice; fixture seed: yaml note_slug fields), Last.fm scrobbles (target: gated on author need; fixture seed: listening yaml `extras`), library RSS, `/library/graph/` constellation.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md: refresh after library section slice"
```

---

### Task E4: Hand off to finishing-a-development-branch

- [ ] **Step 1: Confirm clean working tree + branch state**

Run: `git status && git log --oneline master..HEAD`
Expected: clean tree; ~25 commits on `slice/library-section`.

- [ ] **Step 2: Invoke superpowers:finishing-a-development-branch**

The user will choose merge vs PR vs cleanup. Per the prior slice pattern, expect: merge to master (no-ff), push to origin, archive the brainstorm session under `.superpowers/brainstorm/`.

---

## Self-review

**Spec coverage check:**

- §1 Motivation — covered by Phase A through E (whole plan implements it).
- §2 In-scope items — every bullet has a task: 4 list pages (B8–B12), data yamls (A7–A10), 2 SVGs (A2–A3), `layouts/library/` (B8–B12), `partials/library/` (B2–B7), CSS §37 (C1), entry-library.js (C2), linter pairs (A4–A6), Library nav (D1), filter-chips.yaml (D2). Out-of-scope items deliberately not implemented. ✓
- §3.1 Content + layouts — B1 + B8–B12. ✓
- §3.2 Partials — B2–B7. ✓
- §3.3 Data contract — A7–A10 yamls; A4 parser handles shape; A5 validator covers required/allowed fields. ✓
- §3.4 media_type allowlist — A5 `ALLOWED_MEDIA_TYPES`. ✓
- §3.5 Status taxonomy — A5 `ALLOWED_STATUSES`; B2 status-badge partial maps glyphs. ✓
- §3.6 extras shape — A5 `ALLOWED_EXTRAS` + per-key constraints. ✓
- §3.7 Currently-active rules — B6 partial computes layout, progress-bar gate; B9–B12 partition into active. ✓
- §3.8 Year sections — B5 partial; B9–B12 partition by `finished` year. ✓
- §3.9 "Up next" — B9–B12 emit the block from queued items. ✓
- §3.10 Spoiler treatment — B4 row partial inlines burgundy/muted spans. ✓
- §3.11 Empty state — B9–B12 emit `library-empty` when no items; CSS in C1. ✓
- §3.12 Filter chip dimensions — B9–B12 wire dims per page. ✓
- §3.13 Cross-link rules — B4 row partial conditional links; A6 linter validates. ✓
- §3.14 Link label convention — B4 + B6 use "→ X" suffix. ✓
- §4 Visual design — B2–B7 partials + C1 CSS. ✓
- §4.3 Glyph blocks — B3 type-glyph partial + C1 `.book/.music/.game/.watching` modifiers. ✓
- §4.4 CSS section §37 — C1. ✓
- §4.5 Glyph cost (book + clapper) — A2 + A3. ✓
- §5 JS — C2 entry; C3 dispatch. ✓
- §6 Linters — A5 fixtures; A6 links; D3 CI wiring. ✓
- §7 Fixtures — A7–A10. ✓
- §8 Nav — D1. ✓
- §9 Testing — A4–A6 unit tests; E1 production build; E2 manual spot-check. ✓
- §10 Memory references — applied throughout (filler text in fixtures A7–A10, dev-server caveat in E1, link convention in B4/B6, data-tags in B4). ✓
- §11 Acceptance criteria — E1 + E2 verifies each item. ✓

**Placeholder scan:** no TBD, TODO, "implement later", "add error handling", "similar to". Every step has its actual code or command.

**Type consistency:**
- `parse_library_yaml(text)` returns `list[dict[str, object]]` — used consistently in A4, A5, A6.
- `lint_yaml_file(file_name, text)` signature defined in A5; A5 tests + main use it; A6 doesn't reference it.
- `lint.run(repo_root)` returns `(rc, errs)` — defined in A5 and A6; consumed in A6 tests + main.
- CSS class names: `.library-row`, `.library-year`, `.library-empty`, `.library-chips`, `.library-glyph-block`, `.library-status-badge`, `.library-curr-card`, `.library-um-card` — used consistently across B partials, C1 CSS, and C2 JS selectors.
- Body data attribute: `data-library-page` — set in B9–B12, read in C2.
- Per-page dim values match spec §3.5 status enums and §3.6 extras keys.
- File paths use `assets/images/icons/library/{book,clapper}.svg` consistently in A2/A3 and B3.

No issues found.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-12-library-section.md`.

Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session, batch with checkpoints for review.

Which approach?
