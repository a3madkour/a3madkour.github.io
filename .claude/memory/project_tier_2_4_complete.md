---
name: project-tier-2-4-complete
description: Tier 2.4 anchor-affordance H4-H6 skip shipped 2026-06-08; fixture-first per trigger-gated feedback rule
metadata: 
  node_type: memory
  type: project
  originSessionId: df0f8dca-53dd-4978-ad74-36f105a7b286
---

**Shipped 2026-06-08.** Roadmap row 2.4 — anchor-affordance heading-level tuning.

**Behavior change:**
- `layouts/_default/_markup/render-heading.html` — heading render hook gates the anchor-link emission on `{{ if and $id (lt .Level 4) }}`. H4/H5/H6 IDs still render (Goldmark auto-IDs are preserved for TOC + direct URL navigation), but no §-glyph attaches.
- `tools/check_anchor_link.py` — `_HEADING_TAGS` narrowed from `{h1..h6}` to `{h1, h2, h3}`. The linter no longer requires an anchor-link sibling for H4-H6 markdown headings. AMS block-header H4s (`<h4 class="block-header">` inside `<div class="block-*">` containers) are unaffected — the linter's BLOCK pending mode tracks via the container, not the inner heading.

**Fixture-first per [[feedback-trigger-gated-make-fixture]]:**
- Authored `content/essays/example-h4-density/index.md` — deliberately stressed density signature: 9 H4s across 4 H3s in 2 H2s.
- Built the BEFORE state (`hugo --minify`), confirmed 9 H4 §s; built the AFTER state, confirmed 0 H4 §s + H2/H3 §s preserved + linter green.
- Dev-server spot-check at `/essays/example-h4-density/` — TOC still lists all H4s for navigation; body just doesn't carry the §-glyph there.

**CLAUDE.md updates:**
- Anchor-link affordance section — "headings `<h2>`–`<h6>`" → "headings `<h2>`–`<h3>`" + explanatory sentence at end of section pointing at the render hook + linter narrowing.

**Tests:**
- `tools/check_anchor_link.py`: OK.
- Full ci-local.sh: green (27 linters + Hugo build; LHCI skipped per [[reference-ci-local-lhci-deps]]).

**Not changed:**
- D.1 block-shortcode anchor-links (unrelated; still emit via `{{ partial "anchor-link.html" }}` inside each shortcode).
- Goldmark heading IDs themselves (still emitted for TOC + URL fragments).
- The `data-no-anchor-link` per-element opt-out (still works).

**Why H4-H6 not just H4:** The trigger was "H4 §s feel dense." H5/H6 are even more density-prone but rare in practice (no fixtures use them). Skipping all three in one cap keeps the rule simple and matches the GitHub / MDN / Wikipedia convention of capping deep-link affordances at H3.

**Related:** [[project-anchor-affordance-complete]] · [[feedback-trigger-gated-make-fixture]]
