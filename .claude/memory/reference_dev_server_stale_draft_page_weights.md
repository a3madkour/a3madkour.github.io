---
name: reference-dev-server-stale-draft-page-weights
description: "hugo server --buildDrafts leaves draft pages + UNMINIFIED css in public/, false-failing local check_page_weights.py; clean public/ before local weight checks"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 889a5f3c-3a85-4fd5-a10c-2092dc7137e1
---

# Dev server poisons local check_page_weights via stale draft artifacts

Running `hugo server --buildDrafts` (e.g. for a visual spot-check) writes
**draft pages** (`draft: true`, like `/blog/lorem-ipsum/`) and **unminified
CSS** into `public/`. A later local `python3 tools/check_page_weights.py` (which
audits whatever is in `public/`) then **false-fails**: the draft page appears
with unminified CSS (~157KB vs ~103KB minified) and blows its budget.

This is NOT a regression. **CI builds production** (`hugo --minify`, no
`--buildDrafts`), which excludes drafts entirely — so CI's page-weights is green
and the draft page never ships.

**Fix / correct local check:** clean-build before auditing —
`rm -rf public resources/_gen && hugo --gc --minify --quiet && python3 tools/check_page_weights.py`
→ draft absent, `OK (72 pages audited)`.

Distinct from [[reference_hugo_dev_server_gotcha]] (that one = don't run
`hugo --minify` *while* a dev server is alive → MIME poisoning). This one =
stale draft/unminified leftovers in `public/` AFTER a dev server ran. Both argue
for tearing down the dev server + clean-building before any `public/`-based
linter (page-weights, pagefind, smoke, anchor-link).

Surfaced 2026-07-05 during R6.2 ([[audit-r6-1-complete]] spot-check left the
artifact). `/blog/` budget is 150KB; the legacy blog fixture is `draft: true`.
