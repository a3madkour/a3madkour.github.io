---
name: b3-complete
description: "B.3 research handler — shipped 2026-05-31. Third per-content-type publisher; per-page Hugo bundles for both research cascade types (themes + questions sharing one handler). 353 ert tests (+44 from B.2 baseline 309) + 26 Python integration fixtures (+7 from B.2 baseline 19). Stub spot-check replaced 9 hand-authored fixtures with 6 B-emitted bundles from ~/org/notes/research-{themes,questions}-example-*.org. Closes B.1.x #10 (fs-mtime cascade fallback) + parent B spec §3/§7 wording gaps (#+HUGO_SECTION slash-form + #+HUGO_DESCRIPTION + source_stream). Linter accepts B-emitted author + draft fields."
metadata: 
  node_type: memory
  type: project
  originSessionId: c1b06244-57c3-4b45-89d3-e1e2df8781c2
---

**Shipped (code-complete 2026-05-31):** B.3 — research per-content-type publisher per `docs/superpowers/plans/2026-05-30-phase-3-b-3-research-handler.md` and `docs/superpowers/specs/2026-05-30-phase-3-b-3-research-handler-design.md`. Subagent-driven across 17 tasks (T9 + T10 merged into one commit by implementer).

## What ships in B.3

### Dotfiles (`~/dotfiles/emacs-configs/custom/lisp/`)

**New module:**
- `a3madkour-publish-research.el` + `-test.el` — `publish-research-file` end-to-end. Two cascade types share one handler; internal branch on `#+HUGO_SECTION:` selects per-type normalizer + question-only outputs parse/strip. New helpers: `--parse-outputs-table` (org table → list of `(:kind :title :url :year)` plists), `--strip-outputs-subtree` (pure-functional org-text mutation), `--rewrite-to-tmp-file` (private near-copy of garden's — extract-to-shared logged as B.3.x), `--render-yaml-value` / `--render-outputs-yaml` / `--render-frontmatter` / `--inject-outputs` (frontmatter rendering with `outputs:` injection post-normalize), `--section-to-normalize-sym` (slash→hyphen for the per-section dispatch).

**Modified modules:**
- `a3madkour-publish-history.el` — new `--filesystem-mtime-of-file` helper (closes B.1.x #10).
- `a3madkour-publish-frontmatter.el` — `--last-modified-cascade` (5-step: drawer → keyword → git-mtime → fs-mtime → today, with empty-string fallthrough); `--read-org-keyword` (delegates to `a3madkour-pub-keywords/extract`); `--inject-description` (reads `#+HUGO_DESCRIPTION:` from source, override-wins); `--research-normalize-common` (shared cross-cutting fields); `--normalize-research-theme` (status enum WARN + weight coerce + forbidden-keys drop); `--normalize-research-question` (status WARN + weight coerce + slug-list parses for supporting_notes + related_essays + outputs key drop); `--parse-slug-list` (generic space-delimited → list); `--coerce-weight` (octal-safe float-trip + nil-file guard + drop key on non-numeric); `--research-statuses` / `--theme-forbidden` constants. Dispatch in `normalize` gains `'research-themes` + `'research-questions` clauses. `--known-sections` updated to plural symbols.
- `a3madkour-publish-living.el` — `with-eval-after-load` registers both `("research/themes" . publish-research-file)` + `("research/questions" . publish-research-file)`.
- `a3-pub.sh` — `-l a3madkour-publish-research` added to the three publish-side intercepts.

### Site repo

- `tools/test_publish_integration.py` — `_write_research_source` helper + `TestResearchPublishLiving` class with 7 fixtures: theme-publish-once, question-publish-once-with-outputs, idempotent, slug-shift, cross-ref-WARN-tolerance, removed-unpublish, yaml-passes-linters. Helper escapes `|` in outputs table cells (`\vert{}`). `_publish_living_impl` gained `-l a3madkour-publish-research`.
- `tools/check_research_fixtures.py` — `author` + `draft` added to OPTIONAL on both theme + question (B emits both; was a linter gap).
- `content/research/themes/` + `content/research/questions/` — 9 hand-authored fixtures replaced by 6 B-emitted stub bundles (`example-theme-{one,two}`, `example-question-{one,two,three,four}`).
- `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` — §3 research row + §7 common table + §9 research subsection amended (slash-form section keyword, `source_stream`, `#+HUGO_DESCRIPTION:`, `* Outputs` table contract pointer).
- `docs/superpowers/specs/2026-05-30-phase-3-b-3-research-handler-design.md` + `docs/superpowers/plans/2026-05-30-phase-3-b-3-research-handler.md` — B.3 spec + plan.
- `CLAUDE.md` — status pointer updated.

## Test counts at slice end

- **ert: 353 total** (B.2 baseline 309 + 44 new across history/frontmatter/research/living). All passing.
- **Python integration fixtures: 26 total** (B.2 baseline 19 + 7 new TestResearchPublishLiving fixtures). All passing.
- **`tools/ci-local.sh`**: passed end-to-end on Hugo 0.162.1.
- **Site linters** (`check_research_fixtures.py` + `check_research_links.py`): green against B-emitted content.

## Commits

Dotfiles (`~/dotfiles`, branch `main`, 14 commits `23fc5d7..71fabe3`):
- `705c211` last_modified cascade + fs-mtime fallback (T1)
- `8708c57` empty-string cascade fallthrough + plural research sections (T1 fix)
- `14a9a86` #+HUGO_DESCRIPTION: keyword support (T2)
- `32a4cc2` delegate --read-org-keyword to keywords/extract (T2 fix)
- `a80c8fd` scaffold a3madkour-publish-research module + wrapper -l lines (T3)
- `0a2bde9` research-normalize-common shared helper (T4)
- `a01cb95` research-normalize-common drops empty tags + docstring note (T4 fix)
- `0871ade` theme normalizer + per-section dispatch entry (T5)
- `46499bb` coerce-weight nil-file guard + drop nil weight key (T5 fix)
- `faa2768` question normalizer + per-section dispatch entry (T6)
- `885dbd8` theme status WARN nil-guard + slug-list/outputs docs (T6 polish)
- `7d6d27a` --parse-outputs-table helper (T7)
- `e3818b4` --strip-outputs-subtree helper (T8)
- `e160267` publish-research-file end-to-end (T9 + T10 — handler registration rolled in)
- `71fabe3` remove dead render-yaml-scalar + guard list branch (T9 polish)

Site repo (`master`, 5 commits `c316723..bba6066`):
- `b7b4f9f` design(b-3) spec
- `c316723` plan(b-3) implementation plan
- `6aea649` scaffold integration-test loader (T3)
- `4d760dc` integration fixture — theme publish-once (T11)
- `f711228` integration fixture — question publish-once + helper polish (T12)
- `944f981` integration fixtures — idempotent + slug-shift + cross-ref-WARN + removed-unpublish + linter parity (T13-T16)
- `bba6066` stub fixture handover + spec amendments + CLAUDE.md update + linter author/draft (T17)

All pushed to origin: PENDING — user confirmation. Dotfiles + site both have unpushed commits at end of slice.

## Architectural decisions worth recording

1. **`#+HUGO_SECTION:` source value is slash-form**, not dash-form. T11 (first integration fixture) caught this — elisp `a3madkour-pub/sections` uses slash-form path strings (`"research/themes"`, `"research/questions"`), so the org keyword must match. The brainstorm + initial plan spec'd dash-form; T17 spec amendments corrected both B.3 spec §4 + parent B spec §3 to slash-form.

2. **`#+HUGO_SECTION:` value vs frontmatter normalize dispatch symbol** — slash-form on the source side (`research/themes`), hyphen-form on the normalize dispatch side (`'research-themes`). T9's `--section-to-normalize-sym` does the slash→hyphen conversion (replace `/` with `-` and intern). The two forms intentionally differ: slash for filesystem-path-like dispatch keys, hyphen for elisp section symbols.

3. **`outputs` two-phase handling.** Parse from the ORIGINAL source AST (so the table is still present), then strip the `* Outputs` subtree from the tmp file the ox-hugo exporter sees. Outputs-as-frontmatter is injected post-normalize via `--inject-outputs` so the alist serializer doesn't see structured data through the general string path. The general `--render-yaml-value` list branch now errors on non-string elements as a guard.

4. **`last_modified` cascade** is shared with garden (drawer → keyword → git → fs → today). Library still has its own 2-step `or`; logged as B.3.x follow-up.

5. **`begin-publish`/`finish-publish` lifecycle wrapping** is required in e2e tests so the manifest snapshot defvar doesn't leak. Garden tests had the same shape; B.3 added an inline comment on the first e2e test to document it for future test writers.

6. **Linter scope extension** (`author` + `draft` accepted as OPTIONAL on themes + questions): B-emitted bundles include both fields (ox-hugo adds author; publisher emits explicit draft: false). Hand-authored fixtures predated this. The linter now accepts both shapes; the existing sibling tests for `check_research_fixtures.py` still pass.

## Spot-check status (Task 17)

**Stub spot-check complete 2026-05-31** — 6 hand-written research stubs in `~/org/notes/` → publish-living → 9 fixtures replaced by 6 B-emitted bundles. Three linter fixes applied to stub content during the spot-check:
- `example-theme-one` `garden_topic_ref` changed from `bayesian-statistics` (no topic_map) → `procedural-narrative` (has topic_map; resolves cleanly).
- `example-question-three` `parent_question` removed (linker rejects cross-theme parent chains).
- `works` + `streams` fixtures updated for cross-link consistency with new question slugs.

Final ci-local: all linters pass, 67 pages audited.

**Real-content spot-check still pending.** User writes real themes + questions in `~/org/notes/research-{themes,questions}-<slug>.org` when ready; same pattern as B.2's pending real-corpus pass.

## Known issues / B.3.x follow-ups (logged, not blocking)

1. **`--coerce-year` has an unused `_file` arg** (`a3madkour-publish-research.el`). Either drop it (YAGNI) or add a WARN for malformed years. T7 review minor finding.
2. **`--rewrite-to-tmp-file` is duplicated** between garden + research. Extract to a shared `a3madkour-publish-io` module (or similar) before B.4 essays land — third copy would be unjustified. T9 review minor finding.
3. **Library's `last_modified` cascade not upgraded** — still uses 2-step `or`. Library handler should switch to `--last-modified-cascade`. T1 carry-forward.
4. **`--render-yaml-value` cell-plain-text assumption** — the `--table-rows` cell unwrap uses `org-element-interpret-data` for non-string cells, which would emit `*bold*` or `[[https://...]]` link syntax verbatim. Currently safe (outputs cells are plain text per spec), but undocumented. T7 review minor finding.
5. **Dotfiles ergonomics for outputs table** (new follow-up #13): interactive helpers `a3-research-insert-outputs-template` + `a3-research-add-output`. Lives in the existing [[emacs-publish-helpers-followup]] bucket.
6. **Empty `outputs:` after all-unknown-kind rows** returns nil (same as no heading). T7 review minor — Hugo template would treat the same, but semantics conflate two distinct cases. Defer.
7. **Outputs table parsing assumes flat `* Outputs` heading** — nested or wrapped tables (inside a quote block, etc.) won't be found. Spec says "directly under the heading" — current behavior matches. Edge case noted in T7 review.

## Lessons logged (cross-session)

- `#+HUGO_SECTION:` is slash-form for all multi-level sections. Library uses single-level (`library-reading` not `library/reading`); research is the first multi-level. Future per-content-type handlers (essays, works, streams, about) need to follow the slash-form convention if multi-level.
- `Path(__file__).resolve()` pierces symlinks. Linter-parity integration tests must COPY linters into the tmp site (not symlink) so `__file__` resolves to a path inside the tmp tree.
- B-emitted research bundles emit `author` (ox-hugo) + `draft: false` (publisher). Hand-authored fixtures don't. Site linters need to accept both shapes during transition.

## Next slice: B.4 (essays handler)

Per design spec §12 slice ordering: B.1 → B.1.1 → B.2 → **B.3** → B.4 (essays) → B.5 (works) → B.6 (streams) → B.7 (about) → F → C → D → E. Essays are the most contractually rich per-content-type handler — frontmatter has 18+ fields including `has_*` body-content detection (sidenotes, citations, footnotes, math, widgets, video-sync). First publish-deliberate slice (essays are per-post, not living set). See [[next-slice]].

## How to start the next session

Read site CLAUDE.md + this file + [[b2-complete]] (for the per-medium variance pattern, though essays use per-page-bundle like garden + research) + parent B spec §7 essay-specific subsection + CLAUDE.md essay-frontmatter contract. Then `superpowers:brainstorming` for B.4 — the `has_*` detection contract has some novelty (scan post-export markdown vs. raw source).

## Cross-references

- Parent spec: `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md`
- B.3 spec: `docs/superpowers/specs/2026-05-30-phase-3-b-3-research-handler-design.md`
- B.3 plan: `docs/superpowers/plans/2026-05-30-phase-3-b-3-research-handler.md`
- Prior slice: [[b2-complete]]
- Decomposition: [[phase-3-decomposition]]
- Lessons referenced: [[goldmark-unsafe-for-ox-hugo-html]] (site-wide; research bodies exercise the @@html: flow), [[hugo-int-octal-gotcha]] (weight + year coercion), [[plan-wrapper-script-updates]] (a3-pub.sh -l line in the scaffold task), [[verify-before-merge]] (dev-server spot-check before push), [[filler-text-only]] (Example N + lorem ipsum stubs).
