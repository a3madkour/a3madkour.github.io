---
name: Phase 4 (garden interactions) — merged
description: Phase 4 shipped to master 2026-05-09; next step is the graph-manipulation follow-up slice (zoom/pan/drag), not yet started
type: project
originSessionId: ee7c32a5-f961-4c9b-afda-120ab065f7e2
---
**Phase 4 — garden interactions — MERGED + PUSHED on 2026-05-09** (merge commit `1181ba1`, deployed to origin and GitHub Pages via the repo's Actions workflow).

What shipped (24 commits on the branch, 16 plan tasks + post-final-review polish):
- Eager Matuschak-style stacked-column retrieval (`garden-stack.js`): every garden note page is column 1 from load; click intercept → fetch → DOMParser-extract `<article>` → append; `?stack=` URL sync; deep links restore; click-on-existing re-focuses.
- Path log + first-time consent banner; visited slugs persist to localStorage / sessionStorage based on consent (yes / session / no).
- Outgoing-links + backlinks at column bottom, computed from `partials/garden/graph-data.html` (`partialCached`).
- Force-directed graph (vendored d3-force at `assets/js/vendor/d3-force.min.js` — no npm). Side panel on desktop, separate `/garden/graph/` page on mobile. Tag/stage filters, all/1-hop/2-hop local mode. Bold-stroke "in stack" markers via `garden:stack-changed` event. Position cache in `sessionStorage["garden-graph-positions"]` keyed by filters + viewport so layout is byte-stable across navigation. Slide animation gated by `.is-animating` class so user-toggle animates but page-load restore is instant.
- Esc disambiguation via `lastPointerInStack` flag + `stopImmediatePropagation` (focus-based check was too brittle when SVG canvas whitespace was clicked → focus dropped to body).
- New CI gate `tools/check_garden_links.py` validates internal `/garden/<slug>/` references resolve.
- 27 internal links across 12 of 14 fixtures; one deliberate orphan (`nguyen-2020-games-as-art`).
- ID-collision fix: `namespaceColumnIds` rewrites stacked column's `[id]` descendants to `<slug>--<oldid>` and matching internal `href="#..."` anchors.

**Next slice (not started):** graph-manipulation follow-up — zoom + pan + drag-nodes. Vendor `d3-drag` next to `d3-force`. Add "Reset view" chip and "Pin nodes" toggle to the graph toolbar. ~2 hours of focused work. New spec/plan/branch.

**Why:** keeps each slice scoped; manipulation is a feature, not a polish bug.

**How to apply:** When picking up — `git log origin/master..master` will show the unpushed Phase 4 commits. If the user hasn't pushed yet, ask first before pushing (per CLAUDE.md "Executing actions with care"). Then run `superpowers:brainstorming` for the manipulation slice — should be quick since the design space is small.

**Open follow-ups from final code review (not blocking):**
- I4: race on rapid sequential stack clicks (would need a `pending` set in `appendColumn`)
- Bundle splitting for actual lazy d3-force loading (currently the `import()` is bundled inline because `js.Build` lacks `splitting: true`)
- M1–M9: minor stylistic items (palette comment, button-order privacy nudge, listener delegation on graph nodes, etc.)

**Worktree status:** removed. Branch `phase-4-garden-interactions` deleted (was fully merged). Dev server on 1314 stopped. Repository is in a clean post-merge state on master.

**Pointers:**
- Spec: `docs/superpowers/specs/2026-05-08-garden-interactions-design.md`
- Plan: `docs/superpowers/plans/2026-05-08-garden-interactions.md`
- Merge commit: `1181ba1`
