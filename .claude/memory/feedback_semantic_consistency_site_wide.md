---
name: feedback-semantic-consistency-site-wide
description: "If a visual or interactive primitive has a meaning on the site, it carries that meaning everywhere; deviations must be explicit"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e0e6c7a6-91b5-4722-9141-d7f3ef43db48
---

When a visual or interactive primitive (color token, glyph, button vocab, badge, affordance shape) has been assigned a meaning anywhere on the site, it MUST carry that same meaning everywhere it appears. If a deviation is genuinely necessary, the deviation has to be **explicit** — either via a clearly different visual primitive, or via spec-level commentary explaining why this instance breaks the rule.

**Why:** During the library-redesign brainstorm (2026-05-14), the user caught that `--color-green` had three competing meanings — "finished" status pill, "Related note" Direction-1 internal-nav pill, AND library/playing medium identity tint. A user seeing a green corner-badge on a Hades tile couldn't tell which meaning applied. The same overloading exists for every per-medium tint in the original library spec (burgundy/steel/green/violet all reused semantic colors). The redesign decoupled medium identity (carried by hand-authored glyph shape) from semantic colors (reserved for Direction-1 button vocab + status badges).

**How to apply:**
- Before assigning a new role to a color token, glyph, button style, or badge: search where else it appears. If it already carries a meaning, choose a different primitive (new token, different shape) OR document in the spec why the overload is intentional and how users distinguish the cases.
- During brainstorms and reviews: when proposing a visual decision, name what the primitive already means on the site. The Direction-1 button vocab is the canonical example — burgundy=primary CTA, steel=external nav, green=internal nav + finished, stone=micro-action.
- The principle applies to glyphs too: a glyph used for one medium/concept shouldn't be reused for an unrelated one.
- Related: [[feedback_verify_contrast_ratios]] handles the WCAG side; this rule handles the semantic side.
