---
name: reference-dotfiles-keywords-api
description: "Use `a3madkour-pub-keywords/extract` + `boolean-p` for any new `#+keyword:` read in dotfiles publisher modules — never re-implement with `org-collect-keywords` + `cadar`"
metadata: 
  node_type: memory
  type: reference
  originSessionId: d7fc28b7-3a2d-4df8-9f6f-fceb6b93385a
---

**API:** `a3madkour-publish-keywords.el` in `~/dotfiles/emacs-configs/custom/lisp/` exports:

- `(a3madkour-pub-keywords/extract KEY)` → string value or nil; uses a buffer-local regex scan (lightweight, no org-element dependency).
- `(a3madkour-pub-keywords/boolean-p V)` → t iff V is `"t"` (case-insensitive, strict).
- `(a3madkour-pub-keywords/parse-aliases V)` → alias list parsing.

**Canonical composition pattern** (mirror this; see `a3madkour-publish.el` around line 108–122):

```elisp
(let ((publish-p (a3madkour-pub-keywords/boolean-p
                  (a3madkour-pub-keywords/extract "HUGO_PUBLISH"))))
  …)
```

**Why this matters:**
- Used by every publisher module: `a3madkour-publish.el` (HUGO_PUBLISH / HUGO_DRAFT / HUGO_ALIASES), `a3madkour-publish-frontmatter.el`, etc.
- Re-implementing with `org-collect-keywords` + `cadar` + inline `downcase`/`string-trim` works but (a) duplicates the contract and can drift, (b) pulls `org-element` into the load graph for what should be a cheap pre-export filter, (c) couples to an underdocumented return shape.

**Where I lapsed:** D.2 Task 1 (`a3madkour-publish-multi-filter--doc-p` for `#+multi_export:`) re-implemented this in the first pass. Caught by code-quality review; fixed in commit `d5205ff`. Plan-author missed checking sibling modules.

**How to apply:** Any new dotfiles publisher module that reads a `#+keyword:` value (boolean or string) must `(require 'a3madkour-publish-keywords)` and compose `extract` + (optionally) `boolean-p` / `parse-aliases`. Grep `keywords/extract` before writing any new keyword-reading code.

Related: [[feedback-class-rename-grep-full-codebase]] — same lesson, different domain (grep the codebase first).
