---
name: feedback-no-ai-visuals-in-mockups
description: "Even brainstorm mockups (gitignored) must not contain AI-authored SVGs, paths, or illustrations — use existing assets, CSS shapes, or text stand-ins"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e0e6c7a6-91b5-4722-9141-d7f3ef43db48
---

The spec §1 hard constraint ("No AI-generated illustrations") applies to brainstorm mockups too, not just the shipped site. Even though `.superpowers/brainstorm/` is gitignored and never reaches production, mockups still represent visuals to the user — and an AI-sketched glyph in a mockup can subtly drift the design conversation toward proportions/shapes Claude invented.

**Why:** During the library-redesign brainstorm (2026-05-14), Claude inline-authored four SVG path strings (book/music/game/clapper) as quick sketches for a glyph-comparison mockup. The user caught it ("did you write the svg yourself?") and chose the strict rule: even mockups stay clean of AI-authored visuals. Mockup sketches that look "fine enough" can survive into spec recommendations the user hasn't reviewed at the asset level.

**How to apply:**
- When building a brainstorm mockup that needs a glyph, icon, illustration, or any other graphic asset, use one of:
  1. **Existing repo asset** referenced via `<use href="#sym">` after inlining the actual SVG from `assets/images/icons/`. Audit that the asset matches what's needed.
  2. **CSS-shape placeholder** (circle / rect / pseudo-elements with borders / colored fill). Geometric primitives only.
  3. **Text stand-in** — "[book glyph]" / `<span class="badge">B</span>` / letter discs. Clearly placeholders, not drawings.
- If a comparison genuinely requires a *new* glyph that doesn't exist yet, describe it in text and ask the user to author or sketch it themselves; don't draw it.
- Applies to brainstorm-companion HTML, embedded mockups in spec/plan markdown, and any other "rendered for the user" surface — even ephemeral ones.
- Related: [[feedback_filler_text_only]] is the prose-side equivalent; this is the visual-side equivalent.
