---
name: next-slice
description: "Session-start pointer — next slice is Phase 3 B.1 (garden handler). B.0 (shared publisher infrastructure) staged 2026-05-25 in dotfiles; 239 ert tests passing. Site CLAUDE.md status pushed as `5ded581`. Architectural decisions settled in B parent spec; B.1 likely plan-only (no new brainstorm needed) unless garden growth_stage derivation surfaces surprises."
metadata: 
  node_type: memory
  type: project
  originSessionId: 240f0465-31c7-4fcc-86e7-eaa6fa0a2727
---

**Next slice = Phase 3 sub-project B.1 — garden handler.** B.0 (shared infra) shipped 2026-05-25; see [[b0-complete]].

Per design spec §12 slice ordering: A → B.0 → **B.1 (next)** → B.2 (library) → B.3 (research) → B.4 (essays) → B.5 (works) → B.6 (streams) → B.7 (about) → F (citations) → C (math validators) → D (unified markup) → E (explorables).

## What B.1 must do

- Create `a3madkour-publish-garden.el` + sibling test in `~/dotfiles/emacs-configs/custom/lisp/`.
- Register `(garden . a3madkour-pub-garden/publish-garden-file)` in `a3madkour-pub-living--handlers` (currently empty in B.0).
- Fill in `a3madkour-pub-frontmatter/normalize`'s garden branch (currently pass-through in B.0) with:
  - `growth_stage` derivation (`:PROGRESS:` → seedling/budding/evergreen, `#+HUGO_GROWTH_STAGE:` override).
  - `flavor` inference from `media_type` (concept / media / reference per spec §7).
  - `topic_map` pass-through.
- Wire link-rewriter + asset-copy into the garden handler:
  - Call `a3madkour-pub-rewrite/rewrite-links-in-string` on the post-export body.
  - Call `a3madkour-pub-assets/asset-validate-and-copy` for the bundle dest dir.
  - Call `a3madkour-pub-history/record-publish` after writing `content/garden/<slug>/index.md`.
- Replace `a3madkour-pub-export/export-file`'s skeleton stub with the real ox-hugo invocation (capture buffer + extract frontmatter).
- Add 3-4 new integration fixtures under `tools/test_publish_integration.py` (publish-once, idempotency, slug-shift, removed-note).
- First slice to emit real Hugo content; transition garden fixtures per design spec §11 (fixtures → real garden notes).

## B.0 known issues to fix in B.1

Per [[b0-complete]] "Known issues":

1. **`SITE_DATA_DIR` default path is wrong on this machine.** Both `--publish-living` and `--publish-deliberate` intercepts in `a3-pub.sh` default to `$HOME/Workspace/a3madkour.github.io/data/` (matches defcustom docstring example) but this machine's real repo is at `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/`. Smoke tests passed only because B.0 emits nothing; B.1's real garden publish will silently write to the wrong dir or no-op on missing manifest. Fix: either (a) detect via `git rev-parse --show-toplevel` from `$PWD`, (b) use this machine's absolute path as default, or (c) require `A3_PUB_SITE_DATA_DIR` env var.

2. **Pre-existing `--check-orphans` lacks SITE_DATA_DIR pattern.** Back-port the workaround Task 11/12 added, OR factor out a shared helper.

## Carry-forwards from A.1.d / B.0 still open

- A.1 carry-forward #3 (shared-asset conflict resolution): own design pass needed.
- A.2 items: typed-backlinks (#1), `:noexport:` subtree (#2), `--gc-shared` flag (#4), `--strict` flag.
- `a3-pub.sh --check-orphans` site-data-dir gap (per #2 above).
- B.0 stub-literal extraction: `'((notes . []))` duplicated as `read-manifest` stub in ~4 test bodies; quality reviewer suggested extracting `defconst a3madkour-pub-test--empty-manifest` if B.1+ adds more callers.

## How to start the next session

1. **Verify author committed B.0 dotfiles work**: per [[b0-complete]] "Dotfiles state", 11 files staged + 4 unstaged (Tasks 0-3 work the user unstaged mid-session). All 15 files need to land in one or more local dotfiles commits before B.1 starts.
2. **B.1 may need its own brainstorm** if growth_stage derivation rules need clarification (currently spec §7 prose). Otherwise jump straight to `superpowers:writing-plans`.
3. Reading list: CLAUDE.md + B parent design spec §7 (frontmatter mapping) + §9 (per-section specifics) + [[b0-complete]] (B.0 carry-forwards) + [[phase-3-decomposition]].

## Agent-environment notes (carry-forward)

- **Hugo IS runnable** (`hugo --minify`, `hugo server --buildDrafts`).
- **org-roam IS loadable** via straight in `a3-pub.sh`. B.0's Task 0 gates `org-roam-db-sync` on `org-roam-directory` existing, so batch contexts don't crash.
- **emacs IS on PATH** for the agent. Integration tests work.
- **`org-roam-directory` defaults to `~/org-roam/`** (doesn't exist on this machine); user's notes at `~/org/notes/`.
- **Site repo at `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/`** (not `$HOME/Workspace/...` as the defcustom docstring suggests).
