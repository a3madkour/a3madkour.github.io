---
name: Research surface Slice 2 — merged
description: Force-directed research graph (toggle + panel + standalone page) shipped to master 2026-05-11
type: project
originSessionId: 7ac64b5d-36cb-43d9-8d56-dc2340b28e78
---
Phase 5 Slice 2 of the research surface — force-directed graph + ⊞ Graph toggle on `/research/` + standalone `/research/graph/` page — shipped to master 2026-05-11 in merge `a6654d2`, pushed to origin same day.

**Why:** Closes Phase 5; was the only deferred piece from Slice 1 (which merged earlier the same day in `0ac950c`). Both halves of the research surface (theme/question hubs in Slice 1, graph runtime in Slice 2) are now complete. Phase 5 is fully done.

**How to apply:** Next major branches: Works (Phase 6 — games/music/poetry surfaces), Library (Phase 7 — data-driven filtered view of media-flavor garden notes), Homepage v3 final assembly (Phase 7), org-mode pipeline (Phase 3, blocks the About page Now widget + real content for fixture-shaped data), Pagefind + Lighthouse (Phase 8).

**Key technical decisions logged for future reference:**

- The §27 "Garden graph panel" CSS section was renamed to "Graph (shared)" via a class hoist: `.garden-graph-*` → `.graph-*` for scaffolding (toggle, panel, panel-canvas, panel-toolbar, panel-legend, panel-resize). Surface-specific bits stayed namespaced: `.garden-graph-page`, `.garden-graph-node` (§28), `.research-graph-node-*`, `.research-graph-edge-cross-theme` (§31).

- `research-graph.js` is a copy + trim of `garden-graph.js`, NOT a shared module. Per spec D3: only two callers, both will diverge. Wait for a third graph before extracting `graph-core.js`.

- Cross-theme edges (dashed) derive from shared `supporting_notes` in question fixtures — emergent, no new frontmatter field. Story-atoms produces one cross-theme edge between memory-and-play and procedural-narrative questions in current fixtures.

- Theme palette = burgundy / steel / green deterministic by `theme.weight` order, linter-enforced unique (`validate_unique_theme_weights()` in `tools/check_research_fixtures.py`).

- Multi-entry bundle is page-narrow on research (only `/research/` index + `/research/graph/` standalone), not section-wide like garden. Theme + question pages stay on the core bundle.

- In-graph filter chips: tag is multi-select AND (comma-joined string), status single-select (questions only — theme nodes never dim).

- Mobile (≤720px) toggle navigates to `/research/graph/` instead of opening the panel (matches garden's pattern).

Bundle sizes recorded in CLAUDE.md: core 1.4 KB · essay 4.8 KB · garden 117 KB · research 107 KB.
