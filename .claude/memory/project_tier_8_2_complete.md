---
name: project-tier-8-2-complete
description: Tier 8.2 closed 2026-06-12 — org → synced-poetry export shipped end-to-end with smoke-test-poem live (dotfiles db9da62..a9a1acb, site e81e227..3506ef7)
metadata:
  type: project
---

# Tier 8.2 — Org → synced-poetry export — shipped 2026-06-12

Spec: site `docs/superpowers/specs/2026-05-19-org-synced-poetry-export.md` (commit `e81e227`).
Plan: site `docs/superpowers/plans/2026-06-12-org-synced-poetry-export.md` (commit `27dc811`).
Implementation: dotfiles `db9da62..a9a1acb` (15 commits, branch `main`).
Roadmap: site `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` Tier 8.2.
Source memo: [[project-phase-3-org-synced-poetry-export]] (now historical — slice shipped).

## What shipped

New peer module `a3madkour-publish-poetry.el` (~370 LOC) — sibling of `a3madkour-publish-essays.el`, not a subordinate. Handles the deliberate publish for `#+HUGO_SECTION: works/poetry` org files into `content/works/poetry/<slug>/index.md` bundles. Both modules call shared B.0 infra (`rewrite-to-tmp-file`, `export-file`, `asset-validate-and-copy`, `record-publish`); the essays handler is untouched by this slice.

### Authoring surface (verified end-to-end with smoke-test-poem)

```org
:PROPERTIES:
:ID:       <uuid>
:END:
#+TITLE: ...
#+DATE: 2026-06-12
#+HUGO_SECTION: works/poetry
#+HUGO_PUBLISH: t
#+AUDIO: reading.mp3            ;; relative filename → bundled, OR https://… → passthrough
#+HUGO_TAGS: example synced
#+HUGO_SUMMARY: ...             ;; ox-hugo has no slot; normalizer reads it directly
#+HUGO_CUSTOM_FRONT_MATTER: :collection ...

[00:01]Lorem [00:02]ipsum ...    ;; markers pass through verbatim; \[mm:ss] escapes preserved
```

### Handler pipeline (6 stages over shared B.0 infra)

1. metadata resolve (id, slug, url)
2. multi_export warn-and-skip + marker/audio mismatch soft warnings
3. pre-export rewrite (`a3madkour-pub-rewrite/rewrite-to-tmp-file`)
4. ox-hugo export → markdown body
5. `--collapse-escaped-markers` (Case C fix), `--classify-audio`, `--count-poem-lines`
6. normalize → render → write-if-different → asset-validate-and-copy → audio copy → record-publish

### Test coverage

Dotfiles ert: **662 → 692 (+30 tests)**. Suite is green.
Site repo: 1 new subprocess integration test `tools/test_publish_integration.py::TestPoetryPublishDeliberate` (~1.7s) — runs `a3-pub.sh --publish-deliberate` against a tmp poetry corpus + verifies both site-side linters in-process.

## Implementation notes

- **Subagent-driven** — Tasks 1-11 each ran as fresh implementer + spec reviewer + code quality reviewer per the `subagent-driven-development` skill. Real-corpus closure (Task 12) ran inline.
- **Master-direct** on both repos (matches D.2, anchor-affordance, all Tier 1/4/5 closure precedents).

## Key design decisions

- **Two-symbol convention** — caught during Task 2 implementer cycle, lives in `[[reference-dotfiles-two-symbol-convention]]`. Dispatch alist + `#+HUGO_SECTION:` + `a3madkour-pub/sections` enum use **slash form** (`'works/poetry`). Normalize whitelist `a3madkour-pub-frontmatter--known-sections` + dispatch arm use **hyphen form** (`'works-poetry`). Plan-top note locked the convention; future handlers in the works/research/library trees will hit the same pattern.
- **Case C ox-hugo escape** — Task 0 reconnaissance (one-off observation, no commits) confirmed ox-hugo doubles the backslash: org `\[mm:ss]` → markdown `\\[mm:ss]`. Runtime parser only matches single-backslash, so unfixed output leaves a stray `\` in rendered HTML. Fix: post-export collapse helper `--collapse-escaped-markers` runs between ox-hugo emit and downstream use. Simpler than the spec-§Risks-#1 protect-and-restore approach; lives in [[reference-ox-hugo-doubles-backslash-escape]].
- **`#+AUDIO:` over body-link** — single keyword, auto-routes by `https?://` prefix. Cleaner than the `[[file:reading.mp3]]` walkthrough alternative; mirrors the per-poem asset dir convention (`<poetry-dir>/assets/<id>/`).
- **Peer module vs wrap-essays** — wrapping essays would force opt-out of its `has_*` scan + essay-flavored normalizer. Peer keeps blast radius scoped to one new file + one dispatch-alist line.
- **Render/write helpers cloned, not extracted** — 4 module-private helpers (`--site-root`, `--write-if-different`, `--render-yaml-value`, `--render-frontmatter`) mirror essays/garden byte-for-byte. Extraction to shared infra waits for a third+ handler (B.4 follow-up #3 already tracks this).
- **Cleanup-stale ordering** — Task 10 wiring debug surfaced: `asset-validate-and-copy` deletes any bundle file not in its referenced-basenames set. Audio copy MUST run AFTER it, not before. Stages numbered 7b/7c with inline comment explaining the constraint.

## Real-corpus bugs caught at closure (smoke-test-poem)

The in-process ert + subprocess integration test passed but missed two normalizer parity gaps that only surfaced against a real org file outside the tmpdir:

1. **`a3madkour-pub/poetry-dir` defcustom default** — was `~/notes/works/poetry/` (no `org/` prefix). The org-notes-dir convention is `~/org/notes/`. Fixed to `~/org/notes/works/poetry/` (commit `a9a1acb`). Failure mode was: audio asset lookup fails → `asset-validate-and-copy` cleanup-stales the previously-staged audio → bundle ends up missing the mp3 entirely.
2. **`#+HUGO_SUMMARY:` not read** — normalizer relied only on `raw-alist`, but ox-hugo has no built-in slot for `HUGO_SUMMARY`. Essays reads it directly via `a3madkour-pub-frontmatter--read-org-keyword`. Mirrored that pattern (commit `a9a1acb`). Failure mode was: `summary: ""` in emitted frontmatter regardless of source.

Both fixes verified by re-running `a3-pub.sh` → green publish + correct frontmatter + 30s mp3 bundled.

## Smoke-test fixture

`content/works/poetry/smoke-test-poem/` — sibling of `example-poem-synced` (which uses absolute URL `audio_url:`). Smoke-test exercises the **bundled-audio** path: relative `audio_url: "reading.mp3"` + 30s mp3 from `download.samplelib.com/mp3/sample-30s.mp3`. Lorem ipsum body with `\[00:99]` literal escape + `**irure**` bold. Source org at `~/org/notes/works/poetry/smoke-test-poem.org`.

Functions as the live verification of the elisp pipeline (smoke-test-poem rendered correctly in dev server: 21 word-spans with `data-t`, `data-audio-src="reading.mp3"`, `data-duration="21"`, citation auto-note "With audio reading.").

## Files touched

### Dotfiles (15 commits, branch `main`)

- `emacs-configs/custom/lisp/a3madkour-publish-poetry.el` — NEW (~370 LOC)
- `emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el` — NEW (~300 LOC, 30 tests)
- `emacs-configs/custom/lisp/a3madkour-publish-deliberate.el` — +2 lines (require + alist entry)
- `emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` — +2 lines (dispatch arm)
- `emacs-configs/custom/lisp/a3-pub.sh` — +1 line (`-l` load)

### Site repo (10 commits, branch `master`)

- `docs/superpowers/specs/2026-05-19-org-synced-poetry-export.md` — spec (replaced 2026-05-19 stub)
- `docs/superpowers/plans/2026-06-12-org-synced-poetry-export.md` — plan
- `tools/test_publish_integration.py` — +167 lines (`TestPoetryPublishDeliberate` class)
- `content/works/poetry/smoke-test-poem/index.md` + `reading.mp3` — smoke-test fixture
- `data/url-history.yaml` — manifest entry for smoke-test-poem
- `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` — Tier 8.2 row marked closed

## What's next

Per roadmap, the only remaining Tier 8 row is **8.1 — Sub-project E (explorable explainables)**. Phase 3's final piece. No spec, no plan — would start with own brainstorm cycle. See `memory/project_phase_3_decomposition.md` + parent spec §14.

Tier 3 still human-driven (manual QA). Tier 7 trigger-gated (LHCI ergonomics, waits for author friction). All other tiers closed.

Outside the roadmap: real authored poems can now ship via `a3-pub.sh --publish-deliberate ~/org/notes/works/poetry/<slug>.org` — the pipeline is production-ready.
