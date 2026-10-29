# Library from Notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One org note per library item is the only record. The reading queue and the Boox flow write
status onto it. One share command publishes it as a garden media page plus a library row that link to
each other.

**Architecture:**
- **Site:** the section registry (`data/sections.json`) learns per-shelf garden media cases and a
  `drawer` source.
- **Dotfiles, publisher:** a new module `a3madkour-library-items.el` reads `LIBRARY_*` file-level
  properties and the `:site:` subtree. The garden handler publishes only that subtree. A new collector
  rebuilds `data/<medium>.yaml` from every shared item note at the end of `a3-publish-living`.
- **Dotfiles, config.org:** thin glue calls the module from the citar/queue/Boox code.

**Tech Stack:** Emacs Lisp (org, org-roam, ox-hugo, citar), ERT; Python 3 stdlib linters; Hugo templates
+ CSS.

**Spec:** `docs/superpowers/specs/2026-10-28-library-from-notes-design.md`. Read it first; section
numbers below refer to it.

## Global Constraints

- Dogfood rule: a defect is fixed in the function that produced the output. Never hand-edit
  `data/<medium>.yaml` or `content/garden/<slug>/index.md`.
- Mutation-test every guard: break it, watch its test fail, restore it.
- Private by default: nothing outside the `:site:` subtree (or the `LIBRARY_*` metadata) of a shared note
  reaches the site. That includes images and link targets.
- Papers are untouched. A queue entry whose bib type is not a book gets no `LIBRARY_*` writes.
- Property naming: contract field `f` ↔ file-level property `LIBRARY_` + `(upcase f)`. Extras use
  `LIBRARY_` + the existing key in `a3madkour-pub-library--extras-by-media` (e.g. `LIBRARY_COVER_FILE`).
- Shelf map: book → `library/reading`; album, track → `library/listening`; game → `library/playing`;
  film, series → `library/watching`.
- Status words per shelf (from `data/sections.json`, unchanged):
  - reading `abandoned finished queued reading`
  - listening `dropped finished listening queued`
  - playing `100pct dropped finished playing queued`
  - watching `dropped finished queued watching`
- Site tags on item notes: drop the editorial tags plus `a3madkour-library/structural-tags` (default
  `("Ref" "Book")`), then kebab-case (`ProgrammingLanguages` → `programming-languages`).
- The user's real org files (`~/org/**`) are never written by a test or build step. Tests use temp dirs
  (`a3madkour-test/with-org-env` in `tests/`, `make-temp-file` in `lisp/*-test.el`).
- Dotfiles ERT: `~/emacs-configs/custom/lisp/run-tests.sh` runs the whole suite (selector args are
  ignored), so grep its log. Config tests: `~/emacs-configs/custom/tests/run.sh [PATTERN]`.
- A stale `.elc` shadows edited elisp: delete `lisp/<module>.elc` before running tests.
- Any new elisp module gets an explicit `-l` line in `lisp/a3-pub.sh`.
- Site: never run `hugo --minify` while a dev server is alive.
- Neither repo is pushed; both are pushed together at the end of S1 (not part of this plan).
- No AI-authored prose in any site content; test fixtures use "Example N" / lorem ipsum.

## Review Focus

1. **An image linked under a private heading of a shared note** is not copied into the bundle. Pinned in
   Task 5 (`garden-item/private-image-not-copied`).
2. **A note shared with an empty `:site:` heading** (heading only, whitespace body) is refused, both by
   share and by living publish. Pinned in Tasks 5 and 7.
3. **Unsharing the only item on a shelf** leaves `items: []` rather than the old row, and the site still
   builds. Pinned in Task 6 (`collector/last-item-unshared-empties-shelf`) and Task 9.
4. **A queue entry marked DONE twice, or retired after a manual DONE,** does not overwrite the first
   `LIBRARY_FINISHED` date. Pinned in Task 8 (`queue-done-twice-keeps-first-date`).
5. **A shared item note whose garden publish failed** (e.g. contract error) produces no library row,
   so no `note_slug` dangles. Pinned in Task 6 (`collector/skips-note-without-bundle`).

---

## File map

**Site** (`~/Sync/Workspace/a3madkour.github.io`)
- `data/sections.json`: split the garden `media` case and add the `drawer` source (Task 1).
- `tools/sections.py`, `tools/test_sections.py`: `SOURCES` gains `drawer` (Task 1).
- `tools/check_garden_fixtures.py`, `tools/test_check_garden_fixtures.py`: map `media-*` case names
  to `media` (Task 1).
- `content/garden/severance-s2/index.md`: `status: dropped` (Task 1).
- `layouts/partials/garden/note-header.html`, `assets/css/main.css` (~L1288): status glyphs (Task 2).
- `data/library-shelves.yaml`: drop example slugs and the hero (Task 9).

**Dotfiles** (`~/emacs-configs/custom`)
- `lisp/a3madkour-sections-fixture.json` (+ `.el` if it embeds values): mirror Task 1 (Task 3).
- `lisp/a3madkour-sections.el`: accept `drawer` (Task 3).
- `lisp/a3madkour-publish-author.el`: drawer source in mark (Task 3); remove `a3-library-insert-item`
  (Task 9).
- Create `lisp/a3madkour-library-items.el` + `-test.el`: item-note reading, status, tags, site body,
  commands (Tasks 4, 7).
- `lisp/a3madkour-publish-garden.el`, `lisp/a3madkour-publish-frontmatter.el`: item-note narrowing +
  media frontmatter (Task 5).
- Create `lisp/a3madkour-publish-library-notes.el` + `-test.el`: the collector (Task 6).
- `lisp/a3madkour-publish-living.el`: run the collector, extend the gate (Tasks 5, 6).
- `lisp/a3madkour-publish-registry.el`, `lisp/a3madkour-publish-library.el`: per-file handler →
  refuser (Task 6).
- `lisp/a3-pub.sh`: `-l` both new modules (Tasks 4, 6).
- `config.org` (citar ~L1958, Boox ~L2078–3375, WIP ~L3493–3553) + `tests/test-library-queue.el`
  (registered in `tests/run.sh`): reading-flow glue (Task 8).

---

### Task 1: Registry — per-shelf garden media cases and the `drawer` source (site)

**Files:**
- Modify: `data/sections.json` (garden `variants.cases.media`)
- Modify: `tools/sections.py:40` (`SOURCES`)
- Modify: `tools/check_garden_fixtures.py:29-31`
- Modify: `content/garden/severance-s2/index.md`
- Test: `tools/test_sections.py`, `tools/test_check_garden_fixtures.py`

**Interfaces:**
- Produces:
  - garden cases `media-book` (values `["book"]`), `media-listening` (`["album","track"]`),
    `media-playing` (`["game"]`) and `media-watching` (`["film","series"]`). They replace `media`.
  - Each case has the fields of today's `media` case, with `status.values` set to its shelf's list
    (Global Constraints).
  - `media_type`, `status`, `creator`, `started` and `finished` in those cases carry
    `"from": "pipeline", "source": "drawer"`. `required` is unchanged.
  - The top-level garden `year` stays as is (it is optional).
  - `sections.SOURCES == frozenset({"title", "filetags", "drawer"})`.
  - `derive_flavor` returns `"media"` for any `media-*` case.

- [ ] **Step 1: Write failing tests**
  - `test_sections.py::test_drawer_is_a_valid_source`: a registry field with
    `{"from":"pipeline","source":"drawer"}` loads.
  - `test_sections.py::test_garden_media_status_follows_shelf`: `check_fields` on
    `{"media_type":"game","status":"100pct", …required…}` gives no status error.
    `{"media_type":"game","status":"reading"}` gives `status='reading' not in [...]`.
  - `test_sections.py::test_series_abandoned_rejected`: an error is reported.
  - `test_check_garden_fixtures.py::test_media_cases_derive_media_flavor`: `derive_flavor` returns
    `"media"` for book, album, game and film; `"reference"` for paper; `"concept"` with no `media_type`.
- [ ] **Step 2: Run** `python3 -m unittest tools.test_sections tools.test_check_garden_fixtures -v`. Expected: the four new tests FAIL.
- [ ] **Step 3: Implement.**
  - Edit `sections.json` as above.
  - Add `"drawer"` to `SOURCES`.
  - In `derive_flavor`, return `"media"` when the case starts with `"media-"`; otherwise the case name,
    or `"unknown"`.
  - Set `severance-s2` to `status: dropped`.
- [ ] **Step 4: Run** `python3 tools/sections.py && python3 tools/check_garden_fixtures.py && python3 -m unittest tools.test_sections tools.test_check_garden_fixtures`, then the other registry consumers: `for t in tools/test_check_*fixtures*.py tools/test_check_pagefind_meta.py; do python3 -m unittest "tools.$(basename $t .py)"; done`. Expected: all pass except the pre-existing `test_check_pagefind_meta` failure (note its output before and after; it must be unchanged).
- [ ] **Step 5: Mutation-test.** Remove `"drawer"` from `SOURCES` and watch `test_drawer_is_a_valid_source` fail. Make `derive_flavor` return the raw case name and watch the flavor test fail. Restore both.
- [ ] **Step 6: Commit** (site): `feat(sections): per-shelf garden media cases; drawer source`.

### Task 2: Garden status pill for the new status words (site)

**Files:**
- Modify: `layouts/partials/garden/note-header.html:33-47`
- Modify: `assets/css/main.css` (status-pill block, ~L1288)
- Test: a Hugo build, then grep (no template unit layer exists).

**Interfaces:**
- Produces:
  - glyph mapping: `listening`/`playing`/`watching` → the `reading` circle; `dropped` → the `abandoned`
    cross; `100pct` → the `finished` check;
  - visible label: `100pct` shows "100%"; every other word uses `title`;
  - the CSS color classes reuse the same four tokens, grouped (e.g.
    `.status-pill.status-reading, .status-pill.status-listening, … { color: var(--color-steel); }`).
    No new token, so `check-contrast.py` is unaffected.

- [ ] **Step 1: Baseline.** With no dev server alive: `hugo --minify --quiet && grep -o 'status-pill status-dropped[^<]*<svg' public/garden/severance-s2/index.html`. Expected: no match, because Task 1 made the status `dropped` and the template has no branch for it.
- [ ] **Step 2: Implement** the mapping in the template, using an `in (slice …)` test per glyph group, and the grouped CSS selectors.
- [ ] **Step 3: Verify.** Rebuild. `public/garden/severance-s2/index.html` has `status-pill status-dropped` followed by the cross `<svg` and the label `Dropped`. Then run `python3 tools/check_css_refs.py && python3 tools/check-contrast.py && python3 tools/check_dark_tokens.py`. Expected: all pass.
- [ ] **Step 4: Commit** (site): `feat(garden): status pill covers every shelf's status words`.

### Task 3: Mark reads and writes `drawer`-sourced fields (dotfiles)

**Files:**
- Modify: `lisp/a3madkour-sections-fixture.json` (mirror Task 1's garden cases; the test
  `a3madkour-sections--real-contract-sections-match-fixture` pins the two in lockstep)
- Modify: `lisp/a3madkour-sections.el` (`--validate`: accept source `drawer`)
- Modify: `lisp/a3madkour-publish-author.el`: `--source-satisfied-p` (~L703), `--write-field` (L263),
  `--selector-value` (L690)
- Test: `lisp/a3madkour-publish-author-test.el`, `lisp/a3madkour-sections-test.el`

**Interfaces:**
- Consumes: Task 1's `sections.json`.
- Produces:
  - `(a3madkour-pub-author--drawer-property NAME) -> string`, e.g. `"media_type"` → `"LIBRARY_MEDIA_TYPE"`.
  - `(a3madkour-pub-author--drawer-get NAME) -> string|nil`: file-level property value in the current
    buffer. Blank counts as nil.
  - Source `"drawer"` is satisfied iff `--drawer-get` is non-nil. `--write-field` with source `"drawer"`
    writes the file-level property, creating the drawer as the buffer's first element when absent.
  - `--selector-value` returns `--drawer-get` of ON when non-nil, else the current cfm lookup.

- [ ] **Step 1: Write failing tests** (author-test, temp org buffers):
  - `author-test/drawer-source-satisfied-by-file-property`: a buffer with `:LIBRARY_STATUS: reading` in
    the file drawer. `fields-to-fill "garden"` (book case) does not list `status`.
  - `author-test/drawer-selector-picks-media-case`: `:LIBRARY_MEDIA_TYPE: game` → `missing-required`
    lists `status` and `creator` when they are absent, and the status enum offered is the playing list.
  - `author-test/drawer-field-written-to-file-drawer`: mark `garden` with `completing-read` stubbed to
    `"reading"` and `read-string` to `"Ann Author"`. Afterwards `(org-entry-get (point-min)
    "LIBRARY_STATUS")` is `"reading"`, and no `HUGO_CUSTOM_FRONT_MATTER` line contains `status`.
  - `author-test/drawer-written-into-existing-ref-drawer`: a buffer starting with an `:ID:`/`:ROAM_REFS:`
    drawer keeps those keys after the write. The new key lands in the same drawer.
  - `sections-test/drawer-source-accepted`.
- [ ] **Step 2: Run** `rm -f lisp/*.elc; lisp/run-tests.sh > $SCRATCH/ert.log 2>&1; grep -E "FAILED|unexpected" $SCRATCH/ert.log`. Expected: the 5 new tests fail.
- [ ] **Step 3: Implement** the three functions and the validator change. Use `org-entry-get`/`org-entry-put` at `(point-min)`, guarded by a check that the first element is a property drawer. If the file starts with keywords instead (see memory: org-element file-level drawer must be first), insert a fresh drawer at `point-min`.
- [ ] **Step 4: Run** the suite. Expected: 0 unexpected, apart from the known skip.
- [ ] **Step 5: Mutation-test.** Make `--selector-value` skip the drawer and watch `drawer-selector-picks-media-case` fail. Restore.
- [ ] **Step 6: Commit** (dotfiles): `feat(publish-mark): drawer-sourced contract fields (LIBRARY_*)`.

### Task 4: Item-note module — properties, status, tags, site body (dotfiles)

**Files:**
- Create: `lisp/a3madkour-library-items.el`
- Create: `lisp/a3madkour-library-items-test.el`
- Modify: `lisp/a3-pub.sh` (add `-l a3madkour-library-items`)

**Interfaces:**
- Consumes: `a3madkour-sections/enum`, `a3madkour-pub-frontmatter/filter-editorial-tags`,
  `a3madkour-pub-library/extras-for`, Task 3's `--drawer-property`.
- Produces (all public, `a3madkour-library/` prefix):
  - `(item-p FILE) -> bool`: the file drawer has a non-blank `LIBRARY_MEDIA_TYPE`.
  - `(properties FILE) -> alist`: `(("media_type" . "book") ("status" . …) …)` for every non-blank
    `LIBRARY_*` core field, plus `(extras . PLIST)` built via `extras-for` with the `LIBRARY_` prefix
    (int coercion as in `--collect-extras`).
  - `(shelf-for MEDIA-TYPE) -> "library/reading"|…|nil`.
  - `(statuses MEDIA-TYPE) -> list`: `(a3madkour-sections/enum (shelf-for mt) "status")`.
  - `(in-progress-status MEDIA-TYPE) -> string`: reading/listening/playing/watching.
  - `(set-status STATUS &optional TODAY)`: acts on the current buffer.
    - It errors (`user-error`) unless STATUS is in `statuses`.
    - It writes `LIBRARY_STATUS`.
    - On the in-progress word it stamps `LIBRARY_STARTED` if blank.
    - On `finished`/`100pct` it stamps `LIBRARY_FINISHED` if blank.
    - TODAY defaults to `(format-time-string "%Y-%m-%d")`. Returns STATUS.
  - `(clean-tags TAGS) -> list`: the editorial filter, then remove `structural-tags`, then kebab-case,
    then `delete-dups`.
  - `defcustom a3madkour-library/structural-tags '("Ref" "Book")`.
  - `(site-heading-region) -> (BEG . END)|nil`: the body region (after the heading line and any planning
    or drawer lines) of the first level-1 heading tagged `site` in the current buffer.
  - `(site-body FILE) -> string|nil`: that region's text, or nil when absent or whitespace-only.
  - `(preview FILE) -> string|nil`: `LIBRARY_PREVIEW`, else the first sentence of `site-body`. A
    sentence ends at the first `.`, `!` or `?` followed by whitespace or the end, with org markup
    stripped via `org-export-string-as … 'ascii t` or a regex. Builder's choice; the test pins the
    output.

- [ ] **Step 1: Write failing tests** (temp files):
  - `items/item-p-needs-media-type`.
  - `items/properties-reads-prefixed-drawer-only`: a hand `:PROGRESS: highlighting` is ignored, and
    `LIBRARY_PROGRESS_PCT: 42` becomes extras `:progress_pct 42`.
  - `items/shelf-for-every-media-type` covers all 6, and `"paper"` → nil.
  - `items/set-status-stamps-started-once`: reading on day 1, then reading again on day 2 keeps day 1.
  - `items/set-status-finished-stamps-finished`, and `items/set-status-100pct-stamps-finished` (game).
  - `items/set-status-rejects-wrong-shelf-word` (`"listening"` on a book).
  - `items/clean-tags`: `'("Ref" "Book" "ProgrammingLanguages" "TODO" "fiction")` →
    `'("programming-languages" "fiction")`.
  - `items/site-body-only-site-subtree`: a file with `* Types… ` (private text "SECRET") and
    `* Notes :site:` (text "Public."). `site-body` contains "Public." and not "SECRET".
  - `items/site-body-blank-is-nil`.
  - `items/preview-falls-back-to-first-sentence`: `"First one. Second."` → `"First one."`.
- [ ] **Step 2: Run** the suite. Expected: the new tests fail (module missing).
- [ ] **Step 3: Implement** the module with `(provide 'a3madkour-library-items)`, and add it to `a3-pub.sh`.
- [ ] **Step 4: Run** the suite. Expected: green.
- [ ] **Step 5: Mutation-test** the `site-body` boundary: let it take the whole file and watch `site-body-only-site-subtree` fail. Do the same for the "stamp only if blank" guard. Restore both.
- [ ] **Step 6: Commit** (dotfiles): `feat(library-items): item-note properties, status, tags, site body`.

### Task 5: Garden publish of an item note — site subtree only, media frontmatter, gate (dotfiles)

**Files:**
- Modify: `lisp/a3madkour-library-items.el` (add `site-only-copy`)
- Modify: `lisp/a3madkour-publish-garden.el:48-103`
- Modify: `lisp/a3madkour-publish-frontmatter.el` (`--normalize-garden`)
- Modify: `lisp/a3madkour-publish-living.el` (`--contract-gap`)
- Test: `lisp/a3madkour-publish-garden-test.el`, `-frontmatter-test.el`, `-living-test.el`

**Interfaces:**
- Consumes: Task 4.
- Produces:
  - `(a3madkour-library/site-only-copy FILE) -> TMP-PATH`.
    - It writes a temp `.org` containing FILE's file-level drawer, its `#+` keywords, and the
      `site-body` text.
    - Relative `file:`/bare link paths in the body are expanded against FILE's directory, so asset
      resolution matches the source.
    - The caller deletes the file.
    - It errors if `site-body` is nil.
  - `publish-garden-file`, when `(item-p file)`, uses that copy as the input to *both*
    `rewrite-to-tmp-file` and `asset-validate-and-copy`. The note id still comes from FILE.
  - `--normalize-garden`, when `(item-p source-file)`:
    - sets `media_type`, `status`, `creator`, `year` (int), `started` and `finished` from `properties`,
      omitting blank values;
    - replaces `tags` with `(clean-tags <filetags>)`.
  - The living `--contract-gap` also returns
    `"<file>: library item has no :site: section; write one, then publish"` for an item note whose
    `site-body` is nil, before the registry check.

- [ ] **Step 1: Write failing tests:**
  - `garden-item/body-is-site-subtree-only`: the published `index.md` contains the site text and not the
    private text.
  - `garden-item/private-image-not-copied`: the fixture dir has `a.png` linked under the private heading
    and `b.png` under `:site:`. The bundle contains `b.png` only.
  - `garden-item/media-frontmatter-from-drawer`: `media_type: book`, `status: reading`, `creator`,
    `started`. No `flavor`, and no `Ref` tag.
  - `garden-concept/unchanged`: an existing concept-note test still passes unmodified. Assert the full
    output equals what it produced before the change; record a golden first.
  - `living-test/item-without-site-section-is-not-published`, modeled on
    `note-missing-required-field-is-not-published`.
  - `living-test/item-with-whitespace-site-section-is-not-published`.
- [ ] **Step 2: Run** the suite. Expected: the new tests fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** the suite. Expected: green.
- [ ] **Step 5: Mutation-test.** Pass FILE instead of the site-only copy to `asset-validate-and-copy` and watch `private-image-not-copied` fail. Drop the gate clause and watch both living tests fail. Restore.
- [ ] **Step 6: Commit** (dotfiles): `feat(publish-garden): item notes publish only their :site: section`.

### Task 6: Library collector — shelves from shared item notes (dotfiles)

**Files:**
- Create: `lisp/a3madkour-publish-library-notes.el` + `-test.el`
- Modify: `lisp/a3madkour-publish-living.el` (`a3-publish-living`'s on-all-done, before `finish-publish`)
- Modify: `lisp/a3madkour-publish-registry.el` (library sections' `:handler`)
- Modify: `lisp/a3madkour-publish-library.el` (add the refuser; keep `--render-row` and the extras table)
- Modify: `lisp/a3-pub.sh`

**Interfaces:**
- Consumes: Task 4 `properties`, `clean-tags`, `preview`, `shelf-for`;
  `a3madkour-pub/note-slug`, `a3madkour-pub/note-metadata`;
  `a3madkour-pub-history/recorded-last-modified`;
  `a3madkour-pub-library--render-row`, `a3madkour-pub-yaml/write-if-different`.
- Produces:
  - `(a3madkour-pub-library-notes/row FILE) -> plist|nil`. Keys, in the existing
    `--yaml-key-order`:
    - `:slug` and `:note_slug`: the garden slug;
    - `:title`, `:creator`, `:year`, `:media_type`, `:status`, `:started`, `:finished`;
    - `:last_modified`: the history's recorded value for the garden URL, else the frontmatter cascade;
    - `:preview`;
    - `:tags`: `clean-tags` of the filetags;
    - `:cite_key`: only when the `ROAM_REFS` `@key` is in `data/citations.yaml`;
    - `:extras`.
    It returns nil (with an `a3madkour-pub/warn`) when `content/garden/<slug>/index.md` does not exist.
  - `(a3madkour-pub-library-notes/build-shelves FILES) -> list of written paths`.
    - FILES is every file with section `garden`, `:state 'live`, and `item-p`.
    - It writes all four `data/<medium>.yaml` every run; a shelf with no rows renders `items: []`.
    - Rows are ordered by slug.
    - The header comment names the collector, not a source file.
  - `a3-publish-living` calls `build-shelves` exactly once per run, after the barrier and before
    `finish-publish`, with FILES taken from the run's triples. It is skipped on dry runs, if any exist.
  - `(a3madkour-pub-library/refuse-shelf-file FILE RUN &key on-done)`: the handler for every
    `library/*` section. It logs `"<file>: library shelves are built from item notes; remove
    #+HUGO_SECTION: library/… (see a3-library-add)"` and reports `'err`.

- [ ] **Step 1: Write failing tests:**
  - `collector/row-shape`: the plist equals the expected value for a fixture note with a bundle present.
  - `collector/skips-note-without-bundle`.
  - `collector/rows-span-many-notes`: two book notes → one `reading.yaml` with both rows.
  - `collector/last-item-unshared-empties-shelf`: run with one note, then with zero. `reading.yaml` ends
    with `items: []`.
  - `collector/idempotent`: a second run leaves each yaml's mtime unchanged.
  - `collector/cite-key-only-when-known`.
  - `living-test/shelf-file-is-refused`: an old-style `library/reading` file reports `err` and its yaml
    is not written by it.
  - Site linter check, as a dotfiles integration test, or as a manual step in Task 9 if the integration
    harness can't reach the site: the empty yaml passes `check_library_fixtures.py`.
- [ ] **Step 2: Run** the suite. Expected: the new tests fail.
- [ ] **Step 3: Implement**, and add the `-l` in `a3-pub.sh`.
- [ ] **Step 4: Run** the suite. Expected: green. Old library-handler tests that exercised `publish-library-file` are deleted in Task 9, not here. Here they are marked `:expected-result :failed` only if the refuser breaks them; prefer leaving them pointed at the still-existing function.
- [ ] **Step 5: Mutation-test.** Remove the bundle-exists check and watch `skips-note-without-bundle` fail. Skip writing empty shelves and watch `last-item-unshared-empties-shelf` fail. Restore.
- [ ] **Step 6: Commit** (dotfiles): `feat(publish-library): shelves are collected from shared item notes`.

### Task 7: Commands — add, status, share, unshare (dotfiles)

**Files:**
- Modify: `lisp/a3madkour-library-items.el`, `-test.el`

**Interfaces:**
- Consumes: Tasks 3–4; `a3-publish-mark`, `a3-publish-unmark`; `org-roam-capture-` or a plain file write.
- Produces (interactive):
  - `a3-library-add`. It prompts for media type (6 values), title, creator, year, and status (from
    `statuses`; default `finished` for film, else the in-progress word).
    - It creates `<org-roam-directory>/<slug>.org` with a new `:ID:`, the `LIBRARY_*` drawer,
      `#+title:`, and an empty `* Notes :site:` heading, then visits it.
    - It stamps dates via `set-status`.
    - It refuses if the file exists.
    - Hook: `defvar a3madkour-library/notes-dir` (default `org-roam-directory`), so tests can redirect it.
  - `a3-library-status`: in an item note, `completing-read` over `statuses`, then `set-status`, then runs
    `a3madkour-library/status-changed-functions` with `(file status)`. Task 8 hooks the queue sync there.
  - `a3-library-share`:
    - in a non-item buffer: `user-error`;
    - with `site-body` nil: offers (`y-or-n-p`) to insert `* Notes :site:` at the end, then
      `user-error "write the :site: section, then share again"`;
    - otherwise `(a3-publish-mark "garden")`.
  - `a3-library-unshare`: in an item note, `(a3-publish-unmark)`.

- [ ] **Step 1: Write failing tests:**
  - `commands/add-film-defaults-finished-and-stamps`.
  - `commands/add-refuses-existing`.
  - `commands/share-refuses-without-site-section`: the buffer gains the heading only when `y-or-n-p`
    says yes; `HUGO_PUBLISH` stays absent either way.
  - `commands/share-marks-garden`: with stubs, the buffer gets `#+HUGO_PUBLISH: t` and
    `#+HUGO_SECTION: garden`, and `status` is not prompted again.
  - `commands/status-runs-hook`.
  - `commands/unshare-flips-publish`.
- [ ] **Step 2–4:** Run (the new tests fail), implement, run (green).
- [ ] **Step 5: Mutation-test** the share guard.
- [ ] **Step 6: Commit** (dotfiles): `feat(library-items): add / status / share / unshare commands`.

### Task 8: Reading-flow glue in config.org (dotfiles)

**Files:**
- Modify: `config.org`:
  - `a3madkour/citar-add-to-reading-queue` (L1958);
  - new `a3-reading-queue-add-book` next to it;
  - `a3madkour/toggle-active` (L3521);
  - a new `a3madkour/library-sync-on-todo-change` added to `org-after-todo-state-change-hook` next to
    `deactivate-on-done` (L4035);
  - `a3madkour/library-close-queue-entry` on `status-changed-functions`.
- Create: `tests/test-library-queue.el`. Register it in `tests/run.sh`'s file list, and load
  `lisp/a3madkour-library-items.el` in it.
- Re-tangle: `emacsclient -e '(org-babel-tangle-file "~/emacs-configs/custom/config.org")'`, or in batch.

**Interfaces:**
- Consumes: Task 4 `set-status`, Task 7 `status-changed-functions`; `boox--book-key`,
  `boox--ensure-book-note`, `boox--note-for-key`, `boox--close-queue-entry`; `citar-get-entry`.
- Produces:
  - `(a3madkour/queue-entry-note-file) -> file|nil`, at a queue heading: via `:CITEKEY:` →
    `org-ref-notes/<key>.org` when the bib entry type is in `a3madkour/library-book-bib-types` (defcustom
    `'("book" "mvbook" "inbook")`); else via `:BOOX_KEY:` → `org-ref-notes/<key>.org`; else nil (a paper).
  - citar add, per selected key whose bib type is a book:
    - ensure the note exists (`citar-create-note` when missing, as `boox--note-for-key` does);
    - in it, write `LIBRARY_MEDIA_TYPE book`, `LIBRARY_CREATOR` (bib author), `LIBRARY_YEAR`;
    - `set-status "reading"`.
    Papers: the existing behavior, byte-for-byte.
  - `a3-reading-queue-add-book`:
    - prompts for title, creator, year, and an optional file;
    - assigns `:BOOX_KEY:` up front (`boox--book-key` on the file, or on a title-derived name when there
      is no file);
    - creates the note through `boox--ensure-book-note`;
    - writes the `LIBRARY_*` drawer and sets status `reading`;
    - appends `* TODO Read <title> :active:toread:` with `:BOOX_KEY:` (and `:READING_FILE:` if given);
    - respects the WIP limit the same way citar add does.
  - `toggle-active` on a `:toread:` entry with a note: going inactive → `set-status "queued"`; going
    active → `set-status "reading"`.
  - Hook on a `:toread:` entry with a note:
    - DONE → `set-status "finished"`;
    - DROP → `set-status "abandoned"`;
    - an already-finished note is not re-stamped (the "if blank" rule).
  - `library-close-queue-entry`, on finished/abandoned for a book note with an open entry:
    `boox--close-queue-entry`, or the DROP equivalent for abandoned. A dynamic guard
    `a3madkour/library--syncing` prevents hook re-entry.

- [ ] **Step 1: Write failing tests** (`with-org-env`, citar stubbed via `cl-letf`):
  - `library-queue/citar-book-sets-reading`;
  - `library-queue/citar-paper-untouched`: queue text is unchanged from today's format; no note
    properties are written;
  - `library-queue/add-book-uses-boox-key-filename`: the note is `org-ref-notes/<BOOX_KEY>.org`, and
    `boox--note-for-key` on that key returns the same file;
  - `library-queue/toggle-inactive-sets-queued`;
  - `library-queue/done-sets-finished`; `library-queue/drop-sets-abandoned`;
  - `library-queue/queue-done-twice-keeps-first-date`;
  - `library-queue/status-finished-closes-entry-once`: the entry becomes DONE, the WIP count drops by 1,
    and there is no recursion error.
- [ ] **Step 2: Run** `tests/run.sh library-queue`. Expected: the new tests fail.
- [ ] **Step 3: Implement** in `config.org`, then re-tangle.
- [ ] **Step 4: Run** `tests/run.sh` (the whole suite, including `boox-tests`). Expected: green, with the Boox tests unchanged.
- [ ] **Step 5: Mutation-test** the re-entry guard and the paper bypass.
- [ ] **Step 6: Commit** (dotfiles): `feat(reading-queue): queue and Boox write book status to the item note`.

### Task 9: Retire shelf files, empty-library check, real run (both repos)

**Files:**
- Modify (dotfiles): remove `a3-library-insert-item` (author.el L460) with its tests, and
  `publish-library-file` with its row-from-heading helpers, now unused. Keep the shared render/extras
  helpers Task 6 uses.
- Modify (site): `data/library-shelves.yaml`: remove the `hero:` line and the `example-*` slugs. Keep the
  tag-driven shelves; drop any slug-list shelf whose list becomes empty, and its stub under
  `content/library/shelves/` if one exists. The file's NOTE comment is updated to match.
- User action: delete `~/org/notes/library-{reading,listening,playing,watching}.org`. Ask the user to do
  it or explicitly approve it; never run it unprompted.

- [ ] **Step 1:** Run the dotfiles suite after the removals. Expected: green.
- [ ] **Step 2:** After the user deletes the shelf files, the user (or the agent, via `emacsclient`) runs `M-x a3-publish-living`. Expected:
  - all four `data/<medium>.yaml` files become `items: []`, with the collector header;
  - no `contract` or `handler` errors;
  - `data/url-history.yaml` is unchanged except for normalization.
- [ ] **Step 3:** Site checks, with no dev server alive: `rm -rf public && hugo --minify`, then:
  - `python3 tools/check_library_fixtures.py`, `check_library_links.py`, `check_library_shelves.py`,
    `check_library_covers.py`, `check_garden_fixtures.py`, `check_garden_links.py`, `check_smoke.py`,
    `check_html_links.py`, `check_lhci_urls.py`, plus their `test_` siblings;
  - `npx playwright test --workers=1`.

  Expected: all pass apart from the pre-existing failures (`test_check_pagefind_meta`,
  `test_fetch_library_covers`). Any library page or homepage Currently widget that breaks on zero items
  is fixed in its template here, with the build output checked before and after.
- [ ] **Step 4:** Spot-check with the dev server (`rm -rf public && hugo server --buildDrafts`): `/library/`, `/library/reading/` and `/` (the Currently widget). Expected: sensible empty states, no broken layout at 960px.
- [ ] **Step 5:** Log friction rows in `docs/superpowers/specs/2026-10-15-dogfood-friction-log.md`.
- [ ] **Step 6: Commit** each repo separately: dotfiles `refactor(publish-library): retire per-file shelf handler and insert-item`; site `content(library): shelves come from item notes; examples removed`.
- [ ] **Step 7: Hand off to the user for the first real item.** For example: open the Pierce ref note, `M-x a3-library-status` → reading, write a `* … :site:` section, `M-x a3-library-share`, `M-x a3-publish-living`. Then verify:
  - the garden page shows only the site text;
  - the row is on `/library/reading/` with a working "Note" link.
