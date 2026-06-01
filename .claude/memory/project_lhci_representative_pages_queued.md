---
name: project-lhci-representative-pages-queued
description: "Queued slice — fix LHCI URL drift via curated+validated set, sitemap-derived, or visual-feature autodetect. Filed 2026-06-01 after B.4 push caught two consecutive 404 round-trips"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5145878a-a130-45b0-84d6-28c736593219
---

# LHCI representative page set — queued

**Stub spec:** `docs/superpowers/specs/2026-06-01-lhci-representative-page-set-design.md`. No plan until pick-up; per [[feedback_design_batch_no_plan_until_implement]].

**Why filed:** B.4 push 2026-05-31 evening got 404'd by LHCI twice in a row (5-min round-trips) — first on retired `/essays/example-essay-one/` (B.4 fixture handover not propagated to lighthouserc configs), then on retired `/research/themes/memory-and-play/` + `/research/questions/what-is-a-narrative-atom/` (B.3 leftover). Drift class will recur on B.5/B.6/B.7.

**How to apply:** When picking up B.5 (works handler) or any subsequent fixture-retirement slice, the LHCI URL list in `lighthouserc.json` + `lighthouserc.mobile.json` MUST be re-validated against the retiring slugs before push. Until this slice ships, that re-validation is manual. After it ships, it's automated (option 4.1 = pre-LHCI URL validator) and ideally derived (option 4.2 = sitemap-grouped by Hugo Kind/Section/Type) or autodetected (option 4.3 = visual-feature fingerprint).

**Recommendation:** Ship 4.1 first (~1 hour, kills the round-trip). Defer 4.2 + 4.3 until a real shortcode/template family addition makes them load-bearing.

**Pick-up triggers:**
- Next fixture retirement (B.5 works) — third drift event would justify the slice cost.
- A new shortcode/layout lands without an LHCI URL update.
