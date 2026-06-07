---
name: tier-1-2-complete
description: "Tier 1.2 (--rewrite-file-link parity with rewrite-asset-link) — shipped 2026-06-07 in dotfiles 27d157d. Mirrors the figref fix 1edd900: --rewrite-file-link gains &optional source-file, prefers it when supplied, falls back to --id-to-file for legacy callers; rewrite-link's file-scheme dispatch now threads source-file. Suite 607 → 608 green."
metadata: 
  node_type: memory
  type: project
  originSessionId: 5b5bbb90-9abc-47bc-b613-67a9ddf91b2a
---

**Shipped 2026-06-07.** Bug 1.2 from `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` — `[[file:other.org]]` links from source notes NOT in `org-roam-directory` (e.g. essays under `~/org/essays/` while org-roam points at `~/org/notes/`) silently resolved to wrong paths because the source dir was derived via `(--id-to-file source-note-id)` → nil → fallback to `default-directory`.

## Root cause + parity with figref

Identical architectural shape to the figref fix in commit `1edd900` (`rewrite-asset-link`). The B.1.1 rewriter chain is:

```
rewrite-to-tmp-file (source-file source-note-id)
  └── rewrite-buffer-links (source-note-id source-file)
        └── rewrite-link (org-link source-note-id &optional source-file)
              ├── --rewrite-id-link            (no source-file needed)
              ├── --rewrite-file-link          ← bug 1.2: dropped source-file
              ├── --rewrite-typed-link         (recurses into id-link)
              └── rewrite-asset-link            ✓ figref fix (1edd900) threaded
```

The figref fix only touched the asset-link branch; the file-link branch had the same DB-lookup-of-source-file dependency but was never updated. For interactive Emacs use with the source file open, `default-directory` often happened to match and masked the bug; batch / CLI publishes from the deliberate flow did not.

## Fix

- `--rewrite-file-link` signature: added `&optional source-file`. Body uses `source-file` directly when supplied, otherwise falls back to `(--id-to-file source-note-id)` for backwards compatibility.
- `rewrite-link` file-scheme dispatch (line 315 before edit): now passes `source-file` through as the 4th arg.
- No change to `--rewrite-id-link` recursion — id-links don't have a relative-path dependency.

## Test

`a3madkour-pub-rewrite-test/file-link-relative-path-uses-supplied-source-file` — mirrors the existing `file-link-relative-path-uses-source-dir` fixture but stubs `--id-to-file` → nil for ALL ids and passes `source-file` explicitly through `rewrite-link`'s 3rd arg. Asserts the relative `[[file:tgt.org]]` resolves to `<a href="/garden/target/">text</a>`.

Failed against the buggy code (clean reproduction), passes after the fix. Suite 607 → 608 ert green, 0 unexpected.

## Commits

Dotfiles only:
- `27d157d` fix(rewrite): thread source-file through --rewrite-file-link

Site repo: roadmap row marked ✓ + this memory file.

## Cross-references

- Roadmap: `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` Tier 1
- Prior parity fix: commit `1edd900` (figref / rewrite-asset-link)
- Companion: [[d2-figref-bundled-fix-complete]]
- Next Tier 1 item: 1.3 (TODO filetag leaks into Hugo tags)
