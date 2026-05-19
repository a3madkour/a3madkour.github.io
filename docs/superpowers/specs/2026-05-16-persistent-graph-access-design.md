# Persistent graph access across research + works

**Status:** DESIGN COMPLETE. Brainstormed 2026-05-18. Ready for `superpowers:writing-plans`.

**Stub filed:** 2026-05-16 (surfaced during visual verification of the graph-view chrome-consistency slice).
**Brainstorm:** 2026-05-18.

## Motivation

In the **garden**, the graph is a companion you can keep open while you read:
the `⊞ Graph` launcher lives on every garden note page (via `partials/garden/path-log.html`)
as well as the `/garden/` index, garden-graph.js coordinates with the note "stack",
and panel open/width state persists across navigation. Open the graph, click a node,
land on the note, and the graph is still right there.

In **research** and **works**, the graph is a dead-end: the launcher exists only
on the section umbrella (`/research/`, `/works/`) and the standalone
`/research/graph/` · `/works/graph/` pages. Clicking a node navigates to a theme /
question / game / music / poem page that has **no graph launcher and no panel** —
the graph "goes away" and the only way back is the browser back button or the
umbrella. Traversal kills the graph.

**Desired:** the graph is persistently reachable and re-openable, with retained
state, on every research and works item page — the way garden already does it —
so it stays a usable navigation/orientation aid during traversal. Garden's
launcher placement is *also* improved in the same slice, so all three sections
share one consistent, correct chrome.

## Key finding (de-risks the slice)

`research-graph.js` and `works-graph.js` are copy+trims of `garden-graph.js` and
**already contain the full persistence machinery**:

- `sessionStorage` panel-open key (`research-graph-open` / equivalent),
- un-animated auto-restore of the open panel on `init()` (so it survives navigation),
- node click → `window.location.assign(url)` (full navigation, no stack),
- a mobile branch in `openPanel()` that redirects to the standalone `/x/graph/`,
- panel width persisted in `localStorage`, node positions in `sessionStorage`.

The only reason the panel doesn't survive traversal on item pages today is that
**the graph bundle never loads there, and the item layouts include neither the
panel partial nor a launcher**. This is therefore largely a wiring slice, not a
JS rewrite.

## Decision summary

| Question | Decision |
|---|---|
| Graph access model | **Full in-page panel parity** with garden (not link-back, not lazy-load). The user knowingly accepted the per-page bundle weight. |
| Launcher chrome | **Option D** — a shared sticky context bar, left-aligned `⊞ Graph` toggle + minimal breadcrumb, one shared partial across garden + research + works. |
| Garden's `path-log.html` | **Refactored into the shared partial.** Garden's launcher moves right→left (fixes the panel-covers-launcher bug); stack count / clear / history become garden-only items inside the shared bar. |
| `is-here` current-node marker | **In scope for v1.** |
| Stack coordination | **Out of scope** — garden-specific Zettelkasten behavior. |

## Design

### 1. Launcher chrome — shared sticky context bar (Option D)

A shared partial (working name `layouts/partials/graph-launcher-bar.html`)
renders a **sticky-to-viewport-top** bar containing a **left-aligned
`.graph-toggle`** button and a breadcrumb slot.

- **Left-alignment is load-bearing.** `.graph-panel` is
  `position: fixed; right: 0; width: 320px; z-index: 20` and is *user-resizable*
  via its drag handle. A right-aligned launcher (today's garden behavior:
  `.path-log-actions { margin-left: auto }`, sticky bar only `z-index: 5`) is
  covered by the open/resized panel. A left-aligned launcher is never under the
  panel at any viewport ≥ 720 px, with no z-index changes and no dynamic
  panel-width offset. This is the concrete fix for the garden gripe.
- The launcher reuses the **canonical `.graph-toggle`** (CSS §27) which already
  carries the burgundy `[aria-expanded="true"]` open state from the
  graph-view chrome-consistency slice — so it doubles as the open/close toggle
  and stays visible and meaningful while the panel is open.
- The bar is sticky (`position: sticky; top: 0`), matching garden's existing
  `.garden-path-log` behavior, so it stays visible while scrolling.

**Per-section content of the shared bar:**

- **Garden:** `partials/garden/path-log.html` is refactored to render *inside*
  the shared bar. The reading-path breadcrumb, stack count, `clear` button, and
  `history` link remain as **garden-only items** within the bar; the launcher
  moves to the left-aligned canonical slot.
- **Research:** `research-theme/single.html` and `research-question/single.html`
  include the shared bar. The breadcrumb reuses their existing
  `Research › Theme › Question` trail (currently rendered as `.research-breadcrumb`;
  it moves into the shared bar).
- **Works:** `works-games/single.html`, `works-music/single.html`,
  `works-poetry/single.html` include the shared bar. Works item pages **gain a
  breadcrumb they do not have today** (e.g. `Works › Games › Title`) — a small IA
  win ("up out of the dead-end") bundled with the graph fix.

### 2. Panel + data partials on item pages

Each of the 5 item single layouts gains the section's existing
`graph-panel.html` and `graph-script.html` partials (research → research's,
works → works'). No new panel/legend markup is authored — the panels already
include the shared `graph-legend.html` (CSS §27). `research-graph.js` /
`works-graph.js` `init()` already handle the "not the standalone graph page, not
the umbrella" case: they wire the toggle, restore the panel from
`sessionStorage`, and render into the panel canvas.

### 3. Bundle wiring

`layouts/partials/scripts.html`:

- **Research:** widen the predicate so `entry-research.js` (~107 KB w/ d3) loads
  on `.Section == "research"` (all pages), not just `/research/` +
  `/research/graph/`.
- **Works:** widen so the d3-bearing `entry-works-umbrella.js` (~112 KB) loads on
  all works pages. Plan-phase detail: confirm what per-item `entry-works.js`
  carries today (only `filter-chips.js`, which item pages do not use) and either
  fold the needed bits in or load both — resolved during planning, not assumed
  here.

### 4. Behavior (inherited parity)

- Node click → full navigation; panel auto-reopens un-animated from
  `sessionStorage` on the destination page; stays open across traversal until
  the reader explicitly closes it (existing `garden`-derived behavior).
- **`is-here` current-page node marker:** when the panel renders on an item
  page, the node whose slug matches the current page is marked with an
  `is-here` class as an orientation aid. Cheap: the page knows its own slug;
  graph nodes already carry slugs. Applied on **research and works item pages
  only**. Garden is excluded: it already has a richer orientation model
  (`in-stack` node marking tied to the column stack), and layering `is-here`
  on top would conflict with that semantics — a garden-side change is not part
  of this slice.
- **Mobile (< 720 px):** `.graph-panel` is `display: none` (existing CSS); the
  launcher navigates to the standalone `/research/graph/` · `/works/graph/`
  (existing `openPanel()` `isMobile()` branch). The sticky bar itself works on
  mobile (garden's path-log already is sticky on mobile).
- **Stack coordination:** out of scope. Research/works node-click navigates and
  never stacks (already true in the JS).

### 5. Chrome-consistency gate extension

`tools/check_graph_chrome.py` (sibling-less, from the graph-view
chrome-consistency slice) enforces the canon across 6 graph surfaces. This slice
**extends the gate**: the 5 new item-page surfaces (research theme, research
question, works game, works music, works poem) must assert presence of the
shared launcher bar + the section graph panel + the shared legend, so the canon
stays enforced as the surface count grows.

## Risks / verification (must be done in the plan, not assumed)

- **Page-weight gate:** `/research/` and `/works/` prefixes already carry
  600 KB budgets (with comments anticipating the inlined graph bundle);
  `/works/music/` is 500 KB. Item pages weigh ~10 KB today, so ~110 KB of d3
  drops in with large headroom — **no threshold change is expected**, but the
  plan must build and run `tools/check_page_weights.py` to confirm empirically.
- **LHCI perf:** ~110 KB of d3 parse on item pages may move mobile performance
  scores. Garden item pages already ship this exact payload and pass on CI
  hardware (precedent), but the plan must check which URLs `lighthouserc.json`
  and `lighthouserc.mobile.json` actually hit and confirm no research/works item
  URL regresses below threshold. Per existing project knowledge, LHCI mobile
  `/garden/` is locally CPU-variant; CI hardware is authoritative.
- **Shared-partial refactor of garden's path-log** touches a shipped, reviewed
  surface. The plan must include a garden visual spot-check (launcher now
  left-aligned; stack count / clear / history still present and functional;
  panel still not covered) before merge.
- Run `tools/ci-local.sh` before pushing (mirrors CI step-for-step).

## Known limitation (recorded during implementation)

The shared partial's `generic` breadcrumb is a **two-state model**: a crumb
with a `url` renders as a link; a crumb without a `url` renders as the
current page (`<span … aria-current="page">`). There is no third "plain,
non-link, non-current" state. The only place this matters is the
research-question theme crumb's *fallback* branch (when a question's
`theme` does not resolve to a rendered theme page): it is given
`url: /research/` so it stays a single-`aria-current` page with a link to
the research index (slightly off-target label, but valid markup). The old
inline breadcrumb rendered that fallback as plain non-link text. This is
acceptable because `tools/check_research_links.py` (a CI gate) guarantees
every question's `theme` resolves, so the fallback is unreachable in a
green build. If a future caller needs a genuine plain non-current crumb,
add a third state to `graph-launcher-bar.html` then — out of scope here.

## Out of scope

- Graph rendering, node/edge semantics, physics, filter dimensions — unchanged.
- No `graph-core.js` extraction (ruled out in the prior slice; not revisited).
- Garden graph *behavior* unchanged; only the launcher position moves. (One
  consequence found in implementation review: relocating the launcher to the
  bar's first child requires a 2-line defensive guard in `garden-stack.js`
  `updatePathLog()` so the stack renderer does not prune persistent chrome —
  this protects the launcher, it is not new stack behavior.)
- Stack coordination for research/works.

## Dependency / sequencing

Soft-depends on the graph-view chrome-consistency slice (shipped 2026-05-16) for
the canonical `.graph-toggle` / panel / shared-legend system — now satisfied.
Independent of the elisp pipeline. Polish slice; no phase gate.

## Process

Next: `superpowers:writing-plans` to produce the implementation plan. No plan
drafted yet (per project convention: plan only when implementation is queued —
which it now is).
