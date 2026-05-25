---
name: Citation hover-card slice — merged
description: Phase 3 first Hugo-side slice (citation runtime + linter) shipped 2026-05-12; closes the Phase 3 citation deliverable, Now widget still elisp-blocked
type: project
originSessionId: a1cf2d3b-0e81-4672-8dfa-5d3f70e10716
---
Phase 3 first Hugo-side slice. Shipped to master 2026-05-12 (merge `abe7f1a`, pushed to origin; range `a6654d2..abe7f1a`).

**What shipped:**
- `assets/js/citation-card.js` — singleton hover-card runtime (~2.7 KB added to the essay bundle, total `essay.<hash>.js` is now 7.5 KB up from 4.8 KB). Page-scoped to `/essays/`.
- DOM-clone data path: card content cloned from the server-rendered `<li id="ref-KEY">` in the references list. No JSON blob, single source of truth.
- Mobile (≤720px) two-tap semantics: first tap opens bottom sheet, second tap on same citation passes through to references jump (preserving the `:target` highlight). Desktop hover/focus/Esc unchanged.
- `essay-references.html` partial now emits a `related note` link when `notes_ref` is set (closes the only unused field on the citation shape). Fixture `example-source-2.notes_ref` repointed from dangling `example-note-slug` → `story-atoms`.
- New CI gate `tools/check_citations.py` (~140 LOC stdlib-only) validates citation shape + resolves `notes_ref` against the garden tree. 16-test unit suite. Closes the only un-linted data file in the repo. Total Python gates: 13 → 15.
- CSS §13 gained a hover-card subsection (~55 lines, uses existing AAA tokens, no new contrast pairings).

**Spec + plan:**
- `docs/superpowers/specs/2026-05-12-citation-hover-card-design.md`
- `docs/superpowers/plans/2026-05-12-citation-hover-card.md`

**Post-merge QA fix (committed mid-walkthrough):** dropped the `→ ` arrow prefix from `source` and `related note` links — visual noise inside the cloned card. (Commit `e8eb5fb`.)

**Why:** Mark Phase 3 progress and the new data linter for future cross-reference. Phase 3's remaining piece — Now widget — is still blocked on the user's elisp/ox-hugo pipeline.

**How to apply:** When citing the slice in future status updates, refer to it as "Phase 3 citation slice (2026-05-12, `abe7f1a`)". When discussing un-linted data files, note there are none left as of 2026-05-12.
