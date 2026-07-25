---
name: project_publish_pipeline_audit
description: Six-lens adversarial audit of the org-export publish pipeline (dotfiles elisp) + P1/P2 remediation in progress
metadata: 
  node_type: memory
  type: project
  originSessionId: 9e1e6f44-b16e-444f-a116-99162a5e0853
---

**2026-07-05/06.** Ran a six-lens adversarial audit (via [[adversarial-audit]] skill) on the org→Hugo/PDF/Word publish pipeline: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish*.el` (25 source modules ~7,650 LOC + `a3-pub.sh`, 25 ERT test files ~10k LOC). Roadmap written to `~/dotfiles/emacs-configs/custom/docs/superpowers/specs/2026-07-05-publish-pipeline-audit-roadmap.md` (rows P1 blocking / P2 correctness / P3 dedup / P4 test / P5 hygiene).

**Two systemic findings:** (1) the destructive orphan sweep had no safety rails (deleted `content/<section>/<slug>/` bundles off an incomplete accumulator — partial/cancelled run, empty walk, or nil-slug could wipe live content); (2) "copy instead of abstract" again — a 5-fn YAML render stack copied across 4-5 handlers, already drifted, and the direct cause of the P1.2 escaping bug.

**User chose to fix P1 + P2** (blocking + all 14 correctness) via TDD. Work is in `~/dotfiles` (repo on `main`, has unrelated dirty files — do NOT commit those; nothing committed yet, left for user).

**Test harness gotcha:** `run-tests.sh` loads `.elc` over newer `.el` (`require` prefers compiled). Stale Jun-13 `.elc` shadowed edits → had to `rm -f a3madkour-publish*.elc` (untracked, regenerable) to TDD against source. Baseline was 692 tests; after P1 = 708, all green.

**P1 SHIPPED (verified, 16 new tests):**
- P1.1a status gate: `a3madkour-pub/finish-publish` gained `&key (reap t)`; `a3-pub-async/finish-publish` passes `:reap (eq status 'ok)` so err/cancelled runs skip the sweep.
- P1.1c circuit-breaker: defcustoms `a3madkour-pub-unpublish-removal-floor-count` (5) + `-max-removal-ratio` (0.5); refuse sweep when live-set ≥ floor AND removal fraction > ratio.
- P1.1d delete-bundle guards: error on nil content-root (no cwd fallback), skip empty section/slug, verify `index.md`/`_index.md` present before recursive delete (now `cl-defun`).
- P1.1e nil-slug WARN in `walk-published-source-set`; P1.1f cancel docstring fixed; P1.1g atomic manifest write (temp + `rename-file`) in `history/write-manifest`.
- P1.2 YAML escaping: added shared `a3madkour-pub/yaml-escape-scalar` in core; routed all 4 `--render-yaml-value` (garden/essays/poetry/research) + research output-row through it. Fixes deploy-breaking invalid YAML on quoted titles.

**P2 SHIPPED — all 14, TDD, 731/731 green** (692 baseline +39 tests). Six done by parallel subagents on disjoint files (history/multi-pdf/rewrite/citations/library/multi-filter); the cross-cutting ones (P2.1 record-publish state ×4 handlers, P2.8 has_* fence-strip, P2.12 accumulator new-set filter) + the two production-wiring completions by me.
- P2.1 `(or (plist-get md :state) 'live)` in all 4 handlers (garden needed an `md` binding). P2.8 use fence-stripped `scan-body` for all has_* scans. P2.9 `--coerce-bool` (string "false"→nil). P2.11 drop the `(> coerced 0)` gate. P2.12 filter accumulator to live/draft+url-bearing when building new-set. P2.13 shared `--escape-attr-value`. P2.5 `note-slug` not file-name-base. P2.6 permissive `--file-top-level-id` regex. P2.7 synth `id:` text on no-display file link. P2.10 `--coerce-year` + skip-on-missing-status. P2.3 `:svg-source-file` seam + `multi.el` caller.

**Both follow-ups resolved (2026-07-06):**
- **P2.14 DONE (full wiring):** manifest persists `last_modified` (record-publish `:last-modified`, canonical key order extended, `recorded-last-modified` reader that degrades to nil); cascade gained `prior-recorded` slot + ambient `--prior-last-modified` dynamic var; all 4 handlers bind the recorded value around `normalize` + pass resolved date to record-publish. Proven idempotent by e2e garden test. Byte-stability preserved (key emitted only when present).
- **P2.2 residual — assessed, deliberately NOT changed:** unreachable in practice (id-less = essays = `deliberate--handlers` = skips Step A sweep; living-swept sections are all roam-indexed). A correct fix needs an invasive real-id-vs-surrogate refactor across diff/walk/finish-publish (`record-publish id nil 'removed` misfires on url-surrogate key) = data-loss risk for zero benefit. Documented limitation.

**P3 (dedup) — P3.1/P3.3/P3.7 SHIPPED (2026-07-06), 744/744 green:**
- P3.1 (`be2e4d1`) — new `a3madkour-publish-yaml.el`: shared site-root/write-if-different/render-value/render-frontmatter; handlers = thin wrappers passing drift as params (strict flag, key-hook `tags-empty-array-hook`/research outputs hook, value-fn). ~180 LOC collapsed.
- P3.3 (`0f6d012`) — new `a3madkour-publish-multi-backend.el` (probe-tools/convert-svgs-fan/log-line/run-scaffold); PDF+Word thin over it. NOTE: delegated subagent STALLED (600s watchdog) after PDF; I finished Word `/run` migration + dropped dead `multi-word--log-line` + wrote the module self-test.
- P3.7 (`c0de36e`) — shared `a3madkour-pub/warn` core; research + 3 frontmatter WARNs delegate.
- FLAGGED (not done, rationale in roadmap): P3.2 (handlers too divergent — risk), P3.4 (library slug NFD-vs-NFKD = behavior/URL change, needs user call), P3.5 (marginal + delicate normalizers), P3.6 (adds coupling), P3.8 (test-only churn — focused follow-up available).

**P4 (test-coverage) DONE (2026-07-06, `9892101`, TDD test-only, 744→753 green):** the four flagged gaps were all orchestration-wiring (destructive primitives already well-covered). P4.1 living idempotency e2e (`a3-publish-living` twice → byte-identical bundle; genuinely guards P2.14 reuse — run 2 fs-mtime advances yet first date survives). P4.2 error-aggregation roll-up (living barrier → 'err on any handler err/throw, 'ok only all-ok; deliberate throw logs handler-error + finishes 'err — partial-fail can't report 'ok). P4.3 :removed w/ nil/malformed current_url never converges (delete-bundle uncalled, manifest not advanced). P4.4 recheck self-source skip (removed note no false-positive orphan WARN). **P4.5 assessed + NOT changed** (log-step glyph/modeline + featurep smokes verify real renderer output / catch load failures, not tautologies — same call as P3.8). Only P5 (hygiene) left.

**P5 (hygiene) DONE (2026-07-06, `7161d59`) — CLOSES THE WHOLE ROADMAP.** 751/751 green (753−2 removed redundant tests). P5.1 rename `citations--ref-notes-dir`→`citations/ref-notes-dir` (module-scoped public convention) + `define-obsolete-variable-alias`. P5.3 remove dead `frontmatter--infer-flavor`+`--media-flavors` and `multi-pdf--log-line`+its 2 tests (backend self-test covers formatting). P5.4 multi.el `(require 'a3madkour-publish-yaml)`+call `yaml/site-root` not essays-private `--site-root`. P5.5 a3-pub.sh: `--publish-living` condition-case→`kill-emacs 1` (mirrors deliberate; async 'err roll-up still unobserved by wrapper — noted); SITE_DATA_DIR+target_path via exported env+`getenv` not raw --eval splice (fixes `"`/`\` breakage/injection); assign+export split lines so `|| exit 1` not masked by export builtin (bash gotcha). **P5.2 flagged** (async prefix/command-surface rename = high-churn, user-facing command renames, cosmetic-only — same call as P2.2/P3.2/P3.4). **Only non-P item left: P3.4 library slug NFD-vs-NFKD (URL-changing, user decision).**

**Commits on `main`:** `7b8b7b3` P1+P2, `59a09ee` P2.14, `be2e4d1` P3.1, `c0de36e` P3.7, `0f6d012` P3.3, `0ece492` roadmap, `9892101` P4, `7161d59` P5. Byte-compile clean, `.elc` kept removed. User's unrelated dirty WIP untouched. **Roadmap fully closed** (P3.4 = deferred user decision).

**Gotcha:** garden/library emit frontmatter key `last_modified:`; essays/poetry emit `lastmod:` (research too) — handlers persist via `(or (alist-get 'lastmod ...) (alist-get 'last_modified ...))`. Handler record-publish stubs in tests need `&rest _` to tolerate the new keyword.
