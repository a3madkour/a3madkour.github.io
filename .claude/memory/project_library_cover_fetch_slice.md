---
name: project-library-cover-fetch-slice
description: "Phase 7 Slice 1 — library cover-fetch infra shipped 2026-05-12 (merge cbd00fd, pushed to origin). Adds extras cover keys, fetch script, 12th linter pair, Hugo img template, fair-use posture"
metadata: 
  node_type: memory
  type: project
  originSessionId: db5fa043-88a8-4e7d-9bf8-a4f6d451bda4
---

Phase 7 Slice 1 — library cover-fetch infrastructure — shipped 2026-05-12 via merge `cbd00fd` to master (pushed to origin).

**Why:** Library section shipped glyph-only thumbnails (Phase 7 Slice 0); covers add the scanning anchor real cover art provides on lists like Letterboxd/Goodreads/Backloggd.

**How to apply:** When real library content lands via the Phase 3 elisp pipeline, the cover infra round-trips — author adds `extras.cover_url` / `isbn` / etc. to each org-roam media note, runs `tools/fetch_library_covers.py`, and covers appear via the existing Hugo template.

What landed (17 tasks, 21+ commits + the merge):
- Data: `extras.cover_file` / `cover_url` / `isbn` / `musicbrainz_release_group` / `igdb_id` / `tmdb_id` keys (media-type-scoped).
- 8 PD/fair-use thumbnail covers (~588 KB total) via Wikimedia /thumb/ URLs — Wizard of Oz, Pride & Prejudice, Brandenburg, Entertainer, Hades, Celeste, The General, Nosferatu.
- `tools/fetch_library_covers.py` (~255 lines, stdlib-only): cover_file / cover_url / isbn (Open Library) / mbid (Cover Art Archive) live; IGDB + TMDB raise NotImplementedError (deferred to a future slice with real items + API keys). `tools/.cover-cache.json` audit log with sha256s.
- 12th linter pair `tools/check_library_covers.py` (schema fail + cache/audit/freshness warn). CI runs both.
- Hugo template: `partials/library/type-glyph.html` renders `<img>` when cover cached, glyph fallback otherwise. CSS §37 per-section aspect — listening leaf square (44×44 / 56×56) via existing `[data-library-page="listening"]`, others portrait (44×56 / 56×72).
- Footer colophon line: fair-use credit for Open Library / Cover Art Archive / IGDB / TMDB.
- CLAUDE.md: 11→12 linter pairs, 23→25 verification steps, deferred-features table updated.

Spec: `docs/superpowers/specs/2026-05-12-library-cover-fetch-design.md` (supersedes the deleted sketch).
Plan: `docs/superpowers/plans/2026-05-12-library-cover-fetch.md`.

Final code reviewer flagged 2 non-blocking polish items: schema validation duplicated between `check_library_fixtures.py` + `check_library_covers.py`; main loop only catches `NotImplementedError` (broader exceptions could lose audit data). Both can land in a future polish slice.

Related: [[project_library_section_slice]] (Phase 7 Slice 0, the parent slice).
