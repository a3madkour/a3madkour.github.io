---
name: Phase 4 follow-ups slice — merged
description: G1/G2/I4 graph+stack fixes + multi-entry JS bundling shipped to master 2026-05-11 (merge e4af0ee, pushed to origin)
type: project
originSessionId: cfd5e26b-590f-4577-aed6-8c8b9f757692
---
**Status:** MERGED + PUSHED on 2026-05-11. Merge commit `e4af0ee`. Branch `phase-4-followups` deleted.

**What shipped (4 atomic commits):**

- `203f1b3` Graph: class-toggled cursors + resetPositions persist after settle (G1+G2). `.is-panning` / `.is-dragging-node` on the SVG via zoom/drag start+end handlers; CSS keys grabbing off classes (drops `:active` for graph SVG + nodes — unreliable under pointer capture). `resetPositions()` now uses one-shot `sim.on('end.reset', flushCache)` so persist fires at convergence, not 200 ms into a 1-2 s settle; reduced-motion branch pre-ticks 300 iterations synchronously via `state.renderTick` and flushes immediately (the previous `.alpha(0.5).restart()` animated against the motion preference).
- `961c382` Garden index ⊞ Graph button: explicit color tokens for dark mode. Same root cause as the consent-banner fix (`84c9e54`). The toggle appears in two places — `.garden-path-log` on note pages (styled) and standalone on the garden index (was relying on UA `ButtonText`, didn't follow `data-theme=dark`). Hoisted the rule off the `.garden-path-log` scope.
- `7d5d7f8` Stack: guard `appendColumn` against rapid duplicate clicks (I4). Module-level `pending` Set, try/finally cleanup, post-await re-check of `state.slugs.includes(slug)`.
- `a47ae6a` JS: multi-entry bundling — d3 ships only on garden pages. Three independent `js.Build` calls in `scripts.html`: core (~1.4 KB, every page) + essay (~5 KB, /essays/) + garden (~119 KB, /garden/). Non-garden pages no longer ship d3 at all (was 123 KB on every page).

**Bundle-splitting gotcha worth keeping handy:** esbuild requires `outdir` mode for code splitting, but Hugo's `js.Build` is `outfile`-only. Setting `splitting: true` + `format: "esm"` on a single entry **silently inlines** dynamic imports rather than emitting chunks — verified with a minimal Hugo repro. The only working path today is multi-entry (one `js.Build` call per section). `filter-chips.js` ends up duplicated in essay + garden bundles (~8 KB cost), which is far cheaper than the d3-everywhere status quo.

**Why:** All five items were tracked as Phase 4 known-non-blocking follow-ups (memo: `project_graph_manipulation_slice.md` "Known follow-ups" + `project_phase_4_status.md` open-items list). Picked up in one batch on the same day the graph-manipulation slice merged.

**How to apply:**
- For future cursor-feedback under pointer capture (d3-drag, custom resize handles), default to class-toggled cursors rather than `:active`. The pattern is set in §27/§28 of `main.css` and the resize handle's `.is-resizing`.
- For UA-button color leaks in dark mode: any unstyled `<button>` that should follow theme tokens needs an explicit `color: var(--color-ink-soft)` (or similar). Check this any time a button is rendered outside a styled wrapper.
- If a future slice wants real lazy-loaded chunks, the multi-entry pattern is in place — just add another entry + conditional `<script>` in `scripts.html`. True code splitting via `splitting: true` will need a Hugo enhancement or post-processing step that's not on the table.

**Pointers:**
- Merge commit: `e4af0ee` on master
- CLAUDE.md JS-pipeline section rewritten in `a47ae6a` to describe multi-entry behavior
- No new spec/plan — these were known follow-ups picked from memory
