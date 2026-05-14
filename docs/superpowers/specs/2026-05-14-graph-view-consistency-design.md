# Graph-view visual consistency across sections

**Status:** Stub — queued for brainstorming.

## Motivation

User feedback during the citation-export slice (2026-05-14): the graph views in the three sections that have them — garden, research, works — look visually different from each other.

Each was implemented in its own slice (garden first; research's `research-graph.js` was a copy+trim of `garden-graph.js`; works' `works-graph.js` was a copy+trim of `research-graph.js`). Each carries its own CSS scaffolding under §27 (per CLAUDE.md), and divergent style decisions have accumulated.

The user expects them to look like the same family — same node styling, same legend treatment, same panel chrome, same hover/focus behaviour — even though their semantics (parent/child research edges vs. tag-share works edges vs. topic-map garden edges) differ.

## Open dimensions to surface in the brainstorm

- **Node visual vocabulary** — size scale, fill rule, label position, dragged/active state. Currently each section's nodes look slightly different.
- **Edge visual vocabulary** — solid vs. dashed convention. Each graph uses dashed for some semantic but the semantics differ (cross-topic in garden, shared-supporting-notes in research, cross-medium in works).
- **Legend treatment** — visibility, positioning, terminology. Currently inconsistent.
- **Panel chrome** — graph panel container, resize handle, header buttons. Slight differences in spacing + border across sections.
- **Standalone graph page chrome** — `/garden/graph/`, `/research/graph/`, `/works/graph/` — each layout file has minor divergences in how it stitches together the panel + page-sidebar.
- **Color palette** — garden uses topic-derived colors; research uses theme-weight palette; works mostly uses a single accent. Should there be a unified scheme or section-specific accents with shared structure?

## In scope (likely)

- `assets/css/main.css` §27 (graph CSS scaffolding) — likely a rewrite.
- `assets/js/garden-graph.js`, `research-graph.js`, `works-graph.js` — possibly extract a shared core; currently each is an independent copy+trim.
- Per-section graph layouts (`layouts/garden/graph.html`, `layouts/research/graph.html`, `layouts/works/graph.html`).
- Per-section graph partials (`layouts/partials/{garden,research,works}/graph-{data,script,panel}.html`).

## Out of scope (likely)

- The DATA emitted by each section's `graph-data` partial — those reflect distinct semantics (parent/child edges vs. tag-share vs. topic) and shouldn't be flattened.
- Graph PHYSICS — d3-force parameters can stay per-section.

## Constraints

- No AI-generated SVG icons.
- WCAG AA contrast on every node + edge color.
- Colour-blindness simulation safety (per spec §1).
- Bundle weight already tracked — the works umbrella bundle is ~112KB, research ~107KB, garden ~117KB. A shared core might reduce duplication; a rewrite must not regress.

## Open questions for brainstorm

1. Extract a shared `graph-core.js` module that the three section-specific graphs import? Or keep them as siblings + sync the CSS only?
2. Unified palette across all three, or shared structure with section accents?
3. Legend: a single component the three layouts include, or per-section variants with shared chrome?
4. Should the standalone graph pages share more layout structure (currently each pulls in `page-sidebar.html` + the section's graph-panel partial independently)?

## Process

Pick up with `superpowers:brainstorming` when scheduled. Spec gets fleshed out then; plan drafted only when implementation is queued.
