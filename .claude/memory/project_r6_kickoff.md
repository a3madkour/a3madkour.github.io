---
name: r6-kickoff
description: "NEXT-SESSION ENTRY: R6 (optional design-scale polish) is all that remains of the audit roadmap. R6.1 CSS spacing scale + R6.2 breakpoint tokens are actionable; R6.3 link-crawl is trigger-gated (defer)."
metadata: 
  node_type: memory
  type: project
  originSessionId: a4b4e454-fc0d-4ae8-8172-2c36574d9f94
---

# R6 kickoff — the only remaining audit work (optional)

**The full R1–R5 audit remediation is DONE and pushed** (see [[audit-remediation-roadmap]]). R6 is *optional design-scale polish* — the author opted to do it. Row detail lives in `docs/superpowers/specs/2026-07-03-audit-remediation-roadmap.md` §"Tier R6" (lines ~113-115).

## The three R6 rows

- **R6.1 — CSS spacing scale. ✅ SHIPPED 2026-07-05** (`5795280..996bfbf`) — see [[audit-r6-1-complete]]. 12-step `--space-*` ladder + 31st linter pair (`check_spacing_tokens.py`); 533 rewrites via deterministic codemod. Done first, as planned.
- **R6.2 — Breakpoint tokens. ✅ SHIPPED 2026-07-05** (`b1fc2d6..3e61b81`) — see [[audit-r6-2-complete]]. B1 (document + guard, zero layout change): canonical scale comment + 32nd linter pair `check_breakpoints.py` (CSS↔JS anti-drift). **This closed the whole audit roadmap.** Original framing below for reference:
- ~~R6.2 (was actionable)~~ Desktop breakpoints are **8 one-off values** (`800/900/960/1099/1140/1219` max; `960/1100/1280` min) with a **`1099/1100` off-by-one seam**; JS mirrors magic breakpoints (`RAIL_BREAKPOINT=1100`, `MOBILE_BREAKPOINT=720`) that hand-sync with CSS. Mobile side already disciplined. Reconcile a 3-tier scale (or `--bp-*` custom props for the JS side). **Reconcile the ~960px half-screen tier the author actually tests at** ([[feedback_test_at_half_screen_1080p]]).
- **R6.3 — Built-HTML link-integrity crawl. TRIGGER-GATED — DEFER.** Nothing crawls rendered `public/` for broken `<a href>`s. Fine for a fixture-only site; open only when real interlinked content lands. Don't build now.

## How to run it (established session pattern)

Each row is its own **brainstorm → spec → plan → implement → push** cycle (superpowers skills). This session's proven rhythm:
1. `superpowers:brainstorming` → design doc in `docs/superpowers/specs/2026-XX-XX-<topic>-design.md`.
2. `superpowers:writing-plans` → plan in `docs/superpowers/plans/`.
3. **subagent-driven-development** (fresh implementer + task-reviewer per task, Opus final whole-branch review) OR inline for parity-heavy work.
4. **Verify green then push:** `tools/ci-local.sh` (LHCI stops locally on chromium — expected); commit to **master** (author's pattern — no feature branch this backlog); push; watch the deploy (`gh run watch <id> --exit-status` in background).

**Verification gotcha for R6:** CSS-token refactors are pure-refactor → the guard is a **byte-identical MINIFIED build diff** ([[reference_verify_template_refactor_minified]]) + WCAG contrast still green (`check-contrast.py`) + the 9-spec E2E (`npx playwright test`, needs `npx pagefind@1.5.2 --site public/` for the search spec). `check_dark_tokens.py` guards the dark-block equality if palette-adjacent.

## CI/deploy notes (learned this session)
- Deploy pipeline: build (+ 9-spec E2E gate) → **parallel** lhci-desktop + lhci-mobile → deploy. ~20 min. LHCI was parallelized (R5.1 fallout) because serial ~30 min blew the timeout.
- **GitHub Pages `deploy` step flakes ~1/3 with "Deployment failed, try again later"** — transient; `gh run rerun <id> --failed` fixes it. Not a code issue.
- ~~Two open author decisions~~ **RESOLVED 2026-07-05** (`83e7875`): (1) `assets/jsconfig.json` baseUrl reverted — kept `baseUrl: "."` (harmless dev-only editor file, no reason to touch); (2) streams-poll cron **schedule trigger disabled** (commented out `*/5` cron, kept `workflow_dispatch`) — it was failing every 5 min because TWITCH_*/YOUTUBE_* secrets+vars are unset and the streams section is fixture-only. Re-enable the cron once real streaming credentials are wired.
