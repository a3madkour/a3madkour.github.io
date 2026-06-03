---
name: next-slice
description: "Session-start pointer — D.2 multi-target export SPEC SHIPPED 2026-06-02 (commit c05b46c; see [[d2-spec-queued]]); plan queued. Choose next: (a) D.2 implementation (plan + ship), (b) LHCI 4.1 representative-pages validator (queued ~1h slice), (c) Emacs publish-author helpers (no spec yet), (d) E (explorable explainables; per phase order after D.2). User picks at session start."
metadata: 
  node_type: memory
  type: project
  originSessionId: 6e8aa45d-e277-4939-bd42-732f52c1c0ff
---

**Pick next slice at session start.** D.2 spec shipped; per [[design-batch-no-plan-until-implement]], plan drafting waits until implementation begins.

## Queued slices

### (a) D.2 implementation — plan + ship

- Spec: `docs/superpowers/specs/2026-06-02-phase-3-d2-multi-target-export-design.md` (commit `c05b46c`).
- Per the phase order ([[phase-3-decomposition]]), D.2 is the immediate next slice; E follows.
- Estimate: ~7 days focused work. Highest-novelty piece is the pandoc Lua filter for stateful theorem-family numbering pass (~2d, own subagent task).
- Tool deps: `xelatex`, `biber`, `rsvg-convert`, `pandoc` on author machine (CI does NOT run them).
- See [[d2-spec-queued]] for full architecture summary, pre-implementation reads, risks.

### (b) LHCI 4.1 representative-pages validator (~1h slice)

- Stub spec: `docs/superpowers/specs/2026-06-01-lhci-representative-page-set-design.md`.
- Filed after B.4 push triggered 2 LHCI 404 round-trips from drifted fixture slugs. Ship 4.1 validator first (fast-fails drift); 4.2 sitemap-derived + 4.3 visual-feature autodetect are later phases.
- See [[lhci-representative-pages-queued]].

### (c) Emacs publish-author helpers

- No spec; no plan. Brainstorm fresh when scheduled.
- Sketched 2026-05-30 while seeding library scaffolds. Dotfiles-side ergonomics: interactive commands to mark notes for publish + insert library-item drawer scaffolds + dry-run preview, instead of hand-editing headers/drawers.
- See [[emacs-publish-helpers-followup]].

### (d) Sub-project E (explorable explainables)

- Per phase order ([[phase-3-decomposition]]), E follows D after D.2 ships.
- No spec; no plan. Big design surface: per-page interactive widgets + per-page JS bundle convention + cross-format degradation (PDF/Word fall back to screenshots + URL caption).
- D.2's spec §12 already lays a forward-compat hook (PDF + Word backends skip explorable blocks via `:explorable:` class).

## Recommended sequencing

Strict phase order says D.2 → E. Pragmatic deviations:
- If a real paper or report is coming up that needs PDF/Word: **D.2 implementation first**.
- If LHCI 404s have become a recurring footgun: **4.1 validator first** (~1h, unblocks confident publishing of new B-emitted slugs).
- If you're about to do a publish/library-scaffold session in Emacs and the hand-editing is grating: **(c) Emacs helpers first**.

Each of these is a separable spec → plan → ship cycle. Don't fuse.

## State of the world at session start

**Site (`~/Sync/Workspace/a3madkour.github.io/`):**
- `master` at `c05b46c` (D.2 spec). All earlier work pushed.
- 481 ert tests + 7 site check_math tests passing.

**Dotfiles (`~/dotfiles/`):**
- `main` at `a6336f3` (D.1 T6 ox-hugo config). All pushed.
- 5 pre-existing dirty tracked files (`.gitignore`, `.zshrc`, `bookmarks`, `early-init.el`, `init.el`) — author's in-progress local work, NEVER commit them.
- `org-math-lint` venv at `~/org/notes/tools/org-math-lint/.venv/` may still be broken (cross-platform mismatch from C-era). Pre-existing issue; recreate if math validation gate is needed. See [[reference-org-math-lint-venv-platform]].

**Personal notes (`~/org/`):**
- Unchanged since end of F.
