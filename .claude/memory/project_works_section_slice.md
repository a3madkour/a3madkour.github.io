---
name: works-section-slice-merged
description: "Phase 6 first slice (umbrella + 3 sub-section indexes + per-item pages, runtime deferred) shipped 2026-05-12"
metadata: 
  node_type: memory
  type: project
  originSessionId: ec310218-1708-418e-b53d-565a7a9baa4e
---

Phase 6 first slice. Shipped to master 2026-05-12 (merge `eff9a23`, pushed to origin).

**What shipped:**
- Works umbrella (`/works/`) + three sub-section indexes (`/works/games/`, `/works/music/`, `/works/poetry/`) + per-item page templates for all three.
- 12 fixtures (4 + 4 + 4) covering every status / game_kind / format value, with a round-trip `lyrics_poem ↔ set_to_music` pair between `example-track-with-lyrics` and `example-poem-with-lyrics`.
- Shared `partials/filter-chips.html` reused on all three indexes — games (status / kind / tag), music (format / tag), poetry (collection / tag). Wired via a new 5th multi-entry JS bundle `entry-works.js` → `works.<hash>.js`, page-scoped to `.Section == "works"`.
- CSS §32–§35 (~380 lines, no new tokens).
- Two new CI gates: `tools/check_works_fixtures.py` + `tools/check_works_links.py`. The shared `parse_frontmatter` in `tools/check_fixtures.py` was extended to handle top-level inline flow mappings (`platform_embed: { kind, url }`). `tools/check_filter_chips_config.py` extended with section-path overrides because works lives at `content/works/<sub>/` not `content/<sub>/`. Total Python gates: 15 → 19.
- Stubs (all carry `data-pending`): game iframe embed, music platform iframe, custom audio player, synced-lyrics runtime, audio-pill pulse animation, gif-vs-hero toggle.

**Important quirks discovered during implementation:**
- Hugo reserves BOTH `type` AND `kind` as built-in page attributes — the games enum field was renamed twice: `type` → `kind` (Task 4), then `kind` → `game_kind` (Task 11). The frontmatter field is `game_kind`; the filter chip dim's machine key stays as `"kind"` (short URL semantics). Card data-attribute is `data-kind` for chip JS matching. See `feedback_hugo_reserved_fields.md`.
- Spec amendment: parent §4.19 specified three view tabs (Recent / By collection / By tag) on `/works/poetry/`; this slice replaced that with the shared filter-chips strip for consistency with every other index.

**Spec + plan:**
- `docs/superpowers/specs/2026-05-12-works-section-design.md`
- `docs/superpowers/plans/2026-05-12-works-section.md`

**Follow-up requirements tracked:**
- Works umbrella polish (see [[project_works_umbrella_polish_pending]]) — user found `/works/` bland during the dev-server walkthrough. Type-glyph SVGs from `homepage-v3.html` mockup are the leading candidate visual treatment. Brainstorm at the start of the next Phase 6 slice.
- Runtime slices for the 7 deferred capabilities (iframes, custom audio player, synced-lyrics, etc.) — each scheduled separately as real content lands.

**Why:** Mark Phase 6 progress and the parse_frontmatter extension for future cross-reference. Phase 6 is partial; remaining runtime slices + umbrella polish still pending.

**How to apply:** When citing the slice in future status updates, refer to it as "Phase 6 first slice (2026-05-12)". When discussing Hugo frontmatter field names for works fixtures, remember `game_kind` (not `type`, not `kind`).
