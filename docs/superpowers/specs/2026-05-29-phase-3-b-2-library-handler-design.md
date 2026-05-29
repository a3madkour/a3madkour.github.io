# Phase 3 sub-project B, slice B.2 — library handler design

**Status:** design (brainstormed 2026-05-29)
**Parent spec:** `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` (§8 sketches the library pipeline; this slice spec refines it).
**Position:** B.1.1 (shipped 2026-05-26) → **B.2** → B.3 (research themes + questions).
**Prior slice memories:** [[b1-complete]] (B.1 + B.1.1 — garden handler + pre-export id-link rewriter), [[b0-complete]] (shared infra), [[phase-3-library-tag-shelves]] (tag round-trip rule), [[library-covers-static-path]] (cover-file binding rule).

---

## 1 — Goals

Implement the library publisher. Library is the structural outlier in sub-project B: it emits per-medium YAML rows in `data/<medium>.yaml` rather than per-page Hugo bundles. The handler walks top-level org headings inside one of four source files (`library-reading.org` / `-listening.org` / `-playing.org` / `-watching.org`) and renders each heading as one YAML row. All four files publish via the existing `publish-living` lifecycle alongside garden + research.

Library is the second living section to ship. By the end of B.2:

- `~/org/notes/library-{reading,listening,playing,watching}.org` annotated with `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: library-<medium>` publish end-to-end via `a3-pub.sh --publish-living`.
- `data/{reading,listening,playing,watching}.yaml` regenerated deterministically; first real publish overwrites the existing fixture rows.
- All three library linters (`check_library_fixtures.py` + `check_library_links.py` + `check_library_covers.py`) accept B-emitted output.
- Idempotent re-run produces zero file diffs.

## 2 — Non-goals (deferred or out of scope)

- **Per-item URL resolution for `[[id:UUID]]` links targeting library headings.** Per Q3 decision, library items have no URL in B.2. `[[id:UUID]]` to a library heading falls through to the inert-text path (with WARN). Anchor-jump linking to `/library/<medium>/#<slug>` is queued as B.2.x.
- **`data/library-shelves.yaml` emission.** Shelves are hand-authored curation per [[phase-3-library-tag-shelves]]; the publisher does not touch them.
- **Cover-file copying from `~/org/notes/assets/`.** Covers live at `static/library/covers/<slug>.jpg` and are committed manually per [[library-covers-static-path]]. The handler only verifies the file exists; missing files WARN and the linter catches them downstream.
- **publish-deliberate path for library.** Library belongs to the publish-living set per parent §5. publish-deliberate is for essays / works (slices B.4 / B.5).
- **ox-hugo body export.** Library items are drawer-only metadata; the handler does NOT invoke `a3madkour-publish-export.el`.
- **A.1 link-rewriter invocation.** No body → no inline links → no rewriter call.

## 3 — Per-medium config table

The four-way variance across the library sections collapses into a single per-section config table living inside `a3madkour-publish-library.el`:

```elisp
;; (section-symbol . (yaml-filename
;;                    default-media-type
;;                    allowed-media-types
;;                    allowed-statuses))
'((library-reading   . ("reading.yaml"   "book"  ("book")
                        ("finished" "reading" "queued" "abandoned")))
  (library-listening . ("listening.yaml" "album" ("album" "track")
                        ("finished" "listening" "queued" "dropped")))
  (library-playing   . ("playing.yaml"   "game"  ("game")
                        ("finished" "100pct" "playing" "queued" "dropped")))
  (library-watching  . ("watching.yaml"  "film"  ("film" "series")
                        ("finished" "watching" "queued" "dropped"))))
```

Status enums copied verbatim from `tools/check_library_fixtures.py:ALLOWED_STATUSES`; the linter is authoritative for B-emitted YAML. Parent B spec §8 lists older candidate enums (`to-read` / `playlist` / `listened` / `to-watch` / etc.) that predate the linter's current set — that's a doc bug in the parent spec, flagged as a B.2 finding for follow-up correction.

## 4 — Architecture

One new elisp module `a3madkour-publish-library.el` (+ `-test.el` sibling) under `~/dotfiles/emacs-configs/custom/lisp/`. The module exports one entry-point `publish-library-file (file)` and registers four entries in `a3madkour-publish-living--handlers`:

```elisp
((library-reading   . publish-library-file)
 (library-listening . publish-library-file)
 (library-playing   . publish-library-file)
 (library-watching  . publish-library-file))
```

Dispatch keys on the symbol `note-section` returns; the function reads the section back from the file to look up its per-medium config. Matches B.1's registration pattern (Approach A in the brainstorm — symbol-keyed dispatch with shared function over four entries).

`a3-pub.sh` gains an explicit `-l a3madkour-publish-library` load in its three publish-side intercepts (the same set B.1 wired into: `--publish-living`, `--publish-deliberate`, plus the M-x-callable surface; `--check-orphans` is intentionally NOT updated since it does not dispatch handlers). Pattern mirrors B.1's wrapper-script update; the [[plan-wrapper-script-updates]] feedback memo applies.

Library does NOT call:
- `a3madkour-publish-export.el` (no body export — drawer-only metadata)
- `a3madkour-publish-rewrite.el` (no inline links to rewrite)
- `a3madkour-publish-assets.el` (no per-note asset bundles — covers live in `static/library/covers/` and are manually committed)
- `a3madkour-publish-history/record-publish` (URL-less per Q3)

`finish-publish`'s manifest-based orphan sweep does not touch library YAML files (no manifest rows for library items). The "full replace" of `data/<medium>.yaml` on each publish-living run is the de-facto sweep: headings no longer in the source file disappear from the yaml automatically.

## 5 — Property → YAML mapping

Each top-level org heading becomes one YAML row. The linter (`tools/check_library_fixtures.py`) is authoritative for required/optional/allowed fields; the mapping below reflects what the publisher emits to satisfy it.

### Required fields

| YAML key | Org source | Derivation |
|---|---|---|
| `slug` | `:SLUG:` drawer (optional) → fallback derived from title | Title → Unicode NFD → drop combining marks → lowercase → collapse `[^a-z0-9]+` runs to single `-` → trim leading/trailing `-`. Empty result → WARN + skip the item. |
| `title` | Heading text via `org-element-property :raw-value` | TODO keyword + org tags already stripped by `:raw-value` |
| `creator` | `:CREATOR:` drawer | string |
| `year` | `:YEAR:` drawer | `string-to-number` → int |
| `media_type` | `:MEDIA_TYPE:` drawer (optional) → fallback section default | Must be ∈ allowed-media-types; out-of-set → WARN + emit anyway |
| `status` | `:STATUS:` drawer | Must be ∈ allowed-statuses; out-of-set → WARN + emit anyway |
| `last_modified` | `:LAST_MODIFIED:` drawer (optional) → fallback file git-mtime | YYYY-MM-DD; uses new `--git-mtime-of-file` helper shared with B.1 (closes B.1.1 follow-up #2) |
| `tags` | Per-heading org tags, filtered | Default exclusion: `{TODO, DONE, WAIT, CANCELED, HOLD, NOEXPORT, ATTACH}`. Defcustom `a3madkour-pub-editorial-tags` exposes the list for per-project tuning. Retroactively closes B.1.1 follow-up #6. |

### Optional top-level fields

| YAML key | Org source | Notes |
|---|---|---|
| `started` | `:STARTED:` drawer | YYYY-MM-DD |
| `finished` | `:FINISHED:` drawer | YYYY-MM-DD; linter requires this when status ∈ terminal set (`finished` / `watched` / `listened`) — emitter does not enforce, the linter catches it |
| `spoiler_level` | `:SPOILER_LEVEL:` drawer | one of `none / light / heavy` |
| `cite_key` | `:CITE_KEY:` drawer | pass-through; sub-project F validates against `library.bib` later |
| `canonical_url` | `:CANONICAL_URL:` drawer | linter requires `https://` prefix |
| `note_slug` | `:NOTE_SLUG:` drawer | slug of a garden note about this item |
| `preview` | `:PREVIEW:` drawer | one-line annotation |
| `extras` | composite (see below) | nested map |

### Extras mapping (drawer property → `extras.<key>`)

Universal (any medium):
- `:COVER_FILE:` → `extras.cover_file`
- `:COVER_URL:` → `extras.cover_url`

Per medium (matches `tools/check_library_fixtures.py:ALLOWED_EXTRAS`):

| medium | extras drawer properties → yaml keys |
|---|---|
| book | `:ISBN:` → `isbn`; `:PROGRESS_PCT:` → `progress_pct` (int); `:PROGRESS_LABEL:` → `progress_label` |
| album / track | `:MBID:` → `musicbrainz_release_group` |
| game | `:IGDB_ID:` → `igdb_id` (int); `:HOURS_PLAYED:` → `hours_played` (int); `:PLATFORM:` → `platform` |
| film | `:RUNTIME_MIN:` → `runtime_min` (int); `:TMDB_ID:` → `tmdb_id` (int) |
| series | `:EPISODE_COUNT:` → `episode_count` (int); `:CURRENT_EPISODE:` → `current_episode` (int); `:CURRENT_SEASON:` → `current_season` (int); `:TMDB_ID:` → `tmdb_id` (int) |

Integer-valued extras pass through `string-to-number`. The handler ignores drawer properties not in the per-medium table (forward-compatible with future extras additions, and prevents publish-time errors from authors who set `:ISBN:` on an album by mistake — the linter catches that on output).

### Cover-file existence check

When `:COVER_FILE:` is present, the handler stats `<site-static-dir>/library/covers/<value>` at publish time. Site-static-dir is derived as the sibling of `site-content-dir` (which is the sibling of `site-data-dir` — same cascade as B.1's `--site-content-dir-effective` helper). Missing → WARN, emit the key anyway. `tools/check_library_covers.py` is the CI gate that fails the build when a referenced cover is missing.

Pattern matches A.1's WARN-don't-fail discipline and B.1.1's emit-and-let-linter-catch behaviour.

## 6 — Handler flow

`publish-library-file (file)` runs once per library `.org` file. Steps:

1. **Resolve section + config.** `a3madkour-pub/note-section` returns `'library-reading` etc. Look up the 4-tuple `(yaml-filename default-media-type allowed-media-types allowed-statuses)` from the per-medium config table.
2. **Open + parse.** `with-temp-buffer` + `insert-file-contents` + `org-mode` + `org-element-parse-buffer`.
3. **Walk top-level headings.** `org-element-map ast 'headline (...) nil nil 'headline)` with a depth=1 filter (`(= (org-element-property :level node) 1)`). Nested sub-headings are ignored.
4. **Normalize each heading → row plist** via pure `--normalize-item (headline section config file)`:
   - Title from `:raw-value`.
   - Slug: `:SLUG:` drawer → fallback `--title-to-slug`.
   - Media_type: `:MEDIA_TYPE:` drawer → fallback section default. Validate; WARN on out-of-set; emit anyway.
   - Status: `:STATUS:` drawer (required). Validate; WARN on out-of-set; emit anyway.
   - Per-keyword pass-through: `creator`, `year` (→ int), `started`, `finished`, `spoiler_level`, `cite_key`, `canonical_url`, `note_slug`, `preview`.
   - `last_modified`: `:LAST_MODIFIED:` drawer → fallback `--git-mtime-of-file file`.
   - Tags: `(org-element-property :tags headline)` → `--filter-editorial-tags`.
   - Extras: collect any recognized extras-drawer-keys present (per the medium table) into a nested plist; int-coerce per type table; verify cover-file existence and WARN if missing.
5. **Deduplicate slugs** within the file. Build a set as we walk. On collision: WARN + skip the second occurrence (do not silently overwrite the first row).
6. **Render the YAML.** Reuse B.1's `render-yaml-value` + deterministic key ordering. Source-file-order preserved (matches §8 of this spec + parent §11 idempotency contract). Top-of-file comment header:
   ```
   # Generated by a3madkour-publish-library from <relative-source-path>.
   # Manual edits will be overwritten on next publish-living run.
   ```
7. **Write-if-different.** Same `--write-if-different` helper as B.1 — compare in-memory rendering to disk byte-for-byte, write only on diff.
8. **No `record-publish`.** Library items are URL-less per Q3. URL-history is untouched.
9. **Lifecycle wrapping.** `publish-living` already calls `begin-publish` once + iterates the living source set + calls `finish-publish` once. B.2 introduces no lifecycle changes beyond registering the four handler entries.

## 7 — Error handling (WARN-don't-fail throughout)

| Condition | Behavior |
|---|---|
| Missing required drawer (`:CREATOR:` / `:YEAR:` / `:STATUS:`) | WARN with file + heading context; emit `null` for that key (linter rejects on output side — same as fixtures) |
| Status / media_type out of allowed enum | WARN; emit the bad value (linter catches) |
| Slug collision within file | WARN; skip second occurrence |
| Cover file referenced but missing | WARN; emit `extras.cover_file` key anyway (linter catches via `check_library_covers`) |
| Malformed date (`:STARTED:` / `:FINISHED:` / `:LAST_MODIFIED:`) | WARN; emit raw string (linter catches via date regex) |
| Empty derived slug (title was all non-alphanumeric) | WARN; skip the item entirely |
| `:MEDIA_TYPE:` drawer present but not in any allowed-media-types for the section | WARN; emit anyway |

A.1's "warnings never fail the publish; linters are the gates" discipline applies throughout.

## 8 — Idempotency + transition

### Idempotency

- `render-yaml-value` is deterministic given fixed key-ordering + source-file-order rows.
- `--git-mtime-of-file` returns the same value across runs for an unmodified file (git's commit-tracked timestamp does not move on `touch` or no-op saves).
- `--write-if-different` skips the write when content matches disk byte-for-byte.
- Re-running `publish-living` with no source changes → zero file diffs in `data/`.

### git-mtime granularity tradeoff

Git-mtime resolves to the most recent commit touching the source file. Committing a change to one item (say, updating `:STATUS:` on one heading) advances git-mtime for the whole file → every item lacking an explicit `:LAST_MODIFIED:` gets the same new shared date. Acceptable per Q2's recommendation; document the tradeoff so authors who want stable per-item dates know to pin individual items via explicit `:LAST_MODIFIED:` drawers.

### Transition from fixture YAML → org-sourced YAML

Per parent §11.B.2 row: `data/{reading,listening,playing,watching}.yaml` overwritten. First real `publish-living` after seeding real items in `~/org/notes/library-*.org`:

- The four yaml files in `data/` are rewritten from scratch.
- Fixture rows (`invisible-cities` / `koyaanisqatsi-soundtrack` / `outer-wilds` / `severance-s2` / Lorem-N filler) disappear.
- `check_library_fixtures.py` continues to gate the SHAPE of what's written. B-emitted rows pass it.
- `check_library_links.py` gates `note_slug` + `cite_key` resolution.
- `check_library_covers.py` gates cover file existence for items declaring `cover_file`.

`data/library-shelves.yaml` is not touched (hand-authored curation).

## 9 — Sub-helpers (all ert-tested)

| Helper | Signature | Purity | Notes |
|---|---|---|---|
| `--title-to-slug` | `(title)` → string | pure | NFD + diacritic strip + alphanumeric reduction |
| `--filter-editorial-tags` | `(tags &optional extra-exclusions)` → list | pure | Default exclusion list + per-section override; also called by garden handler (retroactive) |
| `--normalize-item` | `(headline section config file)` → plist | pure (modulo cover-stat IO + git-mtime fallback) | Most of the test surface lives here |
| `--render-library-yaml` | `(rows)` → string | pure | Wraps B.1's `render-yaml-value`; emits the comment header |
| `--write-if-different` | `(path content)` → boolean | IO | Already shipped in B.0 / B.1 — reused |
| `--git-mtime-of-file` | `(file)` → ISO-date string or nil | IO | Lives in `a3madkour-publish-history` (natural module for time helpers); shared with garden |

## 10 — Testing strategy

### Elisp ert tests

Expected ≈ 25-30 new tests in `a3madkour-publish-library-test.el`:

| Group | Count | Coverage |
|---|---|---|
| `--title-to-slug` | ~8 | basic title, apostrophes (`L'Étranger`), diacritics (`Köyaanisqatsi`), ampersands (`Crime & Punishment`), colons (`Dune: Part One`), parentheticals (`Maximum a Posteriori (MAP)`), numeric-leading (`1984`), all-non-alnum-empty edge |
| `--filter-editorial-tags` | ~4 | TODO stripped, NOEXPORT stripped, content tag preserved, per-section override merge |
| `--normalize-item` | ~10 | per-section dispatch (4 sections × happy path), slug-override, media_type-override, status-enum violation WARN, missing-required WARN, extras coercion, cover-file-missing WARN, last_modified explicit beats git-mtime fallback, finished date emission, tag round-trip |
| `--render-library-yaml` | ~3 | PyYAML round-trip golden, source-file-order preserved, deterministic ordering |
| `publish-library-file` end-to-end | ~4 | publish-once, idempotent re-run, slug-collision WARN-skip, removed-item-disappears |
| `--git-mtime-of-file` | ~2 | tracked file returns ISO date; untracked returns nil |

### Python integration fixtures

`tools/test_publish_integration.py` grows 14 → ~18. New `TestLibraryPublishLiving` class with helpers mirroring B.1's `_publish_living` / `_write_garden_source`:

- `test_library_publish_once` — seed 1 item per file (across 4 files), run publish-living, assert 4 yaml files emitted + all 3 library linters (`check_library_fixtures.py` + `check_library_links.py` + `check_library_covers.py`) return rc 0 against B-emitted output.
- `test_library_publish_idempotent` — second run on unchanged source → zero file diffs.
- `test_library_slug_shift` — change `:SLUG:` on one item → old slug row disappears, new slug row appears in same file.
- `test_library_removed_item_unpublish` — delete a heading from source → row disappears from yaml on next publish.

### Site linter parity

No new linter pair required. Existing `check_library_fixtures.py` + `check_library_links.py` + `check_library_covers.py` continue gating output shape regardless of authorship.

### Test-count goal at slice end

- ert: 271 → ~300
- Python integration fixtures: 14 → ~18

## 11 — Slice positioning + commit boundary

Position in parent §12 slice table: **B.2**. Successor of B.1.1; predecessor of B.3 (research themes + questions).

Estimated commit count: ~10-12 in dotfiles. Site repo gets the integration fixtures + this design doc + plan + memory update.

Spot-check checkpoint at slice end: author annotates 2-3 real items per library file, runs `a3-pub.sh --publish-living`, verifies (1) four yaml files written + (2) all three library linters green + (3) `hugo --minify` builds the catalogue + shelves cleanly + (4) browser eyeball of `/library/`, `/library/reading/`, `/library/listening/`, `/library/playing/`, `/library/watching/`.

## 12 — Open follow-ups deferred to B.2.x or later

1. **Anchor-jump linking to library items.** `[[id:UUID]]` to a library-heading UUID resolves to inert text in B.2. If demand surfaces, B.2.x can teach A.1's `note-url` about heading-level IDs and emit `id="<slug>"` anchors on library cards.
2. **`finish-publish` no-retry on failed `delete-bundle`** (carried from B.1.1 follow-up #5). Library doesn't exercise `delete-bundle` (no bundles), so B.2 does not make it worse. Still open.
3. **`published-p` semantics for library item UUIDs.** Parent §3 says file-level `published-p` returns `'live`; library items don't carry per-item URL-history. Document that a query for an individual library-item UUID falls back to file-level — no code change.
4. **Per-item body content.** B.2 ignores body content under headings (preview comes from `:PREVIEW:` drawer per Q5). If authors want longer per-item notes that appear somewhere on the site, that's a separate template + spec decision.
5. **Parent B spec §8 status-enum correction.** Parent §8 lists pre-linter candidate enums (`to-read` / `playlist` / `listened` / `to-watch` / `wishlist` / `watched`) that the live linter rejects. Document or in-place-correct in parent spec at first natural touch. Cosmetic; the live linter is authoritative either way.

## 13 — Cross-references

- Parent B spec: `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` (§8 library)
- B.1 plan (closest implementation precedent): `docs/superpowers/plans/2026-05-25-phase-3-b-1-garden-handler.md`
- A.1 design: `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md`
- Library section design (Hugo-side, existing): `docs/superpowers/specs/2026-05-12-library-section-design.md`
- Library redesign slice (umbrella + shelves, already shipped): [[library-redesign-slice]]
- Memory: [[b1-complete]], [[b0-complete]], [[phase-3-library-tag-shelves]], [[library-covers-static-path]], [[plan-wrapper-script-updates]], [[hugo-template-gotchas]]
