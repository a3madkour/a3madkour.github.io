---
name: tier-1-10-complete
description: "Tier 1.10 (Step B failed slug-shift delete silently orphans) — shipped 2026-06-07 in dotfiles 6d52eef. Captures --unpublish-delete-bundle return in Step B, pushes a WARN onto :orphan-warnings on 'failed. Option (c) from roadmap. Side cleanup: Step C now `push'es onto the shared accumulator instead of overwriting it. Suite 615 → 616. CLOSES TIER 1 (10/10)."
metadata: 
  node_type: memory
  type: project
  originSessionId: 5b5bbb90-9abc-47bc-b613-67a9ddf91b2a
---

**Shipped 2026-06-07.** Bug 1.10 from `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md`. Filed earlier in the same session during the Tier 1.1 analysis. Closes Tier 1 entirely.

## Root cause + why self-healing isn't an option

`finish-publish` Step B's orphan-bundle delete was fire-and-forget — the `'failed` return from `--unpublish-delete-bundle` was discarded. Unlike Step A (bug 1.1), self-healing across runs is unreachable here: by the time Step B runs, the per-section handler has already written the new bundle and called `record-publish` for the new URL, so the next run's diff sees `:stayed` (the manifest already matches the new URL) and never re-attempts the old-slug delete. Net result was a stray `content/<section>/<old-slug>/` that Hugo would build as a duplicate page, invisible to the manifest.

## Option chosen (c, visibility-via-WARN)

Roadmap row listed three options:
- (a) Side-table of failed-delete URLs that next run's diff sweeps.
- (b) `record-publish` a "ghost" `removed` entry for the old URL.
- (c) Loud author-facing WARN + manual cleanup.

Chose (c) as minimum-viable. (a) needs new persistent state + schema; (b) needs synthetic IDs and manifest-walker changes. (c) leverages the existing `:orphan-warnings` result-plist key (already consumed by the publish-UI buffer + the `--check-orphans` printer) — so the orphan surfaces to the author without any new plumbing. Manual `rm -rf` is the cleanup; less ergonomic than auto-retry but the bug is rare enough that the extra machinery isn't justified yet.

## Side cleanup

Step C previously `setq`ed `orphan-warnings` from scratch, which would have stomped Step B's contributions. Both steps now `push` onto the accumulator and the return-plist `nreverses` once for insertion order. Existing Step C tests still pass (order preserved end-to-end).

## Test

`a3madkour-pub-unpublish-test/finish-publish-step-b-failed-delete-surfaces-warning` — mirrors the existing `step-b-deletes-old-bundle` fixture but stubs `delete-directory` to signal an error. Asserts:
- `:slug-shifted` bookkeeping still completes (the rest of Step B is independent of the delete outcome).
- Old bundle survives on disk (stubbed delete failed).
- `:orphan-warnings` includes a WARN that mentions the old slug + the word "manual".

Suite 615 → 616 ert green, 0 unexpected.

## Commits

Dotfiles only:
- `6d52eef` fix(unpublish): Step B surfaces failed slug-shift delete — closes bug 1.10

Site repo: roadmap row marked ✓ + top-of-file status updated to "Tier 2 is the next session" + Tier 1 "Session shape" block rewritten as TIER 1 CLOSED summary + this memory file + MEMORY.md index entry.

## Tier 1 closeout (10/10)

| # | How closed |
|---|---|
| 1.1 | Fixed this session (dotfiles `e50a037`) |
| 1.2 | Fixed this session (dotfiles `27d157d`) |
| 1.3 | Retro-closed by B.2 |
| 1.4 | Retro-closed by B.3 |
| 1.5 | Fixed this session (dotfiles `0cb4414`) |
| 1.6 | Fixed this session (dotfiles `2134de8`) |
| 1.7 | Fixed this session (dotfiles `31f9570`) |
| 1.8 | Retro-closed by A.1.d gate |
| 1.9 | Fixed this session (dotfiles `350a711`) |
| 1.10 | Fixed this session (dotfiles `6d52eef`) — THIS ENTRY |

dotfiles ert 606 → 616 (+10 named regression tests across 6 commits). 7 site-side doc commits. No production-blocking bugs remaining in the publish pipeline correctness layer.

## Next session

Tier 2: UX polish. First row 2.1 is "anchor affordance" — needs `superpowers:brainstorming` before any code. Read [[anchor-affordance-followup]] + the Tier 2 entry in the roadmap.

## Cross-references

- Roadmap: `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` (Tier 1 closeout summary at the top of Tier 1)
- Sibling Tier 1 closures: [[tier-1-1-complete]], [[tier-1-2-complete]], [[tier-1-6-complete]], [[tier-1-7-complete]], [[tier-1-5-1-8-1-9-complete]]
- Source memory for 1.10: filed in [[tier-1-1-complete]] "Out of scope" section during 1.1 analysis
