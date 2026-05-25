---
name: project-graph-view-chrome-consistency-slice
description: Graph-view chrome-consistency slice — shipped + pushed 2026-05-16 (merge e6edadc)
metadata: 
  node_type: memory
  type: project
  originSessionId: a7a980ab-0626-4eae-ab5f-45cfb26e61b9
---

Graph-view chrome-consistency slice merged to master 2026-05-16, merge `e6edadc`,
pushed (`1fe4240..c56077e`). Closes the queued graph-view-consistency stub.

**Scope (deliberately narrowed during brainstorm):** chrome only — the graph
*launcher* button, the in-view controls (filter chips / action buttons / close),
and *legend completeness* — made identical across garden/research/works AND across
the in-page panel vs the standalone `/x/graph/` page. The graphs themselves
(nodes/edges/colors/physics/filter dimensions) were explicitly **out of scope and
untouched**. No `graph-core.js` extraction (user ruled it out).

**Canonical vocabulary (the ONLY graph-control class names now; all CSS in §27):**
`.graph-toggle` (launcher, option B: quiet grey-rule ghost, `--font-ui`, burgundy
fill on `aria-expanded="true"`; one rule, no per-section overrides), `.graph-toolbar`
+ `.graph-toolbar--panel`/`--page` (context base + 2 modifiers — resolved the spec's
open item), `.graph-chip` (active = `aria-pressed="true"` only, no `.is-active`),
`.graph-action` (dashed ghost), `.graph-toolbar-divider`, `.graph-panel-close`
(glyph normalized to `×`), `.graph-legend` + `--panel`/`--page` /
`-key`/`-swatch`/`-mark`(`--dashed`). Per-section §28/§31/§36 chrome CSS pruned
(node/edge/canvas/summary/skip-link rules kept).

**Single source of truth:** `layouts/partials/graph-legend.html` — included by all
6 surfaces, param `(dict "section" "<garden|research|works>" "variant" "<panel|page>")`.
Structure key always server-rendered (identical skeleton, per-section wording).
Color key: research/works server-rendered via `data-swatch="0|1|2"` + static §27
rules; garden = empty `data-graph-legend-dynamic` slot filled at runtime by
`garden-graph.js` (tag palette is content-dependent, inline JS-set style — fine,
not Go-template). Research theme order mirrors `graph-data.html`'s
`themePaletteOrder` (two-pass `sort slug asc` then `sort weight asc`) so legend
colors match node `data-theme-color`.

**New gate:** `tools/check_graph_chrome.py` — sibling-less (like `check_smoke.py`),
wired pre-build in ci-local + hugo.yaml; CI is now 51 named steps. Fails if any
pruned per-section selector reappears or any of the 6 surfaces drops the partial.

**Execution:** subagent-driven, 7-task plan, every task two-stage reviewed. Task 2
hit a review-loop fix: the plan's verbatim swatch markup used
`style="background:var({{ .var }})"` which Go `html/template` sanitizes to
`var(ZgotmplZ)` — see [[reference_hugo_css_var_zgotmplz]]; fixed to data-swatch +
plan/spec corrected. Post-review tweak per user visual verification: works `⊞ Graph`
launcher left-aligned (dropped Task 4's `justify-content:space-between` on
`.works-umbrella-toolbar`) to match garden/research.

**LHCI note:** local ci-local fails LHCI **mobile `/garden/`** perf (~0.84 < 0.90).
NOT a regression — pre-slice master fails identically on this machine; documented
local-CPU variance (see [[reference_ci_local_lhci_deps]]); deterministic
`check_page_weights` gate is GREEN (slice is net −295 CSS, zero added payload); CI
on consistent hardware is authoritative. Do not re-investigate.

**Queued follow-ups:**
- [[project_persistent_graph_access_stub]] — new stub filed this session: keep a
  `⊞ Graph` launcher on every research+works item page (like garden notes) so the
  graph survives node-click traversal. Soft-depends on this slice's canon.
- Hardening nit (not filed as a slice): `garden-graph.js` `buildLegend` still uses
  `innerHTML` for the tag label (pre-existing pattern, no current risk —
  author-controlled slugs). Replace with `createTextNode` before Phase 3 emits real
  org tags. Reviewer-flagged Minor, deferred.
