---
name: audit-r4-complete
description: "Audit-remediation Tier R4 (hygiene/doc-drift/config) shipped 2026-07-04, site 840a20e..6f2f4fb (3 commits); R1–R4 all closed, R5 (structural dedup) is next — start at R5.1 JS test harness"
metadata: 
  node_type: memory
  type: project
  originSessionId: 95b0b22a-9036-45e5-8b84-f1bd965400ea
---

# Audit remediation Tier R4 (hygiene / doc-drift / config) — shipped 2026-07-04

Closed all R4 rows from [[audit-remediation-roadmap]] (R4.3 already shipped with R2.3). Site `840a20e..6f2f4fb`, 3 commits.

- **R4.6 `840a20e`** — poll_streams `write_auto_stub` now `json.dumps`-escapes the title (was `.replace('"')` only → newline-injection into committed frontmatter). +1 test.
- **R4.2/R4.4/R4.5/R4.7 `32739ee`**:
  - R4.2 duplicate §43 in main.css → "Reading history" renumbered to **§42a** (canonical §43 = Citation export; order 42 → 42a → 43, no cascade).
  - R4.4 CI hardening: LHCI `numberOfRuns` 1→3 (gen_lhci_urls preserves it); SHA256 verification on the Hugo `.deb` (`9678d80…`) + Pagefind tarball (`afb824a…`); all first-party `actions/*` pinned to commit SHA (checkout `93cb6ef`, setup-python `ece7cb0`, configure-pages `45bfe01`, upload-pages-artifact `fc324d3`, deploy-pages `cd2ce8f`); `hugoVersion.min` 0.112→0.162; dropped unused `YOUTUBE_API_KEY` secret; `timeout-minutes` on all jobs (build 20 / deploy 10 / poll 5).
  - R4.5 ci-local.sh builds the Pagefind index after Hugo (loud skip if binary absent) + `--gc` flag — local green now exercises the /pagefind/ path.
  - R4.7 research graph-script `partialCached` — moved "research-graph" from the ignored context slot to an explicit cache variant.
- **R4.1 `6f2f4fb`** — CLAUDE.md drift sweep: linter pairs 28→30, CI steps 67→75 (with recount note), stub shortcodes (math/video-sync/lyrics data-pending; widget is live explorables), CI paragraph updated (R2.4 reorder, checksums, SHA-pins, timeouts, numberOfRuns:3), Project-status refreshed → polish roadmap fully closed + audit roadmap R1–R4 closed + R5.1 next.

**Recurring nuisance:** external tooling (LSP/tailwind) keeps re-editing `assets/jsconfig.json` (removes `baseUrl`); reverted several times this session — not part of any change. If it persists, worth a `.gitignore` or config fix.

**Open author decision (not actioned):** streams-poll cron — `GITHUB_TOKEN` pushes don't trigger the deploy workflow, so the 5-min cadence never reaches the live site. Whether to keep the cron at all is the author's call.

Verified: 467 CI linter-pair tests + 47 misc green; clean rebuild; all `check_*.py` green; 75 CI steps confirmed. **Not pushed** — local on master.

**R5 (structural de-dup) is the next queue head — START AT R5.1** (a JS test harness), the prerequisite for R5.2 (graph-core extraction), R5.3 (AMS-block + graph-panel consolidation — subsumes R3.2's deferred piece), R5.4 (Python tooling dedup). R6 optional.
