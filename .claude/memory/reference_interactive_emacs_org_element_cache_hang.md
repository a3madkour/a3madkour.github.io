---
name: reference-interactive-emacs-org-element-cache-hang
description: "org-map-entries + buffer-mutating callback (org-set-tags, delete-region) hangs interactive Emacs even with inhibit-modification-hooks — switch to regex-only rewrite outside of org-element"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 4af348b0-8716-4f87-a22c-765743be0ab4
---

**Trap:** Pre-export buffer rewrites that combine `org-map-entries` (or any function that scans via `org-element-cache-map`) with a callback that MUTATES the buffer — even when wrapped in `(let ((inhibit-modification-hooks t)) …)`. Each mutation invalidates the org-element cache, the next entry visit re-parses from the top, and on a real-sized publish buffer this turns into an effective hang (visible Lisp backtrace into `org-element-paragraph-parser`).

**Fix pattern:**
1. **Best**: drop org-element entirely. Replace the loop with `(while (re-search-forward HEADLINE-REGEX nil t) …)` and a direct text rewrite (`delete-region` + `insert`, or `replace-match`). No org-element involvement, no cache traffic.
2. **If org-element is required**: use the collect-then-mutate pattern. Scan first with `org-map-entries` returning a list of positions/match-strings (NO mutations in the callback). Then iterate the collected list in reverse order with mutations outside any org-element-aware function.

`inhibit-modification-hooks` does NOT save you — that only suppresses the `before-change-functions` / `after-change-functions` hooks, not the org-element cache's own invalidation.

**Bit twice in the D.2 session (2026-06-03):**
- First: `--translate-vocab` did loop-and-edit inside `re-search-forward` with `org-element` queries in the callback. Hung interactive Emacs. Fixed by collecting positions first, then mutating end-to-start. Dotfiles commit `21ce44a`.
- Second: `--strip-visibility-tags` initially used `org-map-entries` + `org-set-tags` inside the callback. User got a Lisp `(quit)` backtrace into `org-element-paragraph-parser` after ~30s wait. Fixed by switching to regex-only rewrite outside org-element. Dotfiles commit `6795951`.

**How to apply:** ANY pre-export buffer rewrite under `org-export-before-processing-functions` that's a loop-and-edit should be either regex-based (no org-element calls in the body) OR collect-then-mutate. If your prototype uses `org-map-entries` + buffer mutation inside the callback, assume it'll hang interactive Emacs even though batch tests pass — batch mode disables some cache behaviors.

Related: [[reference-org-set-tags-clobbers-match-data]] (the regex-only rewrite has its OWN trap from string-op match-data clobbering — capture positions before any `split-string` / `member`).
