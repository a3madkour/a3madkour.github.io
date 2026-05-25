---
name: feedback-test-at-half-screen-1080p
description: User runs a tiling window manager and frequently views the site at half-screen on a 1080p monitor (~960px viewport). Design at multiple widths including 960px.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d27b9186-f371-40e9-ac80-f9b1a00cfcff
---

Test responsiveness at half-screen 1080p (~960px viewport) explicitly — not just narrow phone and full desktop. User runs a tiling window manager and routinely tiles the browser to half a 1080p monitor.

**Why:** During the page-sidebar slice, a 1220px breakpoint problem only surfaced when the user tiled the browser to half-screen (~960px), exposing a rail-vs-content collision that didn't show up at 1440p or 800px. User said: "I am using a tiling window manager, I put the page on a 1080p monitor with half the screen."

**How to apply:**
- Default breakpoints to consider: 360px (phone), 768px (tablet), 960px (half-1080p tiled), 1080px (content max-width), 1280px (typical desktop), 1920px (full 1080p).
- When choosing rail/sidebar/marginalia placement, check what happens at 960px specifically — content fills the viewport with no margin, and any fixed-position chrome at the edge collides with content.
- For Hugo dev-server testing, mention "try at half-screen 1080p" in spot-check checklists for any layout slice.
