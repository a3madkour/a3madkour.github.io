---
name: goldmark-unsafe-for-ox-hugo-html
description: "Hugo's Goldmark renderer defaults to unsafe:false and silently strips inline HTML from markdown — replacing it with `<!-- raw HTML omitted -->`. B's per-section publishers emit anchors via ox-hugo's `@@html:...@@` export snippet syntax, which produces raw HTML in the markdown body. Without `markup.goldmark.renderer.unsafe = true` in hugo.yaml, the anchors silently disappear from rendered pages."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 1e3eb273-5835-4b22-88ad-5642b85830f5
---

ox-hugo's `@@html:<content>@@` export snippet syntax is the standard mechanism for emitting raw HTML into the markdown body. It's the right tool when the elisp pipeline needs to bypass org's normal link rendering (e.g., B.1.1's `rewrite-buffer-links` substituting `[[id:UUID]]` with `<a href="/garden/<slug>/">text</a>`).

But Hugo's Goldmark markdown renderer defaults to `unsafe: false` — at render time, raw HTML inside paragraph content gets stripped and replaced with `<!-- raw HTML omitted -->`. The markdown file on disk is correct; the rendered `public/<path>/index.html` shows plain text where anchors should be.

This is **not surfaced by**:
- the elisp ert test suite (asserts on `:body` plist from `export-file`, never invokes Hugo)
- the Python integration fixture `test_garden_publish_with_cross_link` (asserts on emitted `index.md` markdown, never invokes Hugo)
- `hugo --minify` exit code (treats it as a WARN, not an error)

The only signals are:
- `WARN  Raw HTML omitted while rendering "..."` in `hugo --minify` output
- `grep "raw HTML omitted" public/...` finds the comment markers in rendered HTML
- visual eyeball of the rendered page

## Fix

Add to `hugo.yaml`:

```yaml
markup:
    goldmark:
        renderer:
            unsafe: true
```

This is safe for **author-controlled content** (no user submissions). Don't enable on a CMS-style site where untrusted authors can ship markdown.

## How to apply

Future B.x handlers (library, research, essays, works) all reuse the same `--rewrite-to-tmp-file` + `rewrite-buffer-links` pattern, so the `@@html:` flow applies site-wide. The `unsafe: true` config covers all of them.

If a future site adopts a similar architecture but inherits its own hugo config, double-check this setting first. Without it, the rewriter silently emits broken pages.

Originally caught by [[b1-complete]]'s round-3 spot-check (2026-05-26) — the in-batch tests passed but rendered HTML had `<!-- raw HTML omitted -->` where anchors should be.
