---
name: reference-playwright-reuse-existing-server
description: "playwright.config.ts reuseExistingServer silently serves another checkout's build — assert page identity before trusting a result"
metadata: 
  node_type: memory
  type: reference
  originSessionId: ad301310-23dc-4009-b3e1-3375f3d4be7c
  modified: 2026-09-08T03:55:51.673Z
---

`playwright.config.ts` sets `reuseExistingServer: !process.env.CI`. If the port
is already held — by another worktree, another agent, or a stale server that
outlived its run — Playwright **attaches to it silently** and every assertion
runs against *that* build. No warning, no error, green results.

This is not theoretical: during the 2026-09-07 remediation a reviewer reported
**9/9 passing against a foreign worktree** before noticing the served markup
carried attributes its own tree did not have.

The port is env-overridable (`E2E_PORT`, added 2026-09-07) but that alone is not
enough — servers outlive their agents, so recycled port numbers still collide.

**Before trusting any browser result:**

1. Use a distinct `E2E_PORT`.
2. Confirm the port was free first (`lsof -nP -iTCP:<port> -sTCP:LISTEN`).
3. **Assert page identity** — fetch a page and check for a marker only your tree
   has: a class you just added, a fingerprinted asset hash from your own
   `public/`, an attribute your change introduces. If the marker is absent when
   it should be present, you are on someone else's server.
4. Kill strays afterwards: `pkill -f 'http.server.*--directory public'`.

A stale run can also be the reverse trap: a *removed* marker still present means
you are looking at a pre-change build. Related:
[[reference_hugo_dev_server_gotcha]] for the other way a stale server poisons
local results.
