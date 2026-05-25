---
name: visual-companion-for-visual-designs
description: "When a design choice is visual (layout, UI placement, mockups), use the brainstorming visual companion — don't just describe it in text"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2586b61b-7278-423f-b331-1090fe330889
---

When brainstorming and the next decision is genuinely visual — UI placement, mockup, wireframe, layout comparison — push to the visual companion (`scripts/start-server.sh --project-dir ...`) and show wireframes. Don't just describe the layout in prose.

**Why:** Mid-session 2026-05-13 the user reminded me: "show me a wireframe when designs are visual" after I described a streams-section UI in text only. They'd already accepted the visual companion earlier and expected me to use it whenever a question was visual. The reminder happened during Feature 4 brainstorm; I had defaulted to terminal text for site-rendering chunks even though the chunks contained clearly visual content (live pill placement, archive cards, embed UI).

**How to apply:** Before each brainstorm chunk, ask: "would the user understand this better by *seeing* it?" If yes — and the visual companion is active or trivially restartable — push HTML wireframes. Keep using terminal questions for conceptual/scope/A-B-C-text decisions. The companion is a tool, not a mode, but treat visual chunks of design walkthroughs as default-visual.

Server file: `~/.claude/plugins/cache/claude-plugins-official/superpowers/<version>/skills/brainstorming/scripts/start-server.sh`. Auto-exits after 30min idle; restart cheaply when needed. `.superpowers/` already in `.gitignore`.
