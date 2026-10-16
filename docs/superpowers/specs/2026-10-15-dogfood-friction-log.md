# S1 dogfood run — friction log

**Roadmap:** `2026-10-15-authoring-infra-roadmap.md` §3.1 (session S1)
**Status:** prerequisites done 2026-10-15; blocked on log row 2 before any real publish
**Purpose:** run the shipped pipeline on real org-roam content in every handled section, and
record every failure and annoyance. Triage at the end decides S2 and feeds B1.

## 1. Prerequisites (do these first, on the machine running S1)

- [x] Dotfiles: commit or stash local changes, `git pull`, then confirm with
      `git merge-base --is-ancestor origin/main HEAD` (don't trust a piped pull's exit status).
- [x] Memory symlink: `~/.claude/projects/<project-key>/memory -> <site clone>/.claude/memory`.
- [x] Trampoline check: run `emacs-configs/custom/lisp/run-tests.sh`, then one living publish
      through `a3-pub.sh` with nothing changed (it has no dry-run flag; an unchanged living
      publish should be a no-op — confirm `git status` in the site repo stays clean). If it
      dies with `invalid version number in '-mmacosx-version-min=…'`, port the `run-tests.sh`
      trampoline fix to `a3-pub.sh` before going further.
- [x] Baseline: site repo clean on `main`, `hugo --gc --minify` succeeds, no dev server running.
- [x] Note the starting commit of both repos here: site `8ba7dc2` dotfiles `0e8c7b7`.

**Prereq results (2026-10-15, MacBook):** dotfiles fast-forwarded 2 commits (ancestry asserted); the 6 uncommitted local edits were left in place (none overlap the pulled change). Memory symlink was already present. `run-tests.sh` 927 run / 926 pass / 1 skip, so no trampoline failure, and `a3-pub.sh` loads cleanly under Emacs 31 (only `when-let` obsolescence warnings). The no-op living publish is **not** a no-op: see log rows 1–2. `hugo --gc --minify` succeeds.

## 2. How each section is run

A note publishes when it carries `#+HUGO_PUBLISH: t` and `#+HUGO_SECTION: <section>`
(`a3-publish-mark` sets both; `a3-publish-status` reports them). Living sections publish with
`a3-publish-living`; essays and poetry with `a3-publish-deliberate`. After each section:
`tools/ci-local.sh` (or at least the section's fixture + link linters), a local
`hugo server --buildDrafts`, and a browser look at the index and each new page (also at 960px).

## 3. Candidates per section (as found on 2026-10-15 — you pick)

| Section | Command | State today | Candidate real content |
|---|---|---|---|
| garden | living | 4 real notes published | ~55 unmarked concept notes in `~/org/notes/`, plus `~/org/notes/ref-notes/` (76) for the reference flavor. Pick 3–5 that link to each other and to the published four, so the graph and link linter get real edges. |
| library ×4 | living | Each `notes/library-*.org` holds only the 2 example items | Add 1–2 real items per shelf with `a3-library-insert-item`; at least one with a cover (`tools/fetch_library_covers.py`). |
| research themes / questions | living | Example notes only | A real theme + 1–2 questions, linked to garden notes via `supporting_notes`. Likely sources: the circuits / PCG / Bayesian clusters in `notes/`, `projects/PCG.org`. |
| essays | deliberate | Example essays only (`~/org/essays/`) | One real essay or draft; `~/org/blog/` may hold candidates. Prefer one with a citation and a sidenote. |
| works/poetry | deliberate | One smoke-test poem | `~/org/Artistic/creative-writing/poetry.org`, `~/org/Artistic/google-note-poems.org`. |
| works/games | living (A1) | Never run on real org-roam | `~/org/projects/games.org`. **A1 T12: modifies real org files — explicit consent at run time.** |
| works/music | living (A1) | Never run on real org-roam | `~/org/projects/music.org`, `~/org/Artistic/music_production.org`. Same T12 consent. |

Things to watch, from earlier slices: real org-roam ID resolution (every A1 E2E stubbed it);
cross-section links (garden ↔ research ↔ essays); citations via `a3-sync-citations`; asset
copying; the orphan sweep on a second living publish; unpublishing one note and republishing.

## 4. Log

Severity: *blocks publish* / *wrong output* / *annoyance*.
Triage: *fix now* (S2) / *fold into B1* / *new slice* / *won't fix*.
Rule: *blocks publish* and *wrong output* are always *fix now*.

| # | Section | Action | What happened | Severity | Triage | Resolving commit |
|---|---|---|---|---|---|---|
| 1 | (all) | `a3-pub.sh --publish-living` on a new machine | Exit 2: `org-math-lint not installed at ~/org/notes/tools/org-math-lint/.venv/bin/python`. That path is hard-coded (`a3-pub.sh:78`) and does not exist here; the tool is installed via uv (`~/.local/bin/org-math-lint`) and cloned at `~/Sync/Workspace/org-math-lint`. The suggested install command `cd`s into a missing directory. Worked around with `--skip-math-check`. | blocks publish | fix now | |
| 2 | essays, poetry, garden | Unchanged living publish (§1 no-op check), site `8ba7dc2`, dotfiles `0e8c7b7` | Not a no-op. Deleted every deliberate-published bundle — `essays/example-{one,two,three,four,multi}/` and `works/poetry/smoke-test-poem/` — although their org sources are still marked `#+HUGO_PUBLISH: t`. Also deleted `garden/mei-r-wom-2026/`, rewrote `garden/bayesian-statistics/` (dropped a body link present on the site but absent from this machine's org source), and added `last_modified` to every `data/url-history.yaml` entry. Log line: `delete-bundle: …/example-essay-multi-target-export/ already absent (stale manifest?)`. Org files untouched (mtime diff clean). Restored with `git restore -- content data`. Unresolved: whether the garden changes are org-tree drift between machines or the same sweep bug. | wrong output | fix now | |

## 5. Close-out

- [ ] Every row triaged.
- [ ] *fix now* rows copied into S2's task list; *new slice* rows added to the roadmap as stubs.
- [ ] A1 T12 marked closed (or its blockers logged) in the roadmap and in memory
      `project_works_handlers_slice`.
- [ ] Roadmap §2/§3 status updated; memory `project_authoring_infra_roadmap` updated.
