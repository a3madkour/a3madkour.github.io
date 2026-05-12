# Research surface — Slice 2: force-directed graph

**Date:** 2026-05-11
**Status:** Design
**Slice of:** Phase 5 (Research surface)
**Predecessor:** `2026-05-11-research-surface-design.md` (Slice 1, merged 2026-05-11 in `0ac950c`)
**Parent spec reference:** `2026-05-03-personal-site-design.md` §4.10 (Research index)

## 1. Goal

Add the force-directed research graph + "⊞ Graph" toggle that Slice 1 deferred. The toggle lives on `/research/`; a standalone `/research/graph/` page mirrors `/garden/graph/` for mobile. No graph runtime appears on theme or question pages in this slice.

## 2. What's in scope

1. Build-time data partial that emits `{themes, questions, edges, themePaletteOrder}` as JSON, mirroring `partials/garden/graph-data.html`.
2. New JS module `assets/js/research-graph.js` (copy + trim of `garden-graph.js`).
3. New entry `assets/js/entry-research.js` and a third `js.Build` call in `partials/scripts.html` (page-narrow load — only on `/research/` index and `/research/graph/`).
4. Standalone page at `/research/graph/`.
5. Panel scaffolding partial + toggle button on `/research/`.
6. CSS hoist refactor: rename `.garden-graph-*` → `.graph-*` for the shared scaffolding (toggle + panel + toolbar + canvas + legend); new §31 "Research graph" for research-specific overrides (theme palette fills, shape distinction).
7. Linter extension: unique-`weight` assertion on themes (one extra check, no new gate).

## 3. What's explicitly out of scope

| Item | Why deferred |
|---|---|
| Local-graph mode on theme/question pages | Per-page subgraphs add layout + JS surface area without clear payoff at current fixture density. The `1-hop / 2-hop / all` toolbar buttons we just trimmed from garden-graph would have to come back. |
| `related_questions` frontmatter field | Derivation from shared `supporting_notes` covers the cross-theme case with current fixtures; explicit field is premature. |
| Cross-theme edges from shared `related_essays` | One signal (`supporting_notes`) is enough to demonstrate the dashed-edge variant. |
| Edge tooltips (`via:<garden-slug>`) | Data partial emits the `via:` field; rendering it as an SVG `<title>` is left to a later polish slice. |
| Node hover preview card | Garden doesn't have one either; design for both surfaces simultaneously later. |
| Output nodes in the graph | Parent spec §4.10 fixes nodes = themes + questions. |
| New fixture seeding | Slice 1 fixtures already exercise every variant (see §7). |

## 4. Decisions taken in brainstorming

| # | Decision | Alternative considered | Why this |
|---|---|---|---|
| D1 | Cross-theme edges derived from shared `supporting_notes`. No `related_questions` field. | New `related_questions` field; or both derived AND explicit | Cheap, emergent, no frontmatter contract change. Current fixtures produce one cross-theme edge naturally (`story-atoms`). |
| D2 | Filter dims in the panel: `tag` (multi-AND) + `status` (single-select). | Tag only; tag + status + theme; tag + node-kind | Mirrors garden's `tag + stage` AND-composition model; reuses `filter-chips.js`. Theme already visually clusters via parent-child edges. Status applies to questions only. |
| D3 | Pure copy + trim of `garden-graph.js`. | Extract shared `graph-core.js`; small targeted utilities | YAGNI — only two callers. Wait for a third graph before extracting. |
| D4 | Node color from theme palette (deterministic by `theme.weight`). | Tag-driven (first tag); shape-only no color | No tag→color registry needed. Visual cluster matches parent-child structure; reuses three existing accent tokens (`--color-burgundy`, `--color-steel`, `--color-green`). |
| D5 | Graph surface scope: `/research/` only + `/research/graph/` mobile fallback. | Add local mode on theme pages; add on theme + question pages | Mirrors what garden ended up with. Fixture density (3 themes, 6 questions) doesn't justify per-page subgraphs. |
| D6 | CSS hoist: rename `.garden-graph-*` → `.graph-*` for shared scaffolding. | Duplicate as `.research-graph-*`; partial hoist (scaffolding only) | One source of truth. Small refactor on a known-good module; offset by the dev-server regression check. |

## 5. Architecture

### 5.1 Data partial — `layouts/partials/research/graph-data.html`

Run once per build via `partialCached`. Walks both research types and emits a single JSON blob:

```json
{
  "themes": [
    {"slug": "memory-and-play", "title": "Memory and play",
     "status": "active", "tags": ["memory", "play"], "weight": 10}
  ],
  "questions": [
    {"slug": "how-do-readers-form-narrative-from-shuffle",
     "title": "How do readers form narrative from shuffle?",
     "theme": "memory-and-play", "status": "active",
     "tags": ["memory", "narrative"], "degree": 4}
  ],
  "edges": [
    {"source": "memory-and-play",
     "target": "how-do-readers-form-narrative-from-shuffle",
     "kind": "parent-child"},
    {"source": "how-do-readers-form-narrative-from-shuffle",
     "target": "what-counts-as-story-recall",
     "kind": "parent-child"},
    {"source": "how-do-readers-form-narrative-from-shuffle",
     "target": "what-is-a-narrative-atom",
     "kind": "cross-theme", "via": "story-atoms"}
  ],
  "themePaletteOrder": ["memory-and-play", "procedural-narrative", "save-game-as-form"]
}
```

**Edge rules:**

- **parent-child (solid)**: theme → its-questions (matched by question's `Params.theme`); question → sub-question (matched by sub's `Params.parent_question`).
- **cross-theme (dashed)**: build a `supportingIndex` map (`garden-slug → [question-slug…]`) by scanning every question's `supporting_notes`. For each garden slug with ≥2 question references, emit one edge per cross-theme pair (skip same-theme pairs — those questions already cluster via their shared theme node). Annotate with `via:<garden-slug>`. Deduplicate edges between the same pair (keep first `via`).

**Degree:** computed inside the partial so the client doesn't recompute on every render. Drives node radius (clamped 4–12px for circles; 6×6–14×14 for rects).

**`themePaletteOrder`:** themes sorted by `weight` ascending, then by slug for ties. Client uses array index as `data-theme-color` attribute (0/1/2). Questions inherit their theme's index.

### 5.2 Script partial — `layouts/partials/research/graph-script.html`

Wraps the JSON in `<script type="application/json" id="research-graph-data">…</script>` via `safeJS`. Mirrors `partials/garden/graph-script.html` exactly.

### 5.3 Panel partial — `layouts/partials/research/graph-panel.html`

Side-panel scaffolding for the toggle on `/research/`. Empty containers populated by `research-graph.js`:

```html
<aside id="research-graph-panel" class="graph-panel" hidden aria-hidden="true">
  <header class="graph-panel-header">
    <h2>Research graph</h2>
    <button type="button" class="graph-panel-close" aria-label="Close graph">×</button>
  </header>
  <div class="graph-panel-toolbar"></div>
  <div class="graph-panel-canvas"></div>
  <div class="graph-panel-legend"></div>
  <div class="graph-panel-resize" aria-hidden="true"></div>
</aside>
```

Mirrors `partials/garden/graph-panel.html`. After the §27 hoist, both partials produce identical class names; only the `id` differs (`garden-graph-panel` vs `research-graph-panel`).

### 5.4 Standalone page — `layouts/research/graph.html`

Minimal full-viewport layout. Renders a `<main class="research-graph-page graph-panel-canvas">` plus the data + script partials. No header, no toolbar — the page IS the canvas. Backed by a tiny `content/research/graph.md` with frontmatter:

```yaml
---
title: "Research graph"
layout: graph
build:
  list: never
---
```

`build.list: never` excludes it from `where "Type" "research-question"` queries and from the `/research/` index render.

### 5.5 Index edits — `layouts/research/list.html`

Three additions, all in the existing template:

1. Append the toggle button after the `filter-chips.html` partial call (line 24):
   ```html
   <button type="button" class="graph-toggle" aria-expanded="false"
           aria-controls="research-graph-panel">⊞ Graph</button>
   ```
2. After the `.research-grid`, mount the panel:
   ```go
   {{ partial "research/graph-panel.html" . }}
   ```
3. At the end of `main`, mount the data script:
   ```go
   {{ partial "research/graph-script.html" .Site }}
   ```

### 5.6 JS module — `assets/js/research-graph.js`

Starts as a copy of `garden-graph.js`. Trim:

- Remove the `garden:stack-changed` event listener and in-stack stroke logic (no stack on research).
- Remove the local-graph N-hop mode toggle and its `1-hop / 2-hop / all` toolbar buttons.

Keep verbatim:

- d3 dynamic imports on first toggle (`d3-force`, `d3-zoom`, `d3-drag`, `d3-selection` from `assets/js/vendor/`).
- Drag-to-reposition with stay-put release.
- Wheel zoom (0.3×–4× toward cursor), drag-pan on empty SVG.
- `[Reset view]` and `[Reset positions]` toolbar buttons.
- `sim.on('tick', renderTick)` so user-driven reheats animate.
- Reduced-motion: simulate 300 ticks then freeze.
- Filter chip strip inside the panel (adapt from `[tag, stage]` → `[tag, status]`).
- Position + view persistence cache in `localStorage` keyed by filter combination. Same `{nodes, view}` shape; cache key prefixed `research-graph-positions:` to avoid collision with garden's.
- Click node → navigate to `/research/themes/<slug>/` or `/research/questions/<slug>/` (kind determines URL).

New / adapted:

- **Shape:** themes render as `<rect>` (8×8 default, scaled by degree); questions as `<circle>` (r=5 default, scaled by degree).
- **Fill color:** read from JSON `themePaletteOrder` index → written to node element as `data-theme-color="0|1|2"`; CSS rules in §31 map that to `--color-burgundy / --color-steel / --color-green`. Questions inherit their theme's index.
- **Edges:** `kind === "parent-child"` → default stroke; `kind === "cross-theme"` → adds class `.graph-edge-cross-theme` (CSS applies `stroke-dasharray: 4 3; opacity: 0.6`).
- **Status filter:** chip dimension affects questions only (themes ignored).
- **Mount selectors:** `.research-graph-page` (standalone) or `#research-graph-panel` (toggle). Detect on init; toggle binds `click` to mount.
- **Mobile behavior:** on viewports ≤720px, the toggle's `click` handler navigates to `/research/graph/` instead of mounting the panel. Same pattern as garden.

### 5.7 Entry + bundling

New entry file `assets/js/entry-research.js`:

```js
import './research-graph.js';
```

Edit `layouts/partials/scripts.html` to add a third `js.Build` call. Page-narrow load (not section-wide):

```go
{{- $loadResearch := or
     (and (eq .Section "research") (eq .Kind "section"))
     (and (eq .Section "research") (eq .Layout "graph")) -}}
{{- if $loadResearch -}}
  {{- $researchEntry := resources.Get "js/entry-research.js" -}}
  {{- $research := $researchEntry | js.Build $opts -}}
  {{- if hugo.IsProduction -}}
    {{- $research = $research | minify | fingerprint -}}
    <script src="{{ $research.RelPermalink }}" integrity="{{ $research.Data.Integrity }}"></script>
  {{- else -}}
    <script src="{{ $research.RelPermalink }}"></script>
  {{- end -}}
{{- end -}}
```

Theme and question pages stay on the core bundle only — they never get the ~95 KB d3 payload.

### 5.8 CSS

**Part 1 — §27 hoist refactor:**

Rename in `assets/css/main.css` §27:

| Old | New |
|---|---|
| `.garden-graph-toggle` | `.graph-toggle` |
| `.garden-graph-panel` | `.graph-panel` |
| `.garden-graph-panel-header` | `.graph-panel-header` |
| `.garden-graph-panel-toolbar` | `.graph-panel-toolbar` |
| `.garden-graph-panel-canvas` | `.graph-panel-canvas` |
| `.garden-graph-panel-close` | `.graph-panel-close` |
| `.garden-graph-panel-resize` | `.graph-panel-resize` |
| `.garden-graph-panel-legend` | `.graph-panel-legend` |

Plus their state variants (`[aria-expanded="true"]`, `.is-animating`, `.is-panning`, `.is-resizing`). Rename the section header from "Garden graph panel" to "Graph (shared)".

**Touched in lockstep:** `layouts/partials/garden/graph-panel.html`, `layouts/garden/list.html` (toggle button class), `assets/js/garden-graph.js` (`querySelector` strings).

**Part 2 — new §31 "Research graph"** (~80 lines):

```css
/* 31. Research graph
   ───────────────────────────────────────────────────────── */

/* Theme palette → fill color, deterministic by themePaletteOrder index. */
.graph-node[data-theme-color="0"] { fill: var(--color-burgundy); }
.graph-node[data-theme-color="1"] { fill: var(--color-steel); }
.graph-node[data-theme-color="2"] { fill: var(--color-green); }

/* Shape distinction. */
.graph-node-theme {
  stroke: var(--color-ink);
  stroke-width: 1.5;
}
.graph-node-question {
  /* fill-only, no stroke */
}
.graph-node:hover { opacity: 0.85; }
.graph-node:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 2px;
}

/* Edges. */
.graph-edge {
  stroke: var(--color-ink-soft);
  stroke-width: 1;
}
.graph-edge-cross-theme {
  stroke-dasharray: 4 3;
  opacity: 0.6;
}

```

The standalone `/research/graph/` page uses regular page flow (no viewport-filling wrapper) — mirrors `.garden-graph-page` which has no bare rule of its own. The canvas inside inherits sizing from `.graph-panel-canvas` after the §27 hoist.

No new CSS custom properties. `tools/check-contrast.py` is unchanged — the four documented WCAG pairings still apply.

### 5.9 Linter extension

`tools/check_research_fixtures.py` gains one assertion: theme weights must be unique across themes (so `themePaletteOrder` is deterministic).

```python
def validate_unique_theme_weights(themes):
    seen = {}
    errors = []
    for theme in themes:
        w = theme.get('weight')
        if w is None:
            continue  # weight already required elsewhere
        if w in seen:
            errors.append(f"theme weight {w} duplicated: {seen[w]} and {theme['slug']}")
        seen[w] = theme['slug']
    return errors
```

Plus a matching test in `tools/test_check_research_fixtures.py`. No new linter script, no new CI step.

`tools/check_research_links.py` is unchanged — `parent_question` and `supporting_notes` (the fields feeding graph edges) are already validated.

## 6. Files touched

**New:**

- `layouts/partials/research/graph-data.html`
- `layouts/partials/research/graph-script.html`
- `layouts/partials/research/graph-panel.html`
- `layouts/research/graph.html`
- `content/research/graph.md`
- `assets/js/research-graph.js`
- `assets/js/entry-research.js`

**Edited:**

- `layouts/research/list.html` (toggle button + panel mount + script mount)
- `layouts/partials/scripts.html` (third `js.Build` call)
- `assets/css/main.css` (§27 hoist + new §31)
- `layouts/partials/garden/graph-panel.html` (class renames)
- `layouts/garden/list.html` (toggle button class rename)
- `assets/js/garden-graph.js` (`querySelector` string updates)
- `tools/check_research_fixtures.py` (unique-weight assertion)
- `tools/test_check_research_fixtures.py` (one new test)
- `CLAUDE.md` (§"CSS pipeline" §27 rename + §31 mention; §"Layouts"/§"Partials" additions; §"Project status" Slice 2 entry)

**Not touched:**

- `content/research/themes/*` and `content/research/questions/*` — no fixture changes.
- `layouts/research-theme/single.html`, `layouts/research-question/single.html` — no graph there.
- `data/citations.yaml`, `data/filter-chips.yaml` — no graph filter taxonomy needs curation.

## 7. Fixture coverage

The Slice 1 fixture set exercises every graph variant without modification:

| Variant | Where it surfaces in the 6-question set |
|---|---|
| Theme node, palette index 0 (burgundy) | `memory-and-play` (weight 10) |
| Theme node, palette index 1 (steel) | `procedural-narrative` (weight 20) |
| Theme node, palette index 2 (green) | `save-game-as-form` (weight 30) |
| Theme with no garden topic | `save-game-as-form` (no `garden_topic_ref:`) |
| Question with `parent_question` (sub-question edge) | `what-counts-as-story-recall` → `how-do-readers-form-narrative-from-shuffle` |
| Cross-theme edge (derived) | `story-atoms` cited by `how-do-readers-form-narrative-from-shuffle` and `what-is-a-narrative-atom` (different themes) |
| All three statuses | active (3), dormant (2), answered (1) |
| Multi-AND tag filter | memory, play, narrative, procedural, aesthetics, games |

Graph totals: 9 nodes (3 themes + 6 questions), 7 parent-child edges (6 theme→question + 1 sub-question), 1 cross-theme edge.

## 8. Build + verification

CI gates (unchanged inventory, 13 total):

1. WCAG contrast check.
2. Essay fixtures + unit tests.
3. Garden fixtures + unit tests.
4. Garden links + unit tests.
5. Filter-chips config + unit tests.
6. Research fixtures + unit tests (now includes unique-weight assertion).
7. Research links + unit tests.

**Dev-server spot-check** (final pre-merge):

- `/research/` index renders ⊞ Graph button next to filter chips.
- Click toggle → panel slides in from right, canvas mounts, 9 nodes appear.
- Theme nodes are squares (3 of them, one per accent color); question nodes are circles, fill matches their theme.
- One dashed edge between the two questions sharing `story-atoms`.
- Drag a node → it stays put on release. Click [Reset positions] → drift back.
- Wheel-zoom + drag-pan work.
- Tag chip filter: clicking `memory` dims nodes without that tag.
- Status chip filter (questions only): clicking `dormant` dims active/answered questions; theme nodes unchanged.
- Reload page → toggle is collapsed (panel state isn't persisted, only positions are).
- Open `/research/graph/` directly → full-page graph renders, no panel chrome.
- Resize browser ≤720px on `/research/` → toggle navigates to `/research/graph/` (not panel).
- Garden side: panel + toggle still work on `/garden/` and `/garden/<note>/` after the class rename. Regression check.

## 9. Slice closure criteria

1. All 13 CI gates pass.
2. The new `tools/test_check_research_fixtures.py` unique-weight test passes.
3. Hugo build produces `/research/` with the toggle, `/research/graph/` standalone, and the new `js/research.<hash>.js` bundle.
4. Dev-server checklist (§8) passes.
5. Garden surfaces still work after the §27 hoist (regression check).
6. Bundle sizes recorded in CLAUDE.md alongside essay/garden bundles.
