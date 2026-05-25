---
name: filter-chips-data-tags-must-be-space-delimited
description: assets/js/filter-chips.js splits the tile data-tags attribute on whitespace (/\s+/) — comma-delimited values silently break every tag chip match
metadata: 
  node_type: memory
  type: reference
  originSessionId: aa1fdad1-d521-460c-8929-906ba6d65966
---

`assets/js/filter-chips.js` (line ~57) does:

```js
const tags = (card.getAttribute('data-tags') || '').split(/\s+/).filter(Boolean);
```

Then `tags.includes(wanted)` for each active chip key. If a tile template emits `data-tags="example,demo"` (comma-delimited), the split yields ONE token — `"example,demo"` — and `includes("example")` returns false. Result: chip looks active, zero tiles pass.

**The contract is space-delimited.** Every tile partial that wants to participate in filter-chips MUST emit `data-tags="{{ delimit $tags " " }}"` (space) — not comma.

**How to spot it:** active tag chip shows nothing. Inspect a tile, confirm `data-tags="a,b"` vs `data-tags="a b"`.

Bug seeded in the Phase 6 first slice — all four works templates (`tile.html`, `game-card.html`, `music-row.html`, `poem-row.html`) used comma; fixed in the umbrella polish slice on 2026-05-12. The garden + essay partials use space and have always worked.

Related: [[project_works_umbrella_polish_slice]] uncovered this when the user tested tag filtering on the new Bento umbrella.
