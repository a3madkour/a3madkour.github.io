---
name: ox-hugo-id-links-become-relref
description: "ox-hugo translates `[[id:UUID][text]]` org-link bracket form to `[text]({{< relref \"<underscore_filename>.md\" >}})` — regardless of target publish state. This breaks Hugo's relref resolution when the target's actual bundle uses hyphen-slug paths."
metadata:
  node_type: memory
  type: reference
---

When ox-hugo exports an org file containing `[[id:UUID][text]]` org-roam links, it resolves the UUID to a target file via the org-roam DB and emits a Hugo `relref` shortcode pointing at the underscore-named markdown filename:

```
[[id:09049cd8-...][Bayesian Statistics]]
  ↓ ox-hugo export
[Bayesian Statistics]({{< relref "bayesian_statistics.md" >}})
```

Three problems with this output for the a3madkour.github.io publisher:

1. **Filename mismatch.** ox-hugo uses the source file's basename (with `.md` extension) for the relref target. B-emitted bundles live at `content/<section>/<hyphen-slug>/index.md`. So `bayesian_statistics.md` looks for `content/.../bayesian_statistics.md` which doesn't exist — the actual page is at `content/garden/bayesian-statistics/index.md`. Hugo errors with `REF_NOT_FOUND`.

2. **Unpublished targets blow up too.** ox-hugo still emits the relref shortcode for a target that won't be published. Hugo build errors regardless of whether we wanted that link "muted" (per A.1 spec §6 the unpublished-target case should render as inert plain text).

3. **All link types get translated.** `[[id:...]]`, `[[file:...]]`, typed links like `[[supports:UUID]]` all get the relref treatment, so any fix has to handle all of A.1's link schemes.

## How to fix

**Pre-export buffer rewriting** is the cleanest fix (architectural call made in [[b1-complete]] round-2 spot-check): before invoking ox-hugo, scan the source for `[[...]]` patterns, apply A.1's `a3madkour-pub/rewrite-link` to each, substitute with the returned `:html` (resolved) or `:inert` (unresolved) text. ox-hugo never sees the bracket form; markdown passes raw HTML through to Goldmark.

The alternatives — post-export string substitution on the emitted relref shortcodes, or `org-link-set-parameters` hooks that customize ox-hugo's id-link export — both work but require either filename→note-id mapping or global mutation of org's link parameters. Neither is simpler than the buffer rewrite.

## How to apply

If you're working on the B publisher pipeline and a section handler emits content that ends up with broken internal links in `hugo --minify`, this is almost certainly the cause. Don't try to fix Hugo's relref resolution (e.g., adding aliases); pre-process the source before ox-hugo sees it.
