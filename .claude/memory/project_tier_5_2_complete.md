---
name: project-tier-5-2-complete
description: Tier 5.2 closed 2026-06-08 — six interactive emacs publish-author helpers shipped in a3madkour-publish-author.el (dotfiles 8e5e76b)
metadata:
  type: project
---

# Tier 5.2 — emacs publish-author helpers — shipped 2026-06-08

Spec: dotfiles `docs/superpowers/specs/2026-06-08-emacs-publish-author-helpers-design.md` (commit `8767740`).
Plan: dotfiles `docs/superpowers/plans/2026-06-08-emacs-publish-author-helpers.md` (commit `af05d7a`).
Implementation: dotfiles `8e5e76b`.
Roadmap: site `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` Tier 5.2.
Source memo: [[emacs-publish-helpers-followup]].

## What shipped

Single new dotfiles module `a3madkour-publish-author.el` + sibling test + two thin public wrappers in `a3madkour-publish-library.el`. Six interactive commands:

| Command | Purpose |
|---|---|
| `a3-publish-mark` | Idempotent insert/update of `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION:` |
| `a3-publish-unmark` | Flip `#+HUGO_PUBLISH:` to `nil` (preserves `HUGO_SECTION`) |
| `a3-publish-status` | Minibuffer message describing current publish state |
| `a3-library-insert-item` | Scaffold new heading + drawer in `library-*.org` |
| `a3-library-insert-extras` | Add medium-specific extras to existing heading |
| `a3-publish-jump-to-source` | Auto-detect `content/<section>/<slug>/index.md` → org via manifest; completing-read fallback |

Two new public accessors in library.el: `a3madkour-pub-library/sections` and `a3madkour-pub-library/extras-for`. The existing `--double-dash` internals are unchanged.

Test coverage: 33 new ert tests (skeleton 1 + wrappers 3 + status 5 + mark 6 + unmark 4 + insert-extras 4 + insert-item 5 + jump-to-source 5). Suite 629 → 662.

## Implementation notes

- **Subagent-driven** — executed via 8 implementer + 8 review subagent pairs (sonnet impl + haiku review). One mid-task adjustment: `a3-library-insert-extras` wraps `org-back-to-heading t` in `ignore-errors` because some Org builds signal "Before first headline" rather than returning nil, which would otherwise bypass the command's own `user-error`.
- **No `a3-pub.sh` wrapper update** — verified by grep before commit. author.el is interactive-only.
- **Bystander rule** — staged by exact path; many unrelated dotfiles changes left in the working tree.

## Why this design

- **Compose, don't duplicate**: sections registry, library config, extras table, keywords API, manifest walk — all already exist. No new tables = no drift.
- **Synchronous + read-modify-write on the current buffer**: no async lifecycle (author wants immediate result). All edits confined to the buffer.
- **No init.el keybindings this slice**: author binds manually after merge per their preference.

## Deferred to follow-ups

- `a3-publish-preview-section` — needs new `--dry-run` plumbing on `a3-pub.sh` + `publish-living`. Own session. File as roadmap Tier 5.3 when triggered.
- Mode-line `mode-line-misc-info` segment showing publish state.
- Marginalia annotator for `jump-to-source`'s completing-read.
- `a3-library-bulk-import` — CSV → N headings.

## Files touched (dotfiles)

- `emacs-configs/custom/lisp/a3madkour-publish-author.el` — NEW (~250 lines)
- `emacs-configs/custom/lisp/a3madkour-publish-author-test.el` — NEW (~350 lines)
- `emacs-configs/custom/lisp/a3madkour-publish-library.el` — MODIFY (+2 public wrapper defuns)
- `emacs-configs/custom/lisp/a3madkour-publish-library-test.el` — MODIFY (+3 wrapper tests)

Single dotfiles commit (`8e5e76b`, +708 lines).

## Next slice

Per roadmap, **Tier 6 (About Now widget)** is the next session's queue head. 2.2/2.3/2.4 still trigger-gated; Tier 3 human-driven.
