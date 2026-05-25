---
name: works-umbrella-polish-slice-merged
description: Phase 6 Slice 0 — Bento umbrella + force-directed constellation + three medium glyphs; merged 2026-05-12
metadata: 
  node_type: memory
  type: project
  originSessionId: aa1fdad1-d521-460c-8929-906ba6d65966
---

Phase 6 Slice 0 shipped to master 2026-05-12 (merge `3309247`, pushed to origin). `/works/` rebuilt as Bento variable-tile grid (12 tiles, sizes via `tile_size`/`featured`/`hero` frontmatter) + tag-cloud filter + medium chips + ⊞ Graph view toggle showing a force-directed constellation of every work. Edges: tag-share (solid) + cross-medium ref (dashed; `lyrics_poem ↔ set_to_music`). Standalone `/works/graph/` mirrors the panel as mobile fallback.

Three hand-authored medium glyphs (`glyph-game.svg` / `glyph-music.svg` / `glyph-poetry.svg`) ship once via `partials/works/glyph-sprite.html`; they feed both Bento tiles and graph nodes, and the future Phase 7 homepage Studio strip is now unblocked.

Works JS bundle split: `entry-works-umbrella.js` (~113 KB w/ d3) loads only on `/works/` + `/works/graph/`; `entry-works.js` (~4 KB) stays on per-item pages. Per-item performance unaffected by the d3 dependency.

Linter extensions: `check_works_fixtures` accepts `tile_size`/`featured`/`hero`; `check_filter_chips_config` gains `SECTION_AGGREGATIONS` so the `works` key resolves tag pool across games + music + poetry sub-sections. New `data/filter-chips.yaml` entry for works. Spec: `docs/superpowers/specs/2026-05-12-works-umbrella-polish-design.md`. Plan: `docs/superpowers/plans/2026-05-12-works-umbrella-polish.md`.

**Post-spot-check fixes folded into the slice (3 distinct commits in addition to the 18 plan-task commits):**

- Graph engine tuning: smaller node badges (52/72 → 36/48), wider force spacing (collide radius half-badge + 38 instead of +4; charge −700; link distance 160). Shift+drag opt-in pin applied to all three force-directed graphs (works/garden/research) — plain drag now releases on drop; holding Shift pins. Toolbar gesture hint added.
- Filter-chip plurality fix: top-strip medium chips were emitting plural data-keys ("games") that didn't match singular tile attributes ("game"). Singular everywhere now; `filter-chips.html` gained an optional `labels` map per dim so the umbrella can render "Games" while keeping data-key "game". Backwards-compatible — all existing callers unaffected.
- Production minify bug: original graph-data partial called `jsonify` internally then `safeJS`, while graph-script re-wrapped in `safeJS`. The HTML serializer escaped quotes inside `<script type="application/json">`, breaking the minifier. Refactored to research-graph's pattern: data partial `return`s a Hugo dict; script partial `jsonify | safeJS` at the embed point.
- See [[reference_filter_chips_data_tags_space_delimited]] — `data-tags` contract gotcha discovered during spot-check (4 works templates were comma-delimited, silently breaking every tag chip match; now space-delimited).

Memory: `Always offer dev-server spot-check before merging` — spot-check happened, merge happened, push authorized and complete. GitHub Pages will redeploy from this commit.
