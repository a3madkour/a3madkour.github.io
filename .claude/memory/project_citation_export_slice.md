---
name: project-citation-export-slice
description: Citation-export slice — merged + pushed 2026-05-14
metadata: 
  node_type: memory
  type: project
  originSessionId: 6cf4b615-49d6-4ba4-93a9-5aac82ce1434
---

Citation export slice shipped to master 2026-05-14, merge `4b2a75e`, pushed to origin. CI step count grew 44 → 46; CSS reached §43; 17th linter pair landed.

**Why:** Post-Phase-8 polish — make essays/garden/research/works (and library rows) export citation metadata for Zotero auto-detect and a user-facing modal with five formats (BibTeX/APA/Chicago/MLA/RIS) plus per-reference cite affordances and a bulk-bib download.

**How to apply:** When extending the cite system later (ORCID meta, DOI integration, bulk-bib for non-essay pages, library-item cite from a leaf RSS, etc.) — start from `layouts/partials/cite/` and `assets/js/cite.js`. The pattern: each scope (article) carries its own `<script class="cite-data">`; `cite.js` walks `closest('article')` to find the right one; modal is a singleton in `baseof.html` re-populated on each open.

Followed-on dependencies / next slices:
- Streams section soft-dependency on Citation export is now satisfied.
- Two stubs filed for next brainstorms: [[project_library_redesign_stub]] · [[project_graph_view_consistency_stub]].
