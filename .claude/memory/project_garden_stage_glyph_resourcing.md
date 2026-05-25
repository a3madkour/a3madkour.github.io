---
name: project-garden-stage-glyph-resourcing
description: Garden stage-glyph re-source + greens-only color ramp — shipped to master 2026-05-20
metadata: 
  node_type: memory
  type: project
  originSessionId: 8caf3e9e-8507-4cbc-ba75-2c7d1554b7ab
---

**Shipped 2026-05-20.** Direct master commit `be68e29` (pushed `f155d82..be68e29`).

Two threads in one commit:

**1. Re-sourced the three inlined stage glyphs** in `layouts/partials/garden/stage-glyph.html` from unattributed AI-drafted paths to Lucide v1.16.0 ISC: seedling=`sprout`, budding=`leafy-green`, evergreen=`trees`. Attribution added to the partial's top comment, three rows added to `THIRD_PARTY.md` under a new "Inlined in templates" subsection, `/credits/` updated from "11 SVG icons" to "14 icons (11 file-based + 3 inlined)". `/about/` Colophon already links to `/credits/` — no edit needed; the link IS the citation pattern. Closes one more case from [[feedback-icon-provenance-required]]'s "11 existing icons … need re-sourcing" backlog (those 11 were the file-based icons under `assets/images/icons/`, all done previously; these 3 inlined ones were a separate gap surfaced by the user noticing seedling art looked AI-generated).

**2. Replaced the brand-accent stage palette** with a greens-only ramp. Was `--color-burgundy` (seedling) / `--color-steel` (budding) / `--color-green` (evergreen) — flagged by user as semantically confused (burgundy is overloaded across the site: nav active, link hover, filter-chip active, abandoned status — reading it ALSO as "seedling stage" muddied the rule; steel reads as "link/info" in web conventions). New tokens added in all three palette blocks (`:root`, `[data-theme="dark"]`, `@media prefers-color-scheme: dark`):

- `--color-green-soft` (seedling): light `#4f7058` 4.76:1 AA · dark `#b8d6c0` 11.35:1 AAA
- `--color-green-mid` (budding): light `#3a624a` 5.97:1 AA · dark `#9ecaab` 9.72:1 AAA
- `--color-green` (evergreen, unchanged): 6.83:1 AA · 8.47:1 AAA

`tools/check-contrast.py` extended from 6 to 9 pairings (the 3 green stops at AA 4.5+). CLAUDE.md updated to reflect new linter count + the green ramp's role. All three light-mode shades were tuned via the linter's own ratio function to land safely above 4.5:1 (the first-pass sage values I'd proposed in the companion at 3.4-4.2:1 all failed AA; [[feedback-verify-contrast-ratios]] caught this before any commit).

**Workflow that worked well:** three iterations of the visual companion HTML at `/tmp/seedling-companion.html` served via `python3 -m http.server 8765` — v1 was per-stage swap-outs, v2 was trios-as-sets after the user pushed for visual coherence ("the original had a good progression of small sprout and budding being a bigger plant"), v3 was the same trio with four color-palette comparisons after the user flagged the burgundy/steel red/blue semantics. Each rev took ~5 minutes; the iteration was load-bearing because color and shape decisions are visual, not verbal — confirms [[feedback-visual-companion-for-visual-designs]].

**CI caveat (non-blocker):** `tools/ci-local.sh` flagged the documented `/garden/` mobile-LHCI local-CPU-variance (perf 0.83 vs 0.9 threshold, single page only, all other 11 URLs passed). Per [[reference-ci-local-lhci-deps]] this is the ~5-8 point variance band; the change was pure CSS tokens + linter additions (no JS, no bundle change) so a real perf regression here is implausible. Cloud CI run `26189743117` started immediately after push.

See also: [[feedback-icon-provenance-required]], [[feedback-semantic-consistency-site-wide]] (the "burgundy means interactive everywhere" rule that the old palette violated), [[feedback-verify-contrast-ratios]], [[reference-ci-local-lhci-deps]].
