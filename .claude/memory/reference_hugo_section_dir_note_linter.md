---
name: hugo-section-dir-note-linter-conflict
description: "When adding a Hugo sub-section under `content/<section>/`, the existing per-note linter for that section will likely false-fail on the new section dir. Fix is a 5-line skip rule."
metadata: 
  node_type: memory
  type: reference
  originSessionId: db0fe890-9229-4849-89d1-9d213bd28e0d
---

When you add a Hugo sub-section under an existing content folder (e.g., `content/garden/history/` as a sub-section of `garden/`), the note-level linter for that section (e.g., `tools/check_garden_fixtures.py`) iterates every subdirectory expecting an `index.md`. Sub-section dirs have `_index.md` (Hugo's section marker), not `index.md`, so the linter false-fails with `no index.md`.

**Fix pattern** (5 lines, in the linter's directory loop):

```python
# Skip section directories (have _index.md but no index.md) — they're
# Hugo sections, not per-slug notes.
if (entry / "_index.md").is_file() and not (entry / "index.md").is_file():
    continue
```

**Affected linters in this repo (as of 2026-05-13):** `tools/check_garden_fixtures.py` has the fix (applied during garden path-log retrieval slice, commit `862aeb1`). Other section linters (`check_research_fixtures.py`, `check_works_fixtures.py`, `check_library_fixtures.py`) don't yet hit this case because no sub-sections exist under those folders, but they'd need the same fix if one is added.

**When to apply:** Any future slice that adds a `content/<section>/<sub-section>/_index.md` file. Either:
1. Pre-emptively check the section's note linter for `iterdir() + index.md` pattern and add the skip, OR
2. Wait for the inevitable post-build linter failure and fix then (likely catch is `tools/check_*_fixtures.py` reporting "no index.md").

The sibling test for these linters typically doesn't need updating — the skip rule is trivially correct.
