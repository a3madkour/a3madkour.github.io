---
name: project_authoring_infra_roadmap
description: "2026-10-15 approved roadmap for remaining authoring infra: S1 dogfood run (queue head) → S2 fixes → re-plan → S3–S6 B1 → S7 guide; A2 streams trigger-gated."
metadata:
  type: project
---

Spec: `docs/superpowers/specs/2026-10-15-authoring-infra-roadmap.md` (commit `1cd518f`),
approved by the user 2026-10-15. Supersedes the A1 → A2 → B1 → C order in
[[project_authoring_surface_audit]].

**Queue head: S1, a dogfood run** over every handled section (garden, library ×4, research,
essays, poetry, games, music), producing a friction log. It closes A1 T12
([[project_works_handlers_slice]]) — that part modifies real org files, so get consent at the
time. No plan document for S1; it is a run, not a build.

Decisions taken in the brainstorm:
- B1 before A2: the user is not streaming yet; A2 waits on "first real stream scheduled".
- B1 split by kind: prose pages (about, homepage hero, section intros) get an org source +
  handler (B1a); structural `_index.md` + 4 curated YAML get direct-edit commands (B1b).
- The guide (C) ships after B1 and before A2; its streams page is rewritten when A2 lands.
- Re-plan checkpoint after S2 — reorder if the friction log says B1 is not the biggest problem.
- Recipes excluded ([[project_recipe_hiatus]]).

**Why:** everything but garden has only ever run on fixtures; A1 showed green unit tests miss
what a real run finds.

**How to apply:** S1 is prepared: open `docs/superpowers/specs/2026-10-15-dogfood-friction-log.md`
and work its §1 prerequisites checklist, then §3's per-section candidates (user picks notes). Update the spec's status table at the end of each session.
