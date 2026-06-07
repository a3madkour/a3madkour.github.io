---
name: tier-1-1-complete
description: "Tier 1.1 (finish-publish advances past failed delete-bundle) — shipped 2026-06-07 in dotfiles e50a037. Step A now gates record-publish 'removed on a non-'failed return from --unpublish-delete-bundle, so a failed delete leaves the manifest at live/draft and the next publish run's diff retries. Suite 606 → 607 ert green. Step B has a similar shape (different failure mode — manifest already points to new URL) filed as 1.10 in the roadmap."
metadata: 
  node_type: memory
  type: project
  originSessionId: 5b5bbb90-9abc-47bc-b613-67a9ddf91b2a
---

**Shipped 2026-06-07.** Bug 1.1 from [[next-slice]] / `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` — `finish-publish` Step A advanced manifest state to `removed` even when `--unpublish-delete-bundle` returned `'failed`, silently orphaning content forever (next run's diff no longer surfaced the id under `:removed`).

## Root cause

In `a3madkour-publish-unpublish.el` `finish-publish` Step A, the `dolist` loop called:

```elisp
(a3madkour-pub--unpublish-delete-bundle (car parts) (cdr parts))
(a3madkour-pub-history/record-publish id nil 'removed)
```

The helper's documented return values are `t` (deleted) / `nil` (already absent) / `'failed` (error caught + WARN logged). The caller ignored the return. B.1.1's Task 7 had added the `'failed` return as a visibility-only upgrade (loud `[a3-pub] delete-bundle FAILED` message) but never wired it through the manifest-state gate. See [[b1-complete]] round-2 secondary finding + B.1.x follow-up #5.

## Fix

Capture the return; only `record-publish ... 'removed` when the result is NOT `'failed`. On `'failed`, leave the manifest at `live`/`draft`; the next publish run's diff re-includes the id in `:removed` and retries. No new manifest schema; no retry loop in-process — self-healing across runs.

Updated docstring of `--unpublish-delete-bundle` to make the contract explicit (was previously "retry / manifest-state reset for self-healing on a subsequent run is left as a future task").

## Test

`a3madkour-pub-unpublish-test/finish-publish-step-a-failed-delete-keeps-manifest-state` — mirrors the existing `step-a-happy` fixture but `cl-letf`-stubs `delete-directory` to signal an error. Asserts:
- `:removed` still reports the id (diff semantics unchanged).
- Bundle still on disk (stubbed delete failed).
- Manifest entry stays `state: "live"`.

Suite 606 → 607 ert green, 0 unexpected. Test failed on first run against the buggy code (clean reproduction); passed after the fix landed.

## Commits

Dotfiles only:
- `e50a037` fix(unpublish): Step A skips record-publish on failed delete-bundle

Site repo: roadmap row marked ✓ + new row 1.10 filed (Step B variant — see "Out of scope" below).

## Out of scope — filed as Tier 1.10

Step B (slug-shift sync) has the same `--unpublish-delete-bundle` call shape, but the failure mode is different: by the time Step B runs, the per-section handler has already written the new bundle and called `record-publish` with the NEW URL. A `'failed` delete on the OLD-slug bundle leaves a stray `content/<section>/<old-slug>/` that Hugo will build as a duplicate page, and no manifest entry tracks the old URL anymore — the next run's diff cannot re-detect it. Possible mitigations recorded in the roadmap row; not implemented here to keep this commit focused on the named bug.

## Cross-references

- Parent spec / queue: `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` Tier 1
- Source memory: [[b1-complete]] (round-2 secondary finding); B.1.x follow-up #5
- Companion: [[next-slice]] (overall queue navigation)
- Next Tier 1 item: 1.2 (`--rewrite-file-link` parity with rewrite-asset-link)
