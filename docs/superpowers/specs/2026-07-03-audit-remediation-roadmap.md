# Post-Audit Remediation Roadmap

**Date:** 2026-07-03
**Status:** Active. **Tiers R1–R4 closed** 2026-07-03/04 (R1 `8ba3882..2422e81`; R2 `d09d531..f5962ac`; R3 `92a525b..3c3af9e`; R4 `840a20e..6f2f4fb`). **R5.1 closed 2026-07-04** (`e9b6d95..7910371`). **R5.2 closed 2026-07-04** (`d1e214c..d0ee5b0`; graph-core extraction, 2,280→1,316 LOC, also subsumes R3.2's deferred graph-panel reconciliation). R4.3 folded into other rows. **R5.3a closed 2026-07-05** (`3925b6c`; AMS-block consolidation — 11 shortcodes → thin wrappers over `ams-block.html` partial). **R5.3b closed 2026-07-05** (`4775888`; shared `graph-panel.html` partial — 3 per-section wrappers delegate to `layouts/partials/graph-panel.html` (dict params `id`/`title`/`ariaLabel`/`section`); closes R3.2's structural remainder). **Tier R5 CLOSED 2026-07-05** (`6d638d9..48813f0`; R5.4 Python tooling dedup — shared `tools/test_helpers.py`/`TempRepo` adopted by the 5 test files that duplicated it (16 lighter inline-`setUp` tempdir files left, YAGNI), canonical `parse_citations_yaml` in `check_fixtures`, uniform `run() -> (int, list[str])` seam on every linter; item 3 was already-satisfied: only `check_fixtures` defines the frontmatter parser, distinct data-yaml parsers legitimately stay). R6 is optional. Remaining rows ☐ open.

**Why this exists:** A six-lens multi-agent audit (2026-07-03) swept the whole non-elisp codebase — Python tooling (66 files), JS (39 non-vendor), CSS (5.7k lines), Hugo templates (141), CI/CD, and cross-cutting architecture. It surfaced three correctness/security defects that make CI lie or pollute history, one dominant structural pattern ("copy instead of abstract"), one large testing hole (no client-side test layer at all), and a tail of hygiene + doc-drift items. This roadmap files every finding so future sessions can pick up any tier cleanly. It is the source of truth for audit remediation and is durable across CLAUDE.md churn.

**The two systemic stories (context for the whole roadmap):**
1. **Copy-instead-of-abstract is the dominant maintainability risk, and it has begun to rot.** Three graph runtimes share 70–80% of ~2,280 JS LOC; 12 AMS block shortcodes are identical modulo four tokens; the three `graph-panel.html` partials have *already* drifted (`inert` vs `hidden`, `<h3>` vs `<span>`); 22 Python test files re-roll identical scaffolding; `citations.yaml` has two parsers. None of this is an esbuild constraint — `filter-chips.js` already proves a shared source module inlines into multiple bundles.
2. **The test pyramid is missing its top half.** 28 Python linter pairs rigorously validate static markup shape; **zero** automated coverage of runtime behavior (graphs, filter-chips, cite/search/poetry/explorables, theme cycle) and nothing guards CSS beyond the 9 contrast pairings. Every runtime bug in CLAUDE.md's gotcha log shipped and was caught by eyeball.

**Companions:**
- Sibling roadmap (feature/polish tiers): [`2026-06-07-polish-and-bugfix-roadmap.md`](2026-06-07-polish-and-bugfix-roadmap.md).
- Deferred features (long-horizon): [`2026-06-07-deferred-features-registry.md`](2026-06-07-deferred-features-registry.md).
- Parent design spec: [`2026-05-03-personal-site-design.md`](2026-05-03-personal-site-design.md).

**Rules:**
- Tiers run in numbered order. Within a tier, low-risk rows may fuse into one commit; correctness/security rows get their own commit with named test coverage.
- Row IDs are `R<tier>.<n>` to avoid collision with the sibling roadmap's `1.1`-style IDs.
- Item status: ☐ open · ✓ shipped · ⊘ obsoleted/accepted-as-is. Mark shipped with a link to the `project_*_complete.md` memory file.
- Don't draft per-tier *plans* until the tier opens (per [feedback-design-batch-no-plan-until-implement]). Specs first; plan-per-slice at implementation.
- Findings the audit judged *intentional and correct* are recorded in the "Accepted as-is" section, not as work rows — "address all" includes explicitly deciding not to change something.

---

## Tier R1 — Correctness & security (CI lies or history pollutes; fix first)

**Goal:** stop the pipeline from going green on corrupted data, stop the repo from self-polluting, and close the one supply-chain foothold. All three are contained and independently testable.

| # | Item | Severity | Where to start |
|---|---|---|---|
| R1.1 | ✓ **(shipped `8ba3882`)** **Shared `parse_scalar` corrupts quoted lists containing commas.** `["Marquez, Gabriel"]` parses to two authors; ~15 linters depend on this parser and their validators are too permissive to notice — **CI passes on corrupted data** (verified live). Same parser also drops block-style nested mappings to `''` and returns `None` on CRLF / trailing-newline-free frontmatter (silent skip in the ~14 linters that `if fm is None: continue`). | High (false-green, data integrity) | `tools/check_fixtures.py:151` (`inner.split(",")`), plus `:59-86` (block maps) and `:23,39` (frontmatter regex). Harden the split to respect quotes; add the missing quoted-comma / CRLF / block-map / trailing-newline parser tests (none exist today). Consider a small stdlib tokenizer over regex. |
| R1.2 | ✓ **(shipped `2b3a9d7`; deploy-trigger decision + R4.6 escaping still open)** **`streams-poll` commits on every run.** `write_live_yaml` writes a fresh `last_polled` timestamp each poll → `git status` is always dirty → the workflow commits+pushes every 5 min (288/day) or, if secrets are unset, goes red every 5 min. **0 bot commits to date** = currently failing or disabled. Deeper: `GITHUB_TOKEN` pushes don't trigger the deploy workflow, so the cadence never reaches the live site regardless. | High (history pollution / failure noise / no live effect) | `tools/poll_streams.py:278` + `write_live_yaml:168-171`; commit gate `.github/workflows/streams-poll.yaml:39`. Gate the commit on *real* state change (diff excluding `last_polled`, or don't rewrite `last_polled` when nothing else changed). Decide whether the cron should exist at all given the no-deploy-trigger gap. |
| R1.3 | ✓ **(shipped `2422e81`; broader `actions/*` pin sweep → R4.4)** **Unpinned third-party `treosh/lighthouse-ci-action@v12`** runs inside the privileged build job (`id-token: write` + `pages: write`) that produces the deployed artifact. Floating major tag = token-exfil / artifact-poisoning blast radius. | High (supply chain) | `.github/workflows/hugo.yaml:192,199`. Pin to a full commit SHA. (Sweep the remaining floating `actions/*` majors in R4 — this row is only the third-party privileged one.) |

**TIER R1 CLOSED 2026-07-03** (`8ba3882..2422e81`, 3 commits, +9 named tests). All three shipped with test coverage: R1.1 hardened the shared frontmatter parser (447 CI linter-pair tests green, no downstream regression); R1.2 gated the streams-live write on real state change (22 poll tests green); R1.3 pinned the LHCI action to `3e7e23f`. Carry-forwards into later tiers: streams deploy-trigger decision + auto-stub title escaping (R4.6), broader `actions/*` SHA-pin sweep (R4.4). → [project-audit-r1-complete](../../../.claude/memory/project_audit_r1_complete.md)

---

## Tier R2 — Cheap correctness gaps + guard rails

**Goal:** close small defects that will bite later, and add two ~30-line linters that convert whole finding-classes into automated gates.

| # | Item | Severity | Where to start |
|---|---|---|---|
| R2.1 | ✓ `d09d531` **Documented `math` shortcode does not exist.** CLAUDE.md promises a `{{< math >}}` `data-pending` stub as the landing pad for the elisp math pipeline; `layouts/shortcodes/math.html` is absent (verified). First real `{{< math >}}` in content → Hugo **hard-errors** on unknown shortcode. | Med (guaranteed future build break) | Add `layouts/shortcodes/math.html` mirroring the other deferred stubs (emit a `data-pending` container). Add a fixture that exercises it per [feedback-deferred-features-stay-visible]. |
| R2.2 | ✓ `0b5d3c5` **New linter: dark-block equality guard.** The `[data-theme="dark"]` block and the `@media (prefers-color-scheme: dark)` block carry hand-duplicated tokens that must stay byte-identical; `check-contrast.py` verifies ratios, not that the two blocks *match*. In sync today (14 tokens, 0 diffs, verified) — but nothing enforces it. | Med (latent drift) | New `tools/check_dark_tokens.py` (+ sibling): parse both blocks in `assets/css/main.css` (§1–§3 area, lines ~56–90), assert identical key/value sets. ~30 LOC. Wire into CI + `ci-local.sh`. |
| R2.3 | ✓ `0d1b5e9` (interpolation-aware; +R4.3) **New linter: CSS class referential integrity.** No gate catches CSS selectors orphaned by template redesigns; the file carries ~130 lines of dead rules as a result (see R4.3). | Med (accumulating dead code) | New `tools/check_css_refs.py` (+ sibling): flag classes in `main.css` with zero references across `layouts/` + `assets/js/` + `content/`, allowlisting documented deferrals (e.g. `.poem-audio-pill`). ~40 LOC. Land alongside R4.3 (which uses it to justify the deletions). |
| R2.4 | ✓ `f5962ac` **`check_lhci_urls` validates the stale committed URL list, then `gen_lhci_urls` overwrites it.** The list LHCI actually audits is never resolution-checked, and a short manifest (a section that failed to render) silently shrinks coverage with no floor assertion. | Med (coverage can silently drop) | Reorder so `check_lhci_urls` runs *after* `gen_lhci_urls` (`.github/workflows/hugo.yaml:179` vs `:187`), or point it at the regenerated files. Add a minimum-group/URL-count floor to `tools/gen_lhci_urls.py:111` (`run`). |
| R2.5 | ✓ `b5d00a9` **`cite.js` renders literal `"undefined"`.** A stored `cite-format-pref` (or a `ref` missing that format) makes `setActiveTab` write `formats[format]` with no presence check → `"undefined"` in the output box and a `data:` download of `undefined`. | Med (visible wrong output) | `assets/js/cite.js:65-72`. Guard the lookup; fall back to first available format. Related low-sev template cousin: `cite.html:12` uses `index (split . ",") 0` so a comma-less "First Last" name yields a wrong label — fix in the same pass. |
| R2.6 | ✓ `b5d00a9` **`video-sync` ships an inert `data-video-sync` div** with no JS consumer — the one deferral that emits user-facing dead markup instead of a visible fallback. `has_video_sync` is a required essay field and `example-one` sets it true. | Low (dead markup, deferred feature) | `layouts/shortcodes/video-sync.html`. Either emit a `data-pending`/fallback shape like the other stubs, or document the deferral explicitly so it round-trips when the runtime lands. |
| R2.7 | ✓ `b6e6225` **`check_math` fenced-code stripping misses indented and `~~~` fences.** `CODE_FENCE = ^\`\`\`` won't match indented or tilde fences; math inside one would be miscounted as body math → spurious `has_math` coupling error. Unconfirmed against a live fixture. | Low (uncertain) | `tools/check_math.py:45-53`. Broaden the fence regex; add a fixture with an indented/tilde fence containing math markers. |
| R2.8 | ✓ `b5d00a9` **`findRE` date extraction hard-errors on a missing date.** `index (findRE "\d{4}-\d{2}-\d{2}" ...) 0` builds fine only because required-field contracts guarantee the date; no `default`/length guard. | Low (latent build break) | `layouts/partials/home/currently.html:32`, `layouts/partials/garden/relative-date.html:10`. Add a length guard before indexing. |

**TIER R2 CLOSED 2026-07-03** (`d09d531..f5962ac`, 6 commits, +11 named tests, 2 new linter pairs → 30 total). R2.1 math stub; R2.2 dark-token equality linter (29th pair); R2.3 CSS referential-integrity linter (30th pair, interpolation-aware — resolves `{{ }}`/printf/`${}` construction, so 22 dynamically-built classes correctly pass) shipped with R4.3's dead-CSS purge; R2.4 LHCI order + `min_urls` floor; R2.5/2.6/2.8 cite/video-sync/date-guard; R2.7 code-fence regex. New finding surfaced during R2.3: **R3.6** (unwired no-js sidenote fallback), allowlisted and filed below. → [project-audit-r2-complete](../../../.claude/memory/project_audit_r2_complete.md)

---

## Tier R3 — Accessibility

**Goal:** fix the a11y regressions the "copy" pattern introduced and the JS-built chrome gaps.

| # | Item | Severity | Where to start |
|---|---|---|---|
| R3.1 | ✓ `92a525b` **h2→h4 heading skip in all 12 AMS blocks.** Every block renders `<h4 class="block-header">`; placed under an essay `<h2>` this violates WCAG 2.1 heading-order. "Theorem 1" is a label, not a document section. | Med (WCAG, systemic) | The 12 `layouts/shortcodes/{theorem,lemma,...}.html`. Use a non-heading element (or a context-computed level). Best done together with R5.3 (single shared block partial) so it's a one-place fix. |
| R3.2 | ✓ `98fa5c5` (HTML nits) + `4775888` (structural, via R5.3b) **Graph-panel a11y skeletons have drifted.** `garden`/`research` use `aria-hidden + inert`; `works` uses `hidden`. `works` uses `<h3>` title where others use `<span>`, and server-renders toolbar chips the others fill via JS — so the three open/close JS contracts differ. CLAUDE.md claims "canonical §27 chrome" but only the CSS is shared. | Med (a11y inconsistency) | ✓ Fully closed. HTML nits (`<h3>`→`<span>`, `aria-controls`) done in `98fa5c5`; structural reconciliation (one shared `layouts/partials/graph-panel.html`; 3 section files are thin wrappers; JS-contract unified by R5.2) completed by R5.3b `4775888`. |
| R3.3 | ✓ `934670e` **Search results have no listbox semantics.** Arrow-key highlight toggles a visual `.is-active` class only; the results `<ol>` has no `role="listbox"`/`option`, no `aria-activedescendant` — SR users get no announcement. | Med (a11y) | `assets/js/search.js:84,132-138`. Add roles + `aria-activedescendant`. |
| R3.4 | ✓ `3c3af9e` **Cite modal tabs miss the WAI-ARIA tabs keyboard pattern.** Buttons carry `role="tab"` + `aria-selected` but there's no Arrow-Left/Right handler; only pointer clicks switch tabs. | Low (a11y) | `assets/js/cite.js:61-74,197`. Add arrow-key tab navigation. |
| R3.5 | ✓ `3c3af9e` **`figure` shortcode defaults `alt=""`.** An omitted `alt` silently ships a decorative (empty-alt) image even for content-bearing figures; no lint gate. | Low (a11y, author-dependent) | `layouts/shortcodes/figure.html:5,12`. Consider requiring `alt` or warning when absent. |
| R3.6 | ✓ `3c3af9e` **Unwired no-JS sidenote fallback** (surfaced by R2.3). `html.no-js .essay-body .sidenote { display: block }` exists to show sidenotes inline when JS is off, but nothing ever sets `no-js` on `<html>`, so no-JS mobile readers silently lose sidenote content (they collapse to click-to-open which needs JS). Currently allowlisted in `tools/css-refs-allowlist.txt`. | Low–Med (a11y / progressive enhancement) | Add `class="no-js"` to `<html>` in `baseof.html` + an early `document.documentElement.classList.remove('no-js')` (in the FOUC-guard inline script or core JS). Then drop the allowlist entry so the linter guards it. |

**TIER R3 CLOSED 2026-07-03/04** (`92a525b..3c3af9e`, 4 commits, +2 tests). R3.1 AMS block-header `<h4>`→`<p>` (h2→h4 skip gone; anchor-link linter made tag-agnostic); R3.2 ✓ graph-panel HTML nits (`<h3>`→`<span>`, `aria-controls`) done in `98fa5c5` — structural hidden/inert + JS-contract reconciliation completed by R5.2 (`d0ee5b0`) + R5.3b (`4775888`) (shared `graph-panel.html` partial; R3.2 now fully closed); R3.3 search listbox/combobox pattern; R3.4 cite tabs WAI-ARIA keyboard + roving tabindex; R3.5 figure `warnf` on absent alt (+ 1 fixture fix); R3.6 wired the no-js fallback. JS rows (R3.3/R3.4) verified by build — no JS test harness until R5.1. → [project-audit-r3-complete](../../../.claude/memory/project_audit_r3_complete.md)

---

## Tier R4 — Hygiene, doc-drift, config hardening (trivial, high signal-to-noise)

**Goal:** restore CLAUDE.md as an accurate source of truth and clean the config/CSS cruft. Mostly one-liners; can fuse.

| # | Item | Severity | Where to start |
|---|---|---|---|
| R4.1 | ✓ `6f2f4fb` **CLAUDE.md drift** (it's the source of truth, so these are real bugs): says "67 CI steps" → **actually 71** (verified); lists `widget` as a `data-pending` stub → it's **live** post-explorables and only `lyrics.html` still emits `data-pending`; "Project status (as of 2026-06-11)" is **2 shipped tiers behind** (Tier 8 closed); the `math` stub claim (see R2.1). | Low (doc integrity) | Sweep the Deployment step-count, the stub-shortcode paragraph, and the Project-status section of `CLAUDE.md`. |
| R4.2 | ✓ `32739ee` (→ §42a) **Duplicate `§43` section number in CSS.** Both "Reading history" (4009) and "Citation export" (4252) claim §43; every cross-ref means Citation export. Undermines the §-index that is the file's primary nav aid. | Low | Renumber "Reading history" in `assets/css/main.css:4009` to an unused section; update any inline reference. |
| R4.3 | ✓ `0d1b5e9` (shipped with R2.3; is-match also removed; no-js allowlisted → R3.6) **~130 lines of dead CSS** from past redesigns: `.library-umbrella-grid` cluster (3108–3172), `.home-research-strip` (3540), `.home-two-col` (3588), `.graph-legend--{panel,page}` (1776/1780), `.library-cover-{portrait,square}`, `.research-graph-node-theme rect`, `.filter-strip` alias — all with zero references. | Low | Delete after R2.3's linter confirms each is orphaned (keeps the deletions honest). |
| R4.4 | ✓ `32739ee` **CI config hardening (batch).** `numberOfRuns: 1` against a hard `0.9` error gate → flaky deploy blocks (use median-of-3); Hugo `.deb` + Pagefind `.tar.gz` `wget`-ed with no checksum; all `actions/*` float on major tags (pin to SHA); `module.hugoVersion.min: 0.112.0` contradicts the real ≥0.162.1 floor; `YOUTUBE_API_KEY` secret injected but never read; no `timeout-minutes` on either job. | Low–Med | `lighthouserc.json:36` / `.mobile.json:33`; `hugo.yaml:8-10,40,162`; `streams-poll.yaml:23,31`; both workflow `uses:` lists. |
| R4.5 | ✓ `32739ee` **`ci-local.sh` skips the Pagefind install + index build**, so local green doesn't prove the CI Pagefind path and local LHCI serves a `/pagefind/` 404. `check_page_weights` also runs pre-pagefind locally vs post in CI. | Med (false "CI-equivalent green") | Mirror `hugo.yaml:160-168` into `tools/ci-local.sh`; align the `check_page_weights` position and the `hugo --gc --baseURL` flags. |
| R4.6 | ✓ `840a20e` (escaping; deploy-trigger decision still open for author) **`poll_streams.py` weak YAML escaping of external Twitch titles.** Auto-stub frontmatter does only `title.replace('"','\\"')` (vs `json.dumps` used correctly in `write_live_yaml`); a title with a newline/backslash can break the block and flip `draft`/`archive_status`. Committed to master by a `contents: write` job. | Low (untrusted-input-to-committed-file) | `tools/poll_streams.py:141`. Use `json.dumps` for the title. Folds naturally with R1.2. |
| R4.7 | ✓ `32739ee` **`research/graph-script.html` passes a cache-key string into the context slot** of `partialCached` where the partial ignores it — reads like an intended cache variant but isn't. | Low (confusing) | `layouts/partials/research/graph-script.html:1`. Clean up the call. |

**TIER R4 CLOSED 2026-07-04** (`840a20e..6f2f4fb`, 3 commits, +1 test). R4.1 CLAUDE.md drift sweep (linter pairs 28→30, steps 67→75, stub descriptions, project-status → audit roadmap); R4.2 dup §43 → §42a; R4.4 CI hardening (numberOfRuns 1→3, Hugo/Pagefind SHA256 checksums, all actions/* SHA-pinned, hugoVersion.min→0.162, dropped unused YOUTUBE_API_KEY, job timeouts); R4.5 ci-local Pagefind index build + `--gc`; R4.6 poll_streams `json.dumps` title escaping; R4.7 research graph-script cache-key. **Open author decision (not actioned):** whether streams-poll should exist given GITHUB_TOKEN pushes don't trigger deploy (noted at R1.2/R4.6). → [project-audit-r4-complete](../../../.claude/memory/project_audit_r4_complete.md)

---

## Tier R5 — Structural: kill the duplication (own sessions, test-guarded)

**Goal:** collapse the "copy instead of abstract" pattern (story ①). **R5.1 (test harness) lands first** so every subsequent extraction is guarded against behavioral drift. Each row is its own brainstorm → plan → ship cycle.

| # | Item | Severity | Where to start |
|---|---|---|---|
| R5.1 | ✓ `e9b6d95..7910371` **Establish a JS test harness.** ← **SHIPPED 2026-07-04.** The single biggest structural gap (story ②): ~2,280 LOC of the most stateful code (graphs, filter-chips, cite/search/poetry/explorables, theme cycle) has zero automated coverage. **Decision: Playwright, Node, dev-only** (real-browser E2E over built `public/`; devDeps only, nothing ships). Full brief: [`2026-07-04-r5.1-js-test-harness-brief.md`](2026-07-04-r5.1-js-test-harness-brief.md). Plan: [`2026-07-04-r5.1-js-test-harness.md`](../plans/2026-07-04-r5.1-js-test-harness.md). | High (foundation) | Shipped: `package.json` (devDeps) + 6 `tests/e2e/*.spec.ts` + Playwright `webServer` over `public/` + CI step after Pagefind build (pinned `actions/setup-node@49933ea`) + ci-local loud-skip + CLAUDE.md no-npm-caveat. 7 tests pass. |
| R5.2 | ✓ `d1e214c..d0ee5b0` **Extract `graph-core.js`.** ← **SHIPPED 2026-07-04.** `garden`/`research`/`works` graph runtimes shared ~70–75% of 2,280 LOC. Shipped `assets/js/graph-core.js` = `createGraph(adapter)` factory owning all shared infra (cache/drag/zoom/settle/SVG scaffold/panel-inert/resize/chip primitives, parameterized by `classPrefix`); the three files are now thin adapters (garden 297, research 252, works 229) supplying `parseData`/`applyFilters`/`renderNode`/`edgeClass`/`svgAria`/`forceParams`/`onNodeClick`/`buildToolbar` + optional hooks. **2,280 → 1,316 LOC** (−42%, shared infra fully deduped). Works normalized to garden/research conventions (JS toolbar, `inert` panel, `<div>` canvas) — subsumes R3.2's deferred hidden/inert + JS-contract reconciliation. Guarded by R5.1 E2E (3 graph mount specs + render-seam parity). Design: [`2026-07-04-r5.2-graph-core-design.md`](2026-07-04-r5.2-graph-core-design.md); memory [project-audit-r5-2-complete](../../../.claude/memory/project_audit_r5_2_complete.md). | Med (do after R5.1) | **Not done** (separate from the JS extraction, non-blocking): unify graph-data serialization — `garden/graph-data.html` `jsonify`s inside the data partial vs research/works `jsonify \| safeJS` at the embed point. Garden's form may be intentional (CLAUDE.md: minifier chokes on HTML-escaped quotes in `<script type=application/json>`). Small Hugo-template follow-up. |
| R5.3 | ✓ **Table-drive the 12 AMS block shortcodes + reconcile graph panels.** ✓ `3925b6c` **R5.3a (AMS blocks) SHIPPED 2026-07-05.** 11 numbered blocks now delegate to `layouts/partials/ams-block.html` (dict params `ctx`/`kind`/`class`/`tier`/`counter`); each shortcode is a one-line wrapper passing `"inner" .Inner`; `proof.html` stays bespoke. Byte-identical output confirmed. ✓ `4775888` **R5.3b (graph panels) SHIPPED 2026-07-05.** Shared `layouts/partials/graph-panel.html` (dict params `id`/`title`/`ariaLabel`/`section`); the three per-section `graph-panel.html` files are now one-line wrappers. Closes R3.2's structural remainder. | Med (do after R5.1) | R5.3a: `layouts/shortcodes/{theorem,...}.html` + `layouts/partials/ams-block.html`. R5.3b: `layouts/partials/graph-panel.html` (shared) + `layouts/partials/{garden,research,works}/graph-panel.html` (wrappers) + linter update (`tools/check_graph_chrome.py`). |
| R5.4 | ✓ `6d638d9..48813f0` **Python tooling deduplication.** ← **SHIPPED 2026-07-05.** Shared `tools/test_helpers.py` (`TempRepo`) adopted by the **5** test files that carried a full duplicated `TempRepo` class; the **16** lighter inline-`setUp` tempdir files were left as-is (YAGNI — marginal dedup, no reusable class to extract). `tools/test_test_helpers.py` self-tests the helper (not a linter pair). Canonical `parse_citations_yaml` now lives solely in `check_fixtures`; `check_citations` imports it. Item 3 (parser unification) was found already-satisfied: only `check_fixtures` defined the frontmatter parser; the distinct data-yaml parsers in other linters have genuinely different shapes and legitimately stay, documented in place. Every linter now returns a uniform `run(...) -> (int, list[str])` + thin `main()` (param `repo_root` for most; `check_anchor_link`/`check_lhci_urls` take `public`/config paths — pre-existing). Closes Tier R5's dedup story. | Med | ✓ Shipped. |

---

## Tier R6 — Design-scale polish (optional; own decision)

**Goal:** larger ergonomic improvements that are defensible to defer. Open only if the author wants them.

| # | Item | Severity | Where to start |
|---|---|---|---|
| R6.1 | ☐ **CSS spacing scale.** No spacing tokens — `gap` alone uses ~20 distinct raw rem values (0.2…1.75, incl. px-conversion artifacts like 0.625/0.875). A `--space-*` scale would give one density knob and fix asymmetric rhythm. | Low | `assets/css/main.css`. Introduce a token scale; migrate incrementally. |
| R6.2 | ☐ **Breakpoint tokens.** Desktop breakpoints are 8 one-off values (`800/900/960/1099/1140/1219` max, `960/1100/1280` min) with a `1099/1100` off-by-one seam; JS mirrors magic breakpoints (`RAIL_BREAKPOINT=1100`, `MOBILE_BREAKPOINT=720`) that must hand-sync with CSS. Mobile side is already disciplined. | Low | Document a 3-tier scale (or `--bp-*` custom properties for the JS side); reconcile the half-screen (~960px) tier the author actually tests at. |
| R6.3 | ☐ **Built-HTML link-integrity crawl.** Link linters validate frontmatter-declared refs pre-build; nothing crawls rendered `public/` for broken `<a href>`s. Adequate for a fixture-only site; becomes a gap once real interlinked content lands. | Low (trigger-gated) | Open when real content volume makes it worthwhile. |

---

## Accepted as-is (audit reviewed, no change warranted)

Recorded so "address all" is honest — these were considered and deliberately left alone:

- **Single 5,716-line `main.css`.** Defensible: §-numbered index, flat selectors, strong token discipline; splitting adds `@import`/bundle-order cost to a no-PostCSS pipeline for little gain. The real fix was tooling (R2.2 + R2.3), not splitting.
- **Graph *runtime* copies as separate bundles.** The multi-entry bundling is a documented esbuild trade-off; R5.2 extracts the *shared source*, not the bundle split.
- **`game_kind` / `last_modified`-as-string.** Documented Hugo-reserved-word / YAML-1.2 workarounds, each with a memory entry.
- **`data/library-media.yaml` registry.** Clean metadata registry, not duplication.
- **No visual-regression / broad CSS testing.** Intentional for a hand-rolled solo stylesheet; the contrast gate + R2.2/R2.3 cover the high-value invariants.
- **Event listeners never removed in JS.** Full-reload multi-page site (no SPA) — not a leak.

---

## Suggested session shape

1. **R1** — one session, three separate commits (each with named tests). Highest urgency.
2. **R2 + R4** — can fuse into a hygiene session (guard linters R2.2/R2.3 pair with the dead-CSS/doc-drift cleanups R4.1–R4.3); R2.4/R4.4/R4.5 config items alongside.
3. **R3** — a11y session; R3.1/R3.2 may be absorbed by R5.3 if that lands first.
4. **R5** — multi-session; **R5.1 (test harness) must land before R5.2–R5.4**.
5. **R6** — author-driven, no urgency.
