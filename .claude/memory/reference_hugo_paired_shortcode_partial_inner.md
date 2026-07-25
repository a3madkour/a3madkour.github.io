---
name: reference_hugo_paired_shortcode_partial_inner
description: "Paired shortcode delegating to a partial must reference .Inner literally in the wrapper, else Hugo rejects the closing tag"
metadata: 
  node_type: memory
  type: reference
  originSessionId: a4b4e454-fc0d-4ae8-8172-2c36574d9f94
---

When a **paired** shortcode (`{{< theorem >}}…{{< /theorem >}}`) delegates its render logic to a partial, the thin wrapper must reference `.Inner` (or `.InnerDeindent`) **literally in the shortcode template source**, or Hugo hard-errors at build ("does not evaluate .Inner") and the closing tag is invalid.

Why: Hugo decides whether a shortcode is paired by a static text scan of the *shortcode file* for `.Inner`/`.InnerDeindent` — it does not follow into partials. A wrapper like `{{ partial "x" (dict "ctx" .) }}` never mentions `.Inner`, so the scan fails.

Fix: pass `.Inner` through the dict as a parser hint, e.g.
`{{- partial "ams-block.html" (dict "ctx" . "inner" .Inner "kind" …) -}}`
The `inner` key can be unused — the partial reads `$ctx.Inner` (same object, no divergence). The literal `.Inner` in the wrapper source is all Hugo's parser needs.

Discovered in R5.3a (11 AMS block shortcodes → wrappers over `ams-block.html`). See [[audit-r5-3a-complete]].
