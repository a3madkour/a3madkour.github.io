---
name: project-phase-3-org-synced-poetry-export
description: "Queued stub: Phase 3 Essay/poetry publish must emit the shipped synced-poetry [mm:ss] markup contract"
metadata: 
  node_type: memory
  type: project
  originSessionId: f5bcea34-8124-4ba8-a918-fcf90b93b5af
---

Queued stub filed 2026-05-19 (commit `2bdf093`): `docs/superpowers/specs/2026-05-19-org-synced-poetry-export.md`. **Stub only — no plan; do NOT brainstorm until scheduled** (per [[feedback-file-for-another-slice-means-stub]]).

When Phase 3 reaches the **Essay/poetry publish** command, its output must emit the markup contract the already-shipped synced-poetry runtime consumes (no new runtime work): canonical `[mm:ss]`/`[mm:ss.f]` body markers (zero-padded), line-start vs whitespace-glued placement, backslash-escaped `\[mm:ss]` for literal bracket text, optional `audio_url` frontmatter (bundle-relative or absolute), clean `summary:`; output must pass `tools/check_poetry_synced.py` + `tools/check_works_fixtures.py`. Rides the per-post Essay publish, NOT the frequent garden/library/research publish — sits alongside [[project-phase-3-two-publish-commands]] and [[project-phase-3-library-tag-shelves]]. Hard dep: Phase 3 Slice 1/2 (the elisp+ox-hugo path) must exist first.

Genuinely-open question for the eventual brainstorm (deliberately unresolved): how the author annotates timing in **org** so ox-hugo emits the markers, and how `audio_url`/the audio asset are declared+carried into the page bundle. Consuming runtime: [[project-time-synced-poetry-slice]].
