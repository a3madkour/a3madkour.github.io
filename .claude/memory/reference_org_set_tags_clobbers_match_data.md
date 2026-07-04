---
name: reference-org-set-tags-clobbers-match-data
description: "Inside a re-search-forward loop, split-string and member silently clobber match-data via their internal regex ops — capture match positions and strings BEFORE any non-trivial string operation"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 4af348b0-8716-4f87-a22c-765743be0ab4
---

**Trap:** In a `while (re-search-forward …)` loop that mutates the buffer, helper functions like `split-string`, `string-match`, and `member` (when called on strings containing regex metacharacters) silently overwrite `match-data` via their own internal regex matching. Any later `replace-match`, `match-string`, `match-beginning`, or `match-end` then reads stale positions and the rewrite lands at the wrong offset.

**Symptom:** The original match content appears DUPLICATED in the buffer after replace, plus mangled chunks of the original interlaced with the replacement string. e.g. for `* Kept :NOEXPORT_WORD:draft:` you get `* Kept * Kept\t:draft:NOEXPORT_WORD:draft:` instead of `* Kept\t:draft:`.

**Fix pattern:** capture `(match-beginning 0)`, `(match-end 0)`, and any `(match-string N)` values you'll need into local `let*` bindings IMMEDIATELY after `re-search-forward`, before calling any string-manipulating helper. Then either:
- Use `delete-region` + `insert` instead of `replace-match` (positions are now in let-bound vars), OR
- Wrap the string-manipulating work in `save-match-data`.

**Verified:** Bit `--strip-visibility-tags` in D.2 multi-filter session 2026-06-03. The initial implementation used `org-map-entries` + `org-set-tags` (which triggers the org-element cache trap separately — see [[reference-interactive-emacs-org-element-cache-hang]]); the regex-rewrite replacement that followed hit THIS trap on its first version. Fixed in dotfiles `6795951` by switching from `replace-match` to `delete-region`/`insert` with let-bound positions.

**How to apply:** Whenever you see a `(while (re-search-forward …) … (replace-match …))` loop, scan the body for any string op. If there's a `split-string`, `string-match`, `string-match-p`, or `member` (on strings), promote the match captures to the top of the let-form. The replace-match `LITERAL t` flag doesn't save you — it only suppresses backref expansion, not match-data reads.
