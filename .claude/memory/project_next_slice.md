---
name: next-slice
description: "Session-start pointer — next slice is B.1.1 (pre-export id-link rewriter), then B.2 (library). B.1 shipped 2026-05-25 with 261 ert + 13 integration tests; round-2 spot-check on a linked note proved Hugo can't resolve ox-hugo's relref shortcodes against B-emitted bundles, so link rewriting MUST land before any further linked-note publishing. Architectural call made: pre-export buffer rewrite via new helper `rewrite-buffer-links` that scans + applies A.1's existing `rewrite-link`."
metadata:
  node_type: memory
  type: project
---

**Next slice = B.1.1 — pre-export id-link rewriter.** B.1 shipped 2026-05-25; see [[b1-complete]]. Then B.2 (library).

Per design spec §12 slice ordering: A → B.0 → B.1 → **B.1.1 (next, NEW)** → B.2 (library) → B.3 (research) → B.4 (essays) → B.5 (works) → B.6 (streams) → B.7 (about) → F (citations) → C (math validators) → D (unified markup) → E (explorables).

## Why B.1.1 is now required

Round-2 spot-check (2026-05-25, documented in [[b1-complete]] "round 2") annotated `maximum_a_posteriori.org` — which has 3 id-links — and ran publish-living. Hugo errored with 3× `REF_NOT_FOUND`. Root cause per [[ox-hugo-id-links-become-relref]]: ox-hugo translates `[[id:UUID][text]]` to `[text]({{< relref "<underscore_filename>.md" >}})` regardless of whether the target is published, AND the underscore-filename form never matches B-emitted hyphen-slug bundle paths.

Without B.1.1, every published note that links to another note breaks the Hugo build. We can't publish anything past the 3 link-less notes already shipped (bayesian/bias/cellular).

## What B.1.1 must do

**Architectural call already made:** pre-export buffer rewrite. Two alternatives (post-export string substitution; `org-link-set-parameters` hook) were considered and rejected — pre-export reuses A.1's existing `rewrite-link` exactly as designed.

Concrete tasks (estimated 5-7 tasks for the slice):

1. New helper `a3madkour-pub-rewrite/rewrite-buffer-links (source-note-id)` in `a3madkour-publish-rewrite.el`. Scans current buffer for `[[link]]` patterns via regex (`\\[\\[\\(?:[^][]\\|\\[[^]]*\\]\\)+\\]\\]`); for each match, calls `a3madkour-pub/rewrite-link` and substitutes with `:html` (resolved) or `:inert` (unresolved). Returns accumulated warnings.

2. Wire into garden handler: between `note-metadata` and `export-file`, copy source to a tmp `.org` file, apply `rewrite-buffer-links` in a temp buffer, write the rewritten content to the tmp file, hand the tmp file to `export-file`. (`export-file`'s contract is unchanged.) The tmp file dance preserves source integrity.

3. ert tests:
   - resolved id-link → markdown contains `<a href="/garden/<slug>/">text</a>` (HTML anchor, not relref shortcode).
   - unresolved id-link → markdown contains just `text` (inert; no broken anchor).
   - multiple links in one line (the MAP case: 3 links on one line) all rewrite correctly.
   - the `*Org Hugo Export*` buffer must not contain `{{< relref` afterward.

4. Python integration fixture: extend `tools/test_publish_integration.py` with a "garden publish with cross-link" fixture — publish a note that links to another published note + a third unpublished one. Assert: hugo --minify exits 0 on the resulting bundles; resolved link renders to `/garden/<slug>/`; unresolved link renders as inert text.

5. Re-run round-2 spot-check (annotate `maximum_a_posteriori.org` again) and confirm `hugo --minify` is clean.

6. While you're in there: also file a small follow-up for `finish-publish`'s no-retry behavior on failed `delete-bundle` (see [[publish-living-fixture-sweep]] secondary finding). At minimum WARN loudly; ideally reset the manifest entry so a retry can succeed.

## State of the world at session start

**Site repo (`/Users/a3madkour/Sync/Workspace/a3madkour.github.io/`):**
- master is **4 commits ahead of origin/master** (last: `2d87feb` link-rewriting findings memo, before that `703bcdd` first real B-emitted content). NOT pushed.
- `content/garden/{bayesian-statistics,bias-vs-variance,cellular-automata-are-visual-rule-based-systems}/` — 3 B-emitted bundles, committed.
- `data/url-history.yaml` — 3 live entries.
- Working tree clean.

**Dotfiles (`~/dotfiles/`):**
- main is **16 commits ahead of origin/main** (last: `0825853` site-content-dir derivation fix). NOT pushed.
- 261 ert tests passing.

**Personal notes (`~/org/notes/`):**
- 3 annotated with `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: garden`: `bayesian_statistics.org`, `bias_vs_variance.org`, `cellular_automata_are_visual_rule_based_systems.org`. NOT git-tracked.
- `maximum_a_posteriori.org` was annotated in round-2 spot-check then rolled back (restored from `/tmp/b1-spotcheck-backup-203015/`). Backup dir survives until tmp cleanup.
- All other notes (54 of 57) unannotated.

## Recommended session start

1. Read CLAUDE.md + [[b1-complete]] (round 2 section) + [[ox-hugo-id-links-become-relref]].
2. Confirm the architectural call (pre-export buffer rewrite) still holds — quick re-read of A.1's `rewrite-link` API in `a3madkour-publish-rewrite.el:269` to refresh.
3. Jump to `superpowers:writing-plans` for B.1.1. Plan is small enough (5-7 tasks) that brainstorming is overkill — the architectural call is already locked in.
4. After B.1.1 ships, decide: push the 20 unpushed commits + Task 17 round-2 publish? Or continue to B.2 first?

## Agent-environment notes (carry-forward from [[b1-complete]])

- **Hugo + emacs + ox-hugo + yaml** all loadable in batch context via `a3-pub.sh` or `run-tests.sh`.
- **`(straight-use-package 'yaml)`** is required in all batch contexts (was a B.0 packaging gap caught + fixed in B.1).
- **`org-roam-directory` defaults to `~/org-roam/`** (doesn't exist on this machine); user's notes at `~/org/notes/`.
- **Site repo at `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/`** (resolved via `git rev-parse --show-toplevel` cascade in `a3-pub.sh`).
- **`note-section` returns string, dispatch keys by symbol** — `walk-section` bridges via `symbol-name`.
- **`a3madkour-pub-site-content-dir` defcustom defaults to nil**; derived from `site-data-dir` via `--site-content-dir-effective`. Don't add machine-specific defaults to similar defcustoms — derive via cascade or env.
