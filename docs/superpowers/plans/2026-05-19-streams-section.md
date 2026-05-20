# Streams Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the 7th top-level `/streams/` section: per-stream archive pages with click-to-load YouTube embeds, bidirectional cross-references to essays/garden/research/works, a header live-pill driven by a cron-polled GitHub Action, and a homepage upcoming-streams strip.

**Architecture:** Spec §2 "Approach A" — fully GitHub-Action-driven. One cron Action (`*/5 * * * *`) runs `tools/poll_streams.py` (stdlib + Twitch OAuth + YouTube HEAD probe), writes `data/streams-*.yaml`, and creates auto-stub `content/streams/<slug>/index.md` files on stream-end transitions. Each commit triggers the existing Pages deploy. Two new linter pairs (22nd + 23rd) — `check_streams_fixtures` + `check_streams_links` (bidirectional cross-ref symmetry). Hugo templates read the yaml at build time; no live-state polling JS.

**Tech Stack:** Hugo extended 0.148.0 · Python 3 stdlib (linters + poller) · vanilla JS (click-to-load embed) · hand-rolled CSS (append §46) · GitHub Actions (cron + Pages).

**Spec:** `docs/superpowers/specs/2026-05-13-streams-section-design.md` (read §0 reconciliation first — it governs §1–§16).

**Environment caveat (per session pointer memory):** This agent sandbox SIGKILLs every `hugo` invocation (exit 144) and cannot reach Twitch/YouTube APIs. Python linters + the poller DO run here (stdlib, unittest, mockable HTTP). Hugo template/CSS/JS verification is **user-side** (dev server `hugo server --buildDrafts`). The live cron path is verified **post-merge** by the user (set Twitch dev-app + YouTube key + repo secrets/vars → `workflow_dispatch`). Plan tasks call out the split explicitly per step.

**Working branch:** `feature/streams-section` (already created — spec reconciliation is the first commit `2a0ce4b`).

---

## File map

### New
- `tools/check_streams_fixtures.py` + `tools/test_check_streams_fixtures.py` — 22nd linter pair (per-stream frontmatter contract)
- `tools/check_streams_links.py` + `tools/test_check_streams_links.py` — 23rd linter pair (bidirectional `related_* ↔ source_stream` symmetry)
- `tools/poll_streams.py` + `tools/test_poll_streams.py` — cron poller (Twitch OAuth + YouTube HEAD probe + auto-stub)
- `.github/workflows/streams-poll.yaml` — cron workflow
- `content/streams/_index.md` + `content/streams/<two dummy stream slugs>/index.md`
- `data/streams-schedule.yaml` (user-authored seed) · `data/streams-twitch-cache.yaml` · `data/streams-live.yaml`
- `layouts/streams/list.html` + `layouts/streams/single.html`
- `layouts/partials/streams/live-pill.html` · `embed.html` · `cross-refs.html` · `stream-card.html` · `upcoming.html` · `from-stream.html`
- `layouts/partials/home/streams-strip.html`
- `assets/js/streams.js` + `assets/js/entry-streams.js`

### Modified
- `assets/css/main.css` — append §46
- `data/filter-chips.yaml` — add `streams:` block
- `layouts/_default/baseof.html` — add `"streams"` to triplicated `$citable_sections` predicate
- `layouts/partials/head.html` — same + `archive_status` conditional
- `layouts/partials/scripts.html` — same + 11th `js.Build` entry for `entry-streams.js`
- `layouts/partials/header.html` — 7th nav item + live-pill include
- `layouts/partials/search-modal.html` — add Streams filter chip
- `layouts/partials/cite/normalize-page.html` — streams branch (BibTeX `misc`, archive_status note)
- `layouts/partials/cite/button.html` + `layouts/partials/cite/static-fallback.html` — "Cite this stream" label
- `layouts/home.html` — wire streams strip + page-sidebar section entry
- 7 single templates — include `from-stream.html`: `layouts/essays/single.html`, `layouts/garden/single.html`, `layouts/research-theme/single.html`, `layouts/research-question/single.html`, `layouts/works-games/single.html`, `layouts/works-music/single.html`, `layouts/works-poetry/single.html`
- 4 existing fixture linters: `tools/check_fixtures.py` (essays — no allowed-set change, test only), `tools/check_garden_fixtures.py`, `tools/check_research_fixtures.py`, `tools/check_works_fixtures.py` — accept optional `source_stream`
- 3 post-build linters: `tools/check_pagefind_meta.py` (+ test), `tools/check_cite_meta.py` (+ test), `tools/check_page_weights.py` (+ test) — recognize `streams`
- `tools/check_filter_chips_config.py` — no code change (default branch); test only
- `.github/workflows/hugo.yaml` + `tools/ci-local.sh` — register 2 new linter pairs (insert before `check_graph_chrome` in pre-build block)
- 7-ish existing fixture frontmatter — add `source_stream:` round-trip refs (one per section: essays, garden, research-theme, research-question, works-games, works-music, works-poetry)
- `CLAUDE.md` — counts: 21→23 linter pairs · 55→59 CI steps · 10→11 JS entries · nav locked 6→7 · CSS §46 · deferred-queue row promoted

---

## Standing constraints (per memory + CLAUDE.md)

1. **No `→` arrows on new link labels** (memory `feedback_no_arrow_prefix_on_links`, strengthened 2026-05-13). Existing home strips use `All essays →` etc. — DO NOT propagate that pattern to new streams chrome. Use plain `All streams`, `Watch on Twitch`, etc.
2. **Filler text in fixtures is "Example N" / lorem ipsum only** — never AI-author prose (memory `feedback_filler_text_only`).
3. **`data-tags` must be space-delimited** (memory `reference_filter_chips_data_tags_space_delimited`) — `{{ delimit .Params.tags " " }}`.
4. **Hugo hyphenated data files** require `index site.Data "streams-live"` — dot syntax breaks silently.
5. **`data-pagefind-meta` is one key per element** — multiple keys = multiple spans.
6. **`data-pagefind-filter` is separate from `data-pagefind-meta`** — distinct span required.
7. **Never run `hugo --minify`/`rm -rf public` against a worktree while the user has a dev server alive** (memory `reference_hugo_dev_server_gotcha`).
8. **Hugo `int "08"` parses as octal** — for any zero-padded numeric markers cast via `int (float $s)` (memory `reference_hugo_int_octal_gotcha`).
9. **`<dialog>.close()` — never `removeAttribute('open')`** (memory `reference_dialog_close_inert_state`). Streams has no modal; informational.
10. **Page-sidebar (`partials/page-sidebar.html`) does NOT auto-include** — per-layout responsibility. Streams single pages OPT OUT (single-section pages don't need the rail per spec §15).
11. **Streams single pages MUST emit cite scaffolding** (spec §10 — citable when `archive_status ∈ {archived, removed}`). Per spec §0 reconciliation, RSS is NOT introduced for streams.

---

## Cross-ref slug pin (used throughout)

Existing non-draft fixtures the streams will bidirectionally cross-link to. Pinned here so every later task references the same slugs:

- **Essay**: `example-essay-one`
- **Garden note**: `story-atoms`
- **Game**: `example-playable-full-release`
- **Music**: `example-live-session`
- **Poem**: `example-poem-collected`
- **Research question**: `what-is-a-narrative-atom`
- **Research theme**: `memory-and-play`

Two streams fixtures (Phase 2):
- `2026-04-10-example-live-coding-stream` — `archive_status: archived`, refs game + research-question + garden.
- `2026-04-22-example-music-jam-stream` — `archive_status: removed`, refs music + poem + essay + theme.

---

# Phase 1 — Existing linter extensions (accept `source_stream`)

These come FIRST so subsequent tasks can add `source_stream:` to fixtures without tripping the unknown-field gate.

## Task 1: Extend `check_garden_fixtures.py` to accept `source_stream`

**Files:**
- Modify: `tools/check_garden_fixtures.py:20-46` (the `*_FIELDS` constants)
- Test: `tools/test_check_garden_fixtures.py` (append one new test method)

- [ ] **Step 1: Write the failing test**

Append the following method inside the existing test class in `tools/test_check_garden_fixtures.py` (find the last `def test_*` in the file and add this beside it; reuse whatever `_write` helper / valid-fixture string the existing tests use):

```python
    def test_source_stream_accepted_on_concept_note(self):
        body = """\
---
title: "Example concept note"
draft: false
last_modified: 2026-05-19
growth_stage: budding
source_stream: 2026-04-10-example-live-coding-stream
---

Body.
"""
        d = self.tmp / "content" / "garden" / "with-source-stream"
        d.mkdir(parents=True)
        (d / "index.md").write_text(body)
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_source_stream_accepted_on_media_note(self):
        body = """\
---
title: "Example media note"
draft: false
last_modified: 2026-05-19
growth_stage: budding
media_type: book
status: reading
creator: "Author X"
source_stream: 2026-04-10-example-live-coding-stream
---

Body.
"""
        d = self.tmp / "content" / "garden" / "with-source-stream-media"
        d.mkdir(parents=True)
        (d / "index.md").write_text(body)
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_source_stream_accepted_on_reference_note(self):
        body = """\
---
title: "Example reference note"
draft: false
last_modified: 2026-05-19
growth_stage: evergreen
media_type: paper
creator: "Author X"
source_stream: 2026-04-10-example-live-coding-stream
---

Body.
"""
        d = self.tmp / "content" / "garden" / "with-source-stream-ref"
        d.mkdir(parents=True)
        (d / "index.md").write_text(body)
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tools/test_check_garden_fixtures.py -v 2>&1 | tail -20`
Expected: 3 failures, each error matches `"source_stream" not permitted on <flavor> notes`.

- [ ] **Step 3: Add `source_stream` to all three allowed sets**

Edit `tools/check_garden_fixtures.py`. Find the `CONCEPT_FIELDS` / `MEDIA_FIELDS` / `REFERENCE_FIELDS` declarations (around lines 33-46). Add `"source_stream"` to each:

```python
CONCEPT_FIELDS = ALWAYS_REQUIRED | {"tags", "summary", "topic_map", "roam_refs", "year", "weight", "source_stream"}
MEDIA_FIELDS = ALWAYS_REQUIRED | {
    "media_type", "status", "creator",
    "tags", "summary", "topic_map", "roam_refs", "year",
    "original_url", "started", "finished", "spoiler_level",
    "source_stream",
}
REFERENCE_FIELDS = ALWAYS_REQUIRED | {
    "media_type", "creator",
    "tags", "summary", "topic_map", "roam_refs", "year",
    "original_url",
    "source_stream",
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tools/test_check_garden_fixtures.py -v 2>&1 | tail -10`
Expected: all tests pass. Also re-run the linter against the real tree to confirm no regression: `python3 tools/check_garden_fixtures.py` → `check_garden_fixtures: OK` (or the existing dialect's pass message).

- [ ] **Step 5: Commit**

```bash
git add tools/check_garden_fixtures.py tools/test_check_garden_fixtures.py
git commit -m "lint(garden): accept optional source_stream on all three note flavors

Phase 1 prep for streams section. source_stream is the back-edge
of bidirectional related_garden ↔ source_stream symmetry; the
check_streams_links linter (Phase 3) enforces resolution.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Extend `check_research_fixtures.py` to accept `source_stream`

**Files:**
- Modify: `tools/check_research_fixtures.py:22-30` (`THEME_OPTIONAL` + `QUESTION_OPTIONAL`)
- Test: `tools/test_check_research_fixtures.py` (append two tests)

- [ ] **Step 1: Write the failing tests**

Append to `tools/test_check_research_fixtures.py` (find the existing `LintThemeTests` / question-test class and add beside the other methods):

```python
THEME_WITH_SOURCE_STREAM = """\
---
title: "Memory and play"
status: active
tags: [memory, play]
last_modified: 2026-05-11
description: "Theme framing."
weight: 10
source_stream: 2026-04-22-example-music-jam-stream
---

Body.
"""

QUESTION_WITH_SOURCE_STREAM = """\
---
title: "How do readers form narrative?"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "Question framing."
source_stream: 2026-04-10-example-live-coding-stream
---

Body.
"""
```

And the test methods (placed in `LintThemeTests` and the existing question-test class respectively):

```python
    # in LintThemeTests:
    def test_theme_accepts_source_stream(self):
        _write(self.tmp, "with-stream-theme", THEME_WITH_SOURCE_STREAM)
        self.assertEqual([], lint.lint_theme(self.tmp / "with-stream-theme"))
```

```python
    # in the question test class (same file, search for `lint_question` test method):
    def test_question_accepts_source_stream(self):
        _write(self.tmp, "with-stream-q", QUESTION_WITH_SOURCE_STREAM)
        self.assertEqual([], lint.lint_question(self.tmp / "with-stream-q"))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tools/test_check_research_fixtures.py -v 2>&1 | tail -10`
Expected: both new tests fail with `unknown field 'source_stream'`.

- [ ] **Step 3: Add `source_stream` to both OPTIONAL sets**

Edit `tools/check_research_fixtures.py`:

```python
THEME_OPTIONAL = {"garden_topic_ref", "summary", "source_stream"}
```

```python
QUESTION_OPTIONAL = {
    "parent_question", "started", "tags",
    "supporting_notes", "related_essays", "outputs", "weight",
    "source_stream",
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tools/test_check_research_fixtures.py -v 2>&1 | tail -10`
Expected: all pass. Smoke-run: `python3 tools/check_research_fixtures.py` → OK.

- [ ] **Step 5: Commit**

```bash
git add tools/check_research_fixtures.py tools/test_check_research_fixtures.py
git commit -m "lint(research): accept optional source_stream on themes + questions

Phase 1 prep for streams section. Mirrors the garden change in
Task 1. check_streams_links (Phase 3) enforces round-trip resolution.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Extend `check_works_fixtures.py` to accept `source_stream`

**Files:**
- Modify: `tools/check_works_fixtures.py:30-51` (`GAME_OPTIONAL`, `MUSIC_OPTIONAL`, `POEM_OPTIONAL`)
- Test: `tools/test_check_works_fixtures.py` (append three tests)

- [ ] **Step 1: Write the failing tests**

Append to `tools/test_check_works_fixtures.py` (inside `WorksFixturesLinterTests`):

```python
    def test_game_accepts_source_stream(self):
        body = GAME_VALID.replace(
            "year: 2026\n",
            "year: 2026\nsource_stream: 2026-04-10-example-live-coding-stream\n",
        )
        p = self._write("games", "with-source-stream", body)
        self.assertEqual(lint.lint_file(p), [])

    def test_music_accepts_source_stream(self):
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            "year: 2026\nsource_stream: 2026-04-22-example-music-jam-stream\n",
        )
        p = self._write("music", "with-source-stream", body)
        self.assertEqual(lint.lint_file(p), [])

    def test_poem_accepts_source_stream(self):
        body = POEM_VALID.replace(
            "lines: 14\n",
            "lines: 14\nsource_stream: 2026-04-22-example-music-jam-stream\n",
        )
        p = self._write("poetry", "with-source-stream", body)
        self.assertEqual(lint.lint_file(p), [])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tools/test_check_works_fixtures.py -v 2>&1 | tail -10`
Expected: 3 failures, each `unknown field 'source_stream'`.

- [ ] **Step 3: Add `source_stream` to the three OPTIONAL sets**

Edit `tools/check_works_fixtures.py`:

```python
GAME_OPTIONAL = {
    "tags", "summary", "hero", "embed_url", "source_url", "itch_url",
    "collaborators", "tech_stack", "length", "screenshots",
    "research_questions", "related_essays", "related_notes",
    "source_stream",
} | UMBRELLA_OPTIONAL
```

```python
MUSIC_OPTIONAL = {
    "tags", "summary", "tagline", "cover", "duration",
    "tracks", "platform_embed", "audio_url", "lyrics_poem",
    "related_works", "related_essays", "made_with", "collaborators",
    "source_stream",
} | UMBRELLA_OPTIONAL
```

```python
POEM_OPTIONAL = {"tags", "collection", "set_to_music", "summary", "audio_url", "source_stream"} | UMBRELLA_OPTIONAL
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tools/test_check_works_fixtures.py -v 2>&1 | tail -10`
Expected: all pass. Smoke-run: `python3 tools/check_works_fixtures.py` → OK.

- [ ] **Step 5: Commit**

```bash
git add tools/check_works_fixtures.py tools/test_check_works_fixtures.py
git commit -m "lint(works): accept optional source_stream on games/music/poetry

Phase 1 prep for streams section. Mirrors Tasks 1 + 2.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Confirm essays accept `source_stream` (test-only, no linter change)

`tools/check_fixtures.py` (essays) is open-set — there is no `fm.keys() - allowed` gate. `source_stream` will silently pass. This task adds a unit-test asserting that contract so it's documented and locked.

**Files:**
- Test: `tools/test_check_fixtures.py` (append one test)

- [ ] **Step 1: Write the test**

Append to `tools/test_check_fixtures.py` inside `CheckFixturesTest`:

```python
    def test_source_stream_accepted_on_essay(self) -> None:
        body = VALID_FRONTMATTER.replace(
            "has_video_sync: false\n",
            "has_video_sync: false\nsource_stream: 2026-04-10-example-live-coding-stream\n",
        )
        self.repo.write_essay("with-source-stream", body, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")
```

- [ ] **Step 2: Run test to verify it passes immediately**

Run: `python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -10`
Expected: PASS without any linter change (essay frontmatter is open-set).

- [ ] **Step 3: Commit**

```bash
git add tools/test_check_fixtures.py
git commit -m "test(essays): pin contract — source_stream silently accepted

Essay linter is open-set (no unknown-field gate); this locks the
contract so a future tightening would surface here rather than
breaking source_stream cross-refs from streams pages.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Extend `check_pagefind_meta.py` to recognize `/streams/`

**Files:**
- Modify: `tools/check_pagefind_meta.py` (`SECTION_BY_PREFIX` constant)
- Test: `tools/test_check_pagefind_meta.py` (append two tests)

- [ ] **Step 1: Write the failing tests**

Append to `tools/test_check_pagefind_meta.py` (find the existing `TestSection*` class, add beside it; if there is no such class, place them in the topmost test class in the file):

```python
    def test_section_from_streams_path(self):
        self.assertEqual(check_pagefind_meta.section_from_path("/streams/some-slug/"), "streams")

    def test_section_from_streams_index(self):
        self.assertEqual(check_pagefind_meta.section_from_path("/streams/"), "streams")
```

If the test file uses `from check_pagefind_meta import section_from_path` style instead, replace the qualified name accordingly.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m unittest test_check_pagefind_meta.py -v 2>&1 | tail -15`
Expected: both fail; `section_from_path("/streams/some-slug/")` returns `"home"` (the catch-all wins).

- [ ] **Step 3: Add `/streams/` BEFORE the `/` catch-all**

Edit `tools/check_pagefind_meta.py`. In `SECTION_BY_PREFIX`, insert `("/streams/", "streams")` immediately before `("/", "home")`:

```python
SECTION_BY_PREFIX = [
    ("/essays/",   "essays"),
    ("/garden/",   "garden"),
    ("/research/", "research"),
    ("/works/",    "works"),
    ("/library/",  "library"),
    ("/about/",    "about"),
    ("/blog/",     "blog"),
    ("/credits/",  "credits"),
    ("/streams/",  "streams"),
    ("/",          "home"),
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m unittest test_check_pagefind_meta.py -v 2>&1 | tail -10`
Expected: PASS. (Cannot run `python3 tools/check_pagefind_meta.py` here — it requires `public/` from a Hugo build; that runs in CI.)

- [ ] **Step 5: Commit**

```bash
git add tools/check_pagefind_meta.py tools/test_check_pagefind_meta.py
git commit -m "lint(pagefind): recognize /streams/ as a valid section prefix

Phase 1 prep. Inserted before the / catch-all so /streams/<slug>/
resolves to section 'streams' rather than 'home'.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Extend `check_cite_meta.py` — streams items citable

Per spec §10, streams pages with `archive_status ∈ {archived, removed}` are citable.

**Files:**
- Modify: `tools/check_cite_meta.py` (`CITABLE_PREFIXES` + `NON_CITABLE_EXACT`)
- Test: `tools/test_check_cite_meta.py` (append four tests)

- [ ] **Step 1: Write the failing tests**

Append to `tools/test_check_cite_meta.py` inside the existing `TestCiteMeta` class:

```python
    def test_is_citable_path_streams_item_yes(self):
        self.assertTrue(is_citable_path('public/streams/2026-04-10-example-live-coding-stream/index.html'))

    def test_is_citable_path_streams_index_no(self):
        self.assertFalse(is_citable_path('public/streams/index.html'))

    def test_is_citable_path_streams_slug_with_date_prefix(self):
        # Streams slugs are <YYYY-MM-DD>-<title-slug>; ensure deep paths work.
        self.assertTrue(is_citable_path('public/streams/2026-04-22-example-music-jam-stream/index.html'))

    def test_is_citable_path_streams_non_index_html_no(self):
        # Files other than index.html under /streams/ are not citable.
        self.assertFalse(is_citable_path('public/streams/2026-04-10-x/somefile.html'))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m unittest test_check_cite_meta.py -v 2>&1 | tail -15`
Expected: 2-3 fail (`is_citable_path` returns `False` for streams paths because `public/streams/` is not in `CITABLE_PREFIXES`).

- [ ] **Step 3: Extend the two constants**

Edit `tools/check_cite_meta.py`. Add `'public/streams/'` to `CITABLE_PREFIXES` (last entry):

```python
CITABLE_PREFIXES = (
    'public/essays/',
    'public/garden/',
    'public/research/themes/',
    'public/research/questions/',
    'public/works/games/',
    'public/works/music/',
    'public/works/poetry/',
    'public/streams/',
)
```

Add `'public/streams/index.html'` to `NON_CITABLE_EXACT` (alongside other section-index entries):

```python
NON_CITABLE_EXACT = {
    'public/index.html',
    'public/about/index.html',
    'public/library/index.html',
    'public/library/reading/index.html',
    'public/library/listening/index.html',
    'public/library/playing/index.html',
    'public/library/watching/index.html',
    'public/essays/index.html',
    'public/garden/index.html',
    'public/garden/graph/index.html',
    'public/garden/history/index.html',
    'public/research/index.html',
    'public/research/graph/index.html',
    'public/works/index.html',
    'public/works/graph/index.html',
    'public/works/games/index.html',
    'public/works/music/index.html',
    'public/works/poetry/index.html',
    'public/streams/index.html',
}
```

**Note** (informational): the `archive_status ∈ {archived, removed}` gating is enforced by the Hugo-side citable predicate (Task 17) — `check_cite_meta.py` only checks that markup is present on pages that DO render cite scaffolding. Pages with `archive_status: live` won't emit cite markup at all (the predicate skips them), so the linter has nothing to assert on them and they get silently audited as "no cite-data found → fail" — to handle this cleanly, add an exact-path exception for any live page IF needed. For the seeded fixtures (one `archived`, one `removed`), this is moot.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m unittest test_check_cite_meta.py -v 2>&1 | tail -10`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/check_cite_meta.py tools/test_check_cite_meta.py
git commit -m "lint(cite): streams items citable (archived/removed); index excluded

Phase 1 prep. Per spec §10, streams with archive_status archived|removed
emit cite scaffolding. Live streams skip the predicate so they aren't
audited (gating is Hugo-side; see Task 17). Index page is non-citable
like other section indexes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Extend `check_page_weights.py` — `/streams/` tier 300 KB (per spec §13)

**Files:**
- Modify: `tools/check_page_weights.py` (`BUDGETS_PREFIX`)
- Test: `tools/test_check_page_weights.py` (append two tests)

- [ ] **Step 1: Write the failing tests**

Append to `tools/test_check_page_weights.py` inside `TestBudgetFor`:

```python
    def test_streams_item_tier(self):
        self.assertEqual(cpw.budget_for("/streams/2026-04-10-example-live-coding-stream/"), 300_000)

    def test_streams_index_default(self):
        # Section index falls through to BUDGET_DEFAULT (100 KB) per spec §13.
        self.assertEqual(cpw.budget_for("/streams/"), 300_000)
```

**Note**: spec §13 says `/streams/` (the index) uses the default 100 KB — but the prefix `/streams/` matches both index AND items in `BUDGETS_PREFIX`. To distinguish, we'd need exact-match handling (like `/` → `BUDGET_HOMEPAGE`). The simplest faithful interpretation: budget the whole prefix at 300 KB; the index is empty enough to land well under it. The test reflects this — if you want index-vs-item distinction, refactor `budget_for` to add an exact-match table; out of scope here.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tools/test_check_page_weights.py -v 2>&1 | tail -10`
Expected: both fail with `100000 != 300000` (falls through to `BUDGET_DEFAULT`).

- [ ] **Step 3: Add the `/streams/` tier**

Edit `tools/check_page_weights.py`. Insert into `BUDGETS_PREFIX` (position doesn't matter relative to other prefixes since `/streams/` doesn't share a prefix with anything except `/`):

```python
    ("/streams/",        300_000),   # per-stream page: YT thumbnail (~30KB lazy) + cite blob + chrome
```

Place it adjacent to `/essays/` for readability:

```python
    ("/essays/",         200_000),   # essay pages — accumulated CSS growth (sidenotes, citations, Bento, §43)
    ("/streams/",        300_000),   # streams archive pages — YT thumbnail (lazy) + cite blob + chrome
    ("/about/",          150_000),   # thin page; site-wide CSS bundle dominates
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tools/test_check_page_weights.py -v 2>&1 | tail -10`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/check_page_weights.py tools/test_check_page_weights.py
git commit -m "lint(weights): /streams/ tier at 300KB (spec §13)

Phase 1 prep. YouTube thumbnail (~30KB lazy) + cite data blob (~2KB)
+ click-to-load JS (~1KB) + standard chrome + show notes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: `check_filter_chips_config.py` — confirm default branch handles `streams`

No code change needed (the `_section_content_paths` default returns `[repo_root / "content" / section]`, which works for `content/streams/`). Add a test asserting this, and add a placeholder `streams:` block to `data/filter-chips.yaml` to exercise it.

**Files:**
- Modify: `data/filter-chips.yaml` (append `streams:` block)
- Test: `tools/test_check_filter_chips_config.py` (append one test)

- [ ] **Step 1: Add a `streams:` block to `data/filter-chips.yaml`**

Append to `data/filter-chips.yaml`:

```yaml
streams:
  primary_tags: [example, prototype, lyric]
  primary_top_k: 10
```

(These tags must appear on at least one streams fixture for the linter to pass; we'll seed them in Phase 2 Task 9.)

- [ ] **Step 2: Write the test**

Append to `tools/test_check_filter_chips_config.py` (find the existing test class, add beside it):

```python
    def test_streams_section_default_path(self):
        # The default branch should map 'streams' → content/streams/ without
        # needing a SECTION_PATH_OVERRIDES entry.
        import check_filter_chips_config as cfc
        paths = cfc._section_content_paths(self.tmp, "streams")
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].name, "streams")
        self.assertEqual(paths[0].parent.name, "content")
```

Adapt `self.tmp` to whatever the existing fixture root attribute is.

- [ ] **Step 3: Run test to verify it passes immediately**

Run: `python3 -m unittest tools/test_check_filter_chips_config.py -v 2>&1 | tail -10`
Expected: PASS (no code change needed).

- [ ] **Step 4: Smoke-run the real linter — EXPECT a failure until Phase 2 seeds tags**

Run: `python3 tools/check_filter_chips_config.py`
Expected: failures of the form `data/filter-chips.yaml:streams.primary_tags: "<tag>" is not used by any non-draft note in /content/streams/`. This is **expected** — the streams content dir is empty until Phase 2 Task 9. **Do not commit yet** if this is the only failure; we commit the filter-chips block + the seeded fixtures together in Task 9.

- [ ] **Step 5: HOLD — defer commit to Task 9's combined commit**

Track in TodoWrite: "filter-chips streams block staged; commit with Task 9 fixtures."

---

# Phase 2 — Streams content fixtures + data files

## Task 9: Section `_index.md` + two stream fixtures + filter-chips data commit

**Files:**
- Create: `content/streams/_index.md`
- Create: `content/streams/2026-04-10-example-live-coding-stream/index.md`
- Create: `content/streams/2026-04-22-example-music-jam-stream/index.md`

- [ ] **Step 1: Create the section index**

Write `content/streams/_index.md`:

```markdown
---
title: 'Streams'
description: 'Live broadcasts on Twitch and YouTube — archived here with show notes and cross-references to whatever they produced.'
type: streams
cascade:
  type: streams
---
```

- [ ] **Step 2: Create the first stream fixture (archived, with VOD)**

Write `content/streams/2026-04-10-example-live-coding-stream/index.md`:

```markdown
---
title: "Example live coding stream"
date: 2026-04-10T19:00:00-04:00
duration: "2h 15m"
platforms: [twitch, youtube]
vod_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
twitch_archive_url: ""
archive_url: ""
archive_status: archived
category: coding
tags: [example, prototype]
summary: "Lorem ipsum dolor sit amet — example live coding session."
related_essays: []
related_garden: [story-atoms]
related_research: [what-is-a-narrative-atom]
related_works: [example-playable-full-release]
draft: false
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Example show notes.

## What we did

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
```

- [ ] **Step 3: Create the second stream fixture (removed, no VOD)**

Write `content/streams/2026-04-22-example-music-jam-stream/index.md`:

```markdown
---
title: "Example music jam stream"
date: 2026-04-22T20:00:00-04:00
duration: "1h 40m"
platforms: [twitch, youtube]
vod_url: ""
twitch_archive_url: ""
archive_url: ""
archive_status: removed
category: creative
tags: [example, lyric]
summary: "Lorem ipsum — example music jam; archive intentionally removed for the fixture."
related_essays: [example-essay-one]
related_garden: []
related_research: []
related_works: [example-live-session, example-poem-collected]
draft: false
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Example show notes for the music jam.
```

- [ ] **Step 4: Smoke check (skip the not-yet-existing streams linter)**

Run the per-section fixture linters to confirm no regression:

```bash
python3 tools/check_garden_fixtures.py
python3 tools/check_works_fixtures.py
python3 tools/check_research_fixtures.py
python3 tools/check_fixtures.py
```

All four should print their OK message. (No streams linter exists yet — Phase 3.)

- [ ] **Step 5: Re-run filter-chips linter — should now PASS**

Run: `python3 tools/check_filter_chips_config.py`
Expected: all-pass message. (The two fixtures together cover `example`, `prototype`, `lyric` tags.)

- [ ] **Step 6: Commit**

```bash
git add content/streams/ data/filter-chips.yaml
git commit -m "fixture(streams): seed _index + two stream fixtures + filter-chips block

- archived fixture refs game + research-question + garden note (Task 11 wires back-edges)
- removed fixture refs music + poem + essay (Task 11 wires back-edges)
- filter-chips.yaml: streams.primary_tags = [example, prototype, lyric]
  — all three are covered by the two fixtures so the linter passes.

Round-trip symmetry will be enforced by check_streams_links (Task 13)
once back-edge source_stream: fields are added in Task 11.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Three `data/streams-*.yaml` files (seed in not-live / empty state)

**Files:**
- Create: `data/streams-schedule.yaml`
- Create: `data/streams-twitch-cache.yaml`
- Create: `data/streams-live.yaml`

- [ ] **Step 1: Write `data/streams-schedule.yaml`**

This is user-authored. Seed with two example upcoming entries so the homepage strip + `/streams/` upcoming section have something to render in fixtures.

```yaml
# User-authored upcoming streams. The cron Action never modifies this file.
# Schema: per-entry { title, date (RFC3339), duration_estimate (min),
#                     platforms ([twitch|youtube]+), category, summary?, tags? }
# Sorted by date asc. Past entries (date < now) are filtered out at render.
upcoming:
  - title: "Example upcoming game-dev session"
    date: 2027-01-15T19:00:00-04:00
    duration_estimate: 120
    platforms: [twitch, youtube]
    category: game-dev
    summary: "Lorem ipsum example summary for a scheduled stream."
    tags: [example, prototype]
  - title: "Example upcoming research reading"
    date: 2027-02-03T20:00:00-04:00
    duration_estimate: 90
    platforms: [twitch, youtube]
    category: research
    summary: "Lorem ipsum example summary for a research stream."
    tags: [example]
```

(Dates are far enough in the future that `where … "date" "ge" now` keeps both visible until 2027.)

- [ ] **Step 2: Write `data/streams-twitch-cache.yaml`**

Action-authored fallback for entries not in the manual schedule. Seed empty.

```yaml
# Auto-populated by tools/poll_streams.py hourly from Twitch /helix/schedule.
# Same schema as streams-schedule.yaml. Manual schedule wins on date+title key.
upcoming: []
```

- [ ] **Step 3: Write `data/streams-live.yaml`**

Action-authored live state. Seed not-live.

```yaml
# Action-authored. Rewritten on every poll (~5 min cadence).
# When this file is missing entirely, the live-pill partial emits nothing.
last_polled: 2026-05-19T00:00:00Z
live:
  twitch:
    is_live: false
    title: ""
    started_at: ""
    url: ""
  youtube:
    is_live: false
    video_id: ""
    title: ""
    started_at: ""
    url: ""
```

- [ ] **Step 4: Commit**

```bash
git add data/streams-schedule.yaml data/streams-twitch-cache.yaml data/streams-live.yaml
git commit -m "data(streams): seed schedule + twitch-cache + live (not-live state)

- streams-schedule.yaml: 2 future-dated example entries (user-authored)
- streams-twitch-cache.yaml: empty (Action-populated)
- streams-live.yaml: not-live (Action overwrites every poll)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: Add `source_stream:` back-edges to existing fixtures (bidirectional round-trip)

The streams fixtures forward-reference these slugs in their `related_*:` arrays. The bidirectional symmetry linter (Task 13) requires each referenced page to carry `source_stream: <stream-slug>` back-edge. Wire it now.

**Files (all existing fixtures):**
- Modify: `content/essays/example-essay-one/index.md`
- Modify: `content/garden/story-atoms/index.md`
- Modify: `content/works/games/example-playable-full-release/index.md`
- Modify: `content/works/music/example-live-session/index.md`
- Modify: `content/works/poetry/example-poem-collected/index.md`
- Modify: `content/research/questions/what-is-a-narrative-atom/index.md`

(No theme back-edge for now — the music-jam stream's `related_research` is empty, so no theme back-edge needed yet. The `memory-and-play` theme example in research-fixture tests was illustrative only.)

- [ ] **Step 1: Add to essay**

In `content/essays/example-essay-one/index.md` frontmatter, add a `source_stream:` line — wherever in the frontmatter is fine (essay frontmatter is open-set). Suggested placement: after the last `has_*:` field:

```yaml
source_stream: 2026-04-22-example-music-jam-stream
```

- [ ] **Step 2: Add to garden note**

In `content/garden/story-atoms/index.md` frontmatter, add:

```yaml
source_stream: 2026-04-10-example-live-coding-stream
```

- [ ] **Step 3: Add to game**

In `content/works/games/example-playable-full-release/index.md` frontmatter, add:

```yaml
source_stream: 2026-04-10-example-live-coding-stream
```

- [ ] **Step 4: Add to music**

In `content/works/music/example-live-session/index.md` frontmatter, add:

```yaml
source_stream: 2026-04-22-example-music-jam-stream
```

- [ ] **Step 5: Add to poem**

In `content/works/poetry/example-poem-collected/index.md` frontmatter, add:

```yaml
source_stream: 2026-04-22-example-music-jam-stream
```

- [ ] **Step 6: Add to research question**

In `content/research/questions/what-is-a-narrative-atom/index.md` frontmatter, add:

```yaml
source_stream: 2026-04-10-example-live-coding-stream
```

- [ ] **Step 7: Smoke check — every per-section fixture linter still passes**

```bash
python3 tools/check_fixtures.py
python3 tools/check_garden_fixtures.py
python3 tools/check_works_fixtures.py
python3 tools/check_research_fixtures.py
```

All four → OK.

- [ ] **Step 8: Commit**

```bash
git add content/
git commit -m "fixture(round-trip): add source_stream back-edges for streams round-trip

6 fixtures gain source_stream: pointing at one of the two stream fixtures.
Mirrors the related_*: forward edges set in Task 9. The bidirectional
linter (Task 13) enforces symmetry once it exists.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

# Phase 3 — New linter pairs (22nd + 23rd)

## Task 12: `check_streams_fixtures.py` + test sibling (22nd linter pair)

**Files:**
- Create: `tools/check_streams_fixtures.py`
- Create: `tools/test_check_streams_fixtures.py`

- [ ] **Step 1: Write the failing test file FIRST**

Create `tools/test_check_streams_fixtures.py`:

```python
"""Tests for check_streams_fixtures.py — run with:
   python3 -m unittest tools/test_check_streams_fixtures.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_streams_fixtures as lint  # noqa: E402


VALID = """\
---
title: "Example stream"
date: 2026-04-10T19:00:00-04:00
platforms: [twitch, youtube]
category: coding
archive_status: archived
vod_url: "https://www.youtube.com/watch?v=abc"
draft: false
---

Body.
"""


class StreamsFixturesLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.streams = self.tmp / "content" / "streams"
        self.streams.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, slug: str, body: str) -> Path:
        d = self.streams / slug
        d.mkdir()
        p = d / "index.md"
        p.write_text(body)
        return p

    def test_valid_passes(self):
        p = self._write("2026-04-10-ex", VALID)
        self.assertEqual(lint.lint_file(p), [])

    def test_missing_title(self):
        body = VALID.replace('title: "Example stream"\n', "")
        p = self._write("missing-title", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'title'" in e for e in errs))

    def test_missing_date(self):
        body = VALID.replace("date: 2026-04-10T19:00:00-04:00\n", "")
        p = self._write("missing-date", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'date'" in e for e in errs))

    def test_missing_platforms(self):
        body = VALID.replace("platforms: [twitch, youtube]\n", "")
        p = self._write("missing-platforms", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'platforms'" in e for e in errs))

    def test_missing_category(self):
        body = VALID.replace("category: coding\n", "")
        p = self._write("missing-category", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'category'" in e for e in errs))

    def test_missing_archive_status(self):
        body = VALID.replace("archive_status: archived\n", "")
        p = self._write("missing-archive-status", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'archive_status'" in e for e in errs))

    def test_missing_draft(self):
        body = VALID.replace("draft: false\n", "")
        p = self._write("missing-draft", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'draft'" in e for e in errs))

    def test_bad_archive_status_enum(self):
        body = VALID.replace("archive_status: archived", "archive_status: pending")
        p = self._write("bad-status", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("archive_status='pending'" in e for e in errs))

    def test_bad_category_enum(self):
        body = VALID.replace("category: coding", "category: news")
        p = self._write("bad-category", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("category='news'" in e for e in errs))

    def test_platform_not_in_enum(self):
        body = VALID.replace("platforms: [twitch, youtube]", "platforms: [twitch, kick]")
        p = self._write("bad-platform", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("platforms[1]='kick'" in e for e in errs))

    def test_platforms_not_a_list(self):
        body = VALID.replace("platforms: [twitch, youtube]", "platforms: twitch")
        p = self._write("platforms-not-list", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("platforms must be a list" in e for e in errs))

    def test_archived_requires_vod_url(self):
        body = VALID.replace('vod_url: "https://www.youtube.com/watch?v=abc"\n', 'vod_url: ""\n')
        p = self._write("archived-no-vod", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("archive_status=archived requires non-empty vod_url" in e for e in errs))

    def test_removed_allows_empty_vod(self):
        body = VALID.replace("archive_status: archived", "archive_status: removed")
        body = body.replace('vod_url: "https://www.youtube.com/watch?v=abc"\n', 'vod_url: ""\n')
        p = self._write("removed-no-vod", body)
        self.assertEqual(lint.lint_file(p), [])

    def test_unknown_field(self):
        body = VALID.replace("draft: false\n", "draft: false\nrarity: 99\n")
        p = self._write("extra-field", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("unknown field 'rarity'" in e for e in errs))

    def test_with_all_optionals(self):
        body = """\
---
title: "Full Stream"
date: 2026-04-10T19:00:00-04:00
duration: "2h 15m"
platforms: [twitch, youtube]
vod_url: "https://www.youtube.com/watch?v=abc"
twitch_archive_url: "https://twitch.tv/videos/123"
archive_url: "https://archive.org/details/abc"
archive_status: archived
category: research
tags: [example, research-reading]
summary: "Summary."
related_essays: [example-essay-one]
related_garden: [story-atoms]
related_research: [what-is-a-narrative-atom]
related_works: [example-playable-full-release]
draft: false
---

Body.
"""
        p = self._write("full", body)
        self.assertEqual(lint.lint_file(p), [])

    def test_runner_walks_streams_dir(self):
        self._write("a", VALID)
        self._write("b", VALID)
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(errs, [])

    def test_runner_aggregates_errors(self):
        bad = VALID.replace("category: coding", "category: news")
        self._write("ok", VALID)
        self._write("bad", bad)
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(len(errs) >= 1)

    def test_data_yaml_streams_live_shape(self):
        # data/streams-live.yaml must have last_polled + live.{twitch,youtube} with is_live bool.
        (self.tmp / "data").mkdir()
        (self.tmp / "data" / "streams-live.yaml").write_text(
            "last_polled: 2026-05-19T00:00:00Z\n"
            "live:\n"
            "  twitch:\n"
            "    is_live: false\n"
            "    title: \"\"\n"
            "    started_at: \"\"\n"
            "    url: \"\"\n"
            "  youtube:\n"
            "    is_live: false\n"
            "    video_id: \"\"\n"
            "    title: \"\"\n"
            "    started_at: \"\"\n"
            "    url: \"\"\n"
        )
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_data_yaml_streams_live_missing_keys(self):
        (self.tmp / "data").mkdir()
        (self.tmp / "data" / "streams-live.yaml").write_text("foo: bar\n")
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("streams-live.yaml" in e and "live" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail (import error)**

Run: `python3 -m unittest tools/test_check_streams_fixtures.py -v 2>&1 | tail -5`
Expected: `ModuleNotFoundError: No module named 'check_streams_fixtures'`.

- [ ] **Step 3: Write the minimal linter**

Create `tools/check_streams_fixtures.py`:

```python
#!/usr/bin/env python3
"""Streams fixture frontmatter + data-yaml shape linter.

Walks `content/streams/<slug>/index.md` and validates per-stream
frontmatter against spec 2026-05-13-streams-section-design.md §4
+ §9. Also validates the three data/streams-*.yaml files (shape only;
content is Action-authored or user-seeded).

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

# --- contract ---

REQUIRED = {"title", "date", "platforms", "category", "archive_status", "draft"}
OPTIONAL = {
    "duration", "vod_url", "twitch_archive_url", "archive_url",
    "tags", "summary",
    "related_essays", "related_garden", "related_research", "related_works",
}
FIELDS = REQUIRED | OPTIONAL

PLATFORM_VALUES = {"twitch", "youtube"}
CATEGORY_VALUES = {"game-dev", "research", "coding", "creative"}
ARCHIVE_STATUS_VALUES = {"live", "archived", "removed", "private"}


def lint_file(md: Path) -> list[str]:
    errs: list[str] = []
    if not md.exists():
        return [f"{md}: file does not exist"]
    text = md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md}: no frontmatter"]

    for f in sorted(REQUIRED - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - FIELDS):
        errs.append(f"{md}: unknown field '{f}'")

    # platforms: must be a list, each value in PLATFORM_VALUES
    platforms = fm.get("platforms")
    if platforms is not None:
        if not isinstance(platforms, list):
            errs.append(f"{md}: platforms must be a list")
        else:
            for i, p in enumerate(platforms):
                if str(p) not in PLATFORM_VALUES:
                    errs.append(f"{md}: platforms[{i}]='{p}' not in {sorted(PLATFORM_VALUES)}")

    cat = fm.get("category")
    if cat is not None and cat not in CATEGORY_VALUES:
        errs.append(f"{md}: category='{cat}' not in {sorted(CATEGORY_VALUES)}")

    arc = fm.get("archive_status")
    if arc is not None and arc not in ARCHIVE_STATUS_VALUES:
        errs.append(f"{md}: archive_status='{arc}' not in {sorted(ARCHIVE_STATUS_VALUES)}")

    # cross-validation: archived requires non-empty vod_url
    if arc == "archived":
        vod = fm.get("vod_url") or ""
        if not str(vod).strip():
            errs.append(f"{md}: archive_status=archived requires non-empty vod_url")

    # Related-* must be lists of strings when present
    for rel_field in ("related_essays", "related_garden", "related_research", "related_works"):
        v = fm.get(rel_field)
        if v is not None and not isinstance(v, list):
            errs.append(f"{md}: {rel_field} must be a list")

    # tags must be a list of strings when present
    tags = fm.get("tags")
    if tags is not None and not isinstance(tags, list):
        errs.append(f"{md}: tags must be a list")

    return errs


def _validate_data_yaml(repo_root: Path) -> list[str]:
    """Shape-check the three data/streams-*.yaml files (when present)."""
    errs: list[str] = []
    data = repo_root / "data"
    if not data.exists():
        return errs

    live = data / "streams-live.yaml"
    if live.exists():
        text = live.read_text()
        # Naive top-key presence check — stdlib only, no YAML parser.
        if "live:" not in text:
            errs.append(f"data/streams-live.yaml: missing top-level 'live:' key")
        else:
            for sub in ("twitch:", "youtube:"):
                if sub not in text:
                    errs.append(f"data/streams-live.yaml: missing 'live.{sub.rstrip(':')}' block")
            if "is_live:" not in text:
                errs.append(f"data/streams-live.yaml: missing 'is_live' key under live.<platform>")

    sched = data / "streams-schedule.yaml"
    if sched.exists():
        if "upcoming:" not in sched.read_text():
            errs.append(f"data/streams-schedule.yaml: missing 'upcoming:' top-level key")

    cache = data / "streams-twitch-cache.yaml"
    if cache.exists():
        if "upcoming:" not in cache.read_text():
            errs.append(f"data/streams-twitch-cache.yaml: missing 'upcoming:' top-level key")

    return errs


def run(repo_root: Path) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    streams = repo_root / "content" / "streams"
    if streams.exists():
        for child in sorted(streams.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            if not md.exists():
                continue
            all_errs.extend(lint_file(md))
    all_errs.extend(_validate_data_yaml(repo_root))
    return (1 if all_errs else 0), all_errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_streams_fixtures: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tools/test_check_streams_fixtures.py -v 2>&1 | tail -10`
Expected: all 18 tests pass.

- [ ] **Step 5: Smoke-run on the real tree**

Run: `python3 tools/check_streams_fixtures.py`
Expected: `check_streams_fixtures: OK` (both seeded fixtures + 3 data yamls all pass).

- [ ] **Step 6: Commit**

```bash
git add tools/check_streams_fixtures.py tools/test_check_streams_fixtures.py
git commit -m "lint(streams): 22nd linter pair — check_streams_fixtures

Per-stream frontmatter contract per spec §4 + §9:
- Required: title/date/platforms/category/archive_status/draft.
- Enums: platforms ⊆ {twitch,youtube}; category, archive_status.
- Cross-val: archived ⇒ vod_url non-empty.
- Data-yaml shape: streams-live.yaml has live.{twitch,youtube}.is_live;
  schedule + twitch-cache have upcoming top key.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: `check_streams_links.py` + test sibling (23rd linter pair — bidirectional symmetry)

Mirrors `check_works_links.py`. For each stream `X.related_<sec>: [Y, ...]`: `Y` must exist (non-draft) and `Y.source_stream == X`. And inversely, for each page with `source_stream: X`: `X` must exist (non-draft) and `X.related_<sec>` must include this page's slug.

**Files:**
- Create: `tools/check_streams_links.py`
- Create: `tools/test_check_streams_links.py`

- [ ] **Step 1: Write the failing test file FIRST**

Create `tools/test_check_streams_links.py`:

```python
"""Tests for check_streams_links.py — run with:
   python3 -m unittest tools/test_check_streams_links.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_streams_links as lint  # noqa: E402


def _md(fm: dict) -> str:
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append("Body.")
    return "\n".join(lines) + "\n"


class StreamsLinksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.content = self.tmp / "content"
        for path in [
            "streams", "essays", "garden",
            "research/themes", "research/questions",
            "works/games", "works/music", "works/poetry",
        ]:
            (self.content / path).mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, rel: str, fm: dict) -> Path:
        d = self.content / rel
        d.mkdir(parents=True, exist_ok=True)
        p = d / "index.md"
        p.write_text(_md(fm))
        return p

    def test_symmetric_passes(self):
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["example-essay-one"],
        })
        self._write("essays/example-essay-one", {
            "title": "E1", "date": "2026-01-01", "draft": "false",
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_forward_edge_dangling(self):
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["nonexistent-essay"],
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("nonexistent-essay" in e for e in errs))

    def test_forward_edge_to_draft_fails(self):
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["draft-essay"],
        })
        self._write("essays/draft-essay", {
            "title": "D", "date": "2026-01-01", "draft": "true",
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("draft" in e.lower() for e in errs))

    def test_asymmetric_forward_only_fails(self):
        # Stream points at essay, but essay does NOT point back.
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["example-essay-one"],
        })
        self._write("essays/example-essay-one", {
            "title": "E1", "date": "2026-01-01", "draft": "false",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("asymmetric" in e.lower() or "source_stream" in e for e in errs))

    def test_back_edge_dangling_stream(self):
        # Essay has source_stream pointing at a stream that doesn't exist.
        self._write("essays/example-essay-one", {
            "title": "E1", "date": "2026-01-01", "draft": "false",
            "source_stream": "2026-04-10-nonexistent",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("2026-04-10-nonexistent" in e for e in errs))

    def test_back_edge_present_but_stream_doesnt_list_us(self):
        # Stream exists, essay points back, but stream's related_essays does NOT include the essay.
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["some-other-essay"],
        })
        self._write("essays/some-other-essay", {
            "title": "Other", "date": "2026-01-01", "draft": "false",
            "source_stream": "2026-04-10-s1",
        })
        self._write("essays/example-essay-one", {
            "title": "E1", "date": "2026-01-01", "draft": "false",
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("example-essay-one" in e and "related_essays" in e for e in errs))

    def test_all_four_back_edges(self):
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "coding",
            "archive_status": "archived", "vod_url": "x",
            "related_essays": ["e1"],
            "related_garden": ["g1"],
            "related_research": ["q1"],
            "related_works": ["w1"],
        })
        self._write("essays/e1", {"title": "E1", "date": "2026-01-01", "draft": "false", "source_stream": "2026-04-10-s1"})
        self._write("garden/g1", {"title": "G1", "draft": "false", "last_modified": "2026-01-01", "growth_stage": "budding", "source_stream": "2026-04-10-s1"})
        self._write("research/questions/q1", {"title": "Q1", "theme": "x", "status": "active", "last_modified": "2026-01-01", "description": "d", "source_stream": "2026-04-10-s1"})
        self._write("works/games/w1", {
            "title": "W1", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "status": "playable", "game_kind": "full-release",
            "tagline": "t", "year": 2026,
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_related_works_resolves_across_three_sub_sections(self):
        # related_works slug can resolve under games/, music/, OR poetry/.
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "creative",
            "archive_status": "archived", "vod_url": "x",
            "related_works": ["m1", "p1"],
        })
        self._write("works/music/m1", {
            "title": "M1", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "format": "track", "year": 2026,
            "source_stream": "2026-04-10-s1",
        })
        self._write("works/poetry/p1", {
            "title": "P1", "date": "2026-01-01", "lastmod": "2026-01-02",
            "draft": "false", "lines": 8,
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_research_back_edge_can_be_theme(self):
        self._write("streams/2026-04-10-s1", {
            "title": "S1", "date": "2026-04-10", "draft": "false",
            "platforms": ["twitch"], "category": "research",
            "archive_status": "archived", "vod_url": "x",
            "related_research": ["t1"],
        })
        self._write("research/themes/t1", {
            "title": "T1", "status": "active", "tags": "[memory]",
            "last_modified": "2026-01-01", "description": "d", "weight": 10,
            "source_stream": "2026-04-10-s1",
        })
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_empty_tree_passes(self):
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail (import error)**

Run: `python3 -m unittest tools/test_check_streams_links.py -v 2>&1 | tail -5`
Expected: `ModuleNotFoundError: No module named 'check_streams_links'`.

- [ ] **Step 3: Write the linter**

Create `tools/check_streams_links.py`:

```python
#!/usr/bin/env python3
"""Streams bidirectional cross-reference linter.

For each stream X in content/streams/:
  - X.related_essays:  [...] → each must exist (non-draft) under content/essays/
                              AND that page's source_stream must equal X's slug.
  - X.related_garden:  [...] → likewise under content/garden/.
  - X.related_research:[...] → likewise under content/research/{themes,questions}/.
  - X.related_works:   [...] → likewise under content/works/{games,music,poetry}/.

Inverse: for each page (essays/garden/research/works) with source_stream: X:
  - X must exist (non-draft) under content/streams/.
  - X.related_<sec> must include the page's slug (the directory name).

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


SECTIONS = {
    "essays":   "related_essays",
    "garden":   "related_garden",
    "research": "related_research",
    "works":    "related_works",
}

# Where each section's leaf pages live (sub-dirs are searched in order).
SECTION_LEAVES: dict[str, list[Path]] = {}  # filled per run


def _load_fm(md: Path) -> dict | None:
    if not md.exists():
        return None
    return parse_frontmatter(md.read_text())


def _scan_dir_fms(d: Path) -> dict[str, dict]:
    """Return {slug: fm} for each child dir of d that has an index.md."""
    out: dict[str, dict] = {}
    if not d.exists():
        return out
    for child in sorted(d.iterdir()):
        if not child.is_dir():
            continue
        md = child / "index.md"
        fm = _load_fm(md)
        if fm is not None:
            out[child.name] = fm
    return out


def _is_draft(fm: dict) -> bool:
    v = fm.get("draft")
    return str(v).strip().lower() == "true"


def lint_cross_refs(content_root: Path) -> list[str]:
    errs: list[str] = []

    streams_fms = _scan_dir_fms(content_root / "streams")
    essays_fms  = _scan_dir_fms(content_root / "essays")
    garden_fms  = _scan_dir_fms(content_root / "garden")
    themes_fms  = _scan_dir_fms(content_root / "research" / "themes")
    qs_fms      = _scan_dir_fms(content_root / "research" / "questions")
    games_fms   = _scan_dir_fms(content_root / "works" / "games")
    music_fms   = _scan_dir_fms(content_root / "works" / "music")
    poetry_fms  = _scan_dir_fms(content_root / "works" / "poetry")

    # Per-section lookup: slug → (fm, source_dir_name)
    research_combined: dict[str, dict] = {}
    research_combined.update(themes_fms)
    research_combined.update(qs_fms)
    works_combined: dict[str, dict] = {}
    works_combined.update(games_fms)
    works_combined.update(music_fms)
    works_combined.update(poetry_fms)

    section_fms = {
        "essays":   essays_fms,
        "garden":   garden_fms,
        "research": research_combined,
        "works":    works_combined,
    }

    # Forward edges: streams → other sections
    for stream_slug, sfm in streams_fms.items():
        if _is_draft(sfm):
            continue
        for sec, field in SECTIONS.items():
            refs = sfm.get(field)
            if not refs:
                continue
            if not isinstance(refs, list):
                continue
            target_map = section_fms[sec]
            for ref in refs:
                ref_str = str(ref)
                target_fm = target_map.get(ref_str)
                if target_fm is None:
                    errs.append(
                        f"streams/{stream_slug}: {field} ref '{ref_str}' "
                        f"does not resolve to any page in /{sec}/"
                    )
                    continue
                if _is_draft(target_fm):
                    errs.append(
                        f"streams/{stream_slug}: {field} ref '{ref_str}' targets a draft page"
                    )
                    continue
                back = target_fm.get("source_stream")
                if str(back) != stream_slug:
                    errs.append(
                        f"streams/{stream_slug}: asymmetric — {sec}/{ref_str} "
                        f"has source_stream='{back}' but should be '{stream_slug}'"
                    )

    # Back edges: any-section.source_stream → streams
    for sec, fms in section_fms.items():
        field = SECTIONS[sec]
        for slug, fm in fms.items():
            back = fm.get("source_stream")
            if not back:
                continue
            back_str = str(back)
            sfm = streams_fms.get(back_str)
            if sfm is None:
                errs.append(
                    f"{sec}/{slug}: source_stream='{back_str}' "
                    f"does not resolve to any stream in /streams/"
                )
                continue
            if _is_draft(sfm):
                errs.append(
                    f"{sec}/{slug}: source_stream='{back_str}' targets a draft stream"
                )
                continue
            forward = sfm.get(field) or []
            if not isinstance(forward, list) or slug not in [str(x) for x in forward]:
                errs.append(
                    f"{sec}/{slug}: source_stream='{back_str}' "
                    f"but streams/{back_str}.{field} does not include '{slug}'"
                )

    return errs


def run(repo_root: Path) -> tuple[int, list[str]]:
    content_root = repo_root / "content"
    if not content_root.exists():
        return 0, []
    errs = lint_cross_refs(content_root)
    return (1 if errs else 0), errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_streams_links: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tools/test_check_streams_links.py -v 2>&1 | tail -10`
Expected: all 10 tests pass.

- [ ] **Step 5: Smoke-run on the real tree (validates Phase 2 round-trip)**

Run: `python3 tools/check_streams_links.py`
Expected: `check_streams_links: OK`. (The 6 fixtures wired in Task 11 + 2 streams in Task 9 round-trip cleanly.)

- [ ] **Step 6: Commit**

```bash
git add tools/check_streams_links.py tools/test_check_streams_links.py
git commit -m "lint(streams): 23rd linter pair — check_streams_links bidirectional

Forward (streams.related_<sec> → page) AND back (page.source_stream
→ stream) edges checked with full symmetry. Mirrors check_works_links
shape (lyrics_poem ↔ set_to_music). Real-tree round-trip from Task 11
fixtures passes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 14: Register both linter pairs in `.github/workflows/hugo.yaml` + `tools/ci-local.sh`

**Files:**
- Modify: `.github/workflows/hugo.yaml`
- Modify: `tools/ci-local.sh`

- [ ] **Step 1: Insert into `.github/workflows/hugo.yaml`**

Find the block:

```yaml
      - name: Verify garden history
        run: python3 tools/check_garden_history.py
      - name: Run garden history linter unit tests
        run: python3 -m unittest tools/test_check_garden_history.py -v
      - name: Verify graph-chrome consistency
        run: python3 tools/check_graph_chrome.py
```

Replace with (insert two pairs before the `Verify graph-chrome consistency` step):

```yaml
      - name: Verify garden history
        run: python3 tools/check_garden_history.py
      - name: Run garden history linter unit tests
        run: python3 -m unittest tools/test_check_garden_history.py -v
      - name: Verify streams fixtures
        run: python3 tools/check_streams_fixtures.py
      - name: Run streams fixture linter unit tests
        run: python3 -m unittest tools/test_check_streams_fixtures.py -v
      - name: Verify streams links
        run: python3 tools/check_streams_links.py
      - name: Run streams links linter unit tests
        run: python3 -m unittest tools/test_check_streams_links.py -v
      - name: Verify graph-chrome consistency
        run: python3 tools/check_graph_chrome.py
```

- [ ] **Step 2: Insert into `tools/ci-local.sh`**

Find the block:

```bash
python3 tools/check_garden_history.py
python3 -m unittest tools/test_check_garden_history.py -v 2>&1 | tail -3

python3 tools/check_graph_chrome.py
```

Replace with:

```bash
python3 tools/check_garden_history.py
python3 -m unittest tools/test_check_garden_history.py -v 2>&1 | tail -3

python3 tools/check_streams_fixtures.py
python3 -m unittest tools/test_check_streams_fixtures.py -v 2>&1 | tail -3

python3 tools/check_streams_links.py
python3 -m unittest tools/test_check_streams_links.py -v 2>&1 | tail -3

python3 tools/check_graph_chrome.py
```

- [ ] **Step 3: Verify by running the relevant local pre-build linter stretch**

Run, expecting all-OK:

```bash
python3 tools/check_streams_fixtures.py && \
python3 -m unittest tools/test_check_streams_fixtures.py -v 2>&1 | tail -3 && \
python3 tools/check_streams_links.py && \
python3 -m unittest tools/test_check_streams_links.py -v 2>&1 | tail -3
```

Expected: all four pass.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/hugo.yaml tools/ci-local.sh
git commit -m "ci: register streams linter pairs (22nd + 23rd) in workflow + ci-local

Inserted before check_graph_chrome (the lone sibling-less linter) in
both the hugo.yaml pre-build block and ci-local.sh. Pre-build linter
step count: 44 → 48 (contrast + 23 pairs + 1 sibling-less).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

# Phase 4 — Citation integration

## Task 15: `normalize-page.html` — streams branch

Spec §10: BibTeX type=`misc`; note=`"Live stream broadcast, <start-date>, archived on YouTube"` (or `"...archive intentionally removed"` when `archive_status == "removed"`); `pub_date`/`online_date` from `.Date`.

**Files:**
- Modify: `layouts/partials/cite/normalize-page.html`

- [ ] **Step 1: Edit the type-map block**

In `layouts/partials/cite/normalize-page.html`, find:

```hugo
{{- /* Type map by section. */ -}}
{{- $type := "misc" -}}
{{- if eq .Section "essays" -}}{{- $type = "article" -}}
{{- else if eq .Section "research" -}}{{- $type = "online" -}}
{{- end -}}
```

Replace with:

```hugo
{{- /* Type map by section. */ -}}
{{- $type := "misc" -}}
{{- if eq .Section "essays" -}}{{- $type = "article" -}}
{{- else if eq .Section "research" -}}{{- $type = "online" -}}
{{- else if eq .Section "streams" -}}{{- $type = "misc" -}}
{{- end -}}
```

(Streams = `misc` is already the default; keeping the explicit branch documents intent + provides a stable hook for future per-section tweaks.)

- [ ] **Step 2: Add the streams note branch**

Below the existing poetry-note branch, append the streams branch. Find:

```hugo
{{- /* Synced poetry with a recorded reading — flag the audio performance. */ -}}
{{- if and (eq .Section "works") (eq .Type "works-poetry") .Params.audio_url -}}
  {{- $note = "With audio reading." -}}
{{- end -}}
```

Append immediately after:

```hugo
{{- /* Streams: per-archive status note. */ -}}
{{- if eq .Section "streams" -}}
  {{- $arc := .Params.archive_status | default "archived" -}}
  {{- $startDate := .Date.Format "2006-01-02" -}}
  {{- if eq $arc "removed" -}}
    {{- $note = printf "Live stream broadcast, %s, archive intentionally removed" $startDate -}}
  {{- else -}}
    {{- $note = printf "Live stream broadcast, %s, archived on YouTube" $startDate -}}
  {{- end -}}
{{- end -}}
```

- [ ] **Step 3: User-verify by running their dev server (agent cannot)**

ASK USER: "Restart your `hugo server --buildDrafts`. Open `/streams/2026-04-10-example-live-coding-stream/`. Open the cite modal (Cite this stream button — added in Task 16) — wait, the button label isn't added yet; postpone visual verification to after Task 16."

Note for the executor: this is a pure render-side change that fixture-verifies at build time. Hugo will error on parse failures; runtime correctness verifies after Task 16.

- [ ] **Step 4: Commit**

```bash
git add layouts/partials/cite/normalize-page.html
git commit -m "cite(streams): per-archive_status note + explicit misc type

Spec §10. Renders 'Live stream broadcast, <YYYY-MM-DD>, archived on
YouTube' or '...archive intentionally removed' (when removed). The
explicit streams branch in the type map documents intent (misc is the
default anyway).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 16: `button.html` + `static-fallback.html` — "Cite this stream" label

Both files contain identical label-resolution blocks. Add streams branch to each.

**Files:**
- Modify: `layouts/partials/cite/button.html`
- Modify: `layouts/partials/cite/static-fallback.html`

- [ ] **Step 1: Edit `button.html`**

In `layouts/partials/cite/button.html`, find:

```hugo
{{- else if eq .Section "works" -}}
  {{- if eq .Type "works-games" -}}{{- $label = "Cite this game" -}}
  {{- else if eq .Type "works-music" -}}{{- $label = "Cite this release" -}}
  {{- else if eq .Type "works-poetry" -}}{{- $label = "Cite this poem" -}}
  {{- end -}}
{{- end -}}
```

Replace with (insert streams branch before the closing `{{- end -}}`):

```hugo
{{- else if eq .Section "works" -}}
  {{- if eq .Type "works-games" -}}{{- $label = "Cite this game" -}}
  {{- else if eq .Type "works-music" -}}{{- $label = "Cite this release" -}}
  {{- else if eq .Type "works-poetry" -}}{{- $label = "Cite this poem" -}}
  {{- end -}}
{{- else if eq .Section "streams" -}}
  {{- $label = "Cite this stream" -}}
{{- end -}}
```

- [ ] **Step 2: Edit `static-fallback.html`**

In `layouts/partials/cite/static-fallback.html`, apply the same patch — the identical label block exists there:

```hugo
{{- else if eq .Section "works" -}}
  {{- if eq .Type "works-games" -}}{{- $label = "Cite this game" -}}
  {{- else if eq .Type "works-music" -}}{{- $label = "Cite this release" -}}
  {{- else if eq .Type "works-poetry" -}}{{- $label = "Cite this poem" -}}
  {{- end -}}
{{- end -}}
```

→

```hugo
{{- else if eq .Section "works" -}}
  {{- if eq .Type "works-games" -}}{{- $label = "Cite this game" -}}
  {{- else if eq .Type "works-music" -}}{{- $label = "Cite this release" -}}
  {{- else if eq .Type "works-poetry" -}}{{- $label = "Cite this poem" -}}
  {{- end -}}
{{- else if eq .Section "streams" -}}
  {{- $label = "Cite this stream" -}}
{{- end -}}
```

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/cite/button.html layouts/partials/cite/static-fallback.html
git commit -m "cite(streams): \"Cite this stream\" label (button + static-fallback)

Both files duplicate the label-resolution chain; matching tweak to keep
no-JS fallback heading + visible CTA in sync.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 17: Citable predicate triplet — add `"streams"` + `archive_status` gate

Spec §10 + spec §0 reconciliation. Three files emit the predicate verbatim; all three must update.

**Files:**
- Modify: `layouts/_default/baseof.html`
- Modify: `layouts/partials/head.html`
- Modify: `layouts/partials/scripts.html`

- [ ] **Step 1: Edit `baseof.html`**

In `layouts/_default/baseof.html`, find:

```hugo
{{- $citable_sections := slice "essays" "garden" "research" "works" -}}
{{- $isCitablePage := and (in $citable_sections .Section) (eq .Kind "page") -}}
{{- $isLibraryList := and (eq .Section "library") (ne .RelPermalink "/library/") -}}
{{- if or $isCitablePage $isLibraryList -}}
  {{ partial "cite/modal.html" . }}
{{- end }}
```

Replace with (adds `"streams"` to the slice + an `archive_status` gate for streams):

```hugo
{{- $citable_sections := slice "essays" "garden" "research" "works" "streams" -}}
{{- $isCitablePage := and (in $citable_sections .Section) (eq .Kind "page") -}}
{{- if and $isCitablePage (eq .Section "streams") -}}
  {{- $isCitablePage = in (slice "archived" "removed") .Params.archive_status -}}
{{- end -}}
{{- $isLibraryList := and (eq .Section "library") (ne .RelPermalink "/library/") -}}
{{- if or $isCitablePage $isLibraryList -}}
  {{ partial "cite/modal.html" . }}
{{- end }}
```

- [ ] **Step 2: Edit `head.html`**

In `layouts/partials/head.html`, find:

```hugo
{{- $citable_sections := slice "essays" "garden" "research" "works" -}}
{{- if and (in $citable_sections .Section) (eq .Kind "page") -}}
  {{- partial "cite/meta-tags.html" . }}
```

Replace with:

```hugo
{{- $citable_sections := slice "essays" "garden" "research" "works" "streams" -}}
{{- $isCitablePage := and (in $citable_sections .Section) (eq .Kind "page") -}}
{{- if and $isCitablePage (eq .Section "streams") -}}
  {{- $isCitablePage = in (slice "archived" "removed") .Params.archive_status -}}
{{- end -}}
{{- if $isCitablePage -}}
  {{- partial "cite/meta-tags.html" . }}
```

(Be careful: head.html's existing one-line `if ... -}}` form expands into a multi-line predicate; verify the matching `{{- end -}}` already present in the file still closes the new `{{- if $isCitablePage -}}` — it should.)

- [ ] **Step 3: Edit `scripts.html`**

In `layouts/partials/scripts.html`, find:

```hugo
{{- $citable_sections := slice "essays" "garden" "research" "works" -}}
{{- $isCitablePage := and (in $citable_sections .Section) (eq .Kind "page") -}}
{{- $isLibraryList := and (eq .Section "library") (ne .RelPermalink "/library/") -}}
{{- if or $isCitablePage $isLibraryList }}
```

Replace with:

```hugo
{{- $citable_sections := slice "essays" "garden" "research" "works" "streams" -}}
{{- $isCitablePage := and (in $citable_sections .Section) (eq .Kind "page") -}}
{{- if and $isCitablePage (eq .Section "streams") -}}
  {{- $isCitablePage = in (slice "archived" "removed") .Params.archive_status -}}
{{- end -}}
{{- $isLibraryList := and (eq .Section "library") (ne .RelPermalink "/library/") -}}
{{- if or $isCitablePage $isLibraryList }}
```

- [ ] **Step 4: Commit**

```bash
git add layouts/_default/baseof.html layouts/partials/head.html layouts/partials/scripts.html
git commit -m "cite(streams): triplicated \$citable_sections + archive_status gate

Spec §10. Streams pages emit cite modal + meta-tags + entry-cite.js
ONLY when archive_status ∈ {archived, removed}. live / private
streams emit no cite scaffolding (so check_cite_meta won't audit them).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

# Phase 5 — Streams partials (6 new partials)

## Task 18: `partials/streams/live-pill.html`

**Files:**
- Create: `layouts/partials/streams/live-pill.html`

- [ ] **Step 1: Write the partial**

Create `layouts/partials/streams/live-pill.html`:

```hugo
{{- /* Header live indicator. Reads data/streams-live.yaml and emits a pulsing
       pill linking to whichever platform reports is_live=true (Twitch wins
       when both are live, since the live audience watches there).

       When data/streams-live.yaml is missing entirely (e.g. before the cron
       Action has ever run), `index site.Data "streams-live"` returns nil
       and we emit nothing — never a template error. */ -}}
{{- $live := index site.Data "streams-live" -}}
{{- with $live -}}
  {{- $tw := .live.twitch -}}
  {{- $yt := .live.youtube -}}
  {{- if or $tw.is_live $yt.is_live -}}
    {{- $url := cond $tw.is_live $tw.url $yt.url -}}
    {{- $platform := cond $tw.is_live "Twitch" "YouTube" -}}
    <a class="header-live-pill" href="{{ $url }}" rel="noopener"
       aria-label="Currently live — watch on {{ $platform }}">
      <span class="header-live-pill-dot" aria-hidden="true"></span>
      <span class="header-live-pill-label">LIVE</span>
    </a>
  {{- end -}}
{{- end -}}
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/streams/live-pill.html
git commit -m "streams(partial): live-pill — pulsing header indicator

Reads index site.Data \"streams-live\" (hyphenated-filename gotcha).
Twitch wins on tie; emits nothing when both not-live or yaml missing.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 19: `partials/streams/embed.html`

**Files:**
- Create: `layouts/partials/streams/embed.html`

- [ ] **Step 1: Write the partial**

Create `layouts/partials/streams/embed.html`:

```hugo
{{- /* Click-to-load YouTube embed. Input: dict with .video_id (string).
       Renders a thumbnail + play button; assets/js/streams.js swaps in an
       iframe on click. Privacy-enhanced mode (youtube-nocookie.com) is set
       JS-side, not here. */ -}}
{{- $video_id := .video_id -}}
<div class="yt-embed" data-video-id="{{ $video_id }}">
  <button class="yt-embed-play" type="button"
          aria-label="Load and play YouTube video">
    <img class="yt-embed-thumb" loading="lazy" alt=""
         src="https://i.ytimg.com/vi/{{ $video_id }}/hqdefault.jpg">
    <span class="yt-embed-play-icon" aria-hidden="true">▶</span>
  </button>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/streams/embed.html
git commit -m "streams(partial): embed — click-to-load YouTube placeholder

Renders i.ytimg.com thumbnail + play button; JS in Task 30 mounts the
iframe on click (youtube-nocookie.com origin, autoplay=1).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 20: `partials/streams/cross-refs.html`

**Files:**
- Create: `layouts/partials/streams/cross-refs.html`

- [ ] **Step 1: Write the partial**

Create `layouts/partials/streams/cross-refs.html`:

```hugo
{{- /* Bidirectional related-outputs list, rendered on /streams/<slug>/.
       Input: . is the stream page. Resolves each slug via site.GetPage
       (linter check_streams_links guarantees they all resolve). */ -}}
{{- $page := . -}}
{{- $groups := slice
    (dict "label" "Related essays"   "field" "related_essays"   "base" "/essays/")
    (dict "label" "Related notes"    "field" "related_garden"   "base" "/garden/")
    (dict "label" "Related research" "field" "related_research" "base" "")
    (dict "label" "Related works"    "field" "related_works"    "base" "")
-}}

{{- $anyShown := false -}}
{{- range $groups -}}
  {{- $refs := index $page.Params .field | default slice -}}
  {{- if $refs -}}{{- $anyShown = true -}}{{- end -}}
{{- end -}}

{{- if $anyShown -}}
<section class="streams-cross-refs" aria-labelledby="streams-cross-refs-heading">
  <h2 id="streams-cross-refs-heading">From this stream</h2>
  {{- range $groups -}}
    {{- $refs := index $page.Params .field | default slice -}}
    {{- if $refs -}}
      <div class="streams-cross-refs-group">
        <h3>{{ .label }}</h3>
        <ul>
          {{- $base := .base -}}
          {{- $field := .field -}}
          {{- range $refs -}}
            {{- $slug := . -}}
            {{- $pg := "" -}}
            {{- if eq $field "related_research" -}}
              {{- $pg = site.GetPage (printf "/research/questions/%s/" $slug) -}}
              {{- if not $pg -}}{{- $pg = site.GetPage (printf "/research/themes/%s/" $slug) -}}{{- end -}}
            {{- else if eq $field "related_works" -}}
              {{- $pg = site.GetPage (printf "/works/games/%s/" $slug) -}}
              {{- if not $pg -}}{{- $pg = site.GetPage (printf "/works/music/%s/" $slug) -}}{{- end -}}
              {{- if not $pg -}}{{- $pg = site.GetPage (printf "/works/poetry/%s/" $slug) -}}{{- end -}}
            {{- else -}}
              {{- $pg = site.GetPage (printf "%s%s/" $base $slug) -}}
            {{- end -}}
            {{- with $pg -}}
              <li><a href="{{ .RelPermalink }}">{{ .Title }}</a></li>
            {{- end -}}
          {{- end -}}
        </ul>
      </div>
    {{- end -}}
  {{- end -}}
</section>
{{- end -}}
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/streams/cross-refs.html
git commit -m "streams(partial): cross-refs — render the four related-* lists

Handles related_research's themes-or-questions split + related_works's
games-or-music-or-poetry split (mirrors check_streams_links resolution).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 21: `partials/streams/stream-card.html`

**Files:**
- Create: `layouts/partials/streams/stream-card.html`

- [ ] **Step 1: Write the partial**

Create `layouts/partials/streams/stream-card.html`:

```hugo
{{- /* Archive entry card. Input: . is a stream page. Used on /streams/
       list page; also reusable on the homepage if we ever surface
       archive items there. */ -}}
{{- $cat := .Params.category | default "" -}}
{{- $arc := .Params.archive_status | default "archived" -}}
<article class="stream-card"
         data-category="{{ $cat }}"
         data-archive-status="{{ $arc }}"
         data-tags="{{ delimit (.Params.tags | default slice) " " }}"
         data-year="{{ .Date.Year }}">
  <header class="stream-card-header">
    <a class="stream-card-title" href="{{ .RelPermalink }}">{{ .Title }}</a>
    <p class="stream-card-meta">
      <time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date.Format "Jan 2, 2006" }}</time>
      {{- with .Params.duration }} · <span class="stream-card-duration">{{ . }}</span>{{- end -}}
      · <span class="streams-category-pill streams-category-pill--{{ $cat }}">{{ humanize $cat }}</span>
    </p>
  </header>
  {{- with .Params.summary -}}
    <p class="stream-card-summary">{{ . }}</p>
  {{- end -}}
  {{- /* Output-count summary (essays + garden + research + works). */ -}}
  {{- $counts := slice -}}
  {{- with .Params.related_essays -}}{{- $counts = $counts | append (printf "%d essay%s" (len .) (cond (eq (len .) 1) "" "s")) -}}{{- end -}}
  {{- with .Params.related_garden -}}{{- $counts = $counts | append (printf "%d note%s" (len .) (cond (eq (len .) 1) "" "s")) -}}{{- end -}}
  {{- with .Params.related_research -}}{{- $counts = $counts | append (printf "%d research" (len .)) -}}{{- end -}}
  {{- with .Params.related_works -}}{{- $counts = $counts | append (printf "%d work%s" (len .) (cond (eq (len .) 1) "" "s")) -}}{{- end -}}
  {{- if $counts -}}
    <p class="stream-card-output-counts">Produced: {{ delimit $counts ", " }}</p>
  {{- end -}}
  {{- if eq $arc "removed" -}}
    <p class="stream-card-removed">Archive intentionally removed.</p>
  {{- end -}}
</article>
```

Notes:
- `data-tags` uses space-delimiter (memory `reference_filter_chips_data_tags_space_delimited`).
- Output-count summary is computed inline; no `→` arrows (memory).

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/streams/stream-card.html
git commit -m "streams(partial): stream-card — archive entry card

Includes data-{category,archive-status,tags,year} for filter-chips JS,
output-count summary, and a 'removed' callout. No → arrows (per
feedback_no_arrow_prefix_on_links). data-tags space-delimited.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 22: `partials/streams/upcoming.html`

Implements the schedule merge logic from spec §3 (manual wins; dedup by date+lowercased title), filter past entries.

**Files:**
- Create: `layouts/partials/streams/upcoming.html`

- [ ] **Step 1: Write the partial**

Create `layouts/partials/streams/upcoming.html`:

```hugo
{{- /* Upcoming streams strip. Inputs: dict { limit: int (optional, default 0 = no cap),
       heading: string (optional default "Upcoming streams") }.
       Merge model: manual schedule wins over twitch-cache; dedup key =
       date(YYYY-MM-DD) + lowercased title. Past entries (date < now) dropped.
       Hyphenated data filenames → use `index site.Data "..."`. */ -}}
{{- $args := . -}}
{{- $limit := $args.limit | default 0 -}}
{{- $heading := $args.heading | default "Upcoming streams" -}}

{{- $manualFile := index site.Data "streams-schedule" -}}
{{- $cacheFile  := index site.Data "streams-twitch-cache" -}}
{{- $manual := slice -}}
{{- with $manualFile -}}{{- $manual = .upcoming | default slice -}}{{- end -}}
{{- $cache  := slice -}}
{{- with $cacheFile -}}{{- $cache = .upcoming | default slice -}}{{- end -}}

{{- /* Build the manual-key set: date(YYYY-MM-DD) + lower-title. */ -}}
{{- $manualKeys := dict -}}
{{- range $manual -}}
  {{- $d := .date -}}
  {{- $dateStr := "" -}}
  {{- if (reflect.IsMap $d) -}}{{- $dateStr = (time.AsTime $d).Format "2006-01-02" -}}
  {{- else -}}{{- $dateStr = (printf "%v" $d) | substr 0 10 -}}{{- end -}}
  {{- $k := printf "%s|%s" $dateStr (lower .title) -}}
  {{- $manualKeys = merge $manualKeys (dict $k true) -}}
{{- end -}}

{{- $merged := $manual -}}
{{- range $cache -}}
  {{- $d := .date -}}
  {{- $dateStr := "" -}}
  {{- if (reflect.IsMap $d) -}}{{- $dateStr = (time.AsTime $d).Format "2006-01-02" -}}
  {{- else -}}{{- $dateStr = (printf "%v" $d) | substr 0 10 -}}{{- end -}}
  {{- $k := printf "%s|%s" $dateStr (lower .title) -}}
  {{- if not (index $manualKeys $k) -}}
    {{- $merged = $merged | append . -}}
  {{- end -}}
{{- end -}}

{{- /* Drop past entries + sort by date asc. */ -}}
{{- $nowStr := now.Format "2006-01-02T15:04:05Z07:00" -}}
{{- $future := slice -}}
{{- range $merged -}}
  {{- $dRaw := .date -}}
  {{- $dt := "" -}}
  {{- if (reflect.IsMap $dRaw) -}}{{- $dt = time.AsTime $dRaw -}}
  {{- else -}}{{- $dt = time.AsTime (printf "%v" $dRaw) -}}{{- end -}}
  {{- if not ($dt.Before now) -}}
    {{- $future = $future | append (merge . (dict "_dt" $dt)) -}}
  {{- end -}}
{{- end -}}
{{- $sorted := sort $future "_dt" "asc" -}}
{{- if gt $limit 0 -}}{{- $sorted = first $limit $sorted -}}{{- end -}}

{{- if $sorted -}}
<section class="streams-upcoming" aria-labelledby="streams-upcoming-heading">
  <h2 id="streams-upcoming-heading">{{ $heading }}</h2>
  <ul class="streams-upcoming-list">
    {{- range $sorted -}}
      {{- $cat := .category | default "" -}}
      <li class="streams-upcoming-item" data-category="{{ $cat }}">
        <time datetime="{{ ._dt.Format "2006-01-02T15:04:05Z07:00" }}">{{ ._dt.Format "Mon Jan 2, 3:04 PM" }}</time>
        <span class="streams-upcoming-title">{{ .title }}</span>
        {{- with $cat }} <span class="streams-category-pill streams-category-pill--{{ . }}">{{ humanize . }}</span>{{- end -}}
        {{- with .summary -}}<p class="streams-upcoming-summary">{{ . }}</p>{{- end -}}
        {{- with .platforms -}}
          <p class="streams-upcoming-platforms">on {{ delimit . " + " }}</p>
        {{- end -}}
      </li>
    {{- end -}}
  </ul>
</section>
{{- end -}}
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/streams/upcoming.html
git commit -m "streams(partial): upcoming — manual+cache merge + past-drop + sort

Merge key = date(YYYY-MM-DD)+lower(title). Manual wins. Past entries
dropped via date.Before now. Optional limit. Hyphenated yaml access
via index site.Data \"streams-schedule\".

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 23: `partials/streams/from-stream.html`

Shared attribution block included in 7 cross-section single templates.

**Files:**
- Create: `layouts/partials/streams/from-stream.html`

- [ ] **Step 1: Write the partial**

Create `layouts/partials/streams/from-stream.html`:

```hugo
{{- /* Render the "From the stream: ..." attribution block on any page that
       carries source_stream: <slug>. Resolves via site.GetPage; emits
       nothing when source_stream is absent or the stream page doesn't
       exist (check_streams_links would have caught the latter in CI).
       Input: . is the host page. */ -}}
{{- with .Params.source_stream -}}
  {{- $stream := site.GetPage (printf "/streams/%s/" .) -}}
  {{- with $stream -}}
    <p class="from-stream">
      From the stream: <a href="{{ .RelPermalink }}">{{ .Date.Format "2006-01-02" }} — {{ .Title }}</a>
    </p>
  {{- end -}}
{{- end -}}
```

(No `→` arrow per memory.)

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/streams/from-stream.html
git commit -m "streams(partial): from-stream — shared attribution block

Single partial included in 7 cross-section single templates (Task 27).
DRY: section single layouts don't each carry an inline stream lookup.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

# Phase 6 — Streams section layouts

## Task 24: `layouts/streams/list.html`

**Files:**
- Create: `layouts/streams/list.html`

- [ ] **Step 1: Write the list layout**

Create `layouts/streams/list.html`:

```hugo
{{ define "main" }}
<article class="page streams-index">
  <span data-pagefind-meta="section:streams" hidden></span>
  <span data-pagefind-filter="section:streams" hidden></span>
  <header class="page-header">
    <h1>{{ .Title }}</h1>
    {{ with .Description }}<p class="page-description">{{ . }}</p>{{ end }}
  </header>

  {{ .Content }}

  {{- /* Upcoming strip (no limit on the section index — show everything future). */ -}}
  {{ partial "streams/upcoming.html" (dict "heading" "Upcoming") }}

  {{- /* Filter chips on archive. */ -}}
  {{ $items := .Pages.ByDate.Reverse }}

  {{- $cats := slice -}}
  {{- $years := slice -}}
  {{- $tagCounts := dict -}}
  {{- range $items -}}
    {{- $c := .Params.category -}}
    {{- if and $c (not (in $cats $c)) -}}{{- $cats = $cats | append $c -}}{{- end -}}
    {{- $y := printf "%d" .Date.Year -}}
    {{- if not (in $years $y) -}}{{- $years = $years | append $y -}}{{- end -}}
    {{- range .Params.tags -}}
      {{- $cur := index $tagCounts . | default 0 -}}
      {{- $tagCounts = merge $tagCounts (dict . (add $cur 1)) -}}
    {{- end -}}
  {{- end -}}

  {{- /* Tags ranked by count desc, alphabetical for ties. */ -}}
  {{- $tagPairs := slice -}}
  {{- range $name, $count := $tagCounts -}}
    {{- $tagPairs = $tagPairs | append (dict "name" $name "count" $count) -}}
  {{- end -}}
  {{- $tags := slice -}}
  {{- range (sort (sort $tagPairs "name" "asc") "count" "desc") -}}
    {{- $tags = $tags | append .name -}}
  {{- end -}}

  {{- $dims := slice -}}
  {{- if ge (len $cats) 2 -}}
    {{- $dims = $dims | append (dict "key" "category" "label" "Category" "values" $cats) -}}
  {{- end -}}
  {{- if ge (len $years) 2 -}}
    {{- $dims = $dims | append (dict "key" "year" "label" "Year" "values" $years) -}}
  {{- end -}}
  {{- if ge (len $tags) 2 -}}
    {{- $dims = $dims | append (dict "key" "tag" "label" "Tag" "values" $tags) -}}
  {{- end -}}

  {{ partial "filter-chips.html" (dict "dimensions" $dims "section" "streams") }}

  <section class="streams-archive-list" aria-label="Archived streams">
    {{- range $items -}}
      {{- partial "streams/stream-card.html" . -}}
    {{- end -}}
  </section>
</article>
{{ end }}
```

- [ ] **Step 2: Commit**

```bash
git add layouts/streams/list.html
git commit -m "streams(layout): /streams/ list page — upcoming + filter chips + archive

Standard section-index shape (mirrors works-games/list.html). Filter
dims: category (enum) + year (derived) + tag (two-tier via shared
filter-chips.html). data-pagefind-meta + filter spans per gotcha.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 25: `layouts/streams/single.html`

**Files:**
- Create: `layouts/streams/single.html`

- [ ] **Step 1: Write the single layout**

Create `layouts/streams/single.html`:

```hugo
{{ define "main" }}
<article class="page streams-single">
  <span data-pagefind-meta="section:streams" hidden></span>
  <span data-pagefind-meta="category:{{ .Params.category }}" hidden></span>
  <span data-pagefind-meta="archive_status:{{ .Params.archive_status }}" hidden></span>
  <span data-pagefind-filter="section:streams" hidden></span>

  <header class="streams-single-header">
    <p class="streams-single-meta">
      <time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date.Format "Mon Jan 2, 2006" }}</time>
      {{- with .Params.duration }} · <span>{{ . }}</span>{{- end }}
      · <span class="streams-category-pill streams-category-pill--{{ .Params.category }}">{{ humanize .Params.category }}</span>
    </p>
    <h1>{{ .Title }}</h1>
    {{- with .Params.summary -}}<p class="streams-single-summary">{{ . }}</p>{{- end -}}
  </header>

  {{- /* Cite CTA above the embed (citable when archived/removed; predicate gates upstream). */ -}}
  {{- if in (slice "archived" "removed") .Params.archive_status -}}
    <div class="cite-cta-zone streams-cite-zone">{{ partial "cite/button.html" . }}</div>
  {{- end -}}

  {{- /* Embed / placeholder area, per archive_status. */ -}}
  {{- $arc := .Params.archive_status -}}
  {{- if eq $arc "archived" -}}
    {{- $vod := .Params.vod_url -}}
    {{- $vid := "" -}}
    {{- with findRE "(?:v=|youtu\\.be/|youtube\\.com/embed/)([A-Za-z0-9_-]{6,15})" $vod 1 -}}
      {{- $m := index . 0 -}}
      {{- $vid = replaceRE "^.*[/=]" "" $m -}}
    {{- end -}}
    {{- if $vid -}}
      {{ partial "streams/embed.html" (dict "video_id" $vid) }}
    {{- else -}}
      <p class="streams-archive-missing">VOD URL set but video ID could not be parsed.</p>
    {{- end -}}
  {{- else if eq $arc "live" -}}
    <p class="streams-archive-live">🔴 Currently live, watch on Twitch.</p>
  {{- else if eq $arc "removed" -}}
    <p class="streams-archive-removed">Archive intentionally removed.</p>
  {{- end -}}

  <section class="streams-single-notes">
    {{ .Content }}
  </section>

  {{ partial "streams/cross-refs.html" . }}

  {{- /* Cite scaffolding: emit unconditionally; the centralised predicate
       (baseof/head/scripts) gates whether modal/meta/JS are loaded. */ -}}
  {{- if in (slice "archived" "removed") .Params.archive_status -}}
    {{ partial "cite/static-fallback.html" . }}
    {{ partial "cite/data-blob.html" . }}
  {{- end -}}
</article>
{{ end }}
```

Notes:
- No `page-sidebar.html` include (spec §15 — streams single pages are single-section; rail not needed).
- No `graph-launcher-bar.html` (no streams graph view).
- Citation scaffolding wrapped in the same `archive_status` predicate as the citable triplet — so live / private pages emit no `cite-data` blob (matches `check_cite_meta`'s expectation that audited pages have it).
- Three pagefind-meta spans (one per key — gotcha) + one pagefind-filter span.

- [ ] **Step 2: Commit**

```bash
git add layouts/streams/single.html
git commit -m "streams(layout): /streams/<slug>/ single page

archive_status routing: archived ⇒ click-to-load YT embed, live ⇒
'watch on Twitch' callout, removed ⇒ removed callout. Cite
scaffolding rendered only when archived/removed (matches the
upstream citable-predicate gate). No page-sidebar (single-section).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

# Phase 7 — Chrome wiring

## Task 26: `header.html` — 7th nav item + live-pill include

**Files:**
- Modify: `layouts/partials/header.html`

- [ ] **Step 1: Insert nav item + live-pill before closing `</nav>`**

In `layouts/partials/header.html`, find the dict slice:

```hugo
    {{ range slice
        (dict "url" "/essays/"  "label" "Essays")
        (dict "url" "/garden/"  "label" "Garden")
        (dict "url" "/research/" "label" "Research")
        (dict "url" "/works/"   "label" "Works")
        (dict "url" "/library/" "label" "Library")
        (dict "url" "/about/"   "label" "About")
    }}
```

Replace with:

```hugo
    {{ range slice
        (dict "url" "/essays/"  "label" "Essays")
        (dict "url" "/garden/"  "label" "Garden")
        (dict "url" "/research/" "label" "Research")
        (dict "url" "/works/"   "label" "Works")
        (dict "url" "/library/" "label" "Library")
        (dict "url" "/streams/" "label" "Streams")
        (dict "url" "/about/"   "label" "About")
    }}
```

- [ ] **Step 2: Add live-pill include**

In the same file, find the line just before the RSS-link `<a>`:

```hugo
    {{ end }}
    <a class="icon-button rss-link"
```

Replace with (insert the live-pill partial call between the `{{ end }}` of the nav loop and the RSS link):

```hugo
    {{ end }}
    {{ partial "streams/live-pill.html" . }}
    <a class="icon-button rss-link"
```

- [ ] **Step 3: User-verify**

ASK USER: "Restart dev server, load any page. Confirm 7 nav items (Essays · Garden · Research · Works · Library · Streams · About). With `data/streams-live.yaml` seeded `is_live: false`, no live-pill should appear; edit the yaml to set `live.twitch.is_live: true` + `live.twitch.url: https://twitch.tv/x` and reload → red LIVE pill appears, linking to Twitch. Revert."

- [ ] **Step 4: Commit**

```bash
git add layouts/partials/header.html
git commit -m "chrome(header): 7th nav item Streams + live-pill partial

Streams inserted before About (per spec §0 decision). Live-pill
between nav and RSS-link slot. Updates the locked nav from 6→7 items.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 27: 7 cross-section single templates — include `from-stream.html`

**Files (each modified):**
- `layouts/essays/single.html`
- `layouts/garden/single.html`
- `layouts/research-theme/single.html`
- `layouts/research-question/single.html`
- `layouts/works-games/single.html`
- `layouts/works-music/single.html`
- `layouts/works-poetry/single.html`

For each: insert `{{ partial "streams/from-stream.html" . }}` AFTER the page header (`<h1>` and meta line) and BEFORE the main body content. The exact insertion point depends on each template — guidance below.

- [ ] **Step 1: `layouts/essays/single.html`**

Find the closing `</header>` of the essay header block (whichever `<header>` contains the `<h1>{{ .Title }}</h1>`). Insert immediately after:

```hugo
{{ partial "streams/from-stream.html" . }}
```

- [ ] **Step 2: `layouts/garden/single.html`**

Find the partial that emits the garden note header (likely `{{ partial "garden/note-header.html" . }}`). Insert `{{ partial "streams/from-stream.html" . }}` immediately after.

- [ ] **Step 3: `layouts/research-theme/single.html`**

Find the closing `</header>` of the theme header. Insert `{{ partial "streams/from-stream.html" . }}` immediately after.

- [ ] **Step 4: `layouts/research-question/single.html`**

Same as Step 3 for the question header.

- [ ] **Step 5: `layouts/works-games/single.html`**

Find the closing `</header>` of `<header class="works-game-hero">`. Insert `{{ partial "streams/from-stream.html" . }}` immediately after.

- [ ] **Step 6: `layouts/works-music/single.html`**

Find the closing `</header>` of the music hero block. Insert after.

- [ ] **Step 7: `layouts/works-poetry/single.html`**

Find the closing `</header>` of the poem header block. Insert after.

- [ ] **Step 8: User-verify**

ASK USER: "Restart dev server. Visit each of the 6 fixtures wired in Task 11. Each should render a one-line 'From the stream: <date> — <stream title>' attribution between the title block and the body. Visit a fixture WITHOUT `source_stream:` — confirm no attribution renders."

- [ ] **Step 9: Commit**

```bash
git add layouts/essays/single.html layouts/garden/single.html \
        layouts/research-theme/single.html layouts/research-question/single.html \
        layouts/works-games/single.html layouts/works-music/single.html \
        layouts/works-poetry/single.html
git commit -m "chrome(cross-section): include streams/from-stream.html in 7 single layouts

Renders 'From the stream: <date> — <title>' attribution when
source_stream: <slug> is set. Partial no-ops when absent.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

# Phase 8 — Homepage strip + page-sidebar entry

## Task 28: `partials/home/streams-strip.html`

**Files:**
- Create: `layouts/partials/home/streams-strip.html`

- [ ] **Step 1: Write the strip partial**

Create `layouts/partials/home/streams-strip.html`:

```hugo
{{- /* Homepage "Upcoming streams" strip. Slot mirrors the other strip
       partials (home/research-strip.html etc.) — own header + body block.
       Wraps the shared streams/upcoming.html (limit 2 entries to stay
       above-the-fold). No → arrows per memory feedback_no_arrow_prefix_on_links. */ -}}
<div class="home-streams-block">
  <header class="home-strip-header">
    <h2>Upcoming streams</h2>
    <a class="home-strip-all" href="{{ "/streams/" | relURL }}">All streams</a>
  </header>
  {{ partial "streams/upcoming.html" (dict "limit" 2 "heading" "") }}
</div>
```

(Setting `heading: ""` suppresses the inner `<h2>` from upcoming.html — the strip's own header carries the heading. Note: upcoming.html as-written always sets a heading via `default`. Update upcoming.html to honor `heading: ""`:)

- [ ] **Step 2: Tweak upcoming.html to honor empty heading**

In `layouts/partials/streams/upcoming.html`, find:

```hugo
{{- $heading := $args.heading | default "Upcoming streams" -}}
```

Replace with:

```hugo
{{- $heading := "" -}}
{{- if hasKey $args "heading" -}}{{- $heading = $args.heading -}}
{{- else -}}{{- $heading = "Upcoming streams" -}}{{- end -}}
```

And in the same file, wrap the existing `<h2>` so it omits when empty:

```hugo
<section class="streams-upcoming" aria-labelledby="streams-upcoming-heading">
  <h2 id="streams-upcoming-heading">{{ $heading }}</h2>
```

→

```hugo
<section class="streams-upcoming"{{ if $heading }} aria-labelledby="streams-upcoming-heading"{{ end }}>
  {{- if $heading -}}<h2 id="streams-upcoming-heading">{{ $heading }}</h2>{{- end -}}
```

- [ ] **Step 3: User-verify**

ASK USER: "Wait until Task 29 wires the strip into home.html, then visit /, scroll to the streams strip. Expect 2 upcoming entries from data/streams-schedule.yaml, sorted by date asc."

- [ ] **Step 4: Commit**

```bash
git add layouts/partials/home/streams-strip.html layouts/partials/streams/upcoming.html
git commit -m "streams(home): home/streams-strip + upcoming.html honors empty heading

Strip wraps streams/upcoming.html (limit 2). Heading lives in the
strip header; upcoming.html's inner <h2> suppressed when called with
heading:\"\". No → arrows on 'All streams' link.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 29: `layouts/home.html` — wire streams strip + page-sidebar section entry

**Files:**
- Modify: `layouts/home.html`

- [ ] **Step 1: Add `streams` to the page-sidebar sections slice**

In `layouts/home.html`, find:

```hugo
  {{ partial "page-sidebar.html" (dict "sections" (slice
      (dict "id" "currently" "label" "Currently")
      (dict "id" "essays"    "label" "Essays")
      (dict "id" "research"  "label" "Research")
      (dict "id" "works"     "label" "Works")
    )) }}
```

Replace with:

```hugo
  {{ partial "page-sidebar.html" (dict "sections" (slice
      (dict "id" "currently" "label" "Currently")
      (dict "id" "essays"    "label" "Essays")
      (dict "id" "research"  "label" "Research")
      (dict "id" "works"     "label" "Works")
      (dict "id" "streams"   "label" "Streams")
    )) }}
```

- [ ] **Step 2: Insert the streams strip into the page flow**

Decide placement: after the `home-research-section` (which contains research + garden) and before `studio-strip`. In `layouts/home.html`, find:

```hugo
  <section id="research" class="home-research-section">
    {{ partial "home/research-strip.html" . }}
    {{ partial "home/garden-strip.html" . }}
  </section>

  {{ partial "home/studio-strip.html" . }}
</div>
```

Replace with:

```hugo
  <section id="research" class="home-research-section">
    {{ partial "home/research-strip.html" . }}
    {{ partial "home/garden-strip.html" . }}
  </section>

  <section id="streams" class="home-streams-section">
    {{ partial "home/streams-strip.html" . }}
  </section>

  {{ partial "home/studio-strip.html" . }}
</div>
```

- [ ] **Step 3: User-verify**

ASK USER: "Reload /. Expect: 5 page-sidebar dots (Currently / Essays / Research / Works / Streams). The streams strip appears between research+garden and Studio with the 2 upcoming entries."

- [ ] **Step 4: Commit**

```bash
git add layouts/home.html
git commit -m "home: wire streams strip + page-sidebar section entry

5th sidebar dot 'Streams'. Strip placed between research-section
and studio-strip in page flow.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

# Phase 9 — JS bundle + CSS

## Task 30: `assets/js/streams.js` + `assets/js/entry-streams.js`

**Files:**
- Create: `assets/js/streams.js`
- Create: `assets/js/entry-streams.js`

- [ ] **Step 1: Write `streams.js`**

Create `assets/js/streams.js`:

```js
// Streams runtime. Spec: docs/superpowers/specs/2026-05-13-streams-section-design.md §8.
// Single responsibility: click-to-load YouTube embed. Self-guards on .yt-embed
// so it's safe to load on any page in the section.

export function initStreams() {
  const els = document.querySelectorAll('.yt-embed');
  if (!els.length) return;
  els.forEach((el) => {
    el.addEventListener('click', () => {
      const id = el.dataset.videoId;
      if (!id) return;
      if (el.classList.contains('yt-embed-loaded')) return;
      const iframe = document.createElement('iframe');
      iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1`;
      iframe.allow =
        'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
      iframe.allowFullscreen = true;
      iframe.title = 'YouTube video';
      iframe.loading = 'lazy';
      iframe.style.width = '100%';
      iframe.style.height = '100%';
      iframe.style.border = '0';
      el.replaceChildren(iframe);
      el.classList.add('yt-embed-loaded');
    });
  });
}
```

- [ ] **Step 2: Write `entry-streams.js`**

Create `assets/js/entry-streams.js`:

```js
// Streams-section entry — loaded only on /streams/<slug>/ single pages
// (gated in layouts/partials/scripts.html). streams.js self-guards on
// .yt-embed, so pages without an embed (live / removed / no vod) no-op.
import { initStreams } from './streams.js';
initStreams();
```

- [ ] **Step 3: Commit**

```bash
git add assets/js/streams.js assets/js/entry-streams.js
git commit -m "streams(js): click-to-load runtime + bundle entry

initStreams() mounts youtube-nocookie iframe on .yt-embed click; self-
guards (no-op on pages without .yt-embed). Idempotent: re-click on
already-loaded embed is a no-op.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 31: `scripts.html` — add 11th `js.Build` entry

**Files:**
- Modify: `layouts/partials/scripts.html`

- [ ] **Step 1: Append the streams bundle gate**

In `layouts/partials/scripts.html`, find the synced-poetry block (the last `{{- if and ... }}` block before the closing brace of the partial). Append AFTER it (and before any trailing close):

```hugo
{{- /* Streams runtime: only on /streams/<slug>/ pages. streams.js
       self-guards on .yt-embed so pages without an embed (live /
       removed / no vod) no-op. */ -}}
{{- if and (eq .Section "streams") (eq .Kind "page") }}
{{- $streamsOpts := dict "targetPath" "js/streams.js" "minify" true -}}
{{- $streams := resources.Get "js/entry-streams.js" | js.Build $streamsOpts | fingerprint }}
<script src="{{ $streams.RelPermalink }}" integrity="{{ $streams.Data.Integrity }}" defer></script>
{{- end }}
```

- [ ] **Step 2: User-verify**

ASK USER: "Reload `/streams/2026-04-10-example-live-coding-stream/`. View source (or DevTools Network) — confirm a `streams.<hash>.js` is loaded. Click the YouTube thumbnail → iframe mounts to youtube-nocookie.com/embed/dQw4w9WgXcQ. Reload `/streams/2026-04-22-example-music-jam-stream/` (removed; no embed): streams.js still loads but no-ops cleanly (no console errors)."

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/scripts.html
git commit -m "scripts: 11th js.Build entry — entry-streams.js on /streams/<slug>/

Section+kind narrow guard. Mirror of the poetry entry pattern.
streams.<hash>.js → ~1KB minified.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 32: `assets/css/main.css` — append §46

**Files:**
- Modify: `assets/css/main.css` (append to end)

- [ ] **Step 1: Append §46 banner + styles**

Append to the end of `assets/css/main.css`:

```css

/* ============================================================================
   §46 Streams
   <new top-level section per spec 2026-05-13-streams-section-design.md;
    header live-pill, click-to-load YT embed, archive grid, upcoming strip,
    cross-section from-stream attribution, category pill palette>
   ========================================================================== */

/* Header live-pill */
.header-live-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 2px 8px;
  margin-left: 0.4rem;
  background: rgba(178, 34, 34, 0.10);
  border: 1px solid rgba(178, 34, 34, 0.35);
  border-radius: 999px;
  color: var(--color-burgundy);
  font-family: var(--font-ui);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-decoration: none;
}
.header-live-pill-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #b22222;
  animation: live-pulse 1.6s ease-in-out infinite;
}
@keyframes live-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.55; transform: scale(0.78); }
}
@media (prefers-reduced-motion: reduce) {
  .header-live-pill-dot { animation: none; }
}

/* YouTube click-to-load embed (16:9) */
.yt-embed {
  position: relative;
  aspect-ratio: 16 / 9;
  width: 100%;
  background: #000;
  border-radius: 4px;
  overflow: hidden;
  margin: 1rem 0 1.4rem;
  cursor: pointer;
}
.yt-embed-play {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 0;
}
.yt-embed-thumb {
  width: 100%; height: 100%;
  object-fit: cover;
  display: block;
}
.yt-embed-play-icon {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px; height: 64px;
  background: rgba(178, 34, 34, 0.92);
  color: white;
  border-radius: 50%;
  font-size: 1.6rem;
  line-height: 1;
  padding-left: 4px;
}
.yt-embed-loaded { cursor: default; }

/* Streams index archive grid */
.streams-archive-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  margin-top: 1.2rem;
}
@media (min-width: 960px) {
  .streams-archive-list { grid-template-columns: repeat(2, 1fr); }
}
@media (min-width: 1280px) {
  .streams-archive-list { grid-template-columns: repeat(3, 1fr); }
}
.stream-card {
  background: var(--color-tile);
  border: 1px solid var(--color-ink-soft);
  border-radius: 4px;
  padding: 0.9rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.stream-card-title {
  font-family: var(--font-body);
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-ink);
  text-decoration: none;
}
.stream-card-title:hover { text-decoration: underline; }
.stream-card-meta {
  font-family: var(--font-ui);
  font-size: 0.72rem;
  color: var(--color-ink-soft);
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
}
.stream-card-summary { margin: 0; font-size: 0.9rem; }
.stream-card-output-counts {
  margin: 0;
  font-size: 0.72rem;
  color: var(--color-ink-soft);
  font-style: italic;
}
.stream-card-removed {
  margin: 0;
  font-size: 0.72rem;
  color: var(--color-steel);
  font-style: italic;
}
.stream-card[hidden] { display: none; }   /* filter-chip hide cascade */

/* Streams category pill palette — 4 distinct values; reuse the existing
   accent token set so we stay CB-safe + within the locked palette. */
.streams-category-pill {
  display: inline-flex;
  align-items: center;
  padding: 1px 8px;
  border-radius: 999px;
  font-family: var(--font-ui);
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-stone);
}
.streams-category-pill--game-dev  { background: var(--color-burgundy); }
.streams-category-pill--research  { background: var(--color-steel); }
.streams-category-pill--coding    { background: var(--color-ink); }
.streams-category-pill--creative  { background: var(--color-green); }

/* Upcoming list (used on /streams/ AND inside home-streams-strip) */
.streams-upcoming { margin: 1rem 0; }
.streams-upcoming-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.55rem;
}
.streams-upcoming-item {
  padding: 0.5rem 0.7rem;
  background: var(--color-tile);
  border-left: 3px solid var(--color-burgundy);
  border-radius: 0 3px 3px 0;
  display: grid;
  gap: 0.2rem;
}
.streams-upcoming-item time {
  font-family: var(--font-ui);
  font-size: 0.7rem;
  color: var(--color-ink-soft);
}
.streams-upcoming-title { font-weight: 600; }
.streams-upcoming-summary {
  margin: 0;
  font-size: 0.85rem;
}
.streams-upcoming-platforms {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-ink-soft);
}

/* Homepage streams strip */
.home-streams-block { margin: 2rem 0; }
.home-streams-section { margin: 2rem 0; }

/* Streams single page */
.streams-single-header { margin-bottom: 1rem; }
.streams-single-meta {
  font-family: var(--font-ui);
  font-size: 0.78rem;
  color: var(--color-ink-soft);
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
  margin: 0 0 0.4rem;
}
.streams-single-summary {
  margin-top: 0.4rem;
  font-style: italic;
  color: var(--color-ink-soft);
}
.streams-archive-live,
.streams-archive-removed,
.streams-archive-missing {
  padding: 1rem 1.2rem;
  background: var(--color-tile);
  border-radius: 4px;
  font-family: var(--font-ui);
  font-size: 0.9rem;
  color: var(--color-ink-soft);
  margin: 1rem 0 1.4rem;
}

.streams-single-notes { margin: 1.4rem 0; }

.streams-cross-refs {
  margin-top: 1.6rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-ink-soft);
}
.streams-cross-refs h2 {
  font-size: 1rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-ink-soft);
  margin: 0 0 0.6rem;
}
.streams-cross-refs-group { margin: 0 0 0.8rem; }
.streams-cross-refs-group h3 {
  font-size: 0.78rem;
  font-family: var(--font-ui);
  color: var(--color-ink-soft);
  margin: 0 0 0.2rem;
  font-weight: 600;
}
.streams-cross-refs-group ul {
  margin: 0; padding: 0 0 0 1rem;
}

/* Cross-section attribution block */
.from-stream {
  margin: 0.4rem 0 0.8rem;
  padding: 0.4rem 0.7rem;
  border-left: 3px solid var(--color-burgundy);
  background: rgba(138, 58, 58, 0.05);
  font-family: var(--font-ui);
  font-size: 0.78rem;
  color: var(--color-ink-soft);
  border-radius: 0 3px 3px 0;
}
.from-stream a { color: inherit; }
```

- [ ] **Step 2: Verify contrast (CI gate)**

Run: `python3 tools/check-contrast.py`
Expected: pass — §46 doesn't introduce new color tokens; only reuses existing palette.

- [ ] **Step 3: User-verify visually**

ASK USER: "Reload the streams pages end-to-end. Things to eyeball: (1) the LIVE pill pulses in the header (set `is_live: true` in data/streams-live.yaml to test, then revert), (2) /streams/ shows the 2-card archive grid in light + dark mode, (3) /streams/2026-04-10-... shows the YT thumbnail with red play button, click loads the iframe, (4) the 6 fixture pages show 'From the stream: ...' attribution above the body, (5) homepage `Upcoming streams` strip renders the 2 future entries. Test at 360 / 768 / 960 / 1280 breakpoints (memory: half-screen 1080p ≈ 960)."

- [ ] **Step 4: Commit**

```bash
git add assets/css/main.css
git commit -m "css(§46): streams runtime — live-pill, embed, cards, pills, strip

Reuses existing palette tokens (no new vars; contrast unchanged).
Card grid: 1col / 2col @960 / 3col @1280. Live-pill pulse honors
prefers-reduced-motion. .stream-card[hidden] override for filter-chip
cascade.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

# Phase 10 — Search modal integration

## Task 33: `partials/search-modal.html` — add Streams filter chip

**Files:**
- Modify: `layouts/partials/search-modal.html`

- [ ] **Step 1: Add the chip**

In `layouts/partials/search-modal.html`, find the existing filter-chip row (`<button data-search-filter="section:essays">` etc.). Insert a Streams chip immediately before About (matching the nav order). The exact line varies; the canonical form is:

```html
<button type="button" class="search-filter-chip" data-search-filter="section:streams">Streams</button>
```

Place it directly before the About chip in the row.

- [ ] **Step 2: User-verify**

ASK USER: "Open the search modal (press `/`). Confirm Streams chip appears between Library and About. Type 'example' — filter to Streams; results should include the 2 stream fixtures."

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/search-modal.html
git commit -m "search: Streams filter chip in modal (between Library and About)

Pagefind: section:streams meta+filter spans emitted by list.html /
single.html (Task 24/25); check_pagefind_meta already recognizes
'streams' (Task 5).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

# Phase 11 — Poller + cron workflow

## Task 34: `tools/poll_streams.py` + `tools/test_poll_streams.py` (TDD, multiple steps)

The poller is stdlib-only (no `requests` — use `urllib.request`). All HTTP calls are mocked in tests. Spec §5 lists 7 responsibilities; we'll TDD them in order.

**Files:**
- Create: `tools/poll_streams.py`
- Create: `tools/test_poll_streams.py`

### Sub-task 34A: scaffold + Twitch OAuth

- [ ] **Step 1: Write failing tests for Twitch OAuth**

Create `tools/test_poll_streams.py`:

```python
"""Tests for tools/poll_streams.py — run with:
   python3 -m unittest tools/test_poll_streams.py -v

All network calls are mocked via unittest.mock.patch on urllib.request.urlopen.
"""
from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import poll_streams as ps  # noqa: E402


def _mock_response(body, status=200, headers=None):
    """Helper: build a fake urllib HTTPResponse-like object."""
    resp = MagicMock()
    resp.read.return_value = body.encode("utf-8") if isinstance(body, str) else body
    resp.status = status
    resp.getcode.return_value = status
    resp.headers = headers or {}
    resp.__enter__ = lambda self_: self_
    resp.__exit__ = lambda *a: None
    return resp


class TwitchOAuthTests(unittest.TestCase):
    @patch("poll_streams.urllib.request.urlopen")
    def test_oauth_returns_access_token(self, mock_open):
        mock_open.return_value = _mock_response(json.dumps({
            "access_token": "tok-abc",
            "expires_in": 5184000,
            "token_type": "bearer",
        }))
        token = ps.twitch_oauth("client-id", "client-secret")
        self.assertEqual(token, "tok-abc")

    @patch("poll_streams.urllib.request.urlopen")
    def test_oauth_raises_on_missing_token(self, mock_open):
        mock_open.return_value = _mock_response(json.dumps({"error": "denied"}))
        with self.assertRaises(ps.PollError):
            ps.twitch_oauth("client-id", "client-secret")
```

- [ ] **Step 2: Run tests to verify they fail (import error)**

Run: `python3 -m unittest tools/test_poll_streams.py -v 2>&1 | tail -5`
Expected: `ModuleNotFoundError: No module named 'poll_streams'`.

- [ ] **Step 3: Scaffold `poll_streams.py` with Twitch OAuth**

Create `tools/poll_streams.py`:

```python
#!/usr/bin/env python3
"""Streams live-state + schedule poller.

Cron-invoked by .github/workflows/streams-poll.yaml every 5 min.
- Polls Twitch /helix/streams for live state (+ oauth dance).
- HEAD-probes youtube.com/channel/<id>/live for YT live state (0 Data-API quota).
- Once per hour: pulls Twitch /helix/schedule and writes streams-twitch-cache.yaml.
- On live→not-live transition: writes an auto-stub at content/streams/<slug>/index.md.

Spec: docs/superpowers/specs/2026-05-13-streams-section-design.md §5.
Stdlib only. Always exits 0 on transient API failures (preserves prior yaml).
Exits non-zero only on auth-config errors.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class PollError(Exception):
    """Raised on auth-config or contract violations that must NOT silently 0-exit."""


# --- Twitch ---

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_STREAMS_URL = "https://api.twitch.tv/helix/streams"
TWITCH_SCHEDULE_URL = "https://api.twitch.tv/helix/schedule"
YOUTUBE_LIVE_URL_TEMPLATE = "https://www.youtube.com/channel/{channel_id}/live"


def _http_post_form(url: str, body: dict) -> Any:
    data = urllib.parse.urlencode(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    return urllib.request.urlopen(req, timeout=10)


def _http_get(url: str, headers: dict | None = None) -> Any:
    req = urllib.request.Request(url, method="GET", headers=headers or {})
    return urllib.request.urlopen(req, timeout=10)


def _http_head_no_follow(url: str) -> int:
    """Return HTTP status code from a HEAD request without following redirects."""
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **kw):
            return None
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, method="HEAD")
    try:
        with opener.open(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def twitch_oauth(client_id: str, client_secret: str) -> str:
    """Client-credentials grant. Returns access token. Raises PollError on failure."""
    resp = _http_post_form(TWITCH_TOKEN_URL, {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    })
    with resp:
        payload = json.loads(resp.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise PollError(f"twitch oauth: no access_token in response: {payload!r}")
    return token


if __name__ == "__main__":
    sys.exit(0)  # placeholder; main() lands in Sub-task 34F
```

Add `import urllib.error` near the imports.

Replace the imports block with:

```python
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tools/test_poll_streams.py -v 2>&1 | tail -10`
Expected: 2/2 pass.

- [ ] **Step 5: Commit**

```bash
git add tools/poll_streams.py tools/test_poll_streams.py
git commit -m "poll(streams): scaffold + Twitch OAuth (TDD)

stdlib-only urllib transport. PollError signals auth-config bugs;
transient HTTP failures (next sub-tasks) silently 0-exit.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Sub-task 34B: Twitch live state

- [ ] **Step 1: Write failing tests**

Append to `tools/test_poll_streams.py`:

```python
class TwitchLiveStateTests(unittest.TestCase):
    @patch("poll_streams.urllib.request.urlopen")
    def test_twitch_streams_live(self, mock_open):
        mock_open.return_value = _mock_response(json.dumps({
            "data": [{
                "type": "live",
                "title": "Example live stream",
                "started_at": "2026-04-10T19:00:00Z",
                "user_login": "a3madkour",
            }],
        }))
        state = ps.twitch_live_state("tok-abc", "client-id", "a3madkour")
        self.assertTrue(state["is_live"])
        self.assertEqual(state["title"], "Example live stream")
        self.assertEqual(state["started_at"], "2026-04-10T19:00:00Z")
        self.assertEqual(state["url"], "https://twitch.tv/a3madkour")

    @patch("poll_streams.urllib.request.urlopen")
    def test_twitch_streams_not_live(self, mock_open):
        mock_open.return_value = _mock_response(json.dumps({"data": []}))
        state = ps.twitch_live_state("tok-abc", "client-id", "a3madkour")
        self.assertFalse(state["is_live"])
        self.assertEqual(state["title"], "")
        self.assertEqual(state["url"], "")
```

- [ ] **Step 2: Run to fail**

Run: `python3 -m unittest tools/test_poll_streams.py -v 2>&1 | tail -10`
Expected: 2 new failures (`AttributeError: module 'poll_streams' has no attribute 'twitch_live_state'`).

- [ ] **Step 3: Implement `twitch_live_state`**

Append to `tools/poll_streams.py` (before the `if __name__ ==` block):

```python
def twitch_live_state(token: str, client_id: str, user_login: str) -> dict:
    """Return {is_live, title, started_at, url} for a Twitch user."""
    url = f"{TWITCH_STREAMS_URL}?{urllib.parse.urlencode({'user_login': user_login})}"
    resp = _http_get(url, headers={
        "Authorization": f"Bearer {token}",
        "Client-Id": client_id,
    })
    with resp:
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data") or []
    if not data or data[0].get("type") != "live":
        return {"is_live": False, "title": "", "started_at": "", "url": ""}
    entry = data[0]
    return {
        "is_live": True,
        "title": entry.get("title", ""),
        "started_at": entry.get("started_at", ""),
        "url": f"https://twitch.tv/{user_login}",
    }
```

- [ ] **Step 4: Run to pass**

Run: `python3 -m unittest tools/test_poll_streams.py -v 2>&1 | tail -10`
Expected: 4/4 pass.

- [ ] **Step 5: Commit**

```bash
git add tools/poll_streams.py tools/test_poll_streams.py
git commit -m "poll(streams): twitch_live_state via /helix/streams (TDD)

Maps Helix response shape → {is_live,title,started_at,url}. Empty
data array (not currently live) returns is_live=false with empty
strings (yaml-friendly).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Sub-task 34C: YouTube live HEAD probe

- [ ] **Step 1: Write failing tests**

Append:

```python
class YouTubeLiveProbeTests(unittest.TestCase):
    @patch("poll_streams._http_head_no_follow")
    def test_youtube_live_200(self, mock_head):
        mock_head.return_value = 200
        self.assertTrue(ps.youtube_is_live("UC-abc"))

    @patch("poll_streams._http_head_no_follow")
    def test_youtube_live_302(self, mock_head):
        # 302 redirect = currently live (YouTube redirects /channel/<id>/live to /watch?v=...)
        mock_head.return_value = 302
        self.assertTrue(ps.youtube_is_live("UC-abc"))

    @patch("poll_streams._http_head_no_follow")
    def test_youtube_not_live_404(self, mock_head):
        mock_head.return_value = 404
        self.assertFalse(ps.youtube_is_live("UC-abc"))

    @patch("poll_streams._http_head_no_follow")
    def test_youtube_not_live_other(self, mock_head):
        mock_head.return_value = 500
        self.assertFalse(ps.youtube_is_live("UC-abc"))
```

- [ ] **Step 2: Run to fail; implement; rerun**

Add to `poll_streams.py`:

```python
def youtube_is_live(channel_id: str) -> bool:
    """HEAD-probe youtube.com/channel/<id>/live. 200 or 3xx = live."""
    url = YOUTUBE_LIVE_URL_TEMPLATE.format(channel_id=channel_id)
    status = _http_head_no_follow(url)
    return status == 200 or (300 <= status < 400)
```

Run: `python3 -m unittest tools/test_poll_streams.py -v 2>&1 | tail -10`
Expected: 8/8 pass.

- [ ] **Step 3: Commit**

```bash
git add tools/poll_streams.py tools/test_poll_streams.py
git commit -m "poll(streams): youtube_is_live HEAD probe (0 Data-API quota)

Spec §5: HEAD /channel/<id>/live without following redirects. 200 or
30x = live; everything else = not live. Saves the YT Data API quota
budget for VOD URL discovery (deferred per spec §15).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Sub-task 34D: Auto-stub creation

- [ ] **Step 1: Write failing tests**

Append:

```python
class AutoStubTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_creates_stub_when_absent(self):
        ps.write_auto_stub(
            content_root=self.tmp / "content",
            title="Example live coding stream",
            started_at_iso="2026-04-10T19:00:00Z",
        )
        path = self.tmp / "content" / "streams" / "2026-04-10-example-live-coding-stream" / "index.md"
        self.assertTrue(path.exists())
        text = path.read_text()
        self.assertIn('title: "Example live coding stream"', text)
        self.assertIn("archive_status: archived", text)
        self.assertIn("draft: true", text)
        self.assertIn("category: game-dev", text)
        self.assertIn("platforms: [twitch, youtube]", text)
        self.assertIn('date: 2026-04-10T19:00:00', text)

    def test_idempotent_does_not_overwrite(self):
        path = self.tmp / "content" / "streams" / "2026-04-10-already-here" / "index.md"
        path.parent.mkdir(parents=True)
        path.write_text("---\ntitle: \"Hand-edited\"\n---\nuser content\n")
        ps.write_auto_stub(
            content_root=self.tmp / "content",
            title="already here",
            started_at_iso="2026-04-10T19:00:00Z",
        )
        self.assertIn("user content", path.read_text())

    def test_slugify_strips_punctuation_and_lowercases(self):
        # Title with mixed case + punctuation + multiple spaces.
        slug = ps.slugify("Game Dev: HEX grid (prototype)!")
        # Expected: lowercase, ascii-only kebab.
        self.assertEqual(slug, "game-dev-hex-grid-prototype")

    def test_slug_path_uses_date_prefix(self):
        slug_path = ps.stub_path(
            content_root=self.tmp / "content",
            title="X y z",
            started_at_iso="2026-05-19T14:30:00Z",
        )
        self.assertEqual(
            slug_path,
            self.tmp / "content" / "streams" / "2026-05-19-x-y-z" / "index.md",
        )
```

- [ ] **Step 2: Implement**

Append to `poll_streams.py`:

```python
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = _SLUG_RE.sub("-", s)
    return s.strip("-")


def _date_prefix(started_at_iso: str) -> str:
    """Return YYYY-MM-DD from an RFC3339 / ISO8601 timestamp."""
    # Parse the date portion (first 10 chars) — robust enough for Twitch responses.
    return started_at_iso[:10]


def stub_path(content_root: Path, title: str, started_at_iso: str) -> Path:
    slug = f"{_date_prefix(started_at_iso)}-{slugify(title)}"
    return content_root / "streams" / slug / "index.md"


def write_auto_stub(content_root: Path, title: str, started_at_iso: str) -> Path:
    """Create content/streams/<YYYY-MM-DD>-<slug>/index.md if absent (idempotent).

    Defaults: category=game-dev (user edits post-hoc), archive_status=archived,
    draft=true, platforms=[twitch,youtube], empty vod_url + show notes."""
    path = stub_path(content_root, title, started_at_iso)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_title = title.replace('"', '\\"')
    body = (
        "---\n"
        f'title: "{safe_title}"\n'
        f"date: {started_at_iso}\n"
        "duration: \"\"\n"
        "platforms: [twitch, youtube]\n"
        "vod_url: \"\"\n"
        "twitch_archive_url: \"\"\n"
        "archive_url: \"\"\n"
        "archive_status: archived\n"
        "category: game-dev\n"
        "tags: []\n"
        "summary: \"\"\n"
        "related_essays: []\n"
        "related_garden: []\n"
        "related_research: []\n"
        "related_works: []\n"
        "draft: true\n"
        "---\n"
        "\n"
        "Show notes — fill in.\n"
    )
    path.write_text(body)
    return path
```

- [ ] **Step 3: Run tests; expect all pass**

Run: `python3 -m unittest tools/test_poll_streams.py -v 2>&1 | tail -10`
Expected: 12/12 pass.

- [ ] **Step 4: Commit**

```bash
git add tools/poll_streams.py tools/test_poll_streams.py
git commit -m "poll(streams): slugify + auto-stub writer (idempotent)

Stub defaults match spec §5: category=game-dev (user edits),
archive_status=archived, draft=true, empty vod_url + related_*.
Date-prefixed slug keeps file listing chronological. Idempotent —
never overwrites a hand-edited stub.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Sub-task 34E: Live-state yaml IO + transition detection

- [ ] **Step 1: Write failing tests**

Append:

```python
class LiveStateIOTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_write_live_yaml(self):
        twitch = {"is_live": True, "title": "x", "started_at": "2026-04-10T19:00:00Z", "url": "https://twitch.tv/x"}
        youtube = {"is_live": True, "video_id": "abc", "title": "x", "started_at": "2026-04-10T19:00:00Z", "url": "https://www.youtube.com/watch?v=abc"}
        ps.write_live_yaml(self.tmp / "data" / "streams-live.yaml",
                           polled_at="2026-04-10T19:00:30Z",
                           twitch=twitch, youtube=youtube)
        text = (self.tmp / "data" / "streams-live.yaml").read_text()
        self.assertIn("last_polled: 2026-04-10T19:00:30Z", text)
        self.assertIn("is_live: true", text)
        self.assertIn("video_id: abc", text)

    def test_read_prior_live_yaml(self):
        d = self.tmp / "data"
        d.mkdir()
        (d / "streams-live.yaml").write_text(
            "last_polled: 2026-04-10T18:55:00Z\n"
            "live:\n"
            "  twitch:\n"
            "    is_live: true\n"
            "    title: \"prior session\"\n"
            "    started_at: \"2026-04-10T18:00:00Z\"\n"
            "    url: \"https://twitch.tv/x\"\n"
            "  youtube:\n"
            "    is_live: false\n"
            "    video_id: \"\"\n"
            "    title: \"\"\n"
            "    started_at: \"\"\n"
            "    url: \"\"\n"
        )
        prior = ps.read_live_yaml(d / "streams-live.yaml")
        self.assertTrue(prior["twitch"]["is_live"])
        self.assertEqual(prior["twitch"]["title"], "prior session")
        self.assertFalse(prior["youtube"]["is_live"])

    def test_read_missing_returns_default_not_live(self):
        prior = ps.read_live_yaml(self.tmp / "absent.yaml")
        self.assertFalse(prior["twitch"]["is_live"])
        self.assertFalse(prior["youtube"]["is_live"])
```

- [ ] **Step 2: Implement**

Append:

```python
def write_live_yaml(path: Path, polled_at: str, twitch: dict, youtube: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml = (
        f"last_polled: {polled_at}\n"
        "live:\n"
        "  twitch:\n"
        f"    is_live: {'true' if twitch['is_live'] else 'false'}\n"
        f"    title: {json.dumps(twitch.get('title', ''))}\n"
        f"    started_at: {json.dumps(twitch.get('started_at', ''))}\n"
        f"    url: {json.dumps(twitch.get('url', ''))}\n"
        "  youtube:\n"
        f"    is_live: {'true' if youtube['is_live'] else 'false'}\n"
        f"    video_id: {json.dumps(youtube.get('video_id', ''))}\n"
        f"    title: {json.dumps(youtube.get('title', ''))}\n"
        f"    started_at: {json.dumps(youtube.get('started_at', ''))}\n"
        f"    url: {json.dumps(youtube.get('url', ''))}\n"
    )
    path.write_text(yaml)


_BOOL_RE = re.compile(r"is_live:\s*(true|false)", re.IGNORECASE)
_QUOTED_RE = re.compile(r'^\s*(\w+):\s*"([^"]*)"\s*$')


def read_live_yaml(path: Path) -> dict:
    """Best-effort stdlib YAML read. Returns
    {twitch:{is_live,title,started_at,url}, youtube:{is_live,video_id,title,started_at,url}}."""
    default = {
        "twitch":  {"is_live": False, "title": "", "started_at": "", "url": ""},
        "youtube": {"is_live": False, "video_id": "", "title": "", "started_at": "", "url": ""},
    }
    if not path.exists():
        return default
    text = path.read_text()
    out = default
    section = None
    for raw in text.splitlines():
        s = raw.strip()
        if s == "twitch:":
            section = "twitch"
            continue
        if s == "youtube:":
            section = "youtube"
            continue
        if section is None:
            continue
        if s.startswith("is_live:"):
            m = _BOOL_RE.search(s)
            out[section]["is_live"] = bool(m and m.group(1).lower() == "true")
            continue
        m = _QUOTED_RE.match(raw)
        if m:
            k, v = m.group(1), m.group(2)
            if k in out[section]:
                out[section][k] = v
    return out
```

- [ ] **Step 3: Run; expect pass**

Run: `python3 -m unittest tools/test_poll_streams.py -v 2>&1 | tail -10`
Expected: 15/15 pass.

- [ ] **Step 4: Commit**

```bash
git add tools/poll_streams.py tools/test_poll_streams.py
git commit -m "poll(streams): write/read streams-live.yaml (stdlib YAML)

Narrow stdlib YAML emitter + reader (handles the keys we own; not
a general-purpose YAML lib). read_live_yaml returns a not-live default
on missing file so the cron-Action's first run is clean.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Sub-task 34F: `main()` orchestrator

- [ ] **Step 1: Write failing test**

Append:

```python
class MainOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "data").mkdir()
        (self.tmp / "content").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    @patch("poll_streams.youtube_is_live")
    @patch("poll_streams.twitch_live_state")
    @patch("poll_streams.twitch_oauth")
    def test_live_to_not_live_writes_stub(self, mock_oauth, mock_tw, mock_yt):
        # Seed prior state: Twitch was live, with a title and started_at.
        (self.tmp / "data" / "streams-live.yaml").write_text(
            "last_polled: 2026-04-10T18:55:00Z\n"
            "live:\n"
            "  twitch:\n"
            "    is_live: true\n"
            '    title: "Example live coding stream"\n'
            '    started_at: "2026-04-10T18:00:00Z"\n'
            '    url: "https://twitch.tv/x"\n'
            "  youtube:\n"
            "    is_live: false\n"
            '    video_id: ""\n'
            '    title: ""\n'
            '    started_at: ""\n'
            '    url: ""\n'
        )
        mock_oauth.return_value = "tok"
        mock_tw.return_value = {"is_live": False, "title": "", "started_at": "", "url": ""}
        mock_yt.return_value = False
        env = {
            "TWITCH_CLIENT_ID": "cid",
            "TWITCH_CLIENT_SECRET": "csec",
            "TWITCH_USER_LOGIN": "x",
            "YOUTUBE_CHANNEL_ID": "UC-y",
            "YOUTUBE_API_KEY": "yk",  # unused but tolerated
        }
        rc = ps.main(repo_root=self.tmp, env=env, now_iso="2026-04-10T19:30:00Z")
        self.assertEqual(rc, 0)
        # A stub should have been created from the prior live state's title + started_at.
        stub = self.tmp / "content" / "streams" / "2026-04-10-example-live-coding-stream" / "index.md"
        self.assertTrue(stub.exists())
        # live.yaml should now reflect not-live.
        text = (self.tmp / "data" / "streams-live.yaml").read_text()
        self.assertIn("is_live: false", text)

    @patch("poll_streams.youtube_is_live")
    @patch("poll_streams.twitch_live_state")
    @patch("poll_streams.twitch_oauth")
    def test_not_live_to_live_no_stub(self, mock_oauth, mock_tw, mock_yt):
        # No prior live yaml → first poll, transition to live.
        mock_oauth.return_value = "tok"
        mock_tw.return_value = {"is_live": True, "title": "fresh", "started_at": "2026-04-10T20:00:00Z", "url": "https://twitch.tv/x"}
        mock_yt.return_value = True
        env = {
            "TWITCH_CLIENT_ID": "cid", "TWITCH_CLIENT_SECRET": "csec",
            "TWITCH_USER_LOGIN": "x", "YOUTUBE_CHANNEL_ID": "UC-y", "YOUTUBE_API_KEY": "yk",
        }
        rc = ps.main(repo_root=self.tmp, env=env, now_iso="2026-04-10T20:01:00Z")
        self.assertEqual(rc, 0)
        # No stubs created on go-live.
        self.assertFalse((self.tmp / "content" / "streams").exists() and any((self.tmp / "content" / "streams").iterdir()))
        text = (self.tmp / "data" / "streams-live.yaml").read_text()
        self.assertIn("is_live: true", text)

    @patch("poll_streams.youtube_is_live")
    @patch("poll_streams.twitch_live_state", side_effect=Exception("transient!"))
    @patch("poll_streams.twitch_oauth")
    def test_transient_api_failure_exits_0(self, mock_oauth, mock_tw, mock_yt):
        mock_oauth.return_value = "tok"
        mock_yt.return_value = False
        env = {
            "TWITCH_CLIENT_ID": "cid", "TWITCH_CLIENT_SECRET": "csec",
            "TWITCH_USER_LOGIN": "x", "YOUTUBE_CHANNEL_ID": "UC-y", "YOUTUBE_API_KEY": "yk",
        }
        rc = ps.main(repo_root=self.tmp, env=env, now_iso="2026-04-10T20:01:00Z")
        self.assertEqual(rc, 0)

    def test_missing_secret_exits_nonzero(self):
        rc = ps.main(repo_root=self.tmp, env={}, now_iso="2026-04-10T20:01:00Z")
        self.assertNotEqual(rc, 0)
```

- [ ] **Step 2: Implement `main()`**

Replace the placeholder `if __name__ ==` block at the bottom of `poll_streams.py` with:

```python
REQUIRED_ENV = ("TWITCH_CLIENT_ID", "TWITCH_CLIENT_SECRET", "TWITCH_USER_LOGIN", "YOUTUBE_CHANNEL_ID")


def main(repo_root: Path | None = None, env: dict | None = None, now_iso: str | None = None) -> int:
    repo_root = repo_root or Path(__file__).resolve().parent.parent
    env = env if env is not None else os.environ
    now_iso = now_iso or dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    missing = [k for k in REQUIRED_ENV if not env.get(k)]
    if missing:
        print(f"poll_streams: missing required env: {missing}", file=sys.stderr)
        return 2

    live_yaml = repo_root / "data" / "streams-live.yaml"
    prior = read_live_yaml(live_yaml)

    # --- Twitch ---
    twitch_state = {"is_live": False, "title": "", "started_at": "", "url": ""}
    try:
        token = twitch_oauth(env["TWITCH_CLIENT_ID"], env["TWITCH_CLIENT_SECRET"])
        twitch_state = twitch_live_state(token, env["TWITCH_CLIENT_ID"], env["TWITCH_USER_LOGIN"])
    except PollError as e:
        print(f"poll_streams: twitch error (non-fatal): {e}", file=sys.stderr)
        twitch_state = prior["twitch"]   # preserve prior state on auth blip
    except Exception as e:  # noqa: BLE001 — transient HTTP, DNS, etc.
        print(f"poll_streams: twitch transient: {e}", file=sys.stderr)
        twitch_state = prior["twitch"]

    # --- YouTube ---
    yt_is_live = False
    try:
        yt_is_live = youtube_is_live(env["YOUTUBE_CHANNEL_ID"])
    except Exception as e:  # noqa: BLE001
        print(f"poll_streams: youtube transient: {e}", file=sys.stderr)
        yt_is_live = prior["youtube"]["is_live"]
    youtube_state = {
        "is_live": yt_is_live,
        "video_id": prior["youtube"]["video_id"] if yt_is_live else "",
        "title": prior["youtube"]["title"] if yt_is_live else "",
        "started_at": prior["youtube"]["started_at"] if yt_is_live else "",
        "url": f"https://www.youtube.com/channel/{env['YOUTUBE_CHANNEL_ID']}/live" if yt_is_live else "",
    }

    # --- Transition: live → not-live on Twitch ⇒ auto-stub from prior state ---
    if prior["twitch"]["is_live"] and not twitch_state["is_live"]:
        title = prior["twitch"]["title"] or "Untitled stream"
        started = prior["twitch"]["started_at"] or now_iso
        try:
            write_auto_stub(repo_root / "content", title, started)
        except Exception as e:  # noqa: BLE001
            print(f"poll_streams: stub write failed (non-fatal): {e}", file=sys.stderr)

    write_live_yaml(live_yaml, polled_at=now_iso,
                    twitch=twitch_state, youtube=youtube_state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run all poller tests**

Run: `python3 -m unittest tools/test_poll_streams.py -v 2>&1 | tail -15`
Expected: 19/19 pass.

- [ ] **Step 4: Commit**

```bash
git add tools/poll_streams.py tools/test_poll_streams.py
git commit -m "poll(streams): main() orchestrator + transition stub-write

Twitch + YouTube polled; transient errors preserve prior state and
exit 0; missing required env exits 2. Live→not-live transition on
Twitch writes an auto-stub from the prior state's title+started_at.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

(Spec §5 step 4 — hourly Twitch /helix/schedule poll → `data/streams-twitch-cache.yaml` — is intentionally deferred to a follow-up: the manual `data/streams-schedule.yaml` covers all current UX needs; the schedule cache is an "if entries aren't manually scheduled" fallback. File a follow-up if/when the user wants it.)

---

## Task 35: `.github/workflows/streams-poll.yaml`

**Files:**
- Create: `.github/workflows/streams-poll.yaml`

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/streams-poll.yaml`:

```yaml
name: streams poll

on:
  schedule:
    - cron: '*/5 * * * *'     # every 5 min (GitHub's minimum)
  workflow_dispatch:           # manual trigger for bootstrap + ad-hoc testing

permissions:
  contents: write              # to commit polled data + auto-stubs

concurrency:
  group: streams-poll
  cancel-in-progress: false    # let any in-flight run finish before starting the next

jobs:
  poll:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 1
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - name: Run poller unit tests (regression guard)
        run: python3 -m unittest tools/test_poll_streams.py -v
      - name: Poll streams
        env:
          TWITCH_CLIENT_ID:     ${{ secrets.TWITCH_CLIENT_ID }}
          TWITCH_CLIENT_SECRET: ${{ secrets.TWITCH_CLIENT_SECRET }}
          YOUTUBE_API_KEY:      ${{ secrets.YOUTUBE_API_KEY }}
          TWITCH_USER_LOGIN:    ${{ vars.TWITCH_USER_LOGIN }}
          YOUTUBE_CHANNEL_ID:   ${{ vars.YOUTUBE_CHANNEL_ID }}
        run: python3 tools/poll_streams.py
      - name: Commit if changed
        run: |
          git config user.name  "streams-poll-bot"
          git config user.email "noreply@github.com"
          if git status --porcelain | grep -q .; then
            git add data/streams-live.yaml data/streams-twitch-cache.yaml content/streams/
            git commit -m "chore(streams): poll @ $(date -u +%FT%TZ)"
            git pull --rebase origin master
            git push origin master
          fi
```

- [ ] **Step 2: User-side bootstrap (post-merge)**

ASK USER: "After merge, set the four required pieces in repo Settings → Secrets and variables → Actions:

- **Secret** `TWITCH_CLIENT_ID` (from https://dev.twitch.tv/console/apps)
- **Secret** `TWITCH_CLIENT_SECRET` (same)
- **Secret** `YOUTUBE_API_KEY` (https://console.cloud.google.com — Data API v3 enabled; currently unused by hot path but reserved per spec §15)
- **Variable** `TWITCH_USER_LOGIN` (e.g. `a3madkour`)
- **Variable** `YOUTUBE_CHANNEL_ID` (e.g. `UCxxxxxxxx`)

Then trigger `workflow_dispatch` manually once to verify the first end-to-end run before relying on cron. The job should: run unit tests (green) → poll (write data/streams-live.yaml if not yet present) → either commit & push or no-op."

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/streams-poll.yaml
git commit -m "ci(streams): cron workflow — */5min poll + commit/push

Includes a pre-poll unit-test step as a regression guard. Concurrency
group serialized; transient API failures silently 0-exit (poller side).
User bootstraps Twitch + YouTube secrets/vars post-merge.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

# Phase 12 — Docs + verification

## Task 36: CLAUDE.md updates

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update linter-pair count + names (line ~14)**

In `CLAUDE.md`, find:

```
- Twenty-one linter pairs under `tools/check_*.py` + `tools/test_check_*.py` (CI runs each linter then its unit-test sibling): essay fixtures, essay TOC depth, garden fixtures, garden links, filter-chips config, research fixtures, research links, citations, works fixtures, works links, synced poetry, library fixtures, library links, library covers, library shelves, icon attribution, RSS XSL, garden history, pagefind metadata, cite metadata, page weights. `tools/check_smoke.py` and `tools/check_graph_chrome.py` are sibling-less linters (no paired test file — spec §3.1: logic is too thin to warrant pairing).
```

Replace with:

```
- Twenty-three linter pairs under `tools/check_*.py` + `tools/test_check_*.py` (CI runs each linter then its unit-test sibling): essay fixtures, essay TOC depth, garden fixtures, garden links, filter-chips config, research fixtures, research links, citations, works fixtures, works links, synced poetry, library fixtures, library links, library covers, library shelves, icon attribution, RSS XSL, garden history, streams fixtures, streams links, pagefind metadata, cite metadata, page weights. `tools/check_smoke.py` and `tools/check_graph_chrome.py` are sibling-less linters (no paired test file — spec §3.1: logic is too thin to warrant pairing).
```

- [ ] **Step 2: Update CI step count (line ~152)**

Find:

```
`.github/workflows/hugo.yaml` builds with Hugo extended and deploys `public/` to GitHub Pages on pushes to `master`. CI step order: pre-build linters (contrast + 21 linter pairs + 1 sibling-less = 44 steps) → `hugo --minify` → pagefind metadata linter unit tests → verify pagefind metadata on built pages → cite metadata linter unit tests → verify cite metadata on built pages → install Pagefind 1.5.2 binary → build Pagefind index into `public/pagefind/` → smoke test → page-weight linter + unit tests → Lighthouse CI desktop (2 steps: `lighthouserc.json`) → Lighthouse CI mobile (`lighthouserc.mobile.json`) → upload artifact → deploy. Total: 55 named steps.
```

Replace with:

```
`.github/workflows/hugo.yaml` builds with Hugo extended and deploys `public/` to GitHub Pages on pushes to `master`. CI step order: pre-build linters (contrast + 23 linter pairs + 1 sibling-less = 48 steps) → `hugo --minify` → pagefind metadata linter unit tests → verify pagefind metadata on built pages → cite metadata linter unit tests → verify cite metadata on built pages → install Pagefind 1.5.2 binary → build Pagefind index into `public/pagefind/` → smoke test → page-weight linter + unit tests → Lighthouse CI desktop (2 steps: `lighthouserc.json`) → Lighthouse CI mobile (`lighthouserc.mobile.json`) → upload artifact → deploy. Total: 59 named steps.
```

(A separate cron workflow `.github/workflows/streams-poll.yaml` runs every 5 minutes — outside this build/deploy pipeline.)

- [ ] **Step 3: Update JS bundle count + add entry-streams row**

Find the JS pipeline table. The current intro says "ten times". Update to "eleven times" and add the row. Locate:

```
`layouts/partials/scripts.html` runs Hugo's `js.Build` (esbuild) ten times — minified + fingerprinted, classic-script with SRI:
```

Replace with:

```
`layouts/partials/scripts.html` runs Hugo's `js.Build` (esbuild) eleven times — minified + fingerprinted, classic-script with SRI:
```

Find the last row in the table (the poetry row):

```
| `js/entry-poetry.js` | `poetry.<hash>.js` (~4 KB) | `.Section == "works"` AND `.Kind == "page"` AND `.Type == "works-poetry"` | `poem-synced.js` — synced-reveal runtime; JS-built player |
```

Append immediately after:

```
| `js/entry-streams.js` | `streams.<hash>.js` (~1 KB) | `.Section == "streams"` AND `.Kind == "page"` | `streams.js` — click-to-load YouTube embed |
```

- [ ] **Step 4: Update top-nav locked statement**

Find:

```
- **Top nav** (locked): Essays / Garden / Research / Works / Library / About. Active item gets `aria-current="page"` via `hasPrefix` match.
```

Replace with:

```
- **Top nav** (locked): Essays / Garden / Research / Works / Library / Streams / About. Active item gets `aria-current="page"` via `hasPrefix` match. (Streams added 2026-05-19; was previously 6 items.)
```

- [ ] **Step 5: Add §46 to the CSS section reference**

Find:

```
`assets/css/main.css` is a single hand-rolled stylesheet, organized into numbered sections §1–§45 (see the file's top-of-file index for the list; §32–§36 are reserved for past works-section additions that landed without numbered headers; §38–§40 cover the homepage hero, Currently widget, and homepage strips; §41 covers the cross-template page sidebar; §42 covers the search modal; §43 covers citation export; §44 covers the library umbrella redesign — hero + themed shelves + bottom catalogue; §45 covers the synced-poetry runtime (reveal opacity/flourish + JS-built player chrome)).
```

Replace with:

```
`assets/css/main.css` is a single hand-rolled stylesheet, organized into numbered sections §1–§46 (see the file's top-of-file index for the list; §32–§36 are reserved for past works-section additions that landed without numbered headers; §38–§40 cover the homepage hero, Currently widget, and homepage strips; §41 covers the cross-template page sidebar; §42 covers the search modal; §43 covers citation export; §44 covers the library umbrella redesign — hero + themed shelves + bottom catalogue; §45 covers the synced-poetry runtime (reveal opacity/flourish + JS-built player chrome); §46 covers the streams section — header live-pill, click-to-load YouTube embed, archive grid, upcoming strip, cross-section from-stream attribution, category pill palette).
```

- [ ] **Step 6: Add Pagefind meta-keys row for streams**

Find the Pagefind meta-keys table. Append a row:

```
| Streams | `streams` | `category`, `archive_status` |
```

(Place it after the Library leaves row, before the About / Home / Blog row.)

- [ ] **Step 7: Promote streams from "Designed but not yet implemented" → "Shipped"**

In the project status section, find the "Designed but not yet implemented" table and remove the Streams row:

```
| Streams section | Independent (β parallel with Phase 3 or γ after) | New 7th top-level `/streams/`; cron GitHub Action polls Twitch + YouTube. Bidirectional cross-refs (2 new linter pairs). |
```

Delete that row.

In the "Shipped" line at the top of the project status section, mention the streams slice. Find:

```
**Shipped**: Phases 0–8 (modulo interactive QA walkthrough) plus Citation export + Library redesign + Graph-view chrome-consistency + Persistent-graph-access + TOC collapsible subsections + Time-synced poetry polish slices.
```

Replace with:

```
**Shipped**: Phases 0–8 (modulo interactive QA walkthrough) plus Citation export + Library redesign + Graph-view chrome-consistency + Persistent-graph-access + TOC collapsible subsections + Time-synced poetry + Streams section slices.
```

- [ ] **Step 8: Verify the per-section frontmatter contract gets a Streams paragraph**

Append to the "Frontmatter contracts" section:

```

**Streams** (`content/streams/<YYYY-MM-DD>-<slug>/index.md`) — enforced by `tools/check_streams_fixtures.py`. Required: `title, date, platforms, category, archive_status, draft`. Optional: `duration, vod_url, twitch_archive_url, archive_url, tags, summary, related_essays, related_garden, related_research, related_works`. `platforms` ⊆ `{twitch, youtube}`. `category` ∈ `{game-dev, research, coding, creative}`. `archive_status` ∈ `{live, archived, removed, private}`. Cross-val: `archive_status == archived` ⇒ `vod_url` non-empty. Bidirectional symmetry `related_* ↔ source_stream` enforced by `tools/check_streams_links.py` (the 23rd linter pair). Live state + schedule cache: `data/streams-live.yaml` / `data/streams-schedule.yaml` / `data/streams-twitch-cache.yaml` — shape-validated by the same fixtures linter.
```

- [ ] **Step 9: Add streams to the data-access gotcha list**

In the "Hugo project structure" / Data section (find the "Read the data file via `index site.Data ...`" note), add a reminder:

```
- `data/streams-*.yaml` filenames are hyphenated — `site.Data.streams-live` etc. would silently break. Read via `index site.Data "streams-live"`.
```

(If a sub-bullet list of such examples already exists, append; otherwise add a brief sentence near the existing filter-chips note.)

- [ ] **Step 10: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): register streams slice — counts, nav, §46, contract

21→23 linter pairs · 55→59 CI steps · 10→11 JS entries · nav 6→7
locked · CSS §46 · streams frontmatter contract paragraph · pagefind
meta row · data-access reminder.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 37: Pre-merge verification — run all linters end-to-end

The agent CANNOT run Hugo/LHCI in this sandbox; this task runs every linter that DOES execute here, plus calls out the user-side checks before merge.

- [ ] **Step 1: Run every pre-build linter (in the order CI does)**

```bash
python3 tools/check-contrast.py
python3 tools/check_fixtures.py
python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -3
python3 tools/check_toc_depth.py
python3 -m unittest tools/test_check_toc_depth.py -v 2>&1 | tail -3
python3 tools/check_garden_fixtures.py
python3 -m unittest tools/test_check_garden_fixtures.py -v 2>&1 | tail -3
python3 tools/check_garden_links.py
python3 -m unittest tools/test_check_garden_links.py -v 2>&1 | tail -3
python3 tools/check_filter_chips_config.py
python3 -m unittest tools/test_check_filter_chips_config.py -v 2>&1 | tail -3
python3 tools/check_research_fixtures.py
python3 -m unittest tools/test_check_research_fixtures.py -v 2>&1 | tail -3
python3 tools/check_research_links.py
python3 -m unittest tools/test_check_research_links.py -v 2>&1 | tail -3
python3 tools/check_citations.py
python3 -m unittest tools/test_check_citations.py -v 2>&1 | tail -3
python3 tools/check_works_fixtures.py
python3 -m unittest tools/test_check_works_fixtures.py -v 2>&1 | tail -3
python3 tools/check_works_links.py
python3 -m unittest tools/test_check_works_links.py -v 2>&1 | tail -3
python3 tools/check_poetry_synced.py
python3 -m unittest tools/test_check_poetry_synced.py -v 2>&1 | tail -3
python3 tools/check_library_fixtures.py
python3 -m unittest tools/test_check_library_fixtures.py -v 2>&1 | tail -3
python3 tools/check_library_links.py
python3 -m unittest tools/test_check_library_links.py -v 2>&1 | tail -3
python3 tools/check_library_covers.py
python3 -m unittest tools/test_check_library_covers.py -v 2>&1 | tail -3
python3 tools/check_icon_attribution.py
python3 -m unittest tools/test_check_icon_attribution.py -v 2>&1 | tail -3
python3 tools/check_library_shelves.py
python3 -m unittest tools/test_check_library_shelves.py -v 2>&1 | tail -3
python3 tools/check_rss_xsl.py
python3 -m unittest tools/test_check_rss_xsl.py -v 2>&1 | tail -3
python3 tools/check_garden_history.py
python3 -m unittest tools/test_check_garden_history.py -v 2>&1 | tail -3
python3 tools/check_streams_fixtures.py
python3 -m unittest tools/test_check_streams_fixtures.py -v 2>&1 | tail -3
python3 tools/check_streams_links.py
python3 -m unittest tools/test_check_streams_links.py -v 2>&1 | tail -3
python3 tools/check_graph_chrome.py
python3 -m unittest tools/test_poll_streams.py -v 2>&1 | tail -3
```

Expected: every line green (no failures, all OK messages).

- [ ] **Step 2: User-side dev-server visual walkthrough**

ASK USER: "Start `hugo server --buildDrafts -s /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io` from a clean tree (no `public/`/`resources/` from a prior `--minify` run). Walk the following at breakpoints 360 / 768 / 960 / 1280:

1. **Header on every page**: 7 nav items including Streams between Library and About. No LIVE pill (yaml not-live). Tweak `data/streams-live.yaml` `twitch.is_live: true` + `twitch.url: https://twitch.tv/x` → pill appears red-pulsing, links to Twitch. Revert yaml.
2. **`/`**: 5 page-sidebar dots (Currently / Essays / Research / Works / Streams). Streams strip renders 2 upcoming entries from `data/streams-schedule.yaml`, sorted asc, no `→` arrows on the 'All streams' link.
3. **`/streams/`**: hero header + upcoming strip + filter chips (category + tag; year suppressed since both fixtures are 2026) + 2-card archive grid in 1col/2col/3col responsive.
4. **`/streams/2026-04-10-example-live-coding-stream/`**: archive_status=archived → click-to-load YT thumbnail with red play button, click loads iframe to youtube-nocookie.com/embed/dQw4w9WgXcQ. Cite CTA above embed. Cross-refs section lists game + research-question + garden note (3 groups, each with 1 entry). All cross-ref links resolve.
5. **`/streams/2026-04-22-example-music-jam-stream/`**: archive_status=removed → no embed; 'Archive intentionally removed' callout. Cross-refs lists music + poem + essay. Cite still emits.
6. **Six existing fixture pages with `source_stream`**: `/essays/example-essay-one/`, `/garden/story-atoms/`, `/works/games/example-playable-full-release/`, `/works/music/example-live-session/`, `/works/poetry/example-poem-collected/`, `/research/questions/what-is-a-narrative-atom/` — each shows 'From the stream: <YYYY-MM-DD> — <title>' attribution between header and body. Link resolves to the stream page.
7. **Search modal (`/`)**: Streams chip present between Library and About. Type `example` → results include both stream fixtures (and they have proper titles + URLs).
8. **Citation modal on `/streams/2026-04-10-...`**: Cite this stream button opens modal. BibTeX format includes `note = {Live stream broadcast, 2026-04-10, archived on YouTube}` and `type = misc`. APA/Chicago/MLA/RIS all populate. The 'removed' stream's BibTeX uses `...archive intentionally removed`.
9. **Dark mode**: toggle theme and re-walk steps 2-8 — colours unchanged (no new tokens), card borders + pill colours legible.
10. **Reduced-motion**: enable OS prefer-reduced-motion → LIVE pill dot no longer pulses (static).

Report any visual regressions or unexpected layouts."

- [ ] **Step 3: User-side CI verification (post-merge — informational, not a blocker for this plan task)**

ASK USER: "After merge to master, the build CI runs the 59-step pipeline. Watch the Actions tab. Expected new steps in the Verify-blocks: streams fixtures + streams links + their unit-test siblings (4 new green checks)."

- [ ] **Step 4: Commit nothing — Task 37 is a verification gate, not a code change**

If all linters green + user spot-check returns no regressions, proceed to the finishing step (next).

---

# Finishing the slice

## Task 38: Final review + merge prep

- [ ] **Step 1: Diff against master for a structural review**

```bash
git diff --stat master...HEAD
git log --oneline master...HEAD
```

Expected: ~38 commits (one per task above, plus the spec-reconciliation commit `2a0ce4b`).

- [ ] **Step 2: Run a final whole-branch review via `superpowers:requesting-code-review`**

Per memory `project_time_synced_poetry_slice` lesson: "the final whole-branch review caught cross-cutting bugs per-task reviews structurally could not." Dispatch a fresh subagent.

- [ ] **Step 3: Address review findings if any (amend commits, NOT new fixup commits — keep the branch readable)**

- [ ] **Step 4: Offer the user a final dev-server spot-check (per memory `feedback_verify_before_merge`)**

ASK USER: "Final spot-check pass on the dev server before I merge? I'll wait for explicit go-ahead."

- [ ] **Step 5: Merge `feature/streams-section` → master with `--no-ff` + push**

```bash
git checkout master
git merge --no-ff feature/streams-section -m "Merge branch 'feature/streams-section'"
git push origin master
git branch -d feature/streams-section
```

- [ ] **Step 6: Save the slice memory**

Create `/home/a3madkour/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/project_streams_section_slice.md`:

```markdown
---
name: project-streams-section-slice
description: "Streams section slice — shipped"
metadata:
  type: project
---

**Shipped <YYYY-MM-DD>.** Merge `<hash>` (`--no-ff` `Merge branch 'feature/streams-section'`), pushed.

New 7th top-level `/streams/`: archive pages with click-to-load YT embeds, bidirectional cross-refs (`related_* ↔ source_stream`) to essays/garden/research/works, header live-pill driven by cron-polled `data/streams-live.yaml`, homepage upcoming-streams strip. Cron workflow `.github/workflows/streams-poll.yaml` runs `tools/poll_streams.py` every 5 min (Twitch OAuth + YouTube HEAD probe + auto-stub creation on live→not-live transition). 22nd + 23rd linter pairs: `check_streams_fixtures` + `check_streams_links`. CSS §46. 11th JS entry `entry-streams.js`. Cite integration per spec §10 (archived/removed only).

Hard-won (don't regress):
- Hyphenated data files require `index site.Data "streams-live"` (memory `reference_hugo_jsonify_safejs` family of gotchas).
- archive_status=live emits NO cite scaffolding (gated in triplicated `$citable_sections` predicate), so check_cite_meta doesn't audit live pages.
- streams pages opt OUT of `page-sidebar.html` (single-section).
- User bootstraps Twitch + YouTube secrets/vars (post-merge) to activate the cron path.

Specs: `docs/superpowers/specs/2026-05-13-streams-section-design.md` + §0 reconciliation 2026-05-19.
Plan: `docs/superpowers/plans/2026-05-19-streams-section.md`.
```

Add to `MEMORY.md`:

```
- [Streams section slice — shipped](project_streams_section_slice.md) — <YYYY-MM-DD>; 22nd/23rd linter pairs + cron poller + CSS §46
```

- [ ] **Step 7: Update `project_next_slice.md` memory**

Edit `project_next_slice.md` to reflect new state: streams shipped; next remains Phase 3 Slice 1 garden publish (org-mode pipeline) per CLAUDE.md sequencing.

- [ ] **Step 8: Final commit message log review**

`git log --oneline master | head -45` — visually confirm the new commits read cleanly.

---

# Self-review

After all 38 tasks above land:

**Spec coverage matrix (every section of the streams spec maps to a task):**

| Spec section | Implemented in task(s) |
|---|---|
| §0 Reconciliation (decisions + staleness) | Pre-plan commit `2a0ce4b` + Task 16 (button) + Task 17 (predicate) + Task 32 (CSS §46) + Task 36 (CLAUDE.md) |
| §1 Scope (4 categories, 2 platforms, workflow) | Tasks 9 (fixtures) + 34 (poller) |
| §2 Architecture — Approach A | Task 34 (poller) + 35 (workflow) |
| §3 Data files (schedule/cache/live + merge logic) | Tasks 10 + 22 |
| §4 Frontmatter + cross-section additions | Tasks 9 (streams fm) + 11 (source_stream back-edges) + 27 (from-stream renders) |
| §5 GitHub Action workflow | Task 35 |
| §6 Hugo templates + partials | Tasks 18–25 + 26 (header) + 27 (cross-section) + 28–29 (homepage) |
| §7 CSS §44 (corrected to §46) | Task 32 |
| §8 JS runtime + entry | Task 30 + 31 |
| §9 Two new linter pairs | Tasks 12 + 13 + 14 |
| §10 Citation export (per archive_status) | Tasks 15 (normalize) + 16 (button label) + 17 (predicate) + 6 (cite_meta) + 13 (NON_CITABLE_EXACT) |
| §11 Pagefind + RSS-SUPERSEDED + filter chips | Tasks 5 (pagefind) + 24 (list filter chips) + 33 (search-modal); RSS intentionally omitted per §0 |
| §12 CI workflow growth | Task 14 + 36 |
| §13 Page weight tier | Task 7 |
| §14 Frontmatter additions summary | Tasks 1–4 (linters accept) + 11 (real fixtures) |
| §15 Out of scope | Documented; nothing built |
| §16 Phase placement | This whole plan |

No gaps.

**Placeholder scan:** none. Every step has exact paths, exact code, exact commands.

**Type / name consistency check:** verified — `check_streams_fixtures` / `check_streams_links` names used consistently across hugo.yaml, ci-local.sh, CLAUDE.md update, slice memory. The shared `partials/streams/from-stream.html` is referenced by all 7 single-template tasks under the same path. Citable predicate updates (Task 17) use identical wording in all three files.

**Internal contradiction sweep:** the §11 RSS-superseded decision in spec §0 is honored — Task 24 (list.html) does NOT emit RSS scaffolding, no `layouts/streams/rss.xml` is created, and the workflow's RSS-XSL linter is untouched (it already auto-skips sections without RSS).

---

# Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-19-streams-section.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, two-stage review (spec-conformance + code-quality) between tasks, frequent commits. Memory `project_time_synced_poetry_slice` records this workflow shipped well for the prior big slice + that the final whole-branch review caught cross-cutting bugs per-task reviews missed. Best fit here given the 38-task scope and the cite-predicate triplet pattern that benefits from a fresh reviewer eye.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints for review.

**Which approach?**




