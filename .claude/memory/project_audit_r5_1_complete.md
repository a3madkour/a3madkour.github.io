---
name: audit-r5-1-complete
description: "R5.1 JS test harness SHIPPED 2026-07-04 (e9b6d95..fd714af, pushed) — Playwright E2E, 6 smoke specs, CI-gated; R5.2 graph-core extraction is next"
metadata: 
  node_type: memory
  type: project
  originSessionId: a4b4e454-fc0d-4ae8-8172-2c36574d9f94
---

# Audit R5.1 — JS test harness (shipped, pushed)

**2026-07-04, commits `e9b6d95..fd714af` (8), pushed to origin/master** (first push of the whole R1–R5.1 backlog — 36 commits went up together). Executed via subagent-driven-development: 8 tasks, fresh implementer + task-reviewer per task, final whole-branch review on Opus = READY TO MERGE.

**What shipped:** a **dev-only Playwright E2E harness** — the first client-side test layer on the site (the audit's second systemic finding: "test pyramid has no top half"). This is the guard R5.2–R5.4 refactors run against.

- `package.json` (devDeps only: `@playwright/test` **1.61.1**, pinned exact) + committed `package-lock.json`. `playwright.config.ts` serves built `./public` via `python3 -m http.server` (http://, not file://), Chromium.
- 6 spec files under `tests/e2e/` (7 tests): `core` (brand + no-js/R3.6), `theme` (system→light→dark cycle), `filter-chips` (essays grid narrow + All), `search` (listbox/option + aria-activedescendant/R3.3), `cite` (5-tab ArrowRight roving/R3.4 + clipboard), `graph` (garden SVG `.garden-graph-node` mount — deliberately generic R5.2 safety net).
- CI: 4 steps in `hugo.yaml` **build** job, placed AFTER `Build Pagefind index` (search spec needs the index) and before artifact upload → `deploy` `needs: build` so a red suite blocks deploy. `actions/setup-node` pinned `49933ea5288caeca8642d1e84afbd3f7d6820020` (=v4). Mirrored in `ci-local.sh` with loud-skip when Node absent. CI step count 75→**79**.
- CLAUDE.md "No npm" line now documents the dev-only exception; roadmap R5.1 marked `✓`; brief status → shipped.

**Tests are characterization/GREEN-first by design** — assert current behavior, no RED phase; they exist to catch drift during R5.2–R5.4. [[feedback-dont-defer-cheap-things]] one Minor logged (search.spec.ts one-shot `getAttribute('aria-activedescendant')` — search.js sets it synchronously so flake risk ~nil; optional hardening deferred).

**Gotchas worth carrying:** local Pagefind index for the search spec = `npx --yes pagefind@1.5.2 --site public/` (pagefind not on PATH here); `public/pagefind/` stays gitignored (CI rebuilds).

**Next: R5.2** — graph-core extraction (3 graph runtimes ~70–80% shared). The `graph.spec.ts` mount test is its safety net. See [[audit-remediation-roadmap]].
