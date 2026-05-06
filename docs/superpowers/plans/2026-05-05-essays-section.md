# Essays Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the essays section of the personal site — `/essays/` index with variable-tile grid + filter chips, full essay post layouts (TOC + sidenotes + citations placeholder + code highlighting + footnotes + figures + tags + hero illustrations + series nav), six fixture posts with filler content, per-section RSS, and a homepage essays strip.

**Architecture:** Hugo static site, hand-rolled CSS (extends `assets/css/main.css`), one shared `essay.js` module added to the existing bundle (no per-page bundles), no Tailwind/Node. Fixture content uses lorem ipsum / "Example N" filler only. Deferred features (KaTeX, widgets, video-sync, spoiler runtime, figure lightbox, citation hover-card) ship as no-op shortcode stubs that fixtures still exercise so they round-trip when the renderers arrive.

**Tech Stack:** Hugo extended ≥0.148.0, Python 3 (linter — stdlib only), vanilla JS (ES modules, esbuild via Hugo's `js.Build`), CSS (CSS Grid + custom properties).

**Spec:** `docs/superpowers/specs/2026-05-05-essays-section-design.md`. Read it before starting any task.

**Existing reusable components (don't reimplement):**
- `assets/js/nav.js` already implements TOC active-link highlighting via `IntersectionObserver` against `#TableOfContents a`. The new `essay.js` should NOT duplicate this; it adds popups + smooth-scroll + cite hook on top.
- `assets/css/main.css` defines all tokens (colors, fonts, sizes). New CSS reuses them — never hardcode color values.
- `tools/check-contrast.py` is the existing CI gate; the new linter follows the same shape (Python stdlib, exit 0/1, prints lines).

**Verification model:**
- Python linter: real unit tests via stdlib `unittest`.
- Hugo templates / shortcodes / CSS: TDD-as-fixture — fixture exercising the feature exists or is added first; `hugo` build is run; visual inspection in `hugo server` is the assertion. Each task ends with explicit `hugo --minify` build success + browser check at the affected page.
- Final task: full manual walkthrough checklist.

**Working assumption:** Run `hugo server --buildDrafts` continuously in a separate terminal during implementation; inspect at `http://localhost:1313/`.

---

## Task 1: Fixture frontmatter linter (`tools/check-fixtures.py`)

**Files:**
- Create: `tools/check-fixtures.py`
- Create: `tools/test_check_fixtures.py`

The linter walks `content/essays/*/index.md`, parses YAML frontmatter, and verifies required fields, enums, references, and the cite-key contract against `data/citations.yaml`. Stdlib only (no `pyyaml` dep — we hand-parse a narrow subset of YAML).

- [ ] **Step 1: Write the failing tests**

Create `tools/test_check_fixtures.py`:

```python
"""Tests for check-fixtures.py — run with: python3 -m unittest tools/test_check_fixtures.py -v"""
from __future__ import annotations

import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_fixtures as lint  # noqa: E402


VALID_FRONTMATTER = """\
---
title: "Example essay one"
date: 2026-04-12
lastmod: 2026-04-20
draft: false
summary: "Lorem ipsum"
tags: ["a", "b"]
series: ""
series_order: 0
tile_size: large
featured: true
hero: hero.svg
toc: true
has_sidenotes: true
has_citations: true
has_footnotes: true
has_math: false
has_widgets: false
has_video_sync: false
---

Body. {{< cite "example-source-1" >}}
"""

VALID_CITATIONS = """\
citations:
  example-source-1:
    authors: ["Lastname"]
    year: 2020
    title: "x"
    venue: "y"
    url: "z"
    notes_ref: ""
"""


class TempRepo:
    """Minimal repo skeleton for testing the linter."""
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        (self.root / "data").mkdir()
        (self.root / "content" / "essays").mkdir(parents=True)

    def write_essay(self, slug: str, frontmatter_body: str, hero: bool = False) -> None:
        d = self.root / "content" / "essays" / slug
        d.mkdir(exist_ok=True)
        (d / "index.md").write_text(frontmatter_body)
        if hero:
            (d / "hero.svg").write_text("<svg/>")

    def write_citations(self, body: str) -> None:
        (self.root / "data" / "citations.yaml").write_text(body)

    def cleanup(self) -> None:
        shutil.rmtree(self.root)


class CheckFixturesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    def test_valid_fixture_passes(self) -> None:
        self.repo.write_essay("example-essay-one", VALID_FRONTMATTER, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected failures: {errors}")
        self.assertEqual(errors, [])

    def test_empty_essays_section_passes(self) -> None:
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0)

    def test_missing_required_field_fails(self) -> None:
        broken = VALID_FRONTMATTER.replace('title: "Example essay one"\n', "")
        self.repo.write_essay("broken", broken)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("title" in e for e in errors))

    def test_invalid_tile_size_fails(self) -> None:
        broken = VALID_FRONTMATTER.replace("tile_size: large", "tile_size: huge")
        self.repo.write_essay("broken", broken, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("tile_size" in e for e in errors))

    def test_series_with_zero_order_fails(self) -> None:
        broken = VALID_FRONTMATTER.replace(
            'series: ""\nseries_order: 0',
            'series: "example-series"\nseries_order: 0',
        )
        self.repo.write_essay("broken", broken, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("series_order" in e for e in errors))

    def test_hero_declared_but_missing_fails(self) -> None:
        self.repo.write_essay("broken", VALID_FRONTMATTER, hero=False)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("hero.svg" in e for e in errors))

    def test_lastmod_before_date_fails(self) -> None:
        broken = VALID_FRONTMATTER.replace("lastmod: 2026-04-20", "lastmod: 2026-04-01")
        self.repo.write_essay("broken", broken, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("lastmod" in e for e in errors))

    def test_unknown_cite_key_fails(self) -> None:
        body = VALID_FRONTMATTER + '\n{{< cite "missing-key" >}}\n'
        self.repo.write_essay("broken", body, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("missing-key" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail (no module yet)**

Run: `python3 -m unittest tools/test_check_fixtures.py -v`
Expected: ImportError / ModuleNotFoundError on `import check_fixtures`.

- [ ] **Step 3: Implement `tools/check-fixtures.py`**

Create `tools/check-fixtures.py`:

```python
#!/usr/bin/env python3
"""Essay fixture frontmatter linter.

Walks `content/essays/*/index.md`, validates frontmatter, and checks every
`{{< cite "key" >}}` reference resolves against `data/citations.yaml`.

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from datetime import date as Date
from pathlib import Path

REQUIRED_FIELDS = {
    "title", "date", "lastmod", "draft", "summary",
    "tags", "series", "series_order",
    "toc", "has_sidenotes", "has_citations", "has_footnotes",
    "has_math", "has_widgets", "has_video_sync",
}
ALLOWED_TILE_SIZE = {"large", "medium", "small"}

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
CITE_RE = re.compile(r'\{\{<\s*cite\s+"([^"]+)"\s*>\}\}')


def parse_frontmatter(text: str) -> dict[str, object] | None:
    """Parse YAML frontmatter — narrow subset, no third-party deps."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    out: dict[str, object] = {}
    for raw in m.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = parse_scalar(value.strip())
    return out


def parse_scalar(s: str) -> object:
    if s == "":
        return ""
    if s in ("true", "false"):
        return s == "true"
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        items = [it.strip() for it in inner.split(",")]
        return [it.strip('"').strip("'") for it in items]
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1]
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        y, m, d = (int(x) for x in s.split("-"))
        return Date(y, m, d)
    return s


def parse_citations_yaml(path: Path) -> set[str]:
    """Pull cite keys from data/citations.yaml — looks for two-space-indented
    keys directly under `citations:`."""
    if not path.exists():
        return set()
    keys: set[str] = set()
    in_citations = False
    for raw in path.read_text().splitlines():
        if raw.startswith("citations:"):
            in_citations = True
            continue
        if not in_citations:
            continue
        if raw and not raw.startswith(" "):
            in_citations = False
            continue
        m = re.match(r"^  ([a-zA-Z0-9_\-]+):\s*$", raw)
        if m:
            keys.add(m.group(1))
    return keys


def lint_essay(essay_dir: Path, valid_cite_keys: set[str]) -> list[str]:
    errors: list[str] = []
    md_path = essay_dir / "index.md"
    if not md_path.exists():
        return [f"{essay_dir}: no index.md"]
    text = md_path.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md_path}: no frontmatter"]

    missing = REQUIRED_FIELDS - fm.keys()
    for field in sorted(missing):
        errors.append(f"{md_path}: missing required field '{field}'")

    if "tile_size" in fm and fm["tile_size"] not in ALLOWED_TILE_SIZE:
        errors.append(
            f"{md_path}: tile_size '{fm['tile_size']}' not in {ALLOWED_TILE_SIZE}"
        )

    series = fm.get("series", "")
    series_order = fm.get("series_order", 0)
    if series and series_order == 0:
        errors.append(
            f"{md_path}: series '{series}' set but series_order is 0"
        )

    hero = fm.get("hero", "")
    if hero:
        if not (essay_dir / str(hero)).exists():
            errors.append(f"{md_path}: hero file '{hero}' not found in page bundle")

    date = fm.get("date")
    lastmod = fm.get("lastmod")
    if isinstance(date, Date) and isinstance(lastmod, Date) and lastmod < date:
        errors.append(f"{md_path}: lastmod {lastmod} is before date {date}")

    body = text[FRONTMATTER_RE.match(text).end():] if FRONTMATTER_RE.match(text) else ""
    for cite_key in CITE_RE.findall(body):
        if cite_key not in valid_cite_keys:
            errors.append(
                f"{md_path}: cite key '{cite_key}' not found in data/citations.yaml"
            )
    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    essays_dir = repo_root / "content" / "essays"
    citations_path = repo_root / "data" / "citations.yaml"
    valid_keys = parse_citations_yaml(citations_path)

    errors: list[str] = []
    if essays_dir.exists():
        for essay_dir in sorted(essays_dir.iterdir()):
            if not essay_dir.is_dir():
                continue
            errors.extend(lint_essay(essay_dir, valid_keys))

    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        print("Fixture lint failures:")
        for e in errors:
            print(f"  {e}")
    else:
        print("All essay fixtures pass linter.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tools/test_check_fixtures.py -v`
Expected: 8 tests, all pass.

- [ ] **Step 5: Run linter against current repo**

Run: `python3 tools/check-fixtures.py`
Expected: `All essay fixtures pass linter.` (no fixtures yet, so trivially passes).

- [ ] **Step 6: Commit**

```bash
git add tools/check-fixtures.py tools/test_check_fixtures.py
git commit -m "Add essay fixture frontmatter linter"
```

---

## Task 2: Wire `check-fixtures.py` into CI

**Files:**
- Modify: `.github/workflows/hugo.yaml` (add a step between "Setup Pages" and "Verify CSS contrast (WCAG)")

- [ ] **Step 1: Add the workflow step**

Edit `.github/workflows/hugo.yaml`. After the "Verify CSS contrast (WCAG)" step (currently between Setup Pages and Build), add a new step before Build:

Find:
```yaml
      - name: Verify CSS contrast (WCAG)
        run: python3 tools/check-contrast.py
      - name: Build with Hugo
```

Replace with:
```yaml
      - name: Verify CSS contrast (WCAG)
        run: python3 tools/check-contrast.py
      - name: Verify essay fixtures
        run: python3 tools/check-fixtures.py
      - name: Run linter unit tests
        run: python3 -m unittest tools/test_check_fixtures.py -v
      - name: Build with Hugo
```

- [ ] **Step 2: Run both checks locally to confirm green**

Run: `python3 tools/check-contrast.py && python3 tools/check-fixtures.py && python3 -m unittest tools/test_check_fixtures.py -v`
Expected: contrast passes, fixtures pass (none present), 8 unit tests pass.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "Wire essay fixture linter into Pages workflow"
```

---

## Task 3: Citations data fixture

**Files:**
- Create: `data/citations.yaml`

- [ ] **Step 1: Create the data file**

```yaml
# Fixture citations for essay layout development. Replaced by ox-hugo export
# in Phase 3 — same shape, real bib data.
citations:
  example-source-1:
    authors: ["Lastname, F.", "Othername, G."]
    year: 2020
    title: "Lorem ipsum dolor sit amet"
    venue: "Journal of Examples"
    url: "https://example.invalid/1"
    notes_ref: ""
  example-source-2:
    authors: ["Author, A."]
    year: 2024
    title: "Consectetur adipiscing elit"
    venue: "Proceedings of Things"
    url: "https://example.invalid/2"
    notes_ref: "example-note-slug"
  example-source-3:
    authors: ["Tertius, T.", "Quartus, Q.", "Quintus, Q."]
    year: 2018
    title: "Ut labore et dolore magna aliqua"
    venue: "Annual Review of Examples"
    url: "https://example.invalid/3"
    notes_ref: ""
```

- [ ] **Step 2: Verify linter still passes**

Run: `python3 tools/check-fixtures.py`
Expected: pass.

- [ ] **Step 3: Commit**

```bash
git add data/citations.yaml
git commit -m "Add citations fixture data for essay layout development"
```

---

## Task 4: Deferred-feature shortcode stubs

**Files:**
- Create: `layouts/shortcodes/spoiler.html`
- Create: `layouts/shortcodes/math.html`
- Create: `layouts/shortcodes/video-sync.html`
- Create: `layouts/shortcodes/widget.html`

Each is a single-line template emitting a container with the documented data-attribute hook. Fixtures use them; later slices replace the template body when the renderer arrives.

- [ ] **Step 1: Create `layouts/shortcodes/spoiler.html`**

```go-html-template
<span data-spoiler>{{ .Inner | markdownify }}</span>
```

- [ ] **Step 2: Create `layouts/shortcodes/math.html`**

```go-html-template
<code data-math>{{ .Inner }}</code>
```

- [ ] **Step 3: Create `layouts/shortcodes/video-sync.html`**

```go-html-template
<div data-video-sync data-src="{{ .Get "src" }}"></div>
```

- [ ] **Step 4: Create `layouts/shortcodes/widget.html`**

```go-html-template
<div data-widget data-widget-id="{{ .Get "id" }}"></div>
```

- [ ] **Step 5: Verify Hugo build succeeds**

Run: `hugo --minify`
Expected: build succeeds with 0 errors.

- [ ] **Step 6: Commit**

```bash
git add layouts/shortcodes/spoiler.html layouts/shortcodes/math.html layouts/shortcodes/video-sync.html layouts/shortcodes/widget.html
git commit -m "Add deferred-feature shortcode stubs (spoiler/math/video-sync/widget)"
```

---

## Task 5: Essays section bootstrap (`_index.md`, `list.html`, `single.html` minimal)

**Files:**
- Modify: `content/essays/_index.md`
- Create: `layouts/essays/list.html`
- Create: `layouts/essays/single.html`

Replace the "(Coming soon.)" placeholder with real section frontmatter + filler framing copy. Add minimal layouts that just render title + content + a list of posts. Each is upgraded in later tasks.

- [ ] **Step 1: Update `content/essays/_index.md`**

Replace contents with:

```markdown
---
title: 'Essays'
description: 'Long-form writing — the centerpiece.'
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
```

- [ ] **Step 2: Create `layouts/essays/list.html`**

```go-html-template
{{ define "main" }}
<section class="reading-column essays-index">
  <header class="essays-hero">
    <h1>{{ .Title }}</h1>
    {{ with .Content }}<div class="framing">{{ . }}</div>{{ end }}
  </header>

  {{ if eq (len .Pages) 0 }}
    <p class="meta">No essays yet.</p>
  {{ else }}
    <ul class="page-list">
      {{ range .Pages.ByDate.Reverse }}
        <li>
          <a href="{{ .RelPermalink }}">{{ .Title }}</a>
          <p class="page-list-desc">{{ .Summary }}</p>
        </li>
      {{ end }}
    </ul>
  {{ end }}
</section>
{{ end }}
```

- [ ] **Step 3: Create `layouts/essays/single.html`**

```go-html-template
{{ define "main" }}
<article class="reading-column essay">
  <header class="essay-header">
    <h1>{{ .Title }}</h1>
    <p class="meta">{{ .Date.Format "2 January 2006" }}</p>
  </header>
  <div class="essay-body">
    {{ .Content }}
  </div>
</article>
{{ end }}
```

- [ ] **Step 4: Verify Hugo builds + `/essays/` renders**

Run: `hugo --minify`
Expected: build success.

In `hugo server` → http://localhost:1313/essays/
Expected: page renders with "Essays" title, framing paragraph, and "No essays yet." message.

- [ ] **Step 5: Commit**

```bash
git add content/essays/_index.md layouts/essays/list.html layouts/essays/single.html
git commit -m "Bootstrap essays section with minimal list and single layouts"
```

---

## Task 6: First fixture — `example-essay-three` (minimal small)

**Files:**
- Create: `content/essays/example-essay-three/index.md`

Smallest fixture, exercises basic single-page render and a deferred spoiler stub.

- [ ] **Step 1: Create the fixture**

```markdown
---
title: "Example essay three"
date: 2026-03-01
lastmod: 2026-03-01
draft: false
summary: "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
tags: ["example-tag-a"]
series: ""
series_order: 0
tile_size: small
toc: false
has_sidenotes: false
has_citations: false
has_footnotes: false
has_math: false
has_widgets: false
has_video_sync: false
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. {{< spoiler >}}Lorem ipsum spoiler text — example one two three.{{< /spoiler >}}

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
```

- [ ] **Step 2: Verify linter passes**

Run: `python3 tools/check-fixtures.py`
Expected: pass.

- [ ] **Step 3: Verify Hugo build + render**

Run: `hugo --minify`
Expected: build success.

In `hugo server`:
- http://localhost:1313/essays/ → shows the post in the list
- http://localhost:1313/essays/example-essay-three/ → renders title, date, body, spoiler text inline (as a `<span data-spoiler>` — visually unchanged for now).

- [ ] **Step 4: Commit**

```bash
git add content/essays/example-essay-three/index.md
git commit -m "Add example-essay-three fixture (minimal small, spoiler stub)"
```

---

## Task 7: Essay meta partial

**Files:**
- Create: `layouts/partials/essay-meta.html`
- Modify: `assets/css/main.css` (append section)
- Modify: `layouts/essays/single.html` (use partial instead of inline meta)

Renders the meta line: date · reading-time · tags · series pill.

- [ ] **Step 1: Create `layouts/partials/essay-meta.html`**

```go-html-template
{{/* Meta line: date · reading-time · tags · series pill.
     Caller passes the page context (.). */}}
<p class="essay-meta">
  <time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date.Format "2 January 2006" }}</time>
  <span class="meta-sep">·</span>
  <span class="meta-reading-time">{{ .ReadingTime }} min</span>
  {{ with .Params.tags }}
    <span class="meta-sep">·</span>
    <span class="meta-tags">
      {{ range . }}
        <a href="{{ printf "/tags/%s/" (urlize .) | relURL }}" class="tag-chip">#{{ . }}</a>
      {{ end }}
    </span>
  {{ end }}
  {{ with .Params.series }}
    <span class="meta-sep">·</span>
    <span class="series-pill">{{ . }} (Part {{ $.Params.series_order }})</span>
  {{ end }}
</p>
```

- [ ] **Step 2: Append meta CSS to `assets/css/main.css`**

Add at the bottom of the file:

```css
/* ------------------------------------------------------------------
 * 10. Essay meta line
 * ------------------------------------------------------------------ */
.essay-meta {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 1rem;
}
.essay-meta .meta-sep { color: var(--color-ink-fade); }
.essay-meta .tag-chip {
  color: var(--color-ink-soft);
  text-decoration: none;
}
.essay-meta .tag-chip:hover { color: var(--color-burgundy); }
.essay-meta .series-pill {
  font-style: italic;
  color: var(--color-ink-soft);
}
```

- [ ] **Step 3: Update `layouts/essays/single.html` to use the partial**

Replace contents with:

```go-html-template
{{ define "main" }}
<article class="reading-column essay">
  <header class="essay-header">
    {{ partial "essay-meta.html" . }}
    <h1>{{ .Title }}</h1>
    {{ with .Params.summary }}<p class="lede">{{ . }}</p>{{ end }}
  </header>
  <div class="essay-body">
    {{ .Content }}
  </div>
</article>
{{ end }}
```

- [ ] **Step 4: Verify build + contrast still passes**

Run: `hugo --minify && python3 tools/check-contrast.py`
Expected: build success; contrast pass (no new color tokens introduced).

In `hugo server` → http://localhost:1313/essays/example-essay-three/
Expected: meta line shows "1 March 2026 · ≈1 min · #example-tag-a"; no series pill (series is empty).

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/essay-meta.html assets/css/main.css layouts/essays/single.html
git commit -m "Add essay meta partial (date · reading time · tags · series)"
```

---

## Task 8: Essay card partials + initial card CSS

**Files:**
- Create: `layouts/partials/essay-card.html`
- Create: `layouts/partials/essay-card-featured.html`
- Modify: `assets/css/main.css` (append section)
- Modify: `layouts/essays/list.html` (use card partial)

The card partial is the unit reused by the index, the homepage strip, and series-nav mini-cards. Featured variant adds the eyebrow line. Tile-size resolution is added in Task 9; this task ships flat cards in a simple grid.

- [ ] **Step 1: Create `layouts/partials/essay-card.html`**

```go-html-template
{{/* Standard essay card. Caller passes the page context. */}}
<li class="essay-card" data-tags="{{ delimit (.Params.tags | default slice) " " }}" data-series="{{ .Params.series | default "" }}" data-year="{{ .Date.Format "2006" }}">
  <a class="essay-card-link" href="{{ .RelPermalink }}">
    {{ with .Params.hero }}
      {{ $hero := $.Resources.Get . }}
      {{ if $hero }}<img class="essay-card-hero" src="{{ $hero.RelPermalink }}" alt="">{{ end }}
    {{ end }}
    <h3 class="essay-card-title">{{ .Title }}</h3>
    {{ with .Params.summary }}<p class="essay-card-summary">{{ . }}</p>{{ end }}
    {{ partial "essay-meta.html" . }}
  </a>
</li>
```

- [ ] **Step 2: Create `layouts/partials/essay-card-featured.html`**

```go-html-template
{{/* Featured essay card — adds eyebrow text. Caller passes the page context. */}}
<li class="essay-card essay-card-featured" data-tags="{{ delimit (.Params.tags | default slice) " " }}" data-series="{{ .Params.series | default "" }}" data-year="{{ .Date.Format "2006" }}">
  <a class="essay-card-link" href="{{ .RelPermalink }}">
    <span class="essay-card-eyebrow">{{ with .Params.series }}{{ . }}{{ else }}Featured{{ end }}</span>
    {{ with .Params.hero }}
      {{ $hero := $.Resources.Get . }}
      {{ if $hero }}<img class="essay-card-hero" src="{{ $hero.RelPermalink }}" alt="">{{ end }}
    {{ end }}
    <h3 class="essay-card-title">{{ .Title }}</h3>
    {{ with .Params.summary }}<p class="essay-card-summary">{{ . }}</p>{{ end }}
    {{ partial "essay-meta.html" . }}
  </a>
</li>
```

- [ ] **Step 3: Append card CSS to `assets/css/main.css`**

```css
/* ------------------------------------------------------------------
 * 11. Essay grid + cards
 * ------------------------------------------------------------------ */
.essay-grid {
  list-style: none;
  padding: 0;
  margin: 2rem 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.25rem;
}
@media (max-width: 900px) {
  .essay-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 600px) {
  .essay-grid { grid-template-columns: minmax(0, 1fr); }
}

.essay-card {
  background: var(--color-tile);
  border: 1px solid var(--color-rule);
  border-radius: 10px;
  overflow: hidden;
  transition: border-color 0.15s ease;
}
.essay-card:hover { border-color: var(--color-burgundy); }

.essay-card-link {
  display: block;
  padding: 1.25rem;
  color: var(--color-ink);
  text-decoration: none;
}
.essay-card-link:hover { text-decoration: none; }

.essay-card-eyebrow {
  display: block;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-ink-fade);
  margin-bottom: 0.5rem;
}
.essay-card-hero {
  width: 100%;
  height: auto;
  margin: -1.25rem -1.25rem 1rem;
  width: calc(100% + 2.5rem);
  display: block;
}
.essay-card-title {
  font-size: var(--text-md);
  margin: 0 0 0.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.essay-card-summary {
  color: var(--color-ink-soft);
  font-size: var(--text-sm);
  margin: 0 0 0.75rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.essay-card .essay-meta { margin-top: 0.5rem; font-size: var(--text-xs); }
```

- [ ] **Step 4: Update `layouts/essays/list.html` to use cards**

Replace contents with:

```go-html-template
{{ define "main" }}
<section class="essays-index">
  <header class="essays-hero reading-column">
    <h1>{{ .Title }}</h1>
    {{ with .Content }}<div class="framing">{{ . }}</div>{{ end }}
  </header>

  {{ if eq (len .Pages) 0 }}
    <p class="reading-column meta">No essays yet.</p>
  {{ else }}
    <ul class="essay-grid">
      {{ range .Pages.ByDate.Reverse }}
        {{ if .Params.featured }}
          {{ partial "essay-card-featured.html" . }}
        {{ else }}
          {{ partial "essay-card.html" . }}
        {{ end }}
      {{ end }}
    </ul>
  {{ end }}
</section>
{{ end }}
```

- [ ] **Step 5: Verify build + render**

Run: `hugo --minify && python3 tools/check-contrast.py`
Expected: build success; contrast pass.

In `hugo server` → http://localhost:1313/essays/
Expected: a single card for `example-essay-three` in a 3-column grid (1 occupied), with title + summary + meta line.

- [ ] **Step 6: Commit**

```bash
git add layouts/partials/essay-card.html layouts/partials/essay-card-featured.html assets/css/main.css layouts/essays/list.html
git commit -m "Add essay card partials and 3-column index grid"
```

---

## Task 9: Variable-tile Bento grid (`data-span` resolution + CSS)

**Files:**
- Modify: `layouts/partials/essay-card.html`
- Modify: `layouts/partials/essay-card-featured.html`
- Modify: `assets/css/main.css`

Resolve tile size and span per spec §4.2 priority order, write to `data-span` attribute, drive grid via CSS.

- [ ] **Step 1: Add tile-span computation to `essay-card.html`**

Replace contents with:

```go-html-template
{{/* Standard essay card with tile-size + span resolution.
     Priority: explicit tile_size > featured > active series > default.
     Span: featured → 2x1; hero → adds row span; defaults to 1x1. */}}
{{- $tile := .Params.tile_size -}}
{{- if not $tile -}}
  {{- if .Params.featured -}}{{- $tile = "large" -}}
  {{- else if .Params.series -}}{{- $tile = "medium" -}}
  {{- else -}}{{- $tile = "medium" -}}{{- end -}}
{{- end -}}
{{- $colSpan := 1 -}}{{- $rowSpan := 1 -}}
{{- if .Params.featured -}}{{- $colSpan = 2 -}}{{- end -}}
{{- if .Params.hero -}}{{- $rowSpan = 2 -}}{{- end -}}
{{- $span := printf "%dx%d" $colSpan $rowSpan -}}
<li class="essay-card" data-tile-size="{{ $tile }}" data-span="{{ $span }}" data-tags="{{ delimit (.Params.tags | default slice) " " }}" data-series="{{ .Params.series | default "" }}" data-year="{{ .Date.Format "2006" }}">
  <a class="essay-card-link" href="{{ .RelPermalink }}">
    {{ with .Params.hero }}
      {{ $hero := $.Resources.Get . }}
      {{ if $hero }}<img class="essay-card-hero" src="{{ $hero.RelPermalink }}" alt="">{{ end }}
    {{ end }}
    <h3 class="essay-card-title">{{ .Title }}</h3>
    {{ with .Params.summary }}<p class="essay-card-summary">{{ . }}</p>{{ end }}
    {{ partial "essay-meta.html" . }}
  </a>
</li>
```

- [ ] **Step 2: Add same logic to `essay-card-featured.html`**

Replace contents with:

```go-html-template
{{/* Featured essay card with tile-size + span resolution. */}}
{{- $tile := .Params.tile_size | default "large" -}}
{{- $colSpan := 2 -}}{{- $rowSpan := 1 -}}
{{- if .Params.hero -}}{{- $rowSpan = 2 -}}{{- end -}}
{{- $span := printf "%dx%d" $colSpan $rowSpan -}}
<li class="essay-card essay-card-featured" data-tile-size="{{ $tile }}" data-span="{{ $span }}" data-tags="{{ delimit (.Params.tags | default slice) " " }}" data-series="{{ .Params.series | default "" }}" data-year="{{ .Date.Format "2006" }}">
  <a class="essay-card-link" href="{{ .RelPermalink }}">
    <span class="essay-card-eyebrow">{{ with .Params.series }}{{ . }}{{ else }}Featured{{ end }}</span>
    {{ with .Params.hero }}
      {{ $hero := $.Resources.Get . }}
      {{ if $hero }}<img class="essay-card-hero" src="{{ $hero.RelPermalink }}" alt="">{{ end }}
    {{ end }}
    <h3 class="essay-card-title">{{ .Title }}</h3>
    {{ with .Params.summary }}<p class="essay-card-summary">{{ . }}</p>{{ end }}
    {{ partial "essay-meta.html" . }}
  </a>
</li>
```

- [ ] **Step 3: Append span CSS to the existing essay-grid section in `main.css`**

Add immediately after the existing `.essay-card .essay-meta` rule:

```css
/* Bento span rules — driven by data-span on the card */
.essay-card[data-span="2x1"] { grid-column: span 2; }
.essay-card[data-span="1x2"] { grid-row: span 2; }
.essay-card[data-span="2x2"] { grid-column: span 2; grid-row: span 2; }

.essay-card[data-tile-size="large"] .essay-card-title { font-size: var(--text-lg); }
.essay-card[data-tile-size="small"] .essay-card-title { font-size: var(--text-sm); }
.essay-card[data-tile-size="small"] .essay-card-summary { display: none; }

@media (max-width: 600px) {
  .essay-card[data-span] { grid-column: span 1; grid-row: span 1; }
}
```

- [ ] **Step 4: Verify build**

Run: `hugo --minify && python3 tools/check-contrast.py && python3 tools/check-fixtures.py`
Expected: all pass.

In `hugo server` → http://localhost:1313/essays/
Expected: small fixture renders without summary (`tile_size: small` hides it); single card occupies 1 column.

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/essay-card.html layouts/partials/essay-card-featured.html assets/css/main.css
git commit -m "Add Bento variable-tile grid (tile-size resolution + CSS spans)"
```

---

## Task 10: Fixture #1 — `example-essay-one` (large + featured + hero)

**Files:**
- Create: `content/essays/example-essay-one/index.md`
- Create: `content/essays/example-essay-one/hero.svg`

Largest fixture. Exercises featured + hero (2×2 span), TOC, sidenotes (×3), citations (×2), footnotes (×2), figures (×2), tags (×3), reading time. The shortcodes for sidenote/cite/figure don't exist yet — the fixture body uses raw markdown for sections that need shortcodes; specific shortcodes get filled in during their own tasks.

- [ ] **Step 1: Create the placeholder hero SVG**

Create `content/essays/example-essay-one/hero.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder hero illustration">
  <rect width="800" height="400" fill="#fdfcf8"/>
  <circle cx="200" cy="200" r="120" fill="none" stroke="#6b1f2c" stroke-width="3"/>
  <circle cx="600" cy="200" r="80" fill="none" stroke="#1e4060" stroke-width="3"/>
  <path d="M 120 280 Q 400 100 680 280" fill="none" stroke="#6b1f2c" stroke-width="2" stroke-dasharray="4 6"/>
  <text x="400" y="380" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" fill="#9a958e">EXAMPLE HERO — placeholder</text>
</svg>
```

- [ ] **Step 2: Create the fixture markdown**

Create `content/essays/example-essay-one/index.md`:

```markdown
---
title: "Example essay one"
date: 2026-04-12
lastmod: 2026-04-20
draft: false
summary: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
tags: ["example-tag-a", "example-tag-b", "example-tag-c"]
series: ""
series_order: 0
tile_size: large
featured: true
hero: hero.svg
toc: true
has_sidenotes: true
has_citations: true
has_footnotes: true
has_math: false
has_widgets: false
has_video_sync: false
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

## Section one — example heading

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. {{< cite "example-source-1" >}}

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.[^1]

## Section two — example heading

Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. {{< sidenote >}}Lorem ipsum sidenote — example one.{{< /sidenote >}}

## Section three — example heading

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium. {{< sidenote >}}Lorem ipsum sidenote — example two.{{< /sidenote >}}

## Section four — example heading

Totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. {{< cite "example-source-2" >}}

{{< figure src="hero.svg" caption="Example figure one — placeholder caption." alt="" >}}

Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit. {{< sidenote >}}Lorem ipsum sidenote — example three.{{< /sidenote >}}

## Section five — example heading

Sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.[^2]

{{< figure src="hero.svg" caption="Example figure two — placeholder caption." alt="" class="wide" >}}

Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet.

[^1]: Lorem ipsum footnote — example one two three.
[^2]: Lorem ipsum footnote — example four five six.
```

- [ ] **Step 3: Verify linter passes**

Run: `python3 tools/check-fixtures.py`
Expected: pass (cite keys exist; hero file exists).

- [ ] **Step 4: Verify Hugo build**

Run: `hugo --minify`
Expected: build success.

NOTE: at this point the `cite`, `sidenote`, and `figure` shortcodes don't exist yet. Hugo will emit warnings for missing shortcodes but will not fail. To suppress: skip if Hugo errors here — implement Tasks 11-13 first, then return to verify.

If `hugo --minify` errors on missing shortcodes, that's expected: continue to the next task and re-verify after Tasks 11-13 land.

- [ ] **Step 5: Commit**

```bash
git add content/essays/example-essay-one/
git commit -m "Add example-essay-one fixture (large+featured+hero, full chrome)"
```

---

## Task 11: Sidenote shortcode + CSS

**Files:**
- Create: `layouts/shortcodes/sidenote.html`
- Modify: `assets/css/main.css`

- [ ] **Step 1: Create `layouts/shortcodes/sidenote.html`**

```go-html-template
{{- /* Sidenote: emits a numbered marker + aside. Auto-numbered per page via scratch.
       Forbidden inside code blocks (errored by template). */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "sidenote-count" | default 0)) 1 -}}
{{- $page.Scratch.Set "sidenote-count" $n -}}
<span class="sidenote-marker" tabindex="0" role="button" aria-controls="sn-{{ $n }}" aria-label="Open sidenote {{ $n }}">{{ $n }}</span><aside class="sidenote" id="sn-{{ $n }}"><span class="sidenote-num">{{ $n }}.</span> {{ .Inner | markdownify }}</aside>
```

- [ ] **Step 2: Append sidenote CSS to `main.css`**

```css
/* ------------------------------------------------------------------
 * 12. Sidenotes
 * ------------------------------------------------------------------ */
.sidenote-marker {
  display: inline-block;
  font-family: var(--font-ui);
  font-size: 0.7em;
  vertical-align: super;
  color: var(--color-burgundy);
  padding: 0 0.15em;
  cursor: pointer;
}
.sidenote {
  display: block;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
  margin: 0.5rem 0 1rem;
  padding-left: 1rem;
  border-left: 2px solid var(--color-rule);
}
.sidenote-num {
  color: var(--color-burgundy);
  font-weight: 600;
  margin-right: 0.25rem;
}

/* On wide viewports, float sidenotes into the right rail (added in Task 14). */
@media (min-width: 1100px) {
  .essay-body .sidenote {
    float: right;
    clear: right;
    width: 250px;
    margin-right: -290px;
    padding-left: 0;
    border-left: 0;
    border-top: 1px solid var(--color-rule);
    padding-top: 0.5rem;
  }
}
```

- [ ] **Step 3: Verify build + render fixture #1**

Run: `hugo --minify && python3 tools/check-fixtures.py`
Expected: pass.

In `hugo server` → http://localhost:1313/essays/example-essay-one/
Expected: sidenote markers (small superscript "1", "2", "3" in burgundy) appear inline; sidenote bodies render below the paragraphs (rail layout doesn't kick in until Task 14 adds the three-zone container).

- [ ] **Step 4: Commit**

```bash
git add layouts/shortcodes/sidenote.html assets/css/main.css
git commit -m "Add sidenote shortcode and base styling"
```

---

## Task 12: Cite shortcode + references partial

**Files:**
- Create: `layouts/shortcodes/cite.html`
- Create: `layouts/partials/essay-references.html`
- Modify: `layouts/essays/single.html` (add references partial call)
- Modify: `assets/css/main.css`

- [ ] **Step 1: Create `layouts/shortcodes/cite.html`**

```go-html-template
{{- /* Cite shortcode: looks up the key in site.Data.citations.citations,
       emits an inline <cite> with data-cite-key, jump-anchored to the
       references list. Aborts the build if the key is missing. */ -}}
{{- $key := .Get 0 -}}
{{- $citations := site.Data.citations.citations -}}
{{- $entry := index $citations $key -}}
{{- if not $entry -}}
  {{- errorf "cite: unknown citation key %q in %s" $key .Page.RelPermalink -}}
{{- end -}}
{{- $authors := slice -}}
{{- range $entry.authors -}}
  {{- $last := index (split . ",") 0 -}}
  {{- $authors = $authors | append $last -}}
{{- end -}}
{{- $label := "" -}}
{{- if eq (len $authors) 1 -}}{{- $label = printf "%s %d" (index $authors 0) $entry.year -}}
{{- else if eq (len $authors) 2 -}}{{- $label = printf "%s & %s %d" (index $authors 0) (index $authors 1) $entry.year -}}
{{- else -}}{{- $label = printf "%s et al. %d" (index $authors 0) $entry.year -}}{{- end -}}
{{- /* Track keys used on this page in scratch (collected by essay-references partial) */ -}}
{{- $used := .Page.Scratch.Get "cite-keys" | default slice -}}
{{- if not (in $used $key) -}}{{- $used = $used | append $key -}}{{- end -}}
{{- .Page.Scratch.Set "cite-keys" $used -}}
<cite class="citation" data-cite-key="{{ $key }}"><a href="#ref-{{ $key }}">[{{ $label }}]</a></cite>
```

- [ ] **Step 2: Create `layouts/partials/essay-references.html`**

```go-html-template
{{/* References list rendered at the end of the post.
     Reads keys collected by the cite shortcode via scratch. */}}
{{- $used := .Scratch.Get "cite-keys" | default slice -}}
{{- if $used -}}
  {{- $citations := site.Data.citations.citations -}}
  <section class="essay-references" aria-labelledby="references-heading">
    <h2 id="references-heading">References</h2>
    <ol>
      {{- range $used -}}
        {{- $entry := index $citations . -}}
        <li id="ref-{{ . }}">
          {{ delimit $entry.authors ", " }} ({{ $entry.year }}).
          <em>{{ $entry.title }}</em>.
          {{ $entry.venue }}.
          {{ with $entry.url }}<a href="{{ . }}" rel="noopener">→ source</a>{{ end }}
        </li>
      {{- end -}}
    </ol>
  </section>
{{- end -}}
```

- [ ] **Step 3: Update `layouts/essays/single.html`**

Replace contents with:

```go-html-template
{{ define "main" }}
<article class="reading-column essay">
  <header class="essay-header">
    {{ partial "essay-meta.html" . }}
    <h1>{{ .Title }}</h1>
    {{ with .Params.summary }}<p class="lede">{{ . }}</p>{{ end }}
  </header>
  <div class="essay-body">
    {{ .Content }}
  </div>
  {{ if .Params.has_citations }}
    {{ partial "essay-references.html" . }}
  {{ end }}
</article>
{{ end }}
```

- [ ] **Step 4: Append references CSS to `main.css`**

```css
/* ------------------------------------------------------------------
 * 13. Citations + references
 * ------------------------------------------------------------------ */
.citation {
  font-style: normal;
  color: var(--color-burgundy);
}
.citation a { color: inherit; text-decoration: none; }
.citation a:hover { text-decoration: underline; }

.essay-references {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-rule);
  font-size: var(--text-sm);
}
.essay-references ol { padding-left: 1.5rem; }
.essay-references li { margin-bottom: 0.75rem; line-height: 1.5; }
.essay-references li:target { background: rgba(107, 31, 44, 0.08); padding: 0.25rem 0.5rem; border-radius: 4px; }
```

- [ ] **Step 5: Verify build + render**

Run: `hugo --minify && python3 tools/check-fixtures.py`
Expected: pass.

In `hugo server` → http://localhost:1313/essays/example-essay-one/
Expected: inline citations show as `[Lastname & Othername 2020]` in burgundy; clicking jumps to references list at end of post; references section renders only the two cited entries (1 and 2).

- [ ] **Step 6: Commit**

```bash
git add layouts/shortcodes/cite.html layouts/partials/essay-references.html layouts/essays/single.html assets/css/main.css
git commit -m "Add cite shortcode and references partial with data-cite-key hook"
```

---

## Task 13: Figure shortcode + CSS (with `wide` breakout)

**Files:**
- Create: `layouts/shortcodes/figure.html` (overrides Hugo default)
- Modify: `assets/css/main.css`

- [ ] **Step 1: Create `layouts/shortcodes/figure.html`**

```go-html-template
{{- /* Figure shortcode: semantic <figure><img><figcaption>.
       Supports class="wide" for breakout figures. Resolves src
       from page bundle resources first, falls back to literal URL. */ -}}
{{- $src := .Get "src" -}}
{{- $alt := .Get "alt" | default "" -}}
{{- $caption := .Get "caption" -}}
{{- $class := .Get "class" -}}
{{- $resource := .Page.Resources.Get $src -}}
{{- $url := $src -}}
{{- if $resource -}}{{- $url = $resource.RelPermalink -}}{{- end -}}
<figure class="essay-figure{{ with $class }} {{ . }}{{ end }}">
  <img src="{{ $url }}" alt="{{ $alt }}">
  {{- with $caption -}}<figcaption>{{ . | markdownify }}</figcaption>{{- end -}}
</figure>
```

- [ ] **Step 2: Append figure CSS to `main.css`**

```css
/* ------------------------------------------------------------------
 * 14. Figures
 * ------------------------------------------------------------------ */
.essay-figure {
  margin: 2rem 0;
}
.essay-figure img {
  width: 100%;
  height: auto;
  border-radius: 6px;
  display: block;
}
.essay-figure figcaption {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
  text-align: center;
  margin-top: 0.5rem;
}

/* Wide breakout — extends beyond reading column */
.essay-figure.wide {
  margin-left: calc((var(--reading-column) - 920px) / 2);
  margin-right: calc((var(--reading-column) - 920px) / 2);
  max-width: 920px;
}
@media (max-width: 920px) {
  .essay-figure.wide { margin-left: 0; margin-right: 0; max-width: 100%; }
}
```

- [ ] **Step 3: Verify build + render**

Run: `hugo --minify`
Expected: build success.

In `hugo server` → http://localhost:1313/essays/example-essay-one/
Expected: two figures render; second one (`class="wide"`) extends past the reading column on wide viewports.

- [ ] **Step 4: Commit**

```bash
git add layouts/shortcodes/figure.html assets/css/main.css
git commit -m "Add figure shortcode with wide breakout support"
```

---

## Task 14: TOC partial + three-zone layout CSS

**Files:**
- Create: `layouts/partials/essay-toc.html`
- Modify: `layouts/essays/single.html`
- Modify: `assets/css/main.css`

The three-zone layout uses CSS Grid: TOC rail | reading column | sidenote rail. Below 1024px it collapses to a single column with TOC as a `<details>` disclosure.

- [ ] **Step 1: Create `layouts/partials/essay-toc.html`**

```go-html-template
{{/* Server-rendered TOC. essay.js (existing nav.js) attaches the
     active-link highlighter via IntersectionObserver. */}}
{{ if .TableOfContents }}
<nav class="essay-toc" aria-label="Table of contents">
  <details open>
    <summary>Contents</summary>
    {{ .TableOfContents }}
  </details>
</nav>
{{ end }}
```

- [ ] **Step 2: Update `layouts/essays/single.html` to use the three-zone shell**

Replace contents with:

```go-html-template
{{ define "main" }}
<article class="essay" data-toc="{{ if not (eq .Params.toc false) }}true{{ end }}">
  <header class="essay-header reading-column">
    {{ with .Params.hero }}
      {{ $hero := $.Resources.Get . }}
      {{ if $hero }}<img class="essay-hero" src="{{ $hero.RelPermalink }}" alt="">{{ end }}
    {{ end }}
    {{ partial "essay-meta.html" . }}
    <h1>{{ .Title }}</h1>
    {{ with .Params.summary }}<p class="lede">{{ . }}</p>{{ end }}
  </header>

  <div class="essay-layout">
    {{ if not (eq .Params.toc false) }}
      <div class="essay-toc-zone">
        {{ partial "essay-toc.html" . }}
      </div>
    {{ end }}

    <div class="essay-body reading-column">
      {{ .Content }}
    </div>

    <div class="essay-sidenote-zone" aria-hidden="true"></div>
  </div>

  {{ if .Params.has_citations }}
    <div class="reading-column">{{ partial "essay-references.html" . }}</div>
  {{ end }}
</article>
{{ end }}
```

- [ ] **Step 3: Append three-zone + TOC + hero CSS to `main.css`**

```css
/* ------------------------------------------------------------------
 * 15. Essay three-zone layout (TOC | body | sidenote rail)
 * ------------------------------------------------------------------ */
.essay { margin-bottom: 3rem; }
.essay-hero {
  margin: 0 auto 2rem;
  max-width: 920px;
  width: 100%;
  height: auto;
  display: block;
  border-radius: 8px;
}
.essay-header { margin-bottom: 2rem; }
.essay-header h1 {
  font-size: var(--text-2xl);
  margin: 0.5rem 0 1rem;
}
.essay-header .lede {
  font-size: var(--text-md);
  color: var(--color-ink-soft);
  font-style: italic;
}

.essay-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}
@media (min-width: 1100px) {
  .essay-layout {
    grid-template-columns: 200px minmax(0, var(--reading-column)) 250px;
    justify-content: center;
    gap: 2rem;
  }
}

.essay-toc-zone { font-family: var(--font-ui); }
.essay-toc { font-size: var(--text-sm); }
.essay-toc summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 0.5rem;
}
.essay-toc ul {
  list-style: none;
  padding-left: 0;
  margin: 0;
}
.essay-toc li { margin: 0.35rem 0; }
.essay-toc a {
  color: var(--color-ink-soft);
  text-decoration: none;
}
.essay-toc a:hover { color: var(--color-burgundy); }
.essay-toc #TableOfContents > ul > li > ul { padding-left: 1rem; }

@media (min-width: 1100px) {
  .essay-toc-zone { position: sticky; top: 2rem; align-self: start; max-height: calc(100vh - 4rem); overflow-y: auto; }
  .essay-toc details { open: true; }
  .essay-toc summary { display: none; }
}

.essay-sidenote-zone { display: none; }
```

- [ ] **Step 4: Verify build + render**

Run: `hugo --minify && python3 tools/check-contrast.py`
Expected: pass.

In `hugo server` → http://localhost:1313/essays/example-essay-one/
Expected:
- Wide viewport (>1100px): TOC rail appears on left, body in center, hero at top spanning content width.
- Narrow viewport (<1100px): TOC collapses to "Contents" disclosure above body.

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/essay-toc.html layouts/essays/single.html assets/css/main.css
git commit -m "Add essay TOC partial and three-zone reading layout"
```

---

## Task 15: Fixture #2 — `example-essay-two` (medium + code-heavy + math filler)

**Files:**
- Create: `content/essays/example-essay-two/index.md`

- [ ] **Step 1: Create the fixture**

```markdown
---
title: "Example essay two"
date: 2026-04-01
lastmod: 2026-04-01
draft: false
summary: "Lorem ipsum example two — exercises code highlighting and math placeholder."
tags: ["example-tag-a", "example-tag-c"]
series: ""
series_order: 0
tile_size: medium
toc: true
has_sidenotes: false
has_citations: false
has_footnotes: true
has_math: true
has_widgets: false
has_video_sync: false
---

Lorem ipsum dolor sit amet — example body for code highlighting tests.

## Section one — example heading

Python example block:

```python
def example_function(x: int, y: int) -> int:
    """Lorem ipsum docstring."""
    return x + y

print(example_function(1, 2))
```

## Section two — example heading

Go example block:

```go
package main

import "fmt"

func main() {
    fmt.Println("Lorem ipsum")
}
```

JavaScript example block:

```javascript
function example(a, b) {
  return a + b;
}
console.log(example(1, 2));
```

Inline math placeholder: {{< math >}}\alpha + \beta = \gamma{{< /math >}}.[^1]

[^1]: Lorem ipsum footnote — example one.
```

- [ ] **Step 2: Verify linter + build**

Run: `python3 tools/check-fixtures.py && hugo --minify`
Expected: pass.

In `hugo server` → http://localhost:1313/essays/example-essay-two/
Expected: three code blocks render with Dracula chroma highlighting; math expression renders as `<code data-math>\alpha + \beta = \gamma</code>` (inline mono code).

In `hugo server` → http://localhost:1313/essays/
Expected: two cards now in the grid; the new one is medium tile-size (no span).

- [ ] **Step 3: Commit**

```bash
git add content/essays/example-essay-two/
git commit -m "Add example-essay-two fixture (medium, code-heavy, math stub)"
```

---

## Task 16: `essay.js` module (popups + smooth-scroll + cite hook + reduced-motion)

**Files:**
- Create: `assets/js/essay.js`
- Modify: `assets/js/index.js`

`assets/js/nav.js` already handles TOC scroll-spy. `essay.js` adds: sidenote/footnote popup affordances on narrow viewports, smooth-scroll on TOC clicks (with `prefers-reduced-motion` respect), and a no-op citation hover-card hook for Phase 3.

- [ ] **Step 1: Create `assets/js/essay.js`**

```javascript
// Essay-specific progressive enhancements.
// - Sidenote/footnote popup on narrow viewports
// - Smooth-scroll on TOC clicks (respects prefers-reduced-motion)
// - Citation hover-card hook (no-op placeholder for Phase 3)
//
// Guards on .essay-body presence; bails on non-essay pages.

const RAIL_BREAKPOINT = 1100;

function reducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function isNarrow() {
  return window.innerWidth < RAIL_BREAKPOINT;
}

function setupSidenotePopups() {
  const markers = document.querySelectorAll('.essay-body .sidenote-marker');
  markers.forEach((marker) => {
    marker.addEventListener('click', (e) => {
      if (!isNarrow()) return;
      e.preventDefault();
      const id = marker.getAttribute('aria-controls');
      const aside = id ? document.getElementById(id) : null;
      if (!aside) return;
      aside.classList.toggle('is-open');
    });
    marker.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        marker.click();
      }
    });
  });

  document.addEventListener('click', (e) => {
    if (!(e.target instanceof Element)) return;
    if (e.target.closest('.sidenote-marker') || e.target.closest('.sidenote.is-open')) return;
    document.querySelectorAll('.sidenote.is-open').forEach((el) => el.classList.remove('is-open'));
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.sidenote.is-open').forEach((el) => el.classList.remove('is-open'));
    }
  });
}

function setupTocSmoothScroll() {
  const tocLinks = document.querySelectorAll('.essay-toc a[href^="#"]');
  tocLinks.forEach((link) => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      if (!href) return;
      const target = document.querySelector(href);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({
        behavior: reducedMotion() ? 'auto' : 'smooth',
        block: 'start'
      });
      history.pushState(null, '', href);
    });
  });
}

function setupCitationHook() {
  // Placeholder — Phase 3 will attach a hover-card here. For now we just
  // mark the elements so future code can find them without a markup change.
  document.querySelectorAll('[data-cite-key]').forEach((el) => {
    el.classList.add('citation-hookable');
  });
}

function init() {
  if (!document.querySelector('.essay-body')) return;
  setupSidenotePopups();
  setupTocSmoothScroll();
  setupCitationHook();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
```

- [ ] **Step 2: Update `assets/js/index.js` to import the module**

Replace contents with:

```javascript
import './toggle-theme.js';
import './nav.js';
import './essay.js';
```

- [ ] **Step 3: Append sidenote-popup CSS to `main.css`**

Add to the existing sidenote section:

```css
/* Narrow-viewport popup behavior — only when essay.js is loaded */
@media (max-width: 1099px) {
  .essay-body .sidenote {
    display: none;
    position: absolute;
    width: min(280px, 90vw);
    background: var(--color-tile);
    border: 1px solid var(--color-rule);
    border-radius: 8px;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    padding: 0.75rem 1rem;
    z-index: 10;
    margin-top: 0.5rem;
  }
  .essay-body .sidenote.is-open { display: block; }
  /* No-JS fallback: show inline (sidenotes always visible) */
  html.no-js .essay-body .sidenote { display: block; position: static; }
}
```

- [ ] **Step 4: Verify build + behavior**

Run: `hugo --minify`
Expected: build success. The bundled JS file (in `public/js/bundle.<hash>.js`) should grow by ~3-4 KB.

In `hugo server` → http://localhost:1313/essays/example-essay-one/
Expected:
- Wide: sidenotes float in the right rail (existing CSS); TOC click smooth-scrolls.
- Narrow (<1100px): sidenotes hidden until marker clicked; popup opens; click outside / Esc closes.
- Reduced motion (system preference): TOC click jumps without smooth animation.
- DevTools console: no errors.

- [ ] **Step 5: Commit**

```bash
git add assets/js/essay.js assets/js/index.js assets/css/main.css
git commit -m "Add essay.js for sidenote popups, smooth scroll, citation hook"
```

---

## Task 17: Filter chips (rendering + CSS + JS behavior)

**Files:**
- Modify: `layouts/essays/list.html`
- Modify: `assets/css/main.css`
- Modify: `assets/js/essay.js`

Render tag/series/year chips with suppression rule (skip dimension if <2 distinct values). Tag and series chips link to taxonomy pages (no-JS fallback). Year chips are inert spans (JS-only filter).

- [ ] **Step 1: Update `layouts/essays/list.html`**

Replace contents with:

```go-html-template
{{ define "main" }}
<section class="essays-index">
  <header class="essays-hero reading-column">
    <h1>{{ .Title }}</h1>
    {{ with .Content }}<div class="framing">{{ . }}</div>{{ end }}
  </header>

  {{ if eq (len .Pages) 0 }}
    <p class="reading-column meta">No essays yet.</p>
  {{ else }}
    {{/* Collect dimensions from pages */}}
    {{ $tags := slice }}
    {{ $seriesList := slice }}
    {{ $years := slice }}
    {{ range .Pages }}
      {{ range .Params.tags }}
        {{ if not (in $tags .) }}{{ $tags = $tags | append . }}{{ end }}
      {{ end }}
      {{ with .Params.series }}
        {{ if not (in $seriesList .) }}{{ $seriesList = $seriesList | append . }}{{ end }}
      {{ end }}
      {{ $y := .Date.Format "2006" }}
      {{ if not (in $years $y) }}{{ $years = $years | append $y }}{{ end }}
    {{ end }}

    <nav class="filter-strip" aria-label="Filter essays">
      {{ if ge (len $tags) 2 }}
        <div class="filter-dimension" data-dim="tag">
          <span class="filter-label">Tags</span>
          <button class="filter-chip is-active" data-filter="all">All</button>
          {{ range $tags }}
            <a class="filter-chip" data-filter="{{ . }}" href="{{ printf "/tags/%s/" (urlize .) | relURL }}">#{{ . }}</a>
          {{ end }}
        </div>
      {{ end }}
      {{ if ge (len $seriesList) 2 }}
        <div class="filter-dimension" data-dim="series">
          <span class="filter-label">Series</span>
          <button class="filter-chip is-active" data-filter="all">All</button>
          {{ range $seriesList }}
            <a class="filter-chip" data-filter="{{ . }}" href="{{ printf "/series/%s/" (urlize .) | relURL }}">{{ . }}</a>
          {{ end }}
        </div>
      {{ end }}
      {{ if ge (len $years) 2 }}
        <div class="filter-dimension" data-dim="year">
          <span class="filter-label">Year</span>
          <button class="filter-chip is-active" data-filter="all">All</button>
          {{ range $years }}
            <span class="filter-chip" data-filter="{{ . }}" role="button" tabindex="0">{{ . }}</span>
          {{ end }}
        </div>
      {{ end }}
    </nav>

    <ul class="essay-grid">
      {{ range .Pages.ByDate.Reverse }}
        {{ if .Params.featured }}
          {{ partial "essay-card-featured.html" . }}
        {{ else }}
          {{ partial "essay-card.html" . }}
        {{ end }}
      {{ end }}
    </ul>
  {{ end }}
</section>
{{ end }}
```

- [ ] **Step 2: Append filter-strip CSS to `main.css`**

```css
/* ------------------------------------------------------------------
 * 16. Filter strip (essays index)
 * ------------------------------------------------------------------ */
.filter-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
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

/* Filter state — applied by essay.js */
.essay-grid[data-filter-state] .essay-card { display: none; }
.essay-grid[data-filter-state="all"] .essay-card { display: block; }
```

- [ ] **Step 3: Add filter behavior to `assets/js/essay.js`**

Append before the existing `init` function:

```javascript
function setupFilterChips() {
  const grid = document.querySelector('.essay-grid');
  const strip = document.querySelector('.filter-strip');
  if (!grid || !strip) return;

  function applyFilter(dim, value) {
    grid.setAttribute('data-filter-state', value === 'all' ? 'all' : `${dim}:${value}`);
    grid.querySelectorAll('.essay-card').forEach((card) => {
      if (value === 'all') {
        card.style.display = '';
        return;
      }
      const cardValue = card.getAttribute(`data-${dim === 'tag' ? 'tags' : dim}`) || '';
      const matches = dim === 'tag'
        ? cardValue.split(' ').includes(value)
        : cardValue === value;
      card.style.display = matches ? '' : 'none';
    });
  }

  strip.querySelectorAll('.filter-dimension').forEach((dimEl) => {
    const dim = dimEl.getAttribute('data-dim');
    if (!dim) return;
    dimEl.querySelectorAll('.filter-chip').forEach((chip) => {
      const handler = (e) => {
        e.preventDefault();
        // Clear all chip active states across all dimensions
        strip.querySelectorAll('.filter-chip').forEach((c) => c.classList.remove('is-active'));
        // Within each other dimension, mark "all" active
        strip.querySelectorAll('.filter-dimension').forEach((other) => {
          if (other !== dimEl) {
            const allChip = other.querySelector('.filter-chip[data-filter="all"]');
            if (allChip) allChip.classList.add('is-active');
          }
        });
        chip.classList.add('is-active');
        const value = chip.getAttribute('data-filter') || 'all';
        applyFilter(dim, value);
      };
      chip.addEventListener('click', handler);
      if (chip.tagName === 'SPAN') {
        chip.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') handler(e);
        });
      }
    });
  });

  // Initial state
  grid.setAttribute('data-filter-state', 'all');
}
```

Then update `init` to call it:

```javascript
function init() {
  if (!document.querySelector('.essay-body') && !document.querySelector('.essay-grid')) return;
  setupSidenotePopups();
  setupTocSmoothScroll();
  setupCitationHook();
  setupFilterChips();
}
```

- [ ] **Step 4: Verify build + behavior**

Run: `hugo --minify && python3 tools/check-contrast.py`
Expected: pass.

In `hugo server` → http://localhost:1313/essays/
Expected: with two fixtures (essay-one and essay-two) sharing tags `example-tag-a` and `example-tag-c`, the Tag dimension renders chips. Series dimension is suppressed (<2 series). Year dimension is suppressed (only 2026). Click `#example-tag-c` → only essay-two visible (essay-three doesn't have `example-tag-c`). Click `All` → both visible.

- [ ] **Step 5: Commit**

```bash
git add layouts/essays/list.html assets/css/main.css assets/js/essay.js
git commit -m "Add filter chips for /essays/ index (tag/series/year, suppression rule)"
```

---

## Task 18: Series navigation partial + CSS

**Files:**
- Create: `layouts/partials/essay-series-nav.html`
- Modify: `layouts/essays/single.html`
- Modify: `assets/css/main.css`

- [ ] **Step 1: Create `layouts/partials/essay-series-nav.html`**

```go-html-template
{{- /* Series navigation — prev/next + "Part N of M".
       Walks all essays sharing the .Params.series, ordered by series_order. */ -}}
{{- $current := . -}}
{{- $seriesName := .Params.series -}}
{{- $all := where site.RegularPages "Section" "essays" -}}
{{- $siblings := where $all "Params.series" $seriesName -}}
{{- $sorted := sort $siblings "Params.series_order" "asc" -}}
{{- $count := len $sorted -}}
{{- $idx := -1 -}}
{{- range $i, $p := $sorted -}}
  {{- if eq $p.RelPermalink $current.RelPermalink -}}{{- $idx = $i -}}{{- end -}}
{{- end -}}
{{- $prev := false -}}{{- $next := false -}}
{{- if gt $idx 0 -}}{{- $prev = index $sorted (sub $idx 1) -}}{{- end -}}
{{- if and (ge $idx 0) (lt $idx (sub $count 1)) -}}{{- $next = index $sorted (add $idx 1) -}}{{- end -}}
<nav class="essay-series-nav" aria-label="Series navigation">
  <p class="series-position">{{ $seriesName }} — Part {{ .Params.series_order }} of {{ $count }}</p>
  <div class="series-links">
    {{ if $prev }}
      <a class="series-prev" href="{{ $prev.RelPermalink }}">← {{ $prev.Title }}</a>
    {{ end }}
    {{ if $next }}
      <a class="series-next" href="{{ $next.RelPermalink }}">{{ $next.Title }} →</a>
    {{ end }}
  </div>
</nav>
```

- [ ] **Step 2: Update `layouts/essays/single.html` to call series-nav**

Replace the closing block (after references) with:

Find:
```go-html-template
  {{ if .Params.has_citations }}
    <div class="reading-column">{{ partial "essay-references.html" . }}</div>
  {{ end }}
</article>
```

Replace with:
```go-html-template
  {{ if .Params.has_citations }}
    <div class="reading-column">{{ partial "essay-references.html" . }}</div>
  {{ end }}

  {{ if .Params.series }}
    <div class="reading-column">{{ partial "essay-series-nav.html" . }}</div>
  {{ end }}
</article>
```

- [ ] **Step 3: Append series-nav CSS to `main.css`**

```css
/* ------------------------------------------------------------------
 * 17. Series nav
 * ------------------------------------------------------------------ */
.essay-series-nav {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-rule);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
}
.series-position {
  color: var(--color-ink-fade);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: var(--text-xs);
  margin: 0 0 0.5rem;
}
.series-links {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.series-prev, .series-next {
  color: var(--color-ink);
  text-decoration: none;
}
.series-prev:hover, .series-next:hover { color: var(--color-burgundy); text-decoration: underline; }
.series-next { margin-left: auto; }
```

- [ ] **Step 4: Verify build (no series fixtures yet — should still build)**

Run: `hugo --minify`
Expected: build success.

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/essay-series-nav.html layouts/essays/single.html assets/css/main.css
git commit -m "Add series navigation partial and styling"
```

---

## Task 19: Series fixtures (#4 and #5) + part-1 hero

**Files:**
- Create: `content/essays/example-series-part-1/index.md`
- Create: `content/essays/example-series-part-1/hero.svg`
- Create: `content/essays/example-series-part-2/index.md`

- [ ] **Step 1: Create part-1 placeholder hero**

Create `content/essays/example-series-part-1/hero.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder hero illustration">
  <rect width="800" height="400" fill="#fdfcf8"/>
  <rect x="120" y="120" width="200" height="160" fill="none" stroke="#1e4060" stroke-width="3"/>
  <rect x="480" y="120" width="200" height="160" fill="none" stroke="#6b1f2c" stroke-width="3"/>
  <line x1="320" y1="200" x2="480" y2="200" stroke="#1e4060" stroke-width="2" stroke-dasharray="4 4"/>
  <text x="400" y="380" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" fill="#9a958e">EXAMPLE HERO — placeholder</text>
</svg>
```

- [ ] **Step 2: Create part-1 markdown**

Create `content/essays/example-series-part-1/index.md`:

```markdown
---
title: "Example series — part one"
date: 2026-02-15
lastmod: 2026-02-15
draft: false
summary: "Lorem ipsum series example, part one. Exercises series navigation."
tags: ["example-tag-b"]
series: "example-series"
series_order: 1
hero: hero.svg
toc: true
has_sidenotes: false
has_citations: true
has_footnotes: false
has_math: false
has_widgets: false
has_video_sync: true
---

Lorem ipsum series part one body. {{< cite "example-source-3" >}}

## Section one

Lorem ipsum dolor sit amet, consectetur adipiscing elit.

{{< video-sync src="/example-video.mp4" >}}

## Section two

Sed do eiusmod tempor incididunt ut labore.
```

- [ ] **Step 3: Create part-2 markdown**

Create `content/essays/example-series-part-2/index.md`:

```markdown
---
title: "Example series — part two"
date: 2026-02-22
lastmod: 2026-02-22
draft: false
summary: "Lorem ipsum series example, part two. Continues from part one."
tags: ["example-tag-b"]
series: "example-series"
series_order: 2
toc: true
has_sidenotes: false
has_citations: false
has_footnotes: true
has_math: false
has_widgets: true
has_video_sync: false
---

Lorem ipsum series part two body, picking up from part one.

## Section one

```rust
fn example_function(x: i32, y: i32) -> i32 {
    x + y
}
```

## Section two

{{< widget id="example-widget-1" >}}

[^1]: Lorem ipsum footnote — example.
```

- [ ] **Step 4: Verify linter + build**

Run: `python3 tools/check-fixtures.py && hugo --minify`
Expected: pass.

In `hugo server`:
- http://localhost:1313/essays/ → four cards now; series tag/series chip strip should now appear since series count is now 1 (still suppressed; wait — `example-series` is one series, so series strip stays suppressed). Tag chip strip now shows three tags.
- http://localhost:1313/essays/example-series-part-1/ → series nav at bottom: "example-series — Part 1 of 2" with "Example series — part two →" next link. Video-sync stub renders as empty `<div data-video-sync>` (invisible).
- http://localhost:1313/essays/example-series-part-2/ → series nav: "Part 2 of 2" with "← Example series — part one" prev link. Widget stub renders as empty `<div data-widget>`.

- [ ] **Step 5: Commit**

```bash
git add content/essays/example-series-part-1/ content/essays/example-series-part-2/
git commit -m "Add example-series fixtures (parts 1+2) with deferred-feature stubs"
```

---

## Task 20: Fixture #6 — `example-figures-essay` (figure-heavy)

**Files:**
- Create: `content/essays/example-figures-essay/index.md`
- Create: `content/essays/example-figures-essay/hero.svg`
- Create: `content/essays/example-figures-essay/fig-1.svg`
- Create: `content/essays/example-figures-essay/fig-2.svg`
- Create: `content/essays/example-figures-essay/fig-3.svg`

- [ ] **Step 1: Create the four placeholder SVGs**

`content/essays/example-figures-essay/hero.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Placeholder hero illustration">
  <rect width="800" height="400" fill="#fdfcf8"/>
  <polygon points="200,100 280,260 120,260" fill="none" stroke="#6b1f2c" stroke-width="3"/>
  <polygon points="600,140 680,300 520,300" fill="none" stroke="#1e4060" stroke-width="3"/>
  <text x="400" y="380" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" fill="#9a958e">EXAMPLE HERO — placeholder</text>
</svg>
```

`content/essays/example-figures-essay/fig-1.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 300" role="img" aria-label="Placeholder figure one">
  <rect width="600" height="300" fill="#fdfcf8" stroke="#d4d3cd"/>
  <circle cx="300" cy="150" r="80" fill="none" stroke="#1e4060" stroke-width="2"/>
  <text x="300" y="280" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" fill="#9a958e">EXAMPLE FIGURE 1</text>
</svg>
```

`content/essays/example-figures-essay/fig-2.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" role="img" aria-label="Placeholder figure two (wide)">
  <rect width="800" height="300" fill="#fdfcf8" stroke="#d4d3cd"/>
  <line x1="100" y1="150" x2="700" y2="150" stroke="#6b1f2c" stroke-width="2"/>
  <text x="400" y="280" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" fill="#9a958e">EXAMPLE FIGURE 2 (wide)</text>
</svg>
```

`content/essays/example-figures-essay/fig-3.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 300" role="img" aria-label="Placeholder figure three">
  <rect width="600" height="300" fill="#fdfcf8" stroke="#d4d3cd"/>
  <rect x="200" y="100" width="200" height="100" fill="none" stroke="#6b1f2c" stroke-width="2"/>
  <text x="300" y="280" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" fill="#9a958e">EXAMPLE FIGURE 3</text>
</svg>
```

- [ ] **Step 2: Create the markdown**

`content/essays/example-figures-essay/index.md`:

```markdown
---
title: "Example figures essay"
date: 2026-03-20
lastmod: 2026-03-20
draft: false
summary: "Lorem ipsum example with multiple figures including a wide breakout."
tags: ["example-tag-c"]
series: ""
series_order: 0
tile_size: medium
hero: hero.svg
toc: false
has_sidenotes: false
has_citations: false
has_footnotes: false
has_math: false
has_widgets: false
has_video_sync: false
---

Lorem ipsum example introducing several figures.

{{< figure src="fig-1.svg" caption="Example figure one — placeholder caption." alt="Placeholder figure one" >}}

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

{{< figure src="fig-2.svg" caption="Example figure two — wide breakout." alt="Placeholder figure two" class="wide" >}}

Ut enim ad minim veniam, quis nostrud exercitation ullamco.

{{< figure src="fig-3.svg" caption="Example figure three — placeholder caption." alt="Placeholder figure three" >}}
```

- [ ] **Step 3: Verify linter + build**

Run: `python3 tools/check-fixtures.py && hugo --minify`
Expected: pass.

In `hugo server`:
- http://localhost:1313/essays/example-figures-essay/ → three figures render; the second is a wide breakout extending past the reading column on >920px viewports.
- http://localhost:1313/essays/ → six cards now; the figures fixture has hero so its card has `data-span="1x2"` (taller).

- [ ] **Step 4: Commit**

```bash
git add content/essays/example-figures-essay/
git commit -m "Add example-figures-essay fixture (figure-heavy with wide breakout)"
```

---

## Task 21: Per-section RSS feed + header RSS button conditional

**Files:**
- Create: `layouts/essays/rss.xml`
- Modify: `layouts/partials/header.html`

Hugo emits `/essays/index.xml` automatically when a section has pages — but using `_default/rss.xml`. Adding `essays/rss.xml` lets us customize the section feed if needed; here we keep it simple but mark the file so future customization happens in the right place.

- [ ] **Step 1: Create `layouts/essays/rss.xml`**

```xml
{{- $pages := where site.RegularPages "Section" "essays" -}}
{{- $title := printf "%s — Essays" site.Title -}}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{{ $title }}</title>
    <link>{{ "/essays/" | absURL }}</link>
    <description>{{ site.Params.description | default site.Title }} — essays.</description>
    <language>{{ site.Language.Lang }}</language>
    <atom:link href="{{ "/essays/index.xml" | absURL }}" rel="self" type="application/rss+xml"/>
    {{- range first 20 (sort $pages "Date" "desc") }}
    <item>
      <title>{{ .Title }}</title>
      <link>{{ .Permalink }}</link>
      <pubDate>{{ .Date.Format "Mon, 02 Jan 2006 15:04:05 -0700" | safeHTML }}</pubDate>
      <guid>{{ .Permalink }}</guid>
      <description>{{ .Summary | html }}</description>
    </item>
    {{- end }}
  </channel>
</rss>
```

- [ ] **Step 2: Update `layouts/partials/header.html` to switch RSS target by section**

Find:
```go-html-template
    <a class="icon-button rss-link"
       href="{{ "/index.xml" | relURL }}"
       aria-label="RSS feed"
       title="RSS feed">
      {{ with resources.Get "images/icons/rss.svg" }}{{ .Content | safeHTML }}{{ end }}
    </a>
```

Replace with:
```go-html-template
    {{- $rssHref := "/index.xml" -}}
    {{- $rssLabel := "Site RSS feed" -}}
    {{- if hasPrefix .RelPermalink "/essays/" -}}
      {{- $rssHref = "/essays/index.xml" -}}
      {{- $rssLabel = "Essays RSS feed" -}}
    {{- end -}}
    <a class="icon-button rss-link"
       href="{{ $rssHref | relURL }}"
       aria-label="{{ $rssLabel }}"
       title="{{ $rssLabel }}">
      {{ with resources.Get "images/icons/rss.svg" }}{{ .Content | safeHTML }}{{ end }}
    </a>
```

- [ ] **Step 3: Verify build + RSS feed**

Run: `hugo --minify`
Expected: build success. `public/essays/index.xml` exists.

In `hugo server`:
- http://localhost:1313/essays/index.xml → valid RSS XML with all 6 items.
- http://localhost:1313/essays/ → header RSS button has `aria-label="Essays RSS feed"` and href `/essays/index.xml`.
- http://localhost:1313/ → header RSS button has `aria-label="Site RSS feed"` and href `/index.xml`.

Verify RSS validity by pasting the URL into https://validator.w3.org/feed/ (manual step).

- [ ] **Step 4: Commit**

```bash
git add layouts/essays/rss.xml layouts/partials/header.html
git commit -m "Add per-section RSS feed for essays + section-aware header button"
```

---

## Task 22: Homepage essays strip

**Files:**
- Modify: `content/_index.html`
- Modify: `assets/css/main.css`

Adds a featured essay card + 3-column recent grid + "All essays →" link to the homepage. Reuses the same `essay-card-featured` and `essay-card` partials.

- [ ] **Step 1: Update `content/_index.html`**

Replace contents with:

```html
---
title: 'Abdelrahman Madkour'
description: "Games researcher, writer, occasional maker of music and poems."
layout: 'home'
---
<p class="role">Games researcher, writer, occasional maker of music and poems.</p>
```

- [ ] **Step 2: Create `layouts/home.html`**

This is a new layout (Hugo's `home` type) that the homepage uses by setting `layout: 'home'` in `_index.html`. Create `layouts/home.html`:

```go-html-template
{{ define "main" }}
{{ .Content }}

{{- $essays := where site.RegularPages "Section" "essays" -}}
{{- $essays = sort $essays "Date" "desc" -}}
{{- if $essays -}}
  {{- $featured := false -}}
  {{- range $essays -}}
    {{- if and (not $featured) .Params.featured -}}{{- $featured = . -}}{{- end -}}
  {{- end -}}
  {{- if not $featured -}}{{- $featured = index $essays 0 -}}{{- end -}}
  {{- $recents := first 4 (where $essays "RelPermalink" "ne" $featured.RelPermalink) -}}
  {{- $recents = first 3 $recents -}}

<section class="home-essays">
  <header class="home-essays-header">
    <h2>Essays</h2>
    <a href="{{ "/essays/" | relURL }}" class="home-essays-all">All essays →</a>
  </header>

  <ul class="essay-grid home-essays-grid">
    {{ partial "essay-card-featured.html" $featured }}
    {{ range $recents }}
      {{ partial "essay-card.html" . }}
    {{ end }}
  </ul>
</section>
{{- end }}
{{ end }}
```

- [ ] **Step 3: Append homepage strip CSS to `main.css`**

```css
/* ------------------------------------------------------------------
 * 18. Homepage essays strip
 * ------------------------------------------------------------------ */
.home-essays { margin-top: 3rem; }
.home-essays-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
}
.home-essays-header h2 {
  font-size: var(--text-xl);
  margin: 0;
}
.home-essays-all {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
  text-decoration: none;
}
.home-essays-all:hover { color: var(--color-burgundy); text-decoration: underline; }
.home-essays-grid { margin-top: 0; }
```

- [ ] **Step 4: Verify build + render**

Run: `hugo --minify && python3 tools/check-contrast.py`
Expected: pass.

In `hugo server` → http://localhost:1313/
Expected: homepage role line, then "Essays" header with "All essays →" link, then a grid showing the featured fixture (`example-essay-one`) as a 2x2 card plus three more recent fixtures as 1x1 (or 1x2 if hero) cards.

- [ ] **Step 5: Commit**

```bash
git add content/_index.html layouts/home.html assets/css/main.css
git commit -m "Add essays strip to homepage (featured + 3 recents)"
```

---

## Task 23: Final manual walkthrough

**Files:**
- None (verification only)

Run the full verification checklist from spec §7.2. Each item is a concrete observation against `hugo server`. When all green, this slice is shippable.

- [ ] **Step 1: Run all CI gates locally**

```bash
python3 tools/check-contrast.py
python3 tools/check-fixtures.py
python3 -m unittest tools/test_check_fixtures.py -v
hugo --minify
```

Expected: all four pass with zero warnings.

- [ ] **Step 2: Layout + visual checklist**

In `hugo server` at http://localhost:1313/essays/:
- [ ] All six fixtures appear in the grid
- [ ] Bento spans look correct: fixture #1 is 2x2, #6 is 1x2, #4 is 1x2 (hero), #2/#3/#5 are 1x1
- [ ] Cards have hero images where declared
- [ ] Long titles line-clamp to 3 lines

For each fixture's single page (visit each):
- [ ] At width >1100px: three-zone layout (TOC | body | sidenote rail)
- [ ] At width <1100px: single column with TOC as `<details>` disclosure
- [ ] Hero image renders at top of post (when present)

- [ ] **Step 3: Capabilities checklist**

On `example-essay-one`:
- [ ] TOC: scroll-spy highlights match scrolled section (existing nav.js behavior)
- [ ] TOC: clicking a link smooth-scrolls to that heading
- [ ] Sidenote markers (1, 2, 3) appear inline in burgundy
- [ ] Sidenote: at >1100px floats in right rail; at <1100px hidden until marker clicked → opens popup; click outside / Esc closes
- [ ] Footnote markers (^1, ^2) jump to bottom-of-post anchors
- [ ] Citations show as `[Lastname & Othername 2020]` in burgundy; click jumps to references list
- [ ] Each `<cite>` element has `data-cite-key` attribute (verify in DevTools)
- [ ] References section renders only the cited entries
- [ ] Two figures render with captions; second one (`class="wide"`) extends past the reading column on >920px

On `example-essay-two`:
- [ ] Code blocks render with Dracula chroma highlighting (3 languages)
- [ ] Math expression renders as inline `<code data-math>\alpha + \beta = \gamma</code>`
- [ ] Reading time appears in meta line; matches Hugo's `.ReadingTime` value

On `example-series-part-1` and `-part-2`:
- [ ] Series nav shows "example-series — Part N of 2" position
- [ ] Part 1 has a "→ part two" next link only; Part 2 has a "← part one" prev link only
- [ ] Video-sync stub on part 1 renders as empty `<div data-video-sync data-src="...">` (invisible)
- [ ] Widget stub on part 2 renders as empty `<div data-widget data-widget-id="...">` (invisible)

On `example-figures-essay`:
- [ ] Three figures render with captions
- [ ] Figure 2 (`class="wide"`) is wider than reading column on >920px

- [ ] **Step 4: Filter chips checklist**

At `/essays/`:
- [ ] Tag dimension renders chips (multiple tags exist)
- [ ] Series dimension renders chips (`example-series` plus `All`)
- [ ] Year dimension is suppressed (only 2026)
- [ ] Click `#example-tag-a` → only fixtures with that tag visible
- [ ] Click `All` in tags → all visible again
- [ ] Click an `example-series` chip → tag chip resets to All; only series-part-1 and -2 visible

With JavaScript disabled in browser:
- [ ] Tag chips render as anchor links to `/tags/<slug>/`
- [ ] Series chips render as anchor links to `/series/<slug>/`
- [ ] Year chips render as inert spans

- [ ] **Step 5: Themes + accessibility checklist**

- [ ] Light mode (theme toggle): all pages legible, contrast looks correct
- [ ] Dark mode (theme toggle): all pages legible
- [ ] System theme (clear `theme-pref` in localStorage): respects `prefers-color-scheme`
- [ ] Tab order through `/essays/example-essay-one/`: nav → article meta → TOC links → body links → sidenote markers → footer
- [ ] Focus ring visible on every focusable element
- [ ] `aria-current="page"` on top-nav "Essays" link when on `/essays/`
- [ ] `aria-current="location"` on active TOC link as you scroll
- [ ] System reduced-motion: TOC click jumps without smooth animation; no transitions

- [ ] **Step 6: Homepage strip checklist**

At `/`:
- [ ] "Essays" section appears below role line
- [ ] Featured card is `example-essay-one`
- [ ] 3 recent cards in date order (most recent first, after featured)
- [ ] "All essays →" resolves to `/essays/`

- [ ] **Step 7: RSS checklist**

- [ ] http://localhost:1313/essays/index.xml validates at https://validator.w3.org/feed/
- [ ] http://localhost:1313/index.xml still validates (site-wide, unchanged)
- [ ] Header RSS button on `/essays/...` pages targets `/essays/index.xml` (verify in DevTools)
- [ ] Header RSS button on other pages targets `/index.xml`

- [ ] **Step 8: Deferred-feature stub render checklist**

In DevTools, inspect the rendered HTML for each:
- [ ] `{{< spoiler >}}` in fixture #3 → `<span data-spoiler>Lorem ipsum spoiler text...</span>` (visible inline as plain text)
- [ ] `{{< math >}}` in fixture #2 → `<code data-math>\alpha + \beta = \gamma</code>` (visible as inline code)
- [ ] `{{< video-sync >}}` in fixture #4 → `<div data-video-sync data-src="...">` (empty div)
- [ ] `{{< widget >}}` in fixture #5 → `<div data-widget data-widget-id="...">` (empty div)

- [ ] **Step 9: Deferred-features list (verbatim from spec §9)**

Confirm each row is true and the fixture seeded:

| Capability | Target slice | Fixture seeded? | Verified |
|---|---|---|---|
| Spoiler block runtime | Phase 4 | Yes — fixture #3 | [ ] |
| KaTeX math rendering | Later | Yes — fixture #2 | [ ] |
| Scroll-synced video runtime | Later | Yes — fixture #4 | [ ] |
| Per-page widgets + bundle convention | Later | Yes — fixture #5 | [ ] |
| Figure lightbox | Polish phase | No | [ ] |
| Citation hover-card runtime | Phase 3 | Yes — `data-cite-key` hooks present | [ ] |
| Code highlighting palette swap | Post-Phase-2 | N/A — Dracula kept | [ ] |
| Multi-dimension filter | Later | N/A | [ ] |
| Print stylesheet | Phase 8 | N/A | [ ] |

- [ ] **Step 10: Final commit (only if any walkthrough fixes were made)**

If walking the checklist surfaced any issues, fix them inline and commit. Otherwise, skip.

```bash
git status   # confirm clean
```

If clean: tag the slice complete with a commit on the doc:

```bash
# (Optional) update repo-root CLAUDE.md project status to reflect Phase 2 (Essays slice) shipped.
```

---

## Self-review (post-plan)

**Spec coverage:**
- §1 slice scope → Tasks 5–8 (essays section), 10/15/19/20 (fixtures), 21 (RSS), 22 (homepage strip), 1–2 (linter+CI) ✓
- §2 decisions → embedded in tasks ✓
- §3 architecture → all files in §3.1 mapped to tasks; `essay.js` (Task 16); deferred shortcodes (Task 4) ✓
- §4 components → list (Task 8/9/17), single (Task 5/7/12/14/18), card partials (Task 8/9), TOC (Task 14), sidenote (Task 11), cite + references (Task 12), figure (Task 13), deferred shortcodes (Task 4), essay.js (Task 16) ✓
- §5 data flow → frontmatter contract enforced by linter (Task 1); citations.yaml (Task 3); taxonomies (Task 17); RSS (Task 21); homepage strip (Task 22) ✓
- §6 error handling → linter rules (Task 1), `errorf` in cite shortcode (Task 12), nil-checks in card/single (Tasks 8/14); §6.4 layout edges in CSS (Tasks 8/13) ✓
- §7 testing → CI in Task 2, manual checklist in Task 23 ✓
- §8 fixture set → six fixtures across Tasks 6/10/15/19/20 ✓
- §9 deferred features → Task 23 step 9 confirms each row; stubs in Task 4 ✓

**Placeholder scan:** No "TBD", "TODO", or "fill in details" instructions. Every task has complete code blocks and exact commands.

**Type consistency:** `essay.js` `setupTocSmoothScroll`, `setupSidenotePopups`, `setupCitationHook`, `setupFilterChips` referenced consistently. CSS class names (`.essay-card`, `.essay-grid`, `.essay-body`, `.essay-meta`, `.filter-chip`, etc.) match between Hugo templates and CSS. Frontmatter field names match the linter's `REQUIRED_FIELDS` set.

**Known weaknesses (non-blocking):**
- The `figure.html` shortcode override needs Hugo to honor the project's shortcode over its built-in. This is the standard Hugo behavior; flagged here in case a future Hugo version changes precedence.
- The cite shortcode's last-name extraction (`split "," | first` style) assumes "Lastname, F." format consistently. The linter does not enforce this format on `data/citations.yaml` (only that the key exists). Document this in a comment if real bib entries diverge.
