# Personal Site — Design Spec

**Project:** `a3madkour.github.io` rebuild
**Author:** Abdelrahman Madkour (the user)
**Spec date:** 2026-05-03
**Status:** Design phase complete; implementation not yet begun.
**Source brainstorm:** Conducted via `superpowers:brainstorming` skill with visual companion across one extended session on 2026-05-03. Mockup HTML files in `.superpowers/brainstorm/1178775-1777859433/content/` (gitignored).

---

## 0. Context for future Claude sessions

If you're picking this up cold, read this section first.

### What this document is

The agreed design for a complete rebuild of the personal site at `a3madkour.github.io`. The pre-rebuild site exists in this repo (a Hugo + Tailwind v4 setup; see `CLAUDE.md` for that state). This spec describes the **target** state, not the current one. No implementation has happened against this spec yet.

### What's been decided vs what hasn't

**Decided** (locked, change only with explicit user approval):
- Visual identity (typography, color palette, dark/light mode, accessibility policy)
- Content architecture (top nav, every section's structure, navigation patterns)
- Data model and authoring contract (org-mode shape, BibTeX scope, frontmatter conventions)
- Tech stack (drop Tailwind, vanilla CSS+JS, Pagefind for search, no analytics, no comments)
- Build pipeline (org → ox-hugo + custom elisp → Hugo → GitHub Pages)
- Per-page layouts (homepage, about, essays, garden, research, works, library, search modal)
- CI gates (Lighthouse a11y, contrast checker, build smoke test, required-data check)

**Deferred** (acknowledged, addressed later):
- Special line-by-line poetry presentation (v2)
- Auto-sync lyrics for vocal music (Whisper-based, optional workflow)
- `/references/` browse page (only if needed)
- Comments via Giscus (only if ever)

**To be defined during implementation:**
- Exact CSS file structure (single `main.css` vs split modules — implementation choice)
- Specific JS module organization within `js.Build` bundling
- Bib field conventions for non-academic media (BibLaTeX `@misc` with custom fields — pattern is clear, exact fields will emerge)

### Where to find supporting artifacts

| Artifact | Location |
|---|---|
| Pre-rebuild site state | This repo, master branch; see `CLAUDE.md` |
| Visual mockups (full HTML, real fonts/colors) | `.superpowers/brainstorm/1178775-1777859433/content/*.html` (gitignored — preserved locally on the user's machine) |
| Memory file: pacing feedback | `~/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/feedback_close_architecture_before_visual.md` |
| Memory file: contrast verification habit | `~/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/feedback_verify_contrast_ratios.md` |
| Memory index | `~/.claude/projects/.../memory/MEMORY.md` |

### User context (from brainstorm)

- Heavy Emacs / org-mode / org-roam user; treats the org-mode authoring layer as load-bearing
- Games researcher; writes essays + research papers; makes games, music, poetry as creative output; consumes books/music/games as media
- Wants the site to be a "representation of me on the internet" — collage of professional + personal expression, with the **blog (long-form writing) centered**
- Hard constraints: **no AI text, no AI illustrations** (any AI use limited to: site code, app code, code for interactive explorables)
- Wants minimal tech stack — open to dropping any dependency that doesn't earn its weight
- "Words are mine; not generated" appears in the site footer as an explicit claim

### Pacing feedback (recurring during this brainstorm — preserve in any continuation)

- The user prefers closing architecture/IA threads completely before any visual or implementation work. They corrected me twice during the brainstorm for jumping ahead. **Always confirm priority order before advancing.**
- Cite WCAG ratios precisely, never estimate. They caught one inflated number.
- They use `:LAST_MODIFIED:` (not `:LAST_UPDATED:`) as their existing org property convention. Honor that exact spelling.

### Next step after this spec

Per the brainstorming skill flow:
1. User reviews this doc
2. If user approves: invoke `superpowers:writing-plans` to produce an implementation plan
3. The plan breaks the spec into atomic, executable tasks across the implementation phases listed in §14

---

## 1. Project goals & constraints

### Primary goal

A personal website that serves as the user's representation on the internet, centered on long-form writing with interactive/explorable elements (Bret Victor / Distill / Ciechanowski lineage), supported by a Zettelkasten-style knowledge garden, ongoing research surface, and creative output (games / music / poetry).

### Content priorities, ranked

1. **Long-form essays** with interactive/explorable explainer elements — the centerpiece
2. **Research portfolio** — active questions, ongoing work, supporting notes
3. **Personal archive of notes / Zettelkasten / knowledge garden**
4. **Creative output** (games, music, poetry)

### Hard constraints

- **No AI-generated text** anywhere on the site
- **No AI-generated illustrations** anywhere on the site
- AI is permitted only for: site code, accompanying app code, code for interactive explorables
- **Minimal tech stack** — drop dependencies that don't earn their weight
- **Privacy by org-export boundary** — content not exported never reaches the site
- **Accessibility**: WCAG 2.1 AAA for body text, AA for accents; CB-safe palette; never color-only meaning

### Authoring constraint

All content is authored in **org-mode + org-roam**, exported via **ox-hugo** to Hugo markdown (or templated HTML for richer pages). The site implementation must work with the org export pipeline; any content-side feature is gated by what ox-hugo can produce or what custom elisp can be written to produce.

### Visual North Star

Maggie Appleton's site (`maggieappleton.com`) for warmth and structural patterns (TOC, sidenotes, garden tiles), Acacia Magazine (`acaciamag.com`) for typographic literary feel, Distill.pub for interactive-content support. Synthesized into a cohesive identity — see §2.

---

## 2. Visual identity (locked)

### Typography

| Role | Family | Notes |
|---|---|---|
| Body | **Petrona** (Google Fonts) | Warm transitional serif; selected for legibility + character. Italic has strong personality. |
| UI / sans | **Inter** | Headers, metadata, labels, navigation, buttons. |
| Code / mono | **JetBrains Mono** | Code blocks, inline code, timestamps, technical labels. |

CSS family fallback chains:
```css
--font-body: "Petrona", Georgia, serif;
--font-ui: "Inter", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
```

Font loading: `<link rel="preconnect">` to `fonts.googleapis.com` + `<link rel="stylesheet">` for the three families with the weights/styles used (Petrona regular/600/700/italic; Inter 400/500/600; JetBrains Mono regular). Use `font-display: swap`.

### Color palette

**Cool stone** base in light mode, **deep** charcoal in dark mode. Burgundy primary accent, deep steel secondary accent. All values verified against WCAG.

```css
/* Light mode (default + system-light) */
--color-stone:     #eeeeea;   /* primary background */
--color-ink:       #1c1a17;   /* body text — 14.93:1 AAA */
--color-ink-soft:  #5a564f;   /* secondary text */
--color-ink-fade:  #9a958e;   /* tertiary / metadata */
--color-rule:      #d4d3cd;   /* dividers, borders */
--color-tile:      #fdfcf8;   /* card / surface fills */
--color-burgundy:  #6b1f2c;   /* primary accent — 9.72:1 AAA */
--color-steel:     #1e4060;   /* secondary accent — 9.22:1 AAA */

/* Dark mode (system-dark or .dark on <html>) */
--color-stone:     #181818;   /* primary background */
--color-ink:       #e2e2dd;   /* body text — 13.66:1 AAA */
--color-ink-soft:  #b0aca0;   /* secondary text */
--color-ink-fade:  #7a7770;   /* tertiary */
--color-rule:      #333;
--color-tile:      #2a2a2a;
--color-burgundy:  #d65a6a;   /* primary accent — 4.68:1 AA-body / AAA-large */
--color-steel:     #7eafd0;   /* secondary accent — 7.55:1 AAA */
```

Implementation: theme switch by toggling a class or `data-theme` attribute on `<html>`. Default to `prefers-color-scheme` on first visit; user override persists in `localStorage`.

### Contrast policy

- **Body text**: AAA target (≥7:1). Inks/papers always meet this.
- **Headings, links, accents**: AA minimum (≥4.5:1 normal, ≥3:1 large), AAA where the hue allows.
- **Dark-mode burgundy `#d65a6a`**: 4.68:1 — passes AA for body, AAA for large text. Acceptable because **burgundy is never used for body paragraphs** in our system; only headings, accents, and links (which are inherently larger or bolder).
- **Status indicators always dual-encoded**: color + shape + label. Color alone is never load-bearing for meaning.
- **CB-safe pairing**: burgundy + steel chosen because red/burgundy + blue/steel is unambiguous in deuteranopia, protanopia, and tritanopia simulations.

### Illustration approach (B-narrow)

A small set of **hand-doodled SVG marks** done once, never updated. **No AI**, no per-post illustrations, no per-piece custom artwork.

The set:
- Growth-stage icons: **seedling** (small sprout), **budding** (slightly more leaves), **evergreen** (tree)
- Section divider doodles (one or two variants)
- Decorative hero mark on homepage (geometric / organic shape)
- Game/music/poem type-glyphs for the homepage Studio strip:
  - **Game**: gamepad outline (D-pad + face buttons)
  - **Music**: eighth-note
  - **Poem**: feather/quill

Art direction: thin strokes (~1.5px), monochromatic (uses `currentColor`), small (12–32px display size). Hand-drawn-feeling but not precious.

### Mode behavior

- Default: respect `prefers-color-scheme` (system)
- Toggle button in header (icon: sun-with-rays SVG)
- Override stored in `localStorage`; on next page load, if override exists it wins over system preference
- `prefers-reduced-motion` respected: no large position animations, only fades

### Per-element conventions

- Links: underlined by default, text-underline-offset 3px, decoration-thickness 1px, hover thickens to 2px
- Body line-height: 1.6
- Reading column max-width: 720px (~50–60 chars per line at body size)
- Section dividers: 1px solid `--color-rule`
- Card surfaces: 1px solid `--color-rule`, border-radius 10–12px, hover transitions border-color to accent
- Focus states: 2px outline in `--color-burgundy`, 2px offset

---

## 3. Content architecture (locked)

### Top navigation (5 items)

```
a3madkour    Essays    Garden    Research    Works    About    [RSS] [Theme]
```

Plus icon buttons in header: **RSS** (orange-tinted RSS icon, links to `/index.xml`), **Theme toggle**.

### Top-level paths NOT in main nav

- `/library/` — consumption umbrella (reading/listening/playing). Reachable from About, homepage Currently widget, and footer.
- `/colophon` — site metadata. Reachable from footer.

### Section table

| Path | Role | URL pattern | Backed by |
|---|---|---|---|
| `/` | Homepage | `_index.html` | hand-rolled |
| `/essays/` | Long-form posts (the centerpiece) | `/essays/<slug>/` | org subtrees → page bundles |
| `/garden/` | Knowledge garden — concept + media notes mixed | `/garden/<slug>/` | org-roam notes |
| `/garden/topics/<slug>` | Curated topic maps | hand-curated org files | |
| `/research/` | Research questions hub | theme cards | |
| `/research/themes/<slug>/` | Theme page (may absorb a Garden topic) | org file with optional `garden_topic_ref` | |
| `/research/questions/<slug>/` | Question hub page | org-roam node with sub-question children | |
| `/works/` | Creative output umbrella (3-section overview) | `/works/_index.md` | |
| `/works/games/` | Games index | game cards | |
| `/works/games/<slug>/` | Per-game page (with embed) | org-roam + bib | |
| `/works/music/` | Music index | list rows | |
| `/works/music/<slug>/` | Per-music page (player + tracks + connections) | org-roam + bib | |
| `/works/poetry/` | Poetry list (3 view tabs: Recent / By collection / By tag) | org-roam | |
| `/works/poetry/<slug>/` | Per-poem page (simple v1) | org-roam | |
| `/about/` | Bio + Now + Where + Connect + Colophon | single org file | |
| `/library/` | Consumption overview (3-card umbrella) | filtered view of garden notes | |
| `/library/reading/` | Books — `:MEDIA_TYPE: book` filter | data-driven from `data/reading.yaml` | |
| `/library/listening/` | Music — `:MEDIA_TYPE: album` filter | `data/listening.yaml` | |
| `/library/playing/` | Games — `:MEDIA_TYPE: game` filter | `data/playing.yaml` | |
| `/index.xml` | RSS feed | Hugo built-in | |

### Garden vs Library distinction (critical concept)

Garden notes have two flavors:

1. **Concept notes** — no `:ROAM_REFS:`, no `:MEDIA_TYPE:`. About ideas.
2. **Literature/media notes** — `:ROAM_REFS:` joins to a bib entry, `:MEDIA_TYPE:` declares what kind of thing.

`/garden/` shows all notes (with optional filter by flavor).
`/library/` is a **filtered view** of flavor 2 — same notes, different presentation. Library rows link to the canonical Garden URL.

### Library types vs Reference types

```
LIBRARY MEDIA_TYPE values (appear in /library/)
  book, album, track, game, film, series

REFERENCE MEDIA_TYPE values (appear only in /garden/, not /library/)
  paper, video, article, talk

CONCEPT (no :MEDIA_TYPE:)
  Just an idea note. No bib link required.
```

### Privacy

Privacy is enforced **at the org export boundary**:
- `:noexport:` tag on a subtree (or any org-roam node) excludes it from ox-hugo export
- Strict mode of the freshness gate also requires explicit `:LAST_MODIFIED:` — missing means export blocked
- The site has no concept of "private content" — anything not exported simply doesn't exist on the site

### Works vs Library (creation vs consumption)

| Made by user | Path |
|---|---|
| Games I built | `/works/games/` |
| Music I made | `/works/music/` |
| Poetry I wrote | `/works/poetry/` |

| Consumed by user | Path |
|---|---|
| Books I read | `/library/reading/` |
| Music I listen to | `/library/listening/` |
| Games I play | `/library/playing/` |

These are parallel, not overlapping. A game I made appears in `/works/games/`; a game I play appears in `/library/playing/`.

---

## 4. Per-page designs

Each subsection summarizes the layout. Visual mockups live in `.superpowers/brainstorm/1178775-1777859433/content/`.

### 4.1 Homepage (`/`)

**File:** `.superpowers/brainstorm/.../content/homepage-v3.html` (final)

Section order:
1. **Header** — brand, nav, RSS button, theme-toggle
2. **Hero** — name (Petrona 700, ~3.2rem), one-paragraph positioning (max ~640px), small SVG mark (geometric/organic, color: burgundy)
3. **Currently widget** — "Currently" label-row with pulse dot + timestamp; three lines (reading / listening / playing) each with verb (gray), italic title, "by …" creator, optional spoiler flag (burgundy text), "all X →" right-side link
4. **Essays** — section header with "All essays →" link; **always-shown featured essay** (large card with eyebrow, title, summary, meta, hero-illo SVG); 3-column grid of recent essay cards (title, summary, meta)
5. **Research (moved up)** — section header; 2-column grid of active question cards with burgundy left-rule, status pill, theme name, sub-question/note counts, framing line
6. **Two-column section: Garden + Studio**
   - Left: "From the Garden" — 2-column grid of 6 note tiles (growth stage SVG icon, title, "tended Xd ago")
   - Right: "Lately, in the studio" — list of 4 work rows (gradient type-badge with SVG glyph, title, sub-line of metadata, right-aligned path indicator)
7. **Footer** — colophon line ("Built with Hugo / set in Petrona & Inter / **Words are mine; not generated**"), social links (GitHub / Bluesky / Email)

Hero illustration on featured essay: SVG with circles + curved paths; uses burgundy + steel. Per-essay illustration optional (frontmatter `hero` field; if absent, no illo).

### 4.2 About (`/about/`)

**File:** `.superpowers/brainstorm/.../content/about-page.html`

Narrow column (max ~720px). Sections:
1. **Hero** — name + role line ("games researcher, writer, occasional maker of music and poems") + pronouns/location + portrait placeholder (no AI; user provides photo or hand-drawn avatar OR omits)
2. **Bio** — 3 paragraphs of long-form
3. **Now** — `/now` page tradition. Pulled from `data/now.yaml`. Sections: Reading / Working on / Listening / Wondering. Each section has its own `:LAST_MODIFIED:` and a freshness threshold (14 days for Now). Renders as `which → what` rows.
4. **Where** — Affiliations (lab, university, etc.) + "Other places I keep things" (CV, Google Scholar, ORCID, DBLP)
5. **Connect** — Email (preferred for substantial things), GitHub, Bluesky, Mastodon, RSS, itch.io — each with role-of-each labels
6. **Colophon** — built-with, authored-in (Emacs + org-mode + org-roam + ox-hugo + org-cite + org-roam-bibtex), set-in (fonts), hosted-on, **"No AI wrote any text or made any illustration on this site"** claim, privacy disclosure

Footer: `© year · CC BY-NC-SA 4.0 (writing) · MIT (code) · RSS · Sitemap`.

### 4.3 Essays index (`/essays/`)

**Layout:** variable-tile grid (Bento-style). Each essay's frontmatter sets `tile_size: large | medium | small` and/or `featured: true` (causes 2x wide tile). Auto-promote rules:
- Essays with hero illustrations get taller tiles (`grid-row: span 2`)
- Featured essays get 2x wide
- Recent essays in active series stay larger

Filter chips at top: by tag, by series, by year. Sort: chronological reverse.

### 4.4 Essay post (`/essays/<slug>/`)

Page bundle. Center column for body (max ~720px). Optional left-rail TOC (auto-hide when narrow viewport). Optional right-side popup sidenotes/footnotes.

Capabilities (any post can opt into any of these via frontmatter):
- TOC (auto from H2/H3)
- Sidenotes (right side, popup style — Tufte CSS pattern)
- Footnotes (numbered, bottom of post or popup-on-click)
- Citations (inline `[cite:@key]` → hover-card with title/authors/year + "→ original" + "→ my notes" if note exists; references list at end)
- Math via KaTeX
- Code blocks with syntax highlighting (Hugo's chroma; current Dracula style is a placeholder, may swap)
- Embedded interactive widgets (per-post JS modules in the page bundle, loaded via `js.Build`)
- Scroll-synced video (vanilla `IntersectionObserver` + `video.currentTime`)
- Series navigation (prev/next + index)
- Tags (cross-cutting)
- Figures with captions + lightbox
- Spoiler blocks (rare in essays, supported)

### 4.5 Garden index (`/garden/`)

**Files:** `.superpowers/brainstorm/.../content/garden-interaction-wireframe.html`, `garden-interlinking.html`

Primary browse: **curated topic maps (B)**. Each topic = framing paragraph + tile grid of notes.

Filter strip at top:
- Tag chips (any tag): all / [tag1] / [tag2] / …
- Note flavor: all / concepts / media / references
- Stage: all / seedlings / budding / evergreen
- "Open graph" toggle (top-right) → reveals graph panel

Below: topic sections. Each topic shows topic title, framing, and 4-column tile grid. Tile contents: growth-stage icon + title + "tended Xd ago".

### 4.6 Garden — graph panel (toggleable)

**Implementation:** d3-force, ~30KB.

When opened: ~280px right-rail panel slides in from right. Content:
- Header: "Graph · N nodes" + close button
- Filter strip: local / tags / stage / time
- SVG with force-directed layout
- Nodes: circles. Color = primary tag. Size = link count (degree-based "hub-ness"). Bold stroke = nodes currently in the stack.
- Edges: solid lines for normal links, dashed for cross-references between topics
- Hover node: preview tooltip
- Click node: open in stacked column (see 4.7)
- Local-graph mode: restrict to N-hop neighborhood around a focused node

Mobile: graph view becomes a separate page (topology hard to use on small screens).

### 4.7 Garden — stacked-columns retrieval (Matuschak-style)

**File:** `.superpowers/brainstorm/.../content/retrieval-options.html`, `garden-interaction-wireframe.html`

Click a node → opens that note as a new column to the right of any existing columns. Columns scroll horizontally; each scrolls vertically independently. Like `notes.andymatuschak.org`.

UI:
- **Path log** at top (sticky): "Garden / Note A / Note B / Note C / clear" — breadcrumb + clear button
- **Column container**: `scroll-snap-type: x mandatory`; columns at fixed width (~430px on desktop, full-width on mobile)
- **Per-column content**: growth-stage line, title, body, links section at bottom (outgoing + backlinks)
- **Keyboard nav**: `j/k` within a column, `[ ]` between columns, `Esc` collapses stack

Mobile concession: stack becomes vertical back-stack with browser back button.

**Path log persistence**: `localStorage` across sessions, **with consent banner** on first store. Banner is inline at the top of the path-log area: *"Track your reading path across visits? [yes / no / just this session]"*. Choice itself stored in `localStorage` (key: `path-log-consent`).

### 4.8 Garden note page (`/garden/<slug>/`)

Same template for concept + media + reference notes (all org-roam notes). Renders:
- Frontmatter strip: growth-stage icon + label, last-tended date
- For media notes: `:STATUS:` pill, `:STARTED:`/`:FINISHED:` dates, `:SPOILER_LEVEL:` flag if not none
- Title (Petrona, large)
- Body (markdown rendered to HTML)
- **Spoiler blocks** render as `<details>` with custom CSS (collapsed by default, click-to-reveal, blurred-text variant for inline spoilers)
- **Outgoing links** section: links from this note to other notes (extracted from body)
- **Backlinks** section: notes that link to this one (computed at build time)
- For media notes: "→ original" link from bib `url`, optional embed (iframe for games, audio player for music)

### 4.9 Topic map (`/garden/topics/<slug>/`)

A curated org file with framing paragraph + a manually-ordered list of `[[id:UUID]]` references. Renders:
- Title + framing paragraph
- Tile grid of referenced notes (in the user-defined order, not chronological)
- "This topic is referenced from research themes: …" if applicable

### 4.10 Research index (`/research/`)

**File:** `.superpowers/brainstorm/.../content/research-page-wireframe.html`

**Index style: B+C combination** — theme cards primary + tag chip filters.

Layout:
- Hero with "Research" + framing paragraph
- Filter strip: tag chips + "Open graph" toggle
- 2-column grid of theme cards
- Each theme card: optional "also a Garden topic ↗" badge, title, description, status counts (active/dormant/answered), garden notes count, paper count
- "Open graph" reveals slim panel (right-rail) with **pure force-directed graph** of all research nodes (no hierarchy in layout). Node size = degree. Color = primary tag. Squares for theme nodes, circles for question nodes. Solid edges for parent-child, dashed for cross-theme.

### 4.11 Research theme page (`/research/themes/<slug>/`)

If theme has `garden_topic_ref` set, page absorbs the Garden topic content. Layout:
- Top section (warm cream tinted background, `--color-tile`): research-specific framing — paragraph + 3-column block (Active questions / Dormant / Outputs)
- Below: garden topic content embedded inline (topic framing + tile grid). Same tiles as `/garden/topics/<slug>/`.
- Breadcrumb: `Research › <theme>` with cross-link "↗ also at /garden/topics/<slug>"

If no `garden_topic_ref`: theme page only shows research framing + question outline + outputs. No garden content section.

### 4.12 Research question hub (`/research/questions/<slug>/`)

Sections:
- Status strip: theme tag, status pill (active/dormant/answered), last-tended, started date
- Question statement (Petrona italic-ish, large, prominent)
- **Current thinking** — 2–4 paragraphs of running prose
- **Sub-questions** — list with brief framings (each links to its own hub)
- **Sibling questions** (this theme) — list of related question titles
- **Supporting Garden notes** — tile grid (or compact list) of linked notes
- **Related Essays** — list with brief metadata
- **Outputs** — papers, talks, code (with appropriate icons)
- **Backlinks** — count of references from other questions/notes/essays

### 4.13 Works umbrella (`/works/`)

3-card overview: Games / Music / Poetry. Each card shows recent items + count + "All X →" link.

### 4.14 Games index (`/works/games/`)

**File:** `.superpowers/brainstorm/.../content/games-section.html`

Filter chips: all / playable / in progress / jam / research-prototype / archived. Stats line on right.

2-column card grid. Each card:
- Preview (16:9 aspect): hero image OR gif (with toggle to switch — gif respects `prefers-reduced-motion`)
- "▶ Play in browser" badge (top-right) if web-playable
- Status badge (bottom-left) with year and game-type
- Body: title, tagline, status dot, platforms, tags

### 4.15 Game page (`/works/games/<slug>/`)

Hero: title + italic tagline + status pill + year + collaborators + tech stack + playthrough length.

Embed-or-play block at the top: iframe when possible (itch.io widget, Bitsy embed, custom WebGL), fallback to "Open in itch.io →" link. Below: "Source on GitHub" / control hints.

Sections:
- About — pitch and design intent
- Screens — 3-up grid of screenshots
- **Connections** (2 columns):
  - "Research questions this game explores" — links to `/research/questions/...`
  - "Essays & notes about this game" — pulls **essays tagged with the game slug AND garden notes tagged with it** (graceful fallback to garden note when no essay exists)
- Credits & links — Made-with stack + Find-it/fork-it (itch / GitHub / DOI if cited in a paper)

### 4.16 Music index (`/works/music/`)

**File:** `.superpowers/brainstorm/.../content/music-poetry-pages.html`

List rows (more text-friendly than card grid for audio). Each row: cover thumbnail (80px) + title + format/length/year metadata + brief description + play button + platform links.

Filter chips: all / albums / tracks / experiments / live.

### 4.17 Music page (`/works/music/<slug>/`)

Hero: cover art (200px) + title + tagline + meta strip (format, tracks, length, year, solo/collab).

**Player frame**: choice of self-hosted custom widget OR platform iframe (Bandcamp / SoundCloud), determined per-item from frontmatter:
- If self-hosted audio file present → custom player widget with the site's visual identity (44px round play button in burgundy, progress bar in burgundy, monospace timestamp, link row below)
- Else if platform embed (`:EMBED_BANDCAMP:` / etc.) → iframe of that platform
- Both in the spec; per-item config decides which renders

Below player: alternative platform mirror links.

Sections:
- About — prose
- **Tracks** — numbered list with title + duration. Click any track to play it (jumps and continues from there). Album play button starts track 1.
- **Synced lyrics** if `:LYRICS_POEM:` is set on the music note: see §5.5.
- Connections — Tied to (other works / essays) + Made with (tools/instruments)

### 4.18 Synced lyrics layout (when active)

**File:** `.superpowers/brainstorm/.../content/poetry-revised-and-synced-lyrics.html`

Two-column layout: player on the left, lyrics panel on the right (max-height ~420px, fade-out gradient at bottom).

Lyrics rendering:
- Each line is a `<span class="line" data-time="...">`
- Past lines: `--color-ink-soft`, smaller (1.05rem)
- Current line: `--color-ink`, 600 weight, 1.18rem, slight x-translate to draw eye
- Future lines: `--color-ink-fade`
- Auto-scroll keeps current line near vertical middle (smooth scroll)
- Click a line → seeks audio to that timestamp
- Timestamps **hover-only** (not always visible) — `display: none` until row hover

Mobile: stacks vertically (player above, lyrics below). Auto-scroll within the lyrics container only.

### 4.19 Poetry list (`/works/poetry/`)

**File:** `.superpowers/brainstorm/.../content/poetry-revised-and-synced-lyrics.html` (View 1 + View 2)

Narrow column (max ~720px). Three view tabs:
1. **Recent** (default) — flat reverse-chronological list of poem titles. Just title (italic Petrona) + subtle date metadata. **No first-line preview**, no year section dividers. Optional badge "set to music" for poems with linked recordings; "collection: <name>" badge for poems in a named collection.
2. **By collection** — poems grouped under their `:COLLECTION:` value with a framing paragraph per collection. If collection ties to music ("set to music on Greenhouse Demos"), show that link.
3. **By tag** — poems grouped by tag.

### 4.20 Poem page (`/works/poetry/<slug>/`)

V1: simple display.
- Title (Petrona italic, ~2rem)
- "Audio pill" link if `:LYRICS_POEM:` is set on a music piece pointing to this poem: pill with pulse + "Set to music — listen with synced lyrics ↗"
- Body: poem text rendered as paragraphs, generous line-height (~2.1), Petrona ~1.1rem, narrow column (~600px)

V2 (deferred): line-by-line presentation with custom layouts. Workshop separately.

### 4.21 Library umbrella (`/library/`)

**File:** `.superpowers/brainstorm/.../content/now-widget-and-library.html` (View 2)

3-card overview: Reading / Listening / Playing. Each card: section title, stats line ("X finished · Y reading · Z queued"), top-3 items (each with status dot, italic title, creator, status), "All X →" link.

### 4.22 Reading list (`/library/reading/`)

**File:** `.superpowers/brainstorm/.../content/reading-list.html`

Layout:
- Breadcrumb: "About › Reading"
- Hero with framing
- **Currently reading** highlight (1–3 books, 2-column grid, each with cover thumbnail, title, author/year, progress bar with start date, italic takeaway, "→ my notes" / "→ original" links)
- Stats + filter chip strip ("23 finished · 2 reading · 14 queued")
- Year sections (chronological reverse) with book rows. Each row: meta (type/topic), title (italics for fiction), author/year, brief takeaway extracted from note's first paragraph, links section, status badge with shape+color (✓ for finished, ✗ for abandoned, ▶ for reading, ↑ for queued)
- "Up next" queue at bottom (looser format)

### 4.23 Listening / Playing pages

Same shape as Reading with format-specific adjustments:
- **Listening**: cover art slightly more prominent; primary unit is album-level (tracks visible inside album notes). Format types: album, EP, single, compilation. Display: "X scrobbles" optional if Last.fm integration ever; absent for now.
- **Playing**: hours-played in metadata, platform indicator. Status taxonomy includes "100%" / "completed" / "dropped" beyond standard. Spoiler-flag prominent (most narrative games warrant it).

### 4.24 Search modal

**File:** `.superpowers/brainstorm/.../content/search-modal.html`

Triggered by search icon in header OR `/` keyboard shortcut anywhere. Renders as overlay modal (~900px max width, centered).

Layout:
- Search input with magnifier icon, "Esc to close" kbd hint on right
- Filter chips: in `all` / `essays` / `garden` / `research` / `works` / `library` (with per-section result counts)
- Results pane (scrollable, max-height ~480px), grouped by section with section headers
- Each result: title with `<mark>` highlighting query, snippet with highlighting, badge (essay/garden/research/works/library), metadata (date, status, growth stage as applicable)
- **Spoiler-aware**: notes with spoiler blocks indexed but spoiler text excluded; if a result's parent has spoiler blocks, snippet shows "N spoiler blocks excluded from search" indicator
- Footer: keyboard hints (↑↓ navigate, ↵ open, ⌘↵ new tab, Esc close) + result count and timing

Library: **Pagefind**, run after `hugo --minify` produces `public/`. Pagefind binary generates `public/pagefind/` index. The site loads `pagefind/pagefind-ui.js` only on the search modal.

---

## 5. Cross-cutting features

### 5.1 Citations (dual-link)

`org-cite` source: `[cite:@calvino1972cities]`. ox-hugo passes through; site renders via `cite` shortcode.

Rendered output:
- Inline: small superscript marker → on hover, card showing title, authors, year + 2 action links: "→ original" (bib `url`) and "→ my notes" (linked garden note slug, conditional on existence)
- Bibliography section at end of post: `<ol>` of full citations, each with the same dual links
- Build-time lookup: `data/citations.yaml` maps citekey → note slug + bib metadata

Citations work uniformly for any media type — books, albums, games, films, papers — because all are bib entries with optional org-roam notes.

### 5.2 Footnotes / sidenotes

Tufte-style. Right-side popup or numbered footnotes at end of post. Per-post frontmatter: `notes_style: sidenote | endnote`.

Sidenotes float to the right margin on wide screens; on narrow, fall back to inline expandable footnotes. Implementation: vanilla CSS `position: absolute` for sidenotes; `<details>` for inline collapsing.

### 5.3 TOC (left rail)

Per-post frontmatter `toc: true`. Auto-built from H2/H3 headers. Sticky on left margin on wide screens; collapses or hides on narrow.

### 5.4 Spoiler blocks

Org source:
```org
#+begin_spoiler[discusses the ending]
Plot detail.
#+end_spoiler
```

Markdown emitted by ox-hugo:
```markdown
{{< spoiler summary="discusses the ending" >}}
Plot detail.
{{< /spoiler >}}
```

Hugo shortcode renders to:
```html
<details class="spoiler">
  <summary>Show spoiler — discusses the ending</summary>
  <div class="spoiler-body">Plot detail.</div>
</details>
```

CSS: collapsed `<details>` shows the summary in burgundy with a small caret. Open `<details>` reveals body. Default summary if none provided: "Show spoiler".

Inline spoiler markup (TBD convention; suggested `~text~` or org macro): renders as a `<span class="spoiler-inline">` with a blur filter that lifts on hover/click.

`data-pagefind-ignore` on `.spoiler-body` so search doesn't index plot text.

### 5.5 Synced lyrics

Org source (inside an org-roam note for music or its linked poem):
```org
#+begin_lyrics
[00:00] When the orchard quiets,
[00:08] even the wind is patient with us.
[01:32] Now everything is mostly waiting.
#+end_lyrics
```

Markdown emitted:
```markdown
{{< lyrics >}}
[00:00] When the orchard quiets,
...
{{< /lyrics >}}
```

Hugo shortcode parses `[mm:ss]` timestamps and renders as:
```html
<div class="synced-lyrics">
  <span class="line" data-time="0">When the orchard quiets,</span>
  <span class="line" data-time="8">even the wind is patient with us.</span>
  ...
</div>
```

JS module `synced-lyrics.js` listens to `<audio>` `timeupdate` events and toggles `.line.current` / `.line.past` classes; also handles click-to-seek on each line.

Linked from a music page when the music piece's note has `:LYRICS_POEM:` set. Linked back from the poem page via the "audio pill."

### 5.6 Path log (Garden stacked columns)

Sticky breadcrumb at top of stacked-column container. Tracks the order of notes the user visited within Garden during this session. Each entry is a clickable label that jumps back. "Clear" button resets the stack.

**Persistence with consent**: First time the path-log would write to `localStorage`, an inline banner appears in the path-log row with the consent question. Choice persisted in `localStorage` key `path-log-consent`. Three values: `yes` (persist across sessions), `no` (never persist), `session` (this session only).

### 5.7 Graph view (Garden + Research)

Library: `d3-force` (~30KB minified). No other d3 family modules.

**Garden graph:**
- Nodes: all garden notes
- Node color: primary tag
- Node size: link count (degree)
- Edges: links between notes
- Filters: tag, growth stage, time range, local-graph mode (N-hop neighborhood)

**Research graph (separate page or panel):**
- Pure force-directed (no hierarchy in layout)
- Nodes: themes (squares) + questions + sub-questions (circles)
- Solid edges: parent-child
- Dashed edges: cross-references
- Node size: degree
- Filters mirror Garden's

Implementation: SVG, manually styled. Forces: `forceLink`, `forceManyBody`, `forceCenter`, `forceCollide`. Animation respects `prefers-reduced-motion` (static layout if reduced).

### 5.8 Currently widget (homepage)

Reads `data/now.yaml`. Three lines: reading / listening / playing. Each line: verb + linked italic title + creator + optional spoiler-flag + "all X →" link to library section.

No "also" line for non-media now items — those appear on the About `/now/` section only.

### 5.9 Theme toggle

Icon button in header. Click cycles light → dark → system. Stores choice in `localStorage` key `theme-pref`. On load: read `theme-pref`; if absent, use `prefers-color-scheme`.

Implementation: toggles `data-theme="light"` / `"dark"` / removes attribute on `<html>`. CSS variables defined under `:root[data-theme="dark"]` and `@media (prefers-color-scheme: dark) :root:not([data-theme])`.

### 5.10 RSS

Hugo built-in `index.xml` for site-wide. Per-section RSS where useful (essays, garden, research). Footer link + header icon button. RSS button in header is orange (~`#ee7e2c`) — the universally recognized RSS color.

### 5.11 Reading-time on essay cards

Computed at build time from word count (~200 wpm). Displayed in metadata strips.

---

## 6. Data model & org-mode contract

### 6.1 Org-roam note shapes

**Concept note** (idea, no media tied):
```org
:PROPERTIES:
:ID:               <uuid>
:GROWTH_STAGE:     budding
:LAST_MODIFIED:    [2026-04-22]
:END:
#+title: Salience & memory

(first paragraph as preview)

(rest of note)
```

**Literature/media note** (book / album / game / film / series):
```org
:PROPERTIES:
:ID:               <uuid>
:ROAM_REFS:        @calvino1972cities
:MEDIA_TYPE:       book
:STATUS:           reading
:STARTED:          [2025-12-15]
:FINISHED:         null
:GROWTH_STAGE:     budding
:SPOILER_LEVEL:    light
:LAST_MODIFIED:    [2026-04-22]
;; type-specific extras (any can be omitted):
:HOURS_PLAYED:     14            ;; games
:PROGRESS_PCT:     51            ;; books
:LRC_FILE:         "..."         ;; music with external lyrics
:LYRICS_POEM:      <uuid>        ;; music whose lyrics are a published poem
:COLLECTION:       greenhouse    ;; poems in named collection
:END:
#+title: Invisible Cities

(first paragraph as preview)

(body, including any #+begin_spoiler blocks)
```

**Reference note** (paper / video / article / talk):
```org
:PROPERTIES:
:ID:               <uuid>
:ROAM_REFS:        @nguyen2020games-as-art
:MEDIA_TYPE:       paper
:GROWTH_STAGE:     evergreen
:LAST_MODIFIED:    [2026-04-12]
:END:
```
No `:STATUS:` / dates required — notes are the artifact, not the consumption.

### 6.2 BibTeX scope

`biblio.bib` (or split files, org-roam-bibtex's choice) covers ALL referenced media — books, albums, games, films, papers, articles, videos. Standard BibLaTeX with `@misc` / `@article` / `@book` / `@software` / `@audio` as appropriate.

Required-ish fields per entry:
- `author` / `editor` — can be `{Studio Name}` for game studios
- `title`
- `year`
- `url` — where to find / play / buy / read it (Bandcamp, Steam, itch.io, DOI, blog URL)
- Type-appropriate: `journal`, `publisher`, `howpublished`, `series`

The `url` field is rendered as "→ original" in citations and library row links.

### 6.3 Required-property matrix per content type

| Type | Required | Optional |
|---|---|---|
| Concept note | `:ID:`, `:GROWTH_STAGE:`, `:LAST_MODIFIED:` | tags |
| Media note | `:ID:`, `:ROAM_REFS:`, `:MEDIA_TYPE:`, `:STATUS:`, `:GROWTH_STAGE:`, `:LAST_MODIFIED:` | `:STARTED:`, `:FINISHED:`, `:SPOILER_LEVEL:`, type-specifics |
| Reference note | `:ID:`, `:ROAM_REFS:`, `:MEDIA_TYPE:`, `:GROWTH_STAGE:`, `:LAST_MODIFIED:` | tags |
| Essay (subtree) | `#+title`, `:DATE:`, `:LAST_MODIFIED:` | `:DRAFT:`, `:SUMMARY:`, `:TAGS:`, `:SERIES:`, `:SERIES_ORDER:`, `:TILE_SIZE:`, `:FEATURED:`, `:HERO:`, `:HAS_WIDGETS:`, `:HAS_MATH:` |
| Research question | `:ID:`, `:STATUS:`, `:THEME:`, `:STARTED:`, `:LAST_MODIFIED:` | `:PARENT_QUESTION:`, `:TAGS:` |
| Game | `#+title`, `:STATUS:`, `:GAME_TYPE:`, `:LAST_MODIFIED:` | `:PLATFORM:`, `:STACK:`, `:JAM:`, `:DOI:`, `:HERO:` |
| Music piece | `#+title`, `:FORMAT:`, `:YEAR:`, `:LAST_MODIFIED:` | `:LYRICS_POEM:`, `:LRC_FILE:`, `:DURATION:`, embed/audio fields |
| Poem | `#+title`, `:DATE:`, `:LAST_MODIFIED:` | `:COLLECTION:`, `:TAGS:`, `:LINES:` (auto), `:SET_TO_MUSIC:` (cross-ref to music piece) |

### 6.4 LAST_MODIFIED freshness gate

Strict mode. Missing `:LAST_MODIFIED:` blocks export.

Thresholds:
- `now.org` sections: 14 days
- Garden notes (seedling): 30 days
- Garden notes (budding): 90 days
- Garden notes (evergreen): 365 days (or none)
- Research questions (active): 60 days
- Essays / works / poems: no freshness threshold (publication-locked), but `:LAST_MODIFIED:` must still be present

### 6.5 Status taxonomy (configurable)

Lives in `config/_default/params.yaml` (or equivalent) as a list. Each status has key, label, shape (for CB-safe rendering).

```yaml
reading_statuses:
  - key: reading
    label: Reading
    shape: filled-circle
  - key: finished
    label: Finished
    shape: check
  - key: abandoned
    label: Abandoned
    shape: x
  - key: queued
    label: Up next
    shape: arrow-up
```

Adding a new status (e.g., re-reading, deferred, reference-only) = edit the config, start using the value. No code changes.

### 6.6 Tags

Tags are filters and clustering aids — **not load-bearing** for site structure. The user maintains a controlled vocabulary loosely but adds tags freely. Topic maps drive Garden structure; tag chips assist filtering.

### 6.7 Privacy via org-export boundary

`:noexport:` on a subtree (or any org-roam node, file-level) excludes it from ox-hugo. The site never knows the content existed. This is the entire privacy mechanism.

The user has indicated they may use a `:private:` tag instead in some workflows; ox-hugo can be configured to skip on either tag.

---

## 7. Build pipeline

```
USER'S ORG SOURCE TREE (~/org/...)
├── ~/org/site/now.org              — Now widget data
├── ~/org/site/biblio.bib           — Bibliography (all media + references)
├── ~/org/notes/*.org               — Org-roam notes (concept + media + reference)
├── ~/org/site/essays/*.org         — Essays (one file or subtrees)
├── ~/org/site/research/*.org       — Themes + questions
├── ~/org/site/works/games/*.org    — Game pages
├── ~/org/site/works/music/*.org    — Music pages
└── ~/org/site/works/poetry/*.org   — Poems
        │
        │  ox-hugo + custom elisp helpers
        ▼
EMACS EXPORT (user runs an org-publish or per-section command)
  • Pre-export hook:    freshness gate (strict)
  • Pre-export hook:    required-property check
  • Link transformer:   [[id:UUID]] → /<section>/<slug>/
  • Content exporter:   org → content/<section>/<slug>/index.md (frontmatter + body)
  • Data exporter:      org-roam scan → data/now.yaml, data/{reading,listening,playing}.yaml,
                                          data/citations.yaml, data/notes.json, data/research.yaml
        │
        ▼
REPO STATE (commit + push)
  • content/      (markdown content tree)
  • data/         (all data files for Hugo)
  • static/       (any static assets)
        │
        ▼
HUGO BUILD (GitHub Actions, on push to master)
  • hugo --minify
  • Pagefind binary post-step:  pagefind --site public/
  • Lighthouse + contrast CI gates run
        │
        ▼
DEPLOY TO github.io (existing workflow, slightly modified)
```

The user runs the org export locally; commits the resulting content + data; GitHub Actions takes over from there. Commit cadence is whatever feels natural — typically once per writing session.

---

## 8. Tech stack (locked)

### What's in

| Layer | Choice |
|---|---|
| Static-site generator | **Hugo extended** (≥0.162.1) |
| CSS | **Hand-rolled CSS** in a single `assets/css/main.css`, with CSS custom properties for theming. Hugo's `resources.Get` + `minify` + `fingerprint` pipeline. |
| JS bundler | Hugo's built-in `js.Build` (esbuild internally — no native addons needed) |
| JS framework | **None** — vanilla JS |
| Graph visualization | **d3-force** only (~30KB) |
| Search | **Pagefind** — Rust binary, post-build step, ships static index + JS+CSS |
| Authoring | Emacs + org-mode + org-roam + ox-hugo + org-cite + org-roam-bibtex |
| Hosting | GitHub Pages (existing workflow extended) |
| Fonts | Google Fonts (Petrona / Inter / JetBrains Mono) loaded via `<link>` |

### What's out

- **Tailwind v4** — dropped. Reasons: bespoke component-heavy site doesn't benefit from utility-first; `@theme {}` tokens replaced trivially by CSS custom properties; removes `lightningcss` native-addon issue; aligns with minimal-stack goal; eliminates the `npm run build:css` step entirely.
- **Node dependencies** — none after Tailwind drop. The whole `node_modules/`, `package.json`, `package-lock.json` go away.
- **JS frameworks** (React, Vue, Svelte, etc.) — none
- **Analytics** (any) — none
- **Comments** (Disqus, etc.) — none for v1; possibly Giscus later if ever
- **CDN layer** — GitHub Pages defaults are sufficient
- **External font hosting / Bunny / etc.** — Google Fonts is fine

### Performance budget (target, advisory)

- Most pages: <100KB total weight
- Media-heavy pages (homepage, music page with player): <500KB
- Garden index with graph open: <600KB (d3-force adds ~30KB; the rest is data size-dependent)
- Pagefind: lazy-loaded (only on search modal open)

---

## 9. Hugo project structure

```
content/
  _index.html                  # homepage
  about/index.md
  essays/<slug>/index.md
  garden/
    _index.md
    <slug>/index.md
    topics/<slug>.md
  research/
    _index.md
    themes/<slug>/index.md
    questions/<slug>/index.md
  works/
    _index.md
    games/<slug>/index.md
    music/<slug>/index.md
    poetry/<slug>/index.md
  library/
    _index.md
    reading/_index.md
    listening/_index.md
    playing/_index.md

layouts/
  _default/{baseof,list,single}.html
  index.html                              # homepage
  garden/{list,single,topic}.html
  research/{list,theme,question}.html
  works/{list,games-list,games-single,music-list,music-single,poetry-list,poetry-single}.html
  library/{list,reading,listening,playing}.html
  partials/
    head.html, header.html, footer.html, scripts.html, search-modal.html
    now.html                              # Currently widget
    essay-card.html, essay-featured.html
    note-tile.html, note-page.html
    work-row.html, game-card.html
    research-question.html, research-theme.html
    citation.html, citation-card.html
    spoiler.html
    audio-player.html, synced-lyrics.html
    graph-view.html, stacked-columns.html, path-log.html
    growth-icon.html
    rss-button.html, theme-toggle.html
  shortcodes/
    widget.html                # interactive embed
    scroll-video.html
    spoiler.html
    lyrics.html
    cite.html
    figure.html
    games-embed.html

data/
  now.yaml                     # generated from org
  reading.yaml, listening.yaml, playing.yaml
  notes.json                   # graph nodes + edges
  citations.yaml               # citekey → note slug + bib metadata
  research.yaml                # theme/question hierarchy

assets/
  css/main.css
  js/
    index.js                   # entry; toggles, nav
    toggle-theme.js
    graph.js                   # d3-force — used by Garden + Research
    stacked-columns.js
    audio-player.js
    synced-lyrics.js
    spoiler.js
    search.js                  # Pagefind UI integration
    nav.js
  images/
    growth/{seedling,budding,evergreen}.svg
    icons/{gamepad,note,quill,rss,search,...}.svg

archetypes/
  essays/index.md
  garden-note/index.md
  garden-topic/index.md
  research-theme/index.md
  research-question/index.md
  games/index.md
  music/index.md
  poetry/index.md

config/
  _default/
    config.yaml                # baseURL, language, etc.
    params.yaml                # site params (status taxonomy, etc.)

static/
  pagefind/                    # populated by `pagefind --site public/`

tools/
  check-contrast.py            # CI gate
```

Hugo themes directory: not used; `layouts/` directly.

---

## 10. Elisp helper output specs (the contract)

The site implementation works entirely off these output formats. The user writes the elisp; the site reads the outputs. As long as the helpers produce files matching these specs, the contract is honored.

### 10.1 Pre-export freshness gate

**Behavior:** halt export on missing or stale `:LAST_MODIFIED:` per the matrix in §6.3 + thresholds in §6.4. On violation: stop, jump cursor to offending entry, prompt with `(yes-or-no-p)`. Strict mode never auto-proceeds.

No file output. Process gate.

### 10.2 Org-roam ID resolver (link transformer)

Convert `[[id:UUID][label]]` to `[label](/<section>/<slug>/)` at export.

Resolution rules:
1. Look up org-roam node by ID
2. If `:EXPORT_HUGO_SECTION:` set → use that section
3. Else: file-path heuristic (notes → `/garden/`, essays → `/essays/`, etc.)
4. Slug: `:EXPORT_FILE_NAME:` if set, else slugified `#+title`
5. Fallback (not found): `[label](#broken-link-<UUID>)` + console warning. Build proceeds; CI gates may catch.

Library cross-links: media note's site URL is `/garden/<slug>/`; library rows link to that URL.

### 10.3 `data/now.yaml`

```yaml
last_modified: 2026-05-03
sections:
  - key: reading
    label: Reading
    last_modified: 2026-05-01
    items:
      - "Calvino, *Invisible Cities* — re-read for the games paper"
      - "Crawford, *Chris Crawford on Game Design*"
  - key: working_on
    label: Working on
    last_modified: 2026-04-28
    items: ["..."]
  - key: wondering
    label: Wondering
    last_modified: 2026-04-30
    items: ["..."]
```

Items are markdown-allowed. Section ordering determines display order.

### 10.4 `data/{reading,listening,playing}.yaml`

```yaml
items:
  - slug: invisible-cities          # garden URL slug
    title: Invisible Cities
    creator: Italo Calvino
    year: 1972
    media_type: book                 # or album/track/game/film/series
    status: reading                  # one of the configured statuses
    started: 2025-12-15
    finished: null
    spoiler_level: light             # none/light/heavy
    last_modified: 2026-04-22
    cite_key: calvino1972cities
    canonical_url: "https://..."     # from bib `url`
    note_slug: invisible-cities      # /garden/<slug>/
    preview: "Re-reading for the procedural narrative paper..."   # first paragraph of note
    tags: [fiction, italian, procedural-narrative]
    extras:
      progress_pct: 51
      progress_label: "p. 84 / 165"
```

Each list filtered to the appropriate `media_type`. `extras` is type-specific (progress for books, hours for games, runtime for music).

### 10.5 `data/citations.yaml`

```yaml
calvino1972cities:
  type: book
  title: Invisible Cities
  authors: ["Italo Calvino"]
  year: 1972
  publisher: Einaudi
  url: "https://..."
  note_slug: invisible-cities       # null if no note
  spoiler_level: light                # null if no note
mobius2019outerwilds:
  type: misc
  howpublished: Video game
  title: Outer Wilds
  authors: ["Mobius Digital"]
  year: 2019
  publisher: Annapurna Interactive
  url: "https://store.steampowered.com/app/753640"
  note_slug: outer-wilds
  spoiler_level: heavy
```

Hugo's `cite` shortcode looks up by citekey and renders accordingly.

### 10.6 `data/notes.json`

```json
{
  "generated_at": "2026-05-03T14:00:00Z",
  "nodes": [
    {
      "id": "uuid-here",
      "slug": "salience-and-memory",
      "title": "Salience & memory",
      "section": "garden",
      "media_type": null,
      "growth_stage": "budding",
      "primary_tag": "procedural-narrative",
      "tags": ["procedural-narrative", "memory"],
      "last_modified": "2026-04-28"
    }
  ],
  "edges": [
    {"from": "uuid-a", "to": "uuid-b", "kind": "link"}
  ]
}
```

`kind`: `link` (regular wiki-link) or `parent` (org-roam parent property — used in hub-page rendering, not graph layout for Research).

### 10.7 `data/research.yaml`

```yaml
themes:
  - slug: procedural-narrative
    title: Procedural narrative
    description: "How systems generate meaning when a player walks through them."
    garden_topic_ref: procedural-narrative   # null if no overlap
    questions:
      - slug: how-do-players-construct-meaning
        title: "How do players construct meaning from procedural systems?"
        status: active
        started: 2024-09-15
        last_modified: 2026-05-01
        framing: "..."
        sub_questions:
          - slug: surprising-vs-arbitrary
            title: "When is a system surprising vs arbitrary?"
            status: active
        related_questions: [is-narrative-emergent-or-designed]
        supporting_notes: [salience-and-memory, surprise-budget]
        related_essays: [what-systems-remember]
        outputs:
          - kind: paper
            label: "Salience paper draft"
            status: private
          - kind: talk
            label: "GDC 2025 talk"
            url: "..."
```

### 10.8 Spoiler block transform

Org `#+begin_spoiler[summary]…#+end_spoiler` → markdown `{{< spoiler summary="..." >}}…{{< /spoiler >}}`. Handled by ox-hugo or post-export sed.

### 10.9 Lyrics block transform

Org `#+begin_lyrics … #+end_lyrics` (with `[mm:ss]` per line) → markdown `{{< lyrics >}}…{{< /lyrics >}}`.

### 10.10 Authoring helpers (no output spec — user's tools)

- Lyrics-tap (F8 inserts current `[mm:ss]` from mpv playback)
- Now-section quick update
- Reading-status cycle (`:STATUS:` value rotation)

These help the user but don't affect site contract.

---

## 11. Accessibility & CI gates

### Accessibility rules

- WCAG 2.1: AAA body text, AA accents (formal policy in §2)
- Never color-only meaning (status indicators always color + shape + label)
- Focus states visible, 2px outline
- Links underlined by default
- Tags/chips always have text content
- `prefers-reduced-motion` respected (fades only, no large position animations; force-directed graph defaults to static layout if reduced)
- `prefers-color-scheme` respected by default
- Respect user override of theme

### Required CI gates (all of these block deploy on failure)

| Gate | Tool / Implementation |
|---|---|
| **Lighthouse a11y** | Lighthouse-CI in GitHub Actions. Score ≥90. Fails build if any sampled page below threshold. |
| **Contrast checker** | `tools/check-contrast.py` (or similar): parses CSS for color tokens, asserts WCAG ratio for each used pairing per the policy (AAA body, AA accent). Fails on any violation. |
| **Build smoke test** | `hugo --minify` succeeds; key URLs (homepage, /essays/, /garden/, /research/, /works/, /about/, /library/) return 200. |
| **Required-data check** | Asserts that all referenced citekeys resolve, all `:ROAM_REFS:` link to existing bib entries, all `:LAST_MODIFIED:` properties present where required (the freshness gate is upstream of this — this re-checks at build time). |

### Advisory CI gates (warnings, don't block deploy)

- Link rot — weekly cron, reports broken external links

---

## 12. User preferences captured during brainstorm

These are observations from the brainstorm session. Continuation sessions should respect these.

- **Authoring**: heavy Emacs + org-mode + org-roam. ox-hugo for export. org-roam-bibtex for citations. Pre-export elisp for freshness gates.
- **Tag discipline**: vocab maintained but not load-bearing. Topic maps drive structure.
- **Existing convention**: `:LAST_MODIFIED:` (not `:LAST_UPDATED:` — that was Claude's initial proposal, corrected by user).
- **Privacy**: `:noexport:` (existing org pattern) or `:private:` tag with custom skip in ox-hugo.
- **Stance on AI**: "Words are mine; not generated" appears as an explicit footer claim. AI for code only.
- **Token-efficiency**: user is aware of token costs, prefers efficient screens; pointed at external resources (Typewolf, Fonts In Use) when more options were needed.
- **Decision pacing**: user prefers closing architecture/IA threads completely before any visual work. Memory file: `feedback_close_architecture_before_visual.md`.
- **Numerical precision**: cite WCAG ratios precisely, never estimate. Memory file: `feedback_verify_contrast_ratios.md`.

---

## 13. Deferred / future work

- **Special line-by-line poetry presentation** (v2 of poem pages) — workshop separately
- **Auto-sync lyrics** for vocal music via Whisper / WhisperX — optional authoring workflow if the user has vocal music; for instrumental + read-along the manual `:LRC_FILE:` or inline `[mm:ss]` approach is the path
- **`/references/` browse page** — chronological list of paper/video/article notes, similar to library but for non-consumed-as-experience reference material. Add only if needed.
- **Comments** — Giscus (GitHub Discussions) is the candidate if ever added. No analytics or third-party trackers regardless.
- **Graph filter additions** — citation-derived edges, recency-weighted edge thickness, "co-cited" edges. Workshop when there's more graph-using content.
- **Mobile graph view** — currently spec'd as a separate page on small screens. May want a richer mobile-graph experience eventually.
- **Search "did you mean" / typo correction** — Pagefind has a flag for it; default to enabling once content exists.
- **Pagefind-based filters in the search modal** — start with section filters; add tag, status, growth-stage filters once index is rich enough to need them.
- **Inline-spoiler markup convention** — TBD; suggested `~text~` org macro or custom export block. Block-level spoilers (`#+begin_spoiler`) are spec'd.
- **WCAG-AAA contrast linter coverage for non-HTML sources** — `tools/check-contrast.py` currently parses `assets/css/main.css` tokens against the 9 declared pairings. It does NOT inspect raw HTML appearing inside Markdown bodies (`.md` files passing through `markup.goldmark.renderer.unsafe: true`), shortcode-emitted markup, or per-page inline styles. As authors begin embedding richer raw HTML directly in `.md` content (homepage hero post-Hugo-0.162 rename, future explorables, `@@html:` org export snippets from the B-publisher), uncovered color references could ship without contrast verification. Goal: extend the linter to (a) extract `style="…"` / `class="…"` references from rendered HTML under `public/`, (b) resolve any color tokens referenced (CSS custom property or literal hex/rgb), (c) verify ratios against the same 9-pairing policy. Run as a post-build CI step against the actual rendered output, not the source. Defer until the first real raw-HTML-with-color landing lands in `.md` content.
- **Works page sidebar labels overflow viewport height** — the cross-template page-sidebar rail (CSS §41, `partials/page-sidebar.html`) rotates labels 90° via `writing-mode: vertical-rl`, so label height = viewport height available is bounded by `100vh − 1.25rem margins`. On `/works/` the section labels (Games / Music / Poetry / etc.) are longer than the rail can fit at desktop breakpoints (≥1220 px), causing text to overflow off-screen and become illegible. The `font-size: clamp(0.9rem, 0.7rem + 0.35vw, 1.2rem)` ceiling is too generous for the works umbrella's label set. Two fix paths: (a) cut the upper clamp bound to ~1rem AND shrink letter-spacing on the works template specifically; (b) shorten the labels themselves to single words (e.g. `Games` instead of `Works — Games`). Spotted during B.2 spot-check 2026-05-30; affects only the works umbrella + per-medium sub-indexes (which inherit the same rail). Other section sidebars (essays, garden, research, library, streams) are within bounds.

---

## 14. Implementation phases (rough order)

The implementation plan (next step, `superpowers:writing-plans`) should organize work along these lines.

### Phase 0: Foundation cleanup
- Drop Tailwind: remove `package.json`, `package-lock.json`, `node_modules/`, `assets/css/compiled.css`, `tailwindcss` references in layouts
- Update `.gitignore` (remove tailwind-related entries; add `data/` if exporting on the user's machine and not committing — TBD)
- Decide: data files committed (simpler — user runs export, commits, push) or generated in CI (more complex, requires ox-hugo running in CI). **Recommendation: commit data files**; user runs export locally.

### Phase 1: Visual identity scaffold
- Write `assets/css/main.css` with the full token system, typography, base layout, navigation, footer, light/dark switching
- Theme toggle JS
- Update `layouts/_default/baseof.html` to load `main.css` directly (no Tailwind compile step)
- Re-render existing homepage and About to use the new identity
- **Verify with contrast-checker tool** that all ratios meet policy

### Phase 2: Core sections — Essays, About, Garden notes
- Implement essay list + post layouts (variable-tile grid; full prose layout with TOC, sidenotes, citations placeholder, code highlighting)
- Implement About with placeholder Now widget (until data exporter is ready)
- Implement Garden note page (single template, used for concept + media + reference notes)
- Implement basic Garden index (topic maps, no graph yet)
- RSS feed (Hugo built-in, customized template if needed)

### Phase 3: Org-mode pipeline (depends on user's elisp work)
- Coordinate with the user on data exporter outputs
- Once `data/now.yaml` is reliable, wire the Now widget on homepage + About
- Once `data/citations.yaml` is reliable, implement the `cite` shortcode + hover-card UI
- Once `data/notes.json` is reliable, implement the graph view (d3-force)
- Once `data/{reading,listening,playing}.yaml` is reliable, implement library pages and homepage Currently widget
- **Two separate publishing commands** — different cadences imply different workflows:
  - **Garden / Library / Research publish** (runs frequently, idempotent, fast): exports notes, library yaml, and research themes/questions; meant to run on a regular cadence (daily / hourly) so the "living" surfaces stay current without ceremony. Should be safe to invoke repeatedly with no diff when nothing changed.
  - **Essay publish** (per-post, deliberate): exports a single essay subtree (or all essays) with its assets (hero illo, figures, sidenotes, citations). Treated as a publishing event — not a continuous-export workflow. Output is reviewed before commit.
  - Both commands share underlying ox-hugo + elisp helpers; they differ in selector (which org subtrees to export) + intended invocation frequency.

### Phase 4: Garden interaction model
- Stacked-column retrieval (vanilla JS)
- Path log with consent banner
- Backlinks computation (Hugo template walking content)
- Graph view (Garden version)
- Spoiler shortcode

### Phase 5: Research
- Theme cards index + tag filter
- Theme page (with optional garden-topic absorption)
- Question hub page
- Research graph (separate page or panel)

### Phase 6: Works
- Games index + game page (with iframe embed; gif/screenshot toggle; connections section)
- Music index + music page (custom audio player + platform iframe alternatives + tracklist + synced lyrics shortcode)
- Poetry list (3 view tabs) + poem page (simple v1)

### Phase 7: Library + homepage final
- Library umbrella + reading/listening/playing pages (data-driven from `data/*.yaml`)
- Homepage v3 final assembly: Currently strip (3 lines), Studio strip with type-glyph icons, two-column Garden+Studio
- Footer "Words are mine; not generated"

### Phase 8: Search + polish
- Pagefind integration (post-build step in GitHub Actions; modal UI; spoiler-aware indexing via `data-pagefind-ignore`)
- CI gates wired (Lighthouse, contrast checker, smoke test, required-data check)
- Final QA pass: keyboard nav, screen reader walkthrough, CB simulation review, mobile audit
- Performance audit — meet budgets in §8

---

## 15. Open questions for implementation planning

These don't block the spec but should be resolved when the implementation plan is written:

1. **Data files in repo vs CI-generated** — recommend: committed by user (simpler). Plan should adopt this default.
2. **Workflow file** — `.github/workflows/hugo.yaml` needs Pagefind step added + CI gates. Plan should produce the new workflow.
3. **Per-page bundle JS** — exact convention for essays with interactive widgets (`assets/widget.js` per page bundle? Some convention?).
4. **Static directory `pagefind/`** — gitignored or committed? Pagefind generates it; if generated in CI, gitignored. If user runs Pagefind locally, gitignore is still appropriate (regenerated on CI).
5. **Inline spoiler markup** — pick a convention (`~text~` vs org macro vs custom export).
6. **Asset fingerprinting** — Hugo's `fingerprint` is on by default for the existing CSS. Continue.

---

## 16. Pointers for future Claude sessions

If you're a continuation of this work and need to refresh:

- **This spec**: `docs/superpowers/specs/2026-05-03-personal-site-design.md`
- **Pre-rebuild site state**: `CLAUDE.md` in repo root
- **Visual mockups** (real fonts, real palette, full-document HTML): `.superpowers/brainstorm/1178775-1777859433/content/*.html` — gitignored, but on the user's machine
- **Memory files**: `~/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/`
- **Git history**: this spec is the design baseline; check git log around 2026-05-03 for the spec commit + `.gitignore` updates

If the user asks a question about a decision, search this doc first. If a decision isn't here, it's open and should be raised with the user before implementing.

---

*End of spec.*
