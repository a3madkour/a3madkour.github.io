# Works Umbrella Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the bland `/works/` umbrella's 3-card list with a Bento variable-tile grid + tag-cloud filter + ⊞ Graph view toggle. Hand-author three medium glyphs (gamepad / eighth-note / quill) reusable in tiles, graph nodes, and a future homepage Studio strip.

**Architecture:** Reuse existing primitives — `partials/filter-chips.html` (unchanged), §27 shared graph CSS, the research-graph copy + trim pattern, the essays Bento `data-span` pattern. Split the works JS bundle so per-item works pages stay at ~6 KB while the umbrella ships ~110 KB (vendored d3 inlined). The constellation panel shows tag-share edges (solid) and explicit cross-medium refs (dashed: `lyrics_poem ↔ set_to_music` etc.) already present in fixtures.

**Tech Stack:** Hugo (extended ≥ 0.148.0), hand-rolled CSS, `js.Build` (esbuild) multi-entry bundles, vendored d3-force / d3-zoom / d3-drag / d3-selection (already under `assets/js/vendor/`), Python stdlib for linters.

**Spec:** `docs/superpowers/specs/2026-05-12-works-umbrella-polish-design.md`

---

## File map

### Create

- `assets/images/icons/glyph-game.svg` — gamepad outline, hybrid style, `currentColor` stroke, `viewBox="0 0 24 24"`
- `assets/images/icons/glyph-music.svg` — eighth-note, same direction
- `assets/images/icons/glyph-poetry.svg` — quill, same direction
- `layouts/works/graph.html` — standalone `/works/graph/` page (mobile fallback + deep link)
- `layouts/partials/works/tile.html` — single Bento tile
- `layouts/partials/works/glyph-sprite.html` — three `<symbol>` defs in a hidden `<svg>`
- `layouts/partials/works/graph-data.html` — build-time `partialCached` data partial
- `layouts/partials/works/graph-script.html` — JSON `<script>` wrapper via `safeJS`
- `layouts/partials/works/graph-panel.html` — side-panel scaffolding
- `assets/js/works-graph.js` — copy + trim of `research-graph.js`
- `assets/js/entry-works-umbrella.js` — entry that imports `works.js` + `works-graph.js`

### Modify

- `layouts/works/list.html` — full rewrite (header + sprite + filter strip + Bento grid + graph panel)
- `assets/css/main.css` — replace umbrella block in §33 (lines ~2186–2235), add new §36 "Works graph"
- `layouts/partials/scripts.html` — add 6th `js.Build` for `entry-works-umbrella.js`, narrow `entry-works.js` predicate so the two never overlap
- `data/filter-chips.yaml` — add `works` section
- `tools/check_filter_chips_config.py` — extend `SECTION_PATH_OVERRIDES` so `works` aggregates across `content/works/{games,music,poetry}/`
- `tools/check_works_fixtures.py` — add `tile_size`, `featured`, `hero` to the optional-field allowlist on all three types; add enum validation for `tile_size`
- `tools/test_check_filter_chips_config.py` — new tests for the `works` aggregation
- `tools/test_check_works_fixtures.py` — new tests for the three new optional fields
- `content/works/games/example-playable-full-release/index.md` — add `featured: true`
- `content/works/music/example-album-with-tracks/index.md` — add `featured: true`
- `content/works/poetry/example-poem-collected/index.md` — add `tile_size: large`
- `CLAUDE.md` — Project status note + Reference docs entry

### Delete

- `layouts/partials/works/section-card.html` — replaced by `tile.html` + new umbrella layout

---

## Tasks

### Task 1 — Extend `check_works_fixtures.py` allowlist (TDD)

**Files:**
- Modify: `tools/check_works_fixtures.py:19-41` (the three `*_OPTIONAL` sets)
- Modify: `tools/test_check_works_fixtures.py` (append tests)

- [ ] **Step 1.1: Write failing tests for the new optional fields.**

Append to `tools/test_check_works_fixtures.py`:

```python
class TestUmbrellaFields(LinterCase):
    """Tests for Bento-grid frontmatter fields added in the umbrella-polish slice."""

    def test_game_accepts_tile_size_featured_hero(self):
        md = self.write_game(
            title="X", date="2026-01-01", lastmod="2026-01-01", draft=False,
            status="playable", game_kind="jam", tagline="t", year=2026,
            tile_size="large", featured=True, hero=True,
        )
        errs = lint_file(md)
        self.assertEqual(errs, [])

    def test_music_accepts_tile_size_featured_hero(self):
        md = self.write_music(
            title="X", date="2026-01-01", lastmod="2026-01-01", draft=False,
            format="album", year=2026,
            tile_size="small", featured=True, hero=False,
        )
        errs = lint_file(md)
        self.assertEqual(errs, [])

    def test_poem_accepts_tile_size_featured_hero(self):
        md = self.write_poem(
            title="X", date="2026-01-01", lastmod="2026-01-01", draft=False,
            lines=10,
            tile_size="medium", featured=False, hero=True,
        )
        errs = lint_file(md)
        self.assertEqual(errs, [])

    def test_tile_size_must_be_in_enum(self):
        md = self.write_game(
            title="X", date="2026-01-01", lastmod="2026-01-01", draft=False,
            status="playable", game_kind="jam", tagline="t", year=2026,
            tile_size="huge",
        )
        errs = lint_file(md)
        self.assertTrue(any("tile_size='huge'" in e for e in errs), errs)
```

If `LinterCase`, `write_game`, `write_music`, `write_poem`, or `lint_file` are not present in the test file, inspect the existing tests to learn the helper names and adapt the calls accordingly. The test names and assertions above are the contract.

- [ ] **Step 1.2: Run the new tests, confirm they fail.**

```bash
python3 -m unittest tools.test_check_works_fixtures -v 2>&1 | tail -20
```

Expected: 4 new failures (`test_game_accepts_*`, `test_music_accepts_*`, `test_poem_accepts_*`, `test_tile_size_must_be_in_enum`) — at least three failing with "unknown field 'tile_size'" or similar.

- [ ] **Step 1.3: Extend the three `*_OPTIONAL` sets + add `tile_size` enum validation.**

In `tools/check_works_fixtures.py`, after the existing module-level constants (around line 41) add:

```python
UMBRELLA_OPTIONAL = {"tile_size", "featured", "hero"}
TILE_SIZES = {"small", "medium", "large"}
```

Update the three `*_OPTIONAL` set unions:

```python
GAME_OPTIONAL = GAME_OPTIONAL | UMBRELLA_OPTIONAL
MUSIC_OPTIONAL = MUSIC_OPTIONAL | UMBRELLA_OPTIONAL
POEM_OPTIONAL = POEM_OPTIONAL | UMBRELLA_OPTIONAL
GAME_FIELDS = GAME_REQUIRED | GAME_OPTIONAL
MUSIC_FIELDS = MUSIC_REQUIRED | MUSIC_OPTIONAL
POEM_FIELDS = POEM_REQUIRED | POEM_OPTIONAL
```

Add a shared helper near `_lint_game`:

```python
def _validate_umbrella_fields(md: Path, fm: dict[str, object]) -> list[str]:
    errs: list[str] = []
    ts = fm.get("tile_size")
    if ts is not None and ts not in TILE_SIZES:
        errs.append(f"{md}: tile_size='{ts}' not in {sorted(TILE_SIZES)}")
    for boolfield in ("featured", "hero"):
        val = fm.get(boolfield)
        if val is not None and not isinstance(val, bool):
            errs.append(f"{md}: {boolfield} must be bool, got {type(val).__name__}")
    return errs
```

Call it from each of `_lint_game`, `_lint_music`, `_lint_poem` — append `errs.extend(_validate_umbrella_fields(md, fm))` after the existing per-type validation.

- [ ] **Step 1.4: Run the tests, confirm green.**

```bash
python3 -m unittest tools.test_check_works_fixtures -v 2>&1 | tail -5
```

Expected: all green, including the 4 new tests.

- [ ] **Step 1.5: Run the full linter against current fixtures (regression check).**

```bash
python3 tools/check_works_fixtures.py
```

Expected: `check_works_fixtures: OK` — the existing 12 fixtures still pass.

- [ ] **Step 1.6: Commit.**

```bash
git add tools/check_works_fixtures.py tools/test_check_works_fixtures.py
git commit -m "works linter: accept tile_size/featured/hero on umbrella tiles"
```

---

### Task 2 — Extend `check_filter_chips_config.py` for the `works` umbrella key (TDD)

**Files:**
- Modify: `tools/check_filter_chips_config.py:80-117`
- Modify: `tools/test_check_filter_chips_config.py` (append tests)

- [ ] **Step 2.1: Write failing tests for the aggregated `works` key.**

Append to `tools/test_check_filter_chips_config.py`:

```python
class TestWorksAggregation(LinterCase):
    """The `works` key in filter-chips.yaml aggregates tags across the three
    works sub-sections (games / music / poetry) — not from `content/works/`."""

    def setUp(self):
        super().setUp()
        # Each sub-section gets one fixture with a distinct tag.
        self.write_fixture(
            "content/works/games/g1/index.md",
            title="G", draft=False, tags=["game-only"],
        )
        self.write_fixture(
            "content/works/music/m1/index.md",
            title="M", draft=False, tags=["music-only"],
        )
        self.write_fixture(
            "content/works/poetry/p1/index.md",
            title="P", draft=False, tags=["poetry-only"],
        )

    def test_works_primary_resolves_against_all_three_subs(self):
        self.write_config({"works": {"primary_tags": ["game-only", "music-only", "poetry-only"]}})
        rc, errs = run(self.repo)
        self.assertEqual(rc, 0, errs)

    def test_works_primary_rejects_tag_not_in_any_sub(self):
        self.write_config({"works": {"primary_tags": ["ghost-tag"]}})
        rc, errs = run(self.repo)
        self.assertEqual(rc, 1)
        self.assertTrue(any("ghost-tag" in e for e in errs), errs)
```

If `LinterCase`, `write_fixture`, `write_config`, or `run` differ in name in the existing file, adapt to the local helpers.

- [ ] **Step 2.2: Run tests, confirm failures.**

```bash
python3 -m unittest tools.test_check_filter_chips_config -v 2>&1 | tail -20
```

Expected: 2 failures around the `works` aggregation.

- [ ] **Step 2.3: Implement aggregation.**

In `tools/check_filter_chips_config.py`, replace the `_section_content_path` function with an aggregating variant. Around line 112, replace:

```python
def _section_content_path(repo_root: Path, section: str) -> Path:
    """Return the content directory for a section key."""
    override = SECTION_PATH_OVERRIDES.get(section)
    if override:
        return repo_root / override
    return repo_root / "content" / section
```

with:

```python
# Sections whose tag pool aggregates across multiple content directories.
SECTION_AGGREGATIONS: dict[str, tuple[str, ...]] = {
    "works": ("content/works/games", "content/works/music", "content/works/poetry"),
}


def _section_content_paths(repo_root: Path, section: str) -> list[Path]:
    """Return all content directories that contribute to a section's tag pool.

    Most sections map 1:1 to `content/<section>/`. Sub-sections like games/music/
    poetry have explicit overrides. `works` aggregates across its three sub-
    sections — its tag pool is the union of all three.
    """
    paths = SECTION_AGGREGATIONS.get(section)
    if paths is not None:
        return [repo_root / p for p in paths]
    override = SECTION_PATH_OVERRIDES.get(section)
    if override:
        return [repo_root / override]
    return [repo_root / "content" / section]
```

Update the `run()` loop (around line 158) to use the aggregating helper:

```python
        content_paths = _section_content_paths(repo_root, section)
        display_path = ", ".join(str(p.relative_to(repo_root)) for p in content_paths)
        live: set[str] = set()
        for p in content_paths:
            live |= collect_tags(p)
        for entry in primary:
            if str(entry) not in live:
                errors.append(
                    f"data/filter-chips.yaml:{section}.primary_tags: "
                    f'"{entry}" is not used by any non-draft note '
                    f"in /{display_path}/"
                )
```

- [ ] **Step 2.4: Run tests, confirm green; run the full linter.**

```bash
python3 -m unittest tools.test_check_filter_chips_config -v 2>&1 | tail -5
python3 tools/check_filter_chips_config.py
```

Expected: all green; `All filter-chips config entries pass linter.`

- [ ] **Step 2.5: Commit.**

```bash
git add tools/check_filter_chips_config.py tools/test_check_filter_chips_config.py
git commit -m "filter-chips linter: aggregate works key across games/music/poetry"
```

---

### Task 3 — Add the `works` key to `data/filter-chips.yaml`

**Files:**
- Modify: `data/filter-chips.yaml`

- [ ] **Step 3.1: Add the umbrella section.**

After the existing `poetry:` block in `data/filter-chips.yaml`, append:

```yaml
works:
  # Umbrella aggregates tags across games + music + poetry.
  primary_tags: [example]
  primary_top_k: 10
```

The single `example` tag is the safe shared tag across all 12 fixtures (per the existing `games`/`music`/`poetry` curated lists). Curate further once the elisp pipeline lands.

- [ ] **Step 3.2: Verify the linter passes.**

```bash
python3 tools/check_filter_chips_config.py
```

Expected: `All filter-chips config entries pass linter.`

- [ ] **Step 3.3: Commit.**

```bash
git add data/filter-chips.yaml
git commit -m "filter-chips config: add works umbrella section"
```

---

### Task 4 — Hand-author the three glyph SVGs

**Files:**
- Create: `assets/images/icons/glyph-game.svg`
- Create: `assets/images/icons/glyph-music.svg`
- Create: `assets/images/icons/glyph-poetry.svg`

The hybrid style direction the author picked: clean strokes, organic shapes, `currentColor` stroke (no fill on the gamepad body / quill spine), thin strokes ~1.5px, `viewBox="0 0 24 24"`. The brainstorm `.superpowers/brainstorm/673747-1778634860/content/graph-nodes-closeup.html` is the visual reference.

- [ ] **Step 4.1: Create `glyph-game.svg`.**

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M2 13 Q2 8 7 8 L17 8 Q22 8 22 13 Q22 18 18 18 Q15 18 14 16.5 L10 16.5 Q9 18 6 18 Q2 18 2 13 Z"/>
  <line x1="6" y1="13" x2="9" y2="13"/>
  <line x1="7.5" y1="11.5" x2="7.5" y2="14.5"/>
  <circle cx="16" cy="12.5" r="0.9" fill="currentColor"/>
  <circle cx="18" cy="14" r="0.9" fill="currentColor"/>
</svg>
```

- [ ] **Step 4.2: Create `glyph-music.svg`.**

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M9 6 Q9 11.5 9 17"/>
  <ellipse cx="7" cy="17" rx="2.3" ry="1.6" fill="currentColor" stroke="none"/>
  <path d="M9 6 Q13 4.5 15.5 4 Q16 7 15 10 Q12 11 9 11 Z" fill="currentColor" stroke="none"/>
</svg>
```

- [ ] **Step 4.3: Create `glyph-poetry.svg`.**

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M5 19 Q12 12.5 18 6"/>
  <path d="M10.5 7 Q15.5 3.5 19.5 5.5 Q18 9 15.5 11 Q13 12.5 10.8 13 Q10.4 10 10.5 7 Z" fill="currentColor" fill-opacity="0.10"/>
  <path d="M10.5 7 Q15.5 3.5 19.5 5.5 Q18 9 15.5 11 Q13 12.5 10.8 13"/>
  <path d="M13.2 8.2 Q13.2 10.5 13.2 12"/>
</svg>
```

- [ ] **Step 4.4: Visually verify each glyph renders correctly.**

```bash
# Quick sanity check that the SVGs parse (xmllint may not be installed; if not, skip).
xmllint --noout assets/images/icons/glyph-*.svg 2>/dev/null || echo "(xmllint not available — that's fine)"
ls -la assets/images/icons/glyph-*.svg
```

Expected: 3 files listed, each ~300–500 bytes.

- [ ] **Step 4.5: Commit.**

```bash
git add assets/images/icons/glyph-game.svg assets/images/icons/glyph-music.svg assets/images/icons/glyph-poetry.svg
git commit -m "icons: hand-author medium glyphs (gamepad/eighth-note/quill)"
```

---

### Task 5 — Glyph sprite partial

**Files:**
- Create: `layouts/partials/works/glyph-sprite.html`

The sprite partial inlines the three glyphs as `<symbol>` definitions so `<use href="#g-game">` works on the page. Manual sync with the standalone SVG files (acknowledged in spec §10).

- [ ] **Step 5.1: Create the partial.**

```html
{{- /* Inlines the three works-medium glyphs as <symbol> definitions for
       <use href="#g-{medium}"> references. Rendered once per page (umbrella
       + standalone graph page). Source-of-truth visual files live at
       assets/images/icons/glyph-{game,music,poetry}.svg — keep in sync. */ -}}
<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
  <symbol id="g-game" viewBox="0 0 24 24">
    <g fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M2 13 Q2 8 7 8 L17 8 Q22 8 22 13 Q22 18 18 18 Q15 18 14 16.5 L10 16.5 Q9 18 6 18 Q2 18 2 13 Z"/>
      <line x1="6" y1="13" x2="9" y2="13"/>
      <line x1="7.5" y1="11.5" x2="7.5" y2="14.5"/>
      <circle cx="16" cy="12.5" r="0.9" fill="currentColor"/>
      <circle cx="18" cy="14" r="0.9" fill="currentColor"/>
    </g>
  </symbol>
  <symbol id="g-music" viewBox="0 0 24 24">
    <g fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 6 Q9 11.5 9 17"/>
      <ellipse cx="7" cy="17" rx="2.3" ry="1.6" fill="currentColor" stroke="none"/>
      <path d="M9 6 Q13 4.5 15.5 4 Q16 7 15 10 Q12 11 9 11 Z" fill="currentColor" stroke="none"/>
    </g>
  </symbol>
  <symbol id="g-poetry" viewBox="0 0 24 24">
    <g fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M5 19 Q12 12.5 18 6"/>
      <path d="M10.5 7 Q15.5 3.5 19.5 5.5 Q18 9 15.5 11 Q13 12.5 10.8 13 Q10.4 10 10.5 7 Z" fill="currentColor" fill-opacity="0.10"/>
      <path d="M10.5 7 Q15.5 3.5 19.5 5.5 Q18 9 15.5 11 Q13 12.5 10.8 13"/>
      <path d="M13.2 8.2 Q13.2 10.5 13.2 12"/>
    </g>
  </symbol>
</svg>
```

- [ ] **Step 5.2: Commit.**

```bash
git add layouts/partials/works/glyph-sprite.html
git commit -m "works: add glyph-sprite partial for inlined <symbol> defs"
```

---

### Task 6 — Bento tile partial

**Files:**
- Create: `layouts/partials/works/tile.html`

- [ ] **Step 6.1: Author the partial.**

```html
{{- /* Single Bento tile for the /works/ umbrella.
   Inputs:
     .Page      — the work fixture (a *hugolib.Page)
     .medium    — "game" | "music" | "poetry"
   Resolves:
     data-tile-size = explicit tile_size > (featured ? "large") > "medium"
     data-span      = "2x1" if featured, "1x2" if hero, "2x2" if both, "1x1" otherwise
   Surfaces cross-medium references (lyrics_poem / set_to_music) as a small
   ↔ annotation. Tags rendered as capsule chips, max 3; the active tag (set
   via JS) gains class `t--match`.
*/ -}}
{{- $p := .Page -}}
{{- $medium := .medium -}}
{{- $params := $p.Params -}}

{{- $tile := "medium" -}}
{{- with $params.tile_size }}{{ $tile = . }}{{ end -}}
{{- if and (eq $tile "medium") $params.featured }}{{ $tile = "large" }}{{ end -}}

{{- $span := "1x1" -}}
{{- if and $params.featured $params.hero }}{{ $span = "2x2" -}}
{{- else if $params.featured }}{{ $span = "2x1" -}}
{{- else if $params.hero }}{{ $span = "1x2" -}}{{ end -}}

{{- /* Meta line: per-medium */ -}}
{{- $metaParts := slice -}}
{{- if eq $medium "game" -}}
  {{- with $params.game_kind }}{{ $metaParts = $metaParts | append . }}{{ end -}}
{{- else if eq $medium "music" -}}
  {{- with $params.format }}{{ $metaParts = $metaParts | append . }}{{ end -}}
{{- else if eq $medium "poetry" -}}
  {{- with $params.collection }}{{ $metaParts = $metaParts | append . }}{{ end -}}
{{- end -}}
{{- with $params.year }}{{ $metaParts = $metaParts | append (printf "%d" .) }}{{ end -}}
{{- $meta := delimit $metaParts " · " -}}

{{- /* Cross-ref: poetry → music (set_to_music), music → poetry (lyrics_poem). */ -}}
{{- $crossref := "" -}}
{{- with $params.lyrics_poem -}}
  {{- $target := site.GetPage (printf "/works/poetry/%s" .) -}}
  {{- if $target }}{{ $crossref = printf "↔ poem · %s" $target.Title }}{{ end -}}
{{- end -}}
{{- with $params.set_to_music -}}
  {{- $target := site.GetPage (printf "/works/music/%s" .) -}}
  {{- if $target }}{{ $crossref = printf "↔ music · %s" $target.Title }}{{ end -}}
{{- end -}}

{{- $tags := $params.tags | default slice -}}
{{- $tagList := first 3 $tags -}}

<article class="works-tile" data-tile-size="{{ $tile }}" data-span="{{ $span }}" data-medium="{{ $medium }}"
         data-tags="{{ delimit $tags "," }}"
         data-featured="{{ if $params.featured }}true{{ else }}false{{ end }}">
  <a class="works-tile-link" href="{{ $p.RelPermalink }}">
    <svg class="works-tile-glyph" viewBox="0 0 24 24" role="img" aria-label="{{ $medium }}"><use href="#g-{{ $medium }}"/></svg>
    <h3 class="works-tile-title">{{ $p.Title }}</h3>
    {{- with $meta }}<span class="works-tile-meta">{{ . }}</span>{{ end }}
    {{- if eq $span "2x2" }}
      {{- with $params.summary }}<p class="works-tile-pull">{{ . }}</p>{{ end }}
    {{- end }}
    {{- if $tagList }}
    <div class="works-tile-tags">
      {{- range $tagList }}<span class="works-tile-tag" data-key="{{ . }}">{{ . }}</span>{{ end }}
    </div>
    {{- end }}
    {{- with $crossref }}<span class="works-tile-crossref">{{ . }}</span>{{ end }}
  </a>
</article>
```

- [ ] **Step 6.2: Commit.**

```bash
git add layouts/partials/works/tile.html
git commit -m "works: add Bento tile partial"
```

---

### Task 7 — Rewrite umbrella layout

**Files:**
- Modify: `layouts/works/list.html` (full rewrite)

- [ ] **Step 7.1: Replace the file contents.**

```html
{{ define "main" }}
{{- /* Aggregate Pages across the three sub-sections. */ -}}
{{- $games := where (where site.RegularPages "Section" "works") "Type" "works-games" -}}
{{- $music := where (where site.RegularPages "Section" "works") "Type" "works-music" -}}
{{- $poetry := where (where site.RegularPages "Section" "works") "Type" "works-poetry" -}}
{{- $all := union (union $games $music) $poetry -}}

{{- /* Tag dim values (frequency-ranked, alphabetical for ties). */ -}}
{{- $tagFreq := dict -}}
{{- range $all -}}
  {{- range .Params.tags -}}
    {{- $tagFreq = merge $tagFreq (dict . (add (index $tagFreq . | default 0) 1)) -}}
  {{- end -}}
{{- end -}}
{{- $tagPairs := slice -}}
{{- range $k, $v := $tagFreq -}}{{ $tagPairs = $tagPairs | append (dict "tag" $k "n" $v) }}{{ end -}}
{{- $tagPairs = sort $tagPairs "tag" "asc" -}}
{{- $tagPairs = sort $tagPairs "n" "desc" -}}
{{- $tagValues := slice -}}
{{- range $tagPairs }}{{ $tagValues = $tagValues | append .tag }}{{ end -}}

{{- /* Medium dim values — fixed order. */ -}}
{{- $mediumValues := slice "games" "music" "poetry" -}}

{{- $dims := slice
     (dict "key" "tag" "label" "Tag" "values" $tagValues)
     (dict "key" "medium" "label" "Medium" "values" $mediumValues) -}}

<article class="page works-umbrella">
  {{ partial "works/glyph-sprite.html" . }}

  <header class="page-header">
    <h1>{{ .Title }}</h1>
    {{ with .Description }}<p class="page-description">{{ . }}</p>{{ end }}
  </header>

  {{ .Content }}

  <div class="works-umbrella-controls">
    {{ partial "filter-chips.html" (dict "dimensions" $dims "section" "works") }}
    <div class="works-umbrella-toolbar">
      <label class="works-sort">
        Sort
        <select id="works-sort" aria-label="Sort works">
          <option value="featured">featured</option>
          <option value="chronological">chronological</option>
          <option value="random">random</option>
        </select>
      </label>
      <button type="button" id="works-graph-toggle" class="graph-toggle"
              aria-expanded="false" aria-controls="works-graph-panel">⊞ Graph view</button>
    </div>
  </div>

  <section class="works-bento" aria-label="All works">
    {{- range $all -}}
      {{- $m := "" -}}
      {{- if eq .Type "works-games" }}{{ $m = "game" }}
      {{- else if eq .Type "works-music" }}{{ $m = "music" }}
      {{- else if eq .Type "works-poetry" }}{{ $m = "poetry" }}{{ end -}}
      {{ partial "works/tile.html" (dict "Page" . "medium" $m) }}
    {{- end -}}
  </section>
  <p class="works-empty" hidden role="status">No works match the current filter.</p>

  {{ partial "works/graph-panel.html" . }}
  {{ partial "works/graph-data.html" . }}
  {{ partial "works/graph-script.html" . }}
</article>
{{ end }}
```

- [ ] **Step 7.2: Delete the now-unused `section-card.html` partial.**

```bash
git rm layouts/partials/works/section-card.html
```

- [ ] **Step 7.3: Commit.**

```bash
git add layouts/works/list.html
git commit -m "works: rewrite umbrella as Bento + filter strip + graph toggle"
```

The page won't render yet — `graph-panel.html`, `graph-data.html`, `graph-script.html`, the CSS, and the JS still need to be authored. The dev server will report missing partials on `/works/`; that's expected until Task 12.

---

### Task 8 — Graph data partial

**Files:**
- Create: `layouts/partials/works/graph-data.html`

- [ ] **Step 8.1: Author the data partial.**

```html
{{- /* Build-time graph data for /works/ constellation. Cached once via
       partialCached so the umbrella + standalone /works/graph/ page share
       one cache entry. Output JSON shape:
         { nodes: [{slug, medium, title, url, tags, featured, year}],
           edges: [{source, target, kind: "tag-share"|"cross-ref",
                    weight?: int, shared?: [tag], via?: "lyrics_poem"|...}] }
       Edges:
       - tag-share (solid)  → every pair sharing ≥1 tag.
       - cross-ref (dashed) → derived from lyrics_poem / set_to_music
                              frontmatter; always emitted; if the pair also
                              tag-shares, only the dashed edge is kept (the
                              tag overlap is recorded in `shared`).
*/ -}}
{{- $cached := partialCached "works/graph-data-inner" . "works-graph" -}}
{{- $cached | safeJS -}}
```

- [ ] **Step 8.2: Author the inner (cacheable) partial.**

Create `layouts/partials/works/graph-data-inner.html`:

```html
{{- /* Inner partial — actual data computation. Wrapped by graph-data.html
       so the outer call can use the partialCached cache key. */ -}}
{{- $games := where (where site.RegularPages "Section" "works") "Type" "works-games" -}}
{{- $music := where (where site.RegularPages "Section" "works") "Type" "works-music" -}}
{{- $poetry := where (where site.RegularPages "Section" "works") "Type" "works-poetry" -}}
{{- $all := union (union $games $music) $poetry -}}

{{- $nodes := slice -}}
{{- $slugIndex := dict -}}
{{- range $i, $p := $all -}}
  {{- $m := "" -}}
  {{- if eq $p.Type "works-games" }}{{ $m = "game" }}
  {{- else if eq $p.Type "works-music" }}{{ $m = "music" }}
  {{- else if eq $p.Type "works-poetry" }}{{ $m = "poetry" }}{{ end -}}
  {{- $slug := path.Base $p.File.Dir -}}
  {{- $node := dict
       "slug" $slug
       "medium" $m
       "title" $p.Title
       "url" $p.RelPermalink
       "tags" ($p.Params.tags | default slice)
       "featured" (eq ($p.Params.featured | default false) true)
       "year" ($p.Params.year | default 0) -}}
  {{- $nodes = $nodes | append $node -}}
  {{- $slugIndex = merge $slugIndex (dict $slug $p) -}}
{{- end -}}

{{- /* Tag-share edges: every pair with ≥1 shared tag. */ -}}
{{- $edges := slice -}}
{{- $crossKeys := dict -}}
{{- range $i, $a := $all -}}
  {{- $aSlug := path.Base $a.File.Dir -}}
  {{- $aTags := $a.Params.tags | default slice -}}
  {{- range $j, $b := $all -}}
    {{- if lt $i $j -}}
      {{- $bSlug := path.Base $b.File.Dir -}}
      {{- $bTags := $b.Params.tags | default slice -}}
      {{- $shared := slice -}}
      {{- range $aTags -}}{{ if in $bTags . }}{{ $shared = $shared | append . }}{{ end }}{{ end -}}
      {{- if $shared -}}
        {{- $edges = $edges | append (dict
             "source" $aSlug "target" $bSlug
             "kind" "tag-share" "weight" (len $shared) "shared" $shared) -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{- /* Cross-ref edges: lyrics_poem (music → poetry) and set_to_music (poetry → music). */ -}}
{{- range $a := $all -}}
  {{- $aSlug := path.Base $a.File.Dir -}}
  {{- with $a.Params.lyrics_poem -}}
    {{- $tgt := site.GetPage (printf "/works/poetry/%s" .) -}}
    {{- if $tgt -}}
      {{- $tSlug := path.Base $tgt.File.Dir -}}
      {{- $edges = $edges | append (dict "source" $aSlug "target" $tSlug "kind" "cross-ref" "via" "lyrics_poem") -}}
    {{- end -}}
  {{- end -}}
  {{- with $a.Params.set_to_music -}}
    {{- $tgt := site.GetPage (printf "/works/music/%s" .) -}}
    {{- if $tgt -}}
      {{- $tSlug := path.Base $tgt.File.Dir -}}
      {{- $edges = $edges | append (dict "source" $aSlug "target" $tSlug "kind" "cross-ref" "via" "set_to_music") -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{- /* Dedupe: drop tag-share edges that have an equivalent cross-ref edge. */ -}}
{{- $crossPairs := dict -}}
{{- range $e := $edges -}}
  {{- if eq $e.kind "cross-ref" -}}
    {{- $k1 := printf "%s|%s" $e.source $e.target -}}
    {{- $k2 := printf "%s|%s" $e.target $e.source -}}
    {{- $crossPairs = merge $crossPairs (dict $k1 true $k2 true) -}}
  {{- end -}}
{{- end -}}
{{- $filtered := slice -}}
{{- range $e := $edges -}}
  {{- if eq $e.kind "tag-share" -}}
    {{- $k := printf "%s|%s" $e.source $e.target -}}
    {{- if not (index $crossPairs $k) }}{{ $filtered = $filtered | append $e }}{{ end -}}
  {{- else -}}
    {{- $filtered = $filtered | append $e -}}
  {{- end -}}
{{- end -}}

{{- $data := dict "nodes" $nodes "edges" $filtered -}}
{{- $data | jsonify -}}
```

- [ ] **Step 8.3: Commit.**

```bash
git add layouts/partials/works/graph-data.html layouts/partials/works/graph-data-inner.html
git commit -m "works: build-time graph data partial (nodes + tag-share/cross-ref edges)"
```

---

### Task 9 — Graph script + panel partials

**Files:**
- Create: `layouts/partials/works/graph-script.html`
- Create: `layouts/partials/works/graph-panel.html`

- [ ] **Step 9.1: Author the script wrapper.**

`layouts/partials/works/graph-script.html`:

```html
{{- $json := partial "works/graph-data.html" . -}}
<script type="application/json" id="works-graph-data">{{ $json | safeJS }}</script>
```

- [ ] **Step 9.2: Author the panel scaffolding.**

`layouts/partials/works/graph-panel.html`:

```html
<aside id="works-graph-panel" class="graph-panel" hidden role="region" aria-label="Works constellation">
  <header class="graph-panel-header">
    <h3 class="graph-panel-title">Constellation</h3>
    <button type="button" class="graph-panel-close" aria-controls="works-graph-panel" aria-label="Close graph panel">✕</button>
  </header>
  <div class="graph-panel-toolbar">
    <span class="graph-panel-toolbar-label">Medium</span>
    <button type="button" class="filter-chip is-active" data-dim="medium" data-key="all">All</button>
    <button type="button" class="filter-chip" data-dim="medium" data-key="games">Games</button>
    <button type="button" class="filter-chip" data-dim="medium" data-key="music">Music</button>
    <button type="button" class="filter-chip" data-dim="medium" data-key="poetry">Poetry</button>
    <button type="button" class="graph-panel-toolbtn" data-action="reset-view">Reset view</button>
    <button type="button" class="graph-panel-toolbtn" data-action="reset-positions">Reset positions</button>
  </div>
  <svg class="graph-panel-canvas" role="img" aria-label="Force-directed map of works"></svg>
  <div class="graph-panel-resize" aria-hidden="true"></div>
  <div class="graph-panel-legend">
    <span class="legend-item"><span class="legend-mark legend-mark-solid" aria-hidden="true"></span> tag-share</span>
    <span class="legend-item"><span class="legend-mark legend-mark-dashed" aria-hidden="true"></span> cross-medium ref</span>
  </div>
</aside>
```

- [ ] **Step 9.3: Commit.**

```bash
git add layouts/partials/works/graph-script.html layouts/partials/works/graph-panel.html
git commit -m "works: graph-script + graph-panel partials"
```

---

### Task 10 — Copy + trim `research-graph.js` into `works-graph.js`

**Files:**
- Read: `assets/js/research-graph.js` (760 lines)
- Create: `assets/js/works-graph.js`

The trim: drop stack-coordination event listeners and the N-hop local-graph mode (those are garden-specific anyway and were already absent from research-graph.js); swap the palette + symbol references; adapt node rendering to use `<use href="#g-{medium}">` instead of theme-color rects/circles; adapt edge styling (solid for `kind == "tag-share"`, dashed for `kind == "cross-ref"`).

- [ ] **Step 10.1: Copy the file.**

```bash
cp assets/js/research-graph.js assets/js/works-graph.js
```

- [ ] **Step 10.2: Read both files end-to-end before editing.**

```bash
wc -l assets/js/works-graph.js
```

Open `assets/js/works-graph.js` in your editor and identify:

- The data-loading function (reads `#research-graph-data` → change to `#works-graph-data`).
- The node-rendering function (currently appends `rect` for themes and `circle` for questions with `data-theme-color` attribute → change to append `<svg><use>` referencing `#g-{node.medium}` symbol).
- The edge-rendering function (uses `kind == "cross-theme"` for dashed → change to `kind == "cross-ref"`).
- The filter-chip wire-up inside the panel (research uses `tag` + `status` dims → change to `medium` dim only; the tag dim filter happens upstream from the main strip).
- The mount selector (currently `#research-graph-panel` or page-level → change to `#works-graph-panel` for panel, `#works-graph-canvas` for standalone page if present).
- The position cache key (e.g., `research-graph-positions:<filter>:<viewport>` → change `research` → `works`).
- The toggle button selector (currently `#research-graph-toggle` → change to `#works-graph-toggle`).

- [ ] **Step 10.3: Apply the trim with these specific edits.**

Within `works-graph.js`:

1. Replace every literal `research-graph-data` → `works-graph-data`.
2. Replace every literal `research-graph-panel` → `works-graph-panel`.
3. Replace every literal `research-graph-toggle` → `works-graph-toggle`.
4. Replace every literal `research-graph-canvas` → `works-graph-canvas`.
5. Replace position cache key prefix `research-graph-positions` → `works-graph-positions`.
6. Replace the node-shape function. Where research does:

   ```js
   if (node.type === "theme") { /* render rect with data-theme-color */ }
   else { /* render circle with data-theme-color */ }
   ```

   Use a single SVG `<g>` group per node containing a 52px rounded rect background (gradient via CSS, not inline) and an inline `<svg viewBox="0 0 24 24"><use href="#g-${node.medium}"/></svg>` of size 30 (or 40 if `node.featured`). Pseudocode (adapt to the existing d3 patterns in the file):

   ```js
   const nodeG = nodes.enter().append("g")
     .attr("class", "works-graph-node")
     .attr("data-medium", d => d.medium)
     .attr("data-featured", d => d.featured ? "true" : "false");
   nodeG.append("rect")
     .attr("class", "works-graph-node-badge")
     .attr("width", d => d.featured ? 56 : 44)
     .attr("height", d => d.featured ? 56 : 44)
     .attr("x", d => d.featured ? -28 : -22)
     .attr("y", d => d.featured ? -28 : -22)
     .attr("rx", d => d.featured ? 14 : 11);
   nodeG.append("use")
     .attr("href", d => `#g-${d.medium}`)
     .attr("width", d => d.featured ? 40 : 30)
     .attr("height", d => d.featured ? 40 : 30)
     .attr("x", d => d.featured ? -20 : -15)
     .attr("y", d => d.featured ? -20 : -15);
   nodeG.append("text")
     .attr("class", "works-graph-node-label")
     .attr("y", d => d.featured ? 42 : 32)
     .text(d => d.title);
   ```

7. Replace the edge `kind` check. Where research has `if (edge.kind === "cross-theme") line.classed("dashed", true)`, change to `if (edge.kind === "cross-ref") line.classed("works-graph-edge-cross-ref", true)`; non-cross-ref → `.works-graph-edge-tag-share`.
8. Replace the panel filter logic. Research filters by `tag` + `status`; works filters by `medium` only inside the panel. The umbrella's top-strip tag-chip selection is consumed via the same `setupFilterChips` call (which already broadcasts a custom event) — listen for it and dim non-matching nodes inside the graph. The simplest trim: drop the per-chip in-panel filter for tag (rely on the top strip), keep only the `medium` chips in the panel.
9. Delete any remaining `theme`/`question` references (variable names, classes, data attributes).
10. Update the JSDoc / file header to describe works rather than research.

- [ ] **Step 10.4: Lint-check the JS (syntax sanity).**

```bash
node --check assets/js/works-graph.js
```

Expected: no output (syntax OK). If node isn't installed, skip — the Hugo `js.Build` step will catch syntax errors in Task 13.

- [ ] **Step 10.5: Commit.**

```bash
git add assets/js/works-graph.js
git commit -m "works: copy + trim research-graph.js → works-graph.js"
```

---

### Task 11 — Umbrella entry bundle

**Files:**
- Create: `assets/js/entry-works-umbrella.js`

- [ ] **Step 11.1: Author the entry.**

```js
// Page-narrow entry for /works/ and /works/graph/ only.
// Bundles the existing works filter-chips wiring + the constellation graph.
// Per-item works pages stay on entry-works.js (~6 KB, no d3).
import "./works.js";
import "./works-graph.js";
```

- [ ] **Step 11.2: Commit.**

```bash
git add assets/js/entry-works-umbrella.js
git commit -m "works: add umbrella entry bundle (works.js + works-graph.js)"
```

---

### Task 12 — Wire the umbrella bundle into `scripts.html`; narrow `entry-works.js` predicate

**Files:**
- Modify: `layouts/partials/scripts.html:34-38`

- [ ] **Step 12.1: Replace the current works block.**

Replace lines 34–38 of `layouts/partials/scripts.html`:

```html
{{- if eq .Section "works" }}
{{- $worksOpts := dict "targetPath" "js/works.js" "minify" true -}}
{{- $works := resources.Get "js/entry-works.js" | js.Build $worksOpts | fingerprint }}
<script src="{{ $works.RelPermalink }}" integrity="{{ $works.Data.Integrity }}" defer></script>
{{- end }}
```

with the new two-predicate block:

```html
{{- /* Works split:
       umbrella + standalone graph → entry-works-umbrella.js (~110 KB w/ d3)
       per-item works pages       → entry-works.js (~6 KB, no d3) */ -}}
{{- $isUmbrella := or (eq .RelPermalink "/works/") (eq .RelPermalink "/works/graph/") -}}
{{- if $isUmbrella }}
{{- $worksUmbOpts := dict "targetPath" "js/works-umbrella.js" "minify" true -}}
{{- $worksUmb := resources.Get "js/entry-works-umbrella.js" | js.Build $worksUmbOpts | fingerprint }}
<script src="{{ $worksUmb.RelPermalink }}" integrity="{{ $worksUmb.Data.Integrity }}" defer></script>
{{- else if eq .Section "works" }}
{{- $worksOpts := dict "targetPath" "js/works.js" "minify" true -}}
{{- $works := resources.Get "js/entry-works.js" | js.Build $worksOpts | fingerprint }}
<script src="{{ $works.RelPermalink }}" integrity="{{ $works.Data.Integrity }}" defer></script>
{{- end }}
```

- [ ] **Step 12.2: Start the dev server and verify the build doesn't error.**

```bash
hugo server --buildDrafts
```

Visit `http://localhost:1313/works/` in a browser. You should see:
- The H1, intro line, filter chips, sort dropdown, and ⊞ Graph view toggle.
- Bento tiles with unstyled-ish placeholder content (CSS isn't done yet — that's Task 14).
- No JS console errors. The graph panel exists but is hidden.

Kill the dev server before the production build runs in CI/locally — recall the memory note: `hugo --minify` poisons the dev-server CSS via MIME mismatch.

- [ ] **Step 12.3: Commit.**

```bash
git add layouts/partials/scripts.html
git commit -m "scripts: split works bundle — page-narrow umbrella entry, per-item core"
```

---

### Task 13 — Standalone `/works/graph/` layout

**Files:**
- Create: `layouts/works/graph.html`

Mirror `layouts/research/graph.html` (or `layouts/garden/graph.html`). Breadcrumb + summary + toolbar + full-width canvas + legend.

- [ ] **Step 13.1: Author the standalone page.**

```html
{{ define "main" }}
<article class="page works-graph-page">
  {{ partial "works/glyph-sprite.html" . }}

  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="/works/">Works</a> <span aria-hidden="true">›</span> Constellation
  </nav>

  <header class="page-header">
    <h1>Constellation</h1>
    <p class="page-description">Force-directed map of every work. Solid edges = shared tags. Dashed edges = explicit cross-medium references.</p>
  </header>

  <div class="graph-page-toolbar">
    <span class="works-graph-summary" id="works-graph-summary"></span>
    <button type="button" class="filter-chip is-active" data-dim="medium" data-key="all">All</button>
    <button type="button" class="filter-chip" data-dim="medium" data-key="games">Games</button>
    <button type="button" class="filter-chip" data-dim="medium" data-key="music">Music</button>
    <button type="button" class="filter-chip" data-dim="medium" data-key="poetry">Poetry</button>
    <button type="button" class="graph-panel-toolbtn" data-action="reset-view">Reset view</button>
    <button type="button" class="graph-panel-toolbtn" data-action="reset-positions">Reset positions</button>
  </div>

  <svg class="graph-page-canvas" id="works-graph-canvas" role="img" aria-label="Constellation of works"></svg>

  <div class="graph-page-legend">
    <span class="legend-item"><span class="legend-mark legend-mark-solid" aria-hidden="true"></span> tag-share</span>
    <span class="legend-item"><span class="legend-mark legend-mark-dashed" aria-hidden="true"></span> cross-medium ref</span>
  </div>

  {{ partial "works/graph-script.html" . }}
</article>
{{ end }}
```

Hugo needs a content stub for the page to render. Create `content/works/graph.md`:

```yaml
---
title: Constellation
layout: graph
url: /works/graph/
---
```

- [ ] **Step 13.2: Verify the standalone page loads in the dev server.**

```bash
hugo server --buildDrafts
# In browser: http://localhost:1313/works/graph/
```

Expected: page renders without console errors. Canvas is empty (no CSS or styled nodes yet — that's Task 14).

- [ ] **Step 13.3: Commit.**

```bash
git add layouts/works/graph.html content/works/graph.md
git commit -m "works: standalone /works/graph/ page"
```

---

### Task 14 — CSS §33 umbrella block replacement + new §36 works graph

**Files:**
- Modify: `assets/css/main.css:2182-2235` (§33 umbrella block)
- Modify: `assets/css/main.css` (append new §36 at end of file)

- [ ] **Step 14.1: Replace the §33 umbrella block.**

Open `assets/css/main.css`. Locate the §33 header (around line 2182) and the block ending at line 2235 (after `.works-section-card-all`). Replace those lines (keep the section header comment) with the new Bento + filter-strip rules:

```css
/* =========================================================
 * §33 Works — umbrella + games
 * /works/ Bento grid + filter strip; /works/games/ grid; per-game page.
 * ========================================================= */

/* Umbrella controls (filter strip + toolbar) */
.works-umbrella-controls {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin: 2rem 0 1.5rem 0;
}
.works-umbrella-toolbar {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-family: var(--font-ui);
  font-size: 0.78rem;
}
.works-sort {
  display: inline-flex;
  align-items: baseline;
  gap: 0.4rem;
  color: var(--color-ink-soft);
}
.works-sort select {
  font-family: var(--font-ui);
  font-size: 0.78rem;
  background: var(--color-stone);
  color: var(--color-ink);
  border: 1px solid var(--color-rule);
  border-radius: 4px;
  padding: 0.25rem 0.4rem;
}
.works-umbrella-toolbar .graph-toggle {
  margin-left: auto;
  font-family: var(--font-ui);
  font-size: 0.78rem;
  padding: 0.35rem 0.75rem;
  border: 1px solid var(--color-burgundy);
  color: var(--color-burgundy);
  background: var(--color-stone);
  border-radius: 4px;
  cursor: pointer;
}
.works-umbrella-toolbar .graph-toggle[aria-expanded="true"] {
  background: var(--color-burgundy);
  color: var(--color-stone);
}

/* Bento grid */
.works-bento {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  grid-auto-rows: 160px;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
@media (max-width: 720px) {
  .works-bento { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .works-bento { grid-template-columns: 1fr; }
}

.works-tile {
  border: 1px solid var(--color-rule);
  border-radius: 6px;
  background: var(--color-stone);
  transition: border-color .15s;
  overflow: hidden;
}
.works-tile:hover { border-color: var(--color-ink-soft); }
.works-tile[data-span="2x1"] { grid-column: span 2; }
.works-tile[data-span="1x2"] { grid-row: span 2; }
.works-tile[data-span="2x2"] { grid-column: span 2; grid-row: span 2; }
@media (max-width: 480px) {
  .works-tile[data-span="2x1"], .works-tile[data-span="2x2"] { grid-column: span 1; }
}
.works-tile[hidden] { display: none; }

.works-tile-link {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  height: 100%;
  text-decoration: none;
  color: var(--color-ink);
}
.works-tile-glyph {
  width: 22px; height: 22px;
  margin-bottom: 0.5rem;
}
.works-tile[data-medium="game"] .works-tile-glyph { color: var(--color-burgundy); }
.works-tile[data-medium="music"] .works-tile-glyph { color: var(--color-steel); }
.works-tile[data-medium="poetry"] .works-tile-glyph { color: var(--color-green); }
.works-tile[data-span="2x2"] .works-tile-glyph { width: 30px; height: 30px; }

.works-tile-title {
  margin: 0 0 0.15rem 0;
  font-family: var(--font-body);
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.25;
}
.works-tile[data-span="2x1"] .works-tile-title { font-size: 1.15rem; }
.works-tile[data-span="2x2"] .works-tile-title { font-size: 1.4rem; }

.works-tile-meta {
  font-family: var(--font-ui);
  font-size: 0.7rem;
  color: var(--color-ink-soft);
}
.works-tile-pull {
  font-style: italic;
  font-size: 0.88rem;
  color: var(--color-ink-soft);
  margin: 0.5rem 0 0 0;
}
.works-tile-tags {
  margin-top: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  padding-top: 0.6rem;
}
.works-tile-tag {
  padding: 0.1rem 0.4rem;
  border: 1px solid var(--color-rule);
  border-radius: 999px;
  font-family: var(--font-ui);
  font-size: 0.62rem;
  color: var(--color-ink-soft);
}
.works-tile-tag.is-match {
  background: var(--color-ink);
  color: var(--color-stone);
  border-color: var(--color-ink);
}
.works-tile-crossref {
  margin-top: 0.4rem;
  font-family: var(--font-ui);
  font-size: 0.62rem;
  color: var(--color-burgundy);
}

.works-empty {
  margin-top: 2rem;
  font-style: italic;
  color: var(--color-ink-soft);
  text-align: center;
}
.works-empty[hidden] { display: none; }
```

The existing `/* Games index */` block (starting at line 2237) and everything below it stays unchanged.

- [ ] **Step 14.2: Append new §36 at end of file.**

```css
/* =========================================================
 * §36 Works graph
 * Constellation panel (in-page on desktop) + standalone /works/graph/.
 * Reuses §27 shared graph scaffolding (toggle, panel, toolbar, canvas,
 * legend, resize handle). This section adds works-specific node + edge
 * styling and the panel filter-chip row.
 * ========================================================= */

.works-graph-node-badge {
  fill: url(#works-graph-badge-gradient);
  stroke: var(--color-rule);
  stroke-width: 1;
}
.works-graph-node[data-medium="game"] use { color: var(--color-burgundy); }
.works-graph-node[data-medium="music"] use { color: var(--color-steel); }
.works-graph-node[data-medium="poetry"] use { color: var(--color-green); }
.works-graph-node-label {
  font-family: var(--font-ui);
  font-size: 0.68rem;
  fill: var(--color-ink);
  text-anchor: middle;
  pointer-events: none;
}
.works-graph-node[data-featured="true"] .works-graph-node-label {
  font-weight: 600;
}

.works-graph-edge-tag-share {
  stroke: var(--color-rule);
  stroke-width: 1;
  opacity: 0.7;
}
.works-graph-edge-cross-ref {
  stroke: var(--color-ink-soft);
  stroke-width: 1.25;
  stroke-dasharray: 4 3;
  opacity: 0.8;
}

/* Standalone /works/graph/ */
.works-graph-page .graph-page-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 1.5rem 0 1rem 0;
  font-family: var(--font-ui);
  font-size: 0.78rem;
}
.works-graph-summary {
  color: var(--color-ink-soft);
  margin-right: 1rem;
}
.graph-page-canvas {
  display: block;
  width: 100%;
  height: 70vh;
  min-height: 480px;
  border: 1px solid var(--color-rule);
  border-radius: 6px;
  background: var(--color-stone);
}
.graph-page-legend {
  display: flex;
  gap: 1.5rem;
  margin-top: 0.75rem;
  font-family: var(--font-ui);
  font-size: 0.78rem;
  color: var(--color-ink-soft);
}
.legend-mark {
  display: inline-block;
  width: 22px;
  height: 1px;
  margin-right: 0.4rem;
  vertical-align: middle;
  background: var(--color-ink-soft);
}
.legend-mark-dashed {
  background: none;
  border-top: 1.25px dashed var(--color-ink-soft);
}

/* The shared badge gradient — referenced by .works-graph-node-badge `fill: url(#...)`
   above. The graph mounts an SVG <defs> at runtime containing this gradient. */
```

The badge gradient definition needs an SVG `<defs>` block emitted into the canvas. Add this to the panel + standalone canvas inside `works-graph.js`'s init function (Task 10 trim should add it — note it now if missed):

```js
// In the d3 mount fn, before drawing nodes, append:
const defs = svg.append("defs");
const grad = defs.append("linearGradient")
  .attr("id", "works-graph-badge-gradient")
  .attr("x1", "0").attr("y1", "0").attr("x2", "1").attr("y2", "1");
grad.append("stop").attr("offset", "0%").attr("stop-color", "var(--color-burgundy)").attr("stop-opacity", "0.10");
grad.append("stop").attr("offset", "100%").attr("stop-color", "var(--color-steel)").attr("stop-opacity", "0.08");
```

If your `works-graph.js` doesn't yet include this, add it now in `works-graph.js` and re-commit Task 10's commit isn't strictly necessary — folding into Task 14's commit is fine since the two halves work together.

- [ ] **Step 14.3: Verify contrast linter still passes.**

```bash
python3 tools/check-contrast.py
```

Expected: PASS — palette unchanged.

- [ ] **Step 14.4: Visually spot-check the dev server.**

```bash
hugo server --buildDrafts
# In browser: http://localhost:1313/works/
```

Expected: Bento tiles styled (rounded corners, glyph in correct color per medium, title + meta visible). Click ⊞ Graph view — the panel slides in. Click again or the ✕ — it closes. At ≤720px the layout collapses to 2 columns; at ≤480px to 1 column.

- [ ] **Step 14.5: Commit.**

```bash
git add assets/css/main.css assets/js/works-graph.js
git commit -m "css: §33 umbrella Bento rules; §36 works graph; works-graph.js defs"
```

---

### Task 15 — Tweak `works.js` to recognize the new strip + panel

**Files:**
- Modify: `assets/js/works.js`

The existing `works.js` already wires `setupFilterChips` against `.works-games-grid` / `.works-music-list` / `.works-poetry-list`. The umbrella needs the same wire-up against `.works-bento` and the medium chips.

- [ ] **Step 15.1: Read the current `works.js`.**

```bash
wc -l assets/js/works.js
```

Open the file. Confirm it has a `setupFilterChips({ containerSelector, cardSelector, sectionSelector?, emptyStateSelector? })` call pattern and a per-page selector guard.

- [ ] **Step 15.2: Add an umbrella branch.**

After the existing per-section wire-ups, add a guard for the umbrella page:

```js
// Umbrella (/works/) — Bento grid + tag + medium dims.
if (document.querySelector(".works-bento")) {
  setupFilterChips({
    containerSelector: ".filter-chips",
    cardSelector: ".works-tile",
    emptyStateSelector: ".works-empty",
  });

  // Hook up the graph toggle.
  const toggle = document.getElementById("works-graph-toggle");
  const panel = document.getElementById("works-graph-panel");
  const closeBtn = panel?.querySelector(".graph-panel-close");
  if (toggle && panel) {
    const open = () => {
      panel.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      // Mobile (≤720px): navigate to /works/graph/ instead of toggling.
      // works-graph.js's mount fn handles the actual graph drawing.
    };
    const close = () => {
      panel.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
    };
    toggle.addEventListener("click", () => {
      if (window.matchMedia("(max-width: 720px)").matches) {
        window.location.href = "/works/graph/";
        return;
      }
      panel.hidden ? open() : close();
    });
    closeBtn?.addEventListener("click", close);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !panel.hidden) close();
    });
  }
}
```

- [ ] **Step 15.3: Test in the dev server.**

```bash
hugo server --buildDrafts
# Click a tag chip → tiles narrow.
# Click a medium chip → narrows by medium AND with tag.
# Click ⊞ Graph view → panel opens, graph renders inside.
# Click ✕ or press Esc → panel closes.
```

- [ ] **Step 15.4: Commit.**

```bash
git add assets/js/works.js
git commit -m "works.js: wire umbrella Bento filter strip + graph toggle"
```

---

### Task 16 — Seed Bento variation by setting `featured` / `tile_size` on a few fixtures

**Files:**
- Modify: `content/works/games/example-playable-full-release/index.md`
- Modify: `content/works/music/example-album-with-tracks/index.md`
- Modify: `content/works/poetry/example-poem-collected/index.md`

The linter accepts these fields now (Task 1). Adding them to a few fixtures makes the Bento visually varied in dev — exercises the `2×1` / `2×2` cases.

- [ ] **Step 16.1: Add `featured: true` and `hero: true` to the games fixture.**

Open `content/works/games/example-playable-full-release/index.md`. In the YAML frontmatter, add at the end (before the closing `---`):

```yaml
featured: true
hero: true
```

- [ ] **Step 16.2: Add `featured: true` to the music fixture.**

Open `content/works/music/example-album-with-tracks/index.md`. Add:

```yaml
featured: true
```

- [ ] **Step 16.3: Add `tile_size: large` to the poetry fixture.**

Open `content/works/poetry/example-poem-collected/index.md`. Add:

```yaml
tile_size: large
```

- [ ] **Step 16.4: Verify the linter accepts the changes.**

```bash
python3 tools/check_works_fixtures.py
```

Expected: `check_works_fixtures: OK`.

- [ ] **Step 16.5: Visually verify the Bento.**

```bash
hugo server --buildDrafts
# /works/ should now show one 2x2 tile (the game with featured + hero),
# one 2x1 tile (the music album), and 10 standard 1x1 tiles.
```

- [ ] **Step 16.6: Commit.**

```bash
git add content/works/games/example-playable-full-release/index.md \
        content/works/music/example-album-with-tracks/index.md \
        content/works/poetry/example-poem-collected/index.md
git commit -m "fixtures: seed Bento variation via featured/hero/tile_size"
```

---

### Task 17 — Update CLAUDE.md project status

**Files:**
- Modify: `CLAUDE.md` (Project status section)

- [ ] **Step 17.1: Update the Works bullet under "Shipped".**

In `CLAUDE.md`, find the line under "Project status":

```
- **Works** (Phase 6): umbrella + games / music / poetry indexes + per-item pages. Runtime-heavy pieces deferred — see table below.
```

Replace with:

```
- **Works** (Phase 6): polished umbrella (Bento variable-tile grid + tag-cloud filter + ⊞ Graph view toggle with d3-force constellation; three hand-authored medium glyphs: gamepad/eighth-note/quill); games / music / poetry indexes + per-item pages. Runtime-heavy pieces deferred — see table below.
```

- [ ] **Step 17.2: Add the slice spec to Reference docs.**

In `CLAUDE.md`, under "Reference docs", add a bullet:

```
- **Phase 6 umbrella polish spec**: `docs/superpowers/specs/2026-05-12-works-umbrella-polish-design.md`. Phase 6 Slice 0.
```

- [ ] **Step 17.3: Commit.**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md: works umbrella polish shipped"
```

---

### Task 18 — Full CI gate sweep + dev-server final spot-check

- [ ] **Step 18.1: Run every Python CI gate locally.**

```bash
python3 tools/check-contrast.py && \
python3 tools/check_fixtures.py && \
python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -3 && \
python3 tools/check_garden_fixtures.py && \
python3 -m unittest tools/test_check_garden_fixtures.py -v 2>&1 | tail -3 && \
python3 tools/check_garden_links.py && \
python3 -m unittest tools/test_check_garden_links.py -v 2>&1 | tail -3 && \
python3 tools/check_filter_chips_config.py && \
python3 -m unittest tools/test_check_filter_chips_config.py -v 2>&1 | tail -3 && \
python3 tools/check_research_fixtures.py && \
python3 -m unittest tools/test_check_research_fixtures.py -v 2>&1 | tail -3 && \
python3 tools/check_research_links.py && \
python3 -m unittest tools/test_check_research_links.py -v 2>&1 | tail -3 && \
python3 tools/check_citations.py && \
python3 -m unittest tools/test_check_citations.py -v 2>&1 | tail -3 && \
python3 tools/check_works_fixtures.py && \
python3 -m unittest tools/test_check_works_fixtures.py -v 2>&1 | tail -3 && \
python3 tools/check_works_links.py && \
python3 -m unittest tools/test_check_works_links.py -v 2>&1 | tail -3
```

Expected: every check exits 0; every unittest sweep reports OK.

- [ ] **Step 18.2: Production Hugo build.**

```bash
# IMPORTANT: ensure no dev server is running first (per memory).
pkill -f 'hugo server' 2>/dev/null
hugo --minify
```

Expected: build succeeds with no errors. `public/` populated.

- [ ] **Step 18.3: Dev-server visual spot-check (the user wants to eyeball before merging).**

```bash
hugo server --buildDrafts
# Open http://localhost:1313/works/
```

Run through this checklist in the browser:

1. Header reads "Works" with the intro line.
2. Tag-chip strip renders; "Tag" label, "All" chip first, then primary tags from the linter-validated list.
3. Medium-chip row renders; "Medium" label, "All" / "Games" / "Music" / "Poetry".
4. Sort dropdown defaults to "featured" and renders.
5. ⊞ Graph view button is visible, burgundy outlined.
6. Bento tiles render with the three medium glyphs in correct colors (game=burgundy, music=steel, poetry=green).
7. At least one `2×2` (featured + hero), one `2×1` (featured), and several `1×1` tiles visible.
8. Click a tag chip — tiles narrow; empty state appears if zero tiles match.
9. Click ⊞ Graph view — panel slides in; nodes are visible, with the medium glyphs inside each node badge.
10. Solid edges and dashed edges both render (look for the `lyrics_poem ↔ set_to_music` pair — should be dashed).
11. Drag a node — it moves and stays.
12. Click "Reset positions" — nodes float back.
13. Click ✕ or press Esc — panel closes.
14. Resize window to ≤720px — Bento collapses to 2 cols; click ⊞ now navigates to `/works/graph/`.
15. `/works/graph/` renders the full-page version.
16. Switch theme — glyph colors update (`currentColor` follows token swap).
17. No JS console errors at any point.

Kill the dev server before stopping.

- [ ] **Step 18.4: Stop here for user spot-check.**

Don't merge or push — the author wants to eyeball the changes (memory: "Always offer dev-server spot-check before merging"). Surface a summary of what shipped and the spot-check checklist; wait for go-ahead before any merge action.

---

### Task 19 — Update memory entries after author sign-off

**Files:**
- Modify: `/home/a3madkour/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/project_works_umbrella_polish_pending.md` (delete or repurpose)
- Modify: `/home/a3madkour/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/MEMORY.md` (add new entry, remove pending one)

ONLY do this after the author confirms the slice is good to merge.

- [ ] **Step 19.1: Remove the "pending" memory.**

```bash
rm /home/a3madkour/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/project_works_umbrella_polish_pending.md
```

- [ ] **Step 19.2: Add a "merged" memory.**

Create `/home/a3madkour/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/project_works_umbrella_polish_slice.md`:

```markdown
---
name: works-umbrella-polish-slice-merged
description: Phase 6 Slice 0 (works umbrella → Bento + tag-cloud + ⊞ Graph view); merged YYYY-MM-DD
metadata:
  type: project
---

Phase 6 Slice 0 shipped: `/works/` rebuilt as Bento variable-tile grid (`partials/works/tile.html`) + tag-cloud filter + medium chips + ⊞ Graph view toggle with force-directed constellation (`assets/js/works-graph.js`, copy + trim of `research-graph.js`). Three hand-authored medium glyphs (`assets/images/icons/glyph-{game,music,poetry}.svg`) ship here and will feed the future Phase 7 homepage Studio strip — single visual source via `partials/works/glyph-sprite.html` with manual sync to the standalone files. Works JS bundle split: `entry-works-umbrella.js` (~110 KB w/ d3) loads only on `/works/` + `/works/graph/`; `entry-works.js` (~6 KB) stays on per-item pages. Two new partials per the graph pattern (`graph-data` cached via `partialCached`, `graph-script` JSON wrapper). New CSS §36 "Works graph"; §33 umbrella block replaced. Linter extensions: `tile_size`/`featured`/`hero` accepted on works fixtures; `data/filter-chips.yaml` gains a `works` umbrella key that aggregates across the three sub-sections via a new `SECTION_AGGREGATIONS` map in `check_filter_chips_config.py`. No new CI gates; no new tokens; no new fonts; no npm. Spec at `docs/superpowers/specs/2026-05-12-works-umbrella-polish-design.md`; plan at `docs/superpowers/plans/2026-05-12-works-umbrella-polish.md`.
```

- [ ] **Step 19.3: Update MEMORY.md index.**

In `MEMORY.md`, find and remove the line:

```
- [Works umbrella polish pending](project_works_umbrella_polish_pending.md) — user found /works/ bland; brainstorm umbrella polish as Slice 0 of the next Phase 6 slice
```

Add the new line near the existing works-section-slice entry:

```
- [Works umbrella polish slice — merged](project_works_umbrella_polish_slice.md) — Phase 6 Slice 0 (Bento + tag-cloud + ⊞ Graph view) shipped YYYY-MM-DD
```

Replace `YYYY-MM-DD` with the actual merge date after the user merges.

- [ ] **Step 19.4: Final merge / push happens here, per the author's instructions.**

This plan does NOT commit, merge, or push remotely. The author will instruct after spot-check (memory: `Always offer dev-server spot-check before merging`).

---

## Self-review

**Spec coverage check** (every §-level requirement in the spec maps to a task):

- §2 in-scope: glyphs (Task 4), layout rewrite (Task 7), section-card delete (Task 7), graph (Tasks 8–10, 13), tile partial (Task 6), CSS §33+§36 (Task 14), filter-chips.yaml (Task 3), bundle split (Tasks 11–12). ✓
- §3 visual design: header in Task 7; filter strip in Task 7; Bento grid in Tasks 6+14; graph panel in Tasks 9, 10, 14; standalone page in Task 13. ✓
- §4 data contracts: 4.1 frontmatter additions exercised in Task 16; 4.2 filter-chips.yaml in Task 3; 4.3 partial unchanged (caller-driven); 4.4 graph-data partial in Task 8; 4.5 sprite in Task 5. ✓
- §5 component map: every file in the spec's component table maps to a task. ✓
- §6 JS bundle strategy: scripts.html in Task 12, entry file in Task 11. ✓
- §7 reuse map: no tasks needed (these are unchanged). ✓
- §8 accessibility: tile partial has `role="img" aria-label="<medium>"` (Task 6); graph button has `aria-expanded` + `aria-controls` (Task 9 panel + Task 15 toggle wire-up); reduced-motion handled by the inherited research-graph trim (Task 10). ✓
- §9 tradeoffs: design decisions, no implementation. ✓
- §10 risks: bundle size acknowledged; drift between sprite + SVG files acknowledged (Task 5 comment + spec §10). ✓
- §11 acceptance: all 9 criteria exercised in Task 18 spot-check checklist. ✓

**Placeholder scan**: searched for "TBD", "TODO", "fill in", "add appropriate". None present. Every Hugo template, JS, CSS, and Python snippet contains the actual code an engineer can paste in or apply via Edit.

**Type / name consistency**: `works-graph-data` JSON id, `works-graph-panel` aside id, `works-graph-toggle` button id, `g-game` / `g-music` / `g-poetry` symbol ids, `entry-works-umbrella.js` entry name, `data-medium` / `data-span` / `data-tile-size` tile attributes — all consistent across Tasks 5/7/8/9/10/12/14/15.

**One inline correction during the review**: Task 8 was originally a single partial; split into `graph-data.html` + `graph-data-inner.html` so the outer call can use `partialCached` with a fixed key string (the cache key argument must be a literal/string, and a partial that takes a page context can be cached this way only via the wrapper pattern). Spec §4.4's intent is preserved.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-12-works-umbrella-polish.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Best for a 19-task plan with mixed concerns (Python linters → Hugo templates → CSS → JS); each subagent gets a focused brief.

**2. Inline Execution** — Execute tasks in this session using `executing-plans`, batch execution with checkpoints for review.

Which approach?
