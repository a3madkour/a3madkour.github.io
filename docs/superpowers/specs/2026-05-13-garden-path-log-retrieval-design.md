# Garden path-log retrieval — design stub

**Phase:** Post-Phase-8 polish slice (standalone). Not part of Phase 3 elisp work.
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §5.6 (path log).
**Filed:** 2026-05-13, during Phase 8 Slice 3 QA walkthrough.

---

## Problem

The garden currently:

- Persists the visited-notes list in `localStorage` (key `garden-path-log`) OR `sessionStorage` depending on a consent banner choice.
- Shows the **current stack** (the `?stack=` URL state) as a path log breadcrumb at the top of every garden note: `Garden › Current Note   N in stack [clear]`.
- Has **no surface that reads back the persisted visited list** — there is no history page, no "restore session" button, no recently-visited list in the side panel.

The consent banner therefore asks users to opt into a persistence layer that has **no consumer**. The data is written and never read. A user who stores nothing gets the same effective experience as a user who stores everything.

The current "reload a previous stack" path is implicit:
- Use the browser's Back button (each stack mutation is a `pushState`)
- Bookmark a URL with a `?stack=` value
- Share a URL with a `?stack=` value

These work, but they don't use the persisted visited list at all.

## What this slice should add

At least **one consumer of the persisted visited list** so the consent banner has a payoff. Candidates (pick during brainstorm):

1. **`/garden/history/` page** — a dedicated page that lists recent visited notes (with timestamps), sorted newest-first, with click-to-jump-to-note. Read from `localStorage`/`sessionStorage` on page load.
2. **"Recently visited" widget in the garden index** — top of `/garden/` shows the last 5 notes the user has seen + a "see all" link to a full history.
3. **Path-log popover** — the `N in stack` count in the path log becomes a clickable popover that shows the last 10 visited (across stacks), not just the current stack.
4. **Side panel on garden notes** — an inline "Visited recently" rail in the right margin (desktop only) listing the last 5-10 notes outside the current stack.

A combination is also reasonable — e.g., a small "recently visited" widget on `/garden/` (#2) + a dedicated `/garden/history/` page (#1) that the widget links to.

## Constraints to honor (from current implementation)

- Persistence respects the consent state (no read if consent is `unset` — show an "enable history to see this" empty state).
- No analytics. No external services.
- Stays consistent with site privacy stance (data lives in the user's browser only).
- Works offline (no network calls).
- Reduced-motion respected for any new animations.
- Accessible: any new surface gets keyboard nav + screen-reader landmarks.

## Out of scope

- Cross-device sync (deferred indefinitely; site has no auth).
- A timeline graph view of visited notes (visual nicety, defer).
- Editing the visited list (e.g., "remove this note from history") unless the brainstorm surfaces a clear ask.

## Risks

- **No real content yet**: garden fixtures are `Example N`. A history feature exercises semantics that don't matter for fixtures. Real value lands after Phase 3 + actual notes — *but* the existing consent banner is misleading today regardless of content. Two acceptable framings:
  - Fix now (banner has a payoff even if the payoff is hollow against fixture content)
  - Fix after Phase 3 (so the first impression on real content is correct)

## Pointers for whoever picks this up

- Garden stack runtime: `assets/js/garden-stack.js`
- Path log partial: `layouts/partials/garden/path-log.html`
- Consent banner: rendered inline by `garden-stack.js` (look for `path-log-consent` key)
- Storage keys: `CONSENT_KEY = 'path-log-consent'`, `VISITED_KEY = 'garden-path-log'`
- The spec line that motivates a history page: `docs/superpowers/specs/2026-05-03-personal-site-design.md` §5.6 (path log) — currently silent on how the persisted list resurfaces, which is the gap this slice fills.

---

*End of stub. Brainstorm + plan when ready to ship.*
