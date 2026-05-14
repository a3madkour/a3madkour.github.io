# Library page redesign

**Status:** Stub — queued for brainstorming.

## Motivation

The current `/library/` umbrella renders four equal-weight cards (Reading / Listening / Playing / Watching). User feedback during the citation-export slice (2026-05-14): "the current card setup is a bit too bland."

Open dimensions to explore in the future brainstorm:

- **Visual aesthetics** — uniform glyph+stats+top-3 cards feel generic; nothing surfaces cover art, texture, or per-section personality.
- **Information density / variety** — every section communicates the same shape of summary (counts + top-3 list). A book gets the same treatment as an album; the page doesn't make use of medium-specific cues (cover ratios, durations, year ranges, etc.).
- **Layout / structure** — 2×2 grid is predictable; no visual hierarchy or flow.
- **Interaction / liveness** — currently static. No "what's active right now" affordance at the umbrella level; visitors have to click into a leaf to see what's being engaged with.
- **Purpose mix** — should the page emphasise (a) historical log, (b) right-now showcase, (c) personal-diary commentary, or (d) some balance? Different purposes demand different surfaces.

## In scope (likely)

- `/library/` umbrella layout
- `layouts/library/list.html` and `layouts/partials/library/umbrella-card.html`
- Possibly cover-thumbnail integration at the umbrella tier
- Possibly new partial(s) for per-section variety

## Out of scope (likely)

- Leaf pages (`/library/{reading,listening,playing,watching}/`) — already polished in the cover-fetch slice. Keep unless the redesign demands changes for consistency.
- New library YAML schema fields (unless brainstorm reveals a genuine need).

## Constraints

- No AI-generated illustrations (per spec §1 hard constraint). New SVGs hand-authored under `assets/images/icons/`.
- WCAG AA accents, AAA body.
- Half-screen-1080p (~960px) breakpoint stays usable.
- No new top-level navigation; library stays the 6th nav item.

## Open questions for brainstorm

1. What's the primary purpose of the page — historical log, right-now showcase, or personal-diary? Or weighted mix?
2. Should covers/art surface at the umbrella tier?
3. Bento-style variable-weight grid (like the essays index) — appropriate here, or too busy?
4. Should each section card have its own visual treatment (different ratio / different glyph treatment / different palette accent)?
5. Is there a "currently engaged with" surface at the umbrella tier (mirroring the leaf-page Currently-active strip)?
6. How does the redesign interact with the cite-this-entry buttons that just landed in each row? (Should the umbrella also surface cite affordances for top items?)

## Process

Pick up with `superpowers:brainstorming` when scheduled. Spec gets fleshed out then; plan drafted only when implementation is queued (per the "design-batch: spec for all, plan only when implementing" rule).
