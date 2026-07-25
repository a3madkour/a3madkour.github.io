---
name: reference_verify_template_refactor_minified
description: "Verify Hugo template-consolidation refactors against the MINIFIED build, not raw — raw preserves per-source whitespace/attr-order the minifier erases"
metadata: 
  node_type: memory
  type: reference
  originSessionId: a4b4e454-fc0d-4ae8-8172-2c36574d9f94
---

When consolidating multiple Hugo partials/templates into one shared partial and checking for "no rendered change," diff the **minified** build (`hugo --gc --minify`, what ships), NOT raw output.

Why: raw Hugo output preserves each source file's whitespace and HTML attribute order verbatim. Three partials that differ only in `<aside>` line-breaking / attribute order render byte-different raw, so a single shared partial can't reproduce all of them raw — a raw diff over-flags cosmetic formatting that never ships. The minifier (tdewolff) normalizes whitespace + strips optional quotes.

Caveat: the minifier does **preserve attribute order**, so a source whose attributes were ordered differently than the shared partial shows a cosmetic attribute reorder in the minified diff too — semantically inert (attribute order is irrelevant to browsers/CSS/`getElementById`/attribute selectors). To gate rigorously, don't require byte-identity everywhere; instead: (a) confirm the section whose source order matches the partial is byte-identical, and (b) for the others, assert the change is localized (pre/post-region identical) + all semantic tokens preserved via a small python check.

Discovered in R5.3b (3 graph-panel partials → one shared partial). See [[audit-r5-3b-complete]]. Contrast R5.3a (AMS blocks), where raw byte-identity WAS achievable because the shortcode-output formatting matched.
