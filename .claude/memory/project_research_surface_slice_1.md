---
name: Research surface (Slice 1) — merged
description: Phase 5 first slice (index + theme + question layouts + cross-refs + 2 linters) shipped to master 2026-05-11 (merge 0ac950c, pushed). Graph runtime deferred to Slice 2.
type: project
originSessionId: cfd5e26b-590f-4577-aed6-8c8b9f757692
---
**Status:** MERGED + PUSHED on 2026-05-11. Merge commit `0ac950c`. Branch `research-surface` deleted.

**What shipped (17 atomic commits):**
- `cdaeb1d` `check_research_fixtures.py` — frontmatter contract linter (status/output-kind enums, required/optional/forbidden fields).
- `fa0ac14` Parser extension in `tools/check_fixtures.py` to handle YAML block sequences with flow-style mapping items (`outputs: \n  - { kind: paper, ... }`). Additive — all 53 existing tests still pass. Also lands `test_check_research_fixtures.py` (10 cases).
- `7083f1d` `check_research_links.py` — cross-reference linter (garden_topic_ref → garden topic-map note, theme → theme, parent_question → same-theme question, supporting_notes → garden, related_essays → essays).
- `2dedcda` `test_check_research_links.py` (8 cases).
- `d35e197` Section scaffolding: `content/research/_index.md` replaces "Coming soon"; `themes/_index.md` + `questions/_index.md` set type via cascade and hide bare URLs with `build: render: never`. (Note: Hugo 0.145+ deprecated `_build` → `build`.)
- `2fc3983` 3 theme fixtures (memory-and-play, procedural-narrative, save-game-as-form). 2 with garden_topic_ref, 1 without; all 3 statuses.
- `5e5e7c3` 6 question fixtures across the 3 themes. All variants exercised.
- `b156301` 3 hand-authored output SVG icons (paper, talk, code).
- `c97381f` + `30f93be` + `5749c83` Four partials: status-pill, output-item, theme-card, backlinks-data.
- `0a14190` `/research/` index layout + section `build:` rename.
- `1342341` `/research/themes/<slug>/` theme page layout.
- `f6153cd` `/research/questions/<slug>/` question hub layout (full spec §3.3 sections).
- `580d2af` CSS §30 (~250 lines).
- `fe48542` GitHub Actions: 4 new linter gates (verify counts: 7 verify + 6 unit-test suites = 13 Python checks total).
- `fe46844` CLAUDE.md updates.

**Architectural decisions worth remembering:**
- **Type discrimination via cascade** rather than per-page `type:`. `content/research/themes/_index.md` declares `cascade: { type: research-theme }`; question section declares `research-question`. Hugo resolves layouts via type → `layouts/research-theme/single.html` and `layouts/research-question/single.html`. Cleaner than per-page declarations.
- **Hidden section pages**: `build: { render: never, list: never }` on the bare `_index.md`s so `/research/themes/` and `/research/questions/` return 404. Users navigate via /research/ → card → hub, never via bare section URLs.
- **Garden topic re-use**: theme pages with `garden_topic_ref` set call `partial "garden/topic-section.html" (dict "context" $gardenPage)` to render the same tile grid as `/garden/`'s topic sections. Zero duplication of the tile renderer.
- **Backlinks via `partialCached`**: build-time pass over `site.RegularPages` extracts `/research/questions/<slug>/` references with `findRE`, returns a slug → list-of-backlinks map. Same architecture as `garden/graph-data.html`.
- **Block-sequence YAML parser extension**: `tools/check_fixtures.py`'s `parse_frontmatter` was extended to handle `outputs:` followed by indented `- { ... }` items via two new helpers (`_parse_block_item` + `_split_top_commas`). Additive; covered by the new linter tests. If a future slice needs nested block-style mappings, the parser would need further extension.

**Gotcha**: Hugo 0.145+ removed the `_build` frontmatter key. Use `build:` instead. The plan originally specified `_build` (matching older Hugo docs) — caught at first build, fixed inline in commit `0a14190`.

**Dev-server gotcha during verification**: Running `hugo --minify` populates `public/` + `resources/` with minified+fingerprinted output; the running `hugo server` then served from `public/` (HTML referenced fingerprinted CSS like `/css/main.min.<hash>.css`). After clean `rm -rf public resources && hugo server`, the dev server returned to in-memory serving with unfingerprinted `/css/main.css`. Worth knowing for future verification cycles — don't run `hugo --minify` alongside an active dev server unless you intend to test the production build.

**Slice 2 (graph) — known requirements**:
- New `assets/js/research-graph.js` mirroring `garden-graph.js`. Squares for theme nodes, circles for question nodes per parent spec §4.10.
- New `partials/research/graph-data.html` (build-time JSON).
- Multi-entry bundle gets a `research` entry (per the multi-entry pattern in scripts.html).
- "Open graph" toggle button rendered in `layouts/research/list.html`'s filter strip (currently omitted).
- CSS §30 extends with graph-specific rules.

**Pointers:**
- Merge commit: `0ac950c` on master
- Spec: `docs/superpowers/specs/2026-05-11-research-surface-design.md`
- Plan: `docs/superpowers/plans/2026-05-11-research-surface.md`
