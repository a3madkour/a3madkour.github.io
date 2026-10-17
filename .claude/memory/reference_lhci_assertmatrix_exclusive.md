---
name: reference_lhci_assertmatrix_exclusive
description: "LHCI assertMatrix cannot sit beside assertions/preset — LHCI errors, asserts nothing, and the treosh CI job still goes green"
metadata:
  node_type: memory
  type: reference
  originSessionId: 5c2a5d02-07e8-4ea9-b946-2d0cb3a41302
  modified: 2026-10-17T22:02:41.796Z
---

LHCI rejects a `ci.assert` block holding `assertMatrix` together with `assertions` (or `preset`): `Error: Cannot use assertMatrix with other options`. It then asserts nothing, and the pinned treosh `lighthouse-ci-action` job still reports **success**. That left the mobile gate inert 2026-06-03 → 2026-10-17 (fixed in site `10dcb1e`: `gen_lhci_urls.py` folds the defaults into the matrix as a catch-all entry).

**How to apply:** a green LHCI job proves nothing on its own — grep its log for `Checking assertions against N URL(s)` (present = it asserted) or `Cannot use`. To prove a config enforces, re-run `npx @lhci/cli@0.13.x assert --config=<copy with minScore 0.999>` against the saved `.lighthouseci/` results and expect failures. Locally LHCI needs `chromium` on PATH: a wrapper script `exec`ing Playwright's cached Chrome for Testing works, a symlink does not. Related: [[reference_ci_local_lhci_deps]], [[feedback_mutation_test_every_guard]].
