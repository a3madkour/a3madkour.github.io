---
name: chrome-routing-follows-scope
description: "When a feature's scope narrows to one section (\"only essays\"), check site chrome (header icons, nav, footer) for routing that contradicts the scope — surface this as a brainstorm question, not a post-hoc fix"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: db0fe890-9229-4849-89d1-9d213bd28e0d
---

When a feature's scope is narrowed to a single section (e.g., "RSS pretty-render only for essays," "search only across essays"), check chrome surfaces (header icon links, nav, footer, breadcrumbs) for routing that still references the broader-scope surfaces. Surface this as a brainstorm question — *not* as a post-hoc adjustment after the user notices it in browser verification.

**Why:** During the RSS XSL pretty-render brainstorm (2026-05-13), the user answered "essays only" to the scope question. I designed the XSL + linter scope guard for essays only, but left `layouts/partials/header.html`'s per-section RSS icon routing untouched (it still switched to `/garden/index.xml` on garden pages, `/index.xml` elsewhere). The user caught it during Task 5 browser check and said "this is not what I wanted, I wanted the RSS feed to be only for essays regardless of where I am." Fixed in commit `9685dfc` — header now always links to `/essays/index.xml`. Lesson: "only X" usually means "X is the only one promoted in chrome too," not just "the polish only applies to X."

**How to apply:** During the brainstorm `Which feeds should the stylesheet cover?`-style question, add a follow-up: `Should chrome (header / nav / footer) routing also collapse to that scope, or keep the per-section dynamism for users who navigate the other sections?` Same applies to other content surfaces — search filters, social-share links, footer feed-discovery links, anything in the persistent chrome that surfaces section-specific content.

See also: [[filler-text-only]], [[deferred-features-stay-visible]] — same family of "make the design explicit about cross-cutting concerns."
