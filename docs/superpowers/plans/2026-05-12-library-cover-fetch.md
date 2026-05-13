# Library cover-fetch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the library cover-fetch infrastructure (data shape, Hugo template, fetch script, linter, fair-use posture) with 8 seed real-title fixtures exercising the live cover paths end-to-end. IGDB + TMDB stay stubbed for a future slice.

**Architecture:** Per-medium yaml gains optional cover identifiers (`cover_file` / `cover_url` / `isbn` / `musicbrainz_release_group` / `igdb_id` / `tmdb_id`). An author-driven Python script (`tools/fetch_library_covers.py`, stdlib-only) fetches via the appropriate API and caches to `assets/images/library/covers/<slug>.jpg`. Hugo's `partials/library/type-glyph.html` renders `<img>` when cached; otherwise the existing glyph fallback. A 12th linter pair gates schema + cache coverage + audit-log freshness. Per-section CSS makes the listening leaf square (44×44 / 56×56) while other leaves stay portrait.

**Tech Stack:** Python stdlib (`urllib`, `json`, `pathlib`, `hashlib`, `unittest`); Hugo 0.148.0+ (`resources.Get`); hand-rolled CSS (no PostCSS / Tailwind); existing project YAML helpers (`tools/check_fixtures.py:parse_scalar`).

**Spec:** `docs/superpowers/specs/2026-05-12-library-cover-fetch-design.md`

---

## File Structure

**Create:**
- `tools/fetch_library_covers.py` — author-driven fetch script with 5-way dispatch
- `tools/check_library_covers.py` — 12th project linter
- `tools/test_check_library_covers.py` — linter test sibling
- `tools/test_fetch_library_covers.py` — fetch-script unit tests (mocked HTTP)
- `tools/.fetch-config.json.example` — config template (contact email placeholder)
- `tools/.cover-cache.json` — audit log (committed; populated by script)
- `assets/images/library/covers/wizard-of-oz.jpg` — fixture cover (8 total covers)
- `assets/images/library/covers/pride-and-prejudice.jpg`
- `assets/images/library/covers/brandenburg-concertos.jpg`
- `assets/images/library/covers/the-entertainer.jpg`
- `assets/images/library/covers/hades.jpg`
- `assets/images/library/covers/celeste.jpg`
- `assets/images/library/covers/the-general.jpg`
- `assets/images/library/covers/nosferatu.jpg`

**Modify:**
- `data/reading.yaml` — replace 2 lorem fixtures with Wizard of Oz + Pride and Prejudice
- `data/listening.yaml` — replace 2 lorem fixtures with Brandenburg + The Entertainer
- `data/playing.yaml` — replace 2 lorem fixtures with Hades + Celeste
- `data/watching.yaml` — replace 2 lorem fixtures with The General + Nosferatu
- `tools/check_library_fixtures.py` — accept + validate new optional cover keys
- `tools/test_check_library_fixtures.py` — new cases for valid + invalid cover keys
- `layouts/partials/library/type-glyph.html` — render `<img>` when cached
- `assets/css/main.css` — §37 per-section aspect rules (uses existing `[data-library-page="listening"]`)
- `layouts/partials/footer.html` — colophon credit line
- `.github/workflows/hugo.yaml` — wire 12th linter pair
- `.gitignore` — append `tools/.fetch-config.json`
- `CLAUDE.md` — lint pair count (11→12), deferred-features table, project status, reference docs

---

## Task 1: Fixture-linter schema extension

**Files:**
- Modify: `tools/check_library_fixtures.py`
- Test: `tools/test_check_library_fixtures.py`

- [ ] **Step 1: Read the current fixture linter to find the `extras` validation block**

Run: `grep -n "extras\|validate_\|known_keys" tools/check_library_fixtures.py`

Identify where per-medium `extras` keys are validated and the unknown-key rejection lives.

- [ ] **Step 2: Write failing tests for the 6 new cover keys**

Add to `tools/test_check_library_fixtures.py`:

```python
def test_cover_file_valid(self):
    yaml = dedent("""
    items:
      - slug: wizard-of-oz
        title: The Wonderful Wizard of Oz
        creator: L. Frank Baum
        year: 1900
        media_type: book
        status: finished
        last_modified: 2026-05-12
        extras:
          cover_file: wizard-of-oz.jpg
    """)
    self.assertEqual(run_check(yaml, "reading"), [])

def test_cover_url_valid(self):
    yaml = dedent("""
    items:
      - slug: bach-brandenburg
        title: Brandenburg Concertos
        creator: J.S. Bach
        year: 1721
        media_type: album
        status: finished
        last_modified: 2026-05-12
        extras:
          cover_url: "https://upload.wikimedia.org/.../bach.jpg"
    """)
    self.assertEqual(run_check(yaml, "listening"), [])

def test_isbn_valid_13(self):
    yaml = dedent("""
    items:
      - slug: x
        title: X
        creator: Y
        year: 2020
        media_type: book
        status: finished
        last_modified: 2026-05-12
        extras:
          isbn: "9780156453806"
    """)
    self.assertEqual(run_check(yaml, "reading"), [])

def test_isbn_invalid_format_fails(self):
    yaml = dedent("""
    items:
      - slug: x
        title: X
        creator: Y
        year: 2020
        media_type: book
        status: finished
        last_modified: 2026-05-12
        extras:
          isbn: "not-an-isbn"
    """)
    errs = run_check(yaml, "reading")
    self.assertTrue(any("isbn" in e for e in errs))

def test_igdb_id_positive_int(self):
    # similar pattern — valid 1942, invalid "abc"
    ...

def test_tmdb_id_positive_int(self):
    # similar pattern
    ...

def test_mbid_string(self):
    # any non-empty string is valid; empty string is invalid
    ...

def test_cover_file_must_be_relative(self):
    # "../escape.jpg" and "/abs/path.jpg" must fail
    ...
```

(Reuse existing test-harness helper signatures from the file; the `run_check` shape will be visible in step 1's grep output.)

- [ ] **Step 3: Run tests, confirm they fail**

```
python3 tools/test_check_library_fixtures.py
```

Expected: failures on the new test methods (existing tests still pass).

- [ ] **Step 4: Extend the linter**

In `tools/check_library_fixtures.py`, extend the validation:

```python
COVER_KEYS_UNIVERSAL = {"cover_file", "cover_url"}
COVER_KEYS_BY_MEDIA = {
    "book":   {"isbn"},
    "album":  {"musicbrainz_release_group"},
    "track":  {"musicbrainz_release_group"},
    "game":   {"igdb_id"},
    "film":   {"tmdb_id"},
    "series": {"tmdb_id"},
}

ISBN_RE = re.compile(r"^\d{10}$|^\d{13}$")

def validate_extras_cover_keys(extras: dict, media_type: str, errors: list, ctx: str) -> None:
    allowed = COVER_KEYS_UNIVERSAL | COVER_KEYS_BY_MEDIA.get(media_type, set())
    for key, value in extras.items():
        if key not in allowed:
            continue  # other extras keys handled elsewhere; not our concern
        if key == "isbn":
            if not isinstance(value, str) or not ISBN_RE.match(value):
                errors.append(f"{ctx}: extras.isbn must be 10 or 13 digits, got {value!r}")
        elif key in {"igdb_id", "tmdb_id"}:
            if not isinstance(value, int) or value <= 0:
                errors.append(f"{ctx}: extras.{key} must be a positive integer, got {value!r}")
        elif key == "musicbrainz_release_group":
            if not isinstance(value, str) or not value:
                errors.append(f"{ctx}: extras.musicbrainz_release_group must be a non-empty string")
        elif key == "cover_url":
            parsed = urllib.parse.urlparse(value) if isinstance(value, str) else None
            if not parsed or not parsed.scheme or not parsed.netloc:
                errors.append(f"{ctx}: extras.cover_url must be an absolute URL, got {value!r}")
        elif key == "cover_file":
            if not isinstance(value, str) or "/" in value or ".." in value or not value:
                errors.append(f"{ctx}: extras.cover_file must be a relative filename without '/' or '..', got {value!r}")
```

Wire `validate_extras_cover_keys` into the per-row loop after `extras` is parsed.

Also: extend the existing "unknown extras keys" allow-list to include all 6 new keys per their applicable media types (so unknown-key rejection still catches typos like `cover_files`).

- [ ] **Step 5: Run tests, confirm they pass**

```
python3 tools/test_check_library_fixtures.py
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add tools/check_library_fixtures.py tools/test_check_library_fixtures.py
git commit -m "library: accept cover_file/cover_url/isbn/mbid/igdb_id/tmdb_id in extras"
```

---

## Task 2: Yaml fixtures — 8 real-title entries with cover fields

**Files:**
- Modify: `data/reading.yaml`, `data/listening.yaml`, `data/playing.yaml`, `data/watching.yaml`

No tests in this task — task 1's linter covers schema validation.

- [ ] **Step 1: Identify which 2 lorem entries to replace per leaf**

Run: `grep -n "slug: lorem" data/reading.yaml data/listening.yaml data/playing.yaml data/watching.yaml`

Pick the **last 2 lorem entries** in each leaf (preserves the leading filler entries; replaces tail entries to minimize layout disturbance).

- [ ] **Step 2: Update `data/reading.yaml`**

Replace the 2 selected lorem entries with:

```yaml
  - slug: wizard-of-oz
    title: The Wonderful Wizard of Oz
    creator: L. Frank Baum
    year: 1900
    media_type: book
    status: finished
    started: 2024-11-01
    finished: 2024-11-18
    last_modified: 2026-05-12
    canonical_url: "https://en.wikipedia.org/wiki/The_Wonderful_Wizard_of_Oz"
    preview: "Example notes line one. Lorem ipsum dolor sit amet."
    tags: [fiction, classic]
    extras:
      isbn: "9780486291161"
      cover_url: "https://upload.wikimedia.org/wikipedia/commons/2/27/Wizard_title_page.jpg"

  - slug: pride-and-prejudice
    title: Pride and Prejudice
    creator: Jane Austen
    year: 1813
    media_type: book
    status: finished
    started: 2025-01-04
    finished: 2025-01-22
    last_modified: 2026-05-12
    canonical_url: "https://en.wikipedia.org/wiki/Pride_and_Prejudice"
    preview: "Example notes line two. Lorem ipsum dolor sit amet."
    tags: [fiction, classic]
    extras:
      isbn: "9780141439518"
      cover_url: "https://upload.wikimedia.org/wikipedia/commons/1/17/PrideAndPrejudiceTitlePage.jpg"
```

Keep all surrounding lorem entries intact. Match the existing yaml indentation (2 spaces).

- [ ] **Step 3: Update `data/listening.yaml`**

Replace 2 lorem entries with:

```yaml
  - slug: brandenburg-concertos
    title: Brandenburg Concertos
    creator: Johann Sebastian Bach
    year: 1721
    media_type: album
    status: finished
    last_modified: 2026-05-12
    canonical_url: "https://en.wikipedia.org/wiki/Brandenburg_Concertos"
    preview: "Example notes line one. Lorem ipsum dolor sit amet."
    tags: [classical]
    extras:
      cover_url: "https://upload.wikimedia.org/wikipedia/commons/8/82/BWV1046-1.jpg"

  - slug: the-entertainer
    title: The Entertainer
    creator: Scott Joplin
    year: 1902
    media_type: track
    status: finished
    last_modified: 2026-05-12
    canonical_url: "https://en.wikipedia.org/wiki/The_Entertainer_(rag)"
    preview: "Example notes line two. Lorem ipsum dolor sit amet."
    tags: [ragtime, classical]
    extras:
      cover_url: "https://upload.wikimedia.org/wikipedia/commons/0/0c/TheEntertainer_-_Scott_Joplin.jpg"
```

- [ ] **Step 4: Update `data/playing.yaml`**

Replace 2 lorem entries with:

```yaml
  - slug: hades
    title: Hades
    creator: Supergiant Games
    year: 2020
    media_type: game
    status: finished
    finished: 2024-09-15
    last_modified: 2026-05-12
    canonical_url: "https://www.supergiantgames.com/games/hades"
    preview: "Example notes line one. Lorem ipsum dolor sit amet."
    tags: [roguelike, mythology]
    extras:
      cover_url: "https://upload.wikimedia.org/wikipedia/en/c/cc/Hades_cover_art.jpg"

  - slug: celeste
    title: Celeste
    creator: Maddy Makes Games
    year: 2018
    media_type: game
    status: finished
    finished: 2023-04-02
    last_modified: 2026-05-12
    canonical_url: "https://www.celestegame.com/"
    preview: "Example notes line two. Lorem ipsum dolor sit amet."
    tags: [platformer]
    extras:
      cover_url: "https://upload.wikimedia.org/wikipedia/en/3/3b/Celeste_box_art_full.png"
```

- [ ] **Step 5: Update `data/watching.yaml`**

Replace 2 lorem entries with:

```yaml
  - slug: the-general
    title: The General
    creator: Buster Keaton
    year: 1926
    media_type: film
    status: finished
    finished: 2024-12-29
    last_modified: 2026-05-12
    canonical_url: "https://en.wikipedia.org/wiki/The_General_(1926_film)"
    preview: "Example notes line one. Lorem ipsum dolor sit amet."
    tags: [silent, comedy]
    extras:
      cover_url: "https://upload.wikimedia.org/wikipedia/commons/8/89/The_General_poster.jpg"

  - slug: nosferatu
    title: Nosferatu
    creator: F.W. Murnau
    year: 1922
    media_type: film
    status: finished
    finished: 2025-10-31
    last_modified: 2026-05-12
    canonical_url: "https://en.wikipedia.org/wiki/Nosferatu"
    preview: "Example notes line two. Lorem ipsum dolor sit amet."
    tags: [silent, horror]
    extras:
      cover_url: "https://upload.wikimedia.org/wikipedia/commons/2/2e/Nosferatu_%281922%29_poster.jpg"
```

- [ ] **Step 6: Run the fixture linter to confirm it still passes**

```
python3 tools/check_library_fixtures.py
python3 tools/test_check_library_fixtures.py
```

Expected: 0 errors.

- [ ] **Step 7: Commit**

```bash
git add data/reading.yaml data/listening.yaml data/playing.yaml data/watching.yaml
git commit -m "library: seed 8 real-title fixtures with cover identifiers"
```

---

## Task 3: Fetch-script skeleton + CLI + dry-run

**Files:**
- Create: `tools/fetch_library_covers.py`
- Create: `tools/test_fetch_library_covers.py`

- [ ] **Step 1: Write failing test for CLI argument parsing**

Create `tools/test_fetch_library_covers.py`:

```python
from __future__ import annotations
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import fetch_library_covers as fc

class CliTests(unittest.TestCase):
    def test_default_medium_is_all(self):
        args = fc.parse_args([])
        self.assertEqual(args.medium, "all")
        self.assertFalse(args.force)
        self.assertFalse(args.dry_run)

    def test_medium_flag(self):
        args = fc.parse_args(["--medium", "book"])
        self.assertEqual(args.medium, "book")

    def test_force_flag(self):
        args = fc.parse_args(["--force"])
        self.assertTrue(args.force)

    def test_dry_run_flag(self):
        args = fc.parse_args(["--dry-run"])
        self.assertTrue(args.dry_run)

if __name__ == "__main__":
    unittest.main()
```

Run: `python3 tools/test_fetch_library_covers.py`. Expected: `ModuleNotFoundError: No module named 'fetch_library_covers'`.

- [ ] **Step 2: Write minimal implementation**

Create `tools/fetch_library_covers.py`:

```python
#!/usr/bin/env python3
"""Fetch cover art for library items.

Stdlib-only. Author-driven; not invoked at build time. See:
docs/superpowers/specs/2026-05-12-library-cover-fetch-design.md
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
COVERS_DIR = REPO_ROOT / "assets" / "images" / "library" / "covers"
DATA_DIR   = REPO_ROOT / "data"
AUDIT_LOG  = REPO_ROOT / "tools" / ".cover-cache.json"
CONFIG     = REPO_ROOT / "tools" / ".fetch-config.json"

MEDIA_CHOICES = ("book", "album", "track", "game", "film", "series", "all")
MEDIUM_TO_LEAF = {
    "book":   "reading",
    "album":  "listening",
    "track":  "listening",
    "game":   "playing",
    "film":   "watching",
    "series": "watching",
}

def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch library cover art")
    p.add_argument("--medium", choices=MEDIA_CHOICES, default="all")
    p.add_argument("--force", action="store_true",
                   help="re-fetch even if cache hit")
    p.add_argument("--dry-run", action="store_true",
                   help="print planned actions; no network or disk writes")
    return p.parse_args(argv)

def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    print(f"medium={args.medium} force={args.force} dry_run={args.dry_run}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run tests, confirm CLI tests pass**

```
python3 tools/test_fetch_library_covers.py
```

Expected: 4 tests pass.

- [ ] **Step 4: Commit**

```bash
git add tools/fetch_library_covers.py tools/test_fetch_library_covers.py
git commit -m "library: fetch-script skeleton with CLI + dry-run plumbing"
```

---

## Task 4: Fetch-script yaml loader + source-picker

**Files:**
- Modify: `tools/fetch_library_covers.py`
- Modify: `tools/test_fetch_library_covers.py`

- [ ] **Step 1: Write failing tests for `pick_source`**

Append to `tools/test_fetch_library_covers.py`:

```python
class PickSourceTests(unittest.TestCase):
    def test_cover_file_wins(self):
        item = {"slug": "x", "media_type": "book",
                "extras": {"cover_file": "x.jpg", "cover_url": "https://e/x", "isbn": "9780000000002"}}
        s = fc.pick_source(item)
        self.assertEqual(s, ("cover_file", "x.jpg"))

    def test_cover_url_when_no_file(self):
        item = {"slug": "x", "media_type": "book",
                "extras": {"cover_url": "https://e/x", "isbn": "9780000000002"}}
        self.assertEqual(fc.pick_source(item), ("cover_url", "https://e/x"))

    def test_isbn_book(self):
        item = {"slug": "x", "media_type": "book", "extras": {"isbn": "9780000000002"}}
        self.assertEqual(fc.pick_source(item), ("isbn", "9780000000002"))

    def test_mbid_album(self):
        item = {"slug": "x", "media_type": "album",
                "extras": {"musicbrainz_release_group": "abc-123"}}
        self.assertEqual(fc.pick_source(item), ("mbid", "abc-123"))

    def test_igdb_game(self):
        item = {"slug": "x", "media_type": "game", "extras": {"igdb_id": 1942}}
        self.assertEqual(fc.pick_source(item), ("igdb_id", 1942))

    def test_tmdb_film(self):
        item = {"slug": "x", "media_type": "film", "extras": {"tmdb_id": 95396}}
        self.assertEqual(fc.pick_source(item), ("tmdb_id", 95396))

    def test_no_source_returns_none(self):
        item = {"slug": "x", "media_type": "book", "extras": {}}
        self.assertIsNone(fc.pick_source(item))

    def test_no_extras_returns_none(self):
        item = {"slug": "x", "media_type": "book"}
        self.assertIsNone(fc.pick_source(item))
```

Run: `python3 tools/test_fetch_library_covers.py`. Expected: 8 new failures.

- [ ] **Step 2: Add `pick_source` + yaml loader**

Append to `tools/fetch_library_covers.py`:

```python
# Source priority order. Per-medium ID keys are only consulted for the matching media_type.
MEDIA_TO_ID_KEY = {
    "book":   ("isbn",   "isbn"),
    "album":  ("musicbrainz_release_group", "mbid"),
    "track":  ("musicbrainz_release_group", "mbid"),
    "game":   ("igdb_id", "igdb_id"),
    "film":   ("tmdb_id", "tmdb_id"),
    "series": ("tmdb_id", "tmdb_id"),
}

def pick_source(item: dict) -> tuple[str, object] | None:
    extras = item.get("extras") or {}
    if "cover_file" in extras and extras["cover_file"]:
        return ("cover_file", extras["cover_file"])
    if "cover_url" in extras and extras["cover_url"]:
        return ("cover_url", extras["cover_url"])
    media = item.get("media_type")
    if media in MEDIA_TO_ID_KEY:
        yaml_key, source_kind = MEDIA_TO_ID_KEY[media]
        if yaml_key in extras and extras[yaml_key]:
            return (source_kind, extras[yaml_key])
    return None
```

- [ ] **Step 3: Reuse `tools/check_library_fixtures.py:parse_library_yaml`**

Add a `load_leaf` helper. The existing `parse_library_yaml(text)` function (in `check_library_fixtures.py`) already parses the library yaml shape into `list[dict]` — reuse it directly:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_library_fixtures import parse_library_yaml  # noqa: E402

LEAVES = ("reading", "listening", "playing", "watching")

def load_leaf(leaf: str) -> list[dict]:
    """Parse data/<leaf>.yaml into a list of item dicts.

    Reuses the hand-rolled parser from check_library_fixtures.py
    (the project bans PyYAML; this preserves that contract).
    """
    path = DATA_DIR / f"{leaf}.yaml"
    return parse_library_yaml(path.read_text())
```

- [ ] **Step 4: Write a focused test for `load_leaf` against the actual yaml files**

```python
class LoadLeafTests(unittest.TestCase):
    def test_loads_listening(self):
        items = fc.load_leaf("listening")
        self.assertTrue(len(items) >= 1)
        self.assertIn("slug", items[0])

    def test_loads_reading_with_extras(self):
        items = fc.load_leaf("reading")
        wizard = next((i for i in items if i.get("slug") == "wizard-of-oz"), None)
        self.assertIsNotNone(wizard)
        self.assertEqual(wizard["extras"]["isbn"], "9780486291161")
```

Run: `python3 tools/test_fetch_library_covers.py`. Expected: PickSource tests pass; LoadLeaf tests fail.

- [ ] **Step 5: Run all tests, all pass**

```
python3 tools/test_fetch_library_covers.py
```

- [ ] **Step 6: Commit**

```bash
git add tools/fetch_library_covers.py tools/test_fetch_library_covers.py
git commit -m "library: fetch-script source-picker + yaml loader (reuses project parser)"
```

---

## Task 5: Fetch-script — cover_file dispatch (verify-only)

**Files:**
- Modify: `tools/fetch_library_covers.py`
- Modify: `tools/test_fetch_library_covers.py`

- [ ] **Step 1: Write failing tests**

```python
class CoverFileDispatchTests(unittest.TestCase):
    def test_existing_file_is_ok(self):
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            (covers / "wizard.jpg").write_bytes(b"\xff\xd8\xff\xd9")  # JPEG header
            result = fc.dispatch_cover_file(slug="wizard-of-oz",
                                            cover_file="wizard.jpg",
                                            covers_dir=covers)
            self.assertEqual(result.kind, "cover_file")
            self.assertEqual(result.path.name, "wizard.jpg")
            self.assertTrue(result.cached)

    def test_missing_file_is_error(self):
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_cover_file(slug="x",
                                            cover_file="missing.jpg",
                                            covers_dir=covers)
            self.assertEqual(result.kind, "cover_file")
            self.assertFalse(result.cached)
            self.assertIn("not found", result.error)
```

Add `import tempfile` to the test file.

- [ ] **Step 2: Add a `FetchResult` dataclass + `dispatch_cover_file`**

```python
from dataclasses import dataclass

@dataclass
class FetchResult:
    kind: str
    slug: str
    path: Path | None = None
    cached: bool = False
    error: str | None = None
    sha256: str | None = None

def dispatch_cover_file(*, slug: str, cover_file: str, covers_dir: Path) -> FetchResult:
    target = covers_dir / cover_file
    if target.exists():
        return FetchResult(kind="cover_file", slug=slug, path=target, cached=True)
    return FetchResult(kind="cover_file", slug=slug, path=target,
                       cached=False, error=f"cover_file {cover_file} not found in {covers_dir}")
```

- [ ] **Step 3: Run tests, confirm pass**

```
python3 tools/test_fetch_library_covers.py
```

- [ ] **Step 4: Commit**

```bash
git add tools/fetch_library_covers.py tools/test_fetch_library_covers.py
git commit -m "library: fetch-script cover_file dispatch (verify-only, no fetch)"
```

---

## Task 6: Fetch-script — cover_url dispatch (HTTP download)

**Files:**
- Modify: `tools/fetch_library_covers.py`
- Modify: `tools/test_fetch_library_covers.py`

- [ ] **Step 1: Write failing tests with mocked `urlopen`**

```python
class CoverUrlDispatchTests(unittest.TestCase):
    def test_downloads_to_slug_jpg(self):
        body = b"\xff\xd8\xff\xd9fake-jpeg"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        with unittest.mock.patch("urllib.request.urlopen", return_value=mock_resp) as urlopen, \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_cover_url(slug="wizard-of-oz",
                                            url="https://example.com/x.jpg",
                                            covers_dir=covers,
                                            ua="test-ua/0.1 (test@example.com)",
                                            timeout_s=10)
            self.assertEqual(result.kind, "cover_url")
            self.assertTrue(result.cached)
            self.assertEqual(result.path, covers / "wizard-of-oz.jpg")
            self.assertEqual(result.path.read_bytes(), body)
            # Verify UA header was set
            request = urlopen.call_args.args[0]
            self.assertEqual(request.get_header("User-agent"), "test-ua/0.1 (test@example.com)")
            self.assertEqual(result.sha256, hashlib.sha256(body).hexdigest())

    def test_4xx_returns_error_no_write(self):
        from urllib.error import HTTPError
        err = HTTPError("u", 404, "nf", {}, None)
        with unittest.mock.patch("urllib.request.urlopen", side_effect=err), \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_cover_url(slug="x", url="https://e/x.jpg",
                                            covers_dir=covers,
                                            ua="ua", timeout_s=10)
            self.assertFalse(result.cached)
            self.assertIn("404", result.error)
            self.assertFalse((covers / "x.jpg").exists())

    def test_5xx_retries_once_then_succeeds(self):
        from urllib.error import HTTPError
        body = b"ok"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        err = HTTPError("u", 503, "x", {}, None)
        with unittest.mock.patch("urllib.request.urlopen", side_effect=[err, mock_resp]) as urlopen, \
             unittest.mock.patch("time.sleep") as sleep, \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_cover_url(slug="x", url="https://e/x.jpg",
                                            covers_dir=covers, ua="ua", timeout_s=10)
            self.assertTrue(result.cached)
            self.assertEqual(urlopen.call_count, 2)
            sleep.assert_called()  # 2s backoff between attempts

    def test_5xx_retries_once_then_fails(self):
        from urllib.error import HTTPError
        err = HTTPError("u", 503, "x", {}, None)
        with unittest.mock.patch("urllib.request.urlopen", side_effect=[err, err]) as urlopen, \
             unittest.mock.patch("time.sleep"), \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_cover_url(slug="x", url="https://e/x.jpg",
                                            covers_dir=covers, ua="ua", timeout_s=10)
            self.assertFalse(result.cached)
            self.assertEqual(urlopen.call_count, 2)
            self.assertIn("503", result.error)
```

Add `import hashlib` + `import unittest.mock` + `from urllib.error import HTTPError` to test file as needed.

- [ ] **Step 2: Implement `dispatch_cover_url` + an internal `_download`**

```python
import hashlib
import urllib.error
import urllib.request

RETRY_BACKOFF_S = 2.0

def _download(url: str, ua: str, timeout_s: int) -> bytes:
    """Single GET. Raises urllib.error.HTTPError on non-2xx."""
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read()

def _download_with_retry(url: str, ua: str, timeout_s: int) -> bytes:
    """Download with one retry on 5xx."""
    try:
        return _download(url, ua, timeout_s)
    except urllib.error.HTTPError as e:
        if 500 <= e.code < 600:
            time.sleep(RETRY_BACKOFF_S)
            return _download(url, ua, timeout_s)
        raise

def dispatch_cover_url(*, slug: str, url: str, covers_dir: Path, ua: str, timeout_s: int) -> FetchResult:
    target = covers_dir / f"{slug}.jpg"
    try:
        body = _download_with_retry(url, ua, timeout_s)
    except urllib.error.HTTPError as e:
        return FetchResult(kind="cover_url", slug=slug, path=target,
                           cached=False, error=f"HTTP {e.code}: {url}")
    except urllib.error.URLError as e:
        return FetchResult(kind="cover_url", slug=slug, path=target,
                           cached=False, error=f"URLError: {e.reason} for {url}")
    covers_dir.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return FetchResult(kind="cover_url", slug=slug, path=target,
                       cached=True, sha256=hashlib.sha256(body).hexdigest())
```

Add `import time` if not already imported.

- [ ] **Step 3: Run tests**

```
python3 tools/test_fetch_library_covers.py
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add tools/fetch_library_covers.py tools/test_fetch_library_covers.py
git commit -m "library: fetch-script cover_url dispatch (HTTP + 5xx retry)"
```

---

## Task 7: Fetch-script — isbn → Open Library + mbid → Cover Art Archive

**Files:**
- Modify: `tools/fetch_library_covers.py`
- Modify: `tools/test_fetch_library_covers.py`

- [ ] **Step 1: Write failing tests**

```python
class OpenLibraryDispatchTests(unittest.TestCase):
    def test_isbn_url_construction(self):
        url = fc.openlibrary_url("9780486291161")
        self.assertEqual(url, "https://covers.openlibrary.org/b/isbn/9780486291161-L.jpg")

    def test_dispatch_isbn_downloads(self):
        body = b"jpeg-bytes"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        with unittest.mock.patch("urllib.request.urlopen", return_value=mock_resp) as urlopen, \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_isbn(slug="x", isbn="9780486291161",
                                       covers_dir=covers, ua="ua", timeout_s=10)
            self.assertTrue(result.cached)
            self.assertEqual(result.kind, "isbn")
            self.assertEqual(result.path, covers / "x.jpg")
            self.assertIn("9780486291161-L.jpg", urlopen.call_args.args[0].full_url)

class CoverArtArchiveDispatchTests(unittest.TestCase):
    def test_mbid_url_construction(self):
        url = fc.coverart_archive_url("abc-123-def")
        self.assertEqual(url, "https://coverartarchive.org/release-group/abc-123-def/front-500")

    def test_dispatch_mbid_downloads(self):
        body = b"jpeg-bytes"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        with unittest.mock.patch("urllib.request.urlopen", return_value=mock_resp), \
             tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            result = fc.dispatch_mbid(slug="x", mbid="abc-123",
                                      covers_dir=covers, ua="ua", timeout_s=10)
            self.assertTrue(result.cached)
            self.assertEqual(result.kind, "mbid")
```

- [ ] **Step 2: Implement URL constructors + dispatchers**

```python
def openlibrary_url(isbn: str) -> str:
    return f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

def coverart_archive_url(mbid: str) -> str:
    return f"https://coverartarchive.org/release-group/{mbid}/front-500"

def dispatch_isbn(*, slug: str, isbn: str, covers_dir: Path, ua: str, timeout_s: int) -> FetchResult:
    url = openlibrary_url(isbn)
    result = dispatch_cover_url(slug=slug, url=url, covers_dir=covers_dir, ua=ua, timeout_s=timeout_s)
    return FetchResult(kind="isbn", slug=slug, path=result.path,
                       cached=result.cached, error=result.error, sha256=result.sha256)

def dispatch_mbid(*, slug: str, mbid: str, covers_dir: Path, ua: str, timeout_s: int) -> FetchResult:
    url = coverart_archive_url(mbid)
    result = dispatch_cover_url(slug=slug, url=url, covers_dir=covers_dir, ua=ua, timeout_s=timeout_s)
    return FetchResult(kind="mbid", slug=slug, path=result.path,
                       cached=result.cached, error=result.error, sha256=result.sha256)
```

`urlopen` follows 307s by default — CAA's redirect to S3 just works.

- [ ] **Step 3: Run tests**

```
python3 tools/test_fetch_library_covers.py
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add tools/fetch_library_covers.py tools/test_fetch_library_covers.py
git commit -m "library: fetch-script isbn (Open Library) + mbid (Cover Art Archive) dispatch"
```

---

## Task 8: Fetch-script — IGDB + TMDB stubs

**Files:**
- Modify: `tools/fetch_library_covers.py`
- Modify: `tools/test_fetch_library_covers.py`

- [ ] **Step 1: Write failing tests**

```python
class StubDispatchTests(unittest.TestCase):
    def test_igdb_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError) as cm:
            fc.dispatch_igdb(slug="x", igdb_id=1942,
                             covers_dir=Path("/tmp"), ua="ua", timeout_s=10)
        self.assertIn("IGDB_CLIENT_ID", str(cm.exception))

    def test_tmdb_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError) as cm:
            fc.dispatch_tmdb(slug="x", tmdb_id=95396,
                             covers_dir=Path("/tmp"), ua="ua", timeout_s=10)
        self.assertIn("TMDB_API_KEY", str(cm.exception))
```

- [ ] **Step 2: Implement stubs**

```python
def dispatch_igdb(*, slug: str, igdb_id: int, covers_dir: Path, ua: str, timeout_s: int) -> FetchResult:
    raise NotImplementedError(
        f"IGDB live fetch requires IGDB_CLIENT_ID + IGDB_CLIENT_SECRET; "
        f"rerun when wired (slug={slug}, igdb_id={igdb_id})"
    )

def dispatch_tmdb(*, slug: str, tmdb_id: int, covers_dir: Path, ua: str, timeout_s: int) -> FetchResult:
    raise NotImplementedError(
        f"TMDB live fetch requires TMDB_API_KEY; "
        f"rerun when wired (slug={slug}, tmdb_id={tmdb_id})"
    )
```

- [ ] **Step 3: Run tests**

```
python3 tools/test_fetch_library_covers.py
```

- [ ] **Step 4: Commit**

```bash
git add tools/fetch_library_covers.py tools/test_fetch_library_covers.py
git commit -m "library: fetch-script IGDB + TMDB stubs raise NotImplementedError"
```

---

## Task 9: Fetch-script — main loop + audit log

**Files:**
- Modify: `tools/fetch_library_covers.py`
- Modify: `tools/test_fetch_library_covers.py`
- Create: `tools/.fetch-config.json.example`

- [ ] **Step 1: Write failing tests for main flow + audit-log update**

```python
class MainLoopTests(unittest.TestCase):
    def test_dry_run_makes_no_writes(self):
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td) / "covers"
            audit = Path(td) / "audit.json"
            with unittest.mock.patch.object(fc, "COVERS_DIR", covers), \
                 unittest.mock.patch.object(fc, "AUDIT_LOG", audit), \
                 unittest.mock.patch.object(fc, "load_leaf", return_value=[
                     {"slug": "x", "media_type": "book", "extras": {"isbn": "9780000000002"}}
                 ]):
                rc = fc.main(["--medium", "book", "--dry-run"])
                self.assertEqual(rc, 0)
                self.assertFalse(audit.exists())
                self.assertFalse(covers.exists())

    def test_audit_log_updated_after_fetch(self):
        body = b"\xff\xd8\xff\xd9jpeg"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td) / "covers"
            audit = Path(td) / "audit.json"
            with unittest.mock.patch.object(fc, "COVERS_DIR", covers), \
                 unittest.mock.patch.object(fc, "AUDIT_LOG", audit), \
                 unittest.mock.patch.object(fc, "load_leaf", return_value=[
                     {"slug": "wizard-of-oz", "media_type": "book",
                      "extras": {"cover_url": "https://e/x.jpg"}}
                 ]), \
                 unittest.mock.patch("urllib.request.urlopen", return_value=mock_resp), \
                 unittest.mock.patch("time.sleep"):
                rc = fc.main(["--medium", "book"])
                self.assertEqual(rc, 0)
                self.assertTrue((covers / "wizard-of-oz.jpg").exists())
                log = json.loads(audit.read_text())
                self.assertIn("wizard-of-oz", log)
                self.assertEqual(log["wizard-of-oz"]["source_kind"], "cover_url")
                self.assertEqual(log["wizard-of-oz"]["source"], "https://e/x.jpg")
                self.assertEqual(log["wizard-of-oz"]["sha256"], hashlib.sha256(body).hexdigest())
                self.assertTrue(log["wizard-of-oz"]["fetched_at"].endswith("Z"))

    def test_cache_hit_skips_without_force(self):
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td) / "covers"
            covers.mkdir()
            (covers / "wizard-of-oz.jpg").write_bytes(b"existing")
            audit = Path(td) / "audit.json"
            with unittest.mock.patch.object(fc, "COVERS_DIR", covers), \
                 unittest.mock.patch.object(fc, "AUDIT_LOG", audit), \
                 unittest.mock.patch.object(fc, "load_leaf", return_value=[
                     {"slug": "wizard-of-oz", "media_type": "book",
                      "extras": {"cover_url": "https://e/x.jpg"}}
                 ]), \
                 unittest.mock.patch("urllib.request.urlopen") as urlopen:
                rc = fc.main(["--medium", "book"])
                self.assertEqual(rc, 0)
                urlopen.assert_not_called()
                self.assertEqual((covers / "wizard-of-oz.jpg").read_bytes(), b"existing")

    def test_force_refetches(self):
        body = b"\xff\xd8\xff\xd9new"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td) / "covers"
            covers.mkdir()
            (covers / "wizard-of-oz.jpg").write_bytes(b"old")
            audit = Path(td) / "audit.json"
            with unittest.mock.patch.object(fc, "COVERS_DIR", covers), \
                 unittest.mock.patch.object(fc, "AUDIT_LOG", audit), \
                 unittest.mock.patch.object(fc, "load_leaf", return_value=[
                     {"slug": "wizard-of-oz", "media_type": "book",
                      "extras": {"cover_url": "https://e/x.jpg"}}
                 ]), \
                 unittest.mock.patch("urllib.request.urlopen", return_value=mock_resp) as urlopen, \
                 unittest.mock.patch("time.sleep"):
                rc = fc.main(["--medium", "book", "--force"])
                self.assertEqual(rc, 0)
                urlopen.assert_called_once()
                self.assertEqual((covers / "wizard-of-oz.jpg").read_bytes(), body)

    def test_not_implemented_does_not_abort_loop(self):
        body = b"\xff\xd8\xff\xd9jpeg"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td) / "covers"
            audit = Path(td) / "audit.json"
            with unittest.mock.patch.object(fc, "COVERS_DIR", covers), \
                 unittest.mock.patch.object(fc, "AUDIT_LOG", audit), \
                 unittest.mock.patch.object(fc, "load_leaf", side_effect=lambda leaf: [
                     {"slug": "hades", "media_type": "game", "extras": {"igdb_id": 1942}},
                     {"slug": "ok-game", "media_type": "game",
                      "extras": {"cover_url": "https://e/x.jpg"}},
                 ] if leaf == "playing" else []), \
                 unittest.mock.patch("urllib.request.urlopen", return_value=mock_resp), \
                 unittest.mock.patch("time.sleep"):
                rc = fc.main(["--medium", "game"])
                self.assertEqual(rc, 1)  # stubbed item set rc=1
                self.assertTrue((covers / "ok-game.jpg").exists())
```

- [ ] **Step 2: Implement audit-log helpers**

```python
import datetime

def load_audit_log() -> dict:
    if AUDIT_LOG.exists():
        return json.loads(AUDIT_LOG.read_text())
    return {}

def write_audit_log(log: dict) -> None:
    AUDIT_LOG.write_text(json.dumps(log, indent=2, sort_keys=True) + "\n")

def update_audit_entry(log: dict, slug: str, source_kind: str, source: object, sha256: str) -> None:
    log[slug] = {
        "source_kind": source_kind,
        "source": source,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha256,
    }
```

- [ ] **Step 3: Implement main loop**

```python
def load_config() -> dict:
    if CONFIG.exists():
        return json.loads(CONFIG.read_text())
    return {"contact_email": "anonymous@example.com"}

def build_ua(cfg: dict) -> str:
    return f"a3madkour-site/0.1 ({cfg.get('contact_email', 'anonymous@example.com')})"

PER_SOURCE_SLEEP_MS = {"cover_url": 50, "isbn": 100, "mbid": 250}

def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    cfg = load_config()
    ua = build_ua(cfg)
    audit = load_audit_log()
    rc = 0

    leaves = LEAVES if args.medium == "all" else (MEDIUM_TO_LEAF[args.medium],)
    for leaf in leaves:
        for item in load_leaf(leaf):
            if args.medium != "all" and item.get("media_type") != args.medium:
                continue
            source = pick_source(item)
            if source is None:
                continue
            kind, value = source
            slug = item["slug"]
            target = COVERS_DIR / (value if kind == "cover_file" else f"{slug}.jpg")
            if target.exists() and not args.force:
                continue
            if args.dry_run:
                print(f"[dry-run] {slug}: fetch via {kind} → {target}")
                continue
            try:
                if kind == "cover_file":
                    result = dispatch_cover_file(slug=slug, cover_file=value, covers_dir=COVERS_DIR)
                elif kind == "cover_url":
                    result = dispatch_cover_url(slug=slug, url=value, covers_dir=COVERS_DIR, ua=ua, timeout_s=10)
                elif kind == "isbn":
                    result = dispatch_isbn(slug=slug, isbn=value, covers_dir=COVERS_DIR, ua=ua, timeout_s=10)
                elif kind == "mbid":
                    result = dispatch_mbid(slug=slug, mbid=value, covers_dir=COVERS_DIR, ua=ua, timeout_s=10)
                elif kind == "igdb_id":
                    dispatch_igdb(slug=slug, igdb_id=value, covers_dir=COVERS_DIR, ua=ua, timeout_s=10)
                    continue
                elif kind == "tmdb_id":
                    dispatch_tmdb(slug=slug, tmdb_id=value, covers_dir=COVERS_DIR, ua=ua, timeout_s=10)
                    continue
            except NotImplementedError as e:
                print(f"{slug}: {e}", file=sys.stderr)
                rc = 1
                continue
            if not result.cached:
                print(f"{slug}: {result.error}", file=sys.stderr)
                rc = 1
                continue
            if result.sha256:
                update_audit_entry(audit, slug, kind, value, result.sha256)
            ms = PER_SOURCE_SLEEP_MS.get(kind, 0)
            if ms:
                time.sleep(ms / 1000)

    if not args.dry_run:
        write_audit_log(audit)
    return rc
```

- [ ] **Step 4: Run all tests**

```
python3 tools/test_fetch_library_covers.py
```

Expected: all 5 MainLoopTests pass (plus all earlier classes).

- [ ] **Step 5: Create `tools/.fetch-config.json.example`**

```json
{
  "contact_email": "you@example.com"
}
```

- [ ] **Step 6: Append `tools/.fetch-config.json` to `.gitignore`**

Add this section near the `# Misc` block:

```
# Library cover-fetch config (contact email; commit .example only)
tools/.fetch-config.json
```

- [ ] **Step 7: Commit**

```bash
git add tools/fetch_library_covers.py tools/test_fetch_library_covers.py tools/.fetch-config.json.example .gitignore
git commit -m "library: fetch-script main loop + audit log + config plumbing"
```

---

## Task 10: Run fetch script live; commit covers + audit log

**Files:**
- Create: `tools/.fetch-config.json` (local-only, gitignored)
- Create: 8 cover JPEGs in `assets/images/library/covers/`
- Create: `tools/.cover-cache.json` (committed)

This task hits live Wikipedia URLs. No new code; the prior tasks shipped the script.

- [ ] **Step 1: Create local `.fetch-config.json`**

```bash
cp tools/.fetch-config.json.example tools/.fetch-config.json
# edit tools/.fetch-config.json to set "contact_email" to a real email
```

- [ ] **Step 2: Dry-run first**

```
python3 tools/fetch_library_covers.py --dry-run
```

Expected: prints 8 "[dry-run]" lines (one per real-title fixture) showing the target paths. No files touched.

- [ ] **Step 3: Live run**

```
python3 tools/fetch_library_covers.py
```

Expected:
- 8 cover files appear under `assets/images/library/covers/<slug>.jpg`.
- `tools/.cover-cache.json` written with 8 entries.
- Exit code 0 (no IGDB/TMDB stub paths exercised — all 8 use `cover_url`).
- No stderr output (no failures).

If any URL 404s, swap the URL in the corresponding yaml fixture for an alternate Wikimedia file (`https://commons.wikimedia.org/wiki/Category:Book_covers_by_publisher` etc.) and rerun.

- [ ] **Step 4: Verify cache + audit log**

```
ls -la assets/images/library/covers/
cat tools/.cover-cache.json | python3 -m json.tool | head -30
```

Expected: 8 `.jpg` files; audit log shows `source_kind` / `source` / `fetched_at` / `sha256` per slug.

- [ ] **Step 5: Commit**

```bash
git add assets/images/library/covers/ tools/.cover-cache.json
git commit -m "library: seed 8 PD/fair-use cover thumbnails via fetch script"
```

---

## Task 11: Linter — `tools/check_library_covers.py` (schema + cache coverage + audit consistency + freshness)

**Files:**
- Create: `tools/check_library_covers.py`
- Create: `tools/test_check_library_covers.py`

- [ ] **Step 1: Write failing tests for all 5 check classes**

Create `tools/test_check_library_covers.py`:

```python
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import check_library_covers as clc

class SchemaTests(unittest.TestCase):
    def test_valid_isbn_passes(self):
        errs, warns = clc.check_schema([{"slug":"x","media_type":"book",
                                         "extras":{"isbn":"9780000000002"}}])
        self.assertEqual(errs, [])

    def test_invalid_isbn_fails(self):
        errs, _ = clc.check_schema([{"slug":"x","media_type":"book",
                                      "extras":{"isbn":"abc"}}])
        self.assertTrue(any("isbn" in e for e in errs))

    def test_negative_igdb_fails(self):
        errs, _ = clc.check_schema([{"slug":"x","media_type":"game",
                                      "extras":{"igdb_id":-5}}])
        self.assertTrue(any("igdb_id" in e for e in errs))

    def test_cover_file_with_slash_fails(self):
        errs, _ = clc.check_schema([{"slug":"x","media_type":"book",
                                      "extras":{"cover_file":"../escape.jpg"}}])
        self.assertTrue(any("cover_file" in e for e in errs))

    def test_no_extras_passes_silently(self):
        errs, warns = clc.check_schema([{"slug":"lorem","media_type":"book"}])
        self.assertEqual((errs, warns), ([], []))

class CacheCoverageTests(unittest.TestCase):
    def test_missing_cache_file_warns(self):
        with tempfile.TemporaryDirectory() as td:
            items = [{"slug":"x","media_type":"book",
                      "extras":{"isbn":"9780000000002"}}]
            warns = clc.check_cache_coverage(items, covers_dir=Path(td))
            self.assertTrue(any("x" in w for w in warns))

    def test_cover_file_present_no_warning(self):
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            (covers / "x.jpg").write_bytes(b"j")
            items = [{"slug":"x","media_type":"book",
                      "extras":{"cover_file":"x.jpg"}}]
            self.assertEqual(clc.check_cache_coverage(items, covers_dir=covers), [])

    def test_no_identifier_passes_silently(self):
        with tempfile.TemporaryDirectory() as td:
            items = [{"slug":"lorem","media_type":"book"}]
            self.assertEqual(clc.check_cache_coverage(items, covers_dir=Path(td)), [])

class AuditConsistencyTests(unittest.TestCase):
    def test_sha_match_no_warning(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            body = b"abc"
            (covers / "x.jpg").write_bytes(body)
            audit = {"x":{"source_kind":"cover_url","source":"u","fetched_at":"2026-05-12T00:00:00Z","sha256":hashlib.sha256(body).hexdigest()}}
            self.assertEqual(clc.check_audit_consistency(audit, covers_dir=covers), [])

    def test_sha_mismatch_warns(self):
        with tempfile.TemporaryDirectory() as td:
            covers = Path(td)
            (covers / "x.jpg").write_bytes(b"abc")
            audit = {"x":{"source_kind":"cover_url","source":"u","fetched_at":"2026-05-12T00:00:00Z","sha256":"deadbeef"}}
            warns = clc.check_audit_consistency(audit, covers_dir=covers)
            self.assertTrue(any("sha" in w.lower() for w in warns))

    def test_orphan_audit_entry_warns(self):
        with tempfile.TemporaryDirectory() as td:
            audit = {"missing":{"source_kind":"cover_url","source":"u","fetched_at":"2026-05-12T00:00:00Z","sha256":"x"}}
            warns = clc.check_audit_consistency(audit, covers_dir=Path(td))
            self.assertTrue(any("missing" in w for w in warns))

class FreshnessTests(unittest.TestCase):
    def test_stale_entry_warns(self):
        audit = {"x":{"source_kind":"cover_url","source":"u",
                       "fetched_at":"2020-01-01T00:00:00Z","sha256":"x"}}
        warns = clc.check_freshness(audit, stale_days=365, now_iso="2026-05-12T00:00:00Z")
        self.assertTrue(any("stale" in w.lower() for w in warns))

    def test_fresh_entry_no_warning(self):
        audit = {"x":{"source_kind":"cover_url","source":"u",
                       "fetched_at":"2026-05-01T00:00:00Z","sha256":"x"}}
        warns = clc.check_freshness(audit, stale_days=365, now_iso="2026-05-12T00:00:00Z")
        self.assertEqual(warns, [])

if __name__ == "__main__":
    unittest.main()
```

Run: `python3 tools/test_check_library_covers.py`. Expected: `ModuleNotFoundError`.

- [ ] **Step 2: Implement the linter**

Create `tools/check_library_covers.py`:

```python
#!/usr/bin/env python3
"""Library cover linter.

Validates cover-extras schema (fail), cache coverage (warn),
audit-log consistency (warn), and freshness (warn).
See spec: docs/superpowers/specs/2026-05-12-library-cover-fetch-design.md §9
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Iterable

REPO_ROOT  = Path(__file__).resolve().parent.parent
DATA_DIR   = REPO_ROOT / "data"
COVERS_DIR = REPO_ROOT / "assets" / "images" / "library" / "covers"
AUDIT_LOG  = REPO_ROOT / "tools" / ".cover-cache.json"
LEAVES     = ("reading", "listening", "playing", "watching")

ISBN_RE = re.compile(r"^\d{10}$|^\d{13}$")

COVER_KEYS_UNIVERSAL = {"cover_file", "cover_url"}
COVER_KEYS_BY_MEDIA = {
    "book":   {"isbn"},
    "album":  {"musicbrainz_release_group"},
    "track":  {"musicbrainz_release_group"},
    "game":   {"igdb_id"},
    "film":   {"tmdb_id"},
    "series": {"tmdb_id"},
}

def check_schema(items: Iterable[dict]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    for it in items:
        extras = it.get("extras") or {}
        media  = it.get("media_type")
        slug   = it.get("slug", "<unknown>")
        for key, value in extras.items():
            if key not in COVER_KEYS_UNIVERSAL and key not in COVER_KEYS_BY_MEDIA.get(media, set()):
                continue
            if key == "isbn":
                if not isinstance(value, str) or not ISBN_RE.match(value):
                    errors.append(f"{slug}: extras.isbn must be 10/13 digits, got {value!r}")
            elif key in {"igdb_id", "tmdb_id"}:
                if not isinstance(value, int) or value <= 0:
                    errors.append(f"{slug}: extras.{key} must be positive int, got {value!r}")
            elif key == "musicbrainz_release_group":
                if not isinstance(value, str) or not value:
                    errors.append(f"{slug}: extras.musicbrainz_release_group must be non-empty string")
            elif key == "cover_url":
                p = urllib.parse.urlparse(value) if isinstance(value, str) else None
                if not p or not p.scheme or not p.netloc:
                    errors.append(f"{slug}: extras.cover_url must be absolute URL, got {value!r}")
            elif key == "cover_file":
                if not isinstance(value, str) or "/" in value or ".." in value or not value:
                    errors.append(f"{slug}: extras.cover_file must be relative filename, got {value!r}")
    return errors, []

def check_cache_coverage(items: Iterable[dict], *, covers_dir: Path) -> list[str]:
    warnings: list[str] = []
    for it in items:
        extras = it.get("extras") or {}
        slug = it.get("slug", "<unknown>")
        if "cover_file" in extras and extras["cover_file"]:
            target = covers_dir / extras["cover_file"]
        elif any(k in extras for k in ("cover_url", "isbn", "musicbrainz_release_group", "igdb_id", "tmdb_id")):
            target = covers_dir / f"{slug}.jpg"
        else:
            continue
        if not target.exists():
            warnings.append(f"{slug}: expected cover at {target.relative_to(REPO_ROOT)} — run tools/fetch_library_covers.py")
    return warnings

def check_audit_consistency(audit: dict, *, covers_dir: Path) -> list[str]:
    warnings: list[str] = []
    on_disk = {p.name for p in covers_dir.iterdir() if p.is_file()} if covers_dir.exists() else set()
    for slug, entry in audit.items():
        # Audit slug → cache file (`<slug>.jpg` unless cover_file path; we accept either)
        candidate = covers_dir / f"{slug}.jpg"
        if not candidate.exists():
            warnings.append(f"{slug}: audit entry has no cache file at {candidate.relative_to(REPO_ROOT)}")
            continue
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != entry.get("sha256"):
            warnings.append(f"{slug}: sha256 mismatch — cache differs from audit log")
    return warnings

def check_freshness(audit: dict, *, stale_days: int, now_iso: str | None = None) -> list[str]:
    now = datetime.datetime.fromisoformat(now_iso.replace("Z", "+00:00")) if now_iso \
          else datetime.datetime.now(datetime.timezone.utc)
    warnings: list[str] = []
    for slug, entry in audit.items():
        fetched = datetime.datetime.fromisoformat(entry["fetched_at"].replace("Z", "+00:00"))
        if (now - fetched).days > stale_days:
            warnings.append(f"{slug}: audit entry is stale ({(now - fetched).days} days old)")
    return warnings

def load_audit_log() -> dict:
    if AUDIT_LOG.exists():
        return json.loads(AUDIT_LOG.read_text())
    return {}

def load_all_items() -> list[dict]:
    # Reuse the same yaml loader as fetch_library_covers.load_leaf
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from fetch_library_covers import load_leaf  # noqa: E402
    out = []
    for leaf in LEAVES:
        out.extend(load_leaf(leaf))
    return out

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stale-days", type=int, default=365)
    args = ap.parse_args(argv)
    items = load_all_items()
    audit = load_audit_log()
    errs, _ = check_schema(items)
    warns = []
    warns += check_cache_coverage(items, covers_dir=COVERS_DIR)
    warns += check_audit_consistency(audit, covers_dir=COVERS_DIR)
    warns += check_freshness(audit, stale_days=args.stale_days)
    for e in errs:
        print(f"ERROR: {e}", file=sys.stderr)
    for w in warns:
        print(f"WARN:  {w}", file=sys.stderr)
    if errs:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run tests, confirm pass**

```
python3 tools/test_check_library_covers.py
```

- [ ] **Step 4: Run the linter against the real repo**

```
python3 tools/check_library_covers.py
```

Expected: exit 0; no errors, no warnings (since Task 10 populated the cache + audit log).

- [ ] **Step 5: Commit**

```bash
git add tools/check_library_covers.py tools/test_check_library_covers.py
git commit -m "library: 12th linter pair — cover schema + cache + audit consistency"
```

---

## Task 12: Hugo template — `<img>` with fallback

**Files:**
- Modify: `layouts/partials/library/type-glyph.html`

No automated tests in this task — Hugo template behavior is verified via the dev-server spot-check in the final task.

- [ ] **Step 1: Inspect the current template**

```
cat layouts/partials/library/type-glyph.html
```

(Already read; documented in spec §6.)

- [ ] **Step 2: Replace template body**

Overwrite `layouts/partials/library/type-glyph.html` with:

```hugo
{{- /* Type glyph in tinted block OR <img> when cover cached. Inputs:
       .media_type, .size ("large"/"mini"), .slug, .extras (optional)
       Cover resolution: extras.cover_file > <slug>.jpg fallback.
       See: docs/superpowers/specs/2026-05-12-library-cover-fetch-design.md §6 */ -}}
{{- $mt := .media_type -}}
{{- $size := .size | default "mini" -}}
{{- $slug := .slug -}}
{{- $extras := .extras | default dict -}}
{{- $coverFile := index $extras "cover_file" -}}
{{- $coverPath := "" -}}
{{- if $coverFile -}}
  {{- $coverPath = printf "images/library/covers/%s" $coverFile -}}
{{- else if $slug -}}
  {{- $coverPath = printf "images/library/covers/%s.jpg" $slug -}}
{{- end -}}
{{- $cover := "" -}}
{{- if $coverPath -}}{{- $cover = resources.Get $coverPath -}}{{- end -}}
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
{{- $cls := "library-glyph-block" -}}
{{- if eq $size "large" -}}{{- $cls = printf "%s is-large" $cls -}}{{- end -}}
{{- if $cover -}}
  <span class="library-cover-block {{ $size }} {{ $modifier }}">
    <img class="library-cover" src="{{ $cover.RelPermalink }}" alt="" loading="lazy" />
  </span>
{{- else -}}
  <span class="{{ $cls }} {{ $modifier }}" aria-hidden="true">
    {{- with resources.Get $iconPath -}}{{- .Content | safeHTML -}}{{- end -}}
  </span>
{{- end -}}
```

- [ ] **Step 3: Verify callers of `type-glyph.html` pass `slug` + `extras`**

```
grep -rn "type-glyph.html" layouts/
```

For each call site, confirm the `dict` passed in includes `slug` and `extras`. If a caller doesn't pass them, add them — the template falls back to glyph if either is missing, so additions are safe.

Likely call sites (based on `partials/library/`): `row.html`, `currently-active.html`, `umbrella-card.html`.

- [ ] **Step 4: Boot the dev server and verify build doesn't fail**

```
hugo server --buildDrafts
```

Open `http://localhost:1313/library/reading/`. Wizard of Oz + Pride and Prejudice rows should show real cover thumbnails; other rows show the original glyph fallback.

Kill the dev server after spot-checking.

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/library/type-glyph.html
# also any caller dict updates from step 3
git commit -m "library: type-glyph renders <img> when cover cached, glyph otherwise"
```

---

## Task 13: CSS — per-section aspect rules in §37

**Files:**
- Modify: `assets/css/main.css` (§37 Library)

- [ ] **Step 1: Locate §37 in main.css**

```
grep -n "^/\* §37" assets/css/main.css
```

Insert the new rules immediately after the existing `.library-glyph-block` rules in §37. Read the existing block first so the new selectors slot in coherently.

- [ ] **Step 2: Add cover-block + per-section aspect rules**

```css
/* §37.x — Cover thumbnails (per-section native aspect)
   Listening leaf uses [data-library-page="listening"] from layouts/library-listening/list.html. */
.library-cover-block { display: inline-block; overflow: hidden; border-radius: 3px; vertical-align: top; }
.library-cover-block.mini  { width: 44px; height: 56px; }
.library-cover-block.large { width: 56px; height: 72px; }
.library-cover { width: 100%; height: 100%; object-fit: cover; display: block; }

/* listening leaf: square tiles for both glyph and cover */
[data-library-page="listening"] .library-cover-block.mini,
[data-library-page="listening"] .library-glyph-block.mini   { width: 44px; height: 44px; }
[data-library-page="listening"] .library-cover-block.large,
[data-library-page="listening"] .library-glyph-block.is-large { width: 56px; height: 56px; }
```

(Note the `.is-large` modifier on glyph — confirm exact class name when inserting. From `type-glyph.html` line 8: `$cls = printf "%s is-large" $cls`. The `.library-cover-block` uses `.large` per spec; glyph uses `.is-large`. Selectors differ; that's intentional. Update the selector if mismatched on inspection.)

- [ ] **Step 3: Run the contrast linter (sanity — no token changes, so it should still pass)**

```
python3 tools/check-contrast.py
```

Expected: pass.

- [ ] **Step 4: Boot dev server, spot-check listening leaf**

```
hugo server --buildDrafts
```

Open `http://localhost:1313/library/listening/`. Brandenburg + Joplin rows should be **square** cover thumbnails (not portrait). Glyph fallback rows on the same page should also be square. Other leaves stay portrait.

- [ ] **Step 5: Commit**

```bash
git add assets/css/main.css
git commit -m "css: §37 cover-block + per-section aspect (listening square)"
```

---

## Task 14: Colophon credit line

**Files:**
- Modify: `layouts/partials/footer.html`

- [ ] **Step 1: Read footer.html**

```
cat layouts/partials/footer.html
```

- [ ] **Step 2: Add the credit line**

Modify `layouts/partials/footer.html`: insert a new `<p>` immediately after the existing `.colophon` paragraph:

```html
<p class="colophon-covers">
  Cover art via Open Library, Cover Art Archive, IGDB, and TMDB.
  Copyright respective publishers; reproduced under fair use for non-commercial commentary.
</p>
```

- [ ] **Step 3: Boot dev server, eyeball footer**

```
hugo server --buildDrafts
```

Open any page; scroll to footer. New line should appear under the existing colophon. Both light + dark modes; confirm contrast looks correct (no new tokens introduced — it inherits `.colophon`-style typography).

- [ ] **Step 4: Commit**

```bash
git add layouts/partials/footer.html
git commit -m "footer: add cover-art fair-use credit line"
```

---

## Task 15: CI — wire 12th linter pair

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Find the lint job**

```
grep -n "check_library_links\|check_library_fixtures" .github/workflows/hugo.yaml
```

The new pair sits next to the existing library linters.

- [ ] **Step 2: Append two steps**

After the existing `check_library_links` + `test_check_library_links` block, append:

```yaml
      - name: Check library covers schema + cache coverage
        run: python3 tools/check_library_covers.py
      - name: Test library cover linter
        run: python3 tools/test_check_library_covers.py
```

(Match the existing step's `name:` casing convention and indentation when inserting.)

- [ ] **Step 3: Locally rehearse CI invocations**

```
python3 tools/check_library_covers.py && echo "ok"
python3 tools/test_check_library_covers.py && echo "ok"
```

Both should print `ok`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "ci: gate library cover linter + test sibling (12th pair)"
```

---

## Task 16: CLAUDE.md bookkeeping

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update lint-pair count + verification-step count**

Find the line "Eleven linter pairs under `tools/check_*.py`" (or similar — verify exact wording first via `grep -n "linter pair" CLAUDE.md`). Change "Eleven" → "Twelve". Update the parenthetical that lists them to include "library covers".

Find the line about 11 → CI runs `python ...` (or the 23-verification-step language). Change "11 linter pairs = 23 verification steps" → "12 linter pairs = 25 verification steps".

- [ ] **Step 2: Update deferred-features table**

Find the row "Library cover thumbnails ... type-glyph stand-ins ship now". Change to:

```
| Library cover thumbnails (book / album / game / film / series) | Infra shipped 2026-05-12; live IGDB/TMDB paths land with elisp or real items | yaml `extras` accepts `isbn` / `mbid` / `igdb_id` / `tmdb_id` / `cover_url` / `cover_file`; 8 fixtures seeded |
```

- [ ] **Step 3: Update project-status timeline**

In the "Shipped — Phases 0–6 plus targeted polish" section, append after the library bullet:

```
- **Library cover-fetch** (Phase 7 Slice 1): cover infra (data shape, Hugo `<img>` fallback, fetch script, 12th linter pair, audit log) and 8 seed PD/fair-use covers; live IGDB/TMDB paths stubbed (NotImplementedError) until real items + API keys land.
```

- [ ] **Step 4: Update reference docs section**

Find the "Library cover-fetch sketch (deferred future slice)" line. Replace with:

```
- **Library cover-fetch spec**: `docs/superpowers/specs/2026-05-12-library-cover-fetch-design.md`. Phase 7 Slice 1 (infra shipped; IGDB + TMDB live paths deferred).
```

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md: refresh after library cover-fetch shipped (Phase 7 Slice 1)"
```

---

## Task 17: Final dev-server spot-check + production build sanity

**Files:** none modified

- [ ] **Step 1: Boot dev server**

```
hugo server --buildDrafts
```

- [ ] **Step 2: Walk the 4 library leaves + umbrella**

Visit each in turn:

- `/library/` (umbrella)
- `/library/reading/` — Wizard + P&P show covers; Lorem entries show glyph
- `/library/listening/` — Bach + Joplin show **square** covers; Lorem entries show **square** glyphs; existing Koyaanisqatsi entry shows square glyph (no cover yet — that's OK)
- `/library/playing/` — Hades + Celeste show covers; Lorem entries show glyph
- `/library/watching/` — The General + Nosferatu show covers; Lorem entries show glyph

For each: light + dark modes. Verify:
- Covers render at the expected dimensions (44×56 / 56×72 portrait; 44×44 / 56×56 square for listening).
- Glyph fallback rows don't shift layout vs. cover rows (heights match within a section).
- Filter chips still function (status / format / tag dimensions).
- Footer shows the new fair-use credit line.

- [ ] **Step 3: Run all linters one more time**

```
python3 tools/check-contrast.py
python3 tools/check_fixtures.py
python3 tools/test_check_fixtures.py
python3 tools/check_garden_fixtures.py
python3 tools/test_check_garden_fixtures.py
python3 tools/check_garden_links.py
python3 tools/test_check_garden_links.py
python3 tools/check_filter_chips_config.py
python3 tools/test_check_filter_chips_config.py
python3 tools/check_research_fixtures.py
python3 tools/test_check_research_fixtures.py
python3 tools/check_research_links.py
python3 tools/test_check_research_links.py
python3 tools/check_citations.py
python3 tools/test_check_citations.py
python3 tools/check_works_fixtures.py
python3 tools/test_check_works_fixtures.py
python3 tools/check_works_links.py
python3 tools/test_check_works_links.py
python3 tools/check_library_fixtures.py
python3 tools/test_check_library_fixtures.py
python3 tools/check_library_links.py
python3 tools/test_check_library_links.py
python3 tools/check_library_covers.py
python3 tools/test_check_library_covers.py
```

All should exit 0.

- [ ] **Step 4: Kill dev server before production build**

(Required — per `[[reference_hugo_dev_server_gotcha]]`: `hugo --minify` with an active dev server poisons the CSS via MIME mismatch.)

- [ ] **Step 5: Production build**

```
rm -rf public/
hugo --minify
```

Expected: builds cleanly, no warnings about missing assets.

- [ ] **Step 6: Verify cover files landed in `public/`**

```
ls public/images/library/covers/
```

Expected: 8 cover files with Hugo's fingerprinted filenames.

- [ ] **Step 7: Spot-check the production HTML**

```
grep -l "library-cover" public/library/*/index.html
```

Expected: 4 leaves have at least one `library-cover` reference each.

- [ ] **Step 8: No commit needed for this task**

If everything passed, the slice is ready for the user's merge spot-check (per `[[feedback_verify_before_merge]]` — surface the dev-server URL + "what to eyeball" list).
