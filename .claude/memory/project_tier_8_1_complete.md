---
name: tier-8-1-complete
description: "Tier 8.1 (sub-project E — explorables) shipped 2026-06-12; runtime + 2 library kinds + 28th linter pair + CSS §49 + fixture"
metadata:
  node_type: memory
  type: project
---

**Shipped 2026-06-12.** Sub-project E (Phase 3 final piece per [[project-phase-3-decomposition]]); Tier 8.1 of the polish/bugfix roadmap.

Site commits: `99f6bb5..5e3d5d2` (15 commits: spec + plan + 13 implementation).

What landed end-to-end:

- Runtime `assets/js/explorables/runtime.js` — `registerWidget(id, fn)` + DOMContentLoaded sweep + per-widget try/catch isolation.
- Two library widget classes in `assets/js/explorables/lib/`: `ReactiveValue` (sliders → reactive text) and `ReactiveChart` (sliders → hand-rolled SVG plot, no d3). Shared `_base.js` helpers (clamp, scale, buildControls).
- Per-essay JS bundle convention: each essay with `has_widgets: true` triggers a dynamic `js.Build` call in `layouts/partials/scripts.html` against `assets/js/explorables/<slug>/index.js`. Output `explorables-<slug>.<hash>.js`, page-narrow (13th bundle row in CLAUDE.md table).
- Shortcode `{{< widget id="..." [label="..."] >}}` upgraded from 1-line stub to server-rendered no-JS caption + mount target with `role="figure"` + `aria-label`.
- CSS §49 — ~30 selectors covering chrome, slider cross-browser (webkit + moz prefix pairs), focus ring, fallback caption. No new color tokens.
- 28th linter pair (`tools/check_explorables.py` + `tools/test_check_explorables.py`) — 6 coupling rules: has_widgets↔shortcode presence, id attribute required, id unique per page, per-essay JS file exists, registerWidget covers all ids, no orphan registerWidget. 15 unit tests.
- New fixture `content/essays/example-explorables/` with 3 widgets (ReactiveValue + ReactiveChart + bespoke canvas).
- Migrated `content/essays/example-one/` from legacy `src=` attribute to `id=` shortcode; added minimal per-essay JS.
- Smoke test extended to GET `/essays/example-explorables/` and assert 3 `data-widget-id` attrs + the per-essay `<script>` tag.

Spec: `docs/superpowers/specs/2026-06-12-sub-project-e-explorables-design.md`.
Plan: `docs/superpowers/plans/2026-06-12-sub-project-e-explorables.md`.

**Follow-ups (queued in spec §10):**
1. Org-side authoring (`#+begin_explorable` block in ox-hugo handler) — trigger: first real explorable essay needs export.
2. Step-through animator (3rd library kind).
3. Multi-series ReactiveChart.
4. Static-screenshot fallback for PDF/Word.
5. ReactiveChart screen-reader text alternative.
6. Runtime split into shared bundle (when N>3 widget-bearing essays exist).
7. Cross-widget state coordination.
8. Render-time browserless paint check.
