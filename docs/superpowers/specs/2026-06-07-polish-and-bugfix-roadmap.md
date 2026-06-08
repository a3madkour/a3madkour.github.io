# Polish + Bug-fix Roadmap — Tier Ordering

**Date:** 2026-06-07
**Status:** Active. Each tier maps to one or more future sessions. **Tiers 1, 4, 5, 6 closed; Tier 7 is trigger-gated and Tier 8 holds the large new scopes.** Tier 1 fully closed 2026-06-07; Tier 2.1 + 2.5 shipped, 2.2/2.3/2.4 trigger-gated; Tier 3 human-driven (manual QA); Tier 4 closed 2026-06-08; Tier 5 closed 2026-06-08 (5.1 + 5.2 shipped; preview-section deferred as 5.3 stub); Tier 6 closed-by-deferral 2026-06-08 (6.1 demoted back to the deferred-features registry — see CLOSED block below).

**Why this exists:** The Phase 3 publish-pipeline buildout (sub-projects A → B → F → C → D, all shipped) left a queue of correctness bugs, polish gaps, hygiene cleanups, tooling gaps, and queued small features. Rather than jump straight to sub-project E (explorables — the last Phase 3 piece), the author chose to clear the polish/bug-fix backlog first. This file documents that ordering so future sessions can pick up any tier cleanly without re-deriving the queue.

**Companions:**
- Deferred features (long-horizon, trigger-gated): [`2026-06-07-deferred-features-registry.md`](2026-06-07-deferred-features-registry.md).
- Parent design spec: [`2026-05-03-personal-site-design.md`](2026-05-03-personal-site-design.md) §14.

**Rules:**
- Tiers run in numbered order. Within a tier, items can fuse into a single commit when low-risk; correctness bugs get their own commits with named test coverage.
- Each tier is one or more sessions. Don't fuse tiers.
- Item status: ☐ open · ✓ shipped · ⊘ obsoleted. Mark shipped with a link to the `project_*_complete.md` memory file.
- Don't draft per-tier *plans* until the tier opens. Per [feedback-design-batch-no-plan-until-implement](https://example.invalid) — specs first, plan-per-slice when implementation begins.

---

## Tier 1 — Correctness bugs (data wrong or silently broken)

**Goal:** restore trust in the publish pipeline before piling new features on top. Several of these can hide in CI green because the test layer stubs around them.

| # | Item | Severity | Where to start |
|---|---|---|---|
| 1.1 | ✓ **`finish-publish` advances past failed `delete-bundle`.** Manifest gets marked `state: removed` even when on-disk delete failed silently (e.g. permission error, wrong content-dir computation). Next run sees "manifest already removed → no diff to act on" and the orphan persists. → [project-tier-1-1-complete](../../../.claude/memory/project_tier_1_1_complete.md) (shipped 2026-06-07, dotfiles `e50a037`) | High (data integrity) | `a3madkour-publish-unpublish.el` `--unpublish-delete-bundle` + caller in `finish-publish` Step A. Source: B.1 carry-forward #5 in [project-b1-complete](../../../.claude/memory/project_b1_complete.md). |
| 1.2 | ✓ **`--rewrite-file-link` parity with rewrite-asset-link.** Same architectural issue I fixed for figref this session: `[[file:other-essay.org]]` derives `source-file` via `--id-to-file` (DB lookup). When the source essay isn't in `org-roam-directory`, falls back to `default-directory` → silent breakage. → [project-tier-1-2-complete](../../../.claude/memory/project_tier_1_2_complete.md) (shipped 2026-06-07, dotfiles `27d157d`) | Medium (silent fallback) | `a3madkour-publish-rewrite.el:245` — mirror the fix from `1edd900`. Add a production-mirroring ert test (`--id-to-file` → nil). |
| 1.3 | ✓ **`TODO` filetag leaks into Hugo tags.** `#+filetags: :Foo:TODO:` round-trips `TODO` as a content tag. Observable on MAP bundle. → CLOSED retroactively in B.2 (`a3madkour-pub-frontmatter/filter-editorial-tags` wired into `--normalize-garden`; ert `garden-tags-strip-editorial`). Verified 2026-06-07 — no new fix needed. | Low (cosmetic) | Garden frontmatter normalizer in `a3madkour-publish-frontmatter.el`. Filter editorial tag values (`TODO`, `DRAFT`, etc.) before emit. Source: B.1 #6. |
| 1.4 | ✓ **`last_modified` uses file mtime, not git mtime.** Unstable across `touch` or no-content saves. Spec §12 open-Q-5 wants `git log -1 --format=%cI -- <file>`. → CLOSED retroactively in B.3 (`last-modified-cascade` helper: drawer → keyword → git-mtime → fs-mtime → today; garden normalizer calls it). Verified 2026-06-07 — no new fix needed. | Low (cosmetic but spec-divergent) | Garden normalizer (same place as 1.3). Source: B.1 #2. |
| 1.5 | ✓ **Library `last_modified` cascade not upgraded.** Still uses 2-step `or`; B.3 shipped `--last-modified-cascade` everywhere else. → [project-tier-1-5-1-8-1-9-complete](../../../.claude/memory/project_tier_1_5_1_8_1_9_complete.md) (shipped 2026-06-07, dotfiles `0cb4414`) | Low (consistency) | `a3madkour-publish-library.el` — swap to the shared helper. Source: B.3 carry-forward T1. |
| 1.6 | ✓ **B emits `slug:` on garden concept bundles.** Site linter rejects `slug` on concept-flavor notes; workaround applied 2026-06-02 (hand-edit). Re-bites on every ref-note→garden promotion. → [project-tier-1-6-complete](../../../.claude/memory/project_tier_1_6_complete.md) (shipped 2026-06-07, dotfiles `2134de8`) | Medium (CI fail trigger) | `a3madkour-publish-garden.el` frontmatter assembly — drop the slug line. Source: [project-b-slug-on-concept-followup](../../../.claude/memory/project_b_slug_on_concept_followup.md). |
| 1.7 | ✓ **D.1 attr_shortcode multi-word titles round-trip quotes.** `:title "Two words"` renders as `&amp;quot;Two words&amp;quot;`. Workaround: unquoted single-word titles. → [project-tier-1-7-complete](../../../.claude/memory/project_tier_1_7_complete.md) (shipped 2026-06-07, dotfiles `31f9570`) | Low (workaround sufficient until multi-word title needed) | ox-hugo custom translator OR pre-export buffer rewrite. Source: [feedback-d1-attr-shortcode-unquoted-titles](../../../.claude/memory/feedback_d1_attr_shortcode_unquoted_titles.md). |
| 1.8 | ✓ **`a3-pub.sh --check-orphans` crashes when org-roam dir missing.** `(org-roam-db-sync)` raises on machines without `~/org-roam/`. → CLOSED retroactively in `a3madkour-publish.el:317-319` (gates `(org-roam-db-sync)` on `boundp` + `file-directory-p`). Verified 2026-06-07 — no new fix needed. | Low (machine-specific) | `a3-pub.sh` wrapper — gate on dir existing OR add `--notes-dir <path>` flag. Source: [project-a1d-complete](../../../.claude/memory/project_a1d_complete.md) "Other A.1.d known limitations". |
| 1.9 | ✓ **Asset link `alt` text retains `file:` prefix when no display text.** Observable in `content/essays/example-multi/index.md` after the 2026-06-07 figref fix: `<img src="diagram-1.svg" alt="file:diagram-1.svg" />` — `file:` should have been stripped from the display the same way it's stripped from the path. → [project-tier-1-5-1-8-1-9-complete](../../../.claude/memory/project_tier_1_5_1_8_1_9_complete.md) (shipped 2026-06-07, dotfiles `350a711`) | Low (a11y suboptimal) | `a3madkour-pub/rewrite-asset-link` in `a3madkour-publish-assets.el`: derive display from `filename` when `text == raw path with file: prefix`. Add ert. Discovered during figref Task 9 verification. |
| 1.10 | ✓ **`finish-publish` Step B silently orphans the OLD bundle on failed slug-shift delete.** Same `--unpublish-delete-bundle` call shape as 1.1, but in Step B the manifest already points to the NEW URL (the per-section handler wrote + recorded the new bundle before `finish-publish` ran). A `'failed` return on the OLD-slug delete leaves a stray `content/<section>/<old-slug>/` bundle that Hugo will happily build as an undetected duplicate page; the diff will never re-surface it because no manifest entry tracks the old URL. → [project-tier-1-10-complete](../../../.claude/memory/project_tier_1_10_complete.md) (shipped 2026-06-07, dotfiles `6d52eef`; option (c) — visibility-via-WARN — chosen over the heavier (a) / (b) options) | Medium (silent content duplication) | `a3madkour-publish-unpublish.el` `finish-publish` Step B (lines around 270-279 as of 2026-06-07). Possible fixes: (a) bookkeeping side-table of failed-delete URLs that next run's diff sweeps; (b) `record-publish` a "ghost" removed entry for the old URL; (c) loud author-facing WARN + manual cleanup. Discovered during Tier 1.1 analysis. |

**TIER 1 CLOSED 2026-06-07.** All 10 rows ✓: 1.1, 1.2, 1.6, 1.7, 1.10 shipped this session (one commit each); 1.5, 1.9 also shipped this session; 1.3, 1.4, 1.8 verified retroactively closed by prior B.2 / B.3 / A.1.d work. 7 fixes across 6 dotfiles commits + 7 site doc commits. dotfiles ert 606 → 616 (+10 named regression tests). Tier 2 is the next session's queue head — see entry checklist there.

**Session shape (historical):** Planned as two sessions (Session 1A high-severity, Session 1B small batch) — actually shipped in one extended session via three chunks plus a follow-up.

---

## Tier 2 — UX polish (visible gaps in shipped features)

**Goal:** make shipped features feel finished. Most items have user-facing impact across multiple surfaces.

| # | Item | Trigger | Where to start |
|---|---|---|---|
| 2.1 | ✓ **Anchor affordance.** Shipped 2026-06-07. Site-wide §-glyph on every `id`-bearing element inside `<main>`; SSR via shared partial + heading render hook + 12 D.1 shortcodes + 7 chrome partials; JS module for click-to-clipboard + top-of-viewport banner; 27th linter pair gates the invariant. → [project-anchor-affordance-complete](../../../.claude/memory/project_anchor_affordance_complete.md) | n/a (shipped) | Spec: [`2026-06-07-anchor-affordance-design.md`](2026-06-07-anchor-affordance-design.md). |
| 2.2 | ☐ **D.1 cross-reference auto-formatting.** `{{< ref-block "thm-foo" >}}` → "Theorem 1" via two-pass scratch lookup. | First essay author types a manual reference that gets stale after a renumber. | New shortcode in `layouts/shortcodes/`. Source: D.1 follow-up #1 in [project-d1-complete](../../../.claude/memory/project_d1_complete.md). |
| 2.3 | ☐ **D.1 section-prefixed numbering** ("Theorem 3.2" not just "Theorem 1"). | First long essay where bare integers stop being navigable. | Block-shortcode counters in `layouts/shortcodes/`. Source: D.1 follow-up #2. |
| 2.4 | ✓ **Anchor-affordance heading-level tuning — skip H4-H6** 2026-06-08. Heading render hook gates `{{ if and $id (lt .Level 4) }}` so H4/H5/H6 IDs render without the §-glyph; linter `_HEADING_TAGS` drops h4-h6 to match. AMS block-header H4s (inside `block-*` containers) keep their § via the linter's BLOCK pending mode — unchanged. Triggered fixture-first (no real essays yet): `content/essays/example-h4-density/` exercises 9 H4s across 4 H3s in 2 H2s to make the density visible. → [project-tier-2-4-complete](../../../.claude/memory/project_tier_2_4_complete.md) | n/a (shipped) | One conditional in the heading render hook + `_HEADING_TAGS` set narrow. |
| 2.5 | ✓ **Citation hover-card Source/Related-note pill colors fixed 2026-06-08.** Roadmap row originally pointed at the wrong surface (`.cite-modal-source` in the full-citation modal) — actual bug was in the *hover* citation-card. `.citation-card a { color: var(--color-burgundy); }` (0,1,1) was beating `.ref-cite-source { color: var(--color-steel); }` (0,1,0) on text color when `citation-card.js` clones a reference `<li>`'s innerHTML into the card. Result: Source pill rendered navy *border* but burgundy *text* — a mismatched chip the eye reads as "off / black-bordered." Fix: two scoped overrides (`.citation-card .ref-cite-source { color: var(--color-steel); }` + `.citation-card .ref-cite-note { color: var(--color-green); }`) keep border+text matched when cloned. Dark-mode loudness hypothesis (b) untested — leave for follow-up if author still flags it. | n/a (shipped) | CSS §13 (citation-card block, ~line 707). |

**Session shape:** 2.1 is its own session (design already brainstormed; plan + impl is the next session). 2.2 + 2.3 ship together when triggered. 2.4 is a one-liner fast-follow after 2.1 ships and real essays surface the density question. 2.5 is a small visual-polish slice — diagnose-first before fixing.

---

## Tier 3 — Phase 8 QA walkthrough (manual; human-driven)

**Goal:** verify accessibility / perf / mobile / cross-browser claims by walking the canonical QA checklist with a human at the keyboard. Cannot automate; can only prep.

**Source:** `docs/superpowers/qa-checklists/2026-05-13-phase-8-final-qa.md` — checklist of 45 items across 5 categories. Static-findable issues already resolved (commit `7ac2539`).

| # | Item | What's needed |
|---|---|---|
| 3.1 | ☐ §1.1–1.5, 1.7–1.9 keyboard navigation walkthrough | Human at keyboard + Tab through every interactive surface |
| 3.2 | ☐ §2 screen-reader walkthrough | macOS VoiceOver or NVDA pass |
| 3.3 | ☐ §3 color-blindness simulation | DevTools rendering panel, three palettes |
| 3.4 | ☐ §4 mobile breakpoint pass | Real device at 360 / 414 / 768 / 960 / 1220px or responsive DevTools |
| 3.5 | ☐ §5 perf walk | DevTools throttled CPU + 3G; cross-reference LHCI gates |

**Session shape:** one session per category, or one big "QA day" session. Owner: the author. Claude's role limited to prep — capture findings + file fixes as Tier 1 / 2 items.

**Entry checklist:** Open `docs/superpowers/qa-checklists/2026-05-13-phase-8-final-qa.md`, walk top-to-bottom, log every finding inline in the checklist (already structured for it).

---

## Tier 4 — Hygiene / cleanup (low-risk, fast cycle)

**Goal:** batch the long tail of "logged, not blocking" findings into one or two cleanup commits.

| # | Item | Where | Source |
|---|---|---|---|
| 4.1 | ✓ `defcustom :group 'a3madkour-publish` should be `'a3madkour-pub` → [project-tier-4-complete](../../../.claude/memory/project_tier_4_complete.md) (shipped 2026-06-08; two stragglers — `frontmatter.el:38` + `unpublish.el:47` — corrected; remaining modules already used the canonical `'a3madkour-pub`) | Per-module `defgroup` declarations | B.2 carry-forward #3 |
| 4.2 | ✓ `--coerce-year` has unused `_file` arg → [project-tier-4-complete](../../../.claude/memory/project_tier_4_complete.md) (shipped 2026-06-08; arg dropped from defun + caller; no ert callers existed) | `a3madkour-publish-research.el` | B.3 carry-forward #1 |
| 4.3 | ✓ `rewrite-to-tmp-file` duplicated across garden/research/essays — CLOSED retroactively. Grep confirms full extraction: single source at `a3madkour-publish-rewrite.el:425` (`a3madkour-pub-rewrite/rewrite-to-tmp-file`), called from essays/garden/research handlers. No code change needed. Verified 2026-06-08. | Extract into shared module | B.3 carry-forward #2 (stale; verified retro-closed) |
| 4.4 | ✓ `--render-scalar` `%S` fallback errors on custom structs / hashtables → [project-tier-4-complete](../../../.claude/memory/project_tier_4_complete.md) (shipped 2026-06-08; wrapped the `%S` print form in `--yaml-single-quote` so hashtables/structs/vectors round-trip as quoted strings; +2 ert tests). NOTE: roadmap originally pointed at `frontmatter.el` — actual function lives in `a3madkour-publish-library.el:254`. | `a3madkour-publish-library.el` (was: frontmatter.el — corrected) | B.2 carry-forward #2 |
| 4.5 | ✓ Shipped 2026-06-08. `check_library_covers.run(repo_root) -> (rc, errors)` added for parity with sibling linters; 2 new tests in `test_check_library_covers.py` (13 → 15). Warnings remain CLI-only (advisory). | `tools/check_library_covers.py` | B.2 carry-forward #1 |
| 4.6 | ✓ Shipped 2026-06-08. §6.3 template updated to wrap every shortcode in `@@hugo:...@@` export-snippet, with prelude explaining the ox-hugo HTML-encoding behavior. | `docs/superpowers/specs/2026-05-31-phase-3-b-4-essays-handler-design.md` §6.3 | B.4 follow-up |

**Session shape:** one batch session. Each item is a small diff. Per the dotfiles bystander rule, stage by exact path.

**TIER 4 CLOSED 2026-06-08.** All 4 rows ✓: 4.1, 4.2, 4.4 shipped this session in one dotfiles commit; 4.3 verified retro-closed by prior rewrite-extraction work. Suite 616 → 618 (+2 named tests for the 4.4 fallback). Tier 5 is the next session's queue head — see entry checklist there.

---

## Tier 5 — Tooling gaps

**Goal:** author-side ergonomics. Reduces friction for next batch of real content.

| # | Item | Source |
|---|---|---|
| 5.1 | ✓ **`a3-unpublish-deliberate` command.** Recover from a stale deliberate publish. → [project-tier-5-1-complete](../../../.claude/memory/project_tier_5_1_complete.md) (shipped 2026-06-08; synchronous command composing existing primitives — manifest lookup → `--unpublish-delete-bundle` → `record-publish 'removed`; refuses living-section ids; mirrors bug-1.1's self-healing contract on `'failed` delete; +11 ert tests) | B.4 follow-up #1 |
| 5.2 | ✓ **Emacs publish-author helpers** — 6 interactive commands in `a3madkour-publish-author.el`. → [project-tier-5-2-complete](../../../.claude/memory/project_tier_5_2_complete.md) (shipped 2026-06-08, dotfiles `8e5e76b`; mark / unmark / status / library-insert-item / library-insert-extras / jump-to-source; +33 ert; preview-section deferred to its own slice — Tier 5.3 once filed). | [project-emacs-publish-helpers-followup](../../../.claude/memory/project_emacs_publish_helpers_followup.md) |

**Session shape:** 5.1 was small (one session, shipped 2026-06-08). 5.2 shipped 2026-06-08 in its own brainstorm → spec → plan → ship cycle.

**TIER 5.2 CLOSED 2026-06-08.** Six interactive commands shipped in one dotfiles commit (`8e5e76b`); +33 ert (suite 629 → 662). preview-section deferred — open a Tier 5.3 row when authoring friction surfaces.

**TIER 5.1 CLOSED 2026-06-08.** Synchronous recovery command; bundle delete + manifest `removed` advance; refuses living-section ids (publish-living owns those); preserves bug-1.1's self-healing contract on `'failed` delete. Suite 618 → 629 (+11 ert). Tier 5.2 still queued — own brainstorm cycle.

---

## Tier 6 — Small new features

**Goal:** small new surfaces that don't warrant a full sub-project.

| # | Item | Source |
|---|---|---|
| 6.1 | ⊘ **About Now widget.** Demoted back to deferred-features registry 2026-06-08 — see CLOSED block. → [project-tier-6-deferred](../../../.claude/memory/project_tier_6_deferred.md) | CLAUDE.md "Not started, in phase order" |

**Session shape (historical):** one brainstorm + spec + plan + ship cycle.

**TIER 6 CLOSED-BY-DEFERRAL 2026-06-08.** Brainstorm opened, scoping question surfaced the overlap: the homepage Currently widget (shipped homepage-v3 slice 2026-05-13) already covers Reading / Listening / Playing / Watching auto-derived from `data/{reading,listening,playing,watching}.yaml`. The only *new* surface the Phase 3 spec §4.2 Now section adds beyond that is hand-authored **Working on** + **Wondering** prose. The author opted to skip rather than commit to that maintenance burden today — re-open if "I want a place to write Working on / Wondering copy" becomes a real ask. Row 6.1 moved back to [`2026-06-07-deferred-features-registry.md`](2026-06-07-deferred-features-registry.md) "Authoring / metadata extensions" table with the new trigger condition. Also corrects a factual error in the previous wording — `layouts/about/single.html` has no Now placeholder slot; the Tier 6 work would have added the section from scratch. No spec, no plan, no code shipped this session.

---

## Tier 7 — Deferred ergonomics (CI-side)

**Goal:** when authoring friction shows up around LHCI URL list management, ship 4.2 / 4.3.

| # | Item | Trigger | Source |
|---|---|---|---|
| 7.1 | ☐ **LHCI 4.2 — sitemap-derived URLs.** `tools/gen_lhci_urls.py` parses `public/sitemap.xml`, regenerates `lighthouserc.{json,mobile.json}`. ~80 LOC. | Next fixture retirement annoys the author. | [project-lhci-representative-pages-queued](../../../.claude/memory/project_lhci_representative_pages_queued.md) |
| 7.2 | ☐ **LHCI 4.3 — visual-feature autodetect.** Fingerprint URLs by CSS classes + shortcodes; auto-add novel signatures. ~150 LOC + allowlist. | After 4.2 + fingerprint corpus observable. | Same |

**Session shape:** 7.1 first (only when triggered). 7.2 after 7.1.

---

## Tier 8 — Large new features (LAST, per author's 2026-06-07 reorder)

**Goal:** the big new scopes. Each is its own brainstorm → spec → plan → ship cycle. Held until the polish/bugfix backlog is empty.

| # | Item | Source |
|---|---|---|
| 8.1 | ☐ **Sub-project E — explorable explainables** (Phase 3 final piece). Per-page interactive widgets + per-page JS bundle convention. No spec, no plan. | [project-phase-3-decomposition](../../../.claude/memory/project_phase_3_decomposition.md) |
| 8.2 | ☐ **Org → synced-poetry export.** Phase 3 Essay/poetry publish must emit the shipped `[mm:ss]` + `audio_url` contract. Stub spec exists. | `docs/superpowers/specs/2026-05-19-org-synced-poetry-export.md` |

**Session shape:** each is a multi-session sub-project. Don't open until prior tiers are clear (or author chooses to).

---

## Tier 9 — Long-horizon deferrals

See [`2026-06-07-deferred-features-registry.md`](2026-06-07-deferred-features-registry.md). All entries there are trigger-gated, no near-term commitment. The registry is durable across CLAUDE.md churn — when triggered, items graduate from there into a new Tier 6 / 7 row here.

---

## Authoring infrastructure (not a tier — author task)

- ☐ **B.4 example-*.org stubs not in version control.** The 4 example essays + `~/org/essays/assets/essay-one-uuid-placeholder/` live in `~/org/` (author's notes tree, untracked). If reproducibility matters, copy into a tracked location. Source: B.4 follow-up.

---

## How to use this file

- **Starting a tier session.** Read this file top-to-bottom. Pick the tier called out as "next" (or the first tier with open items if no annotation). For Tier 1 specifically, treat each ☐ as a separate slice with its own commit + ert coverage.
- **Marking shipped.** Edit the ☐ → ✓ inline, append `→ [project-<slug>-complete](../../../.claude/memory/...md)` link. Do NOT delete the row.
- **Adding work mid-tier.** New bugs discovered during a tier session: append to the same tier under "Discovered during this session" subheading; ship in the same session or carry to a follow-up commit.
- **Adding a new tier.** Insert numerically; renumber later tiers if needed. Update the "Active queue" pointer in [`2026-06-07-deferred-features-registry.md`](2026-06-07-deferred-features-registry.md).
- **Reordering.** Update this file with the new ordering + a short note documenting the reorder decision (echo: this file was created in a 2026-06-07 reorder session).

---

## Reorder decision log

- **2026-06-07** — Author's gut said "fix and polish before new features; explorables last". Tiers as listed above; sub-project E pushed to Tier 8. This file created in the same session. Memory pointer: [project-next-slice](../../../.claude/memory/project_next_slice.md).
