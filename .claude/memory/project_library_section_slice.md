---
name: library-section-slice-merged
description: "Phase 7 first slice (umbrella + 4 list pages, 2 linter pairs, fixture-shaped data/*.yaml) shipped 2026-05-12 (merge `eb3d64b`); origin push pending"
metadata: 
  node_type: memory
  type: project
  originSessionId: b7a63097-5f77-48c0-9993-042044e52f1b
---

Phase 7 Slice 0 — `/library/` section. Merged to master 2026-05-12 as `eb3d64b` (`slice/library-section`, 38 commits + the merge commit).

**Why:** Consumption-side counterpart to works. Reading / listening / playing / watching surfaces filtered from media-flavor garden notes via `data/*.yaml` (fixture round-trip; elisp pipeline will overwrite when Phase 3 lands).

**How to apply:** When the next slice touches library: data contract is at `data/{reading,listening,playing,watching}.yaml` per spec §10.4; layouts split by `cascade.type` into `layouts/library-{reading,listening,playing,watching}/list.html` (NOT `layouts/library/<page>/list.html` — that was a plan typo, the implementer corrected it). Two linter pairs (`check_library_fixtures.py` + `check_library_links.py`) gate fixture shape + cross-link resolution. Filter chip dim keys must match the row's `data-*` attributes (e.g., dim `media-type` matches `data-media-type` on rows; dim `format` does NOT — caught by code review post-implementation). Glyph blocks tint per medium (book burgundy, music steel, game evergreen, watching violet — `--color-violet` is glyph-only, doesn't enter `tools/check-contrast.py` audited pairings).

**Spot-check loop surfaced two real fixes** post-implementation:
- Arrow-prefix on row links (`→ my notes` / `→ original`) violated [[feedback_no_arrow_prefix_on_links]] — caught by user during dev-server check, fixed in 815428c. Garden's `original-link` had the same lapse, fixed in d0f096d.
- Format chip dim key was `format` but rows emitted `data-media-type` (silently broken) — caught by [[superpowers:code-reviewer]] in final whole-branch review, fixed in 2bc72c0 along with up-next sort-by-last_modified-desc + tag-rank double-sort + redundant hidden-div removal.

**Companion sketch landed:** `docs/superpowers/specs/2026-05-12-library-cover-fetch-sketch.md` — pre-brainstorm placeholder for the future cover-fetch slice (Open Library / TMDB / IGDB / MusicBrainz APIs, build-time fetch script with local cache).

**Push status:** pushed to origin 2026-05-12 (`671e195..eb3d64b`).
