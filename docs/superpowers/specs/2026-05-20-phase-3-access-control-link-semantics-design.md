# Phase 3 sub-project A: access control + link semantics — design

**Date:** 2026-05-20
**Status:** brainstormed; A.1.0 + A.1.a shipped; A.1.b designed (see `2026-05-20-phase-3-a1-b-link-rewriter-design.md`); A.1.b plan pending
**Phase fit:** Phase 3, sub-project **A** (foundational; precedes B–F). See `memory/project_phase_3_decomposition.md` for the 6-sub-project decomposition.
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §14 (Phase 3).
**Session policy:** no commits — author reviews + pushes manually.

## 1 — Goals

A foundational sub-project that answers, for any org file in `~/org/notes/`:

1. **Is this file published?** (and in what state: live, draft, private, removed)
2. **What URL does it become** on the website?
3. **For every link inside it, what does the link become** on the web?

A's outputs are consumed inline by sub-project **B** (the per-section publisher) via an elisp library at `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` (name TBD at plan time). The library exposes pure-ish functions for B's per-content-type publishers to call during ox-hugo export.

## 2 — Non-goals (deferred or out of scope)

- **Per-section export logic** — frontmatter shape, template choice, fixture-validation against Hugo data contracts. Belongs to **B**.
- **Subtree-mode publishing** (one heading = one Hugo page). A is file-mode only; revisit only if B's library or research design wants it.
- **Per-heading publish-gates beyond `:noexport:`.** `:noexport:` is honored as a hide mechanism inside published files; no `#+HUGO_PUBLISH:` per subtree.
- **Tombstone pages** for unpublished notes. Clean delete + URL-history record only; no placeholder pages.
- **`[cite:@key]` citation export pipeline.** Belongs to sub-project **F** (split out of C at this brainstorm). A.1 does NOT add cite-key validation — F owns that surface end-to-end.
- **Pagefind indexing.** Hugo-side via existing `data-pagefind-body` + per-template meta tags.
- **Math rendering / lint.** Sub-project **C**.
- **Definition / theorem / proof markup** for multi-target export. Sub-project **D**.
- **Per-page interactive widgets.** Sub-project **E**.

## 3 — Source-side context (recap)

`~/org/notes/` (mapped at session start 2026-05-20):

- ~174 .org files, flat structure (no garden/essays/research subdirs); subdirs are `ref-notes/` (academic papers w/ NOTER_DOCUMENT + Zotero PDFs) and `projects/` (1 file).
- Filenames are bare slugs with underscores (`bayesian_statistics.org`); org-roam UUIDs in `:ID:` properties (~95% coverage).
- ~15 files carry an orphan `#+HUGO_LASTMOD:` — residue from a prior aborted ox-hugo attempt. To be ignored / cleaned at publish.
- Tags are topical + lifecycle (`:TODO:` on ~80%). No content-type tags (`:essay:`/`:garden:`).
- Links: `[[id:UUID][display]]`, low-to-medium density. Custom typed link types defined in user's config (`supports` / `contradicts` / `extends` / `example-of` / `causes`).
- Existing `~/org/notes/public-notes/` subdir is used by an unrelated org-publish project (HTML output to `~/Workspace/website/notes`). **Sub-project A's mechanism does NOT use directory placement.**

## 4 — Source-side contract (per-file org keywords)

A file's "publish state" is determined entirely by per-file `#+KEYWORD:` lines. No directory conventions, no tag-driven gates, no property-drawer entries.

| Keyword | Required? | Semantics |
|---|---|---|
| `#+HUGO_PUBLISH:` | Required for publish | Boolean gate. Value `t` = published. Anything else / absent = private. |
| `#+HUGO_SECTION:` | Required for publish | Destination. Value validated against the site's section taxonomy (enum below). Typo → publish fails with "unknown section: X". |
| `#+HUGO_SLUG:` | Optional | Override the default title-derived slug. Use for camelCase ref-notes, evolving titles, or collision resolution. |
| `#+HUGO_DRAFT:` | Optional | `t` = exported with `draft: true` frontmatter. Visible in `hugo server --buildDrafts`; hidden from production. |
| `#+HUGO_ALIASES:` | Optional | Manual additions to the auto-aliases list. Merged with auto-aliases from URL-history. |
| `:noexport:` subtree tag | Optional | Standard org behavior, honored by ox-hugo. Hides subtrees inside published files. |

**Section taxonomy (the enum):**

```
essays
garden
research/themes
research/questions
works/games
works/music
works/poetry
library/reading
library/listening
library/playing
library/watching
streams
about
```

**Validation:** both `#+HUGO_PUBLISH: t` AND `#+HUGO_SECTION: <enum-value>` must be present for publish. Either alone → fail with a clear error. Unknown section value → fail. Files lacking `#+HUGO_PUBLISH: t` are completely ignored except for the link-graph computation step (which needs to know they exist to issue the inert-link WARN).

**Default behavior:** absent keywords = private. Default-deny is intentional; no accidental publishes.

## 5 — Slug derivation + URL stability

### Slug derivation

1. If `#+HUGO_SLUG:` is present → use its value verbatim.
2. Otherwise → derive from `#+title:`: lowercase, ASCII-fold non-ASCII (Unicode normalization), spaces → hyphens, strip punctuation. Standard slugification.

Final URL: `/<HUGO_SECTION>/<slug>/`. E.g.:

- `#+title: Bayesian Statistics` + `#+HUGO_SECTION: garden` → `/garden/bayesian-statistics/`
- `#+title: Бабушкины блины` + `#+HUGO_SLUG: babushkas-pancakes` → `/garden/babushkas-pancakes/`
- `darwicheTractableBooleanArithmetic2022.org` with `#+title: Tractable Boolean Arithmetic` + `#+HUGO_SLUG: tractable-boolean-arithmetic` (filename ignored entirely) → `/garden/tractable-boolean-arithmetic/`

### URL stability via auto-aliases

Title-derived URLs change silently when the title changes. To preserve external links:

- A.1 maintains `data/url-history.yaml` (committed to repo, mutable state).
- On each publish: for every live/draft note, compare current URL against last-recorded; if changed, append a history entry and emit Hugo `aliases: [old-url, …]` frontmatter on the new page.
- Manual `#+HUGO_ALIASES:` is merged with auto-aliases (deduplicated).

See §9 for manifest shape.

## 6 — Link rewriting contract

For every `[[…]]` link encountered in a published org file, A's rewriter produces one of:

- **A live web link**: `<a href="/section/slug/[#anchor]" [class="link-supports"]>display text</a>`
- **Inert prose**: just `display text` with no anchor (link erased, text preserved)
- **An asset reference**: copies the file + rewrites to a relative or `/notes-shared/` URL

Each rewrite returns a list of WARNs alongside its output. The publish driver aggregates WARNs and prints them at end; `--strict` flag (deferred to A.2) treats WARNs as errors.

### Per-link-type rules

| Org link form | Target state | Web output | Warning? |
|---|---|---|---|
| `[[id:UUID][text]]` | live | `<a href="/<section>/<slug>/">text</a>` | — |
| `[[id:UUID][text]]` | draft | `<a href="/<section>/<slug>/">text</a>` (Hugo gates dev vs. prod) | **WARN if source is live** ("live note links to draft target") |
| `[[id:UUID][text]]` | private / removed / unknown ID | `text` (inert prose) | **WARN** |
| `[[file:foo.org][text]]` | target has `:ID:` | Resolve to id-link; recurse rules above | — |
| `[[file:foo.org][text]]` | target lacks `:ID:` | `text` (inert prose) | **WARN** |
| `[[id:UUID::*Section][text]]` | target live, heading exists | `<a href="/<section>/<slug>/#<hugo-slug>">text</a>` — anchor slug computed by Hugo's `sanitizeAnchorNameWithHook` (registered via Goldmark `html.WithIDRenderer(...)`, source-of-truth: `gohugoio/hugo markup/goldmark/autoid.go` — **not** bare Goldmark `parser.IDs.Generate` / `auto_heading_id.go`; the two algorithms differ). Algorithm: (1) trim leading/trailing whitespace; (2) for each rune — keep `IsLetter`/`IsDigit`/`'_'` (lowercased; `IsDigit` = strictly `Nd`, so `Nl`/`No` like `Ⅳ`/`½` drop), keep `' '` and `'-'` (both append as `'-'`, no collapse), drop everything else; (3) if buffer empty, fall back to `"heading"`. Unicode letters preserved (`café` → `café`). | — |
| `[[id:UUID::*Section][text]]` | target private | `text` (inert; anchor lost) | **WARN** |
| `[[id:UUID::*Section][text]]` | target live, heading inside `:noexport:` | A.1: treated as link-to-published-file (anchor pointless but page works). A.2: detected + treated as inert. | A.1: silent. A.2: WARN. |
| `[[supports:UUID][text]]` and other custom typed links | per target state | Same as id-link rules; **plus** `class="link-supports"` (or `link-contradicts`, etc.) on the `<a>` element when the rewrite produces one (`:html` variant). When the rewrite is inert prose (`:text` variant — target private/unknown), there is no anchor to attach a class to. Drives CSS styling + A.2 typed-backlinks. | per id-link rules |
| `[[https://…][text]]` / `[[http://…][text]]` | external | `<a href="https://…">text</a>` unchanged | — |
| `[[mailto:…]]`, `[[tel:…]]` | external | Pass through unchanged | — |
| Other URL schemes (`ftp:`, `git:`, etc.) — anything that isn't `id:`/`file:`/recognized custom type | external | Pass through unchanged | — |
| `[[./assets/page/<own-slug>/foo.png]]` | image, in canonical root | Copy to `content/<section>/<slug>/foo.png`; link rewrites to `foo.png` (relative) | — |
| `[[./assets/shared/diagram.png]]` | image, in canonical root | Copy to `static/notes-shared/diagram.png`; link rewrites to `/notes-shared/diagram.png` | — |
| `[[/abs/path/random.png]]` (image, NOT in canonical root) | image, out of root | **Auto-remediate**: `git mv` source into `assets/page/<source-slug>/random.png`; rewrite the .org source link to canonical relative form; then apply normal copy rule. | INFO ("moved to canonical root") |
| Auto-remediation fails (permission denied, collision with different content) | — | Render `(missing asset: random.png)` inert marker | **ERROR** in `--strict`; WARN otherwise |
| `[[file:bar.pdf]]` (non-image, non-org, in canonical root) | other asset | Same as image rule — copied to bundle, link rewrites to relative path | — |
| `[[id:UUID][text]]` where UUID is unknown to org-roam | unknown | `text` (inert prose) | **WARN** ("unknown ID") |
| `[[./assets/...]]`, abs paths to canonical root, etc. (asset-shaped) | — | **A.1.b**: returns `:pending-asset` sentinel + WARN ("asset rewriting deferred to A.1.c"); link text passes through unchanged. **A.1.c** upgrades to real handling (rows above). | A.1.b: WARN. A.1.c: per asset-row rules. |

### Custom typed-link CSS class emission

For any link whose org form is `[[<type>:UUID][text]]` where `<type>` matches a configured custom link type (`supports`, `contradicts`, `extends`, `example-of`, `causes`):

- The `<a>` element gets `class="link-<type>"` (e.g., `class="link-supports"`) **on `:html` rewrite variants only** — i.e., when the rewriter produces an actual `<a>` element. When the link is inert prose (`:text` variant — target private/unknown), there is no anchor element to attach a class to, so no class is emitted. A.2's typed-backlinks panel surfaces inert-typed links via its own data path, not via CSS classes on rewritten link text.
- CSS rules for these classes are out of scope for A; B's per-section templates / the existing CSS bundle can use them.

### HTML escaping contract

All interpolated values in `:html` rewrite outputs — the URL/href, the display text, and (A.1.c) asset `src`/`alt` attributes — pass through a single emit-time helper `a3madkour-pub--html-escape` defined in `a3madkour-publish-rewrite.el`. The helper escapes the five HTML-sensitive characters: `&` `<` `>` `"` `'` (covering both element-body and double-quoted attribute contexts).

Decision rationale: trusted-author content keeps the practical XSS risk at zero, but a single chokepoint makes the contract auditable in one function and removes the per-caller "did I remember to escape?" burden. Display text from `[[id:UUID][literal text]]` brackets can legitimately contain `<`/`>`/`&` (math, code prose), so unescaped emit would already break rendering for honest authors. Resolved 2026-05-23 as a carry-forward from A.1.b Task 13 review. A.1.c retrofits the three A.1.b `:html` emit points (`a3madkour-publish-rewrite.el` lines ~176 / ~237 / ~275) through the helper alongside the new asset emits, with regression tests for each.

### Custom typed-link backlinks data (A.2)

A.2 will add `(a3madkour-pub/typed-backlinks id)` returning a `((<type> . (<source-id> …)) …)` alist. B's per-section templates can render this as a per-note panel. A.1 emits the data structure as `null` from the API; A.2 fills it in.

## 7 — Asset handling

### Canonical asset root

`~/org/notes/assets/` is the single canonical asset root. Two sub-folders below:

```
~/org/notes/assets/
├── page/
│   ├── <note-slug-1>/
│   │   ├── diagram.png
│   │   └── recording.mp3
│   ├── <note-slug-2>/
│   │   └── screenshot.jpg
│   └── …
└── shared/
    ├── common-figure.svg
    └── …
```

- `page/<note-slug>/` — per-note assets. Each note's assets live under its own slug-named subdir. Copied into that note's Hugo bundle on publish.
- `shared/` — flat dir for assets referenced by many notes. Copied to `static/notes-shared/` on publish (single copy regardless of how many notes reference it).

### Allowed link forms

- Relative to org file's directory: `[[./assets/page/<own-slug>/foo.png]]`, `[[./assets/shared/diagram.svg]]`
- Absolute: `[[~/org/notes/assets/page/<own-slug>/foo.png]]`, `[[/home/USER/org/notes/assets/shared/diagram.svg]]`

Either must resolve into the canonical root after path normalization.

### Pre-publish validation (in elisp library + double-checked by Python linter)

For every asset link encountered in a published file:

1. **Path is in canonical root.** Resolved to either `assets/page/<note-slug>/` or `assets/shared/`. Out-of-root paths trigger auto-remediation (§6 table).
2. **Cross-namespace use is rejected.** A link from `bar.org` to `assets/page/foo/x.png` (where `foo` is a different note's slug) fails validation. Move to `assets/shared/` to share.
3. **Source file exists.** Missing file → render `(missing asset: <name>)` inert marker + WARN (or ERROR in `--strict`).
4. **No extension restriction.** Images, PDFs, audio, video — all handled identically (copied to bundle/shared, link rewrites to relative or `/notes-shared/` URL). This lets synced-poetry audio land naturally.

### Auto-remediation flow

When a link points outside the canonical root:

1. **Determine destination**: default `assets/page/<source-note-slug>/<original-filename>`. On filename collision in destination, append a short content-hash suffix (`foo-a3b2c1.png`).
2. **Attempt move**: `git mv` if source is in a git-tracked location (preserves history); otherwise `mv`. If source FS is read-only or destination already has different content, fail this step.
3. **Rewrite the org source's link** to the new canonical relative path (publish has a visible side effect on the .org source — author sees both the asset move and the link rewrite in `git status` afterwards).
4. **Continue publishing** as if the link had been canonical all along.
5. **Log INFO** for each move performed.
6. **`--dry-run` flag** previews moves + rewrites without committing them. First-time publish on legacy notes may move many files; dry-run is the safety valve.

### Copy + cleanup

- Re-copy referenced assets on every publish (idempotent; small files; cheap).
- Stale per-page assets (in `content/<section>/<slug>/` but no longer referenced) are removed on each publish.
- Shared assets (`static/notes-shared/`) are NOT auto-cleaned — curated namespace; orphans require explicit removal (publisher can offer `--gc-shared` flag later, not in A.1).

### New linter pair (24th in CI)

`tools/check_org_assets.py` + sibling `tools/test_check_org_assets.py` (existing convention). Walks the published-org-files list (read from a manifest the elisp publisher emits — exact name TBD at plan time) and verifies:

- Every asset link resolves into canonical root
- Every asset file exists
- No cross-namespace use
- (Effectively a Python-side double-check that the elisp publish enforced its rules.)

## 8 — URL-history manifest

`data/url-history.yaml` — committed to repo, mutable state. Shape:

```yaml
notes:
  - id: 09049cd8-ba99-435d-a8f2-9c0cbf9322a4
    current_url: /garden/bayesian-statistics/
    history:
      - url: /garden/bayesian-stats/
        replaced_at: 2026-04-12T13:24:00Z
        reason: title_change   # title_change | slug_override | section_change | removed
        # `slug_override` is emitted when the caller passes `:had-slug-override-p t`
        # to `record-publish` (caller reads the source file's `#+HUGO_SLUG:` keyword).
        # `title_change` covers the case where the slug shifted because the title shifted.
    state: live   # live | draft | removed
  - id: 12340000-0000-0000-0000-000000000000
    current_url: null
    history:
      - url: /garden/old-removed-note/
        replaced_at: 2026-05-12T11:00:00Z
        reason: removed
    state: removed
```

On each publish:

- For each currently-published note: if `current_url` differs from last published URL, append a history entry and update `current_url`.
- For each removed note: set `state: removed`, `current_url: null`, append a `reason: removed` history entry.
- For new notes: insert with empty `history`.

On render: each live/draft note's frontmatter gets `aliases: [<all-prior-urls-from-history>]` merged with manual `#+HUGO_ALIASES:`.

## 9 — Unpublish flow

1. Walk all org files; build the new published-set (live + draft).
2. Diff against `url-history.yaml`'s currently-`state: live` + `state: draft`.
3. For each note that *was* published and isn't anymore:
   - Delete `content/<section>/<slug>/` from the Hugo tree
   - Update its `url-history.yaml` entry: `state: removed`, append event with `reason: removed`
   - Add to "removed-this-publish" set
4. For each LIVE published note, re-check all outgoing links. Those pointing at removed-this-publish targets get inert + WARN (per §6 table).
5. `--check-orphans` flag (CLI option on the publish command): runs steps 1–2, prints "would remove: …" and "would inert these external refs: …", and exits without committing changes.

## 10 — A → B interface (the elisp library API surface)

Library path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` (name and exact path TBD at writing-plans time).

Surface (sketch — exact function names refined at plan time):

```elisp
;; Published-set queries
(a3madkour-pub/published-p file-or-id)
  ; → 'live | 'draft | nil

(a3madkour-pub/note-url id)
  ; → "/<section>/<slug>/" | nil

(a3madkour-pub/note-section id)
  ; → 'garden | 'essays | ... | nil

;; Link rewriting — called inline by B's per-section publishers
(a3madkour-pub/rewrite-link org-link source-note-id)
  ; → (:html "<a ...>text</a>" :warnings (...))
  ;  | (:inert "text" :warnings (...))
  ;  | (:asset relative-or-shared-path :warnings (...))             ; A.1.c
  ;  | (:pending-asset original-link-text :warnings (...))          ; A.1.b stub for asset-shaped links

;; Asset handling
(a3madkour-pub/asset-validate-and-copy org-file bundle-dest-dir)
  ; → (:copied (file ...) :warnings (...) :errors (...))

;; URL history
(a3madkour-pub/record-publish id new-url state &key had-slug-override-p)
  ; → updates `data/url-history.yaml`
  ; :had-slug-override-p t when source file has `#+HUGO_SLUG:` (drives slug_override reason)

(a3madkour-pub/aliases-for id)
  ; → ("/garden/old/" "/garden/older/")

;; Unpublish flow
(a3madkour-pub/diff-published-set old new)
  ; → (:added (...) :removed (...) :stayed (...))

(a3madkour-pub/check-orphans)
  ; → (list of warnings); no side effects

;; A.2 — deferred
(a3madkour-pub/typed-backlinks id)
  ; → ((supports . (id1 id2)) (contradicts . (...)))
  ; A.1 returns nil for everything; A.2 fills in.
```

**State files A reads/writes:**

- `data/url-history.yaml` (canonical; committed to repo)
- The library does NOT touch `library.bib` (citations live in F)

**Site repo coupling:** Site is NOT self-contained — it depends on the elisp library living in dotfiles. CI doesn't run elisp; it consumes the committed `content/` + `data/url-history.yaml` outputs. Documented as a known dependency.

## 11 — Testing strategy

| Layer | What | How |
|---|---|---|
| **Elisp unit tests** | Each function in the library has an `ert` test. Pure functions are unit-tested directly; effectful ones use a tmp-dir fixture with seeded org files. | New file `a3madkour-publish-test.el` adjacent to the library. Batch runner: `emacs --batch -l ert -l publish-test.el -f ert-run-tests-batch-and-exit`. |
| **Python linter pair** | `tools/check_org_assets.py` + sibling `tools/test_check_org_assets.py` (24th pair). | Same pattern as the existing 23 linter pairs; CI runs linter then sibling test. |
| **Integration tests** | End-to-end: seeded `~/org/notes/` tmp-dir → run publish → assert resulting `content/` tree shape, `data/url-history.yaml` shape, captured WARN output. | New script `tools/test_publish_integration.py` (Python orchestrator that shells to `emacs --batch` to invoke the elisp publisher on the fixture corpus). |
| **Per-stage manual verification** | After each commit/stage of A.1, author runs the publish on a representative seeded org corpus + spot-checks the diff. | Plan doc enumerates explicit verification checkpoints per stage: seed corpus location, command to run, expected diff highlights. Author signals OK before the plan advances. |

**Manual-verification cadence:** every stage in the implementation plan gets a labeled checkpoint. The plan doesn't advance until the author runs the checkpoint and confirms.

### Snapshot-at-publish-start semantics (introduced in A.1.b)

A publish run takes two snapshots at start:

1. **Metadata cache** — per-publish-run hash table (`a3madkour-pub--metadata-cache`) keyed by absolute file path. `note-metadata` and the 4 public accessors (`published-p`/`note-section`/`note-slug`/`note-url`) hit the cache after first read. Reset explicitly at publish start.
2. **org-roam DB sync** — `(org-roam-db-sync)` invoked at publish start. Guarantees ID resolution sees current on-disk state.

**Consequence:** edits to org files made *during* a publish run are NOT picked up. Author re-runs publish to see changes. This is acceptable for both shell-invoked (`a3-pub.sh`) and interactive-emacs (`M-x`) publish — the library does not assume one context over the other. Documented in each affected accessor's docstring.

## 12 — A.1 vs. A.2 scope split

### A.1 — ships first (this spec)

1. Publication gate + keyword validation + section enum
2. Slug derivation (title-derived + `HUGO_SLUG` override)
3. URL-history manifest + auto-aliases on title/slug/section change
4. Link rewriting: id-links, file-links (auto-convert), heading-anchors, external URLs, custom typed links **as CSS classes only**
5. Inert text + publish-time WARN for links into unpublished targets
6. Asset canonical folder + pre-publish validation + auto-remediation + per-page bundle copy + 24th linter pair
7. Unpublish flow + `--check-orphans` preview flag
8. Draft mode: `HUGO_DRAFT: t` → frontmatter pass-through + warn when a live note links to a draft target
9. elisp library API surface for B (with `typed-backlinks` returning nil)
10. Tests: elisp ert unit tests + Python linter sibling + integration test + per-stage manual-verification checkpoints

### A.2 — ships after A.1 + B's first content-type slice (queued sub-project)

1. Typed-backlinks data computation (`(a3madkour-pub/typed-backlinks id)` fills in real data)
2. `:noexport:` subtree handling inside the link rewriter (link into an `:noexport:` subtree → treated as inert)
3. `--strict` mode (fail-on-warn for hygiene-conscious publishes)
4. (Possibly) `--gc-shared` flag for cleaning orphan shared assets

## 13 — Open questions / known issues

1. **URL stability of heading anchors:** title-derived URLs get auto-aliases; heading-text-derived anchors do NOT (would require per-heading URL history — out of scope). Documented caveat: renaming a heading = potential deep-link rot. Mitigation: give frequently-deep-linked headings an `:ID:` and use `#anchor-from-id` (Hugo handles this if heading templates emit the ID-based anchor).
2. **Live → draft link gotcha:** Hugo excludes drafts in production → live note linking to a draft target produces a 404. A.1's publish-time WARN surfaces this; author's responsibility to promote the draft or rewrite the source. No automatic fallback.
3. **Cross-namespace asset use:** rejected by validator. If you want shared screenshots, `assets/shared/` is the answer.
4. **Slug collision:** if two notes derive to the same `<section>/<slug>` (e.g., two notes both titled "Bayesian Statistics" both targeting `garden`), publish fails with a collision error pointing at both files. Author resolves by setting `#+HUGO_SLUG:` on one.
5. **Both `#+HUGO_PUBLISH:` and `#+HUGO_SECTION:` are required together.** Setting just one = publish fails with a clear "both required" error. Intentional default-deny.
6. **Site repo is not self-contained:** depends on `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`. CI doesn't run elisp; it consumes the committed `content/` + `data/` outputs only.
7. **`#+HUGO_LASTMOD:` legacy keywords:** ~15 files have orphan `#+HUGO_LASTMOD:` from a prior aborted ox-hugo attempt. A.1 silently ignores them. Cleanup is optional; author can remove at leisure.

## 14 — Dependencies on other sub-projects

**A.1 stands alone** (no dependency on B/C/D/E/F).

**A.2 depends on B's first content-type slice** (needs B's typed-backlinks panel template design to validate the panel data shape).

**Downstream sub-projects consume A.1:**

- **B** calls A's link rewriter + published-set queries inline; reads + writes nothing in A's manifest directly.
- **F** (citation pipeline) uses A's published-set predicate to scope cite-key validation to published files only.
- **C, D, E** don't directly consume A but ride on top of B (which rides on A).

## 15 — Glossary

- **A.1** — the v1 ship of sub-project A (this spec).
- **A.2** — the deferred follow-on covering typed-backlinks data + `:noexport:` link handling + `--strict` mode. Own spec, plan, ship.
- **canonical asset root** — `~/org/notes/assets/`.
- **inert text** — link's display text rendered as plain prose (no anchor).
- **live / draft / private / removed** — the four states a note can be in. Live = published + visible in production. Draft = published + visible only in `hugo server --buildDrafts`. Private = no `#+HUGO_PUBLISH: t`. Removed = was published, no longer is.
- **published-set** — the set of all currently-live + currently-draft notes (queried by A's `published-p`).
- **URL-history manifest** — `data/url-history.yaml`, A.1's mutable state file.

---

## Spec self-review checklist (per superpowers:brainstorming)

- [x] Placeholder scan — no TBDs except deliberately marked "at writing-plans time" items (exact function names, library path-name)
- [x] Internal consistency — A.1/A.2 split is consistent throughout; non-goals list matches what's deferred elsewhere
- [x] Scope check — A.1 is focused; A.2 is its own future spec; F is split out cleanly
- [x] Ambiguity check — link-rewriting table covers every form; asset-handling covers every flow; validation rules are concrete

Ready for author review.
