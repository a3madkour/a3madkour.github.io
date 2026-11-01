# Poems As Written Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every poem line reaches the page exactly as typed, through one renderer shared by plain and timed poems.

**Architecture:** The poetry handler copies the poem body straight from the org file; ox-hugo supplies frontmatter only. One Hugo partial renders every poem from `.RawContent`; timing marks add spans and data attributes to it. A shared check refuses text Hugo would read as a shortcode.

**Tech Stack:** Emacs Lisp + ERT (dotfiles), Hugo templates + CSS, Python stdlib linter, Playwright.

**Spec:** `docs/superpowers/specs/2026-11-01-poems-as-written-design.md`

## Global Constraints

- Prose sections do not change: essays, garden, research, library, games, music, recipes.
- Never hand-edit generated bundles. Never write `~/org` from a test or build.
- Fixture text is lorem ipsum. No author prose, ever.
- Only `*bold*` and `/italic/` are interpreted. Underline, code and links show as typed.
- `#+` lines never publish, even mid-poem.
- `{{<` and `{{%` are refused, with the line number, never escaped.
- Do not run `hugo --minify` in the live checkout while the dev server is alive.
- Mutation-test every new guard.
- Work in worktrees and do not push. A dotfiles worktree needs `ln -s ~/emacs-configs/custom/straight <wt>/emacs-configs/custom/straight`, removed before `git worktree remove`. Do not tangle `config.org` in the live tree.
- ERT: `bash <lisp-dir>/run-tests.sh`. Baseline 1145 tests, 1 skipped.
- End commit messages with: `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`

## Review Focus

1. A poem whose first line is indented: trimming blank lines must not remove that line's spaces. Pinned in Task 1.
2. Keywords above the property drawer (an older file shape): the drawer must not publish as verse. Pinned in Task 1.
3. CRLF line endings: no stray `\r` in `index.md`. Pinned in Task 1.
4. Characters that look like emphasis: `* star line`, `a/b/c`, `2*3*4`, and `<b>` or `&` in a line must show as typed. Pinned in Task 2.
5. A file with settings and no verse: refused, rather than publishing an empty poem. Pinned in Task 1.

---

### Task 1: Publisher copies the poem body from the org file

**Files:**
- Modify: `emacs-configs/custom/lisp/a3madkour-publish-poetry.el` (handler stages 4-5, `count-poem-lines`, remove `collapse-escaped-markers`)
- Modify: `emacs-configs/custom/lisp/a3madkour-publish-living.el` (`contract-gap`)
- Test: `emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el`, `a3madkour-publish-living-test.el`

**Interfaces:**
- Produces: `a3madkour-pub-poetry--raw-body (file) -> string`, and `a3madkour-pub-poetry/body-gap (file) -> string or nil`.
- Produces for Task 2: an `index.md` body of raw lines joined by `\n`, ending in one newline.

- [ ] **Step 1: Write the failing tests**

In the poetry test file, using a temp-file helper that writes CONTENT and returns `(a3madkour-pub-poetry--raw-body file)`:

```elisp
;; a3madkour-pub-poetry-test/raw-body-keeps-every-line
;; "A\n  B\n      C\nD  E\n- F\n1. G\n> H\n*I* /J/\n# K\n* L\n\nM" after a drawer and keywords
;; → returned unchanged, plus a final newline.
;; raw-body-drops-drawer-and-keywords: neither :ID: nor #+TITLE appears.
;; raw-body-drops-mid-poem-keyword: "a\n#+AUDIO: x.mp3\nb" → "a\nb\n".
;; raw-body-keeps-first-line-indent: first verse line "    A" keeps its 4 spaces.
;; raw-body-skips-drawer-after-keywords: #+TITLE, then a :PROPERTIES: block, then "A" → "A\n".
;; raw-body-crlf: "A\r\nB\r\n" → "A\nB\n".
;; raw-body-trims-line-ends: "A  \nB" → "A\nB\n".
;; raw-body-keeps-escaped-marker: "\\[00:99] A" survives byte for byte.
;; body-gap-nil-for-verse.
;; body-gap-names-shortcode-line: verse with "{{< x >}}" on line 2 of the poem → string containing "line 2".
;; body-gap-percent-form: same for "{{% x %}}".
;; body-gap-empty-poem: settings only → string containing "no poem text".
```

In the living test file: `gate-refuses-a-poem-with-a-shortcode` calls `a3madkour-pub-living/contract-gap` under `a3madkour-sections-test--with-real-site` with a dated poem and matches `"line"`. `gate-leaves-other-sections-alone` confirms an essay containing `{{<` gets no such gap.

Update the handler end-to-end test so a `# K` line reaches `index.md` and `lines:` counts it. Delete the tests for `collapse-escaped-markers` and the leading-`##` exclusion.

- [ ] **Step 2: Run tests to verify they fail**

Run: `bash emacs-configs/custom/lisp/run-tests.sh 2>&1 | grep -E '^Ran|FAILED +a3'`
Expected: the new tests fail with `void-function`.

- [ ] **Step 3: Implement**

`raw-body`: read the file and normalise CRLF. Skip leading blank lines, `^#\+` lines and any `:PROPERTIES:`…`:END:` block until the first other line. From there drop `^#\+` lines, trim line-end whitespace only, and drop blank lines at both ends. Match keywords case-insensitively.

`body-gap`: nil when the file has verse and no `{{<` or `{{%`. Otherwise a message that starts with the file path. Line numbers count from 1 within the poem body.

Handler: keep the rewrite and export for frontmatter, and set `body` from `raw-body` instead of the export. Remove `collapse-escaped-markers`, and the `##` branch in `count-poem-lines`.

`contract-gap`: after the existing `missing-required` check, when SECTION is `works/poetry`, `(require 'a3madkour-publish-poetry)` and return `body-gap`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `bash emacs-configs/custom/lisp/run-tests.sh 2>&1 | grep -E '^Ran|FAILED +a3'`
Expected: 0 unexpected.

- [ ] **Step 5: Mutation-test**

Break each in turn and confirm a test fails: the `^#\+` filter, the drawer skip, CRLF handling, the `{{%` half of the check, the empty-poem clause, and the `contract-gap` call.

- [ ] **Step 6: Commit**

```bash
git add emacs-configs/custom/lisp/a3madkour-publish-poetry.el emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el emacs-configs/custom/lisp/a3madkour-publish-living.el emacs-configs/custom/lisp/a3madkour-publish-living-test.el
git commit -m "feat(poetry): the poem body comes straight from the org file"
```

### Task 2: One poem renderer

**Files:**
- Create: `layouts/partials/works/poem-body.html` (by `git mv` from `synced-text-parser.html`), `layouts/partials/works/poem-inline.html`
- Delete: `layouts/partials/works/poem-synced.html`
- Modify: `layouts/works-poetry/single.html`, `assets/css/main.css` (§45), `content/works/poetry/example-poem-synced/index.md` only if a test requires it
- Create: `content/works/poetry/example-poem-marks/index.md`, `content/works/poetry/example-poem-marks-timed/index.md`
- Test: `tests/e2e/core.spec.ts`

**Interfaces:**
- Consumes: raw `index.md` bodies from Task 1.
- Produces: `partial "works/poem-body.html" (dict "raw" .RawContent "audio" .Params.audio_url)` returning safe HTML. `partial "works/poem-inline.html" <escaped string>` returning a string.

Plain-poem markup: `<p class="poem-stanza"><span class="poem-line">…</span><br>\n…</p>`, with no wrapper, `data-t` or `poem-word`.

- [ ] **Step 1: Add the fixtures**

Lorem-ipsum twins of the 13-line sample: the same frontmatter shape as `example-poem-minimal`, and these bodies. The timed twin puts `[00:NN]` before each non-blank line.

```text
Lorem ipsum dolor.
Sit amet consectetur.

Adipiscing elit sed.
  Eiusmod tempor.
      Incididunt ut.
Labore  et  dolore.
- magna aliqua
1. enim minim
> veniam quis
*nostrud* and /exercitation/
# ullamco laboris
* nisi aliquip
ex a/b/c 2*3*4 <b> & ea
```

- [ ] **Step 2: Write the failing tests**

Add to `core.spec.ts`, looping over both fixtures:

```ts
// 'poem marks: every line as typed (<slug>)'
// const lines = await page.locator('.works-poem-body .poem-line').allInnerTexts();
// expect(lines.map(l => l.replace(/ /g, ' ').trimEnd())).toEqual(SAMPLE_LINES);
// SAMPLE_LINES keeps "  Eiusmod tempor." with its leading spaces, and has no blank entries.
// await expect(page.locator('.works-poem-body :is(ul, ol, h1, h2, h3, blockquote)')).toHaveCount(0);
// await expect(page.locator('.works-poem-body')).not.toContainText('aria-label');
// await expect(page.locator('.works-poem-body strong')).toHaveText('nostrud');
// await expect(page.locator('.works-poem-body em')).toHaveText('exercitation');

// 'poem marks: indentation is a real offset'
// x of the Range around the text of "Incididunt ut." is greater than x of "Lorem ipsum dolor.", on the plain fixture.

// 'a plain poem has no player or timing'
// on example-poem-marks: .poem-player count 0, [data-t] count 0, .poem-synced count 0.

// 'a long poem line wraps at phone width'
// viewport 400: document.documentElement.scrollWidth <= 400 on /works/poetry/example-poem-marks/.
```

Add to the sample's fixture a final long line of lorem ipsum, over 120 characters, for the wrap test, and include it in `SAMPLE_LINES`.

- [ ] **Step 3: Run to verify they fail**

From the site worktree: `hugo --minify --quiet && E2E_PORT=8090 npx playwright test tests/e2e/core.spec.ts -g 'poem' --workers=1`
Expected: the new tests fail.

- [ ] **Step 4: Implement**

`poem-inline.html` takes already-escaped text and returns it with emphasis applied. Italic runs first, because `</strong>` contains a slash. A marker hugs its text and has a line edge, whitespace or punctuation outside it:

```text
(^|[\s\p{P}])/(\S|\S.*?\S)/($|[\s\p{P}])   →  $1<em>$2</em>$3
(^|[\s\p{P}])\*(\S|\S.*?\S)\*($|[\s\p{P}])  →  $1<strong>$2</strong>$3
```

`* nisi aliquip` must stay literal because the opening star is followed by a space. Note that the `*` and `/` in `2*3*4` and `a/b/c` are inside words, so the outer rule rejects them.

`poem-body.html`, from the old parser:
- Escaped-marker protection, marker grammar and stanza logic stay.
- A line is blank only if trimming leaves nothing, but the kept line loses only line-end whitespace.
- `htmlEscape` each line, then `poem-inline`. Remove `RenderString` and the `$hasMd` branch.
- If `.raw` has no unescaped marker: emit one `poem-line` span per line and no wrapper.
- Timed lines keep today's spans. Text before the first marker stays as indent. An empty token from `split` appends one literal space, so runs survive. Tokens go through `poem-inline`.
- Add `data-audio-src` to the wrapper from `.audio`, replacing `poem-synced.html`.

`single.html`: replace the whole `findRE` branch with `{{ partial "works/poem-body.html" (dict "raw" .RawContent "audio" .Params.audio_url) | safeHTML }}`.

§45 CSS: `.poem-line { white-space: pre-wrap; }`.

Update the marker-grammar comment that names `single.html`, and `grep -rn 'synced-text-parser\|poem-synced.html' layouts tools assets` for stale references.

- [ ] **Step 5: Run to verify they pass**

Run the Step 3 command without `-g`, then:
`python3 tools/check_poetry_synced.py && python3 tools/check_works_fixtures.py && python3 tools/check_works_links.py && python3 tools/check_css_refs.py && python3 tools/check_meta_description.py`
Expected: all tests pass and all linters report OK. Fix a `check_meta_description` failure in `head.html` only if a poem page is the one reported.

- [ ] **Step 6: Mutation-test**

Confirm a test fails when you: swap the italic and bold order, remove `htmlEscape`, remove `pre-wrap`, and make the no-marker branch emit `data-t`.

- [ ] **Step 7: Commit**

```bash
git add layouts assets/css/main.css content/works/poetry tests/e2e/core.spec.ts
git commit -m "feat(poetry): one renderer for every poem, lines as typed"
```

### Task 3: Linter refuses shortcode text

**Files:**
- Modify: `tools/check_poetry_synced.py`
- Test: `tools/test_check_poetry_synced.py`

**Interfaces:** the linter keeps `run(repo_root) -> (int, list[str])`. The new rule applies to every poem, timed or not.

- [ ] **Step 1: Write the failing tests**

```python
def test_shortcode_open_is_an_error_on_a_plain_poem(self):
    # body "a\n{{< x >}}\n" → one error containing the file path and "{{<"
def test_percent_shortcode_is_an_error(self):
    # body "{{% x %}}\n"
def test_clean_plain_poem_passes(self):
    # body "a\nb\n" → rc 0
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 -m unittest tools/test_check_poetry_synced.py 2>&1 | tail -3`
Expected: FAIL.

- [ ] **Step 3: Implement** in `run`, ahead of the existing has-markers skip, and add the rule to the module docstring.

- [ ] **Step 4: Run to verify they pass**

Run: `python3 -m unittest tools/test_check_poetry_synced.py 2>&1 | tail -3 && python3 tools/check_poetry_synced.py`
Expected: OK. Then remove the new check and confirm the tests fail, and restore it.

- [ ] **Step 5: Commit**

```bash
git add tools/check_poetry_synced.py tools/test_check_poetry_synced.py
git commit -m "feat(lint): a poem body cannot hold shortcode text"
```

### Task 4: Prove it end to end and update the docs

**Files:**
- Modify: `CLAUDE.md`, `docs/superpowers/specs/2026-05-19-org-synced-poetry-export.md`, `docs/superpowers/specs/2026-10-15-dogfood-friction-log.md`

**Interfaces:** consumes all earlier tasks.

- [ ] **Step 1: Run the trace sample through the real commands**

In a scratch copy of the site worktree, use a scratch `A3_PUB_PATHS_FILE` that sets every variable in `a3madkour-pub/path-variables`, plus `org-roam-directory`, `org-roam-db-location` and `org-id-locations-file`, to scratch paths. Set `A3_PUB_SITE_DATA_DIR` to the copy's `data/`. Write a plain and a timed poem, run `a3-pub.sh --publish-deliberate <file> --skip-math-check`, then build with `hugo --destination <scratch> --cacheDir <scratch>`.

Expected: 13 of 13 lines as written in both poems. Confirm nothing under `~/org` is newer than a stamp file taken before the run.

- [ ] **Step 2: Confirm prose is unchanged**

Run in both the worktree and a checkout of the base commit: `hugo --quiet --destination <dir> --cacheDir <scratch>`. Then `diff -r` the outputs, ignoring `works/poetry/`, the fixture pages' graph and list entries, and hashed filenames.
Expected: no changed essay, garden, research, library, recipe, game or music page body.

- [ ] **Step 3: Update the docs**

`CLAUDE.md`: Playwright spec and test counts, the `works/` partial list, and the poem path. The 2026-05-19 spec: a status note pointing to this design. Friction row 44: triage `fixed`, with the commits.

- [ ] **Step 4: Run the full checks**

Run: `bash emacs-configs/custom/lisp/run-tests.sh`, `bash emacs-configs/custom/tests/run.sh`, then `python3 -m unittest discover -s tools -p 'test_check_*.py'`.
Expected: ERT and config suites clean. Report any Python failure beyond the known `test_check_pagefind_meta` and `test_fetch_library_covers`.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md docs/superpowers/specs
git commit -m "docs: poems render as written"
```

- [ ] **Step 6: Hand over**

Merge both worktrees locally only with the author's approval. Then the author runs `a3-publish-deliberate` on `defend.org` and `smoke-test-poem.org`. Rerun the poetry linters and view both pages. Do not push; both repos go up at the end of S1.
