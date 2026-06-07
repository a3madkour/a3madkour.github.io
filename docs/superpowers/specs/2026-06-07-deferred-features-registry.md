# Deferred Features Registry

**Date:** 2026-06-07
**Status:** Living registry. Durable home for the "deferred features" list (previously inline in CLAUDE.md). When CLAUDE.md drifts or is rewritten, this file is the source of truth.

**Scope:** every capability that has been intentionally deferred — not "things we forgot", but "things we agreed to defer until a concrete trigger". Each item carries the trigger that would unblock implementation and the existing site state that documents the deferral.

**Companions:**
- Active queue: [`2026-06-07-polish-and-bugfix-roadmap.md`](2026-06-07-polish-and-bugfix-roadmap.md) — the 8 in-flight / near-term tiers.
- Phase 3 sub-project decomposition: parent design spec [`2026-05-03-personal-site-design.md`](2026-05-03-personal-site-design.md) §14.

---

## Rules for this registry

1. **Trigger-gated, not date-gated.** Each entry names the *trigger* — "first essay needs X", "real audio recording lands", "third copy of duplicated code", "author hits friction Y". No fixed delivery dates.
2. **Fixture seed shows the deferral.** Most deferrals are exercised by an obviously-dummy fixture so the round-trip lands the moment a real implementation arrives. The "Fixture / current state" column documents what's already in the repo.
3. **Promotion path.** When a trigger fires, the entry graduates from this registry to a slice spec under `docs/superpowers/specs/` (or `~/dotfiles/.../specs/` for elisp-side work) and ultimately to a `project_*_complete.md` memory file.
4. **Add, don't remove.** When an item ships, *mark it shipped* with a link to the completing slice rather than deleting it. Keeps history readable.

---

## Runtime / interactive capabilities

| Capability | Trigger | Fixture / current state |
|---|---|---|
| **KaTeX math rendering** | First essay author actually wants math rendered (not just `has_math` body lint). | Essay fixture #2 has `has_math: true`; `tools/check_math.py` enforces the source/body coupling; no client-side render yet. |
| **Scroll-synced video runtime** | First essay needs video that progresses with prose scroll. | Essay fixture #4 has `has_video_sync: true`; `video-sync` shortcode is a stub. |
| **Per-page interactive widgets + per-page JS bundle convention** | Sub-project E (explorables) brainstorm. See roadmap Tier 8 #29. | Essay fixture #5 has `has_widgets: true`; `widget` shortcode stub emits `data-pending`. |
| **Game iframe embed** (itch / Bitsy / WebGL) | First game fixture has a real `embed_url`. | Game fixture #1 carries `embed_url`; `works-embed-stub` anchor exists. |
| **Music platform iframe** (Bandcamp / SoundCloud / YouTube) | First real music release in `data/music.yaml`. | Music fixtures #1 / #2 / #4 ride `works-audio-link` text-link form only. |
| **Custom audio player** | When the platform-iframe approach (above) proves insufficient. | `works-player-stub` block reserves the slot. |
| **Synced-lyrics runtime + two-column lyrics layout** | First real lyrics ↔ music pairing. Time-synced poetry runtime already covers the parser → lyrics slice reuses `partials/works/synced-text-parser.html`. | Music fixture #2 ↔ poem fixture #1; `synced-lyrics-stub` block; `lyrics` shortcode is a no-op. |
| **Audio-pill pulse animation** | When real audio plays — animation hangs off the audio-pill element that already renders. | Poem-page audio-pill renders without animation. |
| **Audio-driven playback QA** for synced poetry | Author records a reading (no AI-generated audio per project constraints). | `example-poem-synced` uses a dummy `audio_url`; the audio→animation fallback path is exercised live. |

## Visual polish

| Capability | Trigger | Fixture / current state |
|---|---|---|
| **Gif-vs-hero toggle on game cards** | Real animated game-asset GIFs land in the works dir. | No-op; current cards use SVG glyphs. |
| **Figure lightbox** | First essay needs detail inspection on a figure. | Figures render inline; click does nothing. |
| **Code highlighting palette swap from Dracula** | Post-Phase-2 polish; pick when palette consistency annoys. | Dracula is current `chroma` style. |
| **Print stylesheet** | Phase 8 polish; queued. | No `@media print` rules anywhere. |

## Library / works extensions

| Capability | Trigger | Fixture / current state |
|---|---|---|
| **Library cover thumbnails — live IGDB / TMDB paths** | Real library items needing covers + author appetite for elisp wiring. | YAML `extras` accepts `isbn` / `mbid` / `igdb_id` / `tmdb_id` / `cover_url` / `cover_file`; 8 PD/fair-use thumbnails seeded. |
| **Last.fm scrobble counts on `/library/listening/`** | Author wants ambient listening-history surface. | Listening YAML `extras` ready for it. Spec §4.23 documents the deferral. |
| **Library RSS feeds** | Reader asks. | Essays + garden have RSS; works + library do not. |
| **`/library/graph/` constellation** | Author appetite shows up. | Parent spec did not request a graph view. |

## Authoring / metadata extensions

| Capability | Trigger | Fixture / current state |
|---|---|---|
| **About Now widget** | See roadmap Tier 6 #25 — promoted to near-term. | About template has a placeholder slot. |
| **ORCID `citation_author_orcid` meta** | When an ORCID exists. | `essay-references.html` scaffolds the slot. |
| **Library item cite export** | Reader appetite. | Library items already have ISBN / MBID / IGDB / TMDB external metadata. |
| **DOI / CrossRef integration** | DOI registrar in scope. | `data/citations.yaml` accepts a `doi:` field. |
| **Bulk export** (single `.bib` for all refs on a page) | Reader feedback. | Per-cite export works today. |
| **Bilingual / Arabic-aware citation formats** | First real Arabic content lands. | English-only `data/citations.yaml` shape today. |

---

## Items that GRADUATED to the roadmap (2026-06-07)

These were on the deferred list but the user prioritized them into the active tier roadmap during the 2026-06-07 reordering session:

- **About Now widget** → Tier 6 #25 in [`polish-and-bugfix-roadmap.md`](2026-06-07-polish-and-bugfix-roadmap.md). Stays cross-linked here for navigation.
- **Per-page interactive widgets** → folded into sub-project E (Tier 8 #29 in roadmap). Stays cross-linked here.

---

## Items that SHIPPED (stay here for history; with shipped-pointer)

(Empty at registry birth — populate as deferrals ship.)

---

## How to use this file

- **Adding a new deferral.** Append to the appropriate section with a single-row table entry: capability name, concrete trigger, fixture-or-current-state pointer.
- **Promoting to active work.** Cross-link to the new slice spec under the "GRADUATED" section; don't delete the original row.
- **Shipping.** Move to "SHIPPED" with a link to the `project_*_complete.md` memory file.
- **Stale-trigger audit.** Periodically (when the roadmap empties) scan triggers and ask: does this still match author intent? Outdated triggers get rewritten, not silently deleted.
