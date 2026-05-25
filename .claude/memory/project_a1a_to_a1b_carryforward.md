---
name: a1a-to-a1b-carryforward
description: Known A.1.a contract gaps + deferred cleanups to address when writing the A.1.b plan
metadata: 
  node_type: memory
  type: project
  originSessionId: 1a888769-aa2f-4b65-9f3e-7d198d0e6582
---

A.1.a (foundations) is complete and tested (45 ert tests passing) but deliberately leaves three things for A.1.b. When writing the A.1.b plan, ensure each gets an explicit task:

**1. `slug_override` reason value is never emitted (spec gap).** Spec §8 lists four `reason` values in URL-history entries: `title_change | slug_override | section_change | removed`. A.1.a's `--diff-reason` helper only emits the first three (and `removed`) — `slug_override` is impossible to distinguish from `title_change` without source-file context. Fix in A.1.b: extend `(a3madkour-pub-history/record-publish id new-url state)` to take a `:had-slug-override-p` keyword (or replace with a keyword-args API) so the caller in B can supply the hint. Alternative: amend §8 to drop `slug_override` from the vocabulary if A.1.b/B don't end up wanting it. **Decide which at A.1.b brainstorm; do not silently inherit the gap.**

**2. Redundant file I/O across the 4-function API.** `published-p`, `note-section`, `note-slug`, `note-url` each call `--parse-file`, which re-reads + re-extracts keywords from the file. A naive publish loop reading all 4 values pays 4× the I/O. The `--parse-file` docstring explicitly defers this: "A.1.b will introduce a single-pass `note-metadata' accessor + cache." Fix in A.1.b: expose `(a3madkour-pub/note-metadata file)` returning the plist, make the existing 4 functions thin accessors over it, and optionally memoize (cache invalidated on file mtime change).

**3. Empty-string `:section`/`:slug` is normalized to nil in `--parse-file`, then `note-section`/`note-slug` re-do the same `string-empty-p` check** — belt-and-suspenders that became redundant after a code-review fix in Chunk C. Drop the duplicate guards when A.1.b lands the `note-metadata` accessor.

**Deferred per-chunk reviewer nice-to-haves** (informational; pick up if cheap):
- Keywords: indented-keyword test, multi-occurrence note in docstring, `;;; Commentary:` in the test file.
- Slug: paste-safe `"̀-ͯ"` escape style for the combining-mark range; one dedicated separator-vs-drop test.
- History: noop.

**Cross-cutting context for A.1.b:**
- The library lives at `~/dotfiles/emacs-configs/custom/lisp/` — see [[project-phase-3-decomposition]] and the spec `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md`.
- A.1.b is the **link-rewriter** chunk: id-links (live/draft/private/unknown), file-links (auto-convert via target `:ID:`), heading anchors, external URLs, custom typed links + CSS classes, typed-backlinks stub.
- A.1.b adds the **ID→file dispatching layer** so `published-p`/`note-url` accept org-roam IDs (currently file paths only); will use `org-roam-id-find` or equivalent.
- A.1.b must require `org-roam` (a new dep beyond yaml).
- Test runner `run-tests.sh` already bootstraps straight + adds all build dirs — adding org-roam as a dep is one `(straight-use-package 'org-roam)` in the user's config.org (per the same manual step that handled yaml).
- `a3-pub.sh` wrapper exists for CLI invocations — use it for spot-check examples in A.1.b's plan.

**Tooling artifacts to be aware of when planning A.1.b:**
- `a3-pub.sh` — wraps `emacs --batch` with straight bootstrap + `a3madkour-publish` loaded; takes pass-through `--eval` args.
- `run-tests.sh` — auto-discovers every `*-test.el` in the lisp dir; same bootstrap.
- 45 ert tests + 2 yaml-on-disk helpers in `data/url-history.yaml` (seed file in site repo).
