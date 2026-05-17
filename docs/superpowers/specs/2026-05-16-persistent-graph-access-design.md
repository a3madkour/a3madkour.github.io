# Persistent graph access across research + works

**Status:** STUB. Brainstorm pending. File via `superpowers:brainstorming` when scheduled.

**Date:** 2026-05-16 (surfaced during visual verification of the graph-view chrome-consistency slice).

## Motivation

In the **garden**, the graph is a companion you can keep open while you read:
the `⊞ Graph` launcher lives on every garden note page (via `partials/garden/path-log.html`)
as well as the `/garden/` index, garden-graph.js coordinates with the note "stack",
and panel open/width state persists across navigation. You can open the graph,
click a node, land on the note, and the graph is still right there.

In **research** and **works**, the graph is a dead-end: the `⊞ Graph` launcher
exists only on the section umbrella (`/research/`, `/works/`) and the standalone
`/research/graph/` · `/works/graph/` pages. Clicking a node navigates to a theme /
question / game / music / poem page that has **no graph launcher at all** — the
graph "goes away" and the only way back is the browser back button or returning
to the umbrella. Traversal kills the graph.

**Desired:** the graph should be persistently reachable throughout research and
works — a `⊞ Graph` button (and ideally a re-openable panel with retained state)
present on every research and works page, the way garden already does it — so the
graph stays a usable navigation/orientation aid while you traverse items.

## What already exists (foundation)

- The graph-view chrome-consistency slice (2026-05-16) made `.graph-toggle` a single
  canonical rule and the graph panel/legend/toolbar one shared, section-agnostic
  system. Adding the launcher to additional page types is now a markup-only,
  visually-consistent change — no per-section styling work.
- Garden's model is the reference implementation: `path-log.html` carries the
  launcher on note pages; garden-graph.js owns stack-coordination + panel-state
  persistence (localStorage). Research/works graph JS were copy+trims that
  **dropped** the stack-coordination + persistent-panel machinery.
- Research splits into `research-theme` / `research-question` single layouts;
  works into `works-games` / `works-music` / `works-poetry` single layouts — these
  are the per-item pages that currently lack any graph entry point.

## Open questions for the brainstorm

- **Launcher placement per page type:** research theme/question pages and works
  game/music/poem pages have no path-log analog. Where does `⊞ Graph` live — a
  shared per-page chrome slot (header? the existing `page-sidebar`? a small
  fixed affordance?) consistent across both sections, or section-specific?
- **Panel vs. link-back:** full re-openable in-page panel (like garden, requires
  porting panel-state persistence + the panel partial onto every item page) vs.
  a lighter "return to graph" affordance (link to the standalone `/x/graph/`,
  optionally deep-linked to the just-visited node). Cost vs. value tradeoff.
- **State persistence:** should panel open/width/filter state survive navigation
  across research/works (garden persists it via localStorage)? Does the
  standalone graph deep-link to / highlight the node you came from?
- **Stack coordination:** garden's graph tracks a visited "stack". Do research/works
  want an analogous traversal trail, or is that garden-specific (Zettelkasten)
  and out of scope here?
- **Bundle weight:** research (~107 KB) and works-umbrella (~112 KB) graph bundles
  are currently page-narrow (only `/x/` + `/x/graph/`). Putting a panel on every
  item page widens the load surface — measure against the page-weight gate; a
  link-back affordance avoids this entirely.
- **Mobile:** garden's panel is hidden < 720px (launcher navigates to the
  standalone page instead). Same fallback for research/works.

## Out of scope (likely)

- Graph rendering, node/edge semantics, physics, filter dimensions — unchanged.
- Garden behavior — already has this; only research + works gain parity.

## Dependency / sequencing

Soft-depends on the graph-view chrome-consistency slice (shipped 2026-05-16) for
the canonical launcher/panel/legend system. Independent of the elisp pipeline.
Polish slice; no phase gate.

## Process

Pick up with `superpowers:brainstorming` when scheduled. Spec fleshed out then;
plan drafted only when implementation is queued.
