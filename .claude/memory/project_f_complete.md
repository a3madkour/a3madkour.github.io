---
name: f-complete
description: "F citation pipeline — shipped + Task 18 spot-check 2026-06-01. Org-side authoring path the site's Citation export shortcode was waiting on (since 2026-05-14). Two new elisp modules: `a3madkour-publish-bib.el` (parser + citar adapter + BBT JSON-RPC) + `a3madkour-publish-citations.el` (rewriter + accumulator + emit-yaml + M-x a3-sync-citations). Plugs into B.1.1's `rewrite-to-tmp-file` chokepoint → garden/essays/research handlers inherit cite rewriting for free. 478 ert + 36 integration (1 new pass + 2 manual-skip scaffolds). Real-corpus spot-check shipped 4 in-slice fixes."
metadata:
  node_type: memory
  type: project
---

**Shipped (code-complete 2026-06-01):** F — citation pipeline per `docs/superpowers/specs/2026-06-01-phase-3-f-citation-pipeline-design.md` + `docs/superpowers/plans/2026-06-01-phase-3-f-citation-pipeline.md`. Subagent-driven across 18 tasks + 4 in-slice fix-up commits from Task 18 spot-check.

## What ships in F

### Dotfiles (`~/dotfiles/emacs-configs/custom/lisp/`)

**New modules** (both ~200-300 LoC + ert sibling):
- `a3madkour-publish-bib.el` + `-test.el` — bib resolver behind one `bib-resolve` interface. Three engines:
  - **Parser path:** stdlib elisp `.bib` reader; populates per-run cache via `parse-file`. Handles nested braces, multi-author splitting on ` and `, `@string`/`@preamble` skip + substitution, error paths.
  - **Citar path:** thin wrapper around `citar-get-entry` + `citar-get-value` when `(featurep 'citar)` AND its API is bound. Plist parity asserted against parser-path via dedicated ert.
  - **BBT JSON-RPC** (`refresh-from-zotero`, sync-only): `POST item.export` against `http://localhost:23119/better-bibtex/json-rpc` with 2s timeout. On 2xx + valid JSON → atomic-write the `.bib`; on any failure → warn and continue with on-disk.
  - `normalize-entry` maps raw alist → schema plist with venue chain (journaltitle → booktitle → publisher → eventtitle → **eprinttype (eprintclass)** ← spot-check finding for arXiv preprints), type enum (unknown → "misc"), brace-strip on titles, empty-author fallback to `'("Unknown")`.

- `a3madkour-publish-citations.el` + `-test.el` — orchestrator:
  - `rewrite-cite-keys-in-buffer` (Task 9) — pre-export rewriter. Walks `org-element-parse-buffer` for `'citation` elements, validates each key resolves, fails fast on unknown keys / style overrides (`[cite/text:...]`) / prefix-suffix forms, emits `@@hugo:{{< cite "k" >}}{{< cite "k2" >}}@@` (multi-cite = adjacent shortcodes), strips `#+print_bibliography:` directives. **Two-pass implementation** (forward-validate, reverse-rewrite) — necessary so first-error-wins semantics work; back-to-front single pass would surface later cites' errors first.
  - `cite--lookup-notes-ref` (Task 10) — auto-detect: probe `~/org/notes/ref-notes/<KEY>.org` → require `HUGO_PUBLISH=t` AND `HUGO_SECTION=garden` → derive slug (HUGO_SLUG override else file-name-base downcased) → check manifest for `/garden/<slug>/`. **Manifest read with disk fallback** (post-spot-check fix; see below).
  - `emit-yaml` (Task 11) — `merge` mode (default, per-publish) preserves existing untouched keys; `replace` mode (sync only) purges. Atomic `.tmp + rename`. Sorted output for deterministic diffs. Idempotent.
  - `a3-sync-citations` (Task 15) — interactive command + shell `--sync-citations` flag. Refreshes `.bib` via BBT (best-effort), walks manifest-published `.org` sources, re-resolves every key, writes yaml in replace mode.

**Modified modules:**
- `a3madkour-publish-rewrite.el:381` — `rewrite-to-tmp-file` (the chokepoint B.1.1 built) gains a 6-line lazy-require + call after the existing link rewriter. Single plug; garden/essays/research handlers inherit cite rewriting for free.
- `a3madkour-publish.el` (begin-publish) — primes the bib parser cache at publish start (parallels B.0's accumulator init); critical because no other code path primes the cache, so `bib-resolve` would otherwise miss every key.
- `a3madkour-publish-living.el` + `-deliberate.el` — tail-call `emit-yaml :mode 'merge` after `finish-publish`.
- `a3-pub.sh` — `--sync-citations` intercept + `-l` lines for both F modules in living/deliberate/sync exec blocks + `A3_PUB_BIB_PATH` env-var bridge (`--eval "(when (getenv ...) (setq a3madkour-pub-bib/library-path ...))"`).

### Site (`~/Sync/Workspace/a3madkour.github.io/`)

- `tools/check_citations.py` — KEY_RE loosened from `^[a-z0-9][a-z0-9-]*$` to `^[A-Za-z0-9][A-Za-z0-9-]*$` (Task 1). BBT camelCase keys now accepted. Underscores + leading hyphens still rejected.
- `tools/fixtures/citations/library.bib` — 10 hand-written BBT-keyed entries: 8 type-coverage + 1 no-author fallback + 1 `dummyKey2024` for the cite-with-ref-note integration path.
- `tools/fixtures/citations/{example-cite-one,example-cite-two}.org` + `ref-notes/dummyKey2024.org` — fixture corpus for `TestCitationRoundtrip`.
- `tools/test_check_citations.py` — +3 tests for camelCase accept / underscore reject / leading-hyphen reject.
- `tools/test_publish_integration.py` — +1 PASS (`TestCitationRoundtrip`) + 2 manual-gated `@unittest.skip` scaffolds (`TestSyncPurges`, `TestHugoRendersCitedEssay` — both need either roam-indexed fixtures or live-tree mutation; documented for F.x follow-ups).

## Test deltas

- ert: 398 → **478** (+80; 1 pre-existing skip).
- Python integration: 33 → **34** (+1 PASS + 2 SKIP scaffolds).
- check_citations: 20 → **23** (+3 KEY_RE tests).

## Task 18 spot-check — 4 fix-up commits

Validated against the author's real `~/org/notes/ref-notes/library.bib` (15.6k entries) by publishing `~/org/essays/example-one.org` with a real cite. Each finding shipped a fix:

1. **arXiv preprints lacked a venue field.** BBT `@online` entries carry `eprinttype = {arXiv}` + `eprintclass = {cs.CL}` but no `journaltitle/booktitle/publisher/eventtitle`. Extended `normalize-venue` to fall back to `eprinttype (eprintclass)` → renders `venue: "arXiv (cs.CL)"`. See [[reference-arxiv-venue-chain]].

2. **BBT case-protection braces rendered literally.** Titles like `R-{{WoM}}: {{Retrieval-augmented World Model For Computer-use Agents}}` showed those `{{ }}` in HTML. Strip ALL `{`/`}` chars from titles in normalize-entry. See [[reference-bbt-brace-protection]].

3. **`notes_ref` auto-detect silently failed for real ref-notes.** `finish-publish` clears `a3madkour-pub--manifest-snapshot` at its bottom (per its own docstring at publish.el:182-183), but Task 13 calls emit-yaml AFTER finish-publish. By the time lookup-notes-ref read the snapshot, it was nil → no notes_ref ever. Added disk fallback. See [[reference-finish-publish-snapshot-lifecycle]].

4. **Interactive M-x lacked begin-publish init.** Shell wrapper invoked `begin-publish` before `a3-sync-citations`; interactive M-x did not, so the manifest snapshot was empty and no sources got walked. Lazy-require + auto-call begin-publish at the top of `a3-sync-citations`.

## Plug architecture

```
begin-publish
├── reset publish-run-accumulator (B.0)
├── reset cite accumulator (F Task 13 — added in publish.el during T13 implementation)
├── prime bib parser cache (F Task 16 — added in publish.el during T16 spot-check)
├── snapshot manifest into a3madkour-pub--manifest-snapshot (B.0)
└── org-roam-db-sync (if dir exists)

rewrite-to-tmp-file (per source file)
├── rewrite-buffer-links (B.1.1 — id-links → web URLs)
└── rewrite-cite-keys-in-buffer (F Task 12 — [cite:@k] → @@hugo:{{<cite>}}@@)

ox-hugo export → markdown body (has_citations scan picks up shortcodes)

finish-publish
├── slug-shift (step A)
├── orphan-sweep (step B)
├── write manifest yaml (step C)
└── CLEAR manifest snapshot ← surprise gotcha for any post-finish caller

emit-yaml (Task 13 tail call, AFTER finish-publish)
├── per accumulated cite-key: bib-resolve → validate → lookup-notes-ref
│      (lookup reads snapshot OR falls back to disk read since snapshot was just cleared)
├── render entries with notes_ref injection
├── merge with existing yaml (or replace if :mode 'replace)
└── atomic write
```

## Known follow-ups (F.x)

Surfaced but not in-slice scope:

- **B.4 orphan-sweep over-deletion** (NOT an F issue): during the spot-check, `--publish-deliberate ~/org/essays/example-one.org` deleted `content/essays/example-{two,three,four}/index.md` even though those `.org` sources exist in `~/org/essays/`. `:scope 'deliberate` finish-publish was supposed to operate only on the published source. **File against B.4 follow-up.**
- **Title quality on ref-notes promoted to garden:** ref-notes have a `#+title:` that's the full bibliographic header (`Mei, Kai and Guo, Jiang and ..., R-WoM: ...`) — clunky as a garden tile title. Future F.x or B.1.x slice could add a `HUGO_TITLE` override convention or auto-derive a short title from the cite key.
- **`TestSyncPurges` + `TestHugoRendersCitedEssay`** are integration scaffolds gated with `@unittest.skip`. They need either roam-indexed fixtures (TestSyncPurges) or live-tree mutation (TestHugoRenders); promote both to runnable in a follow-up that adds a self-contained roam test harness.
- **Performance regression test** against the full 15.6k-entry library.bib — currently parser-handles-real-fixture only checks the fixture .bib (10 entries). If author notices publish slowdown, gate on per-publish parse time.
- **Style-override / prefix / suffix org-cite syntax** (`[cite/text:@k]`, `[cite:see @k p.5]`) — V1 fails fast. F.2 follow-up.
- **`#+print_bibliography:` positional rendering** — V1 strips the directive; site auto-renders refs at body end. F.3 follow-up.

## Why this slice mattered

The site has had the cite shortcode + modal + references partial since Citation export slice (2026-05-14), all rendering from `data/citations.yaml`. But that yaml was a hand-written fixture; real authoring required org-side support. F closes the loop: write `[cite:@key]` in org, publish, the right yaml entry appears. The shortcode signature didn't change; only the data source went from fixture to real.

## Commits

**Dotfiles** (`735d05a` baseline → `116950b` tip): 16 commits.
- Tasks 3–15 implementation (13 commits).
- Task 16 prep (env-var bridge + begin-publish bib priming): `72b8f5a`.
- Task 18 spot-check carry-forwards (venue chain + interactive sync init): `303c7ca`.
- Task 18 follow-ups (brace strip + manifest fallback + fixture-count test fix): `116950b`.

**Site** (`6143172` baseline → merge commit on master): 4 worktree commits (Tasks 1, 2, 16, 17) plus the `--no-ff` merge.

## State at end of session

- Dev server running at http://localhost:1313 (PID 83366); spot-checked clean.
- Local CI passes through hugo prod build + post-build linters; LHCI step skipped (no chromium in env, per [[reference-ci-local-lhci-deps]]).
- Main checkout has uncommitted publish artifacts ready to commit: `data/citations.yaml`, `data/url-history.yaml`, `content/essays/example-one/index.md`, `content/garden/mei-r-wom-2026/` (the new garden bundle from `--publish-living`).
- Pre-existing unpushed master commits (3): the F spec, plan, LHCI stub.
- Author requested NOT to push this session — push deferred to next.
