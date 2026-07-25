---
name: audit-r6-1-complete
description: R6.1 CSS spacing scale SHIPPED 2026-07-05 (5795280..996bfbf) — 12-step --space-* ladder + 31st linter pair; R6.2 breakpoint tokens is next R6 row
metadata: 
  node_type: memory
  type: project
  originSessionId: 889a5f3c-3a85-4fd5-a10c-2092dc7137e1
---

# Audit R6.1 — CSS spacing scale (shipped)

**2026-07-05.** Subagent-driven, on master (no branch — audit-backlog pattern). Branch `5795280..996bfbf` (9 commits incl. design+plan). Spec/plan: `docs/superpowers/{specs,plans}/2026-07-05-r6.1-css-spacing-scale-*`. Pushed `83e7875..996bfbf`; deploy watched.

**What shipped:** a 12-step **t-shirt `--space-*` ladder** (`--space-3xs 0.25rem … --space-6xl 4rem`) defined ONCE on the light `:root` (§2) — spacing is **mode-independent**, so NOT duplicated in the dark blocks (unlike color tokens). All **533** in-scope bare-rem `gap`/`padding`/`margin` (+per-side/row/column/logical) values migrated to `var(--space-*)`; **30 sub-0.25rem hairlines left literal**; 2 negative margins → `calc(-1 * var(--space-*))`. Plus a **31st linter pair** `tools/check_spacing_tokens.py` (guard against magic-number drift), wired into CI + ci-local; CLAUDE.md → "Thirty-one linter pairs".

**Design decision (the crux):** Option A = *rationalized scale* (snap the rare tail to nearest step, deliberate sub-pixel–~4px visual change), NOT alias-only. High-frequency values (0.4/0.5/0.6/0.75/1/1.25/1.5/2/3rem) don't move; only the long tail snaps. **Deliberate downward absorptions** where nearest-step would differ: 0.9→md(0.75) not lg, 0.875→md, 0.55→xs, 0.45→2xs, 0.65→sm. Allowlist (stay literal) = {0.02,0.05,0.0625,0.1,0.12,0.125,0.15} — 0.0625(1px)/0.12 found during migration. 0.2/0.3 are NOT allowlisted (snap to 3xs).

**Execution pattern worth reusing:** the migration was done as a **deterministic codemod** (reuses the shipped linter's `IN_SCOPE_PROP_RE`+`REM_RE`, exact float-keyed snap table, comment-segment-safe, fails loud on unmapped values), NOT hand-editing 533 sites. The linter going to **0 violations** is the completeness proof; then task-review the diff. Collapsed plan Tasks 3–6 into one codemod diff (435/435 symmetric). Codemod lived in scratchpad, uncommitted.

**Verification (Option A moves pixels, so NOT byte-identical guard):** linter 0 · `check-contrast.py` green · build OK · **Playwright E2E 9/9** (functional regression guard — asserts behavior, not pixels) · author dev-server visual spot-check at ~960px = the real verifier → "push it". Final opus whole-branch review = READY, only Minors (fixed grid-gap-family coverage 996bfbf; left cosmetic redundant `X X` shorthands + CLAUDE.md list order).

**Next: R6.2 breakpoint tokens** (8 one-off desktop breakpoints + 1099/1100 seam + JS magic breakpoints) — see [[r6-kickoff]]. R6.3 link-crawl stays trigger-gated/deferred. After R6.2 the audit roadmap is fully closed.
