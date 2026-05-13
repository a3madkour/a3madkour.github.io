# Phase 8 — Slice 1: Pagefind runtime implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a custom site-wide search modal powered by Pagefind. Modal opens on `/` keypress or header icon click; lazy-loads the Pagefind low-level JS API; renders results grouped by section with badges, spoiler-aware indicator, and keyboard navigation.

**Architecture:** Pagefind binary installed in CI, indexes `public/` post-`hugo --minify` into `public/pagefind/` (gitignored). Every layout's `<main>` (in `baseof.html`) gets `data-pagefind-body`; each layout emits page-level `data-pagefind-meta` (section, date, status, etc.) on the outermost content wrapper. The `spoiler` shortcode adds `data-pagefind-ignore` on `.spoiler-body`. A new bundle entry `entry-search.js` (output `search.<hash>.js`) loads on every page; the module dynamically `import()`s `/pagefind/pagefind.js` on first modal open. Modal markup lives in a new `layouts/partials/search-modal.html`, included once in `baseof.html`. CSS lives in a new `assets/css/main.css` §42.

**Tech Stack:** Hugo extended ≥ 0.148.0, hand-rolled CSS, vanilla JS bundled via Hugo's `js.Build`, Pagefind ≥ 1.x (Rust binary, downloaded in CI), Python stdlib only for new linter.

**Parent spec:** `docs/superpowers/specs/2026-05-13-phase-8-design.md` §2 (Slice 1).

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `.gitignore` | Modify | Add `public/pagefind/` line (CI-regenerated). |
| `layouts/shortcodes/spoiler.html` | Modify | Add `data-pagefind-ignore` on the `.spoiler-body` div. |
| `assets/images/icons/search.svg` | Create | Hand-authored magnifier-glass icon (stroke-based, `currentColor`). |
| `layouts/_default/baseof.html` | Modify | Add `data-pagefind-body` on `<main>`; include `search-modal.html` once. |
| `layouts/_default/single.html` | Modify | Emit `data-pagefind-meta` on outer content wrapper (essays / garden notes / works subtypes / research subtypes). |
| `layouts/_default/list.html` | Modify | Emit `data-pagefind-meta` on outer content wrapper (essays index / garden index / works umbrellas / library leaves). |
| `layouts/home.html` | Modify | Emit `data-pagefind-meta="section:home"` on outer wrapper. |
| `layouts/about/single.html` | Modify | Emit `data-pagefind-meta="section:about"`. |
| `layouts/research-theme/single.html` | Modify | Emit `data-pagefind-meta="section:research,subtype:theme,status:…"`. |
| `layouts/research-question/single.html` | Modify | Emit `data-pagefind-meta="section:research,subtype:question,status:…"`. |
| `layouts/works-games/single.html` | Modify | Emit `data-pagefind-meta="section:works,medium:game"`. |
| `layouts/works-music/single.html` | Modify | Emit `data-pagefind-meta="section:works,medium:music"`. |
| `layouts/works-poetry/single.html` | Modify | Emit `data-pagefind-meta="section:works,medium:poetry"`. |
| `layouts/library-reading/list.html` | Modify | Emit `data-pagefind-meta="section:library,medium:book"`. |
| `layouts/library-listening/list.html` | Modify | Emit `data-pagefind-meta="section:library,medium:album"`. |
| `layouts/library-playing/list.html` | Modify | Emit `data-pagefind-meta="section:library,medium:game"`. |
| `layouts/library-watching/list.html` | Modify | Emit `data-pagefind-meta="section:library,medium:film_or_series"`. |
| `tools/check_pagefind_meta.py` | Create | Walks `public/` post-build; asserts `data-pagefind-body` on `<main>` and required `data-pagefind-meta` keys per section. |
| `tools/test_check_pagefind_meta.py` | Create | Unit-test sibling using synthetic HTML strings. |
| `layouts/partials/search-modal.html` | Create | `<dialog>`-based modal markup; input, filter chip strip, results region, kbd-hints footer. |
| `layouts/partials/header.html` | Modify | Add `<button data-search-toggle>` between RSS link and theme toggle. |
| `layouts/partials/scripts.html` | Modify | Add `entry-search.js` build + script tag (loaded on every page). |
| `assets/js/entry-search.js` | Create | Bundle entry; imports `./search.js`. |
| `assets/js/search.js` | Create | Modal logic + Pagefind low-level API integration + keyboard nav. |
| `assets/css/main.css` | Append | §42 search modal styles. |
| `.github/workflows/hugo.yaml` | Modify | Install Pagefind binary; run `pagefind --site public/` post-build; run new linter pair. |
| `CLAUDE.md` | Modify | Refresh §JS pipeline table, §Architecture overview, §Project status. |

---

## Working Directory & Branch

Work happens on a slice branch `slice/phase-8-pagefind` off `master`. Before Task 1:

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git checkout -b slice/phase-8-pagefind
```

All task commits land on this branch. Final merge happens via the slice-finishing flow in Task 15 after the dev-server spot-check in Task 13.

---

### Task 1: Branch + .gitignore + spoiler ignore attr

**Files:**
- Modify: `.gitignore`
- Modify: `layouts/shortcodes/spoiler.html`

- [ ] **Step 1: Create slice branch**

```bash
git checkout master
git pull origin master
git checkout -b slice/phase-8-pagefind
```

- [ ] **Step 2: Read current `.gitignore`**

Run: `cat .gitignore`
Expected: lists existing entries (e.g., `public/`, `node_modules/`, `.hugo_build.lock`).

- [ ] **Step 3: Add `public/pagefind/` to `.gitignore`**

Append a new line `public/pagefind/` at the end of the file (under a comment header if the file uses one; otherwise plain).

Final state addition:
```
# Pagefind index (regenerated in CI; see .github/workflows/hugo.yaml)
public/pagefind/
```

(Note: `public/` is likely already gitignored at the repo root, so this line is for documentation + future-proofing if a user ever uncomments `public/`. Keep it.)

- [ ] **Step 4: Modify `layouts/shortcodes/spoiler.html` to add `data-pagefind-ignore`**

Current line 11:
```html
  <div class="spoiler-body">{{ .Inner | markdownify }}</div>
```

Change to:
```html
  <div class="spoiler-body" data-pagefind-ignore>{{ .Inner | markdownify }}</div>
```

- [ ] **Step 5: Commit**

```bash
git add .gitignore layouts/shortcodes/spoiler.html
git commit -m "pagefind: ignore index dir + skip spoiler bodies"
```

---

### Task 2: Hand-author search icon SVG

**Files:**
- Create: `assets/images/icons/search.svg`

- [ ] **Step 1: Inspect existing icon style**

Run: `head -5 assets/images/icons/rss.svg && echo "---" && head -5 assets/images/icons/sun.svg`
Expected: both files are simple SVGs with `currentColor` strokes, no fills, ~20-24px viewBox.

- [ ] **Step 2: Create `assets/images/icons/search.svg`**

Write the file:

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <circle cx="11" cy="11" r="7"/>
  <line x1="16.5" y1="16.5" x2="21" y2="21"/>
</svg>
```

- [ ] **Step 3: Verify rendering**

Run: `hugo server --buildDrafts` in background; open `http://localhost:1313/` and verify any page renders without console errors. (The icon isn't wired in yet — this is just a sanity check that the file parses.)

Run: `xmllint --noout assets/images/icons/search.svg` (if `xmllint` available) — expected exit code 0.
If `xmllint` not present, skip; the inline embed in Task 8 will surface any parse error at build time.

- [ ] **Step 4: Commit**

```bash
git add assets/images/icons/search.svg
git commit -m "pagefind: hand-authored search.svg icon"
```

---

### Task 3: Pagefind metadata linter — unit-test sibling (RED)

**Files:**
- Create: `tools/test_check_pagefind_meta.py`

- [ ] **Step 1: Write the failing test file**

Create `tools/test_check_pagefind_meta.py`:

```python
"""Unit tests for tools/check_pagefind_meta.py.

The linter validates that each rendered HTML page under public/ has:
  1. data-pagefind-body on the <main> element.
  2. data-pagefind-meta="section:..." on some element inside <main>.
  3. The 'section' value matches the page's URL prefix (essays, garden,
     research, works, library, about, home).

Tests run against synthetic HTML strings, not a real public/ directory.
"""

import unittest
from pathlib import Path
import tempfile

from check_pagefind_meta import (
    parse_meta,
    section_from_path,
    validate_page,
    PagefindMetaError,
)


class TestSectionFromPath(unittest.TestCase):
    def test_homepage(self):
        self.assertEqual(section_from_path("/"), "home")

    def test_essays_index(self):
        self.assertEqual(section_from_path("/essays/"), "essays")

    def test_essay_post(self):
        self.assertEqual(section_from_path("/essays/example-1/"), "essays")

    def test_garden_note(self):
        self.assertEqual(section_from_path("/garden/example-2/"), "garden")

    def test_research_theme(self):
        self.assertEqual(
            section_from_path("/research/themes/example-theme/"), "research"
        )

    def test_works_game(self):
        self.assertEqual(
            section_from_path("/works/games/example-game/"), "works"
        )

    def test_library_leaf(self):
        self.assertEqual(section_from_path("/library/reading/"), "library")

    def test_about(self):
        self.assertEqual(section_from_path("/about/"), "about")


class TestParseMeta(unittest.TestCase):
    def test_extracts_section_key(self):
        html = '<article data-pagefind-meta="section:essays,date:2026-01-01">x</article>'
        meta = parse_meta(html)
        self.assertEqual(meta.get("section"), "essays")
        self.assertEqual(meta.get("date"), "2026-01-01")

    def test_missing_meta_returns_empty_dict(self):
        html = "<article>x</article>"
        self.assertEqual(parse_meta(html), {})

    def test_handles_whitespace_in_values(self):
        html = '<article data-pagefind-meta="section: essays , medium: book ">x</article>'
        meta = parse_meta(html)
        self.assertEqual(meta.get("section"), "essays")
        self.assertEqual(meta.get("medium"), "book")


class TestValidatePage(unittest.TestCase):
    def _write_html(self, dirpath: Path, url: str, html: str) -> Path:
        # url like "/essays/example-1/" → file at <dirpath>/essays/example-1/index.html
        rel = url.strip("/")
        target = dirpath / rel / "index.html" if rel else dirpath / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        return target

    def test_valid_page_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            html = (
                "<html><body><main data-pagefind-body>"
                '<article data-pagefind-meta="section:essays,date:2026-01-01">body</article>'
                "</main></body></html>"
            )
            f = self._write_html(public, "/essays/example-1/", html)
            errs = validate_page(f, public)
            self.assertEqual(errs, [])

    def test_missing_pagefind_body_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            html = (
                "<html><body><main>"
                '<article data-pagefind-meta="section:essays">body</article>'
                "</main></body></html>"
            )
            f = self._write_html(public, "/essays/example-1/", html)
            errs = validate_page(f, public)
            self.assertTrue(any("data-pagefind-body" in e for e in errs))

    def test_missing_section_meta_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            html = (
                "<html><body><main data-pagefind-body>"
                "<article>body without meta</article>"
                "</main></body></html>"
            )
            f = self._write_html(public, "/essays/example-1/", html)
            errs = validate_page(f, public)
            self.assertTrue(any("section" in e for e in errs))

    def test_section_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            html = (
                "<html><body><main data-pagefind-body>"
                '<article data-pagefind-meta="section:garden">body</article>'
                "</main></body></html>"
            )
            f = self._write_html(public, "/essays/example-1/", html)
            errs = validate_page(f, public)
            self.assertTrue(any("section mismatch" in e.lower() for e in errs))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests; expect failure (module doesn't exist yet)**

Run: `python3 -m unittest tools/test_check_pagefind_meta.py -v`
Expected: `ModuleNotFoundError: No module named 'check_pagefind_meta'` (or similar import error).

- [ ] **Step 3: Commit failing tests**

```bash
git add tools/test_check_pagefind_meta.py
git commit -m "pagefind: add metadata linter test sibling (failing)"
```

---

### Task 4: Pagefind metadata linter — implementation (GREEN)

**Files:**
- Create: `tools/check_pagefind_meta.py`

- [ ] **Step 1: Write the linter**

Create `tools/check_pagefind_meta.py`:

```python
"""Validate that every rendered HTML page in public/ carries the Pagefind
metadata the search modal depends on.

Checks per page:
  1. <main data-pagefind-body> is present.
  2. Some element inside <main> carries data-pagefind-meta with a 'section' key.
  3. The 'section' value matches what the URL prefix implies.

This linter runs in CI after `hugo --minify` builds public/. It is paired
with tools/test_check_pagefind_meta.py (unit-tested logic on synthetic HTML).
"""

import re
import sys
from pathlib import Path


# URL-prefix → section mapping. Order matters: longer prefixes win.
SECTION_BY_PREFIX = [
    ("/essays/",   "essays"),
    ("/garden/",   "garden"),
    ("/research/", "research"),
    ("/works/",    "works"),
    ("/library/",  "library"),
    ("/about/",    "about"),
    ("/",          "home"),
]

# Pages we skip — taxonomy pages, RSS, /tags/, /series/, /404.html, etc.
# Pagefind ignores them too (no data-pagefind-body), so the linter mustn't
# fail on their absence.
SKIP_PREFIXES = [
    "/tags/",
    "/series/",
    "/categories/",
]
SKIP_FILES = [
    "/index.xml",   # RSS feed (XML, not indexed)
    "/sitemap.xml",
    "/404.html",
]


class PagefindMetaError(Exception):
    pass


def parse_meta(html: str) -> dict:
    """Extract data-pagefind-meta="..." kv pairs from the first occurrence."""
    m = re.search(r'data-pagefind-meta\s*=\s*"([^"]*)"', html)
    if not m:
        return {}
    out = {}
    for pair in m.group(1).split(","):
        if ":" not in pair:
            continue
        k, v = pair.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def section_from_path(url_path: str) -> str:
    for prefix, section in SECTION_BY_PREFIX:
        if url_path.startswith(prefix):
            return section
    return ""


def url_from_file(file: Path, public: Path) -> str:
    rel = file.relative_to(public)
    parts = rel.parts
    if parts == ("index.html",):
        return "/"
    # .../foo/index.html → /foo/
    if parts[-1] == "index.html":
        return "/" + "/".join(parts[:-1]) + "/"
    return "/" + "/".join(parts)


def should_skip(url_path: str) -> bool:
    for prefix in SKIP_PREFIXES:
        if url_path.startswith(prefix):
            return True
    for f in SKIP_FILES:
        if url_path == f:
            return True
    return False


def validate_page(file: Path, public: Path) -> list:
    url = url_from_file(file, public)
    if should_skip(url):
        return []
    html = file.read_text(encoding="utf-8", errors="replace")

    errors = []
    if not re.search(r"<main[^>]*\bdata-pagefind-body\b", html):
        errors.append(f"{url}: missing data-pagefind-body on <main>")

    meta = parse_meta(html)
    if "section" not in meta:
        errors.append(f"{url}: missing data-pagefind-meta with 'section' key")
        return errors

    expected = section_from_path(url)
    if expected and meta["section"] != expected:
        errors.append(
            f"{url}: section mismatch — meta says '{meta['section']}', "
            f"URL implies '{expected}'"
        )
    return errors


def main() -> int:
    public = Path("public")
    if not public.is_dir():
        print(
            "check_pagefind_meta: public/ not found. Run `hugo --minify` first.",
            file=sys.stderr,
        )
        return 2

    all_errors = []
    for html_file in public.rglob("index.html"):
        all_errors.extend(validate_page(html_file, public))

    if all_errors:
        print(f"check_pagefind_meta: {len(all_errors)} issue(s):", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("check_pagefind_meta: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run unit tests from `tools/` directory (the test imports the module by bare name)**

Run: `cd tools && python3 -m unittest test_check_pagefind_meta.py -v && cd ..`
Expected: all tests pass.

- [ ] **Step 3: Verify linter against a fresh build (still fails — layouts not yet emitting meta)**

Run: `hugo --minify && python3 tools/check_pagefind_meta.py; echo "exit: $?"`
Expected: prints "missing data-pagefind-body" / "missing data-pagefind-meta" errors for many pages; exits with code 1.

Note: this is expected; Tasks 5–11 add the meta on layouts.

- [ ] **Step 4: Commit linter**

```bash
git add tools/check_pagefind_meta.py
git commit -m "pagefind: add metadata linter (paired with test sibling)"
```

---

### Task 5: Add `data-pagefind-body` + metadata to baseof + per-layout

**Files:**
- Modify: `layouts/_default/baseof.html`
- Modify: `layouts/_default/single.html`
- Modify: `layouts/_default/list.html`
- Modify: `layouts/home.html`
- Modify: `layouts/about/single.html`
- Modify: `layouts/research-theme/single.html`
- Modify: `layouts/research-question/single.html`
- Modify: `layouts/works-games/single.html`
- Modify: `layouts/works-music/single.html`
- Modify: `layouts/works-poetry/single.html`
- Modify: `layouts/library-reading/list.html`
- Modify: `layouts/library-listening/list.html`
- Modify: `layouts/library-playing/list.html`
- Modify: `layouts/library-watching/list.html`

- [ ] **Step 1: Add `data-pagefind-body` to `<main>` in baseof**

In `layouts/_default/baseof.html`, change line 7:

```html
      <main>
```

to:

```html
      <main data-pagefind-body>
```

- [ ] **Step 2: Read each per-section layout's `{{ define "main" }}` block to find the outermost wrapper element**

Run: `head -20 layouts/_default/single.html`
Expected: shows the existing `{{ define "main" }}` block.

For each layout below, identify the outermost wrapper element inside `{{ define "main" }}` (e.g., `<article>`, `<section class="essay-post">`, etc.) and append `data-pagefind-meta="..."` to it. The exact attribute value per layout is in the table below.

| Layout file | Wrapper to modify (read the file to confirm exact tag) | Attribute to add |
|---|---|---|
| `layouts/_default/single.html` | outer `<article>` or `<main>` content wrapper | `data-pagefind-meta="section:{{ .Section }},date:{{ .Date.Format "2006-01-02" }}"` |
| `layouts/_default/list.html` | outer wrapper | `data-pagefind-meta="section:{{ .Section }}"` |
| `layouts/home.html` | outer wrapper (likely `<div class="home">`) | `data-pagefind-meta="section:home"` |
| `layouts/about/single.html` | outer wrapper | `data-pagefind-meta="section:about"` |
| `layouts/research-theme/single.html` | outer `<main>` or `<article>` | `data-pagefind-meta="section:research,subtype:theme,status:{{ .Params.status }}"` |
| `layouts/research-question/single.html` | outer wrapper | `data-pagefind-meta="section:research,subtype:question,status:{{ .Params.status }}"` |
| `layouts/works-games/single.html` | outer wrapper | `data-pagefind-meta="section:works,medium:game"` |
| `layouts/works-music/single.html` | outer wrapper | `data-pagefind-meta="section:works,medium:music"` |
| `layouts/works-poetry/single.html` | outer wrapper | `data-pagefind-meta="section:works,medium:poetry"` |
| `layouts/library-reading/list.html` | outer wrapper | `data-pagefind-meta="section:library,medium:book"` |
| `layouts/library-listening/list.html` | outer wrapper | `data-pagefind-meta="section:library,medium:album"` |
| `layouts/library-playing/list.html` | outer wrapper | `data-pagefind-meta="section:library,medium:game"` |
| `layouts/library-watching/list.html` | outer wrapper | `data-pagefind-meta="section:library,medium:film_or_series"` |

**Note on `_default/single.html` vs section-specific single layouts:** if a section has its own `single.html` (e.g., `layouts/works-games/single.html`), that file's `{{ define "main" }}` block overrides `_default/single.html` for that section. The garden + essay sections each use their own single (already in the codebase). For Hugo: check `layouts/essay/`, `layouts/garden/`, `layouts/research/` for section-specific singles; if they exist, add the meta there instead of in `_default/single.html`.

Run: `ls layouts/essay/ layouts/garden/ 2>/dev/null && ls layouts/research/ 2>/dev/null`
Expected: lists any per-section `single.html` files that exist.

For any section-specific single layout found, add the matching meta. If `_default/single.html` is still used for some section (no section-specific layout exists for that section), keep the `_default/single.html` modification — its `{{ .Section }}` template logic will emit the correct section.

- [ ] **Step 3: Run hugo build + linter to verify all pages pass**

```bash
rm -rf public/
hugo --minify
python3 tools/check_pagefind_meta.py
echo "exit: $?"
```

Expected: linter exits 0 with `check_pagefind_meta: OK`. If any pages fail, the error output names the URL — go fix the corresponding layout file.

- [ ] **Step 4: Commit**

```bash
git add layouts/
git commit -m "pagefind: emit data-pagefind-body + per-layout meta attrs"
```

---

### Task 6: Wire metadata linter into CI workflow

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Read existing workflow to locate insertion point**

Run: `grep -n "library cover" .github/workflows/hugo.yaml`
Expected: shows the existing library-cover linter pair (lines ~95-98).

- [ ] **Step 2: Add Pagefind metadata linter steps after the library-cover linter**

Insert after the `Run library cover linter unit tests` step (currently at line ~97-98) and before the `Build with Hugo` step:

Wait — the linter requires `public/` (post-build). It must run **after** `hugo --minify`, not before. Move the insertion point.

Locate the `Build with Hugo` step (line ~99-108). Insert the two new steps **after** the Hugo build step and before the `Upload artifact` step:

```yaml
      - name: Run pagefind metadata linter unit tests
        run: cd tools && python3 -m unittest test_check_pagefind_meta.py -v
      - name: Verify pagefind metadata on built pages
        run: python3 tools/check_pagefind_meta.py
```

Final workflow shape near the build step:

```yaml
      - name: Build with Hugo
        env:
          HUGO_CACHEDIR: ${{ runner.temp }}/hugo_cache
          HUGO_ENVIRONMENT: production
          TZ: America/Los_Angeles
        run: |
          hugo \
            --gc \
            --minify \
            --baseURL "${{ steps.pages.outputs.base_url }}/"
      - name: Run pagefind metadata linter unit tests
        run: cd tools && python3 -m unittest test_check_pagefind_meta.py -v
      - name: Verify pagefind metadata on built pages
        run: python3 tools/check_pagefind_meta.py
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public
```

- [ ] **Step 3: Verify workflow YAML parses**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/hugo.yaml'))" && echo OK`
Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "ci: gate deploy on pagefind metadata linter"
```

---

### Task 7: Install Pagefind binary + post-build index step

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Check the latest stable Pagefind release**

Run: `curl -sL https://api.github.com/repos/CloudCannon/pagefind/releases/latest | grep '"tag_name"' | head -1`
Expected: shows the latest tag, e.g., `"tag_name": "v1.3.0"`.

Pin to that exact version. Note it down for Step 2.

- [ ] **Step 2: Add `PAGEFIND_VERSION` to workflow env**

In `.github/workflows/hugo.yaml`, find the `env:` block under `jobs.build`:

```yaml
    env:
      HUGO_VERSION: 0.148.0
```

Change to (substitute the version from Step 1):

```yaml
    env:
      HUGO_VERSION: 0.148.0
      PAGEFIND_VERSION: 1.3.0   # or whatever Step 1 returned, without the leading "v"
```

- [ ] **Step 3: Add Pagefind install step + index step**

Insert two new steps **after** `Verify pagefind metadata on built pages` and **before** `Upload artifact`:

```yaml
      - name: Install Pagefind
        run: |
          wget -O ${{ runner.temp }}/pagefind.tar.gz \
            https://github.com/CloudCannon/pagefind/releases/download/v${PAGEFIND_VERSION}/pagefind-v${PAGEFIND_VERSION}-x86_64-unknown-linux-musl.tar.gz
          tar -xzf ${{ runner.temp }}/pagefind.tar.gz -C ${{ runner.temp }}
          sudo mv ${{ runner.temp }}/pagefind /usr/local/bin/
          pagefind --version
      - name: Build Pagefind index
        run: pagefind --site public/
```

- [ ] **Step 4: Verify workflow YAML still parses**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/hugo.yaml'))" && echo OK`
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "ci: install pagefind binary + build index post-hugo"
```

---

### Task 8: Search modal HTML partial

**Files:**
- Create: `layouts/partials/search-modal.html`

- [ ] **Step 1: Create the partial**

Write `layouts/partials/search-modal.html`:

```html
{{- /* Site-wide search modal. Included once in baseof.html.
       Markup is hidden until JS opens the <dialog> via showModal().
       JS lazy-loads /pagefind/pagefind.js on first open.
*/ -}}
<dialog class="search-modal" aria-label="Search">
  <form class="search-modal-form" role="search" data-search-form>
    <span class="search-modal-icon" aria-hidden="true">
      {{ with resources.Get "images/icons/search.svg" }}{{ .Content | safeHTML }}{{ end }}
    </span>
    <input
      type="search"
      class="search-modal-input"
      data-search-input
      placeholder="Search the site…"
      autocomplete="off"
      spellcheck="false"
      aria-label="Search query"
    />
    <kbd class="search-modal-esc-hint">Esc</kbd>
  </form>
  <nav class="search-modal-filters" aria-label="Filter by section">
    <button type="button" class="search-modal-chip is-active" data-section="all">All</button>
    <button type="button" class="search-modal-chip" data-section="essays">Essays</button>
    <button type="button" class="search-modal-chip" data-section="garden">Garden</button>
    <button type="button" class="search-modal-chip" data-section="research">Research</button>
    <button type="button" class="search-modal-chip" data-section="works">Works</button>
    <button type="button" class="search-modal-chip" data-section="library">Library</button>
  </nav>
  <div
    class="search-modal-results"
    data-search-results
    role="region"
    aria-live="polite"
    aria-atomic="false"
  ></div>
  <footer class="search-modal-footer">
    <div class="search-modal-kbd-hints">
      <span><kbd>↑</kbd><kbd>↓</kbd> navigate</span>
      <span><kbd>↵</kbd> open</span>
      <span><kbd>⌘</kbd><kbd>↵</kbd> new tab</span>
      <span><kbd>Esc</kbd> close</span>
    </div>
    <div class="search-modal-status" data-search-status aria-live="polite"></div>
  </footer>
</dialog>
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/search-modal.html
git commit -m "pagefind: search modal partial (<dialog>-based markup)"
```

---

### Task 9: Include modal in baseof + add header search icon-button

**Files:**
- Modify: `layouts/_default/baseof.html`
- Modify: `layouts/partials/header.html`

- [ ] **Step 1: Add the modal partial call to `baseof.html`**

Current `baseof.html` (after Task 5 edits):

```html
<!DOCTYPE html>
<html lang="{{ .Site.Language.Lang }}">
  {{ partial "head.html" . }}
  <body>
    <div class="page">
      {{ partial "header.html" . }}
      <main data-pagefind-body>
        {{- block "main" . -}}{{- end -}}
      </main>
      {{ partial "footer.html" . }}
    </div>
    {{ partial "search-modal.html" . }}
    {{ partial "scripts.html" . }}
  </body>
</html>
```

The new line `{{ partial "search-modal.html" . }}` goes between the closing `</div>` of `.page` and the `scripts.html` partial. Modal lives outside `.page` so its backdrop covers the whole viewport when open.

- [ ] **Step 2: Add the header search icon-button**

Open `layouts/partials/header.html`. Insert a new `<button>` between the RSS link block (currently lines 25-30) and the theme-toggle button (currently lines 31-36):

```html
    <button class="icon-button"
            type="button"
            data-search-toggle
            aria-label="Open search">
      {{ with resources.Get "images/icons/search.svg" }}{{ .Content | safeHTML }}{{ end }}
    </button>
```

Final ordering in `<nav class="site-nav">`: section links → RSS link → search button → theme toggle button.

- [ ] **Step 3: Verify Hugo build still succeeds (icon not yet wired functionally, but markup parses)**

Run: `hugo --minify 2>&1 | tail -20`
Expected: builds successfully. The new search button appears on every page; clicking does nothing yet (JS lands in Task 11).

- [ ] **Step 4: Commit**

```bash
git add layouts/_default/baseof.html layouts/partials/header.html
git commit -m "pagefind: include modal in baseof + add header search button"
```

---

### Task 10: Search modal CSS — §42

**Files:**
- Modify: `assets/css/main.css` (append §42)

- [ ] **Step 1: Read the bottom of `main.css` to locate the §41 end**

Run: `grep -n "^/\* §41\|^/\* §42" assets/css/main.css`
Expected: shows §41 start; no §42 yet.

Run: `wc -l assets/css/main.css`
Expected: line count of the file.

- [ ] **Step 2: Append §42 to the file**

Add at the end of `assets/css/main.css`:

```css

/* ============================================================================
   §42 Search modal
   <dialog>-based modal opened by header icon or `/` keystroke. Token-driven
   palette; fade-in only; respects prefers-reduced-motion.
   ========================================================================== */

.search-modal {
  /* Native <dialog> centering + reset */
  border: none;
  padding: 0;
  background: transparent;
  max-width: min(900px, 95vw);
  width: 100%;
  max-height: min(80vh, 720px);
  color: var(--color-ink);
  font-family: var(--font-body);
}

.search-modal::backdrop {
  background: color-mix(in srgb, var(--color-ink) 70%, transparent);
  backdrop-filter: blur(8px);
}

.search-modal[open] {
  animation: search-modal-fade-in 120ms ease-out;
  display: flex;
  flex-direction: column;
  background: var(--color-paper);
  border-radius: 8px;
  box-shadow: 0 8px 32px color-mix(in srgb, var(--color-ink) 30%, transparent);
  overflow: hidden;
}

@keyframes search-modal-fade-in {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
  .search-modal[open] { animation: none; }
}

.search-modal-form {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-ink-soft);
}

.search-modal-icon {
  display: inline-flex;
  color: var(--color-ink-soft);
  width: 1.25rem;
  height: 1.25rem;
}

.search-modal-icon svg { width: 100%; height: 100%; }

.search-modal-input {
  flex: 1;
  border: none;
  background: transparent;
  font-family: var(--font-body);
  font-size: 1.125rem;
  color: var(--color-ink);
  outline: none;
}

.search-modal-input::placeholder { color: var(--color-ink-soft); }

.search-modal-esc-hint {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--color-ink-soft);
  border: 1px solid var(--color-ink-soft);
  border-radius: 4px;
  padding: 0.125rem 0.375rem;
}

.search-modal-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid var(--color-ink-soft);
}

.search-modal-chip {
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  background: transparent;
  border: 1px solid var(--color-ink-soft);
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  color: var(--color-ink);
  cursor: pointer;
}

.search-modal-chip:hover,
.search-modal-chip:focus-visible {
  border-color: var(--color-burgundy);
  outline: 2px solid var(--color-burgundy);
  outline-offset: 2px;
}

.search-modal-chip.is-active {
  background: var(--color-burgundy);
  color: var(--color-paper);
  border-color: var(--color-burgundy);
}

.search-modal-results {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 1.25rem;
}

.search-modal-results section {
  margin-top: 1rem;
}

.search-modal-results section:first-child { margin-top: 0.5rem; }

.search-modal-results h3 {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-ink-soft);
  margin: 0 0 0.5rem;
}

.search-modal-results ol {
  list-style: none;
  margin: 0;
  padding: 0;
}

.search-modal-result {
  padding: 0.625rem 0.5rem;
  border-radius: 6px;
  cursor: pointer;
}

.search-modal-result.is-active,
.search-modal-result:hover {
  background: color-mix(in srgb, var(--color-burgundy) 8%, transparent);
}

.search-modal-result a {
  text-decoration: none;
  color: inherit;
  display: block;
}

.search-modal-result-title {
  font-family: var(--font-body);
  font-weight: 600;
  color: var(--color-ink);
}

.search-modal-result-snippet {
  font-size: 0.875rem;
  color: var(--color-ink-soft);
  margin-top: 0.125rem;
  line-height: 1.45;
}

.search-modal-result-snippet mark {
  background: color-mix(in srgb, var(--color-burgundy) 20%, transparent);
  color: inherit;
  padding: 0 0.125rem;
}

.search-modal-result-spoilers {
  font-family: var(--font-ui);
  font-size: 0.6875rem;
  color: var(--color-ink-soft);
  font-style: italic;
  margin-top: 0.125rem;
}

.search-modal-empty {
  font-family: var(--font-body);
  font-style: italic;
  color: var(--color-ink-soft);
  text-align: center;
  padding: 2rem 1rem;
}

.search-modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.25rem;
  border-top: 1px solid var(--color-ink-soft);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--color-ink-soft);
  gap: 1rem;
  flex-wrap: wrap;
}

.search-modal-kbd-hints {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.search-modal-kbd-hints kbd {
  font-family: var(--font-mono);
  font-size: 0.6875rem;
  background: color-mix(in srgb, var(--color-ink-soft) 12%, transparent);
  border: 1px solid var(--color-ink-soft);
  border-radius: 3px;
  padding: 0.0625rem 0.25rem;
  margin: 0 0.125rem;
}

@media (max-width: 600px) {
  .search-modal-kbd-hints { display: none; }
  .search-modal-form { padding: 0.75rem 1rem; }
  .search-modal-filters { padding: 0.5rem 1rem; }
  .search-modal-results { padding: 0.25rem 1rem; }
}
```

- [ ] **Step 3: Update the §index at the top of `main.css`**

Run: `head -50 assets/css/main.css | grep -n "§41\|§42"`

If the file has a numbered index at the top listing sections (per CLAUDE.md: "see the file's top-of-file index"), add a `§42 Search modal` line after `§41`. If the index format is a comment block, mirror it.

- [ ] **Step 4: Verify contrast still passes**

Run: `python3 tools/check-contrast.py`
Expected: passes (no new tokens added; reused existing ones).

- [ ] **Step 5: Commit**

```bash
git add assets/css/main.css
git commit -m "pagefind: css §42 search modal"
```

---

### Task 11: Search modal JS module + bundle entry

**Files:**
- Create: `assets/js/entry-search.js`
- Create: `assets/js/search.js`

- [ ] **Step 1: Create `assets/js/entry-search.js`**

```js
import './search.js';
```

(One-line bundle entry mirroring the existing pattern for other section bundles.)

- [ ] **Step 2: Create `assets/js/search.js`**

```js
/* Site-wide search modal.
   Opens on header icon click or `/` keypress (when not in an input).
   Lazy-loads /pagefind/pagefind.js on first open.
*/

const SECTION_ORDER = ['essays', 'garden', 'research', 'works', 'library', 'home', 'about'];
const SECTION_LABEL = {
  essays:   'Essays',
  garden:   'Garden',
  research: 'Research',
  works:    'Works',
  library:  'Library',
  home:     'Home',
  about:    'About',
};

let pagefindInstance = null;
let pagefindLoadPromise = null;
let currentSection = 'all';
let debounceTimer = null;
let resultRows = [];
let activeRowIndex = -1;

function loadPagefind() {
  if (pagefindLoadPromise) return pagefindLoadPromise;
  pagefindLoadPromise = import('/pagefind/pagefind.js')
    .then((mod) => mod)
    .catch((err) => {
      console.error('[search] Failed to load Pagefind:', err);
      pagefindLoadPromise = null;
      throw err;
    });
  return pagefindLoadPromise;
}

function openModal(modal, input) {
  if (modal.open) return;
  modal.showModal();
  input.focus();
  // Pre-warm Pagefind once the modal is open (the user will probably search).
  loadPagefind().then((p) => { pagefindInstance = p; }).catch(() => {});
}

function closeModal(modal) {
  if (modal.open) modal.close();
}

function debounce(fn, ms) {
  return (...args) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => fn(...args), ms);
  };
}

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderResults(resultsEl, statusEl, groups, totalMs, query) {
  resultRows = [];
  activeRowIndex = -1;

  if (!query) {
    resultsEl.innerHTML = '';
    statusEl.textContent = '';
    return;
  }

  const total = Object.values(groups).reduce((acc, arr) => acc + arr.length, 0);
  if (total === 0) {
    resultsEl.innerHTML = '<p class="search-modal-empty">No results.</p>';
    statusEl.textContent = `0 results in ${totalMs}ms`;
    return;
  }

  const sections = SECTION_ORDER.filter((s) => groups[s] && groups[s].length > 0);
  let html = '';
  for (const section of sections) {
    html += `<section data-section="${section}"><h3>${SECTION_LABEL[section]}</h3><ol>`;
    for (const row of groups[section]) {
      const spoilers = parseInt(row.meta?.spoilers || '0', 10);
      html += `
        <li class="search-modal-result" data-url="${escapeHtml(row.url)}">
          <a href="${escapeHtml(row.url)}">
            <div class="search-modal-result-title">${escapeHtml(row.title)}</div>
            <div class="search-modal-result-snippet">${row.excerpt}</div>
            ${spoilers > 0 ? `<div class="search-modal-result-spoilers">${spoilers} spoiler block${spoilers === 1 ? '' : 's'} hidden from search</div>` : ''}
          </a>
        </li>`;
    }
    html += '</ol></section>';
  }
  resultsEl.innerHTML = html;
  resultRows = Array.from(resultsEl.querySelectorAll('.search-modal-result'));
  statusEl.textContent = `${total} result${total === 1 ? '' : 's'} in ${totalMs}ms`;
}

async function performSearch(query, resultsEl, statusEl) {
  if (!query || !query.trim()) {
    renderResults(resultsEl, statusEl, {}, 0, '');
    return;
  }
  try {
    if (!pagefindInstance) pagefindInstance = await loadPagefind();
  } catch (e) {
    resultsEl.innerHTML = '<p class="search-modal-empty">Search is unavailable.</p>';
    return;
  }
  const t0 = performance.now();
  const filters = currentSection === 'all' ? {} : { section: [currentSection] };
  const search = await pagefindInstance.search(query, { filters });
  // Pagefind returns ids; fetch their data in parallel.
  const top = search.results.slice(0, 30);
  const datas = await Promise.all(top.map((r) => r.data()));
  const groups = {};
  for (const d of datas) {
    const section = d.meta?.section || 'other';
    if (!groups[section]) groups[section] = [];
    groups[section].push(d);
  }
  const elapsed = Math.round(performance.now() - t0);
  renderResults(resultsEl, statusEl, groups, elapsed, query);
}

function setActiveRow(idx) {
  if (resultRows.length === 0) return;
  if (activeRowIndex >= 0) resultRows[activeRowIndex].classList.remove('is-active');
  activeRowIndex = Math.max(0, Math.min(resultRows.length - 1, idx));
  resultRows[activeRowIndex].classList.add('is-active');
  resultRows[activeRowIndex].scrollIntoView({ block: 'nearest' });
}

function openActiveRow(newTab) {
  if (activeRowIndex < 0) return;
  const row = resultRows[activeRowIndex];
  const url = row.dataset.url;
  if (!url) return;
  if (newTab) window.open(url, '_blank');
  else window.location.href = url;
}

function init() {
  const modal = document.querySelector('.search-modal');
  if (!modal) return;
  const input = modal.querySelector('[data-search-input]');
  const resultsEl = modal.querySelector('[data-search-results]');
  const statusEl = modal.querySelector('[data-search-status]');
  const chips = modal.querySelectorAll('[data-section]');
  const trigger = document.querySelector('[data-search-toggle]');

  // Header icon click
  if (trigger) trigger.addEventListener('click', () => openModal(modal, input));

  // `/` keyboard shortcut anywhere
  window.addEventListener('keydown', (e) => {
    if (e.key !== '/') return;
    const tag = (document.activeElement?.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || document.activeElement?.isContentEditable) return;
    e.preventDefault();
    openModal(modal, input);
  });

  // Filter chips
  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      chips.forEach((c) => c.classList.remove('is-active'));
      chip.classList.add('is-active');
      currentSection = chip.dataset.section;
      performSearch(input.value, resultsEl, statusEl);
    });
  });

  // Debounced input
  const debouncedSearch = debounce(() => performSearch(input.value, resultsEl, statusEl), 150);
  input.addEventListener('input', debouncedSearch);

  // Keyboard nav inside the modal
  modal.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveRow(activeRowIndex < 0 ? 0 : activeRowIndex + 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveRow(activeRowIndex - 1);
    } else if (e.key === 'Enter') {
      if (activeRowIndex >= 0) {
        e.preventDefault();
        openActiveRow(e.metaKey || e.ctrlKey);
      }
    }
  });

  // Reset state on close
  modal.addEventListener('close', () => {
    input.value = '';
    resultsEl.innerHTML = '';
    statusEl.textContent = '';
    activeRowIndex = -1;
    resultRows = [];
    currentSection = 'all';
    chips.forEach((c) => c.classList.toggle('is-active', c.dataset.section === 'all'));
  });

  // Click backdrop to close (Pagefind UX expectation)
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal(modal);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
```

- [ ] **Step 3: Verify both files parse**

Run: `node -e "require('fs').readFileSync('assets/js/entry-search.js','utf8'); console.log('OK')"` (if `node` available); otherwise rely on the next task's Hugo build to surface syntax errors.

- [ ] **Step 4: Commit**

```bash
git add assets/js/entry-search.js assets/js/search.js
git commit -m "pagefind: search modal JS module"
```

---

### Task 12: Wire `entry-search.js` into scripts.html

**Files:**
- Modify: `layouts/partials/scripts.html`

- [ ] **Step 1: Read the current `scripts.html`**

Run: `cat layouts/partials/scripts.html`
Expected: existing multi-entry bundling block (core, essay, garden, research, works, works-umbrella, library).

- [ ] **Step 2: Insert the search bundle block**

The search bundle loads on **every page** (the `/` shortcut works site-wide). Place it immediately after the core bundle for symmetry. Insert after line 11 (the existing `<script>` for core):

```hugo
{{- /* Search modal — loaded on every page (the `/` shortcut works everywhere) */ -}}
{{- $searchOpts := dict "targetPath" "js/search.js" "minify" true -}}
{{- $search := resources.Get "js/entry-search.js" | js.Build $searchOpts | fingerprint -}}
<script src="{{ $search.RelPermalink }}" integrity="{{ $search.Data.Integrity }}" defer></script>
```

Final shape of the top of `scripts.html`:

```hugo
{{- $coreOpts := dict "targetPath" "js/core.js" "minify" true -}}
{{- $core := resources.Get "js/index.js" | js.Build $coreOpts | fingerprint -}}
<script src="{{ $core.RelPermalink }}" integrity="{{ $core.Data.Integrity }}" defer></script>

{{- /* Search modal — loaded on every page (the `/` shortcut works everywhere) */ -}}
{{- $searchOpts := dict "targetPath" "js/search.js" "minify" true -}}
{{- $search := resources.Get "js/entry-search.js" | js.Build $searchOpts | fingerprint -}}
<script src="{{ $search.RelPermalink }}" integrity="{{ $search.Data.Integrity }}" defer></script>

{{- if eq .Section "essays" }}
…
```

**Note:** there's already a `js/search.js` *output target path* used by no one yet, but to avoid colliding with any future search bundle, use the targetPath `js/search.js`. (esbuild will produce `js/search.<hash>.js` via fingerprinting.)

Wait — `js/search.js` is also the **source** filename. Hugo's `targetPath` is an output hint; Hugo doesn't auto-derive it from the entry source filename. The existing entries use names like `js/essay.js` as targetPath while the source is `entry-essay.js`. So `targetPath: "js/search.js"` is fine as long as no other entry uses the same target. Verify with:

Run: `grep targetPath layouts/partials/scripts.html`
Expected: shows `core.js`, `essay.js`, `garden.js`, `research.js`, `works-umbrella.js`, `works.js`, `library.js`. No collision with `search.js`.

- [ ] **Step 3: Verify Hugo build succeeds**

```bash
rm -rf public/
hugo --minify 2>&1 | tail -30
ls public/js/ | head
```

Expected: build succeeds; `public/js/` contains a `search.<hash>.js` file alongside the other bundle outputs.

- [ ] **Step 4: Commit**

```bash
git add layouts/partials/scripts.html
git commit -m "pagefind: ship entry-search.js on every page"
```

---

### Task 13: Dev-server spot-check + manual QA

**No files modified in this task** — verification only. If anything fails, write fixes in a follow-up commit.

Before this task: a CI workflow change adds Pagefind, but locally Pagefind isn't installed. To get full coverage, install it locally too.

- [ ] **Step 1: Install Pagefind locally**

Choose one (in order of preference):

```bash
# Option A: npx (works if you have any node available; downloads the binary on first run)
npx -y pagefind --version

# Option B: cargo
cargo install pagefind

# Option C: download the same release the CI uses
PAGEFIND_VERSION=1.3.0  # match what you pinned in Task 7
wget -O /tmp/pagefind.tar.gz https://github.com/CloudCannon/pagefind/releases/download/v${PAGEFIND_VERSION}/pagefind-v${PAGEFIND_VERSION}-x86_64-unknown-linux-musl.tar.gz
tar -xzf /tmp/pagefind.tar.gz -C /tmp
sudo mv /tmp/pagefind /usr/local/bin/
pagefind --version
```

Expected: prints version matching what you pinned in Task 7.

- [ ] **Step 2: Build site + index**

```bash
rm -rf public/
hugo --minify
pagefind --site public/
ls public/pagefind/ | head
```

Expected: `public/pagefind/` contains `pagefind.js`, `pagefind-ui.js` (we don't use it), a wasm file, and `fragment/` + `index/` directories.

- [ ] **Step 3: Serve `public/` and open in browser**

```bash
cd public/
python3 -m http.server 8080
```

Open `http://localhost:8080/` in a browser.

**Spot-check matrix (each item: walk through, mark ☑ / ☒ / ⚠ inline):**

1. ☐ Header shows the magnifier icon between RSS and theme toggle.
2. ☐ Click magnifier → modal opens, focus is in the search input.
3. ☐ Press `Esc` → modal closes.
4. ☐ Press `/` on the homepage → modal opens.
5. ☐ Focus an input (e.g., open a filter-chip disclosure search) → press `/` → modal does NOT open; the `/` types literally.
6. ☐ Type "lorem" (or any word in fixture text) → results appear within ~200ms, grouped by section with headers.
7. ☐ Result snippets show `<mark>`-highlighted query.
8. ☐ Click a section chip (e.g., "Garden") → results filter to garden only.
9. ☐ Click "All" → all sections back.
10. ☐ Click a result → modal closes, browser navigates to the result page.
11. ☐ Re-open modal, type a query → press ↓ → first result has hover/active highlight; ↓ again → second result; ↑ → first.
12. ☐ Press Enter on highlighted result → navigates.
13. ☐ Press ⌘+Enter (or Ctrl+Enter) → opens in new tab.
14. ☐ Click on the backdrop outside the modal → modal closes.
15. ☐ At 360px wide (devtools mobile) → modal sized correctly, no overflow.
16. ☐ Toggle dark mode → modal colors flip correctly.
17. ☐ Open a page with a `{{< spoiler >}}` block → search for the spoiler body text → no result. Search for the summary text → the page surfaces. (Verify `data-pagefind-ignore` is doing its job.)
18. ☐ DevTools Network panel: cold-load any page; the search bundle is ~3-5KB minified; `pagefind.js` is NOT requested on page load (only after first modal open).

- [ ] **Step 4: Verify the cold-load bundle weight**

Open DevTools Network → refresh homepage → filter on `search` → note the size of `search.<hash>.js`.

Expected: under 6 KB minified + brotli.

- [ ] **Step 5: Commit any spot-check fixes (if needed)**

If a checklist item failed, fix it, then:

```bash
git add <files>
git commit -m "pagefind: fix <whatever the issue was>"
```

If no fixes needed, skip this step.

---

### Task 14: Refresh CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read the current CLAUDE.md sections that mention JS bundling**

Run: `grep -n "entry-\|js.Build\|core.<hash>" CLAUDE.md | head -20`
Expected: locates the JS pipeline table around the "JS pipeline — multi-entry bundling" header.

- [ ] **Step 2: Add a new row for `entry-search.js` to the JS pipeline table**

The table currently has rows for index/essay/garden/research/works/works-umbrella/library. Insert a new row right after the `index.js` row:

```markdown
| `js/entry-search.js` | `search.<hash>.js` (~4-6 KB) | every page | imports `search.js`; lazy-loads `/pagefind/pagefind.js` on first modal open |
```

- [ ] **Step 3: Add CSS §42 reference to the §1–§41 sections list**

Find the line `…§41 covers the cross-template page sidebar` and extend it to: `…§41 covers the cross-template page sidebar; §42 covers the search modal`.

- [ ] **Step 4: Add a "Search modal" subsection under "Architecture"**

Insert after the "Theme toggle" subsection (or wherever feels natural in the architecture section). Suggested text:

```markdown
### Search modal

Site-wide search powered by **Pagefind** (Rust binary, downloaded in CI). Pagefind indexes `public/` after `hugo --minify` into `public/pagefind/` (gitignored — regenerated in CI).

- Modal markup: `layouts/partials/search-modal.html`, included once in `baseof.html`. `<dialog>` element for native modal semantics, focus trap, and Esc-to-close.
- Modal JS: bundle entry `js/entry-search.js` → output `search.<hash>.js`, loaded on every page. Dynamically `import()`s `/pagefind/pagefind.js` on first open.
- Triggers: header magnifier icon + `/` key (when focus is not in an input / textarea / contenteditable).
- Indexing controls: `<main data-pagefind-body>` in `baseof.html`; per-layout `data-pagefind-meta="section:…,…"` on outer content wrappers; `data-pagefind-ignore` on `.spoiler-body`.
- Metadata linter: `tools/check_pagefind_meta.py` (+ test sibling) runs post-build in CI, asserting `data-pagefind-body` + a `section` meta key on every indexable page.
- Search filters across 6 sections (all / essays / garden / research / works / library); single-active per query; not multi-select within sections.
```

- [ ] **Step 5: Update §Project status section**

Add a bullet under "Shipped" describing what just landed. Something like:

```markdown
- **Search runtime** (Phase 8 Slice 1): Pagefind-backed site-wide search modal. `<dialog>`-based markup; ~5KB cold-page JS; lazy-loaded `pagefind.js`; section filter chips; keyboard nav; spoiler-aware indicator. New §42 CSS; new `entry-search.js` bundle; new `check_pagefind_meta.py` linter pair gating data-pagefind-body + section meta. CI adds Pagefind binary install + index step.
```

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md: refresh after Phase 8 slice 1 (pagefind runtime)"
```

---

### Task 15: Slice finishing — merge into master

This task follows the project's slice-finishing flow.

- [ ] **Step 1: Confirm working tree clean and all tasks committed**

```bash
git status
git log --oneline master..HEAD
```

Expected: working tree clean. `git log` shows the slice's commits (Tasks 1-12, optionally 13's fixes, 14's CLAUDE.md refresh) — somewhere around 12-14 commits.

- [ ] **Step 2: Run all linters locally one more time**

```bash
python3 tools/check-contrast.py
python3 tools/check_fixtures.py
python3 tools/check_garden_fixtures.py
python3 tools/check_garden_links.py
python3 tools/check_filter_chips_config.py
python3 tools/check_research_fixtures.py
python3 tools/check_research_links.py
python3 tools/check_citations.py
python3 tools/check_works_fixtures.py
python3 tools/check_works_links.py
python3 tools/check_library_fixtures.py
python3 tools/check_library_links.py
python3 tools/check_library_covers.py

rm -rf public/
hugo --minify
python3 tools/check_pagefind_meta.py
```

Expected: every linter passes.

- [ ] **Step 3: Run all linter unit-test siblings**

```bash
for f in tools/test_*.py; do
  echo "--- $f ---"
  python3 -m unittest $f -v 2>&1 | tail -5
done
```

Expected: all unit tests pass.

- [ ] **Step 4: Ask the user to spot-check before merging**

Per the user's standing preference (memory `feedback_verify_before_merge.md`): always offer a dev-server spot-check + a "what to eyeball" checklist before authorizing merge.

Print this checklist to the user (or include in the PR description if they want a GitHub PR):

```
Spot-check before merge:
  hugo server --buildDrafts   # then visit http://localhost:1313/
  - / opens modal everywhere (homepage, an essay, a garden note, a research theme, a library leaf)
  - Esc closes
  - Filter chips work
  - Result clicks navigate
  - Search the word "Example" → results in every section
  - Dark mode: modal colors flip cleanly
  - 960px viewport (half-screen): modal sized correctly
```

Wait for user confirmation before proceeding.

- [ ] **Step 5: Merge into master**

```bash
git checkout master
git merge --no-ff slice/phase-8-pagefind -m "Merge slice/phase-8-pagefind: Pagefind runtime (Phase 8 Slice 1)"
git push origin master
git branch -d slice/phase-8-pagefind
```

- [ ] **Step 6: Verify CI passes on master**

Wait for the GitHub Actions run to complete on master. Check that:
1. The new Pagefind binary install step succeeds.
2. `pagefind --site public/` builds the index.
3. `check_pagefind_meta.py` passes against the built site.
4. The deploy step succeeds and the live site is updated.

If anything fails on CI, fix on a new branch, not by reverting the merge.

---

## Self-Review Notes

Reviewed against the spec §2 (Slice 1 — Pagefind runtime):

- ✅ §2.1 Architecture — implemented via Tasks 7, 8, 9, 11, 12 (binary install, index step, modal markup, JS module, bundle entry).
- ✅ §2.2 File layout — full coverage in the File Structure table above.
- ✅ §2.3 CI install + post-build step — Task 7.
- ✅ §2.4 Modal markup — Task 8.
- ✅ §2.5 Indexing controls — Tasks 1 (spoiler ignore), 5 (data-pagefind-body + per-layout meta).
- ✅ §2.6 Modal JS bundle — Tasks 11, 12.
- ✅ §2.7 Header icon — Tasks 2 (svg) + 9 (button).
- ✅ §2.8 CSS §42 — Task 10.
- ✅ §2.9 Out of scope — respected (no JS-disabled fallback for search itself; no "next page" shortcut; no analytics).
- ✅ Spec line 628 — `data-pagefind-ignore` on `.spoiler-body` — Task 1.
- ✅ Spec §2.5 spoiler-aware indicator — search.js parses `spoilers` meta count when rendering. Note: emitting the count via Hugo template (counting `{{< spoiler >}}` occurrences) is left for an enhancement once real essays with spoilers exist; current fixture set has no spoiler blocks so the count would always be 0 anyway. Plan footnote.

Placeholder scan: no TBD / TODO. `PAGEFIND_VERSION` resolved at plan-execution time in Task 7 Step 1 (curl latest); no longer a placeholder by the time the workflow file is edited.

Type consistency: `currentSection` (search.js) values map to `data-section` attribute on chips (search-modal.html) ✓. `data-pagefind-meta` keys (search.js parses `meta.section`, `meta.spoilers`) match emitter keys in Task 5 ✓. JS bundle target `js/search.js` doesn't collide with any existing entry ✓.

One footnote-level issue: the spoiler-count meta emission (Task 5 doesn't emit it) — fixture set has zero spoilers so it's harmless. Real essays land via Phase 3; emission can land in a follow-up after content exists. Documented above.

---

*End of plan.*
