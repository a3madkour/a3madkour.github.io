---
name: audit-remediation-roadmap
description: "2026-07-03 six-lens audit → remediation roadmap at docs/superpowers/specs/2026-07-03-audit-remediation-roadmap.md; all rows open, R1 (parse_scalar false-green / streams-poll always-commits / unpinned LHCI action) is the queue head"
metadata: 
  node_type: memory
  type: project
  originSessionId: 95b0b22a-9036-45e5-8b84-f1bd965400ea
---

# Post-audit remediation roadmap — queued

A six-lens parallel audit (Python tooling / JS / CSS / templates / architecture / CI) ran 2026-07-03. Findings filed as a tiered roadmap: `docs/superpowers/specs/2026-07-03-audit-remediation-roadmap.md`. Structured like the sibling [[project-next-slice]] polish roadmap; row IDs are `R<tier>.<n>` to avoid collision.

**Two systemic stories drive the whole roadmap:** (1) "copy instead of abstract" — 3 graph runtimes 70–80% shared (~2280 LOC), 12 near-identical AMS block shortcodes, 3 graph-panels that have *already drifted* (`inert` vs `hidden`), 22 duplicated Python test scaffolds, 2 citation parsers; (2) no client-side test layer at all — 28 Python linter pairs check static markup, zero runtime coverage.

**Tiers:** R1 correctness/security (fix first) · R2 cheap gaps + guard linters · R3 a11y · R4 hygiene/doc-drift/config · R5 structural de-dup (R5.1 JS test harness must land first) · R6 optional design-scale · plus an "Accepted as-is" section.

**R1 = queue head, three verified defects:**
- R1.1 `check_fixtures.parse_scalar:151` splits quoted-comma lists (`["Marquez, Gabriel"]`→2 authors) → CI green on corrupted data; ~15 linters depend on it.
- R1.2 `poll_streams.py:278` writes fresh `last_polled` every run → streams-poll commits every 5 min (or red every 5 min); 0 bot commits to date = failing/disabled.
- R1.3 `hugo.yaml:192,199` third-party `treosh/lighthouse-ci-action@v12` unpinned in the privileged deploy-artifact job.

Verified firsthand during the audit: math shortcode absent, CI steps 71 (CLAUDE.md says 67), duplicate §43 in main.css, dark blocks currently in sync (14 tokens, 0 diffs). Per design-batch convention, no per-tier plans until each tier opens.
