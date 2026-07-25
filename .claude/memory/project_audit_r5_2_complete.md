---
name: audit-r5-2-complete
description: "R5.2 graph-core extraction SHIPPED 2026-07-04 (d1e214c..d0ee5b0 + docs 88b0b4a); 2280→1316 LOC, createGraph(adapter) + 3 thin adapters; R5.3 next"
metadata: 
  node_type: memory
  type: project
  originSessionId: a4b4e454-fc0d-4ae8-8172-2c36574d9f94
---

# Audit R5.2 — graph-core extraction (shipped)

**2026-07-04, commits `d1e214c..d0ee5b0` (3 refactor) + `88b0b4a` (docs).** Executed **inline** (executing-plans) — the user chose inline over subagents because R5.2 rides on visual/behavioral parity the E2E specs don't fully capture. Plan: `docs/superpowers/plans/2026-07-04-r5.2-graph-core.md`. Design: `docs/superpowers/specs/2026-07-04-r5.2-graph-core-design.md`. **Not yet pushed** at time of writing (local on master).

**What shipped:** collapsed the 3 near-duplicate d3 graph runtimes into `assets/js/graph-core.js` (`createGraph(adapter)` factory) + 3 thin adapters. **2,280 → 1,316 LOC (−42%)**: core 538, garden 297, research 252, works 229. Shared infra (position cache, drag, zoom, settle loop, SVG scaffold, panel open/close, resize, chip primitives) lives once in core, parameterized by `adapter.classPrefix`. Adapters own the divergent surface: `parseData`/`applyFilters`/`filterCacheKey`/`nodeRadius`/`renderNode`/`edgeClass`/`svgAria`/`forceParams`/`onNodeClick`/`buildToolbar` + optional `onSvgCreate`/`onRenderComplete`/`onOpenPanel` hooks. Garden-only features (stack-coordination, N-hop BFS, dynamic JS legend) stay in garden's adapter via hooks.

**Works was normalized** to garden/research conventions (the [[audit-remediation-roadmap]] R5.2 decision): JS-built toolbar (dropped SSR chips + `wireToolbar` + dead `works-graph-summary`), `aria-hidden`+`inert` panel (was the `hidden` attr), `<div>` canvas (was svg-as-canvas; core creates the `<svg>`, badge-gradient `<defs>` moved to `onSvgCreate`), removed the pre-rendered resize handle (core creates it). **This subsumes R3.2's deferred graph-panel reconciliation.** Its E2E spec updated to the div-wrapper form.

**Gotchas worth carrying:**
- **`graph-core.js` MUST stay at `assets/js/` depth** — its `./vendor/d3-*` dynamic import is relative to the compiled bundle at `js/`. A subdir breaks it. Core is bundled into each of the 3 graph entries (source-level share, like `filter-chips.js`), not a runtime chunk.
- **css-refs linter caught the `${classPrefix}-graph-node` base class** — the static scan resolves interpolation *prefixes*, not leading interpolation (`${p}-graph-node`). Allowlisted `research-graph-node` + `works-graph-node` in `tools/css-refs-allowlist.txt`; garden keeps a literal ref via `updateInStackMarkers`. See [[reference_css_refs_leading_interpolation]].
- **ci-local.sh pagefind gap** (fixed here): the E2E search spec 404'd locally because ci-local skipped the Pagefind index when the `pagefind` binary was absent. Added an `npx pagefind@1.5.2` fallback so local ci-local mirrors CI.
- Verification was E2E (3 graph mount specs, invariant for garden/research) + **throwaway render-seam parity specs** per graph (svg aria/desc, node role/aria/shape, edge class, toolbar, gradient defs, panel inert→open) — stronger than the bare mount specs, deleted after each task.

**Next: R5.3** — AMS-block (12 shortcodes) + graph-panel single-partial consolidation. The graph-panel HTML is now uniform across all 3 sections (R5.2 normalized works), so R5.3's graph-panel piece is reduced to extracting one shared partial. Then R5.4 (Python tooling dedup). See [[audit-remediation-roadmap]].
