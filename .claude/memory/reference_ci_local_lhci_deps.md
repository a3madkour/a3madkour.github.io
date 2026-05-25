---
name: ci-local-lhci-deps
description: "`tools/ci-local.sh` runs Lighthouse CI desktop + mobile via `npx --yes @lhci/cli@0.13.x`. Requires `npx` (Node ≥ 14) and a chromium/google-chrome binary on PATH. Preflight check fails loudly if missing."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 0e7723e4-90d0-47b3-abbf-e45eb1d38a69
---

`tools/ci-local.sh` includes Lighthouse CI desktop + mobile assertions (added 2026-05-14 to close the structural gap that let the library-redesign merge ship red — `/library/` best-practices = 0.74 on Wikipedia-hotlinked covers).

**Dependencies (Arch Linux):**

```
sudo pacman -S nodejs npm chromium
```

The script invokes `npx --yes @lhci/cli@0.13.x autorun --config=<file>` twice (desktop, then mobile). First run downloads `@lhci/cli` to npx cache (~10 MB); subsequent runs cache-hit.

Preflight in `ci-local.sh` checks both `npx` and a `chromium`/`google-chrome` binary on PATH, exits non-zero with an install hint if either is missing — don't silently skip LHCI.

**Local-vs-CI variance to expect:**

LHCI performance scores are CPU-sensitive under mobile-simulate throttling. Local runs on a busy laptop can score 5–8 points below the same code on CI's stable runner. Known sensitive metric: `/garden/` mobile FCP (Petrona via Google Fonts adds render-blocking latency; CLS from filter-chip hydration adds ~0.15). If local LHCI fails on `categories.performance` while CI passes, suspect environment first; if both fail, investigate.

**LHR diagnostic recipe (when LHCI fails):**

The asserter prints `Open the report at https://storage.googleapis.com/lighthouse-infrastructure.appspot.com/reports/<id>.report.html` per URL. Fetch the HTML, regex out `__LIGHTHOUSE_JSON__ = {...}`, inspect the failing audits + their `details.items`. Done this way for run #42 to identify `third-party-cookies` from Wikipedia covers + `/favicon.ico` 404 → fixed the underlying issue rather than tuning thresholds.
