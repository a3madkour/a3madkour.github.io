---
name: audit-r5-4-complete
description: R5.4 Python tooling dedup SHIPPED 2026-07-05 (6d638d9..6ded6cb) — CLOSES Tier R5 + the whole audit-remediation roadmap (only R6 optional left)
metadata: 
  node_type: memory
  type: project
  originSessionId: a4b4e454-fc0d-4ae8-8172-2c36574d9f94
---

# Audit R5.4 — Python tooling dedup (shipped) — CLOSES TIER R5

**2026-07-05.** Subagent-driven (4 tasks, fresh implementer + reviewer each, Opus final = READY after a doc fix). Commits `6d638d9` (item 1), `66dfe5e` (item 2), `48813f0` (item 4), `6ded6cb` (docs). Design/plan under `docs/superpowers/{specs,plans}/2026-07-05-r5.4-*`. **Not yet pushed** at time of writing (local on master).

**This closes Tier R5 and the "copy instead of abstract" systemic story.** The whole audit-remediation roadmap (R1–R5) is now done; only **R6 (optional design-scale polish)** remains, plus two still-open **author decisions** (streams-poll cron existence; `assets/jsconfig.json` baseUrl — see [[audit-remediation-roadmap]]).

**What shipped (4 items, zero linter behavior change — the 30 linter+test pairs + an empty before/after behavior diff were the guard):**
1. **`tools/test_helpers.py` (`TempRepo`)** + `test_test_helpers.py`. Adopted by the **5** test files that carried a full duplicated `TempRepo` class (garden_fixtures, filter_chips_config, fixtures, toc_depth, poetry_synced). **Scope finding:** only 5 of the "~21" had a real class; the other 16 use lighter inline-`setUp` mkdtemp with per-file variations — **left as-is (YAGNI**; marginal dedup, no reusable class to extract). Docs state this honestly (final review caught an "all 30" overstatement → fixed).
2. **Canonical `parse_citations_yaml`** — the rich text→dict parser now lives solely in `check_fixtures` (cycle direction forced this: `check_citations` already imports from `check_fixtures`). `check_fixtures` derives its key-set via `set(parse_citations_yaml(...))`.
3. **Item 3 already-satisfied:** only `check_fixtures` defines the frontmatter parser; 15 linters already import it. The distinct data-yaml parsers (`parse_library_yaml`, streams/filter-chips config) parse genuinely different shapes → documented in place, no rewrite.
4. **Uniform `run(...) -> (int, list[str])` + thin `main()`** on every linter (15 laggards got it; `check_library_fixtures` arity normalized 3→2; 2 dead constants removed). Param is `repo_root` for most; `check_anchor_link`/`check_lhci_urls` take `public`/config paths (pre-existing outliers, documented).

**Verification pattern worth reusing:** for a pure linter refactor, capture each linter's stdout+stderr+exit BEFORE, refactor, re-run, `diff -r` must be empty — objective proof of zero behavior change even where an all-green baseline only exercises the happy path.

**Next: R6 optional**, else the roadmap is closed. See [[audit-remediation-roadmap]].
