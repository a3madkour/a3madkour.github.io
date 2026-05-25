---
name: library-covers-static-path
description: "Library cover images live at `static/library/covers/<slug>.jpg`, referenced via `extras.cover_file: <slug>.jpg` in per-medium YAML. Hotlinking via `cover_url` is forbidden — it trips LHCI third-party-cookies (Wikipedia sets WMF-Uniq cookie on every image fetch)."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 0e7723e4-90d0-47b3-abbf-e45eb1d38a69
---

**Canonical path:** `static/library/covers/<slug>.jpg` — served at `/library/covers/<slug>.jpg`.

**Schema:** Library YAML entries opt into a cover via `extras.cover_file: "<slug>.jpg"`. The three consuming templates resolve it in this order:

- `layouts/partials/library/umbrella-tile.html` — catalogue tile (umbrella + shelf detail pages); direct `<img src="/library/covers/{file}">`.
- `layouts/partials/library/umbrella-hero.html` — featured hero on the umbrella; same.
- `layouts/partials/library/type-glyph.html` — leaf rows + Currently widget; uses `fileExists` to guard `<slug>.jpg` slug-fallback before emitting the `<img>`. Falls back to a Lucide glyph (book / clapper / gamepad / music) when no cover file exists.

**Fetch script:** `tools/fetch_library_covers.py` (stdlib-only; author-driven, not invoked at build time) downloads to `COVERS_DIR = REPO_ROOT / "static" / "library" / "covers"`. Audit log at `tools/.cover-cache.json` records source URL + sha256 + fetched-at; `tools/check_library_covers.py` validates schema + cache coverage + audit consistency.

**Why static/ not assets/:**

Migrated 2026-05-14 from `assets/images/library/covers/` to `static/library/covers/` after the library-redesign merge tripped LHCI on `/library/` best-practices = 0.74. The umbrella + hero templates emit raw `/library/covers/` paths; without files served from `static/`, the chain fell back to `extras.cover_url: <Wikipedia URL>`, which:

1. Failed `third-party-cookies` audit — Wikipedia's `upload.wikimedia.org` sets `WMF-Uniq` cookie on every image response.
2. Failed `inspector-issues` audit — same cookies surface via Chrome DevTools Issues panel.

**Never reintroduce `cover_url:`** in YAML for hotlinked sources. Acceptable use of `cover_url:` is fetch-time only — the fetch script reads it, downloads, writes the file, and the YAML should then carry `cover_file:` instead.

**Page weight implications:**

Self-hosted covers count toward local image weight (vs hotlinks which the linter doesn't measure). 8 fixture covers total ~580 KB on disk. `/library/` and `/library/<leaf>/` budgets bumped to 900 KB to accommodate. When Phase 3 library-publish elisp lands and item count grows, expect to need either (a) further budget bumps, (b) image optimization pass (target 50–60 KB/cover via JPEG quality 75 or WebP), or (c) lazy-load offscreen tiles.

See also: [[ci-local-lhci-deps]] for how LHCI catches third-party-cookie regressions, [[always-run-ci-locally-before-pushing]] for the script that owns the gate.
