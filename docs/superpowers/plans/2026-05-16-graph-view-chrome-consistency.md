# Graph-view chrome consistency — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the graph launcher button, in-view controls (filter chips / action buttons / close), and legend look identical across garden / research / works and across the in-page panel vs the standalone `/x/graph/` page — without touching graph rendering.

**Architecture:** One canonical control CSS set in §27 + one shared `graph-legend.html` partial used by all 6 graph surfaces, so the drift has a single source of truth and cannot structurally recur. Per-context differences (panel vs standalone page) become two named modifier classes, not section-by-section copies. A sibling-less static linter (`check_graph_chrome.py`, modeled on `check_smoke.py`) gates against re-drift.

**Tech Stack:** Hugo templates + partials, hand-rolled CSS (`assets/css/main.css`, numbered sections), vanilla d3 graph JS (`assets/js/{garden,research,works}-graph.js`), stdlib-only Python linters, `tools/ci-local.sh` + `.github/workflows/hugo.yaml`.

**Spec:** `docs/superpowers/specs/2026-05-14-graph-view-consistency-design.md`

**Branch:** Create `feature/graph-chrome-consistency` off `master` before Task 1 (matches the repo's feature-branch + merge pattern; do not work on `master`).

---

## Canonical vocabulary (used by every task — read first)

These are the ONLY graph-control class names after this slice. Every task drives toward exactly this set:

| Canonical | Replaces | Notes |
|---|---|---|
| `.graph-toggle` | itself + `.works-umbrella-toolbar .graph-toggle` | One rule in §27. Option B: quiet grey-rule ghost, `--font-ui`, burgundy fill on `aria-expanded="true"`. |
| `.graph-toolbar` | `.graph-panel-toolbar`, `.garden-graph-toolbar`, `.research-graph-toolbar`, `.graph-page-toolbar` | Context-free base. |
| `.graph-toolbar--panel` / `.graph-toolbar--page` | the per-context padding/border/margin that used to live in the per-section selectors | Two named variants. Resolves the spec's open item: shared base + 2 modifiers. |
| `.graph-chip` | `.chip` (garden/research), `.filter-chip` (works graph only) | Filter chip. Active = `aria-pressed="true"` ONLY (no `.is-active`). |
| `.graph-action` | `.chip.chip-action` (garden/research), `.graph-panel-toolbtn` (works) | Action button (Reset view / Reset positions). |
| `.graph-toolbar-divider` | `.toolbar-divider` | Divider before the action group. |
| `.graph-hint` | itself | Already shared; unchanged. |
| `.graph-panel-close` | itself | Already shared; unchanged. Glyph normalized to `×`. |
| `.graph-legend` + `.graph-legend--panel` / `.graph-legend--page` | `.graph-panel-legend`, `.garden-graph-legend`, `.research-graph-legend`, `.graph-page-legend` | Rendered only by `partials/graph-legend.html`. |
| `.graph-legend-key` / `.graph-legend-swatch` / `.graph-legend-mark` | `.swatch`, `.legend-item`, `.legend-mark`, `.legend-mark-dashed` | Legend internals. |

`.path-log-clear` (garden path-log "clear" button) currently shares a CSS rule with `.graph-toggle` but is NOT a graph control — Task 3 gives it its own identical-looking standalone rule so it does not change.

---

## Task 1: Regression-guard linter (test-first — fails until the refactor lands)

**Files:**
- Create: `tools/check_graph_chrome.py`
- Modify: `tools/ci-local.sh` (pre-build linter group)
- Modify: `.github/workflows/hugo.yaml` (pre-build linter group)
- Modify: `CLAUDE.md` (linter inventory + CI step count)

- [ ] **Step 1: Write the linter**

This is a static source check (no built `public/` needed). Sibling-less, like `tools/check_smoke.py` (logic is thin: substring scans + file-presence). It fails NOW (drift selectors exist; partial does not) and passes only after Tasks 2–6.

Create `tools/check_graph_chrome.py`:

```python
"""Graph-chrome consistency gate.

Enforces the single-source-of-truth invariants from
docs/superpowers/specs/2026-05-14-graph-view-consistency-design.md:

  1. No pruned per-section graph-control selector survives in main.css.
  2. The 6 graph surfaces each include partials/graph-legend.html and do
     NOT hand-roll a legend or per-section toolbar/legend class.

Sibling-less (no paired unit test): the logic is substring scans +
file-presence checks, too thin to warrant pairing — same rationale as
tools/check_smoke.py (spec §3.1).
"""

import sys
from pathlib import Path

CSS = Path("assets/css/main.css")

# Selectors that must not reappear once the refactor lands.
FORBIDDEN_CSS = [
    ".works-umbrella-toolbar .graph-toggle",
    ".garden-graph-toolbar",
    ".research-graph-toolbar",
    ".graph-page-toolbar",
    ".graph-panel-toolbar",
    ".graph-panel-legend",
    ".garden-graph-legend",
    ".research-graph-legend",
    ".graph-page-legend",
    ".graph-panel-toolbtn",
]

# The 6 graph surfaces. Each must include the shared legend partial and
# must not hand-roll a legend / per-section toolbar class.
SURFACES = [
    Path("layouts/partials/garden/graph-panel.html"),
    Path("layouts/partials/research/graph-panel.html"),
    Path("layouts/partials/works/graph-panel.html"),
    Path("layouts/garden/graph.html"),
    Path("layouts/research/graph.html"),
    Path("layouts/works/graph.html"),
]
LEGEND_PARTIAL_CALL = 'partial "graph-legend.html"'
FORBIDDEN_MARKUP = [
    "graph-panel-legend",
    "graph-page-legend",
    "garden-graph-legend",
    "research-graph-legend",
    "graph-panel-toolbtn",
    "graph-panel-toolbar",
    "garden-graph-toolbar",
    "research-graph-toolbar",
    "graph-page-toolbar",
    'class="filter-chip',  # works graph used the global filter-chip class
    "legend-mark-solid",
    "legend-mark-dashed",
]


def main() -> int:
    errors = []

    if not CSS.is_file():
        print("check_graph_chrome: assets/css/main.css missing", file=sys.stderr)
        return 2
    css = CSS.read_text(encoding="utf-8")
    for sel in FORBIDDEN_CSS:
        if sel in css:
            errors.append(f"main.css still contains forbidden selector: {sel}")

    for surface in SURFACES:
        if not surface.is_file():
            errors.append(f"missing surface file: {surface}")
            continue
        text = surface.read_text(encoding="utf-8")
        if LEGEND_PARTIAL_CALL not in text:
            errors.append(f"{surface}: does not include {LEGEND_PARTIAL_CALL}")
        for bad in FORBIDDEN_MARKUP:
            if bad in text:
                errors.append(f"{surface}: still contains hand-rolled chrome: {bad!r}")

    if errors:
        print(f"check_graph_chrome: {len(errors)} issue(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"check_graph_chrome: OK ({len(SURFACES)} surfaces)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it — verify it FAILS now**

Run: `python3 tools/check_graph_chrome.py; echo "exit=$?"`
Expected: `exit=1` with issues listing forbidden selectors (`.graph-panel-toolbar`, `.graph-page-legend`, …) and every surface missing the legend partial. This proves the gate is live before the refactor.

- [ ] **Step 3: Wire into `tools/ci-local.sh`**

This is a SOURCE check (no `public/`), so it runs with the pre-build linter group, not the post-build group. Open `tools/ci-local.sh`, find the pre-build linter section (the block of `python3 tools/check_*.py` calls that runs BEFORE `HUGO_ENVIRONMENT=production hugo --minify` at line ~76 — it is above the `separator "Production build …"` line). Add, as the last line of that pre-build group:

```bash
python3 tools/check_graph_chrome.py
```

- [ ] **Step 4: Wire into `.github/workflows/hugo.yaml`**

Find the pre-build linter steps (the `Verify …` / `check_*` steps that run BEFORE the `Build with Hugo` step at line ~116). Add a new step immediately before `- name: Build with Hugo`:

```yaml
      - name: Verify graph-chrome consistency
        run: python3 tools/check_graph_chrome.py
```

- [ ] **Step 5: Update `CLAUDE.md` inventory**

In `CLAUDE.md`, the Commands section sentence currently reads (search for "sibling-less linter"):

> `tools/check_smoke.py` is a sibling-less linter (no paired test file — spec §3.1: logic is too thin to warrant pairing).

Replace with:

> `tools/check_smoke.py` and `tools/check_graph_chrome.py` are sibling-less linters (no paired test file — spec §3.1: logic is too thin to warrant pairing).

In the Deployment section, find the total step count "Total: 50 named steps." and change to "Total: 51 named steps." Also update the parenthetical "(contrast + 16 linter pairs = 33 steps)" only if a count is stated for sibling-less linters; `check_graph_chrome.py` adds exactly one pre-build step — adjust the running total wording to 51 consistently wherever "50 named steps" appears.

- [ ] **Step 6: Commit**

```bash
git add tools/check_graph_chrome.py tools/ci-local.sh .github/workflows/hugo.yaml CLAUDE.md
git commit -m "test(graph): add sibling-less graph-chrome consistency gate (fails until refactor)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Shared `graph-legend.html` partial + canonical legend CSS

**Files:**
- Create: `layouts/partials/graph-legend.html`
- Modify: `assets/css/main.css` (§27 — add `.graph-legend*` rules)

- [ ] **Step 1: Create the partial**

Single source of truth for all 6 surfaces. Structure key is always server-rendered (identical skeleton, per-section wording). Color key: research + works rendered server-side here from the global `site`; garden emits an empty `data-graph-legend-dynamic` slot that `garden-graph.js` fills with live tag swatches (Task 6).

**Swatch coloring (do NOT use interpolated inline `style`):** server-rendered swatches use a `data-swatch="0|1|2"` attribute resolved by static §27 CSS rules (the codebase's existing `data-theme-color` precedent). Interpolating a CSS custom-property name into `style="background:var({{ … }})"` is sanitized by Go `html/template` to `var(ZgotmplZ)` (colorless) — it MUST NOT be used. Garden is the one exception: its swatches are injected by `garden-graph.js` via `el.style.background = tagColor(tag)` (a JS-set style, not a Go-template context, so not sanitized) — that stays inline-style and is correct (Task 6). Research theme order MUST mirror `partials/research/graph-data.html`'s `themePaletteOrder` exactly (two-pass: `sort "slug" "asc"` then `sort "weight" "asc"`, stable) so legend swatch colors match the graph nodes' `data-theme-color`.

Create `layouts/partials/graph-legend.html`:

```go-html-template
{{- /* Shared graph legend — the ONLY place a graph legend is constructed.
       Param: dict "section" ("garden"|"research"|"works")
                   "variant" ("panel"|"page")
       Structure key: always server-rendered, identical skeleton.
       Color key: research/works server-rendered here via data-swatch +
       static §27 CSS; garden = empty dynamic slot. garden-graph.js fills
       .graph-legend-colorkey[data-graph-legend-dynamic] with inline-styled
       swatches (tag palette is content-dependent) — see Task 6. */ -}}
{{- $section := .section -}}
{{- $variant := .variant -}}
{{- $primary := "" -}}
{{- $secondary := "" -}}
{{- $colors := slice -}}
{{- $dynamic := false -}}
{{- if eq $section "garden" -}}
  {{- $primary = "same topic" -}}
  {{- $secondary = "cross-topic" -}}
  {{- $dynamic = true -}}
{{- else if eq $section "research" -}}
  {{- $primary = "parent link" -}}
  {{- $secondary = "cross-theme" -}}
  {{- /* Mirror graph-data.html's themePaletteOrder EXACTLY (two-pass:
         sort slug asc, then weight asc — stable) so legend swatch colors
         match the graph nodes' data-theme-color. */ -}}
  {{- $themes := slice -}}
  {{- range where site.RegularPages "Type" "research-theme" -}}
    {{- $themes = $themes | append (dict "label" .Title "slug" (path.Base .File.Dir) "weight" (default 0 .Params.weight)) -}}
  {{- end -}}
  {{- $sorted := sort (sort $themes "slug" "asc") "weight" "asc" -}}
  {{- $idx := 0 -}}
  {{- range $sorted -}}
    {{- if lt $idx 3 -}}
      {{- $colors = $colors | append (dict "label" .label "swatch" $idx) -}}
      {{- $idx = add $idx 1 -}}
    {{- end -}}
  {{- end -}}
{{- else if eq $section "works" -}}
  {{- $primary = "shared tags" -}}
  {{- $secondary = "cross-medium" -}}
  {{- $colors = slice
        (dict "label" "Games" "swatch" 0)
        (dict "label" "Music" "swatch" 1)
        (dict "label" "Poetry" "swatch" 2) -}}
{{- end -}}
<ul class="graph-legend graph-legend--{{ $variant }}" aria-label="Graph legend">
  <li class="graph-legend-colorkey"{{ if $dynamic }} data-graph-legend-dynamic{{ end }}>
    {{- range $colors }}
    <span class="graph-legend-key"><span class="graph-legend-swatch" data-swatch="{{ .swatch }}"></span>{{ .label }}</span>
    {{- end }}
  </li>
  <li class="graph-legend-structure">
    <span class="graph-legend-key"><span class="graph-legend-swatch graph-legend-swatch--sm"></span><span class="graph-legend-swatch graph-legend-swatch--lg"></span>size = connections</span>
    <span class="graph-legend-key"><span class="graph-legend-mark" aria-hidden="true"></span>{{ $primary }}</span>
    <span class="graph-legend-key"><span class="graph-legend-mark graph-legend-mark--dashed" aria-hidden="true"></span>{{ $secondary }}</span>
  </li>
</ul>
```

- [ ] **Step 2: Add canonical legend CSS to §27**

In `assets/css/main.css`, locate the §27 legend block — the `.graph-panel-legend { … }` rule and its `.graph-panel-legend .swatch { … }` partner (verbatim current text):

```css
.graph-panel-legend {
  list-style: none;
  margin: 0;
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--color-rule);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}
.graph-panel-legend .swatch {
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-right: 0.25rem;
  vertical-align: middle;
}
```

Replace BOTH rules with the canonical legend system:

```css
.graph-legend {
  list-style: none;
  margin: 0;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.graph-legend--panel {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--color-rule);
}
.graph-legend--page {
  margin-top: 1rem;
  padding: 0;
}
.graph-legend-colorkey,
.graph-legend-structure {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}
.graph-legend-colorkey:empty { display: none; }
.graph-legend-key {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}
.graph-legend-swatch {
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  vertical-align: middle;
}
.graph-legend-swatch[data-swatch="0"] { background: var(--color-burgundy); }
.graph-legend-swatch[data-swatch="1"] { background: var(--color-steel); }
.graph-legend-swatch[data-swatch="2"] { background: var(--color-green); }
.graph-legend-swatch--sm { width: 7px; height: 7px; background: var(--color-ink-fade); }
.graph-legend-swatch--lg { width: 12px; height: 12px; background: var(--color-ink-fade); }
.graph-legend-mark {
  display: inline-block;
  width: 22px;
  height: 0;
  border-top: 2px solid var(--color-ink-soft);
  vertical-align: middle;
}
.graph-legend-mark--dashed { border-top-style: dashed; }
```

(The pruning of the now-orphaned per-section legend rules in §28/§31/§36 happens in Task 5, after the surfaces are repointed.)

- [ ] **Step 3: Verify the partial — syntactically valid AND free of the CSS-sanitization pitfall**

The partial is not yet wired into any surface (Task 5 does that), so it won't appear in `public/` yet. These checks confirm it compiles AND that the ZgotmplZ class of bug cannot occur:

```bash
grep -n 'style="background:var(' layouts/partials/graph-legend.html        # MUST print nothing
grep -c 'data-swatch="{{ .swatch }}"' layouts/partials/graph-legend.html    # MUST print 1
pkill -f 'hugo server' 2>/dev/null; rm -rf public
HUGO_ENVIRONMENT=production hugo --minify >/tmp/t2-build.log 2>&1; echo "build exit=$?"; tail -3 /tmp/t2-build.log
```

Expected: first grep prints nothing (no Go-interpolated CSS — that would render `var(ZgotmplZ)`); second prints `1`; `build exit=0`. If the first grep prints a line, the colorless-swatch bug is present — fix to the `data-swatch` form before continuing. If `hugo --minify` errors, the partial has a template bug — fix before continuing (re-check `range`/`dict`/`slice`/`sort`/`add` against the verbatim spec above). No dev server may be alive during `hugo --minify`.

- [ ] **Step 4: Commit**

```bash
git add layouts/partials/graph-legend.html assets/css/main.css
git commit -m "feat(graph): shared graph-legend partial + canonical §27 legend CSS

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Canonical control CSS in §27 (toggle / toolbar / chip / action / divider)

**Files:**
- Modify: `assets/css/main.css` (§27 + the §24 launcher block + delete the §33 works override)

- [ ] **Step 1: Replace the launcher rule + split off `.path-log-clear`**

In `assets/css/main.css`, find this verbatim block (currently ~line 1197, in the garden path-log area):

```css
/* .graph-toggle appears in two places: inside .garden-path-log on note
   pages, and standalone on the garden index. Style both — without the
   explicit color, the standalone button falls back to UA ButtonText which
   doesn't respect dark mode. */
.garden-path-log .path-log-clear,
.graph-toggle {
  background: transparent;
  border: 1px solid var(--color-rule);
  border-radius: 4px;
  padding: 0.15rem 0.55rem;
  font: inherit;
  color: var(--color-ink-soft);
  cursor: pointer;
}
.garden-path-log .path-log-clear:hover,
.graph-toggle:hover {
  background: var(--color-stone);
  color: var(--color-ink);
}
.graph-toggle[aria-expanded="true"] {
  background: var(--color-burgundy);
  color: var(--color-tile);
  border-color: var(--color-burgundy);
}
```

Replace it with ONLY the `.path-log-clear` rule (graph-toggle moves to §27). `.path-log-clear` keeps a visually identical standalone rule so it does not change:

```css
/* .path-log-clear (garden path-log "clear" button). Was co-styled with
   .graph-toggle; now standalone so the graph launcher can live in §27.
   Explicit color so it doesn't fall back to UA ButtonText (dark mode). */
.garden-path-log .path-log-clear {
  background: transparent;
  border: 1px solid var(--color-rule);
  border-radius: 4px;
  padding: 0.15rem 0.55rem;
  font: inherit;
  color: var(--color-ink-soft);
  cursor: pointer;
}
.garden-path-log .path-log-clear:hover {
  background: var(--color-stone);
  color: var(--color-ink);
}
```

- [ ] **Step 2: Delete the works-umbrella launcher override**

Find and DELETE this verbatim block (currently ~line 2304, in §33):

```css
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
```

The `margin-left: auto` is replaced structurally in Task 4 (a container rule, not a `.graph-toggle` override).

- [ ] **Step 3: Add canonical toggle + toolbar + chip + action CSS to §27**

In `assets/css/main.css` §27, find this verbatim block:

```css
.graph-panel-toolbar {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--color-rule);
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
}
.graph-panel-toolbar .label {
  color: var(--color-ink-soft);
  margin-right: 0.2rem;
}
.graph-panel-toolbar .chip {
  background: transparent;
  border: 1px solid var(--color-rule);
  border-radius: 999px;
  padding: 0.1rem 0.55rem;
  font: inherit;
  cursor: pointer;
  color: var(--color-ink-soft);
}
.graph-panel-toolbar .chip[aria-pressed="true"] {
  background: var(--color-burgundy);
  color: var(--color-tile);
  border-color: var(--color-burgundy);
}
```

Replace it with the canonical control system (toggle + toolbar + chip + action, context-free base + 2 modifiers):

```css
/* --- Graph launcher button (every page that opens a graph) --- */
.graph-toggle {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  background: transparent;
  border: 1px solid var(--color-rule);
  border-radius: 4px;
  padding: 0.28rem 0.7rem;
  color: var(--color-ink-soft);
  cursor: pointer;
}
.graph-toggle:hover {
  background: var(--color-stone);
  color: var(--color-ink);
}
.graph-toggle[aria-expanded="true"] {
  background: var(--color-burgundy);
  color: var(--color-tile);
  border-color: var(--color-burgundy);
}

/* --- Graph toolbar (filter chips + actions). Context-free base; the
       two modifiers carry only the panel-vs-page container chrome. --- */
.graph-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
}
.graph-toolbar--panel {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--color-rule);
}
.graph-toolbar--page {
  padding: 0.5rem 0;
  margin: 1rem 0;
  border-top: 1px solid var(--color-rule);
  border-bottom: 1px solid var(--color-rule);
}
.graph-toolbar .label {
  color: var(--color-ink-soft);
  margin-right: 0.2rem;
}
.graph-chip {
  background: transparent;
  border: 1px solid var(--color-rule);
  border-radius: 999px;
  padding: 0.1rem 0.6rem;
  font: inherit;
  cursor: pointer;
  color: var(--color-ink-soft);
}
.graph-chip[aria-pressed="true"] {
  background: var(--color-burgundy);
  color: var(--color-tile);
  border-color: var(--color-burgundy);
}
.graph-action {
  background: transparent;
  border: 1px dashed var(--color-ink-fade);
  border-radius: 999px;
  padding: 0.1rem 0.6rem;
  font: inherit;
  font-style: italic;
  cursor: pointer;
  color: var(--color-ink-soft);
}
.graph-action:hover {
  color: var(--color-ink);
  border-color: var(--color-ink-soft);
}
.graph-toolbar-divider {
  display: inline-block;
  width: 1px;
  height: 1rem;
  background: var(--color-rule);
  margin: 0 0.4rem;
  vertical-align: middle;
}
```

- [ ] **Step 4: Remove the now-superseded §27 divider + action-chip rules**

Still in §27, find and DELETE these two verbatim blocks (superseded by `.graph-toolbar-divider` / `.graph-action` above):

```css
/* Toolbar divider between filter chips and action chips */
.graph-panel-toolbar .toolbar-divider {
  display: inline-block;
  width: 1px;
  height: 1rem;
  background: var(--color-rule);
  margin: 0 0.4rem;
  vertical-align: middle;
}

/* Action chip variant: italic to visually separate from filter chips */
.graph-panel-toolbar .chip.chip-action {
  font-style: italic;
}
```

Leave `.graph-hint`, `.graph-hint kbd`, `.graph-panel`, `.graph-panel-header`, `.graph-panel-close`, `.graph-panel-canvas`, `.graph-panel-resize` untouched (already shared / not drifted). Normalize the close glyph in markup in Task 5 (not CSS).

- [ ] **Step 5: Build to confirm CSS still compiles**

Run: `pkill -f 'hugo server' 2>/dev/null; rm -rf public; HUGO_ENVIRONMENT=production hugo --minify >/dev/null 2>&1; echo "exit=$?"`
Expected: `exit=0`. (Visual correctness is verified in Task 7 once markup + JS are repointed.)

- [ ] **Step 6: Commit**

```bash
git add assets/css/main.css
git commit -m "feat(graph): canonical §27 control CSS (toggle/toolbar/chip/action); drop works override

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Launcher markup — unify label + right-align on works umbrella

**Files:**
- Modify: `layouts/works/list.html` (launcher label + container alignment)

`layouts/garden/list.html`, `layouts/research/list.html`, `layouts/partials/garden/path-log.html` already emit `class="graph-toggle"` with label `⊞ Graph` and need NO change (verified verbatim). Only works differs.

- [ ] **Step 1: Unify the works launcher label**

In `layouts/works/list.html`, find this verbatim markup:

```html
      <button type="button" id="works-graph-toggle" class="graph-toggle"
              aria-expanded="false" aria-controls="works-graph-panel">⊞ Graph view</button>
```

Replace with (label `⊞ Graph view` → `⊞ Graph`):

```html
      <button type="button" id="works-graph-toggle" class="graph-toggle"
              aria-expanded="false" aria-controls="works-graph-panel">⊞ Graph</button>
```

- [ ] **Step 2: Preserve right-alignment via the container (not a `.graph-toggle` override)**

The deleted override had `margin-left: auto`, which pushed the launcher to the far right of `.works-umbrella-toolbar` (a flex row also containing the Sort `<select>`). Re-establish that WITHOUT a per-section `.graph-toggle` selector (which the Task 1 linter forbids): read the `.works-umbrella-toolbar` base rule in `assets/css/main.css` (search `.works-umbrella-toolbar {`). It is a flex row. Add `justify-content: space-between;` to that existing `.works-umbrella-toolbar { … }` rule (append the one declaration inside the existing brace — do not create a new selector). The Sort label sits left, the launcher right — visually equivalent to before, no forbidden selector.

- [ ] **Step 3: Build + spot-check the works umbrella**

Run: `pkill -f 'hugo server' 2>/dev/null; rm -rf public; HUGO_ENVIRONMENT=production hugo --minify >/dev/null 2>&1 && grep -o '⊞ Graph[^<]*' public/works/index.html`
Expected: `⊞ Graph` (no "view"). Exactly one match.

- [ ] **Step 4: Commit**

```bash
git add layouts/works/list.html assets/css/main.css
git commit -m "fix(graph): unify launcher label to '⊞ Graph'; right-align via works toolbar container

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Wire the legend partial into all 6 surfaces + canonical toolbar markup; prune §28/§31/§36

**Files:**
- Modify: `layouts/partials/garden/graph-panel.html`
- Modify: `layouts/partials/research/graph-panel.html`
- Modify: `layouts/partials/works/graph-panel.html`
- Modify: `layouts/garden/graph.html`
- Modify: `layouts/research/graph.html`
- Modify: `layouts/works/graph.html`
- Modify: `assets/css/main.css` (delete orphaned §28 + §31 + §36 toolbar/legend/canvas-class rules)

- [ ] **Step 1: garden panel partial**

Replace the entire contents of `layouts/partials/garden/graph-panel.html` with:

```go-html-template
<aside class="graph-panel"
       id="garden-graph-panel"
       role="region"
       aria-label="Garden graph"
       aria-hidden="true"
       inert>
  <header class="graph-panel-header">
    <span class="graph-panel-title">Graph</span>
    <button type="button" class="graph-panel-close" aria-label="Close graph panel">×</button>
  </header>
  <div class="graph-toolbar graph-toolbar--panel" aria-label="Graph filters">
    {{- /* Tag/stage chips populated by garden-graph.js once data is parsed */ -}}
  </div>
  <div class="graph-panel-canvas"></div>
  {{ partial "graph-legend.html" (dict "section" "garden" "variant" "panel") }}
</aside>
```

- [ ] **Step 2: research panel partial**

Replace the entire contents of `layouts/partials/research/graph-panel.html` with:

```go-html-template
<aside id="research-graph-panel" class="graph-panel" aria-hidden="true"
      role="region" aria-label="Research graph">
  <header class="graph-panel-header">
    <span class="graph-panel-title">Research graph</span>
    <button type="button" class="graph-panel-close" aria-label="Close graph panel">×</button>
  </header>
  <div class="graph-toolbar graph-toolbar--panel"></div>
  <div class="graph-panel-canvas"></div>
  {{ partial "graph-legend.html" (dict "section" "research" "variant" "panel") }}
</aside>
```

(Close label normalized to "Close graph panel" to match the others; glyph stays `×`.)

- [ ] **Step 3: works panel partial**

Replace the entire contents of `layouts/partials/works/graph-panel.html` with (SSR chips kept — works' SSR-first toolbar is an intentional difference — but using canonical classes + `aria-pressed`, no `.is-active`, no `.filter-chip`, no `.graph-panel-toolbtn`; legend via the partial; close glyph `✕`→`×`):

```go-html-template
<aside id="works-graph-panel" class="graph-panel" hidden role="region" aria-label="Works constellation">
  <header class="graph-panel-header">
    <h3 class="graph-panel-title">Constellation</h3>
    <button type="button" class="graph-panel-close" aria-controls="works-graph-panel" aria-label="Close graph panel">×</button>
  </header>
  <div class="graph-toolbar graph-toolbar--panel">
    <span class="label">Medium</span>
    <button type="button" class="graph-chip" data-dim="medium" data-key="all" aria-pressed="true">All</button>
    <button type="button" class="graph-chip" data-dim="medium" data-key="game" aria-pressed="false">Games</button>
    <button type="button" class="graph-chip" data-dim="medium" data-key="music" aria-pressed="false">Music</button>
    <button type="button" class="graph-chip" data-dim="medium" data-key="poetry" aria-pressed="false">Poetry</button>
    <span class="graph-toolbar-divider" aria-hidden="true"></span>
    <button type="button" class="graph-action" data-action="reset-view">Reset view</button>
    <button type="button" class="graph-action" data-action="reset-positions">Reset positions</button>
    <span class="graph-hint" aria-hidden="true"><kbd>Shift</kbd>+drag to pin</span>
  </div>
  <svg class="graph-panel-canvas" role="img" aria-label="Force-directed map of works"></svg>
  <div class="graph-panel-resize" aria-hidden="true"></div>
  {{ partial "graph-legend.html" (dict "section" "works" "variant" "panel") }}
</aside>
```

- [ ] **Step 4: garden standalone page**

In `layouts/garden/graph.html`, replace this verbatim block:

```go-html-template
  <nav class="garden-graph-toolbar" aria-label="Graph filters">
    {{- /* populated by garden-graph.js */ -}}
  </nav>

  <a href="#garden-graph-skip" class="graph-skip-link">Skip past graph</a>

  <div class="garden-graph-canvas" role="img" aria-label="Force-directed graph of garden notes">
    {{- /* SVG mounted by garden-graph.js */ -}}
  </div>

  <ul class="garden-graph-legend" hidden></ul>
```

with:

```go-html-template
  <nav class="graph-toolbar graph-toolbar--page" aria-label="Graph filters">
    {{- /* populated by garden-graph.js */ -}}
  </nav>

  <a href="#garden-graph-skip" class="graph-skip-link">Skip past graph</a>

  <div class="garden-graph-canvas" role="img" aria-label="Force-directed graph of garden notes">
    {{- /* SVG mounted by garden-graph.js */ -}}
  </div>

  {{ partial "graph-legend.html" (dict "section" "garden" "variant" "page") }}
```

(`.garden-graph-canvas` class is the JS mount target and stays — it is not a chrome class. Only the toolbar + legend chrome change.)

- [ ] **Step 5: research standalone page**

In `layouts/research/graph.html`, replace this verbatim block:

```go-html-template
  <nav class="research-graph-toolbar" aria-label="Graph filters">
    {{- /* populated by research-graph.js */ -}}
  </nav>
  <a href="#research-graph-skip" class="graph-skip-link">Skip past graph</a>
  <div class="research-graph-canvas" role="img" aria-label="Force-directed graph of research themes and questions">
    {{- /* SVG mounted by research-graph.js */ -}}
  </div>
  <ul class="research-graph-legend" hidden></ul>
```

with:

```go-html-template
  <nav class="graph-toolbar graph-toolbar--page" aria-label="Graph filters">
    {{- /* populated by research-graph.js */ -}}
  </nav>
  <a href="#research-graph-skip" class="graph-skip-link">Skip past graph</a>
  <div class="research-graph-canvas" role="img" aria-label="Force-directed graph of research themes and questions">
    {{- /* SVG mounted by research-graph.js */ -}}
  </div>
  {{ partial "graph-legend.html" (dict "section" "research" "variant" "page") }}
```

- [ ] **Step 6: works standalone page**

In `layouts/works/graph.html`, replace this verbatim block:

```go-html-template
  <div class="graph-page-toolbar">
    <span class="works-graph-summary" id="works-graph-summary"></span>
    <button type="button" class="filter-chip is-active" data-dim="medium" data-key="all">All</button>
    <button type="button" class="filter-chip" data-dim="medium" data-key="game">Games</button>
    <button type="button" class="filter-chip" data-dim="medium" data-key="music">Music</button>
    <button type="button" class="filter-chip" data-dim="medium" data-key="poetry">Poetry</button>
    <button type="button" class="graph-panel-toolbtn" data-action="reset-view">Reset view</button>
    <button type="button" class="graph-panel-toolbtn" data-action="reset-positions">Reset positions</button>
    <span class="graph-hint" aria-hidden="true"><kbd>Shift</kbd>+drag to pin</span>
  </div>

  <a href="#works-graph-skip" class="graph-skip-link">Skip past graph</a>

  <svg class="graph-page-canvas works-graph-canvas" id="works-graph-canvas" role="img" aria-label="Constellation of works"></svg>

  <div class="graph-page-legend">
    <span class="legend-item"><span class="legend-mark legend-mark-solid" aria-hidden="true"></span> tag-share</span>
    <span class="legend-item"><span class="legend-mark legend-mark-dashed" aria-hidden="true"></span> cross-medium ref</span>
  </div>
```

with (canonical classes + `aria-pressed`; legend via partial; `.works-graph-canvas` mount class kept; the summary `<span>` stays as a `.label`):

```go-html-template
  <div class="graph-toolbar graph-toolbar--page">
    <span class="label works-graph-summary" id="works-graph-summary"></span>
    <button type="button" class="graph-chip" data-dim="medium" data-key="all" aria-pressed="true">All</button>
    <button type="button" class="graph-chip" data-dim="medium" data-key="game" aria-pressed="false">Games</button>
    <button type="button" class="graph-chip" data-dim="medium" data-key="music" aria-pressed="false">Music</button>
    <button type="button" class="graph-chip" data-dim="medium" data-key="poetry" aria-pressed="false">Poetry</button>
    <span class="graph-toolbar-divider" aria-hidden="true"></span>
    <button type="button" class="graph-action" data-action="reset-view">Reset view</button>
    <button type="button" class="graph-action" data-action="reset-positions">Reset positions</button>
    <span class="graph-hint" aria-hidden="true"><kbd>Shift</kbd>+drag to pin</span>
  </div>

  <a href="#works-graph-skip" class="graph-skip-link">Skip past graph</a>

  <svg class="graph-page-canvas works-graph-canvas" id="works-graph-canvas" role="img" aria-label="Constellation of works"></svg>

  {{ partial "graph-legend.html" (dict "section" "works" "variant" "page") }}
```

`.works-graph-summary` keeps a tiny rule; check it in Step 7's prune (it currently sets `color`/`margin` — keep it; it is not a drift class). `.graph-page-canvas` is referenced by `works-graph.js` as the mount/cursor target — keep its §36 rule (Step 7 distinguishes mount-class rules from chrome rules).

- [ ] **Step 7: Prune orphaned per-section chrome CSS (§28, §31, §36)**

Now that no markup references them, DELETE these verbatim rule groups:

In §28 (`assets/css/main.css`), delete every rule whose selector starts `.garden-graph-page .garden-graph-toolbar` (the `.garden-graph-toolbar`, its `.label`, `.chip`, `.chip[aria-pressed="true"]`, `.toolbar-divider`, `.chip.chip-action` rules) and the `.garden-graph-page .garden-graph-legend` + `.garden-graph-page .garden-graph-legend .swatch` rules. KEEP `.garden-graph-page .garden-graph-canvas` and the `svg` / cursor (`is-panning`, `is-dragging-node`) rules — those target the JS mount element, not chrome.

In §31, delete the `.research-graph-page .research-graph-toolbar` family (`.research-graph-toolbar`, `.label`, `.chip`, `.chip[aria-pressed="true"]`, `.toolbar-divider`, `.chip.chip-action`) and `.research-graph-page .research-graph-legend`. KEEP `.research-graph-page .research-graph-summary`, `.research-graph-canvas` (+ svg/cursor), and ALL node/edge rules (`.research-graph-node*`, `.research-graph-edge*`).

In §36, delete `.works-graph-page .graph-page-toolbar`, `.graph-page-legend`, `.legend-mark`, `.legend-mark-dashed`. KEEP `.works-graph-node*`, `.works-graph-edge*`, `.works-graph-summary`, `.graph-page-canvas`, `.graph-skip-link` (canvas + skip-link are shared graph scaffolding, not drifted chrome — and `.graph-page-canvas` is the works JS mount target).

After this step, `grep -nE '\.(graph-panel-toolbar|garden-graph-toolbar|research-graph-toolbar|graph-page-toolbar|graph-panel-legend|garden-graph-legend|research-graph-legend|graph-page-legend|graph-panel-toolbtn)\b' assets/css/main.css` must return nothing.

- [ ] **Step 8: Build + run the regression linter (markup half should now pass)**

Run:
```bash
pkill -f 'hugo server' 2>/dev/null; rm -rf public
HUGO_ENVIRONMENT=production hugo --minify >/dev/null 2>&1 && echo "build ok"
python3 tools/check_graph_chrome.py; echo "exit=$?"
```
Expected: `build ok`, then `check_graph_chrome: OK (6 surfaces)` `exit=0`. (JS still references old classes — fixed in Task 6 — but the linter only gates CSS selectors + surface markup, both now clean.)

- [ ] **Step 9: Commit**

```bash
git add layouts/partials/garden/graph-panel.html layouts/partials/research/graph-panel.html layouts/partials/works/graph-panel.html layouts/garden/graph.html layouts/research/graph.html layouts/works/graph.html assets/css/main.css
git commit -m "feat(graph): wire shared legend partial into 6 surfaces; canonical toolbar markup; prune per-section chrome CSS

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Repoint the three graph JS modules to canonical classes

**Files:**
- Modify: `assets/js/garden-graph.js`
- Modify: `assets/js/research-graph.js`
- Modify: `assets/js/works-graph.js`

Behavior is unchanged — only class names and the legend mechanism change. Re-confirm against the documented repo gotchas: keep controls as `<button type="button">` (duplicate-id anchor-race memo) and do not touch `<dialog>`/`inert` close logic.

- [ ] **Step 1: garden-graph.js — chip/action classes**

In `assets/js/garden-graph.js`, find `makeFilterChip` and change `b.className = 'chip';` to `b.className = 'graph-chip';`. Find `makeActionChip` and change `b.className = 'chip chip-action';` to `b.className = 'graph-action';`. In `buildActionChips`, change `divider.className = 'toolbar-divider';` to `divider.className = 'graph-toolbar-divider';`.

- [ ] **Step 2: garden-graph.js — legend now fills the partial's dynamic slot**

Replace the entire `buildLegend` function:

```javascript
function buildLegend(host) {
  host.replaceChildren();
  host.removeAttribute('hidden');
  const tags = new Map();
  (state.data.nodes || []).forEach(n => { if (n.tag) tags.set(n.tag, true); });
  Array.from(tags.keys()).slice(0, 4).forEach(tag => {
    const li = document.createElement('li');
    li.innerHTML = `<span class="swatch" style="background:${tagColor(tag)}"></span>${tag}`;
    host.appendChild(li);
  });
  const note = document.createElement('li');
  note.textContent = 'size = link count · solid = same topic · dashed = cross-topic';
  host.appendChild(note);
}
```

with (fills only the partial's color-key slot; structure key is now server-rendered by `graph-legend.html`, so the note is gone):

```javascript
function buildLegend(root) {
  // The structure key (size / solid / dashed) is server-rendered by
  // partials/graph-legend.html. Garden's tag palette is content-dependent,
  // so we only inject swatches into the partial's dynamic color-key slot,
  // matching its DOM shape (.graph-legend-key > .graph-legend-swatch).
  const slot = root.querySelector('.graph-legend-colorkey[data-graph-legend-dynamic]');
  if (!slot) return;
  slot.replaceChildren();
  const tags = new Map();
  (state.data.nodes || []).forEach(n => { if (n.tag) tags.set(n.tag, true); });
  Array.from(tags.keys()).slice(0, 4).forEach(tag => {
    const key = document.createElement('span');
    key.className = 'graph-legend-key';
    key.innerHTML = `<span class="graph-legend-swatch" style="background:${tagColor(tag)}"></span>${tag}`;
    slot.appendChild(key);
  });
}
```

- [ ] **Step 3: garden-graph.js — repoint the buildLegend call site**

`buildLegend` previously received the `<ul>` legend element. It now needs the legend ROOT (so it can find the `.graph-legend-colorkey` slot inside). Grep the call site:

Run: `grep -n "buildLegend\|graph-panel-legend\|garden-graph-legend\|\.graph-legend" assets/js/garden-graph.js`

At the call site, the selector that used to find `.graph-panel-legend` / `.garden-graph-legend` must now find `.graph-legend` (the partial's `<ul>`, present in both panel and standalone). Change that querySelector to `.graph-legend` and pass the found element to `buildLegend`. If the old code guarded on the element being non-null or toggled its `hidden` attribute, keep the null-guard, drop any `hidden` toggling (the partial's legend is never `hidden`; the structure key must show immediately). Do not change WHEN `buildLegend` is called.

- [ ] **Step 4: research-graph.js — chip/action classes + delete buildLegend**

In `assets/js/research-graph.js`: `makeFilterChip` → `b.className = 'graph-chip';`; `makeActionChip` → `b.className = 'graph-action';`; in `buildActionChips`, `divider.className = 'toolbar-divider';` → `divider.className = 'graph-toolbar-divider';`.

Research's legend is now 100% server-rendered (static theme color key + structure key) by the partial. Delete the entire `buildLegend` function:

```javascript
function buildLegend(host) {
  host.replaceChildren();
  host.removeAttribute('hidden');
  const note = document.createElement('li');
  note.textContent = 'square = theme · circle = question · size = link count · dashed = cross-theme';
  host.appendChild(note);
}
```

Then grep for its call site and remove the call (and any now-unused `.research-graph-legend` / `.graph-panel-legend` querySelector feeding it):

Run: `grep -n "buildLegend\|research-graph-legend\|graph-panel-legend\|\.graph-legend" assets/js/research-graph.js`

Delete the `buildLegend(...)` invocation and the line that resolves the legend element for it. Leave everything else (toolbar build, graph render) intact.

- [ ] **Step 5: works-graph.js — canonical selectors + aria-pressed only**

In `assets/js/works-graph.js`, replace the `wireToolbar` function:

```javascript
function wireToolbar(toolbar) {
  if (!toolbar) return;
  if (toolbar.dataset.wired === 'true') return;
  toolbar.dataset.wired = 'true';

  toolbar.querySelectorAll('button[data-dim="medium"][data-key]').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-key') || 'all';
      state.filters.medium = key;
      toolbar.querySelectorAll('button[data-dim="medium"]').forEach(b => {
        const isActive = b.getAttribute('data-key') === key;
        b.classList.toggle('is-active', isActive);
        b.setAttribute('aria-pressed', isActive ? 'true' : 'false');
      });
      rebuildGraph();
    });
    // Seed aria-pressed from the SSR is-active class.
    btn.setAttribute('aria-pressed', btn.classList.contains('is-active') ? 'true' : 'false');
  });

  const resetViewBtn = toolbar.querySelector('button[data-action="reset-view"]');
  if (resetViewBtn) resetViewBtn.addEventListener('click', resetView);
  const resetPosBtn = toolbar.querySelector('button[data-action="reset-positions"]');
  if (resetPosBtn) resetPosBtn.addEventListener('click', resetPositions);
}
```

with (active state is `aria-pressed` ONLY — `.is-active` is gone; SSR markup now seeds `aria-pressed` directly):

```javascript
function wireToolbar(toolbar) {
  if (!toolbar) return;
  if (toolbar.dataset.wired === 'true') return;
  toolbar.dataset.wired = 'true';

  toolbar.querySelectorAll('button[data-dim="medium"][data-key]').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-key') || 'all';
      state.filters.medium = key;
      toolbar.querySelectorAll('button[data-dim="medium"]').forEach(b => {
        b.setAttribute('aria-pressed', b.getAttribute('data-key') === key ? 'true' : 'false');
      });
      rebuildGraph();
    });
  });

  const resetViewBtn = toolbar.querySelector('button[data-action="reset-view"]');
  if (resetViewBtn) resetViewBtn.addEventListener('click', resetView);
  const resetPosBtn = toolbar.querySelector('button[data-action="reset-positions"]');
  if (resetPosBtn) resetPosBtn.addEventListener('click', resetPositions);
}
```

Then grep works-graph.js for any other `is-active`, `filter-chip`, `graph-panel-toolbtn`, `graph-page-toolbar`, `graph-panel-toolbar`, `graph-page-legend`, or `graph-panel-legend` references:

Run: `grep -nE "is-active|filter-chip|graph-panel-toolbtn|graph-(page|panel)-(toolbar|legend)" assets/js/works-graph.js`

Expected after the edit: no functional matches (only the toolbar wiring above, now clean). If the toolbar is located by a `.graph-panel-toolbar` / `.graph-page-toolbar` selector elsewhere, repoint it to `.graph-toolbar`. Works has no `buildLegend` (legend is server-rendered) — confirm none is referenced.

- [ ] **Step 6: Build + full local CI**

Run:
```bash
pkill -f 'hugo server' 2>/dev/null
tools/ci-local.sh
```
Expected: every linter (incl. `check_graph_chrome: OK (6 surfaces)`), the production build, page-weight gate, smoke, and LHCI desktop+mobile all pass. JS bundles rebuild via `js.Build`; net JS should be flat-to-slightly-smaller (research drops `buildLegend`). If LHCI mobile perf wobbles ±5–8 pts (known CPU sensitivity locally), re-run once; only a real gate failure blocks.

- [ ] **Step 7: Commit**

```bash
git add assets/js/garden-graph.js assets/js/research-graph.js assets/js/works-graph.js
git commit -m "feat(graph): repoint graph JS to canonical control classes; legend via shared partial

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Verification matrix + finish

**Files:** none (verification + branch finish)

- [ ] **Step 1: Static guard re-confirm**

Run: `python3 tools/check_graph_chrome.py && grep -rnE "class=\"[^\"]*\b(chip|filter-chip|toolbar-divider|legend-mark|swatch)\b" layouts/ assets/js/ | grep -i graph`
Expected: linter OK; the grep returns no graph-context hits using the OLD names (only the new `graph-chip`/`graph-action`/`graph-legend-*`/`graph-toolbar-divider` should exist — and those won't match the old-name pattern).

- [ ] **Step 2: Manual eyeball pass (dev server)**

Run `hugo server --buildDrafts`. At BOTH full width AND ~960px (half-screen tiling), in BOTH light and dark:

Launcher `⊞ Graph` identical on all 4 host pages:
- [ ] `/garden/` (index)
- [ ] a `/garden/<note>/` page (path-log launcher)
- [ ] `/research/`
- [ ] `/works/` (sits right-aligned after the Sort select; quiet grey-outline; burgundy fill when panel open)

Legend complete (color key + structure key) on all 6 surfaces:
- [ ] garden panel, garden `/garden/graph/`
- [ ] research panel, research `/research/graph/` (now has a theme color key — previously text-only)
- [ ] works panel, works `/works/graph/`

Controls identical (chip shape/active burgundy-fill via `aria-pressed`, dashed-italic `.graph-action`, divider, hint) in panel vs standalone for all three sections. Open/close each panel; toggle filters; Reset view / Reset positions still work; keyboard: chips reachable, `aria-pressed` flips. Graph rendering (nodes/edges/colors/physics/filter dimensions) visibly UNCHANGED — this is the out-of-scope regression guard.

- [ ] **Step 3: Provide the user the eyeball checklist + spot-check**

Per repo convention, before merge: present the user the dev-server URL and the Step 2 checklist; get explicit go-ahead to merge (do not self-merge).

- [ ] **Step 4: Finish the branch**

On user approval, use `superpowers:finishing-a-development-branch` to merge `feature/graph-chrome-consistency` → `master` and push. Update memory with a `project_graph_view_chrome_consistency_slice.md` entry + MEMORY.md pointer; in `CLAUDE.md`, move graph-view-consistency out of the "Designed but not yet implemented" queue table and update the project-status date. Confirm `tools/ci-local.sh` is green on the merge commit before push.

---

## Self-Review

**Spec coverage:** launcher option B → Task 3 Step 3 + Task 4. Chip option A (burgundy-fill, `aria-pressed`, no `.is-active`) → Task 3 Step 3 + Task 6. Action buttons distinct + divider kept → Task 3 Step 3 (`.graph-action`, `.graph-toolbar-divider`). Close glyph `×` → Task 5 Steps 2–3 (`✕`→`×`). Shared legend partial across 6 surfaces, garden-dynamic vs research/works-static slot → Task 2 + Task 5 + Task 6 Steps 2–4. Canonical CSS consolidated into §27, per-section §28/§31/§36 chrome pruned → Tasks 3 + 5 Step 7. Linter (sibling-less) + CI + CLAUDE.md → Task 1. Spec open item (toolbar container modifier) → resolved: `.graph-toolbar` base + `--panel`/`--page` modifiers (Task 3 Step 3). Verification at full + 960px, light+dark, graphs-unchanged guard, eyeball-before-merge → Task 7. No spec requirement is unmapped.

**Placeholder scan:** No "TBD/TODO/handle appropriately". The three grep-then-edit steps (Task 6 Steps 3/4/5 call sites) give the exact grep, the exact new code, and the exact mechanical transform — they are precise instructions for a known-shape edit, not placeholders, because the legend/toolbar call-site selector text is the one thing not capturable verbatim ahead of execution.

**Type/name consistency:** Canonical class set is defined once in the vocabulary table and used identically in every task: `.graph-toggle`, `.graph-toolbar`(+`--panel`/`--page`), `.graph-chip`, `.graph-action`, `.graph-toolbar-divider`, `.graph-legend`(+`--panel`/`--page`), `.graph-legend-colorkey`/`-key`/`-swatch`/`-mark`(+`--dashed`). JS `className` strings in Task 6 match the CSS selectors in Tasks 2–3. Partial param names (`section`, `variant`, `data-graph-legend-dynamic`, `.graph-legend-colorkey`) match between Task 2 (partial) and Task 6 Steps 2–3 (garden JS slot fill). The linter's `FORBIDDEN_CSS`/`FORBIDDEN_MARKUP` lists (Task 1) match exactly the selectors deleted in Tasks 3 + 5.

No issues found.
