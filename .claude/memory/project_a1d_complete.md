---
name: a1d-complete
description: "A.1.d unpublish flow + integration slice — implementation complete, all 6 user-verification spot-checks green; 4 dotfiles + 2 site files staged, awaiting author commit. Sub-project A is now fully shipped; next overall slice = sub-project B."
metadata: 
  node_type: memory
  type: project
  originSessionId: e6261856-5cd9-467f-b858-6dda12ffcd85
---

**State (2026-05-24):** A.1.d (unpublish flow + `--check-orphans` preview + 4 integration fixtures + carry-forwards #1+#2+#5) **implementation-complete + verified**. Author committed Tasks 2-13 during the session as `2915274 first sections of slice A.1.d`; Tasks 14-21 remain staged + uncommitted per session policy. **Sub-project A is now fully shipped** (A.1.0 → A.1.a → A.1.b → A.1.c → A.1.d). Next overall slice = sub-project **B** (per-content-type publisher + templates).

## What shipped

23 plan tasks executed via `superpowers:subagent-driven-development`. Test count progression: 175 (A.1.c end) → **223 ert** + **11 Python sibling** + **8 Python integration** (was 4). Live ert pass + integration pass (~9s). `tools/ci-local.sh` Lighthouse mobile-perf failure is the known local LHCI variance, not an A.1.d regression (A.1.d touches no CSS/JS/Hugo).

Per-stage summary:

| Stage | Tasks | What |
|---|---|---|
| 0 (parent-spec amend) | 1 | §8 reason enum 4→5 (`republished`); url-history.yaml comment update. Committed as `81decda` + clarification follow-up `6d678e0`. |
| 1 (foundation) | 2-4 | `a3madkour-publish-unpublish.el` skeleton + a3-pub.sh registration; accumulator defvar + `begin-publish` extension; `record-publish` republished branch + accumulator append + removed→draft guard. |
| 2 (diff + walk) | 5-6 | `diff-published-set` (pure) + `walk-published-source-set` (standalone-mode driver). |
| 3 (Step A) | 7-8 | `unpublish--delete-bundle` helper + `finish-publish` orchestrator skeleton (Step A wired). |
| 4 (Step B) | 9-11 | `unpublish--rename-asset-dir` (git-mv-vs-mv) + `unpublish--bulk-rewrite-source-links` + Step B wired into `finish-publish`. |
| 5 (Step C) | 12-13 | `unpublish--recheck-live-note-links` (uses `org-roam-id-find`; per memory `reference_org_roam_id_find_returns_cons`) + Step C wired. |
| 6 (CLI) | 14-15 | `check-orphans` thin alias + `--check-orphans` flag intercept in `a3-pub.sh`. |
| 7 (carry-forward #1) | 16 | 3 dedicated ert tests for `--asset-normalize-link-path` (A.1.c shipped untested). |
| 8 (integration) | 17-20 | 4 Python integration fixtures: unpublish, slug-shift, republish-after-removal, link-into-removed-target. |
| 9 (wrap) | 21-22-23 | CLAUDE.md updates; user-verification (6 spot-checks); stage for commit. |

## Bugs caught during execution

1. **Task 4 (record-publish republished branch)**: implementer's coverage-gap test for `removed → draft` revealed that the original `cond` fell through to `--diff-reason` and appended a spurious `section_change` event (because `old-url` is nil after removal, `--section-of-url nil` → nil, `--diff-reason` saw nil vs new section → section_change). Fix: added a guard branch `((equal old-state "removed") nil)` so `removed → draft` is a state-only change with no history event. All 5 enum cases now correctly fire only when intended.

2. **Task 8 (URL parser edge case)**: `(split-string trimmed "/")` didn't omit empty segments — `"//garden//foo//"` parsed to `("garden/" . "foo")` (trailing slash from empty middle segment). Fix: added `t` (omit-nulls) arg: `(split-string trimmed "/" t)`.

3. **Task 9 (rename-file with trailing slashes)**: plan's pseudo-code `(rename-file old-dir new-dir)` with both args having trailing slashes (from `file-name-as-directory`) failed when target parent existed but target didn't. Implementer wrapped both args in `directory-file-name` — works for both files and directories, normalized path is `shell-quote-argument`-friendly for the git-mv path.

## Architectural findings (B follow-up)

**Critical for sub-project B's brainstorm:** `record-publish` eagerly mutates `manifest.current_url`. If B calls `record-publish` for each note BEFORE `finish-publish` (the natural per-note pattern), `diff-published-set` will see manifest's `current_url` already at the new URL, and slug-shift detection silently never fires.

**Workarounds discovered:**
- **Standalone mode works**: when accumulator is empty, `walk-published-source-set` derives URLs from source `.org` keywords, independent of manifest. The slug-shift detection works correctly because old-URL still lives in the manifest at that moment.
- **B-coupled mode needs ordering fix**: either (a) B calls `record-publish` AFTER `finish-publish` for slug shifts (so diff happens first), or (b) `begin-publish` snapshots the manifest into a defvar that `diff-published-set` reads instead of disk, or (c) `record-publish` defers manifest writes to `finish-publish`.

**A.1.d ships with the standalone-mode contract intact.** B's design must address this when it lands. Logged here so the future B brainstorm sees it.

## Other A.1.d known limitations

- **`a3-pub.sh --check-orphans` crashes on missing org-roam dir**: this machine has `~/org/notes/` not `~/org-roam/`. `begin-publish` → `org-roam-db-sync` raises. Workaround for spot-checks: bypass the wrapper's flag and pass `--eval` forms directly that stub `org-roam-db-sync` (per the 4 integration fixtures' pattern). Future enhancement: gate `org-roam-db-sync` on dir existing, OR add a `--notes-dir <path>` flag to the wrapper that sets `org-roam-directory` before invoking `(begin-publish)`.
- **Step B doesn't write manifest events for slug shifts**: only Step A writes manifest events (for removed notes). If a slug shift triggers Step B's asset rename + source rewrite, no `slug_override` history event lands in `url-history.yaml`. In B-coupled mode, B's per-note `record-publish` call is expected to provide the event (with `:had-slug-override-p t`). In standalone mode (today's A.1.d), the event is missing until B exists. Acceptable for now — author can manually `record-publish` post-shift, or wait for B.

## Staged files awaiting author commit

**Dotfiles** (`~/dotfiles`, branch main, 4 files):
```
M  emacs-configs/custom/lisp/a3-pub.sh
M  emacs-configs/custom/lisp/a3madkour-publish-assets-test.el
M  emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
M  emacs-configs/custom/lisp/a3madkour-publish-unpublish.el
```
(Tasks 2-13's elisp work was already committed as `2915274 first sections of slice A.1.d` during the session.)

**Site repo** (master, 4 commits ahead of origin, 2 staged):
```
M  CLAUDE.md
M  tools/test_publish_integration.py
```
The 4 already-committed: `9459a4c` design + `24a2854` plan + `81decda` parent-spec amend + `6d678e0` clarification.

Suggested commit messages drafted in session transcript at the Task 22/23 handoff.

## Carry-forwards still open for A.2 / future

- carry-forward #3 (shared-asset conflict resolution) — own design pass
- carry-forward #4 (`--strict` flag) — A.2
- A.2 items #1 (typed-backlinks), #2 (`:noexport:` subtree handling), #4 (`--gc-shared` flag)
- B-coupling constraint above
- `--check-orphans` org-roam-dir-gating enhancement

## Session policy + commit cadence

Subagent-driven execution across 23 tasks. Per-task: implementer dispatch → spec-compliance review → code-quality review → fix-up if needed → next task. Plan was 2928 lines (matched A.1.c precedent). Stage-but-don't-commit session policy honored throughout; author committed periodically themselves (parallel dotfiles work on citation cleanup also happened during the session — interleaved cleanly with A.1.d staging).

## Cross-references

- Plan: `docs/superpowers/plans/2026-05-24-phase-3-a1-d-unpublish.md` (commit `24a2854`)
- Design: `docs/superpowers/specs/2026-05-24-phase-3-a1-d-unpublish-design.md` (commit `9459a4c`)
- Parent spec amendment: §8 reason enum bump (commit `81decda` + clarification `6d678e0`)
- Prior memory: [[a1c-complete]] (A.1.c)
- Decomposition context: [[phase-3-decomposition]]
- Reference: [[org-roam-id-find-returns-cons]] (used in Task 12)
- Reference: [[plan-wrapper-script-updates]] (applied in Task 2)

## How to start the next session

1. **Verify author committed + pushed A.1.d staging** (the 4 dotfiles + 2 site files above + any uncommitted site doc commits).
2. **Next slice = Phase 3 sub-project B** (per-content-type publisher + templates). Carries the "two publish commands" rule + library-tags-round-trip rule + synced-poetry export contract. Will need to address the **B-coupling ordering constraint** documented above.
3. To pick up B: read CLAUDE.md + parent spec §10 (A → B interface) + `memory/project_phase_3_decomposition.md`, then `superpowers:brainstorming`.
