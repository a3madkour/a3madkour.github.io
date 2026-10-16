# S1 dogfood run — friction log

**Roadmap:** `2026-10-15-authoring-infra-roadmap.md` §3.1 (session S1)
**Status:** prepared 2026-10-15, not started
**Purpose:** run the shipped pipeline on real org-roam content in every handled section, and
record every failure and annoyance. Triage at the end decides S2 and feeds B1.

## 1. Prerequisites (do these first, on the machine running S1)

- [ ] Dotfiles: commit or stash local changes, `git pull`, then confirm with
      `git merge-base --is-ancestor origin/main HEAD` (don't trust a piped pull's exit status).
- [ ] Memory symlink: `~/.claude/projects/<project-key>/memory -> <site clone>/.claude/memory`.
- [ ] Trampoline check: run `emacs-configs/custom/lisp/run-tests.sh`, then one living publish
      through `a3-pub.sh` with nothing changed (it has no dry-run flag; an unchanged living
      publish should be a no-op — confirm `git status` in the site repo stays clean). If it
      dies with `invalid version number in '-mmacosx-version-min=…'`, port the `run-tests.sh`
      trampoline fix to `a3-pub.sh` before going further.
- [ ] Baseline: site repo clean on `main`, `hugo --gc --minify` succeeds, no dev server running.
- [ ] Note the starting commit of both repos here: site `________` dotfiles `________`.

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
| | | | | | | |

## 5. Close-out

- [ ] Every row triaged.
- [ ] *fix now* rows copied into S2's task list; *new slice* rows added to the roadmap as stubs.
- [ ] A1 T12 marked closed (or its blockers logged) in the roadmap and in memory
      `project_works_handlers_slice`.
- [ ] Roadmap §2/§3 status updated; memory `project_authoring_infra_roadmap` updated.
