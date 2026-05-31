# Phase 3 sub-project B, slice B.3 — research handler design

**Status:** design (brainstormed 2026-05-30)
**Parent spec:** `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` (§9 sketches the research pipeline; this slice spec refines it).
**Position:** B.2 (shipped 2026-05-29/30) → **B.3** → B.4 (essays).
**Prior slice memories:** [[b2-complete]] (B.2 — library), [[b1-complete]] (B.1 + B.1.1 — garden handler + pre-export id-link rewriter), [[b0-complete]] (shared infra), [[goldmark-unsafe-for-ox-hugo-html]] (sitewide Hugo config dependency), [[plan-wrapper-script-updates]] (wrapper-script gotcha).

---

## 1 — Goals

Implement the research publisher. Research is the first per-page Hugo bundle handler with **two cascade types sharing one section path tree**: themes (`content/research/themes/<slug>/index.md`) and questions (`content/research/questions/<slug>/index.md`). Both emit page bundles like garden; both share ~80% of the pipeline (ox-hugo export, link-rewrite, asset-copy, write-bundle, record-publish). The handler exposes one entry function that branches on `#+HUGO_SECTION:` only where the contracts genuinely diverge: per-type frontmatter normalize, and the question-only `outputs:` field.

Research is the third living section to ship. By the end of B.3:

- `~/org/notes/research-themes-<slug>.org` + `~/org/notes/research-questions-<slug>.org` files annotated with `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: research/themes` / `research/questions` publish end-to-end via `a3-pub.sh --publish-living`.
- `content/research/{themes,questions}/<slug>/index.md` bundles regenerated deterministically; the existing 9 research fixtures are replaced by stub B-emitted bundles in the Task 10 spot-check.
- Both research linters (`check_research_fixtures.py` + `check_research_links.py`) accept B-emitted output.
- Idempotent re-run produces zero file diffs.

## 2 — Non-goals (deferred or out of scope)

- **Real-content authoring.** Mirrors B.2 — stub spot-check ships; real-corpus authoring is a B.3.x gate on author writing real themes/questions, follow-up #14 (§11).
- **Dotfiles ergonomics for populating the outputs table.** Interactive helpers (template insertion + add-output prompt) belong in the existing `[[emacs-publish-helpers-followup]]` bucket; logged here as follow-up #13 (§11).
- **`weight` uniqueness validation.** Site linter (`tools/check_research_fixtures.py:132 validate_unique_theme_weights`) is authoritative. B emits whatever's authored; conflicts surface as CI failures, not publish-time errors.
- **Cross-link hard-fail.** Following A.1's WARN-don't-fail discipline, broken refs emit WARNs at publish time and the publish proceeds. `check_research_links.py` is the hard gate at CI.
- **Per-section `_index.md` regeneration.** Section-index pages stay hand-authored; the publisher only writes per-item bundles.
- **About Now widget hook.** Out of scope per parent §2.

## 3 — Architecture

One new elisp module `a3madkour-publish-research.el` (+ `-test.el` sibling) under `~/dotfiles/emacs-configs/custom/lisp/`. The module exports one entry-point `publish-research-file (file)` and registers two entries in `a3madkour-publish-living--handlers`:

```elisp
((cons "research/themes"    'a3madkour-pub-research/publish-research-file)
 (cons "research/questions" 'a3madkour-pub-research/publish-research-file))
```

(Slash-form keys per [[b2-complete]] architectural decision 1.)

Inside `publish-research-file`, the dispatch on cascade type is a single branch read from the source's `#+HUGO_SECTION:` keyword:

```
publish-research-file (file):
  exported     = export-file(file)                          ; ox-hugo invoke
  cascade-type = exported.frontmatter.section               ; 'research-themes | 'research-questions
  frontmatter  = normalize(cascade-type, exported.frontmatter, file)
                                                            ; per-type required/optional/forbidden
  outputs      = (if (eq cascade-type 'research-questions)
                    (parse-outputs-table file)
                  nil)
  body         = strip-outputs-subtree(exported.body)       ; questions only; no-op for themes
  body         = rewrite-buffer-links(body, file)           ; B.1.1's @@html: substitution
  assets       = asset-validate-and-copy(file, bundle-dest) ; A.1.c
  write-if-different(bundle-dest / "index.md",
                     render(frontmatter + outputs, body))
  record-publish(file-id, new-url, 'live, ...)
```

`a3madkour-publish-frontmatter.el` gains two new per-section dispatch entries alongside the existing `'garden` and `'library-*` branches: `'research-themes` and `'research-questions`. A shared `--research--normalize-common` helper handles the cross-cutting fields (description, summary, source_stream, last_modified cascade, filter-editorial-tags, draft passthrough). Per-type sub-normalizers add the type-specific fields.

`a3-pub.sh` plumbs `-l a3madkour-publish-research` into the three publish-side intercepts (publish-living, publish-deliberate, default-exec), per [[plan-wrapper-script-updates]].

## 4 — Source layout

```
~/org/notes/research-themes-<slug>.org        → content/research/themes/<slug>/index.md
~/org/notes/research-questions-<slug>.org     → content/research/questions/<slug>/index.md
```

Filename prefix mirrors `#+HUGO_SECTION:` value 1:1. Walker stays flat — no recursion needed; matches garden + library conventions.

Per-file required org keywords:

```org
#+title: <title>
#+HUGO_PUBLISH: t
#+HUGO_SECTION: research/themes        ; or research/questions
#+HUGO_DESCRIPTION: <one-sentence description>
#+HUGO_STATUS: active                  ; active | dormant | answered
#+filetags: :tag1:tag2:
```

Slug derivation: B.2's `--title-to-slug` produces the same slug whether the title contains punctuation (`?` in question titles is common) or not. Same helper, no changes.

## 5 — Source → frontmatter mapping

### Common across both cascade types

| Hugo field | Org source | Notes |
|---|---|---|
| `title` | `#+title` | ox-hugo pass-through |
| `draft` | `#+HUGO_DRAFT: t` | ox-hugo pass-through |
| `last_modified` | cascade — see §8 | new `--filesystem-mtime-of-file` fallback closes B.1.x #10 |
| `tags` | `#+filetags`, filtered through `--filter-editorial-tags` | B.2 helper strips TODO/NOEXPORT |
| `description` | **new** `#+HUGO_DESCRIPTION:` keyword | custom handler; same plumbing as `#+HUGO_GROWTH_STAGE:` |
| `summary` | `#+HUGO_SUMMARY:` | ox-hugo native; themes carry both `description` + `summary` as distinct fields |
| `source_stream` | `#+HUGO_SOURCE_STREAM:` | closes parent-B §7 doc gap |

### Theme-only (when `HUGO_SECTION = research/themes`)

| Field | Source | Notes |
|---|---|---|
| `status` | `#+HUGO_STATUS:` | enum `{active, dormant, answered}` per `tools/check_research_fixtures.py:19` |
| `weight` | `#+HUGO_WEIGHT:` | int (octal-safe cast per [[hugo-int-octal-gotcha]]); uniqueness enforced site-side |
| `garden_topic_ref` | `#+HUGO_GARDEN_TOPIC_REF:` | optional; broken-ref → WARN |

Forbidden on themes per linter (`THEME_FORBIDDEN`): `parent_question`, `theme`. B's normalizer drops these silently if author erroneously sets them.

### Question-only (when `HUGO_SECTION = research/questions`)

| Field | Source | Notes |
|---|---|---|
| `theme` | `#+HUGO_THEME:` | required; broken-ref → WARN |
| `parent_question` | `#+HUGO_PARENT_QUESTION:` | optional; broken-ref → WARN |
| `status` | `#+HUGO_STATUS:` | enum `{active, dormant, answered}` |
| `weight` | `#+HUGO_WEIGHT:` | int, optional |
| `started` | `#+HUGO_STARTED:` | date YYYY-MM-DD; passthrough as string |
| `supporting_notes` | `#+HUGO_SUPPORTING_NOTES:` | space-delimited slug list → YAML list |
| `related_essays` | `#+HUGO_RELATED_ESSAYS:` | space-delimited slug list → YAML list |
| `outputs` | `* Outputs` org table | see §6 |

## 6 — Outputs-table parse (questions only)

The handler scans the parsed org buffer (`org-element-parse-buffer 'greater-element`) for the first headline whose raw value is `Outputs` (case-insensitive match against `org-element-property :raw-value`). Under that headline, the first child element of type `table` is the outputs table.

### Required table shape

```org
* Outputs                                                  :outputs:
| kind  | title                | url                          | year |
|-------+----------------------+------------------------------+------|
| paper | Save States as Edits | https://example.com/paper    | 2024 |
| talk  | Save States as Edits | https://example.com/talk     | 2024 |
| code  | save-replay-tool     | https://github.com/example/x | 2024 |
```

- **Header row** must contain (case-insensitive) columns `kind`, `title`, `url`, `year`. Extra columns are ignored. Missing columns → WARN and skip the table.
- **Each data row** becomes a plist: `(:kind "paper" :title "Save States as Edits" :url "https://example.com/paper" :year 2024)`.
- `kind` is validated against `{paper, talk, code}` per `tools/check_research_fixtures.py:20`. Unknown kind → WARN and skip the row.
- `year` is coerced to int via `(string-to-number)` then re-cast through `(int (float ...))` per [[hugo-int-octal-gotcha]] (matters if author writes `:YEAR: 09` for some reason).
- `url` is emitted verbatim; no reachability check at publish time (CI is not the place to gate on remote 200s).
- `title` is emitted verbatim. Whitespace trimmed at cell boundaries.

### Body-strip pass

After parsing the outputs table to a plist list, the handler **removes the entire `* Outputs` subtree from the body buffer before ox-hugo runs**, using `org-element-extract-element` on the headline element (and `org-element-set-element` semantics, or simpler buffer-bounds-and-delete via `org-element-property :begin / :end`). This prevents the table from rendering as visible body content — the Hugo template at `layouts/research-question/single.html:163-166` already paints the Outputs section from frontmatter.

### Empty + malformed cases

- No `* Outputs` heading present → no `outputs:` key emitted (matches existing fixture `what-is-a-narrative-atom`).
- Heading present but no table under it → WARN, no `outputs:` key.
- Heading present with malformed header row → WARN, no `outputs:` key.
- Heading present with table containing only unknown-kind rows → `outputs: []` (empty list) is **not** emitted; treated same as malformed.

### Order preservation

Table-row order = emitted list order. The Hugo template controls display order (likely newest-year-first) independently.

## 7 — Cross-link emission + WARN discipline

B.3 emits raw frontmatter slugs as-authored. For each of `theme` / `parent_question` / `garden_topic_ref` / `supporting_notes` / `related_essays` / `source_stream`:

1. Resolve the slug via A.1's `published-p`.
2. If `published-p` returns `'live` → emit verbatim, no WARN.
3. If `'private` or `nil` (unpublished / unknown) → emit verbatim, emit one WARN line with the source file + field + slug.

The site-side linter `check_research_links.py` is the hard CI gate. B's role is to surface issues early at publish time so the author can fix in the source.

Matches the link-rewrite WARN-don't-fail discipline B.1.1 already exercises for inline body links ([[goldmark-unsafe-for-ox-hugo-html]] + B.1.1 round-3 spot-check).

## 8 — last_modified cascade (closes B.1.x #10)

B.1's garden normalizer derives `last_modified` from a two-step cascade: `#+HUGO_LASTMOD:` keyword → git-mtime (B.2's `--git-mtime-of-file`). When neither produces a value (file is not committed yet, and there's no explicit override), `last_modified` stays unpopulated and the linter rejects the bundle. This bit B.2 spot-check (Task 17) hard because `~/org/notes/` isn't git-tracked, so every stub got `last_modified` unpopulated.

B.3 ships a new helper `a3madkour-pub-history/--filesystem-mtime-of-file` and extends the cascade:

```
:LAST_MODIFIED: drawer entry   →  authoritative if present
#+HUGO_LASTMOD: keyword         →  ox-hugo native
--git-mtime-of-file (B.2)       →  for committed files
--filesystem-mtime-of-file (B.3) →  new — file's mtime, formatted YYYY-MM-DD
today                            →  ultimate fallback
```

Wired into BOTH garden + research normalizers (the helper change is in shared `a3madkour-publish-frontmatter.el`, so all section normalizers pick it up).

The fs-mtime fallback is "best-effort idempotence": editor saves with no content change will bump mtime and produce a publish diff. Workaround per author: explicit `:LAST_MODIFIED:` drawer or `#+HUGO_LASTMOD:` keyword. The cascade order makes both overrides easy.

## 9 — Slice scope (tasks, tests)

### Task sketch

The implementation plan will turn these into explicit numbered tasks. Sketch:

1. `--filesystem-mtime-of-file` helper in `a3madkour-publish-history.el` (closes B.1.x #10). Cascade extension in `a3madkour-publish-frontmatter.el`. Garden gets the upgrade for free.
2. `#+HUGO_DESCRIPTION:` keyword support in `a3madkour-publish-frontmatter.el` (or `a3madkour-publish-export.el`, wherever HUGO_GROWTH_STAGE is read — verify in dotfiles before plan).
3. `a3madkour-publish-frontmatter.el` — register `'research-themes` + `'research-questions` per-section normalizers; shared `--research--normalize-common` helper.
4. `a3madkour-publish-research.el` scaffold + `--parse-outputs-table` helper + ert tests for the parser in isolation (empty / well-formed / missing-cols / unknown-kind row / malformed year / case-insensitive heading match).
5. `--strip-outputs-subtree` helper + ert tests (pure-buffer mutation; verify body length, verify other content untouched, no-op when no `* Outputs` heading).
6. `publish-research-file` end-to-end. Pipeline per §3.
7. Register both dispatch alist entries in `a3madkour-publish-living.el` with `with-eval-after-load`.
8. `a3-pub.sh` — `-l a3madkour-publish-research` in the three publish-side intercepts.
9. Site-side integration fixtures — `TestResearchPublishLiving` in `tools/test_publish_integration.py`.
10. Stub spot-check (see §10).

### Integration test coverage

`tools/test_publish_integration.py` gains `TestResearchPublishLiving` with:

- `test_research_theme_publish_once` — single theme emits clean bundle, passes `check_research_fixtures.run()`.
- `test_research_question_publish_once` — single question with outputs table + supporting_notes + related_essays emits clean.
- `test_research_publish_idempotent` — second run produces zero diffs.
- `test_research_question_slug_shift` — title change → manifest auto-alias + old bundle gone.
- `test_research_cross_ref_warn` — question with `theme: nonexistent` + `supporting_notes: [private-note]` emits WARNs, doesn't fail; emitted YAML still passes `check_research_fixtures.run()` (linker resolution is `check_research_links.py`'s job, separate gate).
- `test_research_publish_removed_unpublish` — question removed from source → bundle deleted, manifest marks removed.

Plus one fs-mtime regression fixture (under whichever Test class fits, possibly a new `TestLastModifiedCascade`).

### Estimated test counts at slice end

- ert: ~339 total (309 baseline + ~30 new across research handler, outputs-table parser, subtree-stripper, research-frontmatter normalizer, fs-mtime helper).
- Python integration: ~25 total (19 baseline + ~5-6 new TestResearchPublishLiving fixtures + ~1 fs-mtime regression).

## 10 — Stub spot-check (Task 17)

**Status: COMPLETE** (2026-05-31). Mirrors B.2's stub spot-check pattern. Out-of-scope is real-corpus authoring (that's B.3.x).

1. Hand-write ~6 stub `.org` files in `~/org/notes/`:
   - `research-themes-example-theme-one.org` (full frontmatter, `garden_topic_ref: procedural-narrative`)
   - `research-themes-example-theme-two.org` (dormant, no garden_topic_ref)
   - `research-questions-example-question-one.org` (active, with supporting_notes + outputs table)
   - `research-questions-example-question-two.org` (dormant, supporting_notes only, no outputs)
   - `research-questions-example-question-three.org` (answered, full outputs table, no parent_question)
   - `research-questions-example-question-four.org` (sub-question of example-question-three; chains parent_question within same theme)
2. Each gets `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: research/themes` or `research/questions` + `#+HUGO_DESCRIPTION:` + minimal "Example N. Lorem ipsum…" body.
3. Run `a3-pub.sh --publish-living`. Expected: 6 new bundles emitted; 9 existing fixtures removed via finish-publish's Step A.
4. Verify: `tools/ci-local.sh` green (both research linters + Hugo build + smoke + page-weight).
5. Inspect 1-2 emitted bundles by hand — frontmatter ordering, outputs table parsed correctly, body cleanly stripped of `* Outputs`.
6. Commit the swap: bundles + manifest update + this spec + plan.

**Spot-check findings logged:**
- `#+HUGO_SECTION:` value is slash-form (`research/themes`, `research/questions`), not dash-form — spec §4 updated.
- `garden_topic_ref` must point to a garden note with `topic_map:` (linter validates this); `bayesian-statistics` lacks it, swapped to `procedural-narrative`.
- `parent_question` must point to a question in the **same theme** (linter validates cross-theme chains); question-three's `parent_question` removed (both chains now intra-theme).
- Works fixture cross-refs (`research_questions`) and streams fixture `related_research` updated to new B-emitted slugs.

Stubs stay in place as the bootstrap corpus. Real-content authoring (B.3.x) replaces them later.

## 11 — Carry-forwards + follow-ups

### Closed by B.3

- **B.1.x #10** — fs-mtime fallback. Via Task 1's `--filesystem-mtime-of-file` helper + cascade extension. Both garden + research pick it up.
- **Parent B spec §3 wording** — section keyword form. Corrected to `#+HUGO_SECTION: research/themes` / `research/questions` (slash-form, matching dispatch-alist keys); parent B spec §3 updated. Note: `'research-themes` / `'research-questions` are internal elisp symbols for dispatch; the org keyword uses slash-form.
- **Parent B spec §7 gaps** — `source_stream` field documented for research; `#+HUGO_DESCRIPTION:` keyword documented; `* Outputs` table contract documented (this spec § 5–6 supersedes the parent's research mapping).
- **Parent B spec §12 open Q #5** — idempotency vs lastmod git-mtime. Cascade source-overrides → auto-derivation order makes both override paths cheap.

### Still open after B.3 (not in B.3 scope)

- **B.1.x #5** — `finish-publish` does not retry on `delete-bundle` `'failed`. Research exercises this path heavily (theme + question slug shifts will happen during normal editing). Flagging it as a B.3 risk: a wrong-path delete won't be retried and the manifest will silently mark removed. If Task 10 spot-check trips it we patch in-slice; otherwise it stays queued for a B.x or A.2.
- **B.2.x #2** — `--render-scalar` fallback `%S` hardening. Research likely emits more diverse strings than library (long descriptions with quotes/colons/commas/apostrophes in summaries). If Task 10 spot-check trips it, patch in-slice.
- **B.2.x #7** — cover-asset auto-extraction. Doesn't apply to research (no covers); library-only follow-up.

### New follow-ups B.3 logs

- **#13 — Dotfiles ergonomics: insert outputs-table template + add-output interactive command.** Two complementary helpers in the existing `[[emacs-publish-helpers-followup]]` bucket:
  - `a3-research-insert-outputs-template` — inserts `* Outputs :outputs:` heading + table header at point.
  - `a3-research-add-output` — prompts for kind/title/url/year, appends a row to the existing table (or scaffolds one if absent).
  No spec or plan until scheduled.
- **#14 — Real-corpus authoring (B.3.x gate).** Author writes real themes + questions in `~/org/notes/research-{themes,questions}-<slug>.org`, runs publish-living, swaps stubs for real bundles. Same shape as B.2's still-pending real-corpus pass.
- **Possible #15** — if the outputs-table parser turns out to want more flexibility (optional `notes`/`venue` columns), file a small follow-up rather than overdesigning B.3.

### Carry-forwards inherited site-wide (no change in B.3)

- `markup.goldmark.renderer.unsafe: true` (B.1.1) — required because research bodies will exercise the `@@html:` flow via link-rewrite (research notes cite garden notes heavily).
- Slash-form / string-keyed dispatch (B.2 architectural decision 1) — applied to both research keys.
- WARN-don't-fail discipline on broken cross-refs (A.1) — applied to all six research cross-link fields (§7).

## 12 — Glossary

- **cascade type** — `research-themes` or `research-questions`. Discriminator at the top of each org source file; routes the handler's internal branch for normalize + outputs.
- **outputs table** — first org table under the first `* Outputs` heading in a question source file. Parsed to `outputs:` YAML list-of-dicts; stripped from body before ox-hugo runs.
- **last_modified cascade** — drawer → keyword → git-mtime → fs-mtime → today, in that order. Garden + research share the cascade.
- **stub spot-check** — hand-written `Example N. Lorem ipsum…` source files used as a bootstrap corpus to verify the publisher end-to-end; persists until real authoring replaces them.

---

## Spec self-review checklist (per superpowers:brainstorming)

- [x] Placeholder scan — no TBDs; all behavior specified at a level the plan can act on.
- [x] Internal consistency — handler architecture (§3) matches frontmatter mapping (§5) matches task sketch (§9); cross-link discipline (§7) matches A.1 + B.1.1 precedent.
- [x] Scope check — single-slice scoped: one new module + one new keyword + one new helper + ~5 integration fixtures + spot-check. Within one writing-plans cycle.
- [x] Ambiguity check — outputs table required/optional columns enumerated; cascade type discriminator made explicit; section keyword form locked at plural; description source method locked.
- [x] Hard-constraint check — fixture content stays obviously-dummy (Example N, lorem ipsum) per [[filler-text-only]]; no AI text; no UI work in B.3 (publisher only); accessibility unchanged (CSS handles, B emits content).
