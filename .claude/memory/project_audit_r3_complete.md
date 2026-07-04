---
name: audit-r3-complete
description: "Audit-remediation Tier R3 (accessibility) shipped 2026-07-03/04, site 92a525b..3c3af9e (4 commits); R4 is next queue head"
metadata: 
  node_type: memory
  type: project
  originSessionId: 95b0b22a-9036-45e5-8b84-f1bd965400ea
---

# Audit remediation Tier R3 (accessibility) — shipped 2026-07-03/04

Closed all 6 R3 rows from [[audit-remediation-roadmap]]. Site `92a525b..3c3af9e`, 4 commits.

- **R3.1 `92a525b`** — all 12 AMS block shortcodes rendered `<h4 class="block-header">` for a label, causing an h2→h4 heading-order skip. Switched to `<p class="block-header">` (CSS §47 / block-renumber.js / anchor-link all key off the *class*, so no visual/functional change). `check_anchor_link.py` made tag-agnostic (still tolerates legacy `<h4>`); +1 test. example-five body now h1+h2 only.
- **R3.2 `98fa5c5` (◐ partial)** — both hide-mechanisms (garden/research `aria-hidden+inert` vs works `hidden`) are individually a11y-valid, so fixed only HTML nits: works `<h3>` title → `<span>`, garden/research close buttons gain `aria-controls`. Structural reconciliation (single mechanism + unified JS open/close contract) deferred to **R5.3** after R5.1's JS test harness — refactoring the 3 untested graph runtimes blind is the audit's flagged risk.
- **R3.3 `934670e`** — search results got the WAI-ARIA combobox+listbox pattern: input = combobox (`aria-controls`/`aria-expanded`/`aria-autocomplete`), results container = listbox, sections = groups, results = options with unique ids + `aria-selected`; `setActiveRow` drives `aria-activedescendant`. Inner `<a>` taken out of tab order. Removed the results container's `aria-live` (the status element already announces the count).
- **R3.4 `3c3af9e`** — cite modal tabs gained Arrow/Home/End keyboard nav + roving tabindex (`setActiveTab` manages tabindex).
- **R3.5 `3c3af9e`** — figure shortcode `warnf`s when `alt` is entirely absent (`isset .Params "alt"`); explicit `alt=""` stays a valid decorative marker. Caught one omission (`/garden/story-atoms/`), fixed with `alt=""`.
- **R3.6 `3c3af9e`** — wired the dead no-js fallback: `<html class="no-js">` in baseof + the FOUC-guard theme script removes it (`classList.remove('no-js')`); no-JS readers now get `html.no-js .essay-body .sidenote` inline. Dropped `no-js` from the css-refs allowlist (genuinely referenced now → linter guards it).

**No JS test harness yet** (that's R5.1), so R3.3/R3.4 were verified by build (esbuild compiles, roles/attrs render) rather than unit tests — the honest limitation, tracked. 467 CI linter-pair tests green; all `check_*.py` green against the built site. **Not pushed** — local on master.

**R4 (hygiene / doc-drift / config) is the next queue head:** R4.1 CLAUDE.md drift sweep (67→71 steps, stub descriptions, project-status), R4.2 dup §43, R4.4 CI hardening (median-of-3, checksums, `actions/*` SHA-pin sweep, hugoVersion.min, unused secret, timeouts), R4.5 ci-local pagefind gap, R4.6 poll_streams title escaping + streams deploy-trigger decision, R4.7 research graph-script cache-key. (R4.3 already shipped with R2.3.)
