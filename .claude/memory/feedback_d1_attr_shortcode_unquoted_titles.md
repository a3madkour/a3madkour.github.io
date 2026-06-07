---
name: feedback-d1-attr-shortcode-unquoted-titles
description: "D.1 attr_shortcode :title must be unquoted single-word — ox-hugo's special-block attr parser includes surrounding quotes in the value, which Hugo then double-HTML-escapes"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4af348b0-8716-4f87-a22c-765743be0ab4
---

**STATUS — 2026-06-07: HISTORICAL.** Bug fixed in dotfiles `31f9570` (Tier 1.7); post-export sanitizer strips stray `&quot;` wrappers from shortcode attrs. Multi-word `:title "Multi word"` now round-trips correctly. See [[tier-1-7-complete]]. The rule below is preserved as a record of prior behavior; you can ignore it for new content.

**Rule (historical):** In D.1 `#+attr_shortcode:` headers, use unquoted single-word `:title` values. Do NOT quote with `"..."`.

  - OK: `#+attr_shortcode: :title Pythagorean :id thm-pyth`
  - BROKEN: `#+attr_shortcode: :title "Pythagorean theorem" :id thm-pyth`

**Why:** ox-hugo reads `#+attr_shortcode` via `org-export-read-attribute :attr_shortcode` and then calls `org-html--make-attribute-string` to convert to a shortcode call. The org attr parser preserves surrounding quote chars in the value string — `:title "X"` parses to `(:title "\"X\"")`. ox-hugo emits this as `{{< theorem title="&quot;X&quot;" >}}`, and Hugo HTML-escapes the `&quot;` again, so the rendered page shows `&amp;quot;X&amp;quot;` inside `<span class="block-title">`.

**How to apply:** When writing AMS blocks (theorem / lemma / corollary / proposition / definition / claim / conjecture / axiom / remark / example / note) in essays for B.4 publish, keep block titles short and unquoted. Multi-word titles need a real ox-hugo fix (deferred — investigated 2026-06-04 D.2 follow-up, no real content uses multi-word titles yet).

When multi-word titles become a real need, the fix sits in one of: (a) a custom ox-hugo special-block translator that strips quotes from attr values, (b) a pre-export buffer rewrite in our multi-filter for the hugo backend (already exists for latex/pandoc via `--translate-vocab`'s attr extraction).
