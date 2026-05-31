---
name: emacs-publish-helpers-followup
description: "Queued dotfiles work: a set of interactive Emacs commands that author-side mark notes + library items for export, instead of the user manually editing `#+HUGO_PUBLISH:` / `#+HUGO_SECTION:` headers and library drawer properties by hand. Surfaced 2026-05-30 while seeding library-*.org scaffolds — the scaffold approach is fine but every new entry requires remembering the right drawer-property names + valid status enum, which is friction."
metadata:
  node_type: memory
  type: project
---

**Status:** queued; not yet brainstormed or spec'd. Lives in dotfiles repo when implemented (no site-repo touch).

**Why:** Phase 3 sub-projects A + B shipped the publish-side pipeline (annotate org files, run `a3-pub.sh --publish-living`, B handlers emit to `content/`/`data/`). The author-side ergonomics are still bare:

- Marking a single note for publish requires manually editing `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: <section>` into the file's preamble.
- Adding a library item requires remembering the per-medium drawer-property names (`:CREATOR:` / `:YEAR:` / `:STATUS:` / extras like `:ISBN:` / `:MBID:` / `:IGDB_ID:` / `:RUNTIME_MIN:` etc.) and the valid status enum (different per medium — see [[b2-complete]] §3 config table).
- No fast way to flip a note's publish status, preview what a publish-living run would emit, or jump from an emitted bundle back to its org source.

## Sketch of what the helpers might do

(Not a spec — surface for the brainstorm later.)

- `a3madkour-pub-mark-publish` (interactive): in any org file, completing-read over the registered section names from `a3madkour-pub/sections`, inserts/updates `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: <pick>` in the preamble. Idempotent.
- `a3madkour-pub-unmark-publish`: removes / sets to nil.
- `a3madkour-pub-insert-library-item` (interactive, in a `library-*.org` file): completing-read over status enum (derived from the file's section), inserts a new top-level heading + scaffolded drawer with the medium's required + optional + extras properties pre-filled with `:KEY: ` placeholders; point lands on the heading title.
- `a3madkour-pub-insert-library-drawer-extras`: on an existing library heading, inserts only the extras-drawer block matching the file's medium. For converting legacy entries.
- `a3madkour-pub-preview-section` (interactive): runs `a3-pub.sh --publish-living` in dry-run mode (would need a `--dry-run` flag on the script, which doesn't exist yet) and pops up a buffer with the would-be diff.
- `a3madkour-pub-jump-to-source`: from a `content/<section>/<slug>/index.md` or `data/<medium>.yaml` row, jump to the org source that emits it. Needs the manifest from [[b0-complete]] as the index.
- `a3madkour-pub-current-status`: minibuffer message — "this note is marked for publish (garden)" or "this note is private" or "this file's HUGO_PUBLISH header is missing".

## How this slots into B+

This is **authoring-side**, parallel to B/F/C/D/E (which are all publisher-side). It can ship any time:
- Before B.3 (research) — helpers reduce the cost of B.3's spot-check phase.
- After all B.x slices — once the full publish pipeline is stable, the helpers are mature.
- Between any two slices — small enough to fit in a 30-90 min session.

No hard ordering. Spin it up when authoring friction is annoying enough.

## How to start when ready

1. Read [[b0-complete]] for the section registry shape, [[b1-complete]] for the garden drawer-property surface, [[b2-complete]] for the library per-medium config table.
2. `superpowers:brainstorming` to nail down: which helpers ship in v1, what UX (Vertico/Ivy completion vs. straight `completing-read`, keybinding scheme, where to register in `init.el`), whether `--dry-run` belongs on `a3-pub.sh` or in elisp.
3. `superpowers:writing-plans` for the implementation.
4. Lives in `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-author.el` (new module) + sibling test file. Wire keybindings into the user's `init.el` (separate commit from the library code).

## Cross-references

- Companion to publish-side work in [[b0-complete]] / [[b1-complete]] / [[b2-complete]] / [[next-slice]].
- Surfaced while writing the [[next-slice]]'s "library-*.org seed" scaffolds (commit on 2026-05-30, site repo) — those scaffolds use `#+begin_comment` blocks documenting the drawer shape, which is a stopgap until these helpers exist.
