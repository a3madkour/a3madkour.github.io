---
name: project-d2-figref-bundled-fix-complete
description: "D.2 figure-ref bundled fix shipped 2026-06-06 in dotfiles (59869fc..cb9fe63, 8 commits, 14 new ert tests, suite 525 → 543). Closes Bug 1 (rewrite-buffer-links erased [[file:asset.ext]]) and Bug 2 (asset-validate-and-copy hardcoded from-validate sentinel). Task 9 manual verification partially failed — figure-ref :inert + missing bug filed as follow-up."
metadata: 
  node_type: memory
  type: project
  originSessionId: d9590cb9-9f4e-4250-81e6-26b62455844c
---

## Shipped

8 dotfiles commits 2026-06-06: `59869fc..cb9fe63`.

| Task | Commit | What |
|---|---|---|
| 1 | `59869fc` | `--strip-file-prefix-if-asset` helper in rewrite.el |
| 2 | `e1a7038` | wire helper into `rewrite-link` let-binding |
| 3 | `a7949d5` | `asset-validate-and-copy` accepts `source-note-id` (+ corrigendum `30f1c8d`) |
| 4 | `73f008b` | `rewrite-asset-link` tolerates nil source-note-id |
| 5 | `83e0c24` (+ fixup `42283fa`) | `asset-resolve-path` essays-aware branch + `--essay-slug-from-source-file` helper |
| 6a | `79e625e` | essays publisher threads `id` |
| 6b | `0607916` | garden publisher threads `id` |
| 6c | `f6fbace` | research publisher threads `id` |
| 7 | (no commit — fixture in `~/org/essays/`) | `:ID:` drawer added; SVG moved to `assets/<UUID>/` |
| 8 | `cb9fe63` | end-to-end `figure-ref-round-trip` ert test |

**Test suite**: 525 → 543 green (18 new tests). Plus corrigendum commits `30f1c8d` (Task 3 message correction) and `42283fa` (Task 5 nil-slug + tilde-path fixups).

**Spec**: `~/dotfiles/emacs-configs/custom/docs/superpowers/specs/2026-06-05-d2-figure-ref-bundled-fix-design.md` (commit `fc6ccbd`).
**Plan**: `~/dotfiles/emacs-configs/custom/docs/superpowers/plans/2026-06-05-d2-figure-ref-bundled-fix.md` (commit `d70b3c5`).

## Task 9 — partial failure

`M-x a3-publish-deliberate ~/org/essays/example-multi.org` runs to completion (PDF + DOCX re-rendered, mtimes fresh), BUT `index.md` body contains:

```
(missing asset: diagram-1.svg)
```

instead of `<img src="diagram-1.svg" />`. The `:inert + missing` marker means `--asset-resolve-path` returned `:kind missing` — i.e., the essays-aware branch did NOT fire in production. Task 8's end-to-end ert test passes for the same code path, so the gap is between the test environment and the production publish.

## Two follow-ups filed

Both in `~/dotfiles/emacs-configs/custom/docs/superpowers/specs/`:

1. **`2026-06-06-async-publish-pipeline-stub.md`** — Emacs froze 30–60s during the Task 9 publish run on xelatex (synchronous `call-process` at `multi-pdf.el:81`). Includes audit inventory of all 7 sync call sites in publish modules. Brainstorm queued. User-flagged top priority.

2. **`2026-06-06-figure-ref-inert-missing-stub.md`** — the Task 9 bug above. Most likely cause: `a3madkour-pub/essays-dir` defcustom lives in `history.el:29`, `assets.el` doesn't require history. `(boundp 'a3madkour-pub/essays-dir)` likely returns nil at the wrong time → essays-aware branch silently doesn't fire. Probably 1-line require fix. `systematic-debugging` queued.

## Lessons / things to remember

- **Production-mirroring tests matter.** Task 8's end-to-end test passes because it `let`-binds `essays-dir` directly. The production `boundp`-guarded code path isn't exercised. Any future `--asset-resolve-path` work should include a test that DOESN'T pre-bind `essays-dir` — to catch the same class of load-order bug.
- **The test stub pattern across Tasks 6a/6b/6c needed the same adaptation**: the plan's `rewrite-to-tmp-file` stub returned the input file directly, but `publish-essay-file` (and garden / research) wrap the temp source in `unwind-protect (delete-file tmp)`, which would delete the test's input. All three Task 6 commits adapt by creating a real temp file AND returning a distinct copy from the stub. Worth replicating if any future B publisher work touches this path.
- **Don't trust commit-message predictions.** Task 3's commit message claimed `validate-nil-source-note-id-tolerated` would fail until Task 4. It didn't — both tests stub `rewrite-asset-link` via `cl-letf` and never hit the real nil-path. Corrigendum landed as `30f1c8d`.
- **Code review can save real correctness bugs.** Task 5's code reviewer caught a real bug: unpublished drafts with `:ID:` but no `#+HUGO_PUBLISH` would emit `rel-path = "page//diagram.svg"` (empty slug component). Fix landed in `42283fa` before next task.
