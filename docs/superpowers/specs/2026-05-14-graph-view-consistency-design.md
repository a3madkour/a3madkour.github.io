# Graph-view chrome consistency

**Status:** Designed — brainstormed 2026-05-16, ready for plan.
**Stub filed:** 2026-05-14 (during the citation-export slice). **Brainstorm:** 2026-05-16.

## Motivation

The three sections with force-directed d3 graphs — garden, research, works — were
each implemented in its own slice (research's graph JS was a copy+trim of garden's;
works' a copy+trim of research's). The user's complaint, restated precisely during
the brainstorm:

1. **Primary:** the *launcher* button — the control that opens / shows the graph
   view — looks different depending on the page.
2. **Secondary:** the controls *inside* the view (filter chips, action buttons,
   close) also look different per section.
3. **Tertiary:** legends are uneven — research's is a one-line text string; some
   standalone-page legends are thinner than their panel counterpart.

The graphs **themselves are fine** and intentionally differ (garden colors nodes by
tag, research by theme-weight + square/circle type encoding, works by medium with
glyph badges; filter dimensions differ by domain). This slice does **not** touch
graph rendering.

## Scope

**In scope**

- The graph launcher button (`.graph-toggle`).
- In-view controls: filter chips, action buttons ("Reset view" / "Reset positions"),
  panel close button.
- Legend completeness on all 6 graph surfaces.

**Out of scope**

- Graph rendering: node shapes/colors, edge rendering, color palette, d3-force
  physics, and filter *dimensions* (garden N-hop/stack, research status, works
  medium) all stay exactly as-is.
- `graph-core.js` extraction / any JS-architecture consolidation (explicitly ruled
  out by the user — the ~80% JS duplication is left alone).
- The section `graph-data.html` partials and the JSON they emit.
- Legend *visual language* redesign — only presence + completeness + shared markup.

## Decisions made during the brainstorm

| Decision | Choice | Rationale |
|---|---|---|
| Effort tier | Visual / chrome only | Preserves all semantic node/color encoding; lowest risk; no bundle regression. |
| Launcher look | **B — quiet grey-outline ghost** | Inter UI font (fixes the serif `font:inherit` bug), grey-rule outline, transparent bg, burgundy fill on open. Launcher shouldn't compete with page content until hovered/opened. |
| Launcher label | `⊞ Graph` everywhere | Works' umbrella currently says "⊞ Graph view"; unify. |
| Filter-chip active state | **A — burgundy fill** | Today's garden/research look, made canonical; least change to the two graphs that already read right. |
| Action buttons | Dashed ghost-pills, distinct from chips | Toggles vs actions should read differently. |
| Toolbar divider | Kept | Between filter chips and action buttons (garden/research convention). |
| Active-state hook | `aria-pressed="true"` only | Kill works' `.is-active` chip variant. |
| Close glyph | `×` everywhere | Works' `✕` → `×`. |
| Legend scope | Complete legend on **all 6 surfaces** | garden/research/works × {in-page panel, standalone `/x/graph/`}. Research's text line and the thin standalone legends become full color-key + structure-key legends. |
| Implementation approach | **Approach 2** — shared legend partial + canonical control CSS | Fixes the drift *structurally* (one source of truth) so it can't recur, while staying chrome-only. |

## Architecture

### Canonical control CSS (one source of truth in §27)

All graph-control styling consolidates into CSS §27 ("Graph (shared)"). Per-section
graph-*control* rule blocks in §31 (research) and §36 (works) are pruned; only
genuinely section-specific *graph-rendering* CSS remains in those sections.

- **`.graph-toggle`** — single rule. `--font-ui`, grey-rule (`--color-rule`)
  outline, transparent background, `--color-ink-soft` text; hover →
  stone bg / ink text; `aria-expanded="true"` → burgundy fill / tile text.
  **Delete** `.works-umbrella-toolbar .graph-toggle` + its
  `[aria-expanded="true"]` partner (current CSS ~2304–2318) and the base rule's
  serif `font: inherit`.
- **`.graph-chip`** — filter chip. One radius / font-size / gap / padding;
  `aria-pressed="true"` → burgundy fill / tile text. Replaces the per-section
  chip classes and works' `.is-active` model.
- **`.graph-action`** — action button ("Reset view" / "Reset positions"):
  dashed ghost-pill, transparent, visually distinct from `.graph-chip`.
- **`.graph-panel-close`** — single `×` glyph; one rule.
- Toolbar layout container: one class (e.g. `.graph-toolbar`) used by both the
  panel and the standalone page, replacing `.garden-graph-toolbar` /
  `.research-graph-toolbar` / `.graph-page-toolbar`. Divider element kept between
  the filter group and the action group.

**Class-rename discipline:** the plan stage MUST grep the entire repo for every
existing graph-control class (`graph-toggle`, `*-graph-toolbar`,
`graph-page-toolbar`, `graph-panel-toolbtn`, chip `.is-active`,
`graph-panel-close`, `graph-*-legend`, `graph-page-legend`) before any rename —
the obvious file list reliably misses a usage.

### Shared legend partial

New `layouts/partials/graph-legend.html`, included by all **6 surfaces**:

- garden panel — `layouts/partials/garden/graph-panel.html`
- garden standalone — `layouts/garden/graph.html`
- research panel — `layouts/partials/research/graph-panel.html`
- research standalone — `layouts/research/graph.html`
- works panel — `layouts/partials/works/graph-panel.html`
- works standalone — `layouts/works/graph.html`

It renders an identical skeleton:

- **Structure key** — byte-identical across all six surfaces: a "size = connections"
  swatch pair, a solid-link mark, a dashed-link mark. The *labels* for the
  solid/dashed marks are passed in per section (garden: same-topic / cross-topic;
  research: theme→question / cross-theme; works: tag-share / cross-medium). Always
  server-rendered.
- **Color key** — a `data-graph-legend-colorkey` slot:
  - Research (themes) and works (mediums): color set is known at build time →
    rendered server-side from data passed into the partial.
  - **Garden's tag palette is dynamic** (varies with content; top-N tags) →
    `garden-graph.js` injects swatches into that same slot using the same DOM
    shape + `.graph-legend-swatch` classes. Garden keeps its dynamic behavior; the
    *markup, classes, and structure-key are still the single shared source.*

Legend CSS lives in §27 alongside the controls.

### JS touch points (chrome only — no behavior change)

- `garden-graph.js` — stop building the legend `<ul>`; instead populate the shared
  partial's color-key slot with the dynamic tag swatches (same DOM shape/classes
  as before). Update control selectors to the canonical class names.
- `research-graph.js` — stop building the legend (now fully static via the
  partial). Update control selectors.
- `works-graph.js` + works panel/standalone markup — drop the hardcoded `<div>`
  legend; rely on the partial. Update control selectors / wire-up.
- Filter-chip / action-button JS in all three — selector + class updates only
  (`.graph-chip`, `.graph-action`, `aria-pressed`). No behavior change. Re-verify
  against the documented repo gotchas: `<dialog>.close()` inert-state, duplicate-id
  anchor race (graph controls are already `<button type="button">` — keep them so).

## Linter / regression gate

A thin guard so the drift can't recur. Fail the build if either:

1. Any pruned per-section graph-control selector reappears in `assets/css/main.css`
   (`.works-umbrella-toolbar .graph-toggle`, `.garden-graph-toolbar`,
   `.research-graph-toolbar`, `.graph-page-toolbar`, graph-chip `.is-active`), or
2. Any of the 6 surfaces fails to include `partials/graph-legend.html`.

**Pairing decision (finalize in plan):** lean sibling-less, smoke-style (precedent:
`tools/check_smoke.py` — logic too thin to warrant a paired unit test). If the
check grows real branching, add the paired test instead. CI step count + the
top-of-CLAUDE.md linter inventory update accordingly.

## Verification

- `tools/ci-local.sh` (mirrors CI step-for-step, includes LHCI desktop+mobile)
  must pass before push. Run with **no dev server alive** (production build poisons
  the dev-server CSS via MIME mismatch).
- Manual eyeball pass, light + dark, at **full width and ~960px** (half-screen
  tiling WM):
  - `⊞ Graph` launcher identical on all 4 host pages: garden index, a garden
    note page, research index, works umbrella.
  - All 6 legend surfaces render a complete color-key + structure-key legend.
  - Filter chips / action buttons / close button identical in panel vs standalone,
    all three sections.
  - Graph rendering unchanged (nodes, edges, colors, physics, filters) — this is
    the regression guard for "out of scope" staying out of scope.
- Provide the user the eyeball checklist + dev-server spot-check before merge.

## Risks

- **Garden legend dynamism:** the partial must not force garden's tag color-key
  static (loses info) nor force research/works into JS. The `data-graph-legend-colorkey`
  slot pattern addresses this — verify garden's injected swatches match the shared
  DOM/CSS exactly.
- **Selector renames touching JS:** chip/action/close selectors are referenced in
  the three graph JS files; a missed reference silently breaks a control. Mitigated
  by the mandatory full-repo grep at plan stage + the manual matrix.
- **Bundle weight:** chrome-only edits; no new vendored code. Net JS should be
  flat-to-slightly-down (garden/research stop building legend DOM). Confirm against
  the existing page-weight gate.

## Open items for the plan

- Exact canonical token values for `.graph-toggle` / `.graph-chip` / `.graph-action`
  (padding, font-size, gap, radius) — pick from the existing values, documented in
  the plan.
- Final linter form (sibling-less smoke vs paired) and its CI wiring.
- Whether the shared toolbar container also needs a per-context (panel vs
  standalone) modifier class, or one class with context-neutral rules suffices.

## Process

Plan via `superpowers:writing-plans` once this spec is approved. No code before the
plan. TOC collapsible-subsections is the next queued stub after this slice ships.
