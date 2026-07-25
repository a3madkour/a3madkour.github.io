---
name: audit-r5-3b-complete
description: "R5.3b graph-panel single-partial SHIPPED 2026-07-05 (4775888 impl, bf9e8c4 docs, 0cd0819 lint-fix); also closes R3.2 structural remainder; R5.4 next"
metadata: 
  node_type: memory
  type: project
  originSessionId: a4b4e454-fc0d-4ae8-8172-2c36574d9f94
---

# Audit R5.3b — graph-panel single-partial (shipped)

**2026-07-05.** Subagent-driven (2 tasks + a controller-resolved plan defect + a final-review fix). Design (committed with R5.3a-era docs), plan `90937b3`, impl `4775888`, docs `bf9e8c4`, lint-hardening `0cd0819`. Design/plan under `docs/superpowers/{specs,plans}/2026-07-05-r5.3b-*`. **Not yet pushed** at time of writing.

**What shipped:** the three `layouts/partials/{garden,research,works}/graph-panel.html` partials → one-line wrappers over a new shared `layouts/partials/graph-panel.html` (params `id`/`title`/`ariaLabel`/`section`); the **9 call sites unchanged**. Mirrors the already-shared `graph-legend.html`. **Standardized the toolbar `aria-label="Graph filters"` up** (research/works gained it — the intended a11y delta). **This closes R3.2's deferred graph-panel skeleton reconciliation** (R3.2 ◐→✓).

**Two notable events:**
1. **Plan defect (verification method).** The plan said verify with a raw (`hugo` no-minify) byte-identical diff. That's WRONG for unifying differently-formatted partials: raw HTML preserves each source's `<aside>` line-breaking + attribute order, so a single shared partial can't reproduce all three raw. **Fix: verify against the MINIFIED build (what ships).** Garden was byte-identical minified (its source aside order already matched the partial); research/works showed only (a) a cosmetic `<aside>` attribute reorder — semantically inert — and (b) the toolbar aria-label. Verified panel-localized via a python pre/post-aside + token-preservation check. See [[reference_verify_template_refactor_minified]].
2. **check_graph_chrome false-green (final review caught).** The refactor moved the `graph-legend.html` include *inside* the shared partial, so the linter was updated to accept transitive inclusion (`SHARED_PANEL_CALL`) — but the shared partial itself wasn't a checked SURFACE, so dropping its legend later would pass green while every panel lost its legend. **Fix `0cd0819`:** added `layouts/partials/graph-panel.html` to SURFACES (now 7). Proved a removed legend fails the linter.

**Next: R5.4** — Python tooling dedup (the audit's "22 Python test files re-roll identical scaffolding" + `citations.yaml` two-parsers). Then R6 optional. See [[audit-remediation-roadmap]].
