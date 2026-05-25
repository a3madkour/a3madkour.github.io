---
name: a1a-foundations-slice
description: "Phase 3 sub-project A.1.a (foundations layer) — implementation complete 2026-05-20, staged in user's index awaiting commit + push"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1a888769-aa2f-4b65-9f3e-7d198d0e6582
---

A.1.a (foundations) finished implementation 2026-05-20. **Staged in both repos** (user index, not yet committed — session-policy was no-commit; user reviews + commits between sessions).

**Scope delivered** (per `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` §4 + §5 + §8 + §10):
- Per-file org keyword parsing (`HUGO_PUBLISH` / `HUGO_SECTION` / `HUGO_DRAFT` / `HUGO_SLUG` / `HUGO_ALIASES`) + section enum validator (13-member enum).
- Slug derivation: title-derived default + `#+HUGO_SLUG:` override; NFKD ASCII-fold; lowercase + hyphens; separator-class distinction (`._/\\` collapse to hyphens vs apostrophes/etc. drop).
- Public API (file-path input; ID dispatching deferred to A.1.b): `published-p` → `'live | 'draft | nil` (signals `user-error` on bad combos); `note-section` / `note-slug` / `note-url`.
- URL-history manifest (`data/url-history.yaml` in site repo): `read-manifest`/`write-manifest`/`record-publish` (with reason classification: `section_change` | `title_change` | `removed`) / `aliases-for`.

**Files staged (dotfiles repo, branch `main`):**
- NEW: `emacs-configs/custom/lisp/a3madkour-publish-keywords{,-test}.el`
- NEW: `emacs-configs/custom/lisp/a3madkour-publish-slug{,-test}.el`
- NEW: `emacs-configs/custom/lisp/a3madkour-publish-history{,-test}.el`
- NEW: `emacs-configs/custom/lisp/a3-pub.sh` (CLI wrapper; bootstraps straight + loads library; pass `--eval` through)
- MODIFIED: `emacs-configs/custom/lisp/a3madkour-publish{,-test}.el` (entry-point grew from ~25 LoC bootstrap shell to ~140 LoC with 13 new tests)
- MODIFIED: `emacs-configs/custom/lisp/run-tests.sh` (added straight bootstrap + glob-add of build dirs to load-path)

**Files staged (site repo, branch `master`):**
- NEW: `data/url-history.yaml` (empty seed `notes: []` + §8 schema comments)
- NEW: `docs/superpowers/plans/2026-05-20-phase-3-a1-a-foundations.md` (plan doc)
- (Already-staged-from-earlier-in-session, separate commit checkpoints): `M  CLAUDE.md` + `?? docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md`)

**Tests:** 45 ert tests (10 keywords + 9 slug + 12 history + 13 entry-point + 1 bootstrap smoke); all green via `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh`. Per-stage manual-verification checkpoint done — user spot-checked `published-p`/`note-url`/URL-history round-trip; controller verified the same independently. On-disk yaml matches spec §8 schema.

**Execution shape:** 5-plan split (A.1.0 → A.1.a → A.1.b → A.1.c → A.1.d). A.1.0 bootstrap shipped inline-execution earlier in the same session; A.1.a shipped subagent-driven (one implementer per of 4 chunks + spec review + code quality review + final whole-implementation review). Each chunk reviewer found 1–3 minor fixes; all fixed inline.

**Reviewer-flagged carry-forward to A.1.b** (durable in [[a1a-to-a1b-carryforward]]):
1. **`slug_override` reason in spec §8 but never produced** — `--diff-reason` can't distinguish title-change-induced-slug-change from explicit HUGO_SLUG override. A.1.b must either add `:had-slug-override-p` hint to `record-publish` OR amend §8 to drop the value.
2. **Redundant file I/O across 4-function API** — `published-p`/`note-section`/`note-slug`/`note-url` each call `--parse-file`. A.1.b introduces `(note-metadata file)` + memoization.
3. **Belt-and-suspenders empty-string guards** in `note-section`/`note-slug` — duplicate work after `--parse-file`'s normalization landed. Drop once `note-metadata` exists.

Plus deferred per-chunk reviewer nice-to-haves (keywords: indented-keyword test + multi-occurrence docstring note + test-file commentary; slug: paste-safe `\uNNNN` escape style + dedicated separator-vs-drop test).

**In-flight deviations from the plan:**
- `run-tests.sh` extended beyond plan (straight bootstrap + build-dir glob). Plan Task 1 only had `--eval` install.
- `a3-pub.sh` NEW file not in plan — added mid-execution when CLI spot-check commands hit load-path friction.
- yaml.el config switched from planned dynamic vars to keyword args (`yaml-parse-string :object-type 'alist :sequence-type 'array ...`). Plan anticipated this fork.
- `--parse-file` dropped `(org-mode)` activation (code-quality fix; ~1s autoload cost) and normalized empty `:section`/`:slug` to nil (code-quality fix).
- `defgroup a3madkour-pub-history` collapsed into parent `a3madkour-pub` (final reviewer fix: defcustoms now discoverable from `M-x customize-group RET a3madkour-pub`).

**Key tooling artifacts to know next session:**
- `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh` — auto-discovers `*-test.el`, runs ert in batch.
- `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` — wraps `emacs --batch` with library pre-loaded; takes pass-through `--eval` args (prints `[a3-pub] ready (v…)` to stderr before user evals).
- `~/dotfiles/emacs-configs/custom/config.org` line ~2962-2979 — "Exporting to website" stub; needs `(straight-use-package 'yaml)` added + tangle for permanence (per A.1.0 plan Task 1 Step 4; manual author action, not enforced by tests).
