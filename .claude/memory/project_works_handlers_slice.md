---
name: project_works_handlers_slice
description: "Slice A1 — works/games + works/music org handlers. Built on branch works-handlers in both repos, 12 tasks subagent-driven, NOT YET MERGED. The E2E found 6 defects that 829 green unit tests missed."
metadata:
  node_type: memory
  type: project
---

**2026-09-28/29. Slice A1 of the "author everything from Emacs" decomposition
([[project_authoring_surface_audit]]). Complete and review-clean on branch `works-handlers`
in BOTH repos; NOT merged.**

- Spec: `docs/superpowers/specs/2026-09-28-works-games-music-handlers-design.md` — **read §8a**
- Plan: `docs/superpowers/plans/2026-09-28-works-games-music-handlers.md` (12 tasks)
- Site: `main..works-handlers` = 9 commits, 6 files, +2576/-75
- Dotfiles: `main..works-handlers` = 28 commits, 15 files, +2873/-17
- Verified: elisp 875 tests / 1 known pre-existing failure
  (`a3madkour-pub-multi-pdf/compile-chain-runs-four-passes`); `check_works_fixtures.py` and
  `check_works_links.py` green; the linter's own suite 37/37.

## What shipped

`a3madkour-publish-works.el` — one module, two living-section registrations (`works/games`,
`works/music`) sharing one entry point. `a3madkour-works-lint.el` — pre-publish lint, org
`FILE:LINE:` errors, default-on with `--skip-works-check`. `a3madkour-works-vocab.el` — the
shared-vocabulary reader. Plus: two normalize branches in `frontmatter.el`, an additive
5th positional `extra-refs` on `asset-validate-and-copy`, `collect-triples` inverted to walk
the notes tree once instead of once per handler, and `a3-pub.sh` wiring.

**`data/works-vocab.json` is the single home of the works contract** — enums AND the
required/optional field sets — read fail-closed by `check_works_fixtures.py` and by elisp.
Proven empirically: adding a field to the JSON propagates to both languages with zero code
edits.

## The lesson worth keeping: green ERT is not an acceptance gate

Every one of 12 tasks passed its own adversarial review with a green suite, and **the
end-to-end run then found the feature could not pass `check_works_fixtures.py` at all** —
six defects, then three more at the final review. All needed real ox-hugo, real Hugo, or the
real authoring convention to surface. §8a of the spec tabulates them.

**Nine separate tests on this branch were found to pin nothing.** The shapes, all worth
recognising on sight:
- A test whose **own fixtures authored the wrong form**, so it certified the bug it existed
  to catch (`#+ID:` keyword vs `:PROPERTIES: :ID:` drawer).
- A test that **looped over the very constant it asserted about** — delete a key from the
  constant and it stayed green.
- Tests matching a **substring several code paths emit**, pinning none of them. Assert on
  the distinct part of a message.
- Tests feeding a **hand-built alist** where only the real exporter reproduces the input.
- A **negative** assertion ("this bad output does not appear"), which passes trivially when
  the output shape changes for an unrelated reason.

## Known-good traps recorded here because they cost real time

- **Emacs 31.1 on this macOS cannot native-compile subr trampolines**
  (`clang: invalid version number in '-mmacosx-version-min=18.0'`). Any test that mocks
  `call-process`/`make-process` dies before its own assertions. That was **54 of 55** ert
  failures. `run-tests.sh` now disables trampolines (dotfiles `9a6f12e`) — see
  [[reference_emacs31_subr_trampoline_breakage]].
- `a3-pub.sh` does **not** disable them, and `test_publish_integration.py`'s HOME override
  gives the subprocess an empty `eln-cache`, so **all 15 publish-subprocess tests are red on
  this machine, before and after this branch** (proven by checkout-and-diff of the failure
  sets). Whether a real publish is affected depends on a warm `eln-cache`; untested.
- `json-parse-string ... :object-type 'alist` returns **symbol** keys on Emacs 31.1. Intern
  before an alist lookup, or use `assq`.
- `#+HUGO_CUSTOM_FRONT_MATTER:` carries **flat scalars only** — ox-hugo round-trips any
  value as a string. A map-valued field needs flat component keys assembled in the
  normalizer (`platform_kind`+`platform_url` → `platform_embed`) or a named org table
  (`tracks`). One custom key cannot carry it, and the render hook's `:omit` makes the
  failure **silent**. Spec §3.3.
- **Anything parsed for frontmatter must be stripped before export**, whichever org
  construct carries it. The spec originally claimed dropping the property drawer removed the
  need for a strip stage; the `#+NAME: tracks` table disproved it.

## Left open

- **Real org-roam identity resolution is still unexercised** — all E2E runs stubbed
  `note-metadata`/`note-slug`/`note-url`. Same gap as the outstanding recipes corpus run
  ([[project_recipe_slice_2_complete]]).
- `#+HUGO_SUMMARY:` now works, but whether works wants `summary` *beside* `tagline` is an
  unanswered design question.
- Roadmap rows: rule 6's literal key list should derive from the render key-hook's set (needs
  that `cond` as a table); the double-`on-done` path across five handlers can fire
  `finish-publish` — whose default `:reap t` **is** the orphan sweep — while a file is in
  flight.
- Pre-existing, found en route: `--skip-recipe-check` had no effect on `a3-pub.sh`'s default
  path (**fixed here**); the ert suite writes `citations.yaml` into both source trees on
  every run (not fixed).

## Next in the decomposition

A2 streams (poller queues / Emacs adopts), B1 direct-edit affordances for 19 `_index.md` +
4 curated YAML files, then C the authoring guide. See [[project_authoring_surface_audit]].
