# Phase 3 sub-project F — citation pipeline

**Status:** design (brainstormed 2026-06-01)
**Parent spec:** `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` (sub-project A — access control + link semantics)
**Sequence:** A → B.0 → B.1 → B.1.1 → B.2 → B.3 → B.4 → **F** → C → D → E (per [[phase-3-decomposition]])
**Prior slice memories:** [[b4-complete]] (B.4 essays shipped 2026-05-31), [[next-slice]] (queued pointer), [[citation-export-slice]] (site-side runtime shipped 2026-05-14).

---

## 1 — Goals & non-goals

### Goals

Ship the citation pipeline — the **org-side authoring path** the site-side citation runtime has been waiting on since Phase 3.5 (Citation export slice, 2026-05-14). The site already has the `{{< cite >}}` shortcode + modal + reference-list partial; what it lacks is real data in `data/citations.yaml`. F closes that loop.

Two surfaces ship together:

1. **Per-publish embedded incremental:** every `publish-living` / `publish-deliberate` run extracts `[cite:@key]` occurrences from in-scope org sources, resolves each against `~/org/notes/ref-notes/library.bib`, and merges entries into `data/citations.yaml` without disturbing unrelated keys.
2. **`M-x a3-sync-citations` / `a3-pub.sh --sync-citations`:** standalone command that optionally refreshes `library.bib` from Zotero via Better-BibTeX JSON-RPC, then walks every currently-published org source, re-resolves every cite-key, and overwrites `data/citations.yaml` wholesale (purging unused keys).

### In scope

- New `a3madkour-publish-bib.el` module + `-test.el` sibling — `.bib` parser, citar adapter, BBT JSON-RPC client, resolver dispatch.
- New `a3madkour-publish-citations.el` module + `-test.el` sibling — pre-export buffer rewriter, cite-key accumulator, yaml emitter, `notes_ref` auto-detect, `a3-sync-citations` command.
- Pre-export buffer rewrite of `[cite:@key]` → `@@hugo:{{< cite "key" >}}@@` (sibling of B.1.1's id-link rewriter).
- Citation key linter regex loosened to accept BBT-style camelCase.
- `a3-pub.sh --sync-citations` intercept + new `-l` lines in living / deliberate / sync exec blocks.
- Test fixtures under `tests/fixtures/citations/`: stub `.bib` (8 entries covering all major `@type`s), 2 stub source `.org` files, 1 stub ref-note for `notes_ref` auto-detect.

### Non-goals

- **Style-override / prefix / suffix org-cite syntax** (`[cite/text:@k]`, `[cite:see @k p. 5]`) — V1 fails fast with an educational pointer. Future F follow-up.
- **`#+print_bibliography:` positional rendering** — V1 strips the directive on pre-export; the existing `essay-references` partial auto-appends at end of body. Positional support is a future follow-up.
- **Rich BibTeX field passthrough** (abstract, keywords, file paths) — V1 maps the existing `data/citations.yaml` schema only; site runtime already covers BibTeX/APA/Chicago/MLA/RIS exports.
- **Always-on BBT JSON-RPC** — only `a3-sync-citations` probes Zotero; publish stays portable.
- **Math validators** — sub-project C.
- **Unified def/thm/figure markup, multi-target export** — sub-project D.
- **Explorables / per-page widgets** — sub-project E.
- **Library-item cite-export** — already shipped in [[library-redesign-slice]]; F doesn't touch it.

---

## 2 — Module structure

```
~/dotfiles/emacs-configs/custom/lisp/
├── a3madkour-publish-bib.el            [NEW]   bib resolver (~250 LoC)
├── a3madkour-publish-bib-test.el       [NEW]   ert sibling
├── a3madkour-publish-citations.el      [NEW]   rewriter+emitter+sync (~200 LoC)
├── a3madkour-publish-citations-test.el [NEW]   ert sibling
├── a3madkour-publish-export.el         [MOD]   call rewrite-cite-keys-in-buffer
├── a3madkour-publish-living.el         [MOD]   tail-call cite-emit-yaml in finish
├── a3madkour-publish-deliberate.el     [MOD]   tail-call cite-emit-yaml in finish
└── (a3-pub.sh)                          [MOD]  --sync-citations flag + -l intercepts

~/Sync/Workspace/a3madkour.github.io/
├── tools/check_citations.py            [MOD]   loosen KEY_RE to [A-Za-z0-9-]
├── tools/test_check_citations.py       [MOD]   +2-3 regex tests
├── tests/fixtures/citations/library.bib    [NEW] 8-entry BBT-keyed fixture
├── tests/fixtures/citations/example-cite-one.org   [NEW]
├── tests/fixtures/citations/example-cite-two.org   [NEW]
├── tests/fixtures/citations/ref-notes/dummyKey2024.org [NEW]
├── tools/test_publish_integration.py   [MOD]   +3 tests (roundtrip, sync-purges, hugo-render)
└── docs/superpowers/specs/2026-06-01-phase-3-f-citation-pipeline-design.md [NEW]
```

**Two-module split rationale:** the `.bib` parser is a self-contained grammar problem with its own deep edge-case surface; bundling it with the rewriter/emitter would put a 250-LoC parser next to a 200-LoC orchestrator, breaking the per-concern split A established. Splitting also localizes the resolver-engine drift risk (citar vs parser vs BBT) inside one module behind one interface.

---

## 3 — Source-side contract

### 3.1 Supported `[cite:...]` forms

| Org source | Rewritten to | Notes |
|---|---|---|
| `[cite:@key]` | `@@hugo:{{< cite "key" >}}@@` | The 95% case |
| `[cite:@a;@b;@c]` | `@@hugo:{{< cite "a" >}}{{< cite "b" >}}{{< cite "c" >}}@@` | Adjacent shortcodes — site's existing `essay-references` partial dedupes by key |
| `[cite:@key]` inside `[fn::...]` / footnote / table cell / sidenote | Rewritten as above | No special handling needed — rewrite runs before ox-hugo |

**Unsupported in V1 (fail-fast):**
- `[cite/text:@k]`, `[cite/noauthor:@k]`, `[cite/locators:@k]`, any other `[cite/STYLE:...]` form.
- `[cite:see @k]`, `[cite:@k p. 5]`, any prefix or suffix text inside the brackets.
- `[cite:]` (empty cite).

Error message shape (held to one line of preamble + one of hint):
```
~/org/essays/example-five.org:42: cite/style not supported in V1: [cite/text:@friedmanApproximateKnowledgeCompilation]
  hint: V1 supports [cite:@key] and [cite:@k1;@k2]. Style overrides, prefix, and suffix
        are tracked as F-follow-up work; see this spec §1 non-goals.
```

### 3.2 Buffer-position safety

The rewriter calls `org-element-parse-buffer` and walks the AST for elements of type `'citation`, rather than regex-scanning the buffer. This avoids false positives inside `#+BEGIN_SRC` blocks, `:noexport:` subtrees, and verbatim/code inline spans. Org-cite is the parser; F is the renderer.

### 3.3 `#+print_bibliography:` handling

V1 strips any `#+print_bibliography:` line from the buffer during pre-export rewrite. The site's `essay-references` partial auto-renders at end of body via `Scratch.cite-keys`. Positional rendering (honoring where the directive appears) is a future follow-up.

---

## 4 — Bib resolver architecture

The `bib-resolve` interface returns a single shape regardless of which engine produced it:

```elisp
(bib-resolve "abelaConstructiveApproachGeneration2015")
;; → (:authors ("Abela, Ryan" "Liapis, Antonios" "Yannakakis, Georgios N")
;;    :year 2015
;;    :title "A Constructive Approach for the Generation of Underwater Environments"
;;    :venue "FDG Workshop on Procedural Content Generation in Games"
;;    :type "inproceedings"
;;    :url nil :doi nil :publisher nil :volume nil :issue nil :pages nil :isbn nil)
;; → nil if key unknown
```

### 4.1 Engine dispatch

```elisp
(defun bib-resolve (key)
  (cond
   ((bib--citar-loaded-p)  (bib--read-via-citar key))
   ((bib--parser-cache)    (bib--read-via-parser key))
   (t                      (bib--parser-init) (bib--read-via-parser key))))
```

- **citar path (M-x context):** thin wrapper around `citar-get-entry` + `citar-get-value`. Inherits citar's mtime-aware cache, so the on-disk `.bib` can change underneath without explicit invalidation.
- **Parser path (batch / shell context):** `bib--parse-file` runs once per session into a key→raw-entry-alist hash, then `bib--read-via-parser` dispatches via `gethash` + `bib--normalize-entry`.
- **BBT JSON-RPC path:** never invoked from `bib-resolve`. Only `bib-refresh-from-zotero` (called from `a3-sync-citations`) hits BBT, and only to overwrite the `.bib` on disk — the resolver then proceeds normally.

### 4.2 `.bib` parser

Stdlib-only ELisp BibTeX entry parser. Handles:
- `@type{key, field = {value}, …}` and `@type{key, field = "value", …}` forms.
- Nested braces in field values (`{{Egyptian Streets}}` — strip OUTERMOST pair only).
- BibTeX comments (lines starting with `%` outside entries) — skipped.
- `@string{...}` — recognized, definitions cached, references substituted.
- `@preamble{...}` — recognized, skipped.
- Line continuations and multi-line field values.
- `author = {A and B and C}` — split on ` and ` (BibTeX convention, not commas).
- `date = "2014-12-27"`, `date = "2014"`, `date = "2014-12-27T16:00:18+00:00"`, legacy `year = 2014` — first 4 ASCII digits become `:year` int.

The parser DOES NOT validate against the schema; that's `bib--normalize-entry`'s job. Parser output is raw-field plist; normalizer is the lossy projection.

### 4.3 BBT JSON-RPC (sync command only)

```
POST http://localhost:23119/better-bibtex/json-rpc
Content-Type: application/json
{"jsonrpc": "2.0", "method": "item.export",
 "params": {"library_id": 1, "translator": "Better BibTeX"}}
```

- 2-second connection timeout.
- On 2xx with valid body: atomic write to `~/org/notes/ref-notes/library.bib` (`.tmp` + rename — preserves citar cache invalidation).
- On any failure (ECONNREFUSED / non-2xx / malformed response / timeout): warn to `*Publish Output*`, continue with on-disk `.bib`.
- Configurable via defcustom `a3madkour-publish-bib-bbt-endpoint`; set to `nil` to disable BBT path entirely (sync still works against on-disk `.bib`).

---

## 5 — BibTeX → `data/citations.yaml` field mapping

| `citations.yaml` field | Source priority | Coercion |
|---|---|---|
| `<key>` (entry key) | BibTeX `@type{KEY, …}` | Verbatim — case-preserving |
| `authors: [str, …]` | `author` (split on ` and `) | Each kept as `"Lastname, First"` |
| `year: int` | `date` first 4 digits → legacy `year` field | `"2014-12-27" → 2014` |
| `title: str` | `title` | Strip outermost braces; preserve inner braces verbatim |
| `venue: str` | `journaltitle` → `booktitle` → `publisher` → `eventtitle` → `"?"` | First non-empty wins; warn if `"?"` lands |
| `url: str` (opt) | `url` | Must start `http://` or `https://`; otherwise dropped |
| `doi: str` (opt) | `doi` | Verbatim |
| `publisher: str` (opt) | `publisher` | Kept independently even when also venue fallback |
| `volume: str` (opt) | `volume` | Verbatim |
| `issue: str` (opt) | `issue` then `number` | First non-empty wins |
| `pages: str` (opt) | `pages` | Verbatim |
| `isbn: str` (opt) | `isbn` | Verbatim |
| `type: str` (opt) | `@<type>` (lowercased) | Enum: `article \| book \| inproceedings \| incollection \| online \| misc \| report \| thesis \| unpublished`. Unknown types map to `misc`. |
| `notes_ref: str` (opt) | Auto-detect from `~/org/notes/ref-notes/<KEY>.org` (see §6) | Garden slug |

**Empty-author fallback:** some `@online` / `@misc` entries have no author. F emits `authors: ["Unknown"]` and warns to `*Publish Output*`. Linter accepts; site renders `"Unknown (year). Title."` in the reference list.

**Brace-protection rule:** BibTeX titles often wrap whole strings in extra braces to preserve case (`title = {{{Egyptian Streets}}}`). F strips the OUTERMOST pair around the whole field; inner braces survive as part of the yaml string. The yaml string is rendered verbatim by Hugo templates.

---

## 6 — `notes_ref` auto-detection

For each accumulated cite-key, F probes for an associated ref-note:

1. **Filesystem probe:** `~/org/notes/ref-notes/<KEY>.org` exists?
2. **Keyword read:** `read-org-keyword` for `HUGO_PUBLISH` and `HUGO_SECTION`. Require `HUGO_PUBLISH=t` AND `HUGO_SECTION=garden`.
3. **Slug derive:** apply B.1's slug-derivation logic (`HUGO_SLUG` keyword override → filename-derived default).
4. **Manifest check:** the slug appears in `data/url-history.yaml` (consumed via A.1.d's manifest snapshot defvar) with a `/garden/<slug>/` URL.
5. **Emit `notes_ref: <slug>`** on success; otherwise emit no `notes_ref` field.

**No warnings on miss.** A ref-note that exists but isn't published is a normal state (queued, draft, or removed). Warning on every miss would create per-publish noise for the same keys; author resolves by running the garden publish or marking the ref-note `HUGO_PUBLISH: t`.

**Performance:** ref-note probes are O(cited-keys-this-publish), not O(library.bib). For a 20-citation essay, 20 filesystem probes. Probes happen during `cite-emit-yaml` (once per session per key), not per-buffer.

**Manifest-backed, not filesystem-backed:** the slug→URL lookup uses A.1's manifest snapshot — the same oracle B.1's link rewriter uses. Mid-run unpublishes don't show up until `finish-publish` records them, preserving snapshot-at-publish-start semantics.

---

## 7 — Per-publish data flow (embedded incremental)

```
begin-publish
  bib--snapshot           ; citar warm-load OR .bib parse into in-memory hash, kept for run
  cite--accumulator := ∅  ; clear session defvar

walk-and-emit             ; per handler, per source file
  open buffer
  rewrite-buffer-links    ; B.1.1 — id-links → web URLs
  rewrite-cite-keys-in-buffer  ; F — [cite:@key] → @@hugo:{{< cite "key" >}}@@
    └ for each KEY:
        entry := bib-resolve KEY        ; fail-fast if nil
        cite-accumulate KEY SOURCE-FILE ; grow accumulator
  ox-hugo export → markdown body
  has_citations scan picks up {{< cite }}  ; B.4 already does this
  write content/<section>/<slug>/index.md
  record-publish (A)

finish-publish
  cite-emit-yaml accumulator
    ├ for each KEY in accumulator:
    │   entry := bib-resolve KEY
    │   notes_ref := cite--lookup-notes-ref KEY (manifest-snapshot-backed)
    │   merge into existing data/citations.yaml (preserve keys NOT in accumulator)
    └ atomic write: data/citations.yaml.tmp → rename
  bib--snapshot := nil
```

**Merge semantics:** non-cited-this-run keys stay in `data/citations.yaml` untouched. A partial publish (one essay) does not drop the cite data its sibling essays needed.

---

## 8 — Sync-command data flow

`M-x a3-sync-citations` / `a3-pub.sh --sync-citations`:

```
1. bib-refresh-from-zotero
   ├─ try BBT JSON-RPC (2s timeout)
   ├─ success: atomic-write fresh .bib to ~/org/notes/ref-notes/library.bib
   └─ failure: warn, continue with on-disk .bib

2. Walk all currently-published org sources
   ├─ Read manifest (data/url-history.yaml via snapshot defvar) → list of live source files
   ├─ For each: open, cite--scan-buffer, accumulate keys with (KEY . SOURCE-FILE)

3. Re-resolve EVERY accumulated key against fresh bib
   ├─ For each unique KEY:
   │   entry := bib-resolve KEY
   │   if nil: fail-fast with all SOURCE-FILEs that cited this key
   │   notes_ref := cite--lookup-notes-ref KEY
   └ Build complete entries hash

4. Wholesale overwrite data/citations.yaml
   ├─ Sort entries by key (deterministic diffs)
   └─ Atomic write: .tmp → rename

5. Report
   "Synced N keys (M added, K removed, P refreshed from changed bib entries)."
```

The sync command is the **only** wholesale-write path. Publishes always merge.

---

## 9 — Error handling

| Where | Failure | Behavior |
|---|---|---|
| `begin-publish` | `library.bib` doesn't exist | Fail-fast: `"~/org/notes/ref-notes/library.bib not found; either export from Zotero/BBT or set a3madkour-publish-bib-path"` |
| `begin-publish` | `.bib` parse error (unbalanced braces, malformed `@type{}`) | Fail-fast: report entry key + line being parsed |
| Rewriter | `[cite:@key]` → `bib-resolve` returns nil | Fail-fast: `<source>:<line>: cite key <key> not found in library.bib` |
| Rewriter | Unsupported org-cite form | Fail-fast per §3.1 with educational hint |
| `cite-emit-yaml` | Bib entry missing required yaml field (no title, etc.) | Fail-fast: `<key>: bib entry missing required field <field>` |
| `bib-refresh-from-zotero` | BBT unreachable / non-2xx / malformed | Warn + continue with on-disk `.bib` (sync only) |

**No multi-error batching.** First error stops the run. Rationale: simpler contract; matches B.1.1's rewriter discipline; re-runs are cheap (manifest snapshot + in-memory bib hash; no disk I/O bottleneck).

**Resolver-path drift safeguard.** ert tests hit `bib-resolve` with the same fixture `.bib` through both citar and parser paths, asserting plist equality entry-by-entry. Drift surfaces as a red test, not a silent runtime divergence.

**Atomicity.** `cite-emit-yaml` writes to `data/citations.yaml.tmp` then renames. Mid-write crash (process killed, disk full) leaves prior yaml intact. Matches B's `--write-if-different` discipline.

**No `--continue-on-error` flag.** Fail-fast is the contract; an opt-out invites warn-buffer-blindness. Author workaround for in-flight cite-keys: comment the `[cite:@...]` out, publish, uncomment when ready.

---

## 10 — Linter changes

`tools/check_citations.py`:
- `KEY_RE`: `^[a-z0-9][a-z0-9-]*$` → `^[A-Za-z0-9][A-Za-z0-9-]*$`. BBT camelCase keys accepted; underscores still rejected; leading-hyphen still rejected.
- `ALLOWED_FIELDS` unchanged — the existing schema is exactly what F emits.
- `REQUIRED_FIELDS` unchanged: `{authors, year, title, venue}`.
- `notes_ref` resolution unchanged: must point to a published, non-draft garden slug.
- Year-range check unchanged: `[1500, current_year + 2]`.

`tools/test_check_citations.py`:
- Add 2-3 tests: `abelaConstructiveApproachGeneration2015` accepted; `bad_underscore_key` rejected; `-leading-hyphen` rejected.
- Existing tests stay green (lowercase-kebab keys still pass the loosened regex).

**No new linter pair.** The cite-pipeline contract is "what's in `data/citations.yaml` matches what the bib resolved to" — and that's an elisp-side invariant, validated by ert tests against the fixture bib. The Python linter's job is shape-validation of the yaml on disk, which is unchanged.

---

## 11 — Wrapper-script changes

`a3-pub.sh` gets:

1. `--sync-citations` flag intercept (matching `--check-orphans` / `--publish-living` / `--publish-deliberate` precedent).
2. `-l a3madkour-publish-bib` + `-l a3madkour-publish-citations` added to BOTH:
   - The existing `--publish-living` exec block.
   - The existing `--publish-deliberate` exec block.
   - The new `--sync-citations` exec block.

Per [[plan-wrapper-script-updates]]: new top-level modules need explicit `-l` lines; autoload only saves declared functions. Spot-check during implementation will catch any missed `-l`.

---

## 12 — Testing

### ert (dotfiles) — +~85 tests

`a3madkour-publish-bib-test.el` (~50 tests):
- `.bib` parser: single-entry, multi-author splitting, brace-protected titles, `date` variants, comments, `@string` substitution, `@preamble` skip, line continuations, malformed-brace error, missing-required-field detection (~25)
- `bib-resolve` dispatch: citar-loaded vs parser path return identical plists for same fixture (~5)
- `bib--normalize-entry`: venue chain, year-from-date, type enum mapping (incl. unknown→misc), brace-stripping, empty-author fallback (~10)
- citar adapter: `cl-letf` stubs around `citar-get-entry`; missing-citar fallback to parser (~5)
- BBT JSON-RPC: mocked HTTP via `cl-letf` on `url-retrieve-synchronously` — 200 happy path, ECONNREFUSED, non-2xx, malformed JSON, 2s timeout (~5)

`a3madkour-publish-citations-test.el` (~35 tests):
- Buffer rewriter: bare `[cite:@k]`, multi-cite `[cite:@a;@b;@c]`, inside `[fn::sidenote]`, inside table cell, inside `#+BEGIN_SRC` (must NOT rewrite), inside `:noexport:` subtree (must NOT rewrite), all unsupported-form failure paths, multiple errors → first stops, accumulator population, `cite--scan-buffer` position-correctness (~15)
- `cite--lookup-notes-ref`: ref-note absent → no `notes_ref`; ref-note present but draft → no `notes_ref` (silent); ref-note present + published + in manifest → emit; `HUGO_SLUG` override path; O(1) probe behavior (~5)
- Yaml emitter: merge preserves untouched keys, sorted output, missing-required-field fails, atomic `.tmp + rename`, idempotent re-run zero-diff (~10)
- `a3-sync-citations`: BBT-down warn path, full purge of unused keys, sort-deterministic output (~3)
- Stripping `#+print_bibliography:` from buffer (~2)

### Python (site) — +2-3 tests in existing `test_check_citations.py`

Loosened-regex tests: camelCase accept, underscore reject, leading-hyphen reject.

### Integration (`tools/test_publish_integration.py`) — +3 tests

- **`TestCitationRoundtrip`:** stub `.bib` with 8 BBT-keyed entries + 2 stub essays citing 4 keys → run publish → `data/citations.yaml` has exactly those 4 keys with shape matching the §5 mapping (no abstract, no keywords; venue chain resolved correctly per entry type).
- **`TestSyncPurges`:** pre-seed `data/citations.yaml` with 10 keys → corpus cites 3 → `a3-sync-citations` → assert yaml has exactly those 3.
- **`TestHugoRendersCitedEssay`:** extend the existing essays Hugo-build integration test to assert `<cite>` anchors point at `#ref-<key>` AND `essay-references` section renders each entry with correct title/authors/year.

### Fixtures

- `tests/fixtures/citations/library.bib`: 8 hand-written BBT-keyed entries covering `@article`, `@book`, `@inproceedings`, `@incollection`, `@online`, `@misc`, `@report`, `@thesis`. ~80 lines. Exercises brace-protected titles, multi-author splits, missing-author fallback, all venue-chain branches.
- `tests/fixtures/citations/example-cite-one.org`: kitchen-sink — bare cite, multi-cite, cite-in-sidenote, cite-in-footnote, `notes_ref`-auto-detect path.
- `tests/fixtures/citations/example-cite-two.org`: narrow — single cite resolving to existing fixture ref-note.
- `tests/fixtures/citations/ref-notes/dummyKey2024.org`: stub ref-note exercising auto-detect.

### Out-of-scope tests

- Real Zotero against the developer's machine — BBT JSON-RPC is mocked everywhere; manual smoke is up to the author.
- The full 15.6k-entry `~/org/notes/ref-notes/library.bib` — performance regression-prone there; flag as F-follow-up if it surfaces.

**Slice estimate:** +~85 ert (398 → ~483), +~3 sibling Python, +~3 integration (33 → 36), 4 new elisp files + 1 fixture `.bib` + 3 fixture `.org` files, 1 Python linter regex loosen, `a3-pub.sh` flag + 2 `-l` intercepts per exec block.

---

## 13 — Implementation order (sketch — full plan in writing-plans phase)

1. Stub fixtures + linter regex loosen (foundation; everything else depends on it).
2. `a3madkour-publish-bib.el` parser path + tests (no resolver dispatch yet — parser-only).
3. `bib--normalize-entry` + tests (the lossy mapping).
4. `bib-resolve` dispatch + citar adapter + tests (parity assertions).
5. `a3madkour-publish-citations.el` rewriter + accumulator + tests.
6. `cite--lookup-notes-ref` + tests (manifest snapshot dependency lands here).
7. `cite-emit-yaml` merge semantics + tests.
8. Wire rewriter into `a3madkour-publish-export.el` + integration test (TestCitationRoundtrip).
9. Wire `cite-emit-yaml` tail call into `living` + `deliberate` + integration test.
10. BBT JSON-RPC client + mocked tests.
11. `a3-sync-citations` command + integration test (TestSyncPurges).
12. `a3-pub.sh --sync-citations` flag + `-l` intercepts + smoke test.
13. Hugo integration test (TestHugoRendersCitedEssay).
14. Real-bib spot-check (author runs `M-x a3-sync-citations` against the full 15.6k-entry `~/org/notes/ref-notes/library.bib`, validates performance + correctness — flagged as Task 14 in the eventual plan).

---

## 14 — Known follow-ups (post-slice)

- **Style-override / prefix / suffix org-cite syntax** — `[cite/text:@k]`, `[cite:see @k p. 5]`. Requires cite-shortcode signature change (accept prefix + suffix args) and partial work. Discrete future F.2 slice.
- **`#+print_bibliography:` positional rendering** — discrete F.3 slice.
- **Rich BibTeX field passthrough** — opens up abstract-in-pagefind and arxiv-link affordances; discrete future slice gated on feature appetite.
- **Performance regression test against the full 15.6k-entry `library.bib`** — flag as B.4-style follow-up if author notices publish slowdown.
- **`a3-unpublish-citations`** — purge cite entries for an unpublished essay without a full sync. Open question whether this matters in practice (the sync command handles it; just runs a touch slower).
- **Bib refresh on save-hook** — Better-BibTeX has a watch-mode that auto-exports on Zotero change; F could leverage instead of explicit `--sync-citations`. Discrete future slice.

---

## 15 — Spec self-review

- [x] **Placeholder scan**: no TBD / TODO; all decisions concrete. Module LoC estimates are projections.
- [x] **Internal consistency**: §4 dispatch matches §7 + §8 flow; §9 error table matches §3.1 fail-fast cases; §10 linter changes align with §5 mapping (existing schema preserved); §11 wrapper-script changes match §2 module structure.
- [x] **Scope check**: single implementation plan-sized. ~85 ert + ~14 tasks lands in the same range as B.1, B.2, B.3, B.4.
- [x] **Ambiguity check**: BBT JSON-RPC scope explicit (sync-only); error-handling specifies behavior per failure mode; `notes_ref` auto-detect rule explicit; multi-cite rendering form explicit; unsupported org-cite forms enumerated with educational error message.
