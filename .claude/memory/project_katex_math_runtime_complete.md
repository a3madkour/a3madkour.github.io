---
name: project_katex_math_runtime_complete
description: KaTeX build-time math shipped + merged to main; master→main rename with pending remote steps
metadata: 
  node_type: memory
  type: project
  originSessionId: af9a74f8-6c52-4c5e-ab75-4088923e4f56
---

Build-time KaTeX math feature — **merged to `main` locally 2026-07-24** (fast-forward, commit `43eeb26`; `75afdbe` adds the CI trigger change). NOT pushed (push = live deploy). Spec `docs/superpowers/specs/2026-07-23-katex-math-runtime-design.md`, plan `docs/superpowers/plans/2026-07-23-katex-math-runtime.md`.

**Mechanism:** Hugo native `transform.ToMath` (embedded KaTeX), zero client JS. Bare `\(...\)`/`\[...\]` render everywhere incl. nested in AMS blocks (they `markdownify` inner → passthrough re-runs). `{{< math >}}` is an escape-hatch shortcode only. Vendored self-hosted `assets/css/katex.css` + 20 `static/fonts/katex/*.woff2`, `has_math`-gated `<head>` link. §50 in main.css.

**Post-merge remediation (adversarial-audit + /code-review → user chose "fix everything"), commit `43eeb26`:**
- Render is **unconditional** — a `has_math` gate on the passthrough hook CANNOT work: inside a shortcode's `markdownify` pass the hook's `.Page`/`.PageInner` resolve to the **home page**, not the essay, so the flag reads empty and nested AMS-block math would silently stop rendering. Verified empirically.
- Essays-only enforced via CI instead: `check_math.py` gained a **scope check** (fails if rendered-math markers appear outside `content/essays/`). Also reconciled its markers to matched-delimiter detection only (`\(...\)`/`\[...\]`/`{{< math >}}`); dropped `$$`, single-`$`, bare `\begin{}` (not enabled delimiters). Poems' unpaired `\[00:99]` timestamps correctly not flagged. Tests: 20/20.
- Extracted `layouts/partials/render-math.html` — shared `transform.ToMath`+`throwOnError`+error dance (render hook + shortcode both delegate). Fixed `$.Page.File.Path` nil-deref (uses `RelPermalink`) + misleading "org-math-lint is the backstop" comment (org-math-lint is dotfiles pre-publish, NOT site CI — the Hugo build is the validity gate here).
- Kept §50 `.katex { color: var(--color-ink) }` deliberately (forces ink in tinted contexts — not pure redundancy).

**master→main rename (2026-07-24):** local `master` renamed to `main`; `.github/workflows/hugo.yaml` deploy trigger updated `master`→`main` (`75afdbe`). **REMAINING manual remote steps (deploy-live, not done):** push `main`, switch GitHub default branch to `main`, delete `origin/master`. `main` is 11 ahead of `origin/master`, unpushed.

**Leftover cleanup:** `katex-math` branch still exists (merged, == `43eeb26`) checked out in worktree `.claude/worktrees/katex-math` (harness-managed, prior session → `ExitWorktree` is a no-op here). Safe to delete once that worktree is gone. See [[project_recipe_slice_2_complete]] — parked `recipes` branch ALSO claims main.css §50 + CLAUDE.md counts; if it merges after this, renumber math→§51 and reconcile counts.

**Local verification:** math E2E 4/4, `check_math` 20/20, `check_css_refs`/`check_fixtures`/`check_smoke`/`check_page_weights` green, clean build. (Search E2E needs CI-built Pagefind index; dotfiles publish-integration tests need emacs/org env — both fail locally, pre-existing/env-only.)
