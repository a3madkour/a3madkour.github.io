---
name: When planning a class rename, grep the whole codebase first
description: Before writing the file list for a CSS class rename, run grep -r to find every usage — don't trust the obvious files only
type: feedback
originSessionId: 7ac64b5d-36cb-43d9-8d56-dc2340b28e78
---
When planning a CSS class rename refactor, grep the entire codebase for the class name before writing the implementation plan's file list. The "obvious" set (the section it lives in + the directly-referencing template) almost always misses a usage site, and the miss causes a silent functional regression.

**Why:** In the Phase 5 Slice 2 plan (`docs/superpowers/plans/2026-05-11-research-graph.md`), Task 1's file list named four files for the `.garden-graph-*` → `.graph-*` rename: `main.css §27`, `partials/garden/graph-panel.html`, `garden/list.html:59`, `garden-graph.js`. A fifth usage in `partials/garden/path-log.html:14` was missed entirely. The code reviewer caught it, but only after the implementer had committed. The bug was that the ⊞ Graph button on every garden NOTE page was unstyled, had no click handler, and never updated `aria-expanded` — because the JS queried `.graph-toggle` and the path-log button still said `.garden-graph-toggle`. The garden index toggle worked fine; the regression was specifically on note pages.

**How to apply:** When the next class-rename or refactor task arrives, run `grep -rn "<old-class-name>" .` BEFORE drafting the file list. Compare grep output against the file list — every match should either be in the list, explicitly excluded with a reason (e.g., "string literal in storage key, not a selector"), or clearly out of scope. Apply the same to JS `querySelector` strings, HTML class attributes, and aria-controls/labels-by id references. The cheapest fix is at planning time; finding it during review costs ~3 extra commits (regression catch, fix, follow-up consistency).
