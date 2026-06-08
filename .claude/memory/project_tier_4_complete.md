---
name: project-tier-4-complete
description: Tier 4 (hygiene/cleanup) closed 2026-06-08 in one dotfiles commit — :group rename + unused arg drop + %S fallback fix; 4.3 retro-closed
metadata:
  type: project
---

# Tier 4 hygiene cleanup — shipped 2026-06-08

Roadmap: [[../../docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md]] Tier 4.

## What shipped

All four rows ✓ in one dotfiles commit (`28c83b4`). dotfiles ert suite 616 → 618.

- **4.1** — `:group 'a3madkour-publish` (the bare-typo, non-existent group) → `'a3madkour-pub`. Only two stragglers existed (`a3madkour-publish-frontmatter.el:38`, `a3madkour-publish-unpublish.el:47`); the other modules were already on the canonical `'a3madkour-pub` (or their own `*-pub-assets` / `*-pub-rewrite` / `*-pub-multi` / `*-pub-async` subgroups).
- **4.2** — `a3madkour-pub-research--coerce-year` had an unused `_file` arg. Dropped from defun + the single caller (line 120). No ert tests called it (verified by grep), so signature change is local.
- **4.3** — retro-closed. Grep confirms `rewrite-to-tmp-file` is already fully extracted to `a3madkour-publish-rewrite.el:425` and called from essays/garden/research handlers. No code change.
- **4.4** — `a3madkour-pub-library--render-scalar` `%S` fallback (line 270) now wraps the print form in `--yaml-single-quote`. Without this, a hashtable / struct / vector value in a library extras plist would emit `#<hash-table ...>` / `#s(...)` / `[1 2 3]` as a bare scalar and PyYAML would reject the row. **+2 ert tests** (hashtable + vector) verify the fallback emits single-quoted output.

## Source-pointer correction

Roadmap row 4.4 had pointed at `a3madkour-publish-frontmatter.el` — the actual function is in `a3madkour-publish-library.el`. Corrected in the row inline.

## Files touched (dotfiles)

- `emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` — `:group` typo fix (4.1)
- `emacs-configs/custom/lisp/a3madkour-publish-unpublish.el` — `:group` typo fix (4.1)
- `emacs-configs/custom/lisp/a3madkour-publish-research.el` — drop unused arg (4.2)
- `emacs-configs/custom/lisp/a3madkour-publish-library.el` — wrap `%S` fallback (4.4)
- `emacs-configs/custom/lisp/a3madkour-publish-library-test.el` — +2 ert tests (4.4)

Staged by exact path per the bystander rule — many unrelated dotfiles changes were left untouched in the working tree.

## Next slice

Per the updated roadmap, **Tier 5 is the next session's queue head**. Tier 2.2/2.3/2.4 remain trigger-gated fast-follows; Tier 3 is human-driven QA. Tier 5 has two items: 5.1 `a3-unpublish-deliberate` command (small one-session slice), 5.2 emacs publish-author helpers (own brainstorm → spec → plan → ship cycle).
