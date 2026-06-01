---
name: reference-lhci-kitchen-sink-essay-variance
description: Mobile LHCI perf on /essays/example-one/ swings 0.83-0.93; kitchen-sink essay sits right at the 0.9 threshold under mobile throttling; rerun clears flakes
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5145878a-a130-45b0-84d6-28c736593219
---

# LHCI mobile flakes on the kitchen-sink essay

Observed 2026-06-01: `/essays/example-one/` failed mobile LHCI perf with 0.83 (threshold 0.9). Triggered a `gh run rerun --failed` with NO code change. Rerun passed.

**Why it sits right at the line:** example-one is the B.4 kitchen-sink stub — hero SVG + 6 different shortcodes (cite/sidenote/footnote/math/widget/video-sync) + 3 figure renders of hero.svg + a code block + level-4 TOC nesting. Mobile LHCI CPU throttling (4x default) is enough variance to swing perf score ±0.05 on this URL.

**How to apply:**
- Do not change `lighthouserc.mobile.json` thresholds in response to a single failure.
- First action on `/essays/example-one/` mobile-perf failure: `gh run rerun <id> --failed`.
- If it fails 2+ times consecutively → real budget exceedance; either switch the LHCI URL to a lighter essay (`/essays/example-three/` is minimal — bare body, no shortcodes) or trim shortcodes from example-one.
- Architectural fix is the queued slice [[project_lhci_representative_pages_queued]] — auto-detect when a new visual feature warrants an LHCI URL and pick the lightest representative per layout.

Related: [[reference_lhci_google_fonts_flakiness]] (the prior LHCI flake class, now mitigated by self-hosting fonts) and [[reference_ci_local_lhci_deps]] (local-vs-CI LHCI behavior).
