---
name: project-tier-2-3-complete
description: "Tier 2.3 D.1 section-prefixed numbering shipped 2026-06-11; per-essay opt-in via frontmatter; client-side JS post-process (Hugo can't do it server-side)"
metadata: 
  node_type: memory
  type: project
  originSessionId: df0f8dca-53dd-4978-ad74-36f105a7b286
---

**Shipped 2026-06-11.** Roadmap row 2.3 — D.1 section-prefixed numbering with per-essay opt-in.

**Behavior:**
- Per-essay opt-in: frontmatter `block_numbering: "section-prefixed"`.
- `layouts/_default/baseof.html` emits `data-block-numbering="<value>"` on `<main>` when the param is set; absent attribute = bare integers (no behavior change for existing essays).
- `assets/js/block-renumber.js` runs on `DOMContentLoaded` (or sync if already past), gated on `main.dataset.blockNumbering === 'section-prefixed'`. Single-pass walks `h2[id]` + every `div[class~="block-{kind}"]` in document order, increments a per-section counter for the block's family (theorem-family shared / others per-kind), rewrites the `.block-header` leading "Kind N" to "Kind M.N" via tree-walker over the header's text nodes (first match wins so titled blocks `Theorem 1 (Foo)` still rewrite cleanly), records `id → label` in a map. Second pass rewrites all `.ref-block[href^="#id"]` to match — and clears the `.ref-block-unresolved` class on refs that now resolve.
- Loaded via `entry-essay.js` (existing essay bundle, no new entry needed). Pages without the frontmatter flag short-circuit immediately — no DOM walk cost.

**Why client-side:**
- Hugo's shortcode model runs theorem/lemma/etc. shortcodes BEFORE Goldmark processes the surrounding markdown. At theorem-render time the surrounding H2s don't exist yet — no way for the shortcode to know "what section am I in."
- Three workarounds were considered: (a) JS post-process; (b) author-typed `section="3"` on each block; (c) drop the AMS shared counter for per-kind counters. The user picked (a) — cleanest authoring, no new conventions, gracefully degrades to bare integers without JS.

**Fixture-first per [[feedback-trigger-gated-make-fixture]]:**
- `content/essays/example-long-numbering/` — 5 H2 sections, 14 numbered blocks; opted in via frontmatter. Was first authored without the opt-in flag (showing bare integers) to discuss the design; user picked path A; the JS module + opt-in were then added and the fixture's trailing prose was rewritten from "navigability problem" to "implementation notes" since it now demonstrates the working feature.

**Why the "skipping numbers" UX cost was acceptable to keep:**
- AMS shared-counter convention (theorem/lemma/corollary/proposition share `theorem-family`) creates the appearance of skipped numbers in long essays — Theorem 1 → Lemma 2 → Theorem 3 → ... → Theorem 12. The rationale is cross-reference uniqueness: "Theorem 2.7" identifies one block; with per-kind counters you'd have both a Theorem 7 AND a Lemma 7, breaking ref-uniqueness.
- With section-prefix shipped (Tier 2.3), the skipping perception is largely hidden — counters reset per H2, so adjacent blocks now read `Theorem 5.1 → Lemma 5.2 → Theorem 5.3` rather than jumping by global counts.

**Changes:**
- `assets/js/block-renumber.js` — new, ~95 LOC including comments.
- `assets/js/entry-essay.js` — imports + DOMContentLoaded wire.
- `layouts/_default/baseof.html` — `<main>` carries `data-block-numbering` when frontmatter set.
- `content/essays/example-long-numbering/index.md` — new fixture, opted-in.
- `CLAUDE.md` — semantic-blocks section gets a "section-prefixed numbering" paragraph.

**Tests:**
- Full ci-local.sh: green (27 linters + Hugo build; LHCI skipped per [[reference-ci-local-lhci-deps]]).
- Visual eyeball: opted-in fixture (`example-long-numbering`) shows `Kind M.N` everywhere; non-opted fixtures (`example-blocks-crossref`, `example-five`, `example-multi`) still show bare integers (no regression).
- Brief flash of bare integers before JS runs is observable on slow loads — sub-100ms on normal connections. Acceptable per per-essay opt-in scope.

**Caveats / not-shipped:**
- No three-level numbering (e.g., `Theorem 3.1.1`). H3+ doesn't reset the per-section counter — block kept at H2-section granularity only.
- No CSS to mask the brief pre-JS flash. If the flash becomes annoying with real content, a `[data-block-numbering] .block-header { visibility: hidden; }` + `.block-renumber-done .block-header { visibility: visible; }` toggle would work; not shipped today.
- `block_numbering` frontmatter isn't validated against an allowlist by `tools/check_fixtures.py` — keeping it as a free-form string for forward compatibility (future values could be `"section-h3-prefixed"` etc.).

**Related:** [[project-tier-2-2-complete]] · [[project-d1-complete]] · [[feedback-trigger-gated-make-fixture]]
