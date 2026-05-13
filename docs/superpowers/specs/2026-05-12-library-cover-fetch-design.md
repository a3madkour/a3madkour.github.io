# Library cover fetch — design

**Date**: 2026-05-12
**Phase**: 7 (library polish)
**Status**: APPROVED
**Supersedes**: `2026-05-12-library-cover-fetch-sketch.md` (deleted on commit)
**Companion to**: `2026-05-12-library-section-design.md` (parent slice; ships glyph-only fallback per its §2)
**Inherits constraints from**: parent spec §1 (no AI art, accessibility, fixture-filler ethos)

---

## 1. Motivation

The library section ships with hand-authored type glyphs (book / clapper / gamepad / eighth-note) standing in for cover art. Glyphs work at any scale and never go stale, but lose the scanning anchor real cover art provides on lists like Letterboxd / Goodreads / Backloggd. As the library grows, rows blur together.

Real cover art is publisher promotional material, not AI-generated, so the parent spec's no-AI rule does not block it. The blocker has always been asset pipeline.

This slice ships the **infra** for covers — data shape, template integration, fetch script, linter, cache, fair-use posture — and seeds 8 real-title fixtures end-to-end. Live IGDB / TMDB API paths stay stubbed (code + mocked tests) for a future slice that pairs with real catalog data.

## 2. Scope

**In scope**:

- Data-shape extension: `extras` keys for `cover_file` / `cover_url` / `isbn` / `musicbrainz_release_group` / `igdb_id` / `tmdb_id` across all 4 library yamls.
- Hugo template integration: `partials/library/type-glyph.html` renders `<img>` when a cover is cached; falls back to glyph otherwise.
- Per-section native aspect: listening leaf goes square (44×44 / 56×56); other leaves stay portrait (44×56 / 56×72).
- Fetch script `tools/fetch_library_covers.py` with 4 live source paths (`cover_file`, `cover_url`, `isbn`, `mbid`) and 2 stubbed (`igdb_id`, `tmdb_id`).
- Audit log `tools/.cover-cache.json` committed; sha256 per cached file.
- Linter pair `tools/check_library_covers.py` + `tools/test_check_library_covers.py`. 12th linter pair on the project; CI runs both.
- Fixture seed: 2 real titles per leaf (8 total), with real PD or fair-use cover art. Notes / summary / commentary on those fixtures stay filler.
- Colophon credit line in footer; renders unconditionally.
- Fair-use posture documented in spec (§5) — not legal advice, but the reasoning + practical posture.

**Out of scope** (deferred to a future slice):

- Live IGDB + TMDB fetches against real items (needs API keys and real catalog).
- Live API hits during Hugo builds (rate-limit risk + flakiness — fetch is always author-driven).
- Cover-credit mouseover (per-row publisher tooltip).
- Cover-based filter chips ("show only covered items").
- Garden-side media-flavor covers (separate surface; future cache reuse).
- AI-generated covers (forbidden by parent §1).

## 3. API options per medium

Every medium has at least one free, key-free option and a higher-fidelity option behind a free account. No paid tier needed.

### Books

| Source | Identifier | Key | Notes |
|---|---|---|---|
| **Open Library Covers** | ISBN-10 / ISBN-13 | none | Primary. UA header with contact email required. |

### Music (album / track)

| Source | Identifier | Key | Notes |
|---|---|---|---|
| **Cover Art Archive** + MusicBrainz | release-group MBID | none | Primary. UA header with contact email required. |
| iTunes Search API | name + artist | none | No signup; small thumbnails, upscalable via URL surgery. |
| Discogs | release id | free | Excellent for obscure releases. |
| Last.fm | name + artist | free | Lower-quality art; very broad coverage. |
| Spotify Web API | track / album id | free OAuth | High-quality; TOS adds use constraints. |

### Games

| Source | Identifier | Key | Notes |
|---|---|---|---|
| **IGDB** (Twitch) | IGDB id | free (Twitch dev account) | Primary. 4 req/s. Richest metadata. |
| RAWG | RAWG id | free key | Lower friction than IGDB; almost-as-good coverage. |
| GiantBomb | GB id | free key | Strong for older games. |
| Steam Web API | appid | none (most endpoints) | Steam catalog only. |

### Film / TV

| Source | Identifier | Key | Notes |
|---|---|---|---|
| **TMDB** | TMDB id | free | Primary. 40 req / 10s. Industry-standard for hobby projects. |
| OMDb | IMDb id | free tier (1000 req/day) | Lighter coverage than TMDB. |
| TVDB | TVDB id | paid ($12/yr) | Avoid unless TMDB lacks coverage. |
| IMDb | — | — | No public API. TOS prohibits scraping. |

## 4. Fair-use posture

Not legal advice. This is the analysis as commonly applied to personal-site cover thumbnails.

**Four-factor test** (US):

1. **Purpose and character of use** — Non-commercial personal library with curated index + commentary (status pills, ratings, garden-linked notes). Plausibly transformative. ✅
2. **Nature of work** — Cover art is creative/expressive. Slightly against. ⚠️
3. **Amount used** — Thumbnails ≤80px wide, reduced from full publisher artwork. Strong precedent: *Kelly v. Arriba Soft* (9th Cir. 2003), *Perfect 10 v. Amazon* (9th Cir. 2007), *Bill Graham Archives v. DK* (2d Cir. 2006) — all favor thumbnail use. ✅
4. **Effect on market** — Cover thumbnails don't substitute for the work. Publishers actively distribute cover art as promotional material. ✅

Three of four factors favor fair use; the case strengthens when covers appear alongside actual commentary (the library section's status, notes, and garden backlinks qualify).

**Industry precedent**: Letterboxd, Goodreads, RateYourMusic, Backloggd, Last.fm all show third-party covers on user lists with no publisher licensing arrangement. None have lost a meaningful copyright case over this.

**Practical risk on a personal site at low traffic**: near zero. Publishers don't send takedowns for cover thumbnails; they send them for full ebook contents, ripped audio, or full-frame film stills.

**Risk factors that would shift the calculus** (none apply here):

- Monetizing the site / running ads against covers.
- Full-resolution covers rather than thumbnails.
- Stripping publisher marks / credit.
- Reproducing the interior of the work.

**Posture commitments**:

- Thumbnails only (≤80px wide cache target). Never full-res.
- Honor each API's `User-Agent` + attribution requirement (Cover Art Archive + Open Library require contact email).
- Cache locally — no hot-linking.
- DMCA takedown willingness — remove on rightsholder request.
- Colophon line in footer (§9 below).

## 5. Yaml data shape additions

Append to the `extras` block of each library yaml:

```yaml
extras:
  # universal (any medium):
  cover_file: "wizard-of-oz.jpg"   # local file under assets/images/library/covers/
  cover_url:  "https://..."        # author-provided URL

  # ID-keyed (per medium):
  isbn: "9780156453806"            # book — Open Library lookup
  musicbrainz_release_group: "..." # album/track — Cover Art Archive lookup
  igdb_id: 1942                    # game — stubbed in this slice
  tmdb_id: 95396                   # film/series — stubbed in this slice
```

**Resolution priority** (template + fetch-script agree):

1. `cover_file` present → load `assets/images/library/covers/<cover_file>`
2. `cover_url` present → fetch + cache to `<slug>.<ext>`
3. ID-keyed identifier → fetch via per-medium API + cache to `<slug>.<ext>`
4. None → glyph fallback

**Multi-edition handling**: when more than one edition exists for the same work, the author wins via `cover_file` (commit the exact image they want). ID-keyed lookup picks whatever the API returns as canonical.

**`tools/check_library_fixtures.py` updates**: accept the new keys as optional. Reject unknown keys (existing behavior). Validate:

- `isbn` matches `^\d{10}$|^\d{13}$`
- `igdb_id`, `tmdb_id` are positive ints
- `cover_url` parses as a URL (`urllib.parse.urlparse` returns `scheme + netloc`)
- `cover_file` is a relative filename (no `/`, no `..`)

## 6. Hugo template + CSS

### Template — `partials/library/type-glyph.html`

```hugo
{{- $coverFile := .extras.cover_file -}}
{{- $coverPath := "" -}}
{{- if $coverFile -}}
  {{- $coverPath = printf "images/library/covers/%s" $coverFile -}}
{{- else -}}
  {{- $coverPath = printf "images/library/covers/%s.jpg" .slug -}}
{{- end -}}
{{- $cover := resources.Get $coverPath -}}
{{- if $cover -}}
  <span class="library-cover-block {{ $size }} {{ $modifier }}">
    <img class="library-cover" src="{{ $cover.RelPermalink }}" alt="" loading="lazy" />
  </span>
{{- else -}}
  {{- /* existing glyph-block fallback unchanged */ -}}
{{- end -}}
```

`alt=""` — the cover is decorative; the row title is already in the row meta. `loading="lazy"` for every cover (the layout reserves space via fixed dimensions; no CLS).

### CSS — `assets/css/main.css` §37

```css
/* default: portrait everywhere */
.library-cover-block { display: inline-block; overflow: hidden; border-radius: 3px; }
.library-cover-block.mini  { width: 44px; height: 56px; }
.library-cover-block.large { width: 56px; height: 72px; }

/* listening leaf: square tiles for both glyph and cover */
.library-leaf-listening .library-cover-block.mini,
.library-leaf-listening .library-glyph-block.mini  { width: 44px; height: 44px; }
.library-leaf-listening .library-cover-block.large,
.library-leaf-listening .library-glyph-block.large { width: 56px; height: 56px; }

.library-cover { width: 100%; height: 100%; object-fit: cover; display: block; }
```

`.library-leaf-listening` lands on the listening leaf's `<body>` (via `layouts/library/listening/list.html`). Other leaves get no class — portrait stays default. Existing glyph rules for size are unchanged outside the listening cascade.

## 7. Fetch script — `tools/fetch_library_covers.py`

**Stdlib-only** (no `requests` dep; the project bans npm and limits Python to stdlib). Imports: `urllib.request`, `urllib.parse`, `json`, `pathlib`, `argparse`, `time`, `hashlib`, `sys`. YAML parsing reuses the hand-rolled helpers in `tools/check_fixtures.py` (the existing linters already use this — `parse_scalar` etc.) so no PyYAML dependency.

### CLI

```
tools/fetch_library_covers.py [--medium book|album|game|film|series|all] [--force] [--dry-run]
```

- `--medium`: limit to one media type. Default `all`.
- `--force`: re-fetch even if cache hit.
- `--dry-run`: print planned actions; no network, no disk.

### Source dispatch

| Source kind | API or behavior | This slice |
|---|---|---|
| `cover_file` | Verify file exists at `assets/images/library/covers/<cover_file>`; no fetch. Author-named filename. | Live |
| `cover_url` | `GET <cover_url>` → save to `assets/images/library/covers/<slug>.jpg`. | Live |
| `isbn` (book) | `GET https://covers.openlibrary.org/b/isbn/<isbn>-L.jpg` → save to `<slug>.jpg`. | Live |
| `mbid` (album/track) | `GET https://coverartarchive.org/release-group/<mbid>/front-500` → save to `<slug>.jpg` (follows 307). | Live |
| `igdb_id` (game) | `raise NotImplementedError("IGDB live fetch requires IGDB_CLIENT_ID + IGDB_CLIENT_SECRET; rerun when wired")` | Stubbed |
| `tmdb_id` (film/series) | `raise NotImplementedError("TMDB live fetch requires TMDB_API_KEY; rerun when wired")` | Stubbed |

### HTTP behavior

- `User-Agent: a3madkour-site/0.1 (<contact-email>)` — email loaded from `tools/.fetch-config.json` (gitignored). A `tools/.fetch-config.json.example` ships in the repo with a placeholder.
- Retry once on 5xx with 2s backoff. Bail on 4xx (logged, non-fatal — the row falls back to glyph).
- 10s per-request timeout.
- Per-source sleep:
  - `cover_url`: 50ms (no documented limit, courteous default)
  - `isbn` (OL): 100ms (no documented limit; conservative)
  - `mbid` (CAA): 250ms (CAA asks for ≤1 req/s)
  - IGDB/TMDB stubs: noop

### Failure handling

All non-`NotImplementedError` failures are caught and logged to stderr with the slug + source + error. The script keeps going to the next item. Exit code:

- `0` if no items errored.
- `1` if any item errored (so CI can opt in to "fail if anything broke" later, but not now).

### Idempotency

Cache hit (`<slug>.jpg` exists, or `<cover_file>` exists for the literal-filename path) → skip unless `--force`. Script can be re-run after editing yaml; existing covers untouched.

### Cache filename convention

All non-`cover_file` paths normalize the cached filename to `<slug>.jpg`, regardless of the source's actual MIME type. Browsers content-sniff (the `.jpg` extension is decorative), and Hugo's `resources.Get` is bytes-only — so a cached file containing PNG bytes under a `.jpg` name still renders correctly. This lets the Hugo template hardcode `<slug>.jpg` lookups without needing the audit log at render time.

`cover_file` paths keep the author-provided filename (any extension), since the template uses the literal value.

## 8. Audit log + cache strategy

### Audit log — `tools/.cover-cache.json` (committed)

```json
{
  "wizard-of-oz": {
    "source_kind": "cover_url",
    "source": "https://upload.wikimedia.org/.../Wizard_title_page.jpg",
    "fetched_at": "2026-05-12T18:34:00Z",
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }
}
```

Committed so reviewers see what was fetched and when. `sha256` detects upstream silent swaps (publishers updating covers); the linter (§9) warns when sha mismatches or the entry goes stale.

### Cache location — `assets/images/library/covers/`

Lives under `assets/` (not `static/`) so Hugo can fingerprint + minify, and the per-page `resources.Get` lookup works.

- File names: `<slug>.<ext>` for ID-keyed and `cover_url` paths; original filename for `cover_file` (already author-named).
- Extensions follow source MIME (`.jpg` from OL/CAA; whatever the cover_url returned).
- Commit binaries to git (sketch §6 option A). ~30–80 KB each; 8 fixtures × ~50 KB = ~400 KB this slice. LFS migration is trivial later if the library grows past thousands of items.

### Gitignored — `tools/.fetch-config.json`

```json
{ "contact_email": "you@example.com" }
```

The shipped example (`tools/.fetch-config.json.example`) carries a placeholder. The live file stays out of git so the contact email isn't published in the repo (even though it's in CLAUDE.md's session context, the file itself is author-controlled).

## 9. Linter — `tools/check_library_covers.py`

12th linter pair. CI runs `python3 tools/check_library_covers.py && python3 tools/test_check_library_covers.py`. Brings the project from 11 → 12 pairs, 23 → 25 verification steps.

### Checks

| # | Check | Severity |
|---|---|---|
| 1 | Schema: each `extras` cover key has the right type (ISBN regex, positive int for ids, URL parse, relative filename). | Fail |
| 2 | Cache coverage: every row with a cover identifier has a cached file. | Warn |
| 3 | Audit-log consistency: every cache file has an audit entry; each entry's sha256 matches the on-disk file. | Warn |
| 4 | Audit-log freshness: entries older than `--stale-days` (default 365). | Warn |
| 5 | No-cover rows pass silently. | — |

**Rationale for warn-not-fail on 2–4**: missing cache is a workflow signal ("run `tools/fetch_library_covers.py`"), not a broken-site bug. The site builds and falls back to glyph either way. Failing CI on workflow signals would block merges for non-bugs.

Exit code: `0` on warnings; `1` only on schema violations.

### Test sibling — `tools/test_check_library_covers.py`

Standard pattern matching the other 11 pairs — stdlib `unittest`. Test cases:

- Schema valid / invalid (one per key type).
- Missing cache file → warning emitted.
- sha256 mismatch → warning emitted.
- Stale entry → warning emitted.
- No-identifier row → silent.

### CI wiring — `.github/workflows/hugo.yaml`

Append to the lint job, pattern-identical to the other 11 linters:

```yaml
- name: check_library_covers
  run: python3 tools/check_library_covers.py
- name: test_check_library_covers
  run: python3 tools/test_check_library_covers.py
```

## 10. Colophon

**Footer addition** — `layouts/partials/footer.html` (or wherever the existing colophon block lives):

```
Cover art via Open Library, Cover Art Archive, IGDB, and TMDB.
Copyright respective publishers; reproduced under fair use for non-commercial commentary.
```

Renders unconditionally — no asset-walk during build; appears as soon as the slice ships.

## 11. Fixture seed

Eight real-title fixtures across the four leaves. Titles + creators are real metadata; notes / summary / commentary text on these fixtures stay filler ("Example notes line one." etc.).

| Leaf | Title (real) | Creator (real) | Cover source | Cover license |
|---|---|---|---|---|
| reading | The Wonderful Wizard of Oz | L. Frank Baum | Wikimedia title-page scan | PD-US (1900) |
| reading | Pride and Prejudice | Jane Austen | Wikimedia 1894 Allen cover | PD-US (1894) |
| listening | Brandenburg Concertos | J.S. Bach | Bach Gesellschaft 1871 plate (Wikimedia) | PD |
| listening | The Entertainer | Scott Joplin | 1902 sheet music cover (Wikimedia) | PD-US (1902) |
| playing | Hades | Supergiant Games | Publisher press-kit image | Fair use |
| playing | Celeste | Maddy Makes Games | Publisher press-kit image | Fair use |
| watching | The General | Buster Keaton | 1926 poster (Wikimedia) | PD-US (1926) |
| watching | Nosferatu | F.W. Murnau | 1922 poster (Wikimedia) | PD-US (1922) |

The two `playing` fixtures use modern game cover art under fair use (no PD games exist in commonly-recognized form). Their `cover_url` points to the publisher's press-kit image; the file lands in cache via the live `cover_url` path. Hades + Celeste both ship official press kits with cover art free to redistribute for editorial/commentary use.

The remaining ~4-5 entries per leaf stay as "Example N" with no cover identifier — exercises the glyph fallback path on the same page.

## 12. Acceptance criteria

- All 4 yaml schemas accept new `extras` cover keys without breaking `tools/check_library_fixtures.py`.
- 8 fixtures across 4 leaves carry real titles + cached real cover art; remaining fixtures stay filler.
- `tools/fetch_library_covers.py` exists; live-exercises `cover_file`, `cover_url`, `isbn`, `mbid` paths against fixtures.
- `igdb_id` + `tmdb_id` dispatch paths raise `NotImplementedError` and are covered by mocked-HTTP unit tests.
- `tools/check_library_covers.py` + `tools/test_check_library_covers.py` ship as 12th linter pair; CI runs both.
- `tools/.cover-cache.json` committed with sha256s.
- `tools/.fetch-config.json` gitignored; `.example` committed.
- Hugo template renders `<img>` when cover cached, glyph otherwise. `alt=""`, `loading="lazy"`.
- Listening leaf body class triggers square aspect for glyph + cover in CSS §37.
- Colophon line lands in footer; renders unconditionally.
- `tools/check-contrast.py` still passes (no token changes).
- `hugo --minify` builds cleanly.
- Dev-server spot-check (light + dark): each leaf renders a mix of covers + fallback glyphs; listening leaf visibly square; no layout regressions.

## 13. Privacy + rate-limit considerations

- API calls reveal what the author is reading / watching / playing to the provider. Open Library + Cover Art Archive are key-free → no per-user correlation. TMDB + IGDB tie requests to an API key → provider can correlate. The author should be aware before wiring live keys.
- Open Library + Cover Art Archive require `User-Agent` with contact email — honored.
- Rate limits per §3 — script's per-source sleep stays under documented limits.
- Cover art is public publisher promotional material; redistribution under fair use is industry-standard for personal sites with commentary. See §4.

## 14. Bookkeeping

When this slice ships, update `CLAUDE.md`:

- Lint-pair count: 11 → 12 pairs; 23 → 25 verification steps.
- Deferred-features table: change the "Library cover thumbnails" row from "future library cover-fetch slice (sketch exists)" → "infra shipped 2026-05-12; live IGDB/TMDB paths land with elisp / real items".
- Project-status timeline: append a "Shipped" entry.
- Reference docs: drop the sketch line, add this design's path.

Delete `docs/superpowers/specs/2026-05-12-library-cover-fetch-sketch.md` in the same commit. The git history preserves the sketch; a stale doc next to its successor is worse than no doc.

Add a memory entry post-merge: `project_library_cover_fetch_slice.md` (Phase 7 Slice 1).

## 15. Open questions resolved during brainstorming

| Sketch §11 question | Resolution |
|---|---|
| Currently-active vs row cover dims | Per-section native aspect: listening square (44×44 / 56×56); other leaves portrait (44×56 / 56×72). |
| Multi-edition books — which cover wins? | Author override via `cover_file` always wins. ID-keyed picks API canonical. |
| Failed-fetch UX | Silent glyph fallback at render; script logs to stderr; linter warns when cache missing. |
| Linter — soft-warn forever or fail-on-stale? | Soft-warn forever. Schema violations still fail. |
| Cache under `assets/` or `static/`? | `assets/` — Hugo fingerprinting + `resources.Get` lookup. |
