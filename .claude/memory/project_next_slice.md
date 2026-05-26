---
name: next-slice
description: "Session-start pointer — next slice is Phase 3 B.2 (library handler). B.1 (garden handler) code-complete 2026-05-25; 259 ert tests + 13 Python integration fixtures green. Task 17 (real-corpus handover) gated on author annotating ~/org/notes/ with HUGO_PUBLISH + HUGO_SECTION keywords. B.2 spec already covered in B parent spec §8."
metadata:
  node_type: memory
  type: project
---

**Next slice = Phase 3 sub-project B.2 — library handler.** B.1 (garden) code-complete 2026-05-25; see [[b1-complete]].

Per design spec §12 slice ordering: A → B.0 → B.1 → **B.2 (next)** → B.3 (research) → B.4 (essays) → B.5 (works) → B.6 (streams) → B.7 (about) → F (citations) → C (math validators) → D (unified markup) → E (explorables).

## Two paths into the next session

**Option 1: Address B.1.x follow-ups first**, then B.2. The three known issues per [[b1-complete]] "Known issues":
1. Link rewriting is stubbed — pre-export buffer rewrite OR `org-link-set-parameters` hooks (architectural call).
2. `last_modified` uses file mtime; spec wants git-mtime-of-HEAD.
3. B parent spec §7 needs a one-line correction (drop "flavor is emitted").

**Option 2: Skip directly to B.2** (library handler). The follow-ups can ride along with B.2 or land as a separate B.1.1 slice. Library is the structural outlier per spec §8 — per-medium YAML rows (not per-page Hugo bundles), parsed from top-level org headings in 4 files (`library-reading.org`, `library-listening.org`, `library-playing.org`, `library-watching.org`). YAML emission replaces the existing `data/<medium>.yaml` files from scratch (no merge); library tags round-trip from per-heading `:tags:` into per-row YAML.

**Option 3: User-driven Task 17 spot-check.** Author annotates `~/org/notes/` with `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: garden`, runs `a3-pub.sh --publish-living`, eyeballs `/garden/` in `hugo server`. This may surface real link-rewriting issues that inform Option 1's architectural choice.

Recommended sequencing: Option 3 → Option 1 → Option 2. The spot-check informs the link-rewriting fix; the fix sets the pattern B.2-B.7 will mirror; then library starts cleanly.

## How to start the next session

1. Read CLAUDE.md status pointer + [[b1-complete]] + B parent spec §8 (library specifics).
2. Decide path (1/2/3 above) with the author.
3. If Option 2: jump straight to `superpowers:writing-plans` for B.2 — sub-project B's parent spec covers it, no new brainstorm needed unless §8 surfaces ambiguity.
4. If Option 1: probably needs a small spec (or just a focused brainstorm) because the link-rewriting architecture has two genuinely different paths.

## Agent-environment notes (carry-forward from [[b1-complete]])

- **Hugo + emacs + ox-hugo + yaml** all loadable in batch context via `a3-pub.sh` or `run-tests.sh`.
- **org-roam IS loadable** via straight.
- **`yaml` package now bootstrapped via `(straight-use-package 'yaml)`** in both wrapper script and test runner — was the B.0 packaging gap caught by B.1 Task 1 smoke tests.
- **`org-roam-directory` defaults to `~/org-roam/`** (doesn't exist on this machine); user's notes at `~/org/notes/`.
- **Site repo at `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/`** (resolved via `git rev-parse` cascade in `a3-pub.sh`).
- **`note-section` returns string, dispatch keys by symbol** — `walk-section` bridges via `symbol-name`. B.2's library section may want the same pattern (multiple library-* sections in one handler module).
