---
name: audit-r1-complete
description: "Audit-remediation Tier R1 (correctness/security) shipped 2026-07-03, site 8ba3882..2422e81 (3 commits, +9 tests); R2 is next queue head"
metadata: 
  node_type: memory
  type: project
  originSessionId: 95b0b22a-9036-45e5-8b84-f1bd965400ea
---

# Audit remediation Tier R1 — shipped 2026-07-03

Closed the three correctness/security defects from the 2026-07-03 audit ([[audit-remediation-roadmap]]). Site `8ba3882..2422e81`, 3 commits, each with named test coverage per the roadmap rule.

- **R1.1 `8ba3882`** — `tools/check_fixtures.py` `parse_scalar` split inline arrays on every comma → `["Marquez, Gabriel"]` became two authors, and permissive validators passed it (CI green on corrupted data). Routed the array split through the existing `_split_top_commas` helper. Also normalized CRLF + tolerated a closing `---` with no trailing newline in `parse_frontmatter` (was returning None → silent skip in the ~14 linters that `if fm is None: continue`). +6 tests. 447 CI linter-pair tests green; 7 real linters lint clean against live fixtures.
- **R1.2 `2b3a9d7`** — `tools/poll_streams.py` `main()` now gates the `streams-live.yaml` write on a real twitch/youtube state change (`changed or not exists`); `last_polled` alone no longer churns. Was rewriting every run → 5-min cron committed 288×/day (or red 288×/day if secrets unset; 0 bot commits to date confirmed failing/disabled). +3 tests (WriteGatingTests). 22 poll tests green.
- **R1.3 `2422e81`** — pinned `treosh/lighthouse-ci-action` from floating `@v12` to commit `3e7e23fb74242897f95c0ba9cabad3d0227b9b18` (v12.6.2) in both `hugo.yaml` usages; it runs in the privileged (`id-token:write`+`pages:write`) build job.

**Not pushed** — commits are local on master; author pushes when ready.

**Carry-forwards** (filed into later roadmap tiers, not lost): streams deploy-trigger decision — `GITHUB_TOKEN` pushes don't trigger the deploy workflow, so the cron never reaches the live site — + auto-stub title `json.dumps` escaping (both R4.6); broader `actions/*` floating-major SHA-pin sweep (R4.4).

**R2 is the next queue head:** missing `math` shortcode stub, dark-block equality linter, CSS-class referential-integrity linter, LHCI-order fix, `cite.js` `undefined` render. Pre-existing `test_publish_integration.py` failures are environmental (need `~/org/notes` + emacs), not regressions — verified identical on HEAD.
