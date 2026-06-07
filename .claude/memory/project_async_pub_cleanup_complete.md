---
name: project-async-pub-cleanup-complete
description: "Async-publish dead-code cleanup + mode-line hygiene shipped 2026-06-07 in dotfiles `99f0240` (pushed). 6 dead defuns + 1 defvar + 8 tests removed. Mode-line `(:eval …)` entry leak fixed; 3s flash on cancel/err per spec §4.4. Net -76 lines; suite 610 → 606 green (deleted 8 tests, added 4)."
metadata: 
  node_type: memory
  type: project
  originSessionId: 7e32a468-c0c0-4b00-9ea9-3bbafccb12e4
---

## Shipped

Dotfiles `99f0240` (1 commit, pushed origin/main 2026-06-07). 7 lisp files, 137 insertions / 213 deletions.

### Deletions (dead code from async-pub slice carry-over)

| Symbol | Reason |
|---|---|
| `a3madkour-pub-multi/orchestrate` | sync `export-bundle` wrapper; no live callers |
| `a3madkour-pub-multi--after-essay-publish-handler` | hook target; hook never installed |
| `a3madkour-pub-multi-install` | no-op'd defun (was DEPRECATED comment-only) |
| `a3madkour-pub-essays-after-publish-hook` defvar | no consumers |
| `a3madkour-pub-multi-pdf--convert-svg` | replaced by `--convert-svgs-fan` |
| `a3madkour-pub-multi-pdf--compile-tex` | replaced by `--compile-tex-async` |

8 tests removed (orchestrate-* + auto-trigger-* + 3 stub helpers in multi-test; svg-to-pdf + xelatex-loop + 2 compile-tex returns in multi-pdf-test).

### Mode-line hygiene (design spec §4.4)

- `--modeline-stop` now drops the `(:eval …)` entry from `mode-line-misc-info`. Was previously a permanent global-var leak — `add-to-list` in `--modeline-start` re-installed (idempotent), but no removal path existed.
- On `:cancelled` / `:err` status, mode-line flashes `[a3-pub ⨯ cancelled]` / `[a3-pub ✗ err]` for 3s before clearing. Was previously instant-clear.
- `--modeline-start` cancels any in-flight flash timer before re-installing — prevents a fresh publish mid-flash from visibly blinking when the stale clear timer fires.
- New `--terminal-run` defvar holds the just-finished run for the flash window.
- New `--flash-timer` defvar tracks the cancellation handle.
- New `--modeline-misc-entry` defconst — canonical reference for the form installed/removed, so `delete` matches the same structure.

4 new ert tests cover the new behavior:
- `modeline-stop-ok-clears-entry-immediately`
- `modeline-stop-cancelled-stashes-and-keeps-entry`
- `modeline-stop-err-flashes-then-clears`
- `modeline-start-cancels-stale-flash-timer`

## Suite

610 → 606 green (deleted 8 dead tests, added 4 mode-line tests).

## Notes

- Stale `.elc` files masked source edits again during this slice (defconst added to async.el wasn't visible to byte-compiled callers until I cleared). Cleared with `find ~/dotfiles/emacs-configs/custom/lisp -name '*.elc' -delete`.
- `essays.el:283` doc-comment that referenced the now-deleted `orchestrate` was rewritten to drop the specific function name.
