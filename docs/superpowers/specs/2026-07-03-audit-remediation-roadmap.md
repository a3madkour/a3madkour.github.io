# Post-Audit Remediation Roadmap

**Date:** 2026-07-03
**Status:** Active. All rows ☐ open. Tiers run in numbered order (R1 first).

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
| R1.1 | ☐ **Shared `parse_scalar` corrupts quoted lists containing commas.** `["Marquez, Gabriel"]` parses to two authors; ~15 linters depend on this parser and their validators are too permissive to notice — **CI passes on corrupted data** (verified live). Same parser also drops block-style nested mappings to `''` and returns `None` on CRLF / trailing-newline-free frontmatter (silent skip in the ~14 linters that `if fm is None: continue`). | High (false-green, data integrity) | `tools/check_fixtures.py:151` (`inner.split(",")`), plus `:59-86` (block maps) and `:23,39` (frontmatter regex). Harden the split to respect quotes; add the missing quoted-comma / CRLF / block-map / trailing-newline parser tests (none exist today). Consider a small stdlib tokenizer over regex. |
| R1.2 | ☐ **`streams-poll` commits on every run.** `write_live_yaml` writes a fresh `last_polled` timestamp each poll → `git status` is always dirty → the workflow commits+pushes every 5 min (288/day) or, if secrets are unset, goes red every 5 min. **0 bot commits to date** = currently failing or disabled. Deeper: `GITHUB_TOKEN` pushes don't trigger the deploy workflow, so the cadence never reaches the live site regardless. | High (history pollution / failure noise / no live effect) | `tools/poll_streams.py:278` + `write_live_yaml:168-171`; commit gate `.github/workflows/streams-poll.yaml:39`. Gate the commit on *real* state change (diff excluding `last_polled`, or don't rewrite `last_polled` when nothing else changed). Decide whether the cron should exist at all given the no-deploy-trigger gap. |
| R1.3 | ☐ **Unpinned third-party `treosh/lighthouse-ci-action@v12`** runs inside the privileged build job (`id-token: write` + `pages: write`) that produces the deployed artifact. Floating major tag = token-exfil / artifact-poisoning blast radius. | High (supply chain) | `.github/workflows/hugo.yaml:192,199`. Pin to a full commit SHA. (Sweep the remaining floating `actions/*` majors in R4 — this row is only the third-party privileged one.) |

---

## Tier R2 — Cheap correctness gaps + guard rails

**Goal:** close small defects that will bite later, and add two ~30-line linters that convert whole finding-classes into automated gates.

| # | Item | Severity | Where to start |
|---|---|---|---|
| R2.1 | ☐ **Documented `math` shortcode does not exist.** CLAUDE.md promises a `{{< math >}}` `data-pending` stub as the landing pad for the elisp math pipeline; `layouts/shortcodes/math.html` is absent (verified). First real `{{< math >}}` in content → Hugo **hard-errors** on unknown shortcode. | Med (guaranteed future build break) | Add `layouts/shortcodes/math.html` mirroring the other deferred stubs (emit a `data-pending` container). Add a fixture that exercises it per [feedback-deferred-features-stay-visible]. |
| R2.2 | ☐ **New linter: dark-block equality guard.** The `[data-theme="dark"]` block and the `@media (prefers-color-scheme: dark)` block carry hand-duplicated tokens that must stay byte-identical; `check-contrast.py` verifies ratios, not that the two blocks *match*. In sync today (14 tokens, 0 diffs, verified) — but nothing enforces it. | Med (latent drift) | New `tools/check_dark_tokens.py` (+ sibling): parse both blocks in `assets/css/main.css` (§1–§3 area, lines ~56–90), assert identical key/value sets. ~30 LOC. Wire into CI + `ci-local.sh`. |
| R2.3 | ☐ **New linter: CSS class referential integrity.** No gate catches CSS selectors orphaned by template redesigns; the file carries ~130 lines of dead rules as a result (see R4.3). | Med (accumulating dead code) | New `tools/check_css_refs.py` (+ sibling): flag classes in `main.css` with zero references across `layouts/` + `assets/js/` + `content/`, allowlisting documented deferrals (e.g. `.poem-audio-pill`). ~40 LOC. Land alongside R4.3 (which uses it to justify the deletions). |
| R2.4 | ☐ **`check_lhci_urls` validates the stale committed URL list, then `gen_lhci_urls` overwrites it.** The list LHCI actually audits is never resolution-checked, and a short manifest (a section that failed to render) silently shrinks coverage with no floor assertion. | Med (coverage can silently drop) | Reorder so `check_lhci_urls` runs *after* `gen_lhci_urls` (`.github/workflows/hugo.yaml:179` vs `:187`), or point it at the regenerated files. Add a minimum-group/URL-count floor to `tools/gen_lhci_urls.py:111` (`run`). |
| R2.5 | ☐ **`cite.js` renders literal `"undefined"`.** A stored `cite-format-pref` (or a `ref` missing that format) makes `setActiveTab` write `formats[format]` with no presence check → `"undefined"` in the output box and a `data:` download of `undefined`. | Med (visible wrong output) | `assets/js/cite.js:65-72`. Guard the lookup; fall back to first available format. Related low-sev template cousin: `cite.html:12` uses `index (split . ",") 0` so a comma-less "First Last" name yields a wrong label — fix in the same pass. |
| R2.6 | ☐ **`video-sync` ships an inert `data-video-sync` div** with no JS consumer — the one deferral that emits user-facing dead markup instead of a visible fallback. `has_video_sync` is a required essay field and `example-one` sets it true. | Low (dead markup, deferred feature) | `layouts/shortcodes/video-sync.html`. Either emit a `data-pending`/fallback shape like the other stubs, or document the deferral explicitly so it round-trips when the runtime lands. |
| R2.7 | ☐ **`check_math` fenced-code stripping misses indented and `~~~` fences.** `CODE_FENCE = ^\`\`\`` won't match indented or tilde fences; math inside one would be miscounted as body math → spurious `has_math` coupling error. Unconfirmed against a live fixture. | Low (uncertain) | `tools/check_math.py:45-53`. Broaden the fence regex; add a fixture with an indented/tilde fence containing math markers. |
| R2.8 | ☐ **`findRE` date extraction hard-errors on a missing date.** `index (findRE "\d{4}-\d{2}-\d{2}" ...) 0` builds fine only because required-field contracts guarantee the date; no `default`/length guard. | Low (latent build break) | `layouts/partials/home/currently.html:32`, `layouts/partials/garden/relative-date.html:10`. Add a length guard before indexing. |

---

## Tier R3 — Accessibility

**Goal:** fix the a11y regressions the "copy" pattern introduced and the JS-built chrome gaps.

| # | Item | Severity | Where to start |
|---|---|---|---|
| R3.1 | ☐ **h2→h4 heading skip in all 12 AMS blocks.** Every block renders `<h4 class="block-header">`; placed under an essay `<h2>` this violates WCAG 2.1 heading-order. "Theorem 1" is a label, not a document section. | Med (WCAG, systemic) | The 12 `layouts/shortcodes/{theorem,lemma,...}.html`. Use a non-heading element (or a context-computed level). Best done together with R5.3 (single shared block partial) so it's a one-place fix. |
| R3.2 | ☐ **Graph-panel a11y skeletons have drifted.** `garden`/`research` use `aria-hidden + inert`; `works` uses `hidden`. `works` uses `<h3>` title where others use `<span>`, and server-renders toolbar chips the others fill via JS — so the three open/close JS contracts differ. CLAUDE.md claims "canonical §27 chrome" but only the CSS is shared. | Med (a11y inconsistency) | Reconcile `layouts/partials/{garden,research,works}/graph-panel.html` to one skeleton (follow the already-unified `graph-legend.html` model). Overlaps R5.3. |
| R3.3 | ☐ **Search results have no listbox semantics.** Arrow-key highlight toggles a visual `.is-active` class only; the results `<ol>` has no `role="listbox"`/`option`, no `aria-activedescendant` — SR users get no announcement. | Med (a11y) | `assets/js/search.js:84,132-138`. Add roles + `aria-activedescendant`. |
| R3.4 | ☐ **Cite modal tabs miss the WAI-ARIA tabs keyboard pattern.** Buttons carry `role="tab"` + `aria-selected` but there's no Arrow-Left/Right handler; only pointer clicks switch tabs. | Low (a11y) | `assets/js/cite.js:61-74,197`. Add arrow-key tab navigation. |
| R3.5 | ☐ **`figure` shortcode defaults `alt=""`.** An omitted `alt` silently ships a decorative (empty-alt) image even for content-bearing figures; no lint gate. | Low (a11y, author-dependent) | `layouts/shortcodes/figure.html:5,12`. Consider requiring `alt` or warning when absent. |

---

## Tier R4 — Hygiene, doc-drift, config hardening (trivial, high signal-to-noise)

**Goal:** restore CLAUDE.md as an accurate source of truth and clean the config/CSS cruft. Mostly one-liners; can fuse.

| # | Item | Severity | Where to start |
|---|---|---|---|
| R4.1 | ☐ **CLAUDE.md drift** (it's the source of truth, so these are real bugs): says "67 CI steps" → **actually 71** (verified); lists `widget` as a `data-pending` stub → it's **live** post-explorables and only `lyrics.html` still emits `data-pending`; "Project status (as of 2026-06-11)" is **2 shipped tiers behind** (Tier 8 closed); the `math` stub claim (see R2.1). | Low (doc integrity) | Sweep the Deployment step-count, the stub-shortcode paragraph, and the Project-status section of `CLAUDE.md`. |
| R4.2 | ☐ **Duplicate `§43` section number in CSS.** Both "Reading history" (4009) and "Citation export" (4252) claim §43; every cross-ref means Citation export. Undermines the §-index that is the file's primary nav aid. | Low | Renumber "Reading history" in `assets/css/main.css:4009` to an unused section; update any inline reference. |
| R4.3 | ☐ **~130 lines of dead CSS** from past redesigns: `.library-umbrella-grid` cluster (3108–3172), `.home-research-strip` (3540), `.home-two-col` (3588), `.graph-legend--{panel,page}` (1776/1780), `.library-cover-{portrait,square}`, `.research-graph-node-theme rect`, `.filter-strip` alias — all with zero references. | Low | Delete after R2.3's linter confirms each is orphaned (keeps the deletions honest). |
| R4.4 | ☐ **CI config hardening (batch).** `numberOfRuns: 1` against a hard `0.9` error gate → flaky deploy blocks (use median-of-3); Hugo `.deb` + Pagefind `.tar.gz` `wget`-ed with no checksum; all `actions/*` float on major tags (pin to SHA); `module.hugoVersion.min: 0.112.0` contradicts the real ≥0.162.1 floor; `YOUTUBE_API_KEY` secret injected but never read; no `timeout-minutes` on either job. | Low–Med | `lighthouserc.json:36` / `.mobile.json:33`; `hugo.yaml:8-10,40,162`; `streams-poll.yaml:23,31`; both workflow `uses:` lists. |
| R4.5 | ☐ **`ci-local.sh` skips the Pagefind install + index build**, so local green doesn't prove the CI Pagefind path and local LHCI serves a `/pagefind/` 404. `check_page_weights` also runs pre-pagefind locally vs post in CI. | Med (false "CI-equivalent green") | Mirror `hugo.yaml:160-168` into `tools/ci-local.sh`; align the `check_page_weights` position and the `hugo --gc --baseURL` flags. |
| R4.6 | ☐ **`poll_streams.py` weak YAML escaping of external Twitch titles.** Auto-stub frontmatter does only `title.replace('"','\\"')` (vs `json.dumps` used correctly in `write_live_yaml`); a title with a newline/backslash can break the block and flip `draft`/`archive_status`. Committed to master by a `contents: write` job. | Low (untrusted-input-to-committed-file) | `tools/poll_streams.py:141`. Use `json.dumps` for the title. Folds naturally with R1.2. |
| R4.7 | ☐ **`research/graph-script.html` passes a cache-key string into the context slot** of `partialCached` where the partial ignores it — reads like an intended cache variant but isn't. | Low (confusing) | `layouts/partials/research/graph-script.html:1`. Clean up the call. |

---

## Tier R5 — Structural: kill the duplication (own sessions, test-guarded)

**Goal:** collapse the "copy instead of abstract" pattern (story ①). **R5.1 (test harness) lands first** so every subsequent extraction is guarded against behavioral drift. Each row is its own brainstorm → plan → ship cycle.

| # | Item | Severity | Where to start |
|---|---|---|---|
| R5.1 | ☐ **Establish a JS test harness.** The single biggest structural gap (story ②): ~2,280 LOC of the most stateful code (graphs, filter-chips, cite/search/poetry/explorables, theme cycle) has zero automated coverage. Start with a thin Playwright (or similar) smoke suite over the built site: theme three-state cycle, a filter chip narrows tiles, search modal opens, a graph mounts, cite modal opens/copies. This is the prerequisite for R5.2–R5.3. | High (foundation) | New test tooling. Note the no-npm constraint applies to the *site*, not necessarily its dev tooling — decide whether the harness lives behind a dev-only dependency or a vendored runner. Resolve that in the R5.1 brainstorm. |
| R5.2 | ☐ **Extract `graph-core.js`.** `garden`/`research`/`works` graph runtimes share 70–80% of ~2,280 lines. Move the domain-agnostic clusters first (lowest risk, ~350–450 lines deleted): panel-resize (`setupPanelResize`/`applySavedPanelWidth`/`PANEL_*`), localStorage position cache (`positionsCacheKey`/`load`/`saveCachedPositions`/`persistCacheDebounced`/`flushCache`), `reducedMotion`/`isMobile`/`nodeRadius` constants, `openPanel`/`closePanel`/`makeFilterChip`/`makeActionChip`. Import into all three bundles — the pattern `filter-chips.js` already proves. Leave genuinely-divergent domain logic per-file, config-object-driven. | Med (do after R5.1) | `assets/js/{garden,research,works}-graph.js`. Also unify the graph-data serialization: `garden/graph-data.html:92` calls `jsonify` inside the data partial while research/works return a dict and `jsonify | safeJS` at the embed point — one convention. |
| R5.3 | ☐ **Table-drive the 12 AMS block shortcodes + reconcile graph panels.** The 12 block files are identical modulo `(kind, counter, tier, label)`; make the body one shared partial with 12 thin `{{ partial "block" (dict …) }}` wrappers (if ox-hugo requires per-name files). Reconcile the three `graph-panel.html` skeletons to one (subsumes R3.1 + R3.2 if not already shipped). | Med (do after R5.1) | `layouts/shortcodes/{theorem,...}.html`; `layouts/partials/{garden,research,works}/graph-panel.html`. Model: the already-unified `graph-legend.html`. |
| R5.4 | ☐ **Python tooling deduplication.** 22 test files re-roll identical tempdir scaffolding (no shared `test_helpers.py`); `citations.yaml` has two divergent parsers (`check_fixtures.parse_citations_yaml` vs `check_citations.parse_citations_yaml`); 6 linters roll their own YAML instead of the shared module; `run()`/`main()` entrypoints are inconsistent (15 of 30 linters have no `run()` seam; return arity varies `(rc,errors)` vs `(rc,errors,warnings)`). | Med | `tools/`. Add a shared test-scaffold helper; unify the two citation parsers; standardize on the `run(repo_root) -> (rc, errors)` seam. Best done after R1.1 hardens the shared parser (don't build on the fragile version). |

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
