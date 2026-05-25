---
name: always-run-ci-locally-before-pushing
description: ALWAYS run `tools/ci-local.sh` before `git push`. Script mirrors the CI workflow step-for-step. Skipping it means CI catches what local missed — re-confirmed 2026-05-13 after THREE consecutive CI failures on the same slice (missing pagefind meta, then page-weight, then page-weight again).
metadata:
  type: feedback
  originSessionId: db0fe890-9229-4849-89d1-9d213bd28e0d
---

**Rule (caps in original from the user):** **ALWAYS RUN CI LOCALLY BEFORE PUSHING.**

There is a script: `tools/ci-local.sh`. Run it. If it ends with `CI-EQUIVALENT GREEN — safe to push`, push. If it exits non-zero anywhere, fix locally and re-run until green. Never push on a partial sweep.

```bash
tools/ci-local.sh
```

What it does (mirrors `.github/workflows/hugo.yaml` step-for-step):

1. Every pre-build linter + its sibling unit test (16 pairs as of 2026-05-14).
2. `HUGO_ENVIRONMENT=production hugo --minify` (strips drafts so page-weight measurements match CI).
3. Post-build linters + tests: `check_pagefind_meta.py`, `check_cite_meta.py`, `check_page_weights.py`, `check_smoke.py`.
4. **Lighthouse CI (added 2026-05-14)** — `npx --yes @lhci/cli@0.13.x autorun` runs against both `lighthouserc.json` (desktop) and `lighthouserc.mobile.json`. Asserts perf/a11y/best-practices/seo ≥ 0.9 on 12 URLs each. Requires `npx` + `chromium`/`google-chrome` on PATH; preflight fails loud if missing. See [[ci-local-lhci-deps]].

`set -euo pipefail` at the top — first failure halts the script.

**Why this memory exists:**

During the garden path-log retrieval slice (2026-05-13), CI failed THREE consecutive times on issues my local sweeps would have caught:

1. **First push (`5d56dbd..4e3f576`):** CI failed on `check_pagefind_meta.py` — the new `/garden/history/` layout was missing the `data-pagefind-meta="section:garden"` + filter spans. My Task 9 sweep had skipped post-build linters entirely.
2. **Fix-up push (`4e3f576..c7df140`):** CI failed on `check_page_weights.py` — 2 essay pages 2 KB over the 100 KB default budget (cumulative CSS growth from new §43 + existing essay CSS finally crossed). My re-push sweep had included pagefind but still skipped page-weights.
3. **Third push attempt (during prep for next session):** Caught locally THIS time because I finally ran the full CI-equivalent. User instruction after the second failure: "ALWAYS RUN CI LOCALLY BEFORE PUSHING" — caps in original.

The cost of skipping a step is a red CI badge + a follow-up commit + user trust. The cost of running the script is ~45 seconds.

**Invocation gotcha (handled by the script):** `tools/test_check_pagefind_meta.py` does NOT do `sys.path.insert(...)` like other linter tests; it requires running from the `tools/` directory (per the CI workflow's `cd tools && python3 -m unittest ...` form). The script handles this with `(cd tools && python3 -m unittest test_check_pagefind_meta.py)`. Don't try to run it from project root via `python3 -m unittest tools/test_check_pagefind_meta.py` — gives `ModuleNotFoundError`.

**Budget tuning during a slice:** When CSS/JS/images grow as a slice adds visual surfaces, `tools/check_page_weights.py`'s `BUDGETS_PREFIX` may need updating. The slice that pushes cumulative payload over the threshold owns the budget update. Don't trim cosmetically to stay under an outdated budget — raise the budget AND its sibling-test assertions together (`tools/test_check_page_weights.py`). Established tiers as of 2026-05-13:

| Prefix | Budget | Reason |
|---|---|---|
| `/garden/graph/`, `/research/graph/`, `/works/graph/` | 600 KB | inline d3 |
| `/works/`, `/garden/`, `/research/` | 600 KB | graph JS reference + content |
| `/works/music/` | 500 KB | media |
| `/library/`, `/library/<leaf>/` | 900 KB | umbrella + leaves carry hero + catalogue + themed shelves with 8 self-hosted covers (~80–150 KB each) since the 2026-05-14 LHCI third-party-cookies fix — see [[library-covers-static-path]] |
| `/essays/` | 200 KB | accumulated CSS growth (sidenotes, citations, Bento, §43) |
| `/` (home) | 500 KB | hero + Currently + strips |
| default | 100 KB | about, taxonomy lists, etc. |

See also: [[hugo-section-dir-note-linter-conflict]].
