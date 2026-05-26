# Phase 3 sub-project B — per-content-type publisher + templates

**Status:** design (brainstormed 2026-05-24)
**Parent spec:** `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` (sub-project A — access control + link semantics)
**Sequence:** A → **B** → F → C → D → E (per `memory/project_phase_3_decomposition.md`)
**Prior slice memories:** [[a1d-complete]] (A.1.d shipped 2026-05-24), [[phase-3-two-publish-commands]] (carries the two-command rule), [[phase-3-library-tag-shelves]] (library tag round-trip rule), [[phase-3-org-synced-poetry-export]] (synced-poetry contract stub).

---

## 1 — Goals

Implement the publisher itself: org-mode sources at `~/org/notes/` become Hugo content files at `content/<section>/<slug>/index.md` (for page-shaped sections) and YAML rows in `data/<medium>.yaml` (for library). All seven destinations (garden / library / research / essays / works / streams / about) ship through one of two top-level commands invoked from both M-x and shell. ox-hugo handles the org→markdown body; B owns frontmatter normalization, link-rewriting + asset hookup (delegating to A), URL-history recording, and per-section template contracts.

B is the first downstream consumer of sub-project A's elisp library. Its design exercises and validates A's API surface (parent spec §10) under real usage; one A.1 refactor is required (the manifest-snapshot fix in §6 below).

## 2 — Non-goals (deferred or out of scope)

- **Citation pipeline / `[cite:@key]` parsing** — sub-project F.
- **Math validators / KaTeX rendering** — sub-project C; B emits whatever ox-hugo produces.
- **Unified def/thm/figure markup that targets PDF + Word** — sub-project D.
- **Per-page interactive widgets / explorables** — sub-project E.
- **Typed-backlinks data computation** — A.2 (B leaves the panel-data plist stubbed at `nil`).
- **`:noexport:` subtree handling inside the link rewriter** — A.2 (B inherits whatever A.1 ships).
- **`--strict` mode** — A.2.
- **Now-widget data shape on the About page** — future slice (B publishes the static About page; the Now widget is its own surface).
- **Live polling for streams** — existing cron workflow `.github/workflows/streams-poll.yaml` already covers this; B only emits the static stream item pages.
- **Custom typed-link emission** — A.1 already settled (CSS classes only). B inherits.

## 3 — Source-side model (per section)

| Section | Source shape | Discriminator |
|---|---|---|
| garden | One `.org` per note, anywhere under `~/org/notes/` | `#+HUGO_SECTION: garden` |
| essays | One `.org` per essay | `#+HUGO_SECTION: essays` |
| research | One `.org` per theme OR question | `#+HUGO_SECTION: research-theme` or `research-question` |
| works | One `.org` per game / album / track / poem | `#+HUGO_SECTION: works-games` / `works-music` / `works-poetry` |
| streams | One `.org` per stream item | `#+HUGO_SECTION: streams` |
| about | One `.org` for the about page | `#+HUGO_SECTION: about` |
| library | **Four `.org` files**: `library-reading.org` / `-listening.org` / `-playing.org` / `-watching.org`. Top-level headings = items. | `#+HUGO_SECTION: library-reading` etc. (set once at the file level) |

A.1 already requires both `#+HUGO_PUBLISH:` + `#+HUGO_SECTION:` together. B extends the section enum with the values above. Library is the structural outlier — its `#+HUGO_PUBLISH: t` marks the file, and B's library handler walks subtrees inside it.

**A.1 semantics for library sections:** `library-reading` / `-listening` / `-playing` / `-watching` are URL-less sections. A's `note-section` returns the symbol (e.g. `'library-reading`); A's `note-url` returns `nil` (no per-item page exists); A's `record-publish` is NOT called for library items (no URL to record). Library files participate in the published-set predicate (`published-p` returns `'live`) so other sections' link-rewriter calls into library notes get warned about correctly, but the manifest does not grow rows for library items.

## 4 — Command surface

```
M-x a3-publish-living                  ;; iterates garden+library+research source sets
M-x a3-publish-deliberate              ;; prompts for file-or-id, dispatches by section
a3-pub.sh --publish-living             ;; same as M-x version
a3-pub.sh --publish-deliberate <path>  ;; same as M-x version
```

Both commands wrap the same library functions; M-x and shell are thin entry points. `publish-living` is idempotent and safe to invoke on cron / save-hook / pre-push; `publish-deliberate` is one file (or one subtree promotion for library item) at a time and intended for human review.

Both commands follow the same lifecycle:

```
begin-publish        ;; snapshots manifest + metadata cache + org-roam DB
walk-and-emit        ;; per-section handler runs for each in-scope file/subtree
finish-publish       ;; Step A (unpublish removed) + Step B (slug-shift asset+source rewrite) + Step C (link recheck)
```

`record-publish` is called by each section handler per-note, **using the manifest snapshot read by `diff-published-set`** — this is the B-coupling fix (§6).

## 5 — Module structure

New elisp modules under `~/dotfiles/emacs-configs/custom/lisp/` (each with a `-test.el` sibling). Mirrors the per-concern split A established (8 modules + tests).

| Module | Purpose |
|---|---|
| `a3madkour-publish-export.el` | Shared ox-hugo wrapper. Exposes `(export-file file dest-dir)` that calls ox-hugo on a single file, captures the output buffer, returns `(:body markdown :frontmatter alist :warnings (...))`. Owns ox-hugo configuration (page-bundle mode, shortcode escaping, taxonomy handling). |
| `a3madkour-publish-frontmatter.el` | Per-section frontmatter normalization. Exposes `(normalize section raw-alist source-file)` → `cleaned-alist`. Handles `growth_stage` derivation, `flavor` inference from `media_type`, `has_*` boolean detection by source-content scan, etc. |
| `a3madkour-publish-garden.el` | Garden handler. `(publish-garden-file file)` does export → normalize-frontmatter → link-rewrite (A) → asset-copy (A) → write `content/garden/<slug>/index.md` → record-publish (A). |
| `a3madkour-publish-library.el` | Library handler. `(publish-library-file file)` walks subtrees, normalizes each to a YAML-row plist, writes `data/<medium>.yaml`. Per-item record-publish NOT called (library items aren't URL-targeted; they're rows). |
| `a3madkour-publish-research.el` | Research handler — both themes + questions. Cross-ref resolution (`parent_question` / `theme` / `supporting_notes` / `related_essays`). |
| `a3madkour-publish-essay.el` | Essay handler. Series + sidenote-presence + citation-presence + toc + has_* flag derivation; hero / featured / tile_size pass-through. |
| `a3madkour-publish-works.el` | Works sub-dispatcher (games / music / poetry). Routes by `HUGO_SECTION`. Owns synced-poetry markup emission (per [[phase-3-org-synced-poetry-export]]) for poetry. |
| `a3madkour-publish-streams.el` | Streams handler. Cross-ref symmetry validation (`related_*` ↔ `source_stream`). |
| `a3madkour-publish-about.el` | About static-page handler. Smallest module. |
| `a3madkour-publish-living.el` | `(a3-publish-living)` top-level. Walks living source set (any file whose `HUGO_SECTION` ∈ {`garden`, `library-*`, `research-theme`, `research-question`}), invokes per-section handler, runs full begin/finish lifecycle. |
| `a3madkour-publish-deliberate.el` | `(a3-publish-deliberate file-or-id)` top-level. Resolves arg → file path → reads HUGO_SECTION → dispatches to per-section handler. Wraps single-file invocation in begin/finish lifecycle. |

`a3-pub.sh` extended with `--publish-living` and `--publish-deliberate <path>` flag intercepts (matching the existing `--check-orphans` precedent). All new modules `-l`'d in `a3-pub.sh` for both flag paths (per [[plan-wrapper-script-updates]]).

## 6 — B-coupling fix (manifest snapshot)

The only A.1 refactor B requires. Three small edits to `a3madkour-publish-history.el`:

1. Add defvar `a3madkour-pub--manifest-snapshot` (initially `nil`).
2. In `begin-publish`, read `data/url-history.yaml` once into the defvar (after the existing metadata-cache + org-roam-db reset).
3. In `diff-published-set`, read the manifest from the snapshot defvar instead of re-reading disk.

`record-publish` continues to write to disk eagerly (no behavior change for non-B callers — interactive M-x debugging, ad-hoc `--eval` shell invocations all keep working). The snapshot is only consulted by `diff-published-set`. `finish-publish` clears the snapshot at the end.

This means B's per-section handlers can safely call `record-publish` mid-publish: even though disk gets updated, `diff-published-set` (running inside `finish-publish` after all handlers finish) reads the pre-publish snapshot and correctly detects slug shifts.

**Why this fix vs the alternatives** (recorded for posterity): option (a) — calling `record-publish` after `finish-publish` for slug shifts — imposes per-call discipline on every B caller and is easy to forget. Option (c) — deferring all `record-publish` writes to `finish-publish` — is a larger A.1 refactor that breaks callers expecting immediate persistence. The snapshot approach is localized to A.1 code, mirrors the existing snapshot-at-publish-start semantics from parent spec §11.1, and leaves A.1.d's write semantics intact.

## 7 — Frontmatter mapping (per section)

ox-hugo gives B several mappings for free (`#+title` → `title`, `#+date` → `date`, `#+filetags` → `tags`, `#+HUGO_CUSTOM_FRONT_MATTER: :key val` → arbitrary keys). Per-section normalizers fill in the rest.

### Common across all sections

| Hugo field | Source |
|---|---|
| `title` | `#+title` |
| `draft` | `#+HUGO_DRAFT: t` → true; default false |
| `lastmod` / `last_modified` | git-mtime-of-last-commit-touching-file (or `#+HUGO_LASTMOD:` override); see §12 open issue 5 |
| `tags` | `#+filetags` (split on `:`) |
| `summary` | `#+HUGO_SUMMARY:` |

### Garden-specific

| Field | Source |
|---|---|
| `growth_stage` | derived from `:PROGRESS:` (none/highlighting → seedling; ref-notes → budding; main-notes/done → evergreen); `#+HUGO_GROWTH_STAGE:` overrides |
| `media_type` | `#+HUGO_MEDIA_TYPE:` (one of: book / album / track / game / film / series / paper / video / article / talk) |
| `creator`, `status`, `started`, `finished`, `spoiler_level`, `original_url`, `year`, `weight` | per-keyword `#+HUGO_*:` |
| `topic_map` | `#+HUGO_TOPIC_MAP: slug-1 slug-2 …` (space-delimited slug list) |
| `roam_refs` | derived from org-roam refs (existing org-roam mechanism) |

Flavor (concept / media / reference) is inferred from `media_type`: missing → concept; book/album/track/game/film/series → media; paper/video/article/talk → reference. Frontmatter `flavor:` is emitted for the Hugo template's convenience, even though `media_type` carries the same information.

### Essay-specific

| Field | Source |
|---|---|
| `date` | `#+date` |
| `series` / `series_order` | `#+HUGO_SERIES:` / `#+HUGO_SERIES_ORDER:` |
| `toc` | `#+HUGO_TOC: t/nil` |
| `featured` / `tile_size` / `hero` | per-keyword `#+HUGO_*:` |
| `has_sidenotes` / `has_citations` / `has_footnotes` / `has_math` / `has_widgets` / `has_video_sync` | derived from post-export markdown body scan (presence of `{{< sidenote >}}` / `{{< cite >}}` / `[^` footnote ref / `\(…\)` or `\[…\]` math delim / `{{< widget >}}` / `{{< video-sync >}}` respectively) — author can override via explicit `#+HUGO_HAS_<X>:` keyword |

### Research themes

`garden_topic_ref` (slug), `status` (per-keyword).

### Research questions

`parent_question`, `theme`, `supporting_notes`, `related_essays`, `status` (per-keyword; lists are space-delimited slug lists).

### Works games

`medium: game`, `game_kind`, `status`, `embed_url`, `cover_file` (per-keyword; `game_kind` not `kind` per [[hugo-reserved-fields]]).

### Works music

`medium: music`, `format`, `lyrics_poem`, `cover_file`, `audio_link`.

### Works poetry

`medium: poetry`, `collection`, `set_to_music`, `audio_url`, `audio_pill_label`; body gets the synced-poetry transform per [[phase-3-org-synced-poetry-export]] stub spec.

### Streams

`date`, `platforms`, `category`, `archive_status`, `duration`, `vod_url`, `twitch_archive_url`, `archive_url`, `related_essays`, `related_garden`, `related_research`, `related_works` (per-keyword; lists space-delimited).

### About

`title` only; static body.

### Library items (no Hugo content; YAML rows)

```yaml
- title: <heading text>
  creator: <:CREATOR: property>
  status: <:STATUS: property; medium-dependent enum>
  started: <:STARTED: property>
  finished: <:FINISHED: property>
  tags: [t1, t2, ...]   # from per-heading :tags:  ← the round-trip rule
  extras:
    isbn: <:ISBN:>
    mbid: <:MBID:>
    igdb_id: <:IGDB_ID:>
    tmdb_id: <:TMDB_ID:>
    cover_file: <:COVER_FILE:>
    original_url: <:ORIGINAL_URL:>
```

## 8 — Library pipeline detail

Library is the structural outlier; worth its own section.

### Source layout

```
~/org/notes/library-reading.org      ;; #+HUGO_PUBLISH: t  #+HUGO_SECTION: library-reading
~/org/notes/library-listening.org    ;; #+HUGO_PUBLISH: t  #+HUGO_SECTION: library-listening
~/org/notes/library-playing.org      ;; #+HUGO_PUBLISH: t  #+HUGO_SECTION: library-playing
~/org/notes/library-watching.org     ;; #+HUGO_PUBLISH: t  #+HUGO_SECTION: library-watching
```

Each file body is a list of top-level org headings:

```org
* Pride and Prejudice  :classics:romance:
  :PROPERTIES:
  :CREATOR: Jane Austen
  :STATUS: finished
  :STARTED: 2024-11-02
  :FINISHED: 2024-12-15
  :ISBN: 9780141439518
  :COVER_FILE: pride-and-prejudice.jpg
  :END:

* Lord Jim  :classics:
  :PROPERTIES:
  :CREATOR: Joseph Conrad
  :STATUS: reading
  :STARTED: 2025-04-01
  :END:
```

### Handler flow (`publish-library-file file`)

1. Parse the org file with `org-element-parse-buffer`.
2. For each top-level heading, build a YAML-row plist (per §7 schema).
3. Per-item `:tags:` round-trip into the row's `tags: [...]` (the library-tags-round-trip rule).
4. Status enum validated per medium:
   - reading ∈ {to-read, reading, finished, abandoned}
   - listening ∈ {playlist, listening, listened}
   - playing ∈ {wishlist, playing, finished, abandoned}
   - watching ∈ {to-watch, watching, watched, abandoned}
5. Write `data/<medium>.yaml` from scratch — full replace, no merge. (Org file is the source of truth; the existing per-medium yaml is regenerated each publish.)
6. Library items do NOT call `record-publish` — they aren't URL-targeted (no `/library/<medium>/<slug>/` per-item page exists; items render only inside the shelves + catalogue on `/library/`).
7. `data/library-shelves.yaml` is hand-authored and NOT touched by the publisher (shelves are a curation decision; per [[phase-3-library-tag-shelves]]).

### Cover-file binding

`:COVER_FILE: <slug>.jpg` round-trips into `extras.cover_file`. The image file itself lives at `static/library/covers/<slug>.jpg` and is committed manually (per [[library-covers-static-path]] — no hotlinking). B does NOT copy covers from `~/org/notes/assets/` because covers are a per-medium curation, not a per-note asset.

## 9 — Per-section specifics (non-library)

### Garden

Handler invokes export → frontmatter normalize → A's link-rewriter (rewrites `[[id:UUID]]` and `[[file:other.org]]` per A.1's contract) → A's asset-copy (per-page bundle under `content/garden/<slug>/`) → write index.md → record-publish. `topic_map` notes (curated tile grids) get their `topic_map` list emitted as-is — the Hugo template handles tile resolution at build time.

### Research

Two sub-discriminators inside one handler module — `research-theme` vs `research-question`. Cross-ref keywords (`theme:`, `parent_question:`, `garden_topic_ref:`, `supporting_notes:`, `related_essays:`) are space-delimited slug lists in `#+HUGO_*:` keywords. The handler validates each slug resolves to a published target (via A's `published-p`) and emits a WARN for broken refs (does not fail the publish — matches A's WARN-don't-fail discipline).

### Essays

Series + series_order keywords; toc keyword. The `has_*` boolean detection scans the post-export markdown body for the corresponding shortcode patterns and sets the frontmatter flag automatically; author can override per-essay via explicit `#+HUGO_HAS_<X>:` keyword. Essays' `hero` / `featured` / `tile_size` are pass-through.

### Works

Sub-dispatcher on `HUGO_SECTION` value. Games + music sections are standard frontmatter pass-through. **Poetry** is special: body gets the synced-poetry transform per `docs/superpowers/specs/2026-05-19-org-synced-poetry-export.md`. Output must pass the existing `check_poetry_synced` linter and the `check_works_fixtures` linter. `lyrics_poem` ↔ `set_to_music` round-trip validation (existing `check_works_links` linter enforces this on the output side; B emits both sides correctly from per-keyword lists).

### Streams

Standard frontmatter pass-through. `related_essays / related_garden / related_research / related_works` are space-delimited slug lists; symmetry validation (related_* ↔ source_stream on the linked-to page) is enforced by the existing `check_streams_links` linter on output.

### About

Single file, single output. Minimal handler — export, normalize, write `content/about/index.md`. The Now widget data is its own future surface; B does not own it.

## 10 — A → B interface usage

B consumes A.1's existing API surface (parent spec §10) directly. No new A-side functions required beyond the §6 manifest snapshot. Concrete call sites per section handler:

```elisp
(let ((section (a3madkour-pub/note-section file)))
  (when (eq section 'garden)
    (let* ((exported    (a3madkour-pub-export/export-file file))
           (frontmatter (a3madkour-pub-frontmatter/normalize 'garden
                          (plist-get exported :frontmatter) file))
           (body        (a3madkour-pub-rewrite/rewrite-links-in-string
                          (plist-get exported :body) file))
           (assets      (a3madkour-pub-assets/asset-validate-and-copy
                          file bundle-dest-dir)))
      ;; write content/garden/<slug>/index.md
      (a3madkour-pub-history/record-publish
        file-id new-url 'live :had-slug-override-p slug-overridden-p))))
```

**B → A reads:** `published-p`, `note-url`, `note-section`, `aliases-for`, `rewrite-link` / `rewrite-links-in-string`, `asset-validate-and-copy`.
**B → A writes:** `record-publish` (per-note, after writing the Hugo file).
**B → A lifecycle:** wraps each top-level command in `begin-publish` / `finish-publish`.

## 11 — Idempotency + transition strategy

### Idempotency contract (publish-living)

- Running `publish-living` with no source changes produces zero file diffs in `content/` + `data/`.
- Output files are written via "compute → if-different-from-disk → write" to avoid spurious git churn.
- Frontmatter key ordering is deterministic (alphabetical within each section's normalize function).
- ox-hugo's body output is already deterministic for a given source.
- Library YAML rows are written in source-file-order (matches the heading order in the org file).

### Transition strategy from fixtures to org-sourced content

The existing `content/{essays,garden,research,works,about}/` and `data/{reading,listening,playing,watching}.yaml` hold fixtures (obviously-dummy, per spec hard constraint). When B starts publishing real content:

- **publish-living** does a sync, not a merge: walks all published-live garden + library + research source notes, derives expected output paths, and removes any `content/<section>/<slug>/` directory (or YAML row) that's not in the expected set. This means the first real `publish-living` run on real source content will delete all matching-section fixtures.
- **publish-deliberate** is per-note — it does NOT delete other content in its section. It only writes one note's bundle.
- The author commits fixture removal in the same commit as B.x's first real-content publish, so the diff is reviewable.

### Per-section fixture handover (per slice)

| Slice | Fixtures cleared | Real content seeded |
|---|---|---|
| B.1 garden | `content/garden/*/` (except `_index.md`, `graph.md`, `history/`) | Real garden notes published from `~/org/notes/` |
| B.2 library | `data/{reading,listening,playing,watching}.yaml` overwritten | Real library items |
| B.3 research | `content/research/{themes,questions}/*/` | Real themes/questions |
| B.4 essays | `content/essays/*/` (except `_index.md`) | Real essays |
| B.5 works | `content/works/{games,music,poetry}/*/` (except `_index.md`s) | Real works items |
| B.6 streams | `content/streams/*/` (except `_index.md`) | Real stream items |
| B.7 about | `content/about/_index.md` overwritten | Real about content |

`tools/check_*_fixtures.py` linters continue to gate on the SHAPE of what's in `content/`, regardless of whether the content was fixture-authored or B-emitted. So a B-emitted garden note must still pass `check_garden_fixtures.py`.

## 12 — Testing strategy + slice ordering + open questions

### Testing

Extends parent spec §11.

- **Elisp ert tests** — per-section handler module gets its own `-test.el` sibling. Pure normalization functions tested directly; effectful handlers use tmp-dir fixtures (seeded `~/org/notes/`-shaped corpora). Expected new test count: ≈250-300 ert tests across the 11 new modules.
- **Python linter parity** — existing 24 linter pairs continue to gate the OUTPUT shape; no new linter pair required per slice (the existing pairs catch shape regressions whether the author or B wrote the file).
- **Integration tests** — `tools/test_publish_integration.py` (existing, A.1.d shipped 8 fixtures) grows new fixtures per slice. Expected count: 8 → ≈25-30 by end of B (4-5 fixtures per slice covering publish-once, idempotency, slug-shift, link-cross-ref-warn, removed-note-unpublish).
- **Per-stage manual verification** — each slice's plan enumerates a real-corpus spot-check checkpoint (e.g., "publish 3 garden notes from ~/org/notes/, eyeball `content/garden/`, verify link rewriting in browser").

### Slice ordering

Living-first carve: ship publish-living end-to-end (garden + library + research) before touching publish-deliberate. Each command's surface matures together.

| Slice | Scope | Why this order |
|---|---|---|
| B.0 | Shared infra: `-export.el`, `-frontmatter.el`, `-living.el` scaffolding, `-deliberate.el` scaffolding, `a3-pub.sh` flags, B-coupling fix in `-history.el`, init test sibling per module | Foundation; nothing user-visible until B.1 |
| B.1 | garden handler | Simplest; tests publish-living end-to-end on a single section |
| B.2 | library handler | Per-subtree pipeline; second living section; YAML emission |
| B.3 | research handler | Closes publish-living (themes + questions both) |
| B.4 | essays handler + has_* detection + series support | First publish-deliberate slice; meatiest single handler |
| B.5 | works handler (games + music + poetry) | Discharges the synced-poetry contract |
| B.6 | streams handler | Cross-ref symmetry; smaller than works |
| B.7 | about handler | Smallest module; closes B |

Each slice = own writing-plans + execute-plan cycle. Sub-sub-design specs only when a slice has architectural depth beyond what this parent spec covers (e.g., the synced-poetry transform in B.5 may want its own design refresh of the 2026-05-19 stub).

### Open questions / known issues

**Link rewriting (B.1.1, shipped 2026-05-26):** pre-export buffer rewrite via `a3madkour-pub-rewrite/rewrite-buffer-links` runs in the garden handler before ox-hugo sees the source. Helper substitutes `[[id:UUID]]` / `[[file:...]]` / `[[<type>:UUID]]` org bracket-link forms with the resolved HTML (wrapped in `@@html:...@@` org export snippets) or inert plain text for unpublished targets. Other section handlers (B.2 library, B.3 research, B.4 essays, B.5 works) should adopt the same `--rewrite-to-tmp-file` pattern. Closes the round-2 spot-check finding (Hugo `REF_NOT_FOUND` on B-emitted hyphen-slug bundles).

1. **What happens when an org file's `HUGO_SECTION` changes between publishes?** Section change = URL change (e.g., `/garden/x/` → `/essays/x/`). A.1's manifest records the new URL and adds an auto-alias from the old. B's handlers should handle this without special-casing: the old-section handler doesn't see the file (it's no longer in that section's source set), so finish-publish's Step A path catches the orphan and unpublishes the old bundle; the new-section handler emits at the new path; record-publish updates the manifest. Should work without special-casing, but call out in tests.
2. **Cover-file existence checking in library handler:** when `:COVER_FILE: <slug>.jpg` is set, B verifies `static/library/covers/<slug>.jpg` exists at publish time and emits a WARN if missing (consistent with A's WARN-don't-fail discipline); existing `check_library_covers.py` linter will fail CI if the file is referenced and missing.
3. **`#+HUGO_LASTMOD:` legacy keywords:** ~15 source files carry orphan `#+HUGO_LASTMOD:` from a prior aborted ox-hugo attempt. Parent A spec §13.7 says A.1 silently ignores them. B's frontmatter normalizer respects them (uses the keyword if present, falls back to git-mtime otherwise) — they happen to mean what we want them to mean.
4. **About Now widget:** out of scope for B; its own future slice. About handler writes only what the source contains.
5. **Idempotency vs `lastmod` git-mtime:** if `lastmod` is derived from filesystem mtime, re-running publish on an unchanged file gives the same lastmod only when the file hasn't been touched. Switch to git-mtime-of-last-commit-touching-file (or HEAD) to stay idempotent even across `touch` commands and editor saves with no content change.

### Carry-forwards to A.2 / future

- A.1 carry-forward #3 (shared-asset conflict resolution) — own design pass.
- A.2 typed-backlinks data — B leaves backlinks-data panel data stubbed at `nil`.
- B-coupling constraint — resolved by §6 in this spec.
- Streams existing cron-polling integration — B does not change it; existing `data/streams-{live,schedule,twitch-cache}.yaml` continues to work.

## 13 — Glossary

- **publish-living** — top-level B command for frequent, idempotent re-export of garden / library / research source sets.
- **publish-deliberate** — top-level B command for per-file publish of one essay / works item / streams item / about page; intended for human review.
- **manifest snapshot** — the A.1 `data/url-history.yaml` read into a defvar at `begin-publish`, used by `diff-published-set` instead of re-reading disk; introduced in §6 to fix the B-coupling ordering bug.
- **per-section handler** — one of seven elisp modules (`-garden`, `-library`, etc.) that owns the per-section frontmatter mapping + output writing.
- **library round-trip rule** — org per-heading `:tags:` must appear in the corresponding `data/<medium>.yaml` row's `tags:` array.
- **synced-poetry contract** — `[mm:ss]`-marker + `audio_url` markup shape; B.5's poetry handler must emit it correctly per the 2026-05-19 stub spec.

---

## Spec self-review checklist (per superpowers:brainstorming)

- [x] Placeholder scan — no TBDs; all section behaviors specified at a level that can be plan'd.
- [x] Internal consistency — slice ordering matches command carve (living slices ship first); fixture handover matches slice ordering; module list matches handler responsibilities described in §9.
- [x] Scope check — each slice (B.0 through B.7) is small enough for one writing-plans cycle; parent spec covers shared infra without dictating sub-slice implementation detail.
- [x] Ambiguity check — `flavor` derivation rule made explicit (§7 garden); status enums per medium enumerated (§8); growth_stage mapping explicit (§7); library YAML row schema laid out (§7 + §8).
- [x] Hard-constraint check — no AI text required, no AI visuals required, fixture-only authoring preserved through transition (per §11), accessibility constraints out of B's scope (B emits content; CSS handles a11y).
