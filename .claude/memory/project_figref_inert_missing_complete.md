---
name: project-figref-inert-missing-complete
description: "Figref :inert + missing bug fixed 2026-06-07 in dotfiles `03b5bb3..1edd900`. Task 9 verified (grep -c '<img' index.md → 1). Root cause was NOT the handoff's boundp hypothesis — it was rewrite-asset-link calling --id-to-file (DB lookup) when callers already had source-file in scope. Fix threads source-file through path A + path B."
metadata: 
  node_type: memory
  type: project
  originSessionId: 7e32a468-c0c0-4b00-9ea9-3bbafccb12e4
---

## Shipped

Dotfiles `03b5bb3..1edd900` (1 commit, pushed to origin/main 2026-06-07). 4 lisp files, 111 insertions / 10 deletions. Suite 609 → 610 green.

| File | Change |
|---|---|
| `a3madkour-publish-assets.el` | `rewrite-asset-link` gains `&optional source-file`; falls back to `--id-to-file` when not given. `asset-validate-and-copy` threads `org-file` through. |
| `a3madkour-publish-rewrite.el` | `rewrite-link`, `rewrite-buffer-links`, `rewrite-to-tmp-file` all gain & pass `source-file`. |
| `a3madkour-publish-essays-test.el` | New ert `figure-ref-round-trip-when-id-not-in-orgroam-db` — stubs `--id-to-file` → nil to mirror production DB miss. |
| `a3madkour-publish-assets-test.el` | 1-line stub signature update (+ `&optional _source-file`). |

## Root cause

Handoff hypothesized a `(boundp 'a3madkour-pub/essays-dir)` load-order failure. **That was wrong.** By the time `rewrite-asset-link` runs in production, `history.el` has been loaded transitively via `essays.el` line 21.

Actual cause: `org-roam-directory` is `~/org/notes/` (config.el:87). The org-roam DB (83 nodes) contains zero files from `~/org/essays/`. So `(org-roam-id-find "394db383-...")` returns nil for essay UUIDs. That cascades:

1. `rewrite-asset-link` does `(let* ((source-file (a3madkour-pub--id-to-file source-note-id)) …))` → `source-file = nil`.
2. `--asset-resolve-path` gets `path source-file=nil`. The essays-aware branch is gated on `(and source-file essays-dir …)` → skipped.
3. Falls through to `abs = (expand-file-name path source-dir)` → `~/org/essays/diagram-1.svg`.
4. That file doesn't exist (real SVG is at `assets/<UUID>/diagram-1.svg`).
5. `:kind missing` → inert `(missing asset: diagram-1.svg)` in body.

Task 8's ert test passed because it `cl-letf`s `--id-to-file` to return the file path directly — exactly the DB lookup that fails in production.

## Why threading, not requiring history

`rewrite-asset-link` and `asset-validate-and-copy` callers already know the source file path. Re-deriving via DB lookup was an architectural smell — DB knowledge isn't required, and the publishers run on files outside `org-roam-directory` too. The cleanest fix is to thread the known path through.

Backwards-compatible: optional `source-file` param, falls back to `--id-to-file` when not supplied.

## Sibling bug NOT fixed (separate scope)

`a3madkour-pub--rewrite-file-link` (rewrite.el:245) has the same architectural issue — it calls `--id-to-file source-note-id` to compute `source-file` for resolving `[[file:other-essay.org]]` relative paths. For essays linking to other essays via file: links, this would silently fall back to `default-directory`. Not fixing in this scope; surface separately if it ever causes a symptom.

## Process notes

- Stale `.elc` files cleared before the fix; reappeared after `run-tests.sh` byte-compiled in batch mode. Untracked; gitignored if not, won't be committed.
- Followed `superpowers:systematic-debugging` end to end: investigation BEFORE fix, production-mirroring test BEFORE implementation, single hypothesis tested. Two failing tests after the fix were stub-API-drift in existing tests; corrected in the same commit.
