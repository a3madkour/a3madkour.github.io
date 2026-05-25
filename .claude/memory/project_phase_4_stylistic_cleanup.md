---
name: Phase 4 stylistic cleanup (M1–M10) — merged
description: Ten code-review nits across the Phase 4 surface shipped to master 2026-05-11 (merge 7403df8, pushed). Closes the M1-M9 list from prior memory + a bonus M10.
type: project
originSessionId: cfd5e26b-590f-4577-aed6-8c8b9f757692
---
**Status:** MERGED + PUSHED on 2026-05-11. Merge commit `7403df8`. Branch `phase-4-stylistic-cleanup` deleted.

**What shipped (10 atomic commits, one per item):**

- `04cbbfd` M1 — TAG_PALETTE curation/fall-through comment (`garden-graph.js`)
- `a7dfccc` M2 — Consent banner privacy-first button order: No,never / Just this session / Yes,persist (was reverse)
- `7e1818b` M3 — Delegate node click + keydown onto nodeLayer; read identity from `__data__` + `dataset.slug` instead of per-node closure
- `aeaa8fb` M4 — `NODE_R_MIN/MAX/PER_DEGREE` constants + formula comment for `nodeRadius()`
- `3527caa` M5 — Log corrupt JSON in positions cache + visited list (drop + reset, don't fail forever); keep `SecurityError` swallows silent on `localStorage` access in `readConsent/writeConsent` since those are documented expected failures
- `464c9a9` M6 — `getActiveCanvas()` helper replaces duplicated graph-page-vs-panel lookup in `flushCache` + `rebuildGraph`
- `2a03300` M7 — Split `buildToolbar` → `buildFilterChips` + `buildActionChips`, with separate `makeFilterChip` / `makeActionChip` factories (filter chips need `aria-pressed` toggle; action chips are one-shot — different semantics deserved different builders)
- `2046490` M8 — Document garden-UI z-index scale in §24 header: 1 (resize handle) → 5 (path log) → 10 (essay sidenote popover) → 20 (graph panel). Round-5 convention for headroom.
- `3fcb36f` M9 — Guard `.garden-note-title` lookup in `updatePathLog`: fall back to slug if title element missing
- `009a028` M10 — Drop `aria-hidden="true"` on `.garden-graph-panel-legend`; the legend is the only place the visual encoding (color/size/solid/dashed) is spelled out, so SR users need it (the SVG `<desc>` just gives counts)

**Source of the list:** the prior memory `project_phase_4_status.md` mentioned "M1-M9: minor stylistic items (palette comment, button-order privacy nudge, listener delegation on graph nodes, etc.)" but the actual list wasn't in files. I spawned a `superpowers:code-reviewer` agent with the three known anchors as sanity checks; it returned 10 items including all three originals. Verified two (M9 unguarded `.textContent`, M10 `aria-hidden`) by spot-grep before acting to make sure they were real.

**Why:** Closes out Phase 4 entirely. No remaining known follow-ups from the slice or its post-merge fix batch.

**How to apply:**
- For UI features with both filter-toggle chips and one-shot action chips, give them separate constructors. They look similar but have different ARIA semantics — the `.chip-action` italic hack was the original signal that `buildToolbar` was conflating concerns.
- Privacy-first consent UX: ordering matters. Default focus/reading-order should land on the most privacy-preserving choice. Not just a stylistic nit — it's the difference between consent and dark-pattern.
- Don't catch-and-swallow JSON parse alongside storage access — they're different failure modes. JSON corruption is unexpected and worth logging + clearing; `SecurityError` on private-browsing-strict is expected and should stay silent.

**Pointers:**
- Merge commit: `7403df8` on master
- No spec/plan — pulled from code-reviewer pass; items recorded here in case any need to be revisited
