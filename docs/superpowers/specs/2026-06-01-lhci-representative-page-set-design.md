# LHCI representative page set — design

**Status:** approved, ready for plan (slice 4.1 only; 4.2 + 4.3 remain deferred).
**Filed:** 2026-06-01 (stub) — see commit history.
**Approved:** 2026-06-04, after two consecutive B.4 push failures from LHCI URL drift (`example-essay-one` → `example-one` for B.4; `memory-and-play` / `what-is-a-narrative-atom` → `example-theme-one` / `example-question-one` for B.3) and a deferral check at session start.

## 1 — Problem

`lighthouserc.json` + `lighthouserc.mobile.json` hand-pin 12 URLs each (identical lists today). Each B sub-project (B.1 garden, B.3 research, B.4 essays — and future B.5 works, B.6 streams, B.7 about) retires hand-authored fixture slugs and replaces them with B-emitted slugs. The LHCI configs aren't auto-updated, so the next push 404s after ~3 min of LHCI work and burns a CI cycle.

Drift class will recur every time a fixture retirement lands. The same class also covers per-URL overrides — the `lighthouserc.mobile.json` `assertMatrix` references `/essays/example-one/$` to soften the kitchen-sink perf gate; if that URL retires, the override silently dies and the original `0.9` floor reapplies without warning.

## 2 — Goals

1. Eliminate the 5-min "push → LHCI 404 → re-push" round-trip.
2. Cover every distinct rendering path (one URL per layout/template), not every page.
3. Auto-extend when a new layout/template lands (e.g., a new shortcode adds CSS, a new Section adds a layout family). **Deferred to 4.2 / 4.3.**

## 3 — Non-goals

- Audit every page (~111 today; ~37 min of LHCI; variance compounds and exhausts GH Actions minutes).
- Replace the existing LHCI assertion thresholds (`minScore: 0.9`).
- Edit the LHCI configs from the validator. Validator is read-only.

## 4 — Design

A new sibling linter pair: `tools/check_lhci_urls.py` + `tools/test_check_lhci_urls.py`. Runs after `hugo --minify` and before LHCI. Read-only. Fast-fails on drift in seconds, not minutes.

### 4.1 — The three checks

The linter performs three checks in order. Any failure produces one line on stderr and contributes to a non-zero exit. Existence failures don't short-circuit equality/regex checks — the linter runs all three and reports every issue in a single pass so a re-push fixes all problems at once.

#### 4.1.1 — Existence

For each URL in `ci.collect.url` (both configs), strip the `http://localhost` prefix and assert `public/<path>/index.html` exists as a regular file.

- `http://localhost/` → `public/index.html`
- `http://localhost/essays/example-one/` → `public/essays/example-one/index.html`
- Trailing slash is required by LHCI today; the linter accepts both `…/foo/` and `…/foo` and normalizes via `.strip("/")`, matching `check_smoke.py`'s `file_for_url` helper.

#### 4.1.2 — Desktop/mobile equality

Assert that `lighthouserc.json` → `ci.collect.url` is **equal as an ordered list** to `lighthouserc.mobile.json` → `ci.collect.url`. Catches one-sided additions (a new URL added to mobile only, or vice versa). Identical-but-reordered lists are treated as drift — the configs are co-maintained and order is intentional.

The two URL arrays must stay identical. Diverging them would mean some rendering paths are audited only on desktop or only on mobile, which is not the model.

#### 4.1.3 — assertMatrix regex coverage

For each entry in `lighthouserc.mobile.json` → `ci.assert.assertMatrix`, compile the `matchingUrlPattern` field with Python's `re.compile` and assert it matches **at least one** URL in `collect.url` via `re.search` (substring match on the full URL, matching LHCI's `String.prototype.match` semantics in JS).

This catches dead overrides: when the kitchen-sink URL `example-one` is renamed or retired, the `/essays/example-one/$` regex stops matching, the perf-gate softening silently reverts to the global `0.9` floor, and the next CI run fails on perf score variance. Today `lighthouserc.json` has no `assertMatrix` block; the check applies only to mobile but skips gracefully if either config lacks the field.

Regex compile errors (invalid pattern syntax) are surfaced as their own error line.

### 4.2 — Error message format

Each error is one line on stderr, prefixed with the source config so the author knows where to edit:

```
lighthouserc.json: /essays/example-one/: missing file at essays/example-one/index.html
lighthouserc.mobile.json: collect.url differs from lighthouserc.json (1 added, 0 removed)
lighthouserc.mobile.json: assertMatrix[0].matchingUrlPattern '/essays/example-one/$' matches no URL in collect.url
lighthouserc.mobile.json: assertMatrix[0].matchingUrlPattern '/[' is not a valid regex: missing ], unterminated subpattern
```

A trailing summary line names the count: `check_lhci_urls: N issue(s)`. On clean, prints `check_lhci_urls: OK (M URLs, K assertMatrix overrides)`.

### 4.3 — Exit codes

Mirrors the stdlib convention used across `check_*.py` linters:

- `0` — all checks pass.
- `1` — one or more validation failures (existence / equality / regex coverage / regex syntax).
- `2` — bootstrap failure: `public/` directory missing, or either LHCI config file missing / unparseable JSON.

Exit 2 is distinct from validation failure so CI logs can distinguish "you forgot to run hugo first" from "drift found." Note: an "unparseable JSON" failure is also exit 2 since it means the config itself is malformed, not that a URL is wrong.

### 4.4 — CI placement

New step pair inserted right after `check_smoke.py` and before `check_page_weights.py`:

```yaml
- name: Verify LHCI URLs resolve to built pages
  run: python3 tools/check_lhci_urls.py
- name: Run LHCI URL linter unit tests
  run: cd tools && python3 -m unittest test_check_lhci_urls.py -v
```

Step count: 63 → 65. The build-validation cluster (smoke, LHCI URLs, page-weight) stays contiguous, before the two LHCI gates.

### 4.5 — Tests

`tools/test_check_lhci_urls.py` covers the three checks plus parsing and bootstrap edges. Target ~10 test methods using `tempfile.TemporaryDirectory` to stub a fake `public/` and JSON configs:

- existence: ok / missing / root URL `/` / nested path
- URL parsing: with/without `http://localhost` prefix, trailing slash present, root `/` → `public/index.html`
- equality: identical lists / mobile has extra / desktop has extra / same URLs in different order (treated as drift)
- assertMatrix: regex matches / matches nothing / assertMatrix absent (desktop) / invalid regex syntax
- bootstrap: missing `public/` → exit 2 / missing config file → exit 2 / non-JSON config → exit 2
- aggregation: multiple failures combine into single exit-1 run with all messages emitted

## 5 — Future work (deferred)

### 5.1 — Auto-derive from sitemap + Page.Kind/Type

`tools/gen_lhci_urls.py`: parse `public/sitemap.xml` post-build, group by Hugo (Kind, Section, Type), pick the first URL per group, write into both LHCI configs replacing `collect.url`.

**Cost:** ~80 lines Python + sibling test pair + Hugo template emitting a `representative-pages.json` data file (sitemap alone lacks Hugo metadata).
**Strength:** Zero drift. New section / new Type automatically gets an LHCI URL.
**Pick-up trigger:** A new shortcode/layout family lands without being added to the LHCI list (4.1 would catch the *drift*, but author still has to hand-edit; 4.2 removes the manual step).

### 5.2 — Visual-feature autodetect

Detect when a published page introduces a CSS class or shortcode never seen before. Maintain `data/lhci-feature-fingerprints.yaml` keyed by URL. CI step diffs current fingerprints vs. the manifest snapshot from the prior commit; URLs with novel class/shortcode usage get auto-added to the LHCI list.

**Cost:** ~150 lines Python + sibling tests + Hugo template emitting fingerprints. CI ordering: after Hugo build, before LHCI.
**Strength:** Auto-extends as the site grows. A new shortcode (e.g., a future `{{< widget >}}` runtime) pulls the first essay using it into the LHCI gate.
**Risk:** Fingerprint noise (`<main>`, `<header>` on every page); needs an allowlist of distinguishing CSS namespaces.
**Pick-up trigger:** After 5.1 is in place and the fingerprint corpus is observable.

## 6 — Out of scope

- Changing LHCI assertion thresholds.
- Switching from GitHub Actions LHCI to a hosted LHCI service.
- Per-page performance budgets (separate concern — `tools/check_page_weights.py` already walks `public/` and gates byte budgets).
- Single-source-of-truth refactor of the URL list (would require a generator script writing both configs; 4.1.2 equality check enforces parity without the refactor).

---

**Self-review:**

- All placeholders resolved (no TBD / TODO).
- Internally consistent: three checks (existence + equality + regex coverage) align with goals (eliminate round-trip, catch dead overrides) and CI placement (after hugo, before LHCI).
- Scope is single-implementation-plan-sized: ~50 lines Python + ~10 test methods + 2 CI steps.
- No ambiguity in error format, exit codes, or URL parsing rules.
