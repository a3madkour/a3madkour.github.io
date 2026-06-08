# Phase 3 sub-project B.4 — essays handler

**Status:** design (brainstormed 2026-05-31)
**Parent spec:** `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` (sub-project B — per-content-type publisher + templates)
**Sequence:** B.0 → B.1 → B.1.1 → B.2 → B.3 → **B.4** → B.5 → B.6 → B.7 (per parent spec §12)
**Prior slice memories:** [[b3-complete]] (B.3 shipped 2026-05-31), [[b2-complete]] (B.2 shipped 2026-05-30), [[b1-complete]] (B.1+B.1.1 shipped 2026-05-25/26), [[b0-complete]] (B.0 shipped 2026-05-25), [[next-slice]] (queued pointer).

---

## 1 — Goals & non-goals

### Goals

Ship the essays handler — the **first `publish-deliberate` slice**. Per-essay org sources at `~/org/essays/<slug>.org` (kitchen-sink + 3 narrow stubs, mirroring B.3's stub-handover pattern) become Hugo bundles at `content/essays/<slug>/index.md` via `M-x a3-publish-deliberate <file>` / `a3-pub.sh --publish-deliberate <path>`.

B.4 also lands the **B.0 finish-publish `:scope` contract amend** — without it, the first deliberate publish would catastrophically unpublish every other bundle (Step A unpublish sweep treats "missing from accumulator" as "removed"). Folded in here because the gap is too small to warrant its own slice.

### In scope

- New `a3madkour-publish-essays.el` module + `-test.el` sibling.
- New defvar `a3madkour-pub/essays-dir` (default `~/org/essays/`).
- Register `'essays` handler entry in `a3madkour-pub-deliberate--handlers`.
- `finish-publish :scope 'deliberate` keyword (B.0 contract amend) — skip Step A unpublish + Step C re-link-check; Step B narrowed to the single touched-id's slug-shift.
- `has_*` post-export body scan (6 flags) with per-keyword `#+HUGO_HAS_<X>:` override.
- Series support (`#+HUGO_SERIES:` + `#+HUGO_SERIES_ORDER:`).
- `tile_size` / `featured` / `hero` / `source_stream` pass-through.
- Per-page hero asset handling via existing A.1.c `asset-validate-and-copy`.
- 4 stub source files in `~/org/essays/` (author-local, not git-tracked) — one kitchen-sink + 3 narrow.
- Retirement of the 7 hand-authored essay fixtures in the slice's final commit.
- `a3-pub.sh` `-l a3madkour-publish-essays` wire-up (per [[plan-wrapper-script-updates]]).

### Non-goals

- **Citation pipeline** (`[cite:@key]` parsing, `data/citations.yaml` emission) — sub-project F.
- **KaTeX runtime / math validators** — sub-project C.
- **Widget / video-sync runtime** — sub-project E.
- **`essay-references.html` partial behavior** — unchanged; reads `data/citations.yaml` as today.
- **Now widget on About** — separate future slice (B.7).
- **`a3-unpublish-deliberate <id>`** — known limitation; future follow-up.
- **Essay-to-essay cross-ref via org-roam ID** — out of scope (plain markdown links cover the gap; future F-era cite-shortcode).
- **B.5+ handlers** (works / streams / about) — own slices.

---

## 2 — Module structure

```
~/dotfiles/emacs-configs/custom/lisp/
├── a3madkour-publish-essays.el         [NEW]   handler module (~220 LoC)
├── a3madkour-publish-essays-test.el    [NEW]   ert sibling
├── a3madkour-publish-deliberate.el     [MOD]   register 'essays handler entry
├── a3madkour-publish-unpublish.el      [MOD]   finish-publish :scope kwarg
├── a3madkour-publish-unpublish-test.el [MOD]   deliberate-scope tests
├── a3madkour-publish-frontmatter.el    [MOD]   add 'essays normalizer arm
├── a3madkour-publish-frontmatter-test.el [MOD] tests for essays normalizer
├── a3madkour-publish.el                [MOD]   defvar a3madkour-pub/essays-dir
└── (a3-pub.sh)                          [MOD]  -l a3madkour-publish-essays intercept

~/org/essays/                            [stub sources, author-local, Syncthing-synced]
├── example-one.org                     [NEW]  kitchen sink — every feature
├── example-two.org                     [NEW]  series part 2 (pairs with example-one)
├── example-three.org                   [NEW]  minimal (all has_* negative; no optional keys)
└── example-four.org                    [NEW]  has_* keyword override demo

~/Sync/Workspace/a3madkour.github.io/
├── content/essays/example-essay-*      [DEL]   hand-authored fixtures retired (7)
├── content/essays/example-*            [NEW]   B-emitted bundles (4)
├── tools/test_publish_integration.py   [MOD]   add TestEssaysPublishDeliberate
└── docs/superpowers/specs/2026-05-31-phase-3-b-4-essays-handler-design.md [NEW]
```

**Module naming**: `-essays.el` (plural) for consistency with the `'essays` section symbol and the `essays/` URL section. Parent B spec table called it `-essay.el` (singular); overriding because B.3 used `-research.el` for `'research` → plural-matches-section is the established convention.

---

## 3 — Source-side contract

### 3.1 Location

Essays live at `~/org/essays/<slug>.org` — a new directory the author creates. **Not under `~/org/notes/`. Not org-roam-indexed.** Not git-tracked (Syncthing-synced like notes).

New defvar `a3madkour-pub/essays-dir` (default `~/org/essays/`), parallel to existing `a3madkour-pub/org-notes-dir`.

### 3.2 Cross-reference model (asymmetric)

- **Essay → note** via `[[id:UUID-of-note]]` org-roam link. A.1's rewriter resolves the UUID via `org-roam-id-find` and emits `/garden/<slug>/`. Works because notes are roam-indexed.
- **Note → essay** is NOT a direct ID link. Author creates a ref-note in `~/org/notes/ref-notes/` that references the published essay URL (existing ref-notes flow). The ref-note renders as a normal garden card and surfaces the connection on the garden surface.
- **Essay → essay** out of B.4 scope. Plain markdown link or future cite-shortcode if needed later.

### 3.3 Org file shape

```org
:PROPERTIES:
:ID:       <uuid>
:END:
#+title: Example essay one
#+date: 2026-04-12
#+filetags: :example-tag-a:example-tag-b:example-tag-c:
#+HUGO_PUBLISH: t
#+HUGO_SECTION: essays
#+HUGO_SUMMARY: Lorem ipsum dolor sit amet…
#+HUGO_TILE_SIZE: large
#+HUGO_FEATURED: t
#+HUGO_HERO: hero.svg
#+HUGO_TOC: t
#+HUGO_SERIES: example-series
#+HUGO_SERIES_ORDER: 1
#+HUGO_SOURCE_STREAM: 2026-04-22-example-music-jam-stream
# Optional has_* override — absent means body-scan:
# #+HUGO_HAS_MATH: nil

* Section one — example heading
Lorem ipsum. {{< cite "example-source-1" >}}

Lorem ipsum.[fn:1]

* Section two — example heading
Lorem ipsum. {{< sidenote >}}Lorem ipsum sidenote — example one.{{< /sidenote >}}

[fn:1] Lorem ipsum footnote — example one two three.
```

Hugo shortcodes (`{{< sidenote >}}` / `{{< cite >}}` / `{{< widget >}}` / `{{< video-sync >}}` / `{{< math >}}` / `{{< figure >}}`) written verbatim — ox-hugo pass-through. Footnotes use `[fn:N]` → `[^N]`. Series is the `#+HUGO_SERIES:` + `#+HUGO_SERIES_ORDER:` keyword pair.

### 3.4 Hero asset

`#+HUGO_HERO: hero.svg` references `~/org/essays/assets/<essay-id>/hero.svg` (parallel to notes' `~/org/notes/assets/<note-id>/`). A.1.c's `asset-validate-and-copy` copies it to the per-page bundle. Author hand-authors the SVG (no AI visuals per CLAUDE.md hard constraint).

### 3.5 Frontmatter mapping

Output `content/essays/<slug>/index.md` frontmatter:

| Hugo field | Source | Notes |
|---|---|---|
| `title` | `#+title` | ox-hugo built-in |
| `date` | `#+date` | required |
| `lastmod` | `:LAST_MODIFIED:` drawer → `#+HUGO_LASTMOD:` → git-mtime of last commit → fs-mtime → today | B.3 cascade (closes B.1.x #10) |
| `draft` | `#+HUGO_DRAFT: t` else `false` | |
| `summary` | `#+HUGO_SUMMARY:` | |
| `tags` | `#+filetags` | |
| `series` | `#+HUGO_SERIES:` (string; `""` when absent) | always emitted for linter parity |
| `series_order` | `#+HUGO_SERIES_ORDER:` (int; `0` when absent) | always emitted |
| `toc` | `#+HUGO_TOC: t/nil` (default `true`) | |
| `tile_size` | `#+HUGO_TILE_SIZE:` (medium / large) | optional; omit when absent |
| `featured` | `#+HUGO_FEATURED: t` | optional |
| `hero` | `#+HUGO_HERO:` | optional; asset-validate-and-copy fires when set |
| `source_stream` | `#+HUGO_SOURCE_STREAM:` | optional |
| `has_sidenotes` | scan post-export body for `{{< sidenote ` | override `#+HUGO_HAS_SIDENOTES:` |
| `has_citations` | scan for `{{< cite ` | override `#+HUGO_HAS_CITATIONS:` |
| `has_footnotes` | scan for `[^N]` markdown footnote ref | override `#+HUGO_HAS_FOOTNOTES:` |
| `has_math` | scan for `{{< math ` or `\(` or `\[` | override `#+HUGO_HAS_MATH:` |
| `has_widgets` | scan for `{{< widget ` | override `#+HUGO_HAS_WIDGETS:` |
| `has_video_sync` | scan for `{{< video-sync ` | override `#+HUGO_HAS_VIDEO_SYNC:` |

**Override semantics**: keyword present → keyword wins absolutely (`t`/`nil` → `true`/`false`). Keyword absent → body scan determines. Default `false` when scan negative.

### 3.6 Living vs deliberate scope

`publish-living` does NOT walk `~/org/essays/`. Essays are deliberate-only. `walk-published-source-set` stays scoped to `org-notes-dir`. Essay removal/rename outside a deliberate run is manual (delete bundle + edit manifest by hand). A future B.X follow-up may add `a3-unpublish-deliberate <id>`.

---

## 4 — finish-publish `:scope` keyword (B.0 contract amend)

`finish-publish` currently treats the per-run accumulator as the full new-set. For `publish-deliberate`, the accumulator has only the one file touched → Step A's "removed = manifest-not-in-new-set" would unpublish every other bundle. First-ever deliberate run nukes the site.

Threading a `:scope` kwarg through `finish-publish` fixes this.

### 4.1 New signature

```elisp
(cl-defun a3madkour-pub/finish-publish (&key dry-run (scope 'living))
  ...)
```

- `scope` ∈ `{'living, 'deliberate}`. Default `'living` (current behavior; all existing callers stay correct).
- `publish-deliberate` calls `(finish-publish :scope 'deliberate)`.
- `publish-living` calls `(finish-publish)` — unchanged.

### 4.2 Step-by-step behavior

| Step | `'living` | `'deliberate` |
|---|---|---|
| Read accumulator → new-set | yes | yes |
| Step A — unpublish removed | runs (diff vs manifest; deletes orphan bundles) | **skipped entirely** |
| Step B — slug-shift sync | runs over all diff'd shifts | **narrowed**: lookup the single accumulator entry's id in the manifest; if `current_url` ≠ new URL just recorded, apply asset-rename + bulk-link-rewrite + old-bundle-delete for that one shift only |
| Step C — re-link-check | runs against the removed-set | **skipped** (no removed-set produced) |
| Manifest snapshot cleared | yes | yes |

### 4.3 Returned plist

Same shape; `:removed` always nil under `'deliberate`; `:slug-shifted` at most one entry. Callers that ignore the return value (interactive M-x flow) unaffected.

### 4.4 Tests (added to `a3madkour-publish-unpublish-test.el`)

1. `deliberate-skips-step-a-when-accumulator-has-one-entry` — seed manifest with 3 ids; accumulator has 1; call with `:scope 'deliberate`; assert no bundles deleted, no `record-publish 'removed` calls.
2. `deliberate-step-b-narrows-to-touched-id` — seed manifest with id-A at old-url; accumulator has id-A at new-url AND id-B in the manifest with a different shifted url that the deliberate run does NOT see; assert id-A's slug-shift fires, id-B's does not.
3. `deliberate-step-c-skipped` — seed manifest with a removed id; deliberate scope; assert orphan-warnings nil (no recheck ran).
4. `living-default-unchanged` — existing tests stay green with default `:scope 'living`.

---

## 5 — Essays handler module

`a3madkour-publish-essays.el` — single new module, ~220 LoC. Mirrors B.3's structural pattern.

### 5.1 Public entry

```elisp
(defun a3madkour-pub-essays/publish-essay-file (file)
  "Publish a single essay FILE to content/essays/<slug>/index.md.

Pipeline:
  pre-export-rewrite-links (shared rewrite-to-tmp-file)
  → export (ox-hugo)
  → has-* body-scan + frontmatter normalize
  → asset-validate-and-copy
  → write-if-different
  → record-publish")
```

Registered in `a3madkour-pub-deliberate--handlers` as `'(essays . a3madkour-pub-essays/publish-essay-file)`.

### 5.2 Pipeline steps

1. **Resolve metadata** via `(a3madkour-pub/note-metadata file)` → `(:id :slug :section)`.
2. **Pre-export rewrite** via shared `(a3madkour-pub-rewrite/rewrite-to-tmp-file file id "a3-pub-essays")` (extracted in commit `f3b7e15`).
3. **Export** via `(a3madkour-pub-export/export-file tmp-src)` → `(:frontmatter :body)`. `unwind-protect` deletes tmp-src.
4. **Inject description** via existing `frontmatter-inject-description` (unchanged from B.3).
5. **Normalize** via new dispatch entry `(a3madkour-pub-frontmatter/normalize 'essays raw-fm file)`.
6. **Scan body for `has_*`** — private helper `a3madkour-pub-essays--scan-has-flags` returns 6-key plist; merged into normalized fm with keyword-override priority.
7. **Asset copy** via `(a3madkour-pub/asset-validate-and-copy file bundle-dir)` — handles hero.svg.
8. **Write bundle** via `write-if-different`; rendered fm reuses garden's render helper (or local copy — extraction deferred per §8).
9. **Record publish** via `(a3madkour-pub-history/record-publish id new-url 'live)`.

### 5.3 has_* scanner

```elisp
(defun a3madkour-pub-essays--scan-has-flags (body)
  "Return plist of (:has_sidenotes T/NIL :has_citations T/NIL ...)
derived from substring scan of BODY (post-export markdown)."
  (list :has_sidenotes  (and (string-match-p "{{< sidenote "    body) t)
        :has_citations  (and (string-match-p "{{< cite "         body) t)
        :has_footnotes  (and (string-match-p "\\[\\^[^]]+\\]"    body) t)
        :has_math       (and (or (string-match-p "{{< math "     body)
                                 (string-match-p "\\\\("         body)
                                 (string-match-p "\\\\\\["       body)) t)
        :has_widgets    (and (string-match-p "{{< widget "       body) t)
        :has_video_sync (and (string-match-p "{{< video-sync "   body) t)))
```

Override merge: normalize reads `#+HUGO_HAS_<X>:` from raw frontmatter; if present, that wins; else scanner result wins; defaults `false` for negative scan.

### 5.4 Essays normalizer (`'essays` dispatch entry)

Lives in `a3madkour-publish-frontmatter.el` (existing module; B.4 adds a dispatch arm). Responsibilities:

- Map ox-hugo's raw frontmatter keys to the essay-fixture-required keys (CLAUDE.md contract: 14 required + 4 optional).
- Coerce `series` to `""` when absent, `series_order` to `0` when absent — fixture linter requires the keys always present.
- Coerce `draft` / `featured` / `toc` to bool; `toc` defaults `true`.
- Apply the `has_*` override merge per §5.3.
- `lastmod` cascade per §3.5.
- Drop any frontmatter keys NOT in the essay contract (defensive — ox-hugo sometimes emits noise).

### 5.5 Ert tests (~28 expected)

- `scan-has-flags-*` — 12 tests: one positive + one negative per flag (6×2).
- `normalize-essays-required-keys-present` — assert all 14 required keys emitted on a minimal raw fm.
- `normalize-essays-series-defaults` — empty series fields default to `""` / `0`.
- `normalize-essays-optional-keys-omitted-when-absent` — `tile_size` / `featured` / `hero` / `source_stream` absent → key not present in output.
- `normalize-essays-has-override-wins` — keyword `nil` beats positive scan.
- `normalize-essays-has-scan-fills-when-keyword-absent` — keyword absent → scan determines.
- `normalize-essays-lastmod-cascade` — 5 tests covering each tier.
- `publish-essay-file-end-to-end-stubbed` — full pipeline call with stubbed export + assets.
- `publish-essay-file-records-publish-with-correct-url` — record-publish called with `/essays/<slug>/`.
- `publish-essay-file-no-hero-skips-asset-copy` — hero absent → asset-validate-and-copy NOT called for hero.svg.

---

## 6 — Integration tests + stub source files

### 6.1 Integration tests (Python, `tools/test_publish_integration.py`)

New `TestEssaysPublishDeliberate` class — ~7 tests, mirroring B.3's `TestResearchPublishLiving` pattern. Each spins up a tmp `~/org/essays/`-shaped corpus, invokes the publisher via `emacs --batch`, asserts on `content/essays/` output + manifest + stderr.

| Test | Coverage |
|---|---|
| `test_essay_publish_once` | Single essay → bundle written + manifest updated + correct frontmatter shape |
| `test_essay_publish_idempotent` | Second `--publish-deliberate` on unchanged source → zero file diff (mtime preserved) |
| `test_essay_slug_shift` | Title change → finish-publish Step B (deliberate-scoped) renames asset dir + rewrites referring source links + deletes old bundle |
| `test_essay_deliberate_does_not_touch_other_sections` | Seed manifest with 2 garden + 1 essay; deliberate-publish the essay; assert garden bundles untouched, no `'removed` calls |
| `test_essay_has_flags_scan_detects_each_shortcode` | One essay per shortcode pattern (6 sub-cases) → emitted frontmatter has corresponding `has_*` true |
| `test_essay_has_keyword_override_wins` | Source has `{{< sidenote >}}` AND `#+HUGO_HAS_SIDENOTES: nil` → emitted `has_sidenotes: false` |
| `test_essay_yaml_passes_site_linter` | B-emitted bundle passes `tools/check_fixtures.py` shape check |

Brings the integration test count from 26 → ~33.

### 6.2 Stub source files (author-local, `~/org/essays/`)

Author hand-creates 4 stubs during implementation for real-corpus spot-check:

| Stub | Exercise dimensions |
|---|---|
| `example-one.org` | **Kitchen sink**: featured + hero + tile_size=large + source_stream + series="example-series" + series_order=1 + toc + sidenotes + citations + footnotes + math + widget + video-sync + figures + code blocks + deep heading nesting (level-4) |
| `example-two.org` | series="example-series" + series_order=2 — pairing with example-one (validates series-nav across multiple essays) |
| `example-three.org` | Minimal — bare body, no shortcodes, no hero, no source_stream (negative case: all `has_*` false; optional keys omitted) |
| `example-four.org` | Has_* keyword override demo — body has `{{< sidenote >}}` AND `#+HUGO_HAS_SIDENOTES: nil` → emitted `has_sidenotes: false` |

Each stub uses filler text only (lorem ipsum / "Example N") per [[feedback_filler_text_only]].

### 6.3 `example-one.org` reference template

**Shortcode syntax note.** Raw `{{< X >}}` written in org body text gets HTML-encoded by ox-hugo (`&lt;cite ...&gt;` reaches the rendered page). Wrap every Hugo shortcode in an `@@hugo:...@@` export-snippet so it survives export as raw markup. For paired shortcodes, wrap both the open and close tags (the inner content stays as plain org). The B.4 has-marker scanner reads org-source + post-export body together, so either form is detected — but only the export-snippet form actually renders correctly.

```org
:PROPERTIES:
:ID:       essay-one-uuid-placeholder
:END:
#+title: Example essay one
#+date: 2026-04-12
#+filetags: :example-tag-a:example-tag-b:example-tag-c:
#+HUGO_PUBLISH: t
#+HUGO_SECTION: essays
#+HUGO_SUMMARY: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
#+HUGO_TILE_SIZE: large
#+HUGO_FEATURED: t
#+HUGO_HERO: hero.svg
#+HUGO_TOC: t
#+HUGO_SERIES: example-series
#+HUGO_SERIES_ORDER: 1
#+HUGO_SOURCE_STREAM: 2026-04-22-example-music-jam-stream

* Section one — example heading
Lorem ipsum. @@hugo:{{< cite "example-source-1" >}}@@

Lorem ipsum.[fn:1]

#+begin_src python
def example(x, y):
    return x + y
#+end_src

** Subsection one.a — example
Lorem ipsum. @@hugo:{{< sidenote >}}@@Lorem ipsum sidenote — example one.@@hugo:{{< /sidenote >}}@@

*** Subsubsection one.a.i — example
Lorem ipsum.

**** Deep subsection one.a.i.A — example
Deep heading; stresses TOC scrollspy collapse.

* Section two — example heading
@@hugo:{{< math >}}@@\alpha + \beta = \gamma@@hugo:{{< /math >}}@@

@@hugo:{{< figure src="hero.svg" caption="Example figure one — placeholder caption." alt="" >}}@@

@@hugo:{{< widget src="example-widget" >}}@@

@@hugo:{{< video-sync src="example.mp4" >}}@@

@@hugo:{{< figure src="hero.svg" caption="Example figure two — placeholder caption." alt="" class="wide" >}}@@

[fn:1] Lorem ipsum footnote — example one two three.
```

The hero SVG (`~/org/essays/assets/essay-one-uuid-placeholder/hero.svg`) author hand-copies/draws.

### 6.4 Fixture retirement

Hand-authored fixtures retired in the slice's final commit:

```
content/essays/example-essay-one/         [DEL]
content/essays/example-essay-two/         [DEL]
content/essays/example-essay-three/       [DEL]
content/essays/example-figures-essay/     [DEL]
content/essays/example-series-part-1/     [DEL]
content/essays/example-series-part-2/     [DEL]
content/essays/example-deep-toc-essay/    [DEL]
```

Replaced by 4 B-emitted bundles under `content/essays/example-{one,two,three,four}/`. The `_index.md` stays (section index, not per-essay page).

---

## 7 — Tasks, ordering, and verification gates

### 7.1 Task list

| # | Task | Module / file | Test count |
|---|---|---|---|
| 1 | `essays-dir` defvar + a3-pub.sh wiring | `a3madkour-publish.el`, `a3-pub.sh` | 2 ert |
| 2 | finish-publish `:scope` kwarg + Step A/B/C narrowing | `a3madkour-publish-unpublish.el` | 4 ert (§4.4) |
| 3 | Essays normalizer dispatch entry | `a3madkour-publish-frontmatter.el` | 5 ert |
| 4 | has_* scanner helper | `a3madkour-publish-essays.el` | 12 ert (6×2) |
| 5 | has_* override merge logic | `a3madkour-publish-essays.el` | 2 ert |
| 6 | lastmod cascade for essays | `a3madkour-publish-frontmatter.el` | 5 ert |
| 7 | Series defaults coercion (`""` / `0`) | `a3madkour-publish-frontmatter.el` | 2 ert |
| 8 | `publish-essay-file` pipeline | `a3madkour-publish-essays.el` | 3 ert |
| 9 | Register `'essays` handler in deliberate alist | `a3madkour-publish-deliberate.el` | 1 ert |
| 10 | a3-pub.sh `-l a3madkour-publish-essays` intercept | `a3-pub.sh` | (manual smoke) |
| 11 | Integration: publish-once | `test_publish_integration.py` | 1 |
| 12 | Integration: idempotency | same | 1 |
| 13 | Integration: slug-shift (deliberate-scoped Step B) | same | 1 |
| 14 | Integration: deliberate-doesn't-touch-other-sections | same | 1 |
| 15 | Integration: has_* scan + override + linter parity | same | 3 |
| 16 | **Real-corpus spot-check** | author runs against 4 stubs; eyeballs output | manual |
| 17 | Fixture retirement + final commit | `content/essays/` | (CI) |

Totals: ~37 new ert + 7 integration. End state: 393 ert + 33 integration (from 356 / 26).

### 7.2 Slice ordering rationale

- **finish-publish `:scope` (task 2) before any essay-handler code** — all deliberate-mode integration tests depend on it. Landing it first keeps the dependency direction clean.
- **Normalizer (task 3) before scanner (task 4)** — normalizer is the API surface scanner integrates into.
- **Real-corpus spot-check (task 16) before fixture retirement (task 17)** — author needs visual verification before deleting the hand-authored set.

### 7.3 Spot-check checklist (task 16)

Author runs on their machine:

```bash
$ a3-pub.sh --publish-deliberate ~/org/essays/example-one.org
$ a3-pub.sh --publish-deliberate ~/org/essays/example-two.org
$ a3-pub.sh --publish-deliberate ~/org/essays/example-three.org
$ a3-pub.sh --publish-deliberate ~/org/essays/example-four.org
```

Verifies:

- 4 bundles land at `content/essays/example-{one,two,three,four}/index.md`.
- `example-one/hero.svg` copied from `~/org/essays/assets/<id>/hero.svg`.
- Frontmatter shape passes `python3 tools/check_fixtures.py`.
- `hugo server --buildDrafts` renders each at `/essays/<slug>/` without errors.
- example-one's TOC shows level-4 nesting and scrollspy works.
- example-one + example-two series-nav partial shows "Part 1/2 of example-series" and prev/next links.
- example-four's frontmatter shows `has_sidenotes: false` despite shortcode in body.
- `data/url-history.yaml` manifest has 4 new entries.
- Re-running `--publish-deliberate` on each is idempotent (no diff).
- `git status` shows only `content/essays/example-*` changes + manifest update (no rogue garden/research/library mutations — proves deliberate scope).

### 7.4 CI gates (existing)

`tools/ci-local.sh` runs all 50 linter steps + Hugo build + LHCI. Per [[feedback_always_run_ci_locally]], author runs before pushing.

---

## 8 — Open questions + follow-ups

### 8.1 Settled inside the spec

- **Stub source location**: `~/org/essays/` (§3.1).
- **No roam-indexing for essays**; asymmetric cross-ref via notes/ref-notes/ (§3.2).
- **finish-publish gap fix folded into B.4** (§4).
- **4 stubs, kitchen-sink `example-one`** (§6).
- **`has_*` override semantics**: keyword present → wins absolutely; absent → body scan; default false (§3.5/§5.3).
- **Frontmatter render reuses garden's helper** (or local copy); shared extraction deferred to B.5.

### 8.2 Defer to writing-plans

- **Where exactly to read `#+HUGO_HAS_<X>:` overrides** — (a) parse via `note-metadata` pre-export and pass into normalize, or (b) read raw frontmatter ox-hugo emits. Both work. Leaning (a) for consistency with B.3's `#+HUGO_DESCRIPTION:` pattern.
- **Exact regex for `[^N]` footnote scan** — naïve `\[\^[^]]+\]` matches both definitions and references; probably fine.
- **`a3-pub.sh` flag wiring detail** — same intercept pattern as B.3; plan enumerates the `-l` line.

### 8.3 Future follow-ups + tracked risks

| # | Item | Source | Trigger / when picked up |
|---|---|---|---|
| 1 | `a3-unpublish-deliberate <id>` command | known limitation | Author hits a deliberate-removed essay needing manifest cleanup |
| 2 | Essay-to-essay cross-ref via org-roam ID | known limitation | Author requests; plain markdown link covers gap until then |
| 3 | Shared `render-frontmatter` extraction | duplication | B.5 makes it the 4th copy → extract during B.5 |
| 4 | Citations pipeline (`{{< cite >}}` parsing + `data/citations.yaml` emission) | scope boundary | Sub-project F |
| 5 | Real essay content migration from `~/org/blog/` | author decision | Post-B.4; not B.4's responsibility |
| 6 | **R1** — `{{< widget >}}` / `{{< video-sync >}}` ox-hugo pass-through verification | unverified assumption | Kitchen-sink example-one renders both; spot-check task 16 confirms; fix-up commit lands in this slice if wrong |
| 7 | **R2** — Layout regression surface from 8 → 4 stub collapse | coverage trade-off | Author visual-reviews `/essays/` section + each per-essay page on dev server at slice close; any regression lands as a fix-up commit |
| 8 | **R3** — finish-publish `:scope` regression on living mode | scope-fix introduces risk to existing callers | §4.4 test 4 (`living-default-unchanged`) gates against it in CI; no manual step required |

### 8.4 Carry-forwards

- A.2 typed-backlinks data — essays inherit "panel-data plist stubbed at nil" from B inheritance chain.
- Shared `render-frontmatter` extraction (#3 above) — B.5 trigger.
- `a3-unpublish-deliberate` command (#1 above) — own future slice.

---

## Spec self-review checklist

- [x] Placeholder scan — no TBDs; all behaviors specified at a level a plan can consume.
- [x] Internal consistency — task ordering matches dependency graph (§7.2); stub list matches `has_*` test coverage; module structure (§2) matches handler responsibilities (§5).
- [x] Scope check — single writing-plans cycle; parent spec covers shared infra; B.4 stays focused on essays + scope-fix.
- [x] Ambiguity check — override semantics explicit (§3.5); `has_math` patterns enumerated (§5.3); deliberate-scope Step B narrowing explicit (§4.2).
- [x] Hard-constraint check — no AI text required (filler only); no AI visuals (author hand-authors hero.svg); fixture-only authoring preserved through transition (§6.4); accessibility unaffected (B emits content, CSS handles a11y).
