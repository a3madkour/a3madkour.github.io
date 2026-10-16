# Authoring infrastructure roadmap

**Date:** 2026-10-15
**Status:** approved design; S1 is queue head
**Supersedes the sequencing in:** the 2026-09-27 authoring-surface audit (slices A1 → A2 → B1 → C)

## 1. Goal

Every artifact on the site can be authored from Emacs, and that is **proven on real
org-roam content**, not fixtures. Recipes are out of scope (indefinite hiatus, 2026-10-15).

## 2. Where things stand

| Gap tier (2026-09-27 audit) | What | Slice | State |
|---|---|---|---|
| 1. Real content, no path | `works/games`, `works/music` | A1 | Shipped and deployed. Never run against real org-roam (T12 open). |
| 2. Machine-authored content | `streams`: `tools/poll_streams.py` writes `content/streams/<date>-<slug>/index.md` stubs | A2 | Not started. Trigger-gated (§5). |
| 3. Hand-edited structural pages | 19 `_index.md` files, incl. homepage, about, credits, library leaves | B1 | Not started |
| 4. Hand-edited curated YAML | `filter-chips.yaml`, `library-shelves.yaml`, `library-media.yaml`, `streams-schedule.yaml` | B1 | Not started |
| — | Authoring guide | C | Not started |

Sections with a handler today: garden, library ×4, research themes/questions (living);
essays, poetry (deliberate); games, music (living, A1). Only **garden** has real published
content (4 notes). Every other section has published fixtures only.

Out of scope by choice: icons (hand-drawn by constraint), explorables (code, not content),
`tools/fetch_library_covers.py` (shell-only, works).

## 3. Session sequence

| # | Session | Output | Gate to start |
|---|---|---|---|
| S1 | Dogfood run, every handled section | Friction log; A1 T12 closed | Machine prerequisites (§3.1) |
| S2 | Dogfood fixes | Each *fix now* row closed | S1 log triaged |
| — | **Re-plan checkpoint** | Roadmap updated against the log | S2 done |
| S3 | B1 design | B1 spec + plan (covers B1a and B1b) | Checkpoint passed |
| S4 | B1a implementation: prose-page org handler | Merged, E2E green | B1 plan approved |
| S5 | B1b implementation: structural direct-edit commands | Merged, E2E green | B1 plan approved (may run beside S4) |
| S6 | B1 acceptance on real content | Acceptance log | S4 + S5 merged |
| S7 | C: authoring guide | Guide shipped | S6 done |
| A2 | Streams: poller queues, Emacs adopts | Spec → plan → impl | Trigger: first real stream scheduled |

S1 may span two sessions. Sessions S4 and S5 are independent once the plan exists.

### 3.1 S1 — dogfood run

Prerequisites on whichever machine runs it:
- `git pull` dotfiles (it was 2 commits behind origin on 2026-10-15) and resolve local
  uncommitted changes first.
- Recreate the memory symlink:
  `~/.claude/projects/<project-key>/memory -> <clone>/.claude/memory`.
- Check whether the Emacs 31.1 subr-trampoline failure reproduces
  (memory: `reference_emacs31_subr_trampoline_breakage`). If it does, apply the `run-tests.sh`
  fix to `a3-pub.sh` before publishing anything; otherwise publishing may fail for reasons
  unrelated to what is being tested.

Run: pick a few real notes per section (garden, library ×4, research themes + questions,
essays, poetry, games, music). Publish them with the real commands (`a3-publish-living`,
`a3-publish-deliberate`), then run the site linters, `hugo` locally, and a browser pass. The
games/music runs close A1 T12, which modifies real org files and needs explicit consent at
the time.

### 3.2 S2 — dogfood fixes

Each *fix now* row as a small TDD change. The parked elisp items join only if S1 hit them:
P3.8 (dedup 13 `with-tmp-*` test macros), the ERT suite writing `citations.yaml` into both
source trees, the `a3-pub.sh` trampoline fix (if not already done in S1).

### 3.3 S3–S6 — B1

Split by kind (decided 2026-10-15):
- **B1a — prose pages** (about, homepage hero, section intros): an org source and a small
  handler, through the living or deliberate pipeline. The S3 spec decides which pages are
  "prose" and which pipeline.
- **B1b — structural files** (the remaining `_index.md` + the four curated YAML files):
  Emacs commands that edit the site file in place with completion over the live taxonomy,
  scaffolds, and validation against the existing linter contract. No manifest, no unpublish.
  `a3-library-insert-item` is the existing model.

S3 must also say how `credits` and the library leaves are classified. Neither was settled
in the audit.

### 3.4 S7 — C

One guide page per section. Written after B1, **before A2**: its streams page documents the
current poller behaviour and is rewritten when A2 lands. This reverses the audit's
"guide never ships with a not-yet section" rule, because A2 is now trigger-gated rather than
scheduled.

## 4. Gates applied to every build session

From A1, where 829 green unit tests missed 6 defects that the end-to-end run found:

1. **Acceptance is end to end.** Real org → real ox-hugo → real Hugo build → site linters
   green → browser look. Stubbed org-roam lookups do not count as acceptance.
2. **Mutation-test every new guard.** Break it and watch the test fail. Review tests for the
   five A1 patterns: fixtures authoring the wrong form, loops over the asserted constant,
   substrings several code paths emit, hand-built input only the real exporter produces,
   negative assertions.
3. **Adversarial audit twice per slice:** post-spec and post-implementation.
4. **Run CI locally before every push** (`tools/ci-local.sh`, dotfiles `run-tests.sh`).
   Verify merges by running the suites, and check ancestry explicitly after a pull
   (memory: `reference_pipeline_masks_exit_status`).
5. **One home per cross-repo contract.** A field set or vocabulary shared by Python and elisp
   lives in one data file both read fail-closed, as `data/works-vocab.json` does for works.

## 5. A2 — trigger-gated

**Trigger:** the first real stream is scheduled.

**Design direction (from the audit):** the poller stops writing `content/streams/` bundles
and appends to a machine-owned capture queue; an Emacs command turns a queue entry into an
org file that publishes through a streams handler. This also removes the need for Python
`slugify` and elisp `slug/slugify` to agree on slugs, which no single test could check.

## 6. Friction log and handoff

**Log location:** `docs/superpowers/specs/<date>-dogfood-friction-log.md`.

**Row:** section · action · what happened · severity (*blocks publish* / *wrong output* /
*annoyance*) · triage (*fix now* / *fold into B1* / *new slice* / *won't fix*) · resolving
commit.

**Triage rule:** *blocks publish* and *wrong output* are *fix now* (S2). Editing-affordance
annoyances fold into B1. Anything else becomes a stub row in this roadmap. Nothing is
discussed without being logged.

**Handoff:** each session ends by updating §2/§3 status here and a memory entry, so the next
session can start cold on either machine.

**Re-plan checkpoint:** after S2, compare the roadmap with the friction log before S3. If
dogfooding shows B1 is not the largest problem, reorder.
