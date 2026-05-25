---
name: project-phase-3-library-tag-shelves
description: "Phase 3 library-publish command must round-trip org-mode item tags into data/<medium>.yaml's per-item `tags:` list; shelves themselves stay hand-authored in library-shelves.yaml"
metadata: 
  node_type: memory
  type: project
  originSessionId: e54ad22c-8c11-4afb-8360-ad0b334d6968
---

The library umbrella's tag-driven shelves mechanism is already wired on the Hugo side (see `layouts/partials/library/umbrella-shelf.html` + `data/library-shelves.yaml`). A shelf entry with `tag: <name>` filters items across all four medium yamls (`data/{reading,listening,playing,watching}.yaml`) whose `tags:` array contains that tag.

**Why:** User asked to "add to the ox-hugo export pipeline a way to specify tags that act as shelves" during the library-redesign slice (2026-05-14). The pipeline doesn't exist yet (Phase 3 not started), but the requirement needs to round-trip when it does. Captured in `docs/superpowers/specs/2026-05-14-library-redesign-design.md` §11.5.

**How to apply (when Phase 3 library-publish slice is drafted):**

- The publish writer must extract org-mode tags (mechanism TBD: `#+filetags:` vs per-heading `:tags:` — Phase 3 spec picks one) and emit them as `tags: [...]` in each item entry under `data/<medium>.yaml`.
- `data/library-shelves.yaml` stays hand-authored. Shelves are a *curation* decision (small editorial act); the pipeline does NOT auto-generate shelves from tags. Authors add shelf entries by hand to surface a tag.
- Existing linter `tools/check_library_shelves.py` gates this: a shelf resolving to zero items fails the build, so mis-spelled tags or empty tag sets are caught at CI.
- Split rationale: *what's in the library* should be idempotent and frequent (no human review per publish); *how it's surfaced* should be deliberate (a shelf is editorial). Matches the two-publish-command shape in [[project-phase-3-two-publish-commands]].

Linker: [[project-phase-3-two-publish-commands]], [[project-library-section-slice]], [[project-library-redesign-slice]] (pending — slice not yet merged).
