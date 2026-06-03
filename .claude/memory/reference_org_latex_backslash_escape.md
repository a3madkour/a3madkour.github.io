---
name: reference-org-latex-backslash-escape
description: "`org-latex-plain-text` converts `\\` to `$\\backslash$`; to emit raw LaTeX from a pre-export buffer rewrite, use the `@@latex:...@@` export-snippet form"
metadata: 
  node_type: memory
  type: reference
  originSessionId: d7fc28b7-3a2d-4df8-9f6f-fceb6b93385a
---

**Trap:** any literal `\` in a plain-text org node gets converted to `$\backslash$` by `org-latex-plain-text` (verified at `~/.emacs.d/straight/build/org/ox-latex.el:3254`). So buffer-rewriting `[[#id][text]]` → `\hyperref[id]{text}` as plain org text produces `$\backslash$hyperref[id]{text}` in the `.tex` output — math-mode backslash glyph + literal text, not a `\hyperref` command.

**Fix:** emit org's export-snippet form:

```elisp
;; In a pre-export hook that mutates the buffer:
(replace-match (format "@@latex:\\hyperref[%s]{%s}@@"
                       (match-string 1) (match-string 2))
               t t)
```

- Inside `format`, `"\\hyperref"` produces `\hyperref` (one backslash).
- `@@latex:...@@` is org's export-snippet syntax; `org-latex-export-snippet` extracts the content verbatim (no escaping) when backend is `latex`.
- The snippet is invisible to other backends — pandoc / md just drop it.

**Escape-count gotcha:** elisp escaping rules differ depending on whether the string flows through `replace-match`'s replacement-string parser or just through `format`. For `format` going into `replace-match` with `LITERAL=t`, the buffer content equals the formatted string verbatim — so use `"\\hyperref"` (4 chars) for `\hyperref` (1 backslash). With `LITERAL=nil` the replacement-string parser would double the backslash again.

**Where I lapsed:** D.2 Task 3 first emitted `\hyperref` as plain text. Caught by code-quality review. Fixed in commit `25db8ee` in dotfiles. The escape miscount was caught a second time during the fix (implementer used `"\\\\hyperref"` per my over-prescriptive instruction; tests caught it; fix re-applied).

**How to apply:** Any pre-export buffer rewrite that needs to emit raw backend-specific text must use the matching `@@<backend>:...@@` snippet form. Same applies to HTML (`@@html:`) and md (`@@md:`).
