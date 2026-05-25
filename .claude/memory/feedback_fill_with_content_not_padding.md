---
name: feedback-fill-with-content-not-padding
description: "When a section feels short, prefer more content (more items, larger tiles) over more padding/min-height. Substance over chrome."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d27b9186-f371-40e9-ac80-f9b1a00cfcff
---

When a section looks too short / lacks presence, fill it with MORE content (more items in the data query, larger tiles) rather than with extra padding or `min-height`. Substance over chrome.

**Why:** During the page-sidebar slice, I padded the homepage Research section with `5rem 0 5rem` + `min-height: 65vh` to give it more vertical room (the user wanted the active sidebar label not to switch to Works so quickly). User pushed back: "well don't have it be empty space, add an extra question in the research and more stuff from the garden." Bumping the data query (2→3 questions, 6→10 tiles) AND trimming the padding (5rem→4rem) was the right move.

**How to apply:**
- If a section feels short in v1 fixtures, first check whether the data query is artificially capped (e.g., `first 2`, `first 6`) and consider bumping to a more generous number.
- Use `min-height` only when the data is genuinely thin (empty state) and the section would collapse to nothing.
- Padding is for breathing room between content, not for adding presence to thin content.
