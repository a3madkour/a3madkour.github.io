---
name: project-persistent-graph-access-slice
description: Persistent graph access (research+works) slice — shipped + pushed 2026-05-18 (merge 3321541)
metadata: 
  node_type: memory
  type: project
  originSessionId: d2c8ba83-4c2f-42d9-9eef-24419825f6e3
---

Persistent-graph-access slice merged to master 2026-05-18, merge `3321541`,
pushed (`c56077e..3321541`). Closes the queued persistent-graph-access stub.
Spec `docs/superpowers/specs/2026-05-16-persistent-graph-access-design.md`,
plan `docs/superpowers/plans/2026-05-18-persistent-graph-access.md`.

**Scope shipped:** new shared `layouts/partials/graph-launcher-bar.html`
(variant-switched: `garden` reproduces path-log DOM verbatim; `generic` =
breadcrumb + `data-graph-current` for research/works). Sticky bar + section
graph-panel + graph-script now on all 5 item layouts (research-theme/-question,
works-games/-music/-poetry) so the graph survives node-click traversal like
garden. Garden `path-log.html` delegates to the shared partial (launcher
relocated right→left, fixes panel-covers-launcher). `.graph-launcher-bar` shell
migrated §24→§27; `is-here` current-node CSS+JS on research/works only (garden
keeps its `in-stack` model). Bundle predicates widened (d3 on item pages —
`eq .Section "research"`; works singles get `entry-works-umbrella.js`).
`check_graph_chrome.py` extended (now `6 graph + 5 item surfaces`).

**Executed subagent-driven, 9 tasks, two-stage reviewed.** Review loop caught
real defects (the valuable part):
- Task 1 review → plan defect: relocating launcher would let `garden-stack.js`
  `updatePathLog()` prune it + break `check_garden_history.py`. Folded into
  Task 2 as Fix A (keep-set guard `child !== toggle`) + Fix B (linter + paired
  test retargeted to `graph-launcher-bar.html` where the `/garden/history/`
  link now lives).
- Task 9 LHCI caught a **real a11y regression**: `research/graph-panel.html`
  lacked `inert` (garden's has it; `research-graph.js` already round-trips it)
  → accessibility 0.89<0.90 on the two LHCI-tested research item pages. Fixed
  by adding `inert` (research only; works panel uses `hidden`, intentionally
  not unified). Re-verified ≥0.90 via LHCI re-run.
- Step-4 spot-check (user) caught: `.graph-toggle` too chunky (slimmed padding
  `0.28rem 0.7rem`→`0.12rem 0.5rem`, single canonical rule) and broken works
  graph-node icons → see [[reference_works_graph_panel_needs_glyph_sprite]].
- Orphaned `.research-breadcrumb` CSS removed (slice created the orphan).

**LHCI note (RESOLVED):** local ci-local exited 1 ONLY on LHCI mobile
`/garden/` perf ≈0.83<0.90 (umbrella). Confirmed pure local-CPU variance —
**GitHub Actions run 26073239774 on merge `3321541` completed `success`**
(full 51-step pipeline incl. LHCI desktop+mobile on consistent hardware). NOT
this slice (`/garden/` umbrella HTML byte-identical master→branch; garden
bundle +42 B dead-on-that-page; page-weight gate green). Same documented
pre-existing local variance as [[project_graph_view_chrome_consistency_slice]]
/ [[reference_ci_local_lhci_deps]]; CI hardware authoritative. Closed — do not
re-investigate.

**Discovered pre-existing, deferred (recorded in spec "Discovered pre-existing
issues"):** `.tile-meta` color-contrast on research item pages (separate
ticket); graph-panel closed-state mechanism divergence (research/garden
`aria-hidden+inert` vs works `hidden`) — both out of scope.

Page-weight headroom confirmed concretely: new d3-bearing item pages 37–47%
of budget (peak `/works/music/*` 46.6% of 500 KB). Followed
[[feedback_verify_before_merge]] + [[feedback_always_run_ci_locally]].
