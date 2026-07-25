---
name: audit-remediation-roadmap
description: "2026-07-03 six-lens audit → remediation roadmap; R1–R5 ALL CLOSED 2026-07-05 (R5.4 Python tooling dedup shipped, local). Whole roadmap done; only R6 (optional polish) + 2 open author decisions remain"
metadata: 
  node_type: memory
  type: project
  originSessionId: 95b0b22a-9036-45e5-8b84-f1bd965400ea
---

# Post-audit remediation roadmap — R1–R5 ALL DONE; only R6 optional

A six-lens parallel audit ran 2026-07-03. Tiered roadmap: `docs/superpowers/specs/2026-07-03-audit-remediation-roadmap.md` (row IDs `R<tier>.<n>`). **Tiers R1–R4 + R5.1 all closed 2026-07-03/04** — see [[audit-r1-complete]], [[audit-r2-complete]], [[audit-r3-complete]], [[audit-r4-complete]], [[audit-r5-1-complete]]. **All 36 commits PUSHED to origin/master 2026-07-04** (the prior local-only backlog + R5.1 went up together; deploy workflow now includes the E2E gate).

**Two systemic stories drive what remains:** (1) "copy instead of abstract" — 3 graph runtimes 70–80% shared (~2280 LOC), 12 near-identical AMS block shortcodes, duplicated Python test scaffolds; (2) ~~no client-side test layer~~ — **R5.1 shipped the Playwright E2E harness that guards the rest of R5.**

## R5.2 — graph-core extraction: SHIPPED 2026-07-04

`d1e214c..d0ee5b0` + docs `88b0b4a` (local, executed inline). 2,280→1,316 LOC; `createGraph(adapter)` core + 3 thin adapters; works normalized (JS toolbar / inert panel / div canvas), subsuming R3.2. See [[audit-r5-2-complete]]. **`graph-core.js` must stay at `assets/js/` depth** (d3 relative import).

## R5.3a — AMS block consolidation: SHIPPED 2026-07-05

`da48e80..b651784` (local, subagent-driven). 11 numbered AMS shortcodes → thin wrappers over `layouts/partials/ams-block.html`; `proof.html` bespoke. Byte-identical rendered-HTML diff gate. Hugo gotcha: [[reference_hugo_paired_shortcode_partial_inner]]. See [[audit-r5-3a-complete]].

## R5.3b — graph-panel single-partial: SHIPPED 2026-07-05

`4775888` impl + `bf9e8c4` docs + `0cd0819` lint-fix (local, subagent-driven). 3 graph-panel partials → shared `layouts/partials/graph-panel.html` (params id/title/ariaLabel/section) + 3 wrappers; 9 call sites unchanged; toolbar aria-label standardized up. **Closes R3.2** (◐→✓). Two events: plan-defect (verify against MINIFIED not raw — [[reference_verify_template_refactor_minified]]) + a check_graph_chrome false-green the final review caught (shared partial added to SURFACES). See [[audit-r5-3b-complete]].

## R5.4 — Python tooling dedup: SHIPPED 2026-07-05 (CLOSES TIER R5)

`6d638d9..6ded6cb` (local, subagent-driven). test_helpers.TempRepo (5 heavy files migrated; 16 lighter left YAGNI), canonical `parse_citations_yaml` in check_fixtures, uniform `run()->(int,list)` seam on every linter; item 3 already-satisfied. Guard = 30 test pairs + empty before/after behavior diff. See [[audit-r5-4-complete]].

## ROADMAP DONE — only R6 (optional) + 2 author decisions remain

**Tiers R1–R5 all closed.** R6 is optional design-scale polish (not started; open it only if the author wants it). The **two open author decisions** below (streams-poll cron existence; jsconfig.json baseUrl) are the only other unactioned items — they need the author, not more engineering.

### (superseded) original R5.2 note — graph-core extraction

The 3 graph runtimes (garden / research / works) are ~70–75% duplicated (2280 LOC, confirmed by recon). **Scoping brief written 2026-07-04: `docs/superpowers/specs/2026-07-04-r5.2-graph-core-brief.md`** (local commit `7540c90`, not yet pushed) — extraction boundary (`createGraph(options)` factory + 3 thin adapters), unified data contract, 10 risks, and **4 open architecture decisions needing a brainstorm**: toolbar build-vs-wire, panel inert-vs-hidden, canvas div-vs-svg (works is the outlier on all three), and add research/works e2e mount specs FIRST (`graph.spec.ts` only covers garden today). Hard constraint: `graph-core.js` must stay at `assets/js/` depth (relative `./vendor/d3-*` import path).

`tests/e2e/graph.spec.ts` is the deliberately-generic safety net (SVG + ≥1 `.garden-graph-node` mount). **R5.2 is gated on: (1) R5.1 deploy confirmed green, (2) the brainstorm resolving those 4 decisions.** Then R5.3 (AMS-block + graph-panel consolidation — subsumes R3.2's deferred structural piece), R5.4 (Python tooling dedup). R6 optional.

**Before touching graph code, run `npx playwright test` (or `tools/ci-local.sh`) to establish the green baseline, then keep it green through the extraction.**

## Two open author decisions (not actioned)
- **streams-poll cron**: `GITHUB_TOKEN` pushes don't trigger deploy, so the 5-min cadence never reaches the live site — keep the cron at all? (R4.6 fixed the escaping; the existence question is the author's.)
- **`assets/jsconfig.json`**: external tooling (LSP/tailwind) repeatedly removes its `baseUrl`; reverted ~4× this session — worth a permanent gitignore/config fix.
