---
name: reference-ox-hugo-doubles-backslash-escape
description: ox-hugo doubles literal backslash in paragraph text — org `\[mm:ss]` → markdown `\\[mm:ss]`. Runtime parsers expecting single-backslash must collapse post-export.
metadata:
  type: reference
---

# ox-hugo doubles literal backslashes in paragraph text

Empirically verified during Tier 8.2 Task 0 reconnaissance (2026-06-12):

Org source:
```
[00:17]Duis aute \[00:99] reprehenderit
```

ox-hugo markdown output:
```
[00:17]Duis aute \\[00:99] reprehenderit
```

The org-source single-backslash escape `\[` becomes a markdown double-backslash `\\[`. This is ox-hugo's paragraph-text serialization behavior (markdown round-trip safety for backslashes).

**Consequence:** any runtime parser that treats `\[mm:ss]` as an escape sentinel (e.g. `layouts/partials/works/synced-text-parser.html:21` regex `\\\[(\d…)\]`) will get confused by the doubled form. The Goldmark render also unescapes `\\` → `\`, leaving the rendered HTML with a stray `\` in front of the escaped marker.

**How to apply:**

- If you're authoring a handler that ships markdown emitted by ox-hugo AND the runtime expects single-backslash escape semantics, add a post-export collapse pass before `write-if-different`.
- Pattern (works-poetry handler — `a3madkour-publish-poetry.el`):
  ```elisp
  (defun a3madkour-pub-poetry--collapse-escaped-markers (md)
    (replace-regexp-in-string
     "\\\\\\\\\\(\\[[0-9]\\{1,2\\}:[0-9]\\{2\\}\\(?:\\.[0-9]\\{1,2\\}\\)?\\]\\)"
     "\\\\\\1"
     md t))
  ```
  The regex (in elisp string syntax with the magic 4-backslash → 2-literal-backslash → 1-regex-backslash conversion) matches `\\[mm:ss]` literally and replaces with `\[mm:ss]`.
- Simpler than the alternative protect-and-restore (replace `\[` with a sentinel before export, swap back after) — single regex pass after the export buffer is already a string.
- The spec's risk note (§Risks #1) anticipated this as "Case B" (consumed) but reality was "Case C" (doubled). Either case requires the same kind of fix.

**Reconnaissance command** (kept for re-verification when ox-hugo upgrades):

```bash
emacs --batch -l ox-hugo --visit=/tmp/test.org \
  --eval "(setq-local org-hugo-base-dir \"/tmp/recon-hugo\")" \
  --eval "(org-hugo-export-to-md)"
```

Source: [[project-tier-8-2-complete]] Task 0 + Task 6.
