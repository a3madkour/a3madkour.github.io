---
name: project-lhci-representative-pages-queued
description: "4.1 SHIPPED 2026-06-04 (see [[project-lhci-url-validator-complete]]); 4.2 sitemap-derived + 4.3 fingerprint autodetect still queued — pick up at next fixture-retirement slice"
metadata:
  node_type: memory
  type: project
  originSessionId: 5145878a-a130-45b0-84d6-28c736593219
---

# LHCI representative page set — 4.1 shipped, 4.2/4.3 queued

**Status update 2026-06-04:** 4.1 (pre-LHCI URL validator) shipped — see [[project-lhci-url-validator-complete]]. Repo now has `tools/check_lhci_urls.py` + sibling tests + CI step pair. Fast-fail on URL drift is live.

**4.2 + 4.3 remain queued.** Full design for both lives in `docs/superpowers/specs/2026-06-01-lhci-representative-page-set-design.md` §5.

## 4.2 — Sitemap-derived URLs (queued, no plan)

`tools/gen_lhci_urls.py` — parse `public/sitemap.xml`, group by Hugo (Kind, Section, Type), pick first URL per group, write into both LHCI configs' `collect.url`. ~80 LOC + Hugo template emitting `representative-pages.json` (sitemap alone lacks Hugo metadata). Zero drift.

**Why filed:** 4.1 catches drift but doesn't prevent it — author still hand-edits configs on fixture retirement. 4.2 removes the manual step.

**Pick-up trigger:** Next time fixture retirement happens AND author finds hand-editing the configs painful. Without that pain signal, defer.

## 4.3 — Visual-feature autodetect (queued, no plan)

Fingerprint each LHCI URL by sorted CSS classes + shortcode names in `<body>`. Persist to `data/lhci-feature-fingerprints.yaml`. CI step diffs current build's fingerprints vs. prior commit's; URLs with novel classes/shortcodes auto-added. ~150 LOC + Hugo template + allowlist of "actually-distinguishing" CSS namespaces (filters out `<main>`/`<header>` noise).

**Why filed:** 4.2 keeps the LHCI list complete for known sections/types; 4.3 auto-extends as the site grows (new shortcode → first essay using it gets audited automatically).

**Pick-up trigger:** After 4.2 lands and the fingerprint corpus is observable. Risk: fingerprint noise — needs the namespace allowlist to be useful.

## Original "why filed" (preserved)

B.4 push 2026-05-31 evening got 404'd by LHCI twice in a row (5-min round-trips) — first on retired `/essays/example-essay-one/` (B.4 fixture handover not propagated to lighthouserc configs), then on retired `/research/themes/memory-and-play/` + `/research/questions/what-is-a-narrative-atom/` (B.3 leftover). 4.1 closed this round-trip class as of 2026-06-04.
