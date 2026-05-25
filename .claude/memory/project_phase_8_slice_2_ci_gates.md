---
name: project-phase-8-slice-2-ci-gates
description: Phase 8 second slice (build smoke + page-weight + Lighthouse CI mobile+desktop) shipped to master 2026-05-13 (merge d8235f5)
metadata: 
  node_type: memory
  type: project
  originSessionId: 24cd0623-f93e-4288-bac7-27d7f97abfbc
---

Phase 8 Slice 2 — CI gates trio — merged.

Shipped to master 2026-05-13 (merge `d8235f5`, pushed to origin). 9 commits, 7 files, +532/-3.

**Why:** Spec `docs/superpowers/specs/2026-05-13-phase-8-design.md` §3 calls for three post-build gates so deploy is protected against regressions in page render correctness, payload size, and Lighthouse scores. With Slices 1 + 2 shipped, Phase 8's remaining work is just the manual QA pass (Slice 3).

**How to apply:** Slice 3 (final QA checklist) is next. It's largely user-driven (keyboard / SR / CB / mobile walkthrough) — Claude's role is drafting the checklist + fixing whatever surfaces. Pick up when the user is ready.

**What's live now:**
- `tools/check_smoke.py` — sibling-less linter (logic too thin to warrant test sibling per spec §3.1); asserts the 7 spec §11 URLs each resolve to non-empty parseable HTML
- `tools/check_page_weights.py` + `tools/test_check_page_weights.py` (14th linter pair, 24 tests) — per-page byte budget with prefix-keyed classifier. Slice extended spec §8 categories to current site reality: `/library/` at 500 KB (cover images), `/research/` at 600 KB (research-graph JS inlined on index)
- `lighthouserc.json` (desktop) + `lighthouserc.mobile.json` — two-config approach (avoided env-override brittleness); 12 stable fixture URLs each; 4 categories ≥0.9 (a11y / perf / bp / seo) with severity `error`
- 6 new CI workflow steps inserted between Pagefind index build and Upload artifact: smoke → page-weight + unit tests → LHCI desktop → LHCI mobile
- Workflow grew from 34 named steps (Slice 1 end) to 40 (Slice 2 end)

**Gotcha captured in CLAUDE.md** (worth re-reading when touching LHCI later):
- Two-config-file approach (`lighthouserc.json` + `lighthouserc.mobile.json`) is intentionally simpler than LHCI env override (`LHCI_COLLECT__SETTINGS__PRESET=""`), which can't be tested locally without LHCI CLI installed

**Spec-vs-reality deviation noted in classifier:**
- §8 budget table predates Library + the homepage v3 research index. The classifier now carries two extra entries (`/library/`, `/research/`) reflecting actual post-Phase-7 site shape. If a future page type blows budget, follow the same pattern: widen the classifier (don't override per page) unless the page is genuinely too heavy for its category.
