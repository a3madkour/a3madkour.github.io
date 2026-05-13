# Library cover fetch pipeline — design sketch

**Date**: 2026-05-12
**Phase**: 7 (library polish, post-elisp)
**Status**: SKETCH — pre-brainstorm placeholder; not approved, not planned
**Companion to**: `docs/superpowers/specs/2026-05-12-library-section-design.md` (parent slice; deferred covers explicitly per its §2)
**Inherits constraints from**: parent spec §1 (no AI art, accessibility, fixture-only content for shape-testing)

---

## 1. Motivation

The library section ships with hand-authored type glyphs (book / clapper / gamepad / eighth-note) standing in for cover art. That's deliberately minimal — it works at any scale and never goes stale, but it loses the scanning anchor that real cover art provides on lists like Letterboxd / Goodreads / Backloggd. Once the library has 50+ entries per leaf, the rows start to feel uniform.

Real cover art is publisher artwork, not AI-generated, so the parent spec's no-AI rule does NOT block it. The blocker has been "where do covers come from" — an asset pipeline question rather than an aesthetic one.

This sketch enumerates the realistic paths so the next maintainer can pick one without re-deriving the option space.

## 2. Scope (when this slice lands)

**In scope:**

- A way for each library item to have an associated cover image, sourced (a) from a metadata API by ID, (b) from a hand-authored URL, or (c) from a local file the author placed in `assets/images/library/covers/`.
- Cached covers committed to repo (git-lfs OR plain — see §6) so production builds don't depend on third-party uptime.
- Hugo template integration: `partials/library/type-glyph.html` extended to render `<img>` when a cover is available, falling back to the existing tinted-block + glyph when not.
- A linter step verifying every row that declares a cover identifier resolves to a cached file (or warns if the file is missing).
- One refresh script (`tools/fetch_library_covers.py`) that reads the yaml, hits the right API per `media_type`, downloads new covers, and updates the cache. Run on demand by the author, not on every build.

**Out of scope:**

- Live API hits during Hugo builds (rate-limit risk, build slowness, third-party flakiness).
- Cover art for `garden/` media-flavor notes (separate surface; can borrow from the same cache later).
- Cover-credit attribution UI (the publisher imprint is already on the row meta line; full credit can be a future mouseover).
- Search by cover.
- AI-generated covers — explicitly forbidden per parent §1.

## 3. Per-medium API options

| Medium      | Source                          | Identifier needed     | API key |
|---|---|---|---|
| `book`      | Open Library Covers API         | ISBN-10 or ISBN-13     | none    |
| `album`/`track` | MusicBrainz + Cover Art Archive | MBID (release-group)  | none (UA header required) |
| `game`      | IGDB (Twitch)                   | IGDB ID               | yes (Twitch developer key) |
| `film`/`series` | TMDB                       | TMDB ID               | yes (free tier, account signup) |

Open Library + Cover Art Archive are key-free; IGDB + TMDB require accounts. The author can opt out of API-keyed sources by leaving those identifier fields empty (rows fall back to glyph).

## 4. Yaml data shape additions (per `data/{reading,listening,playing,watching}.yaml`)

Append to the `extras` block (already type-specific per parent §3.6):

```yaml
extras:
  # existing keys (book): progress_pct, progress_label
  isbn: "9780156453806"           # book — Open Library lookup key

  # existing keys (album/track): (none)
  musicbrainz_release_group: "..." # album/track — MBID

  # existing keys (game): hours_played, platform
  igdb_id: 1942                    # game — IGDB internal id

  # existing keys (film): runtime_min
  # existing keys (series): episode_count, current_episode, current_season
  tmdb_id: 95396                   # film/series — TMDB id

  # universal alternatives (any medium):
  cover_url: "https://..."         # author-provided URL; takes precedence over API-fetched
  cover_file: "lorem-game-iv.jpg"  # local file under assets/images/library/covers/
```

Resolution order at render time:
1. `cover_file` exists in `assets/images/library/covers/` → use it
2. `cover_url` is set → trust the cache (the fetch script downloaded it locally and renamed it `<slug>.jpg`)
3. ID-keyed fields → cached file under `assets/images/library/covers/<slug>.jpg` from a previous fetch
4. None of the above → fall back to current tinted-block + type-glyph

## 5. Fetch script flow

```
tools/fetch_library_covers.py [--medium=book|album|game|film|series|all] [--force]

For each item in data/<page>.yaml:
  determine cache target: assets/images/library/covers/<slug>.<ext>
  if cache hit and not --force: skip
  pick the highest-priority identifier present (cover_url > ID)
  fetch from the appropriate API
  write to cache
  update an audit log: tools/.cover-cache.json (slug → source URL + fetch date)
```

The script is **idempotent** and run on demand by the author after editing yaml. Build never hits external APIs. Failures during fetch are logged but non-fatal — the row falls back to glyph.

## 6. Cache + git strategy

Covers are binary blobs (~30–80 KB each per item). At ~24 fixture items × 4 mediums × thumbnail-size, that's ~1–2 MB total in fixtures, growing with real content. Three storage options:

**A. Plain git** — commit covers under `assets/images/library/covers/`. Simplest. Repo grows linearly with library size; OK for hundreds of items, painful past thousands.

**B. Git LFS** — covers go through git-lfs. Repo stays small; LFS adds a fetch step on every clone. Free tier on GitHub is 1 GB storage / 1 GB bandwidth/month — fine for personal site.

**C. Build-time external fetch** — `.gitignore` the cache dir; CI fetches before Hugo build using the same script. Saves repo size at the cost of build flakiness + a CI secret per API.

Recommendation when this slice lands: **start with A**. Personal site won't hit thousands of items; simplest path; LFS migration later is trivial (`git lfs migrate import --include="assets/images/library/covers/**"`).

## 7. Hugo template integration

Modify `partials/library/type-glyph.html`:

```hugo
{{- $coverPath := printf "images/library/covers/%s.jpg" .slug -}}
{{- $cover := resources.Get $coverPath -}}
{{- if $cover -}}
  <img class="library-cover" src="{{ $cover.RelPermalink }}" alt="" loading="lazy" width="64" height="80" />
{{- else -}}
  {{- /* existing glyph-block fallback */ -}}
{{- end -}}
```

CSS additions to §37 Library:
- `.library-cover { width: 100%; height: 100%; object-fit: cover; border-radius: 3px; }`
- Currently-active card: cover dimensions become 56×72 (matches glyph block)
- Row glyph-mini: 44×56 cover

Lazy-load all covers (`loading="lazy"`) so above-the-fold currently-active cards load eagerly via priority hints if needed; year-section rows defer.

## 8. Linter

New `tools/check_library_covers.py` (sibling test pair):

- For every yaml row with a cover identifier (`isbn`, `tmdb_id`, etc.) OR `cover_file`: verify the cached file exists under `assets/images/library/covers/<slug>.jpg`.
- Warn (don't fail) if a row has an identifier but no cache hit — the author needs to run `fetch_library_covers.py`.
- Validate audit log freshness: warn on entries older than N months (default 12 — covers can change when publishers update artwork).

Wired into CI as a 12th linter pair (would bring the total to 11 → 12 pairs, 23 → 25 verification steps after this slice ships).

## 9. Privacy + rate-limit considerations

- API calls reveal what the author is reading/watching/playing to the API provider. For books (Open Library, no auth) this is benign. For TMDB/IGDB it's tied to the API key, so the provider can correlate. The author should be aware.
- Open Library + Cover Art Archive ask for a User-Agent header identifying the script + an email contact; honor that.
- Rate limits (TMDB: 40 req/10s; IGDB: 4 req/s) — script should sleep between calls when batch-fetching.
- Covers are public publisher artwork; redistribution under fair-use / educational use is generally fine for personal sites. Add a colophon line crediting "Cover art via Open Library, TMDB, IGDB, MusicBrainz" if any covers ship.

## 10. When to run this slice

Reasonable triggers:

1. The library has grown past ~30 real items per leaf and the rows start to look samey.
2. The elisp pipeline lands (Phase 3) — the cover-fetch step can be invoked as part of org-roam node export, keeping yaml + cache regeneration coherent.
3. The author wants to use the library for a specific public surface (e.g., end-of-year roundup post) where covers add scanning value.

Until then: type-glyph fallback is fine. The current `[[reference_filter_chips_data_tags_space_delimited]]`-shaped yaml already accommodates `extras` extensions, so no breaking change to data when this lands.

## 11. Acceptance criteria (for the future slice)

- All 4 yaml schemas accept new `extras` keys without breaking the existing fixtures linter.
- `tools/fetch_library_covers.py` runs against fixtures, downloads at least one cover per medium, and updates the cache + audit log.
- Hugo build serves cached covers when present; falls back to glyph when absent.
- New linter pair gates CI without false positives on the deferred-cover state (rows without identifiers should pass silently).
- One real-world manual run end-to-end on the author's actual library data, with at least 5 covers per medium, before the slice merges.
- CLAUDE.md updated; deferred-features table loses the "cover thumbnails" row.

---

## Appendix: open questions to resolve in brainstorm

1. Currently-active vs row cover: same dimensions or different?
2. Multi-edition books (one work, several covers): which one wins? Let the author pick via `cover_file`?
3. Failed-fetch UX: silent fallback to glyph, or render a "?" placeholder so the author notices?
4. CI: should `tools/check_library_covers.py` run in soft-warn mode forever, or bump to fail-on-stale after some grace period?
5. Should the cache live under `assets/` (Hugo can fingerprint + minify) or `static/` (passthrough)? Probably `assets/` for fingerprinting + cache busting.
