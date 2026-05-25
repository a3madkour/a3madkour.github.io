---
name: plan-wrapper-script-updates
description: "When a slice adds a new top-level elisp module, the plan must include an explicit 'update a3-pub.sh load chain' step — otherwise spot-checks via the wrapper silently fail on functions without autoload declarations."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: edcdc7b8-71ae-4757-af99-5e45cb71e09f
---

When an A.1.* slice (or any Phase 3 slice) adds a new top-level elisp module under `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-*.el`, the plan must include an explicit step to update `a3-pub.sh`'s `-l <module-name>` load chain.

**Why:** `a3-pub.sh` is the spot-check wrapper. It loads modules explicitly. If a new module isn't loaded, calls to that module's public functions via the wrapper silently fail under `emacs --batch` — emacs errors but the error doesn't surface; the user just sees missing side effects (empty bundles, no output).

Autoload declarations partially save you: `a3madkour-publish-rewrite.el` carries `(autoload 'a3madkour-pub/rewrite-asset-link ...)`, which triggers a load of `-assets.el` when the function is called. But functions WITHOUT autoload (like `a3madkour-pub/asset-validate-and-copy`) hit a void-function error.

**How to apply:**

When writing-plans for any new Phase 3 slice, check whether the slice introduces a new `a3madkour-publish-*.el` top-level module. If yes:

1. Add a task (or a step in the relevant introduction task) that updates `a3-pub.sh` to include `-l <new-module>` in the exec chain.
2. The new `-l` should slot in just BEFORE the readiness `--eval` message.
3. Verify in the user-verification checkpoint: run a wrapper spot-check that exercises one PUBLIC function from the new module (not just one autoloaded by the rewriter).

Caught the gap in A.1.c — verified 2026-05-24 — and the wrapper fix is staged. Future plans should preempt.

Related: `run-tests.sh` uses auto-discovery (`for test_file in "$LISP_DIR"/*-test.el`), so test files DON'T need explicit registration. The wrapper does.

Cross-refs: [[a1c-complete]] (where the gotcha was caught) + [[a1b-complete]] (which established the wrapper-load convention).
