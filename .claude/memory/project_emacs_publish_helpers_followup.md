---
name: emacs-publish-helpers-followup
description: "Emacs author-side publish helpers — SHIPPED as Tier 5.2 (2026-06-08). Six interactive commands in a3madkour-publish-author.el. One sketched command did not ship: the dry-run publish preview."
metadata:
  node_type: memory
  type: project
---

**Status: SHIPPED (Tier 5.2, 2026-06-08).** Previously recorded here as "queued; not yet
brainstormed or spec'd" — that was stale and was corrected 2026-09-27 while auditing the
authoring surface.

- Spec: `~/dotfiles/emacs-configs/custom/docs/superpowers/specs/2026-06-08-emacs-publish-author-helpers-design.md`
- Plan: `~/dotfiles/.../plans/2026-06-08-emacs-publish-author-helpers.md`
- Code: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-author.el` + sibling test
- Closure memo: [[project_tier_5_2_complete]]

## What shipped — six interactive commands

| Command | Purpose |
|---|---|
| `a3-publish-mark` | Set/update `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION:` in the current org buffer |
| `a3-publish-unmark` | Flip `#+HUGO_PUBLISH:` to nil, preserving the keyword line + section |
| `a3-publish-status` | Minibuffer report of the current file's publish state |
| `a3-library-insert-item` | New top-level heading + scaffolded drawer in a `library-*.org` |
| `a3-library-insert-extras` | Per-medium extras drawer keys on an existing library heading |
| `a3-publish-jump-to-source` | From `content/<section>/<slug>/index.md` back to the org source, or completing-read over the manifest |

## The one sketched command that did NOT ship

`a3madkour-pub-preview-section` — a dry-run of `a3-publish-living` that pops up a buffer
with the would-be diff. It was cut because it needs a `--dry-run` path the shell wrapper
does not expose. Note that `asset-validate-and-copy` already takes a `dry-run` argument,
so the primitive exists at the asset layer; what is missing is a whole-run dry mode and
the wrapper flag.

**Why it still matters:** with `works/games` and `works/music` joining the living sweep
(slice A1), a living publish will touch more sections at once, and "show me what this
would change before it changes it" gets correspondingly more valuable.

## Full Emacs command surface today

Publishing: `a3-publish-living` · `a3-publish-deliberate` · `a3-unpublish-deliberate`
Authoring: the six above
Citations: `a3-sync-citations`
Async control: `a3-pub-async/cancel-current-run` · `a3-pub-async/buffer`

Shell: `a3-pub.sh --publish-living` / `--publish-deliberate <path>`, with
`--skip-math-check` and `--skip-recipe-check`.

## Cross-references

- Authoring-surface audit and the four-tier gap list: [[project_authoring_surface_audit]]
- Slice A1 (games + music handlers): [[project_works_handlers_slice]]
