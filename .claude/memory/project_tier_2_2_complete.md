---
name: project-tier-2-2-complete
description: Tier 2.2 D.1 cross-reference auto-formatting shipped 2026-06-08; ref-block shortcode + scratch-write across 11 numbered AMS blocks
metadata: 
  node_type: memory
  type: project
  originSessionId: df0f8dca-53dd-4978-ad74-36f105a7b286
---

**Shipped 2026-06-08.** Roadmap row 2.2 — D.1 cross-reference auto-formatting via a new `ref-block` shortcode.

**Behavior:**
- New `layouts/shortcodes/ref-block.html` — takes one positional arg (the block id), looks up `$page.Scratch.Get (printf "block-label-%s" $id)`, renders `<a class="ref-block" href="#thm-foo">Theorem 1</a>` on hit.
- On miss: renders `<a class="ref-block ref-block-unresolved" ...>{id}</a>` — visible warning style (mono font, `--color-warn`, dashed underline) so authors notice unresolved refs.
- Each of the 11 numbered AMS shortcodes (theorem / lemma / corollary / proposition / definition / remark / example / note / claim / conjecture / axiom) writes `block-label-{id} → "{Kind} {n}"` to scratch right after the counter increments. Proof is unnumbered → no scratch write → not addressable by ref-block.

**Why this approach:**
- Hugo renders shortcodes top-to-bottom on each page; there is no native second-pass. Backward refs (target block comes BEFORE the ref-block call) resolve at server-side. Forward refs (target block comes AFTER) fall back to the bare id — visible to author during proofing.
- The roadmap row mentioned "two-pass scratch lookup" but Hugo doesn't support that natively. A client-side JS upgrade for forward-refs is an option for later — for now, the documented forward-ref limitation is acceptable because in AMS-style writing, refs after the block are the dominant pattern.
- Each shortcode change is a single inserted line — minimal blast radius.

**Fixture-first per [[feedback-trigger-gated-make-fixture]]:**
- `content/essays/example-blocks-crossref/` — 4 sections: backward (block-then-ref), forward (ref-then-block), broken (id never on page), coverage (all 11 kinds). Renders the scratch resolution + the unresolved-warning state side-by-side.

**Changes:**
- `layouts/shortcodes/ref-block.html` — new (~22 LOC including comments).
- 11 shortcodes updated: `{{- $page.Scratch.Set (printf "block-label-%s" $id) $aria -}}` inserted right after the no-title `$aria` is computed (before the with-title branch).
- `assets/css/main.css` §47 — added `.ref-block` (resolved: burgundy + underline) + `.ref-block-unresolved` (warn-yellow + mono + dashed underline) selectors.
- `content/essays/example-blocks-crossref/index.md` — new fixture.
- `CLAUDE.md` — semantic-blocks section updated to document ref-block + forward-ref limitation.

**Tests:**
- `tools/check_anchor_link.py`: OK (block-* container scan unaffected — the ref-block links don't carry ids themselves).
- Full ci-local.sh: green (27 linters + Hugo build; LHCI skipped per [[reference-ci-local-lhci-deps]]).
- Visual eyeball: dev server at `/essays/example-blocks-crossref/` shows the three cases distinctly.

**Forward-ref limitation — documented options for later:**
- Client-side JS upgrade: scan `.ref-block-unresolved`, lookup `#id` block-header in DOM, rewrite text. ~30 LOC; lightweight; lossy on no-JS (acceptable).
- Hugo two-pass via custom output format: complex; not worth it unless many essays hit forward-refs.

**Related:** [[project-d1-complete]] · [[project-tier-2-4-complete]] · [[feedback-trigger-gated-make-fixture]]
