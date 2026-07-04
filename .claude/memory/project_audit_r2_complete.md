---
name: audit-r2-complete
description: "Audit-remediation Tier R2 (cheap gaps + guard linters) + R4.3 shipped 2026-07-03, site d09d531..f5962ac (6 commits, +11 tests, 2 new linter pairs); R3 is next queue head"
metadata: 
  node_type: memory
  type: project
  originSessionId: 95b0b22a-9036-45e5-8b84-f1bd965400ea
---

# Audit remediation Tier R2 (+ R4.3) — shipped 2026-07-03

Closed all 8 R2 rows from [[audit-remediation-roadmap]]. Site `d09d531..f5962ac`, 6 commits. Two new linter pairs → **30 linter pairs** total.

- **R2.1 `d09d531`** — added `layouts/shortcodes/math.html` (data-pending stub, mirrors lyrics/widget); was documented but absent → would hard-error Hugo on first real `{{< math >}}`. Exercised in example-one; inner `\(...\)` keeps check_math coupling consistent.
- **R2.2 `0b5d3c5`** — new `tools/check_dark_tokens.py` (29th pair): asserts the `:root[data-theme=dark]` and `@media(prefers-color-scheme:dark)` blocks in main.css have identical token maps. Wired into CI + ci-local after contrast.
- **R2.3 + R4.3 `0d1b5e9`** — new `tools/check_css_refs.py` (30th pair): flags CSS classes with no reference in layouts/assets/js/content. **Interpolation-aware** — resolves Hugo `{{ }}`, printf `%s`, JS `${}` prefix construction, so the 22 dynamically-built classes (stage-*, status-*, streams-category-pill--*, type-badge--*, research-status-*, graph-legend--*) correctly pass. Allowlist `tools/css-refs-allowlist.txt`. R4.3: deleted the confirmed-dead rules (.filter-strip alias, .works-tile-tag.is-match, .library-um*/.library-umbrella-grid §44 cluster + media query, .home-research-strip, .home-two-col). Allowlisted .poem-audio-pill (deferral) + .no-js (see R3.6).
- **R2.4 `f5962ac`** — reordered CI + ci-local so `check_lhci_urls` validates the *regenerated* lighthouserc (was validating the stale committed list before gen overwrote it); added a `min_urls` floor (20; 26 today) in `lhci-overrides.json` so a short manifest fails loudly instead of silently shrinking LHCI coverage.
- **R2.5/2.6/2.8 `b5d00a9`** — cite.js no longer renders literal "undefined" on a missing format (falls back to first available); cite.html surname split handles comma-less "First Last"; video-sync shortcode emits a visible data-pending fallback instead of an invisible div; currently.html + relative-date.html guard the `findRE` `[0]` index.
- **R2.7 `b6e6225`** — check_math CODE_FENCE now matches indented + `~~~` fences (was `^```` only).

**New finding surfaced by R2.3 → filed as R3.6:** `html.no-js .essay-body .sidenote` is an unwired progressive-enhancement fallback (nothing sets `no-js` on `<html>`), so no-JS mobile readers lose sidenotes. Allowlisted for now; R3.6 wires it.

Verified: site rebuilds clean; contrast/dark-token/css-refs/smoke/math/lhci linters green; +11 named tests (447→ CI pairs unaffected; dark 5, css-refs 11, math +3, gen_lhci +2). **Not pushed** — local on master.

**R3 (accessibility) is the next queue head:** R3.1 h2→h4 AMS block heading skip, R3.2 graph-panel a11y drift, R3.3 search listbox, R3.4 cite tabs keyboard, R3.5 figure alt, R3.6 no-js wiring. R3.1/R3.2 may fold into R5.3 (shared partials). No JS test harness yet (R5.1) — JS fixes (R3.3/R3.4) are verify-by-build until then.
