# LHCI representative page set — design stub

**Status:** queued (stub only — no plan until implementation begins, per [[feedback_design_batch_no_plan_until_implement]]).
**Filed:** 2026-06-01, in response to two consecutive B.4 push failures from LHCI URL drift (`example-essay-one` → `example-one` for B.4; `memory-and-play` / `what-is-a-narrative-atom` → `example-theme-one` / `example-question-one` for B.3).

## 1 — Problem

`lighthouserc.json` + `lighthouserc.mobile.json` hand-pin 12 URLs. Each B sub-project (B.1 garden, B.3 research, B.4 essays — and future B.5 works, B.6 streams, B.7 about) retires hand-authored fixture slugs and replaces them with B-emitted slugs. The LHCI configs aren't auto-updated, so the next push 404s after ~3 min of LHCI work and burns a CI cycle.

Drift class will recur every time a fixture retirement lands. Catching it pre-push needs either:

- (a) The set is **auto-derived** from a stable source (sitemap + Hugo Page.Kind/Section/Type) so slug changes propagate.
- (b) The set is **manually curated** but **drift-validated pre-LHCI** (a tiny linter that asserts every URL resolves to a built `public/<path>/index.html`).

## 2 — Goals

1. Eliminate the 5-min "push → LHCI 404 → re-push" round-trip.
2. Cover every distinct rendering path (one URL per layout/template), not every page.
3. Auto-extend when a new layout/template lands (e.g., a new shortcode adds CSS, a new Section adds a layout family).

## 3 — Non-goals

- Audit every page (~111 today; ~37 min of LHCI; variance compounds and exhausts GH Actions minutes — discussed in this session's CI thread).
- Replace the existing LHCI assertion thresholds (`minScore: 0.9`).

## 4 — Design options (sketch)

### 4.1 Manual curation + pre-LHCI URL validator

`tools/check_lhci_urls.py` (sibling linter pair): parse both LHCI configs, for each URL assert `public/<path>/index.html` exists. Runs after `hugo --minify`, before LHCI. Fast-fail on drift in seconds, not minutes. Doesn't prevent drift, but kills the round-trip.

**Cost:** ~20 lines Python + sibling test pair. CI step #51.
**Limits:** Author still hand-edits configs when fixtures retire. The slice owner adds the URL update to their fixture-retirement task.

### 4.2 Auto-derive from sitemap + Page.Kind/Type

`tools/gen_lhci_urls.py`: parse `public/sitemap.xml` post-build. Group URLs by Hugo (Kind, Section, Type) — enumerate the distinct triples and pick the first URL per group (alphabetical or by date). Write into `lighthouserc.json` + `.mobile.json` `collect.url` arrays, replacing whatever's there.

**Cost:** ~80 lines Python + sibling test pair, plus a write-step in CI.
**Limits:** Sitemap doesn't carry Hugo metadata directly; need a Hugo template helper to emit a `representative-pages.json` data file at build (one URL per (Section, Type, Kind)). Then gen_lhci_urls reads that.
**Strength:** Zero drift. New section / new Type automatically gets an LHCI URL.

### 4.3 Visual-feature autodetect (the stretch goal)

Detect when a published page introduces a CSS class or shortcode never seen before — that's the signal "this page has a new template family worth auditing." Implementation:

- Build a manifest `data/lhci-feature-fingerprints.yaml` keyed by URL, value = sorted list of (CSS classes referenced in `<body>`) ∪ (shortcode names emitted).
- A CI step diffs current build's fingerprints vs. the manifest snapshot from the prior commit (`git show HEAD~1:data/lhci-feature-fingerprints.yaml`).
- Any URL whose fingerprint contains classes/shortcodes NOT present in any other LHCI URL → add to the LHCI list for this run; persist into manifest.

**Cost:** ~150 lines Python + sibling tests + Hugo template that emits the fingerprint data. CI step ordering: after Hugo build, before LHCI.
**Strength:** Auto-extends as the site grows. A new shortcode (e.g., a `{{< widget >}}` runtime that lands later) automatically pulls the first essay using it into the LHCI gate.
**Risk:** Fingerprint noise — classes added by every page (`<main>`, `<header>`) get filtered; needs an allowlist of "actually-distinguishing" CSS namespaces.

## 5 — Recommendation (when picked up)

Ship 4.1 (validator) first — closes the drift-round-trip and is ~1 hour of work. Then 4.2 (sitemap-derived) as a follow-up; defer 4.3 until 4.2 is in place and the fingerprint corpus is observable.

## 6 — Triggers for pick-up

- Next fixture retirement (B.5 / B.6 / B.7) — that's the third time this slice has bit; cost of the round-trip approaches the cost of fixing it.
- Or: after a new shortcode/layout lands without an LHCI URL update (R1 from prior slices, or a future visual feature).

## 7 — Out of scope

- Changing LHCI assertion thresholds.
- Switching from GitHub Actions LHCI to a hosted LHCI service.
- Per-page performance budgets (separate concern — `tools/check_page_weights.py` already gates byte budgets).

---

**Self-review:** stub-level; no concrete API surface, no test counts. Pick-up trigger requires a brainstorming session before plan-writing per [[feedback_file_for_another_slice_means_stub]].
