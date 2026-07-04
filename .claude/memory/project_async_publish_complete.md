---
name: async-publish-complete
description: "Async publish pipeline shipped 2026-06-07; dotfiles `216e6c9..03b5bb3` (36 commits) pushed to origin/main. Editor stays interactive during M-x a3-publish-deliberate (was 30-60s freeze). *a3-publish* status buffer + mode-line spinner + clean cancel. 609 ert + 2 Python integration tests."
metadata: 
  node_type: memory
  type: project
  originSessionId: 2c08431e-013f-458c-a665-ac6e0c33baf8
---

**Shipped 2026-06-07** in dotfiles `216e6c9..03b5bb3` (36 commits, pushed `cea5d2d..03b5bb3` to origin/main).

## What landed

- **New module** `a3madkour-publish-async.el` (~380 LOC): `run-process` primitive (make-process wrapper with stderr/stdout sinks + auto-buffer-kill), `barrier` N-way join, run handle struct, single-in-flight lock, `*a3-publish*` status buffer + `a3-pub-mode` (`C-c C-c` cancel + `n`/`p` section nav), mode-line spinner indicator, lifecycle `begin-publish` / `finish-publish` wrappers, `cancel-current-run`, `kill-emacs-hook` cleanup for SIGTERM path.
- **B handlers** (B.1 garden, B.2 library, B.3 research, B.4 essays): signature `(file run &key on-done)` with `condition-case` wrapper routing `'ok`/`'err` through on-done. Each has a `/planned-steps` function returning the integer step count (drives mode-line N/M fraction).
- **Top-level commands** `a3-publish-deliberate` + `a3-publish-living` rewritten to async lifecycle. `living` uses `--collect-triples` + barrier across all matching files (replaced `--walk-section`).
- **D.2 multi-export** parallel: `multi-pdf/run` (rsvg fan + ox-latex sync + xelatex chain via sentinels) + `multi-word/run` (PNG fan + pandoc sentinel) run concurrently via `export-bundle :on-done`. The essays handler dispatches `export-bundle` directly with the run handle — the after-essay-publish hook is no-op'd to avoid double-fire.
- **8 subprocess sites** converted to `a3-pub-async/run-process`: rsvg-convert (pdf + png), xelatex/biber chain, pandoc, git log (for history mtime, uses new `:stdout-buf`), git mv (assets + unpublish).
- **a3-pub.sh** spawns Emacs in background + traps SIGTERM, propagates to emacs child → kill-emacs-hook deletes tmp-dirs.
- **Batch-mode** sets `synchronous-p` to t when `noninteractive`, so a3-pub.sh CLI publishes still complete the multi-export tail (Emacs's batch mode doesn't wait for sentinels before kill-emacs).
- **Integration tests** under `emacs-configs/custom/tests/integration/`: pytest + PyYAML, conftest with shared fixtures, end-to-end deliberate-essay publish, SIGTERM cancel test (asserts manifest unchanged + non-zero exit).

## Architecture notes

- **Status vocabulary**: handler-level `'ok 'err 'cancelled` (symbols) bubble up via on-done; run-handle struct field uses `:running :ok :err :cancelled` (keywords). `finish-publish` translates via `pcase`.
- **Sync-mode shim**: `with-a3-pub-async-sync` macro let-binds `a3-pub-async--synchronous-p` to t — every `run-process` and `barrier` call honors the shim and runs inline. The existing 543-test corpus stayed green without async-aware fixtures.
- **ox-latex / ox-hugo stay sync** in-process (spec §6 non-goal). Editor blocks ~1-2s at start of publish; the long xelatex/pandoc tail is async. Forked-Emacs export is a deferred follow-up.
- **Citations flush**: `finish-publish` fires emit-yaml on `(eq status 'ok)` regardless of scope. Original code did this in both `a3-publish-deliberate` AND `a3-publish-living` tail-call positions; the wrapper centralizes the trigger.

## Critical post-spot-check fixes

1. **Essays handler async dispatch** (`6008bbe`): manual spot-check showed editor was still freezing because the essays handler triggered D.2 via the SYNC `run-hook-with-args` → `--after-essay-publish-handler` → `orchestrate` (sync wrapper around `export-bundle`). Fix: essays handler probes `#+multi_export: t` and calls `export-bundle` directly with `:run run :on-done`. `multi-install` no-op'd.
2. **Cancel wiring + batch-mode sync** (`03b5bb3`): final review caught that `run-process` never pushed proc to `(a3-pub-async-run-live-processes)` and `cancel-current-run` didn't call `finish-publish`. Cancel was a no-op AND held the lock forever. Fix: helpers `--push-live-process` / `--remove-live-process`; cancel tail-calls `finish-publish` with `'cancelled`. Same commit added `--ensure-batch-sync-mode` (forces sync when `noninteractive`) because Emacs batch mode doesn't wait for sentinels — a3-pub.sh CLI publishes were silently dropping PDF/Word output.

## Known follow-ups (not blocking)

- **Mode-line entry not removed on stop**: `(:eval …)` form stays in `mode-line-misc-info` after the publish completes (harmless, evaluates to "" when idle, but leaky on module reload).
- **3s flash on cancel/err** (spec §4.4): mode-line clears immediately rather than holding the cancelled/err glyph for 3s. Add `run-with-timer` if visual feedback proves insufficient.
- **Dead code** still present: `a3madkour-pub-multi/orchestrate` (sync wrapper, kept for test compatibility), `--after-essay-publish-handler`, `multi-install` (no-op'd defun), `a3madkour-pub-essays-after-publish-hook` defvar (no consumer), `multi-pdf--convert-svg` + `--compile-tex` sync helpers (only their tests reference them). Worth a cleanup commit.
- **Per-pass xelatex log entries** could use `inhibit-message t` to avoid minibuffer noise during the spinner.

## Sequence next time

- Test cleanup pass to remove dead `orchestrate`/`install`/hook code + sync `--convert-svg` / `--compile-tex`.
- Then back to phase order — see [[project-next-slice]] for queue.

## Files of note

- Spec: `~/dotfiles/emacs-configs/custom/docs/superpowers/specs/2026-06-06-async-publish-pipeline-design.md`.
- Plan: `~/dotfiles/emacs-configs/custom/docs/superpowers/plans/2026-06-06-async-publish-pipeline.md`.
- Module: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-async.el`.
- Integration tests: `~/dotfiles/emacs-configs/custom/tests/integration/`.
