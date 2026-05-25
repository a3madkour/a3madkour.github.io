---
name: project-phase-3-two-publish-commands
description: "Phase 3 (org-mode pipeline) must expose two separate publish commands — one for living surfaces (garden/library/research), one for essays"
metadata: 
  node_type: memory
  type: project
  originSessionId: d27b9186-f371-40e9-ac80-f9b1a00cfcff
---

When Phase 3 (org-mode pipeline) is picked up, the elisp + ox-hugo work must produce **two separate publishing commands**, not a single monolithic export:

1. **Garden / Library / Research publish** (frequent, idempotent, fast): exports the "living" surfaces — garden notes, library yaml (`data/{reading,listening,playing,watching}.yaml`), research themes + questions, plus `data/notes.json` for the graph. Meant to run on a regular cadence (daily, hourly, or on save) without ceremony. Must be safe to invoke repeatedly with no diff when nothing changed.

2. **Essay publish** (per-post, deliberate): exports a single essay subtree (or all essays) including its assets — hero illustration, figures, sidenotes, citations, series nav. Treated as a publishing event, not a continuous-export workflow. Output reviewed before commit.

Both share underlying ox-hugo + elisp helpers; they differ in the selector (which org subtrees) + intended invocation frequency.

**Why:** Added to spec §14 Phase 3 in 2026-05-13 (commit `b88a178`) at the user's explicit request: "for the org-mode pipeline add the requirement that there should be a separate command for publishing the garden/library/research, which can be updated regularly, and publishing an essay". The user wants Phase 3 to anticipate the operational cadence — frequent updates to garden/library/research shouldn't require the friction of an essay-style publish flow, and essays shouldn't be exposed to the risk of an automatic frequent-run pipeline.

**How to apply:** When brainstorming the Phase 3 slice (or the first slice that touches the elisp pipeline), surface this requirement up front — the elisp commands' names, scopes, and invocation patterns should match the two-command split. Don't merge them into a single "publish everything" command.

See also: spec `docs/superpowers/specs/2026-05-03-personal-site-design.md` §14 Phase 3, CLAUDE.md "Not started" → "Phase 3 — org-mode pipeline" note.
