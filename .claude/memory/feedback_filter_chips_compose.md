---
name: Filter chip dimensions compose with AND
description: When a page has multiple filter chip dimensions (tag, flavor, stage, year, etc.), each dimension is independently active and they compose as AND — not single-active-across-dimensions
type: feedback
originSessionId: f650a5e2-2f72-4cc6-b153-672e907bd65a
---
When a section renders multiple filter-chip dimensions, each dimension keeps its own active chip independently and the result is the intersection (logical AND) of all active filters. Don't enforce "single chip active across all dimensions."

**Why:** User's reasoning: "if the user wants budding notes that are part of a given tag, then they should be able to apply both." A knowledge garden (and similar surfaces) treat filtering as a primary verb; cross-cutting questions like "evergreen notes about memory" are exactly what users come to filter for. Single-active across dimensions makes those questions impossible.

**How to apply:**
- Default to independent multi-dimension AND for any filter strip with 2+ dimensions
- Each dimension still has its own "all" reset chip
- Active state is per-dimension, not global
- This supersedes the essays-slice convention (which was single-active); when revisiting essays, make it consistent
- Implementation: JS tracks `{[dim]: activeKey}` map; cards evaluated against intersection
