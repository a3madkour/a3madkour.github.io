---
name: Graph manipulation slice — merged
description: Phase 4 follow-up slice (zoom/pan/drag-node + resize panel) shipped to master 2026-05-11; includes 6 post-merge fixes from QA. Pushed to origin.
type: project
originSessionId: 91fc49fd-379f-4c60-8b2a-f8ce525bb3d5
---
**Status:** MERGED + PUSHED on 2026-05-11. Merge commit `6935109` (pre-fixes); post-merge fixes 41bbd29 → 84c9e54. Branch `graph-manipulation` deleted.

**What shipped (13 slice commits + 6 follow-up fixes):**

Slice (vendored ~80 KB of d3 modules — `d3-zoom`, `d3-drag`, `d3-selection` alongside existing `d3-force`):
- Wheel zoom (0.3×–4×) toward the cursor; drag-pan on empty SVG; clamp at extents; double-click-to-zoom disabled
- Node drag via d3-drag with Obsidian-style stay-put release (drag-end keeps `fx/fy`)
- `wasDragged` flag suppresses navigation when a drag actually moved; pure-click branch releases the pin we set in start
- Reset view + Reset positions toolbar buttons (italic action-chip variant)
- Position cache migrated `Array<{slug,x,y}>` → `{nodes:[{slug,x,y,pinned}], view:{k,tx,ty}}` with legacy normalization on read
- Mount-time restore: cached view transform + pinned `fx/fy` reapplied; `state.pinnedSlugs` and `state.viewTransform` reset at start of each `buildSimulation` call
- Pre-existing Phase 4 bug fixed: `sim.on('tick', renderTick)` was missing — simulation reheats never re-rendered. Added in Task 6.
- CSS §27/§28: grab/grabbing cursors, toolbar divider, action-chip italic variant

Post-merge fixes (from QA — surfaced six real bugs that the planning + reviews missed):
- **`selection.interrupt` stub** (`41bbd29`) — d3-zoom calls it on transform set; lives in d3-transition which we don't vendor. Cache-hit mount was throwing → SVG mounted without `renderTick` → all nodes at (0,0). Stub it as chainable no-op on the d3-selection prototype.
- **Cache key drops slug when scope=all** (`66d3faa`) — was keying per focal note even when the subgraph is identical. Dragged positions now persist across note navigation. Local-mode (1-hop/2-hop) still keys per slug.
- **Defer drag reheat to first `drag` event** (`3679985`) — was reheating on `start`, which fires on every click. Simulation stayed hot for the mousedown-to-click window, neighbors drifted visibly during navigation. Now reheats only on actual movement (`__reheated` flag guards repeated restarts).
- **Graph node clicks dispatch `garden:graph-navigate`** (`d7e6aa1`) — was `window.location.assign`, which lost the stack. Now appends to the stack via the same path as in-column link clicks. Standalone `/garden/graph/` page still navigates (no stack mounted).
- **Resizable side panel** (`e085cbb`) — 6px left-edge handle, pointer-capture drag, width clamped to [240px, 80vw], persisted in `localStorage['garden-graph-panel-width']`. Hidden under 720px alongside the panel itself.
- **Consent banner button color in dark mode** (`84c9e54`) — pre-existing Phase 4 bug: UA `ButtonText` overrode the banner's `color: var(--color-ink)`. Set explicit `color` on the button rule.

**Why:** The slice's spec/plan got most of the architecture right but missed several runtime details that only emerge under interaction. The `interrupt` issue in particular was a real "didn't vendor a transitive dep" gotcha — d3-zoom calls a d3-transition method internally.

**How to apply:**
- For future d3-anything slices: confirm the *runtime* dependency graph, not just the import-statement dependency graph. esm.sh's `?bundle` flag doesn't help here because d3-zoom expects the consumer to pass selections that have the d3-transition methods.
- When a manipulation surface fires events on every gesture (click/drag/etc.), be skeptical of "reheat on start" — clicks are gestures too.
- When persistence is keyed by something the user shouldn't perceive (focal note, viewport), include only when it materially affects layout. The cache-key bug here was a Phase-4 holdover.

**Known follow-ups (documented but not blocking):**
- Cursor `:active` may not flip during pointer-captured drag/pan on all browsers. Would need a JS-toggled `.is-dragging` / `.is-panning` class to be reliable. Not user-blocking.
- `resetPositions()` calls `persistCacheDebounced()` 200ms after the click, but the simulation is mid-settle; cache captures pre-converged positions. Next mount may briefly show off layout that another reset fixes. Either trigger persist on `sim.on('end', ...)` or pre-tick synchronously inside resetPositions.

**Pointers:**
- Spec: `docs/superpowers/specs/2026-05-11-graph-manipulation-design.md`
- Plan: `docs/superpowers/plans/2026-05-11-graph-manipulation.md`
- Merge commit: `6935109`
- Post-merge fixes: `41bbd29`, `66d3faa`, `3679985`, `d7e6aa1`, `e085cbb`, `84c9e54`
