# Phase 3 sub-project A — A.1.b link rewriter — design

**Date:** 2026-05-20
**Status:** brainstormed; awaiting plan
**Phase fit:** Phase 3, sub-project **A**, sub-slice **A.1.b** (link rewriter + ID dispatching + carry-forwards). Third of A's five-plan sequence (A.1.0 → A.1.a → **A.1.b** → A.1.c → A.1.d).
**Parent spec:** [`2026-05-20-phase-3-access-control-link-semantics-design.md`](./2026-05-20-phase-3-access-control-link-semantics-design.md) (the sub-project A spec). This document captures A.1.b-specific design decisions and amends parent-spec sections where this slice diverges from the original sketch.
**Predecessor slice:** A.1.a foundations (keyword parsing, slug derivation, `published-p` / `note-url`, URL-history manifest). Plan doc: [`2026-05-20-phase-3-a1-a-foundations.md`](../plans/2026-05-20-phase-3-a1-a-foundations.md). Carry-forward memory: `memory/project_a1a_to_a1b_carryforward.md`.

---

## 1 — Scope

In:
1. **Link rewriter** (`rewrite-link`) — id-links, file-link auto-convert via target `:ID:`, heading anchors (`*Section`), external pass-through (`http(s)`, `mailto`, `tel`, other URL schemes), custom typed links with `class="link-<type>"`. Asset-shaped links (`[[./assets/...]]`, absolute paths to canonical root) return `:pending-asset` sentinel + WARN; A.1.c upgrades.
2. **ID dispatching layer** — `published-p` / `note-url` / `note-section` / `note-slug` accept org-roam UUIDs (currently file-paths only). New private `--id-to-file` uses `org-roam-id-find`. Adds `org-roam` as a new dep.
3. **`note-metadata` accessor + per-publish-run memoization** — single-pass plist returned from one `--parse-file` call; the 4 existing public accessors become thin wrappers over it; redundant empty-string guards in `note-section`/`note-slug` are dropped (parent-spec carry-forward #2 + #3).
4. **`slug_override` reason resolution** — `:had-slug-override-p` keyword on `record-publish`; `--diff-reason` consults it to emit `slug_override` vs `title_change` correctly (parent-spec carry-forward #1).

Out (queued elsewhere):
- Asset link real handling + the 24th linter pair → **A.1.c**.
- Unpublish flow + integration tests → **A.1.d**.
- `--strict` mode, `:noexport:` link rejection, typed-backlinks real data → **A.2**.

## 2 — API surface (this slice)

```elisp
;; NEW (public)
(a3madkour-pub/note-metadata file-or-id)
  ; → plist (:id :section :slug :state :file :title ...) | nil
  ; Snapshot at first call this publish run; result cached.

(a3madkour-pub/rewrite-link org-link source-note-id)
  ; → (:html "<a …>text</a>" :warnings (...))
  ;  | (:inert "text" :warnings (...))
  ;  | (:pending-asset original-link-text :warnings (...))  ; A.1.c stub

;; NEW (private — internal helpers)
(a3madkour-pub--id-to-file id)              ; → abs-file-path | nil; uses org-roam-id-find
(a3madkour-pub--heading-anchor heading-text) ; → string; Goldmark `github` autolink-style slug

;; EXTENDED — UUID now accepted in addition to file-path
(a3madkour-pub/published-p   file-or-id)
(a3madkour-pub/note-section  file-or-id)
(a3madkour-pub/note-slug     file-or-id)
(a3madkour-pub/note-url      file-or-id)

;; EXTENDED — keyword param
(a3madkour-pub-history/record-publish id new-url state &key had-slug-override-p)
```

**Notable: `rewrite-link` is 2-arity, not 3.** Parent spec §10 sketched `(rewrite-link org-link source-note-id build-mode)`; A.1.b drops `build-mode` because no behavior in the per-link-type table actually diverges by build mode (draft-target links emit the same `<a>` either way; WARN is emitted unconditionally; Hugo handles dev/prod gating downstream).

## 3 — Cache + DB-sync discipline (snapshot-at-publish-start semantics)

A.1.b introduces two snapshots taken at publish start:

1. **Metadata cache** — `defvar a3madkour-pub--metadata-cache` is a hash table keyed by absolute file path. `note-metadata` populates entries on first read; subsequent accessor calls hit the cache (no re-parse). **Reset explicitly at publish start** via `(setq a3madkour-pub--metadata-cache (make-hash-table :test 'equal))`.

2. **org-roam DB sync** — `(org-roam-db-sync)` invoked at publish start. Guarantees ID resolution sees current on-disk state. DB snapshot taken at the same moment as the metadata cache reset.

**Snapshot semantics, explicit:** edits to org files made *during* a publish run are NOT picked up. The author re-runs publish to see those changes. This is documented:
- In the `note-metadata` docstring.
- In `published-p` / `note-section` / `note-slug` / `note-url` docstrings (each of which mentions cache behavior briefly).
- In the A.1.b plan doc (design notes section).
- In the parent spec §11 testing-strategy section (mini-subsection on snapshot semantics).

**Publish is invokable from interactive emacs**, not shell-only — both contexts get the same snapshot semantics. Stale-after-edit-during-publish is acceptable in both.

## 4 — File organization

| Change | File |
|---|---|
| NEW | `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el` + `a3madkour-publish-rewrite-test.el` |
| NEW | `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-id.el` + `a3madkour-publish-id-test.el` |
| MODIFY | `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` (+ test sibling) — introduce `note-metadata`; refactor 4 accessors to thin wrappers; accept `file-or-id` via `--id-to-file` dispatch; publish-start cache reset entry-point |
| MODIFY | `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el` (+ test sibling) — `record-publish` keyword arg + `--diff-reason` upgrade |
| MODIFY | `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh` — add `(straight-use-package 'org-roam)` to bootstrap |
| MODIFY | `~/dotfiles/emacs-configs/custom/config.org` — add `(straight-use-package 'org-roam)` near the existing yaml install (manual author action; not enforced by tests) |

**Why split the rewriter and id files?** The rewriter is logic-heavy (per-link-type dispatcher + anchor slugifier); the id module is the org-roam dep boundary. Keeping them separate makes the dep surface easy to audit and the rewriter logic unit-testable with mocked id lookups.

## 5 — Per-link-type dispatch (concrete behavior in A.1.b)

Implementation of parent-spec §6 table, scoped to A.1.b's in-scope link types:

| Org link form | A.1.b behavior |
|---|---|
| `[[id:UUID][text]]` (live target) | `(:html "<a href=\"/<section>/<slug>/\">text</a>" :warnings nil)` |
| `[[id:UUID][text]]` (draft target) | `:html` with same href + WARN if source is live ("live note links to draft target") |
| `[[id:UUID][text]]` (private / unknown UUID) | `(:inert "text" :warnings ("link target X is private/unknown"))` |
| `[[file:foo.org][text]]` (target has `:ID:`) | Resolve to id-link via target's `:ID:`; recurse |
| `[[file:foo.org][text]]` (target lacks `:ID:`) | `(:inert "text" :warnings ("file-link target lacks :ID:"))` |
| `[[id:UUID::*Section][text]]` (live target, heading exists) | `:html` with `href="/<section>/<slug>/#<goldmark-slug>"` |
| `[[id:UUID::*Section][text]]` (live target, heading missing) | `:html` with href + WARN ("heading not found in target") |
| `[[id:UUID::*Section][text]]` (private target) | `:inert` (anchor lost) + WARN |
| `[[<type>:UUID][text]]` where `<type>` ∈ configured custom-link-types | Per id-link rules + `class="link-<type>"` always emitted (even on inert variant — relevant for A.2 typed-backlinks data) |
| `[[https://…][text]]` / `[[http://…][text]]` | `(:html "<a href=\"https://…\">text</a>" :warnings nil)` — pass-through |
| `[[mailto:…]]`, `[[tel:…]]` | Pass-through `:html` |
| Other URL schemes (`ftp:`, `git:`, etc.) — not `id:`/`file:`/custom-type | Pass-through `:html` |
| `[[./assets/...]]`, abs paths to canonical root, etc. | `(:pending-asset original-link-text :warnings ("asset rewriting deferred to A.1.c"))` |
| `[[id:UUID::*Section]]` (target live, heading inside `:noexport:` subtree) | A.1.b: treated as link-to-published-file (anchor pointless but page works), silent. A.2 will detect + treat as inert with WARN. |

**Custom typed-link list** — `(defcustom a3madkour-pub-typed-link-types '(supports contradicts extends example-of causes) ...)`. User can extend via `M-x customize-group RET a3madkour-pub`.

**Heading-anchor slugifier** — implements Hugo Goldmark's `github` autolink-headings algorithm (preserve unicode letters/numbers; lowercase; whitespace → hyphen; strip non-letter/non-number/non-`-`/non-`_`). Reference: `goldmark/extension/auto_heading_id.go`. A.1.b's plan task will pin the exact algorithm + write a Goldmark-cross-check test suite covering accented characters, contiguous spaces, leading/trailing whitespace, and punctuation.

## 6 — Carry-forward resolutions from A.1.a

1. **`slug_override` reason** — `:had-slug-override-p` keyword on `record-publish`. The caller (B's publisher, eventually) reads the source file's `#+HUGO_SLUG:` keyword; passes `t` when set, `nil` otherwise. `--diff-reason` emits `slug_override` when the keyword is `t` AND the slug changed; emits `title_change` when keyword is `nil` AND the slug changed.
2. **Redundant file I/O across the 4-function API** — resolved by `note-metadata` + per-publish hash table memoization (§3). The 4 accessors become one-line wrappers.
3. **Belt-and-suspenders empty-string guards** — removed when accessors become thin wrappers (the work the guards did is already done in `--parse-file`'s normalization).

## 7 — Parent-spec amendments

Apply at the end of this brainstorm (single commit alongside this design doc):

- **§6 per-link-type table** — add row for asset-shaped links in A.1.b: `:pending-asset` sentinel + WARN ("asset rewriting deferred to A.1.c"). A.1.c upgrades that row to real `:asset` semantics.
- **§6 heading-anchor row** — pin slug algorithm to Hugo Goldmark `github` autolink style (reference doc + algorithm sketch).
- **§10 API sketch** — drop `build-mode` from `rewrite-link` signature; add `:pending-asset` to documented return shapes.
- **§11 testing-strategy** — add subsection on snapshot-at-publish-start semantics (metadata cache reset + `org-roam-db-sync` invocation at publish start; stale-after-edit-during-publish is acceptable).
- **§8 URL-history vocabulary** — clarify that `slug_override` is emitted when caller passes `:had-slug-override-p t` to `record-publish`.

## 8 — Testing

| Layer | What | How |
|---|---|---|
| ert unit | Per-link-type dispatcher (every row in §5 table) | New `a3madkour-publish-rewrite-test.el` |
| ert unit | ID dispatching (known UUID → file; unknown UUID → nil) | New `a3madkour-publish-id-test.el` with mocked `org-roam-id-find` |
| ert unit | Heading-anchor slugifier — Goldmark cross-check suite | Hand-computed reference set: accented chars, contiguous spaces, leading/trailing whitespace, punctuation, empty heading |
| ert unit | `note-metadata` cache hit/miss; explicit reset | `a3madkour-publish-test.el` updates |
| ert unit | `record-publish` with `:had-slug-override-p` (both branches) | `a3madkour-publish-history-test.el` updates |
| Tmp-dir fixture | Rewriter against seeded `~/org/notes/` skeleton (2–3 org files + bootstrap org-roam DB) | New helper in test sibling; uses `(make-temp-file ... t)` + minimal org-roam DB init |
| Per-stage manual checkpoint | After each implementation chunk, author runs `rewrite-link` via `a3-pub.sh` on the seeded corpus + spot-checks output | Plan doc enumerates checkpoints |

Integration tests (full publish round-trip) remain deferred to **A.1.d**, where unpublish + integration land together.

## 9 — Open questions

1. **org-roam DB location at publish time.** The default is `~/org/notes/org-roam.db`. Confirm this matches the author's setup (or expose a defcustom). Decide at plan time; trivial either way.
2. **`org-roam-db-sync` cost on first run after fresh clone.** Could be slow on a many-thousand-note corpus. Acceptable trade-off given snapshot guarantees; surface in `a3-pub.sh` startup log so author knows what's happening.

## 10 — Dependencies + transitions

- **New runtime dep:** `org-roam` (via straight) — added to `run-tests.sh` bootstrap and to `config.org` author config.
- **After A.1.b ships:** A.1.c picks up assets + the 24th linter pair. A.1.b's `:pending-asset` sentinel return becomes the spec contract A.1.c implements against.

## Spec self-review checklist (per superpowers:brainstorming)

- ✅ No "TBD" / "TODO" in this doc (the open questions in §9 are scoped and resolvable at plan time).
- ✅ Internal consistency — API surface (§2) matches per-link-type behavior (§5) matches testing (§8); parent-spec amendments (§7) line up with carry-forward resolutions (§6) and API changes (§2).
- ✅ Scope check — single slice's worth of work; well-defined; A.1.a precedent shows comparable scope shipped cleanly subagent-driven.
- ✅ Ambiguity check — every per-link-type row in §5 has explicit input shape + output shape; `:pending-asset` boundary explicit.
