---
name: reference-works-graph-panel-needs-glyph-sprite
description: Any layout hosting the works graph panel MUST also include works/glyph-sprite.html
metadata: 
  node_type: memory
  type: reference
  originSessionId: d2c8ba83-4c2f-42d9-9eef-24419825f6e3
---

`works-graph.js` renders every graph node with an inline
`<use href="#g-{medium}">` glyph resolved against the `<symbol>`s in
`layouts/partials/works/glyph-sprite.html` (a self-contained `display:none`
inline SVG sprite, one include per page by design).

**Constraint:** any layout that renders `works/graph-panel.html` (or otherwise
runs `works-graph.js`) MUST also include `{{ partial "works/glyph-sprite.html" . }}`
on the same page, or the graph nodes show no icons (the `<use>` references
resolve to nothing — silent, no error). Include it once per page (no
`partialCached` needed; matches the umbrella/standalone pattern). Place it
adjacent to the `works/graph-panel.html` include.

Bit me in the persistent-graph-access slice: Task 5 added the works graph panel
to the 3 works single layouts without the sprite → broken node icons, caught
only at the dev-server spot-check. Relevant for future works-runtime slices
that add more works pages/panels. Research graph nodes are plain shapes (no
glyphs) so research layouts need no equivalent. See
[[project_persistent_graph_access_slice]].
