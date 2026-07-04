---
name: audit-remediation-roadmap
description: "2026-07-03 six-lens audit → remediation roadmap; R1–R4 CLOSED 2026-07-03/04; R5.1 (JS test harness, Playwright decision locked) is the NEXT QUEUE HEAD — read its brief"
metadata: 
  node_type: memory
  type: project
  originSessionId: 95b0b22a-9036-45e5-8b84-f1bd965400ea
---

# Post-audit remediation roadmap — R1–R4 done, R5 next

A six-lens parallel audit ran 2026-07-03. Tiered roadmap: `docs/superpowers/specs/2026-07-03-audit-remediation-roadmap.md` (row IDs `R<tier>.<n>`). **Tiers R1–R4 all closed 2026-07-03/04** — see [[audit-r1-complete]], [[audit-r2-complete]], [[audit-r3-complete]], [[audit-r4-complete]]. All work is **local on master, NOT pushed** (22 commits).

**Two systemic stories still drive what remains:** (1) "copy instead of abstract" — 3 graph runtimes 70–80% shared (~2280 LOC), 12 near-identical AMS block shortcodes, duplicated Python test scaffolds; (2) no client-side test layer at all.

## NEXT QUEUE HEAD: R5.1 — JS test harness

**Decision locked 2026-07-04: Playwright, Node, dev-only** (real-browser E2E over built `public/`; `package.json` devDeps only, `node_modules` gitignored, nothing ships — the "no npm" rule is about the *shipped site*, not dev/CI tooling). Full kickoff brief: `docs/superpowers/specs/2026-07-04-r5.1-js-test-harness-brief.md` — has the 6 first-tests (theme cycle / filter chips / search listbox / cite tabs / graph mount / no-js) + CI wiring + gotchas.

**To start next session:** read the brief → draft the plan via `superpowers:writing-plans` → implement (thin smoke suite first). R5.1 is the prerequisite guard for R5.2 (graph-core extraction), R5.3 (AMS-block + graph-panel consolidation — subsumes R3.2's deferred structural piece), R5.4 (Python tooling dedup). R6 optional.

## Two open author decisions (not actioned)
- **streams-poll cron**: `GITHUB_TOKEN` pushes don't trigger deploy, so the 5-min cadence never reaches the live site — keep the cron at all? (R4.6 fixed the escaping; the existence question is the author's.)
- **`assets/jsconfig.json`**: external tooling (LSP/tailwind) repeatedly removes its `baseUrl`; reverted ~4× this session — worth a permanent gitignore/config fix.
