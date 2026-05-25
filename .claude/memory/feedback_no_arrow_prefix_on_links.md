---
name: No arrow prefix on link labels
description: Never add "→" arrows to link labels — leading OR trailing, content OR chrome. Plain text reads cleaner; the link's own color + underline carries the affordance signal.
type: feedback
originSessionId: a1cf2d3b-0e81-4672-8dfa-5d3f70e10716
---
**Rule:** Link labels should NEVER carry a `→` arrow. Not leading (`→ source`), not trailing (`Reading history →`, `full history →`, `history →`), not anywhere. Plain text only.

**Scope (updated 2026-05-13):** This rule now applies to BOTH content links AND chrome links. Earlier the rule allowed chrome ("Open graph", "history →") to use symbols; the user clarified during the garden path-log retrieval walkthrough that trailing `→` flourishes are unwanted in chrome too. The only acceptable glyph-bearing affordances are functional state indicators (e.g., `⊞ Graph` as a toggle icon-prefix, `▾` to indicate a dropdown trigger). Plain words for navigation links: `Reading history`, `full history`, `history`, `source`, `related note`, `view note`.

**Why:** Caught originally during QA of the citation hover-card slice (2026-05-12) — the leading `→` added visual clutter inside hover-cards. Re-affirmed during the garden path-log retrieval browser walkthrough (2026-05-13): the user explicitly asked for all `→` arrows to be removed (widget "Reading history →", popover "full history →", path-log chrome "history →"), and asked me to commit the rule to memory more strongly. The arrow's job (signalling "this is a link / goes somewhere") is already done by the link's color + underline-on-hover.

**How to apply:**
- Strip any literal `→` from link labels — drop the arrow entirely, do NOT replace with a different glyph.
- Includes labels in: references lists, hover-cards, sidenote/citation popups, widget actions, popover actions, path-log strip, footer, navigation, breadcrumbs.
- Glyphs that AREN'T arrows but signal state (`▾` for expanded, `⊞` for grid view, `›` as breadcrumb path-separator) may stay — they're functional indicators, not link-affordance flourishes.
- When designing a new content surface with affordance links, explicitly check this rule against the partial templates BEFORE authoring — easy to miss in long specs.

**Lapses to learn from:**
- 2026-05-12 (library section): authored as "→ my notes" / "→ original" in `partials/library/row.html` + `currently-active.html`; fixed during dev-server spot-check.
- 2026-05-13 (garden path-log retrieval, this session): authored trailing `→` flourishes on three new link types (widget view-all, popover view-all, path-log chrome) despite the rule already existing. User caught all three during browser walkthrough. Lesson: trailing-arrow lapses are just as common as leading-arrow lapses; the original memory only mentioned "leading" which I read literally.
