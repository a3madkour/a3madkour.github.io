---
name: remaining-work-proceeds-in-phase-order
description: "When picking the next slice for the personal site, work through the remaining phases in numeric order rather than cherry-picking"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ec310218-1708-418e-b53d-565a7a9baa4e
---

Remaining site work proceeds in phase order (Phase 3 → 6 → 7 → 8), not cherry-picked by interest or unblocked-ness.

**Why:** User stated 2026-05-12 right after the citation hover-card slice merged. The phase list in [[CLAUDE.md]] §14 is the master ordering and should be honored linearly — even when later phases (Works, Library) are unblocked and earlier phases (Phase 3 org-mode pipeline, About-page Now widget) have external dependencies.

**How to apply:** When asked "what's next" or kicking off a new slice, propose work from the lowest-numbered incomplete phase first. If that phase is blocked (e.g. Phase 3 elisp/ox-hugo on user's side), surface the block explicitly and wait — do not skip ahead to Phase 6/7/8 unless the user authorizes the skip. Phase status as of 2026-05-12:

- Phase 3 — org-mode pipeline (elisp + ox-hugo). Citation hover-card runtime slice shipped Hugo-side ([[project_citation_hover_card_slice]]); About-page Now widget + actual content wiring still pending on user's elisp work.
- Phase 6 — Works (games / music / poetry)
- Phase 7 — Library + Homepage v3 final assembly
- Phase 8 — Pagefind + Lighthouse CI + final QA
