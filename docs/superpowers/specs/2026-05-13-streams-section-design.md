# Streams section — design

**Phase:** New top-level section. Slot β (parallel with Phase 3) or γ (after Phase 3) — see §16.
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md`.
**Origin:** `~/org/projects.org` TODO captured 2026-05-03 ("Adjust the website design spec and so on to match the streaming setup you want") + follow-up clarification 2026-05-13 (track live state + post a schedule).

A new 7th top-level section `/streams/` that houses the user's live broadcasting workflow. Streams are sessions on Twitch + YouTube Live, archived on YouTube, with show notes + bidirectional cross-references to whatever essays / garden notes / research / works they produced. The site shows live state in the header (pulsing pill, auto-polled), an upcoming-streams strip on the homepage, and a per-stream archive page with click-to-load YouTube embed.

---

## 0. Reconciliation at scheduling (2026-05-19)

This spec was filed 2026-05-13 in a design batch. Six slices shipped before it was scheduled. The architecture (§2, "Approach A") is unchanged and stands as brainstorm-approved; the items below **override** any conflicting wording in later sections. The implementation plan is built against this section + the corrected spec.

**Decisions confirmed with the user (2026-05-19):**

1. **Nav** — add a 7th top-nav item **before About** (`Essays · Garden · Research · Works · Library · Streams · About`). CLAUDE.md's "Top nav (locked)" note is updated to 7 items as part of this slice.
2. **RSS** — **no streams RSS feed.** Since this spec was written, RSS was deliberately scoped to essays-only (`hugo.yaml` sets `home/section/taxonomy/term: [HTML]`; the header hardcodes the essays feed; works + library intentionally have none). **§11's RSS subsection is SUPERSEDED** — streams are discoverable via the section index, homepage strip, and Pagefind. No `layouts/streams/rss.xml`; no RSS-XSL linter touch.
3. **Verification split** — the agent sandbox cannot run Hugo, GitHub Actions, or the live Twitch/YouTube APIs. Agent scope: `tools/poll_streams.py` written test-first against mocked HTTP (stdlib only), all linters + unit tests, dummy fixtures, templates, CSS, JS. User scope (post-merge): Hugo build + visual spot-check on dev server; Twitch dev-app + YouTube API-key + repo secrets/vars bootstrap, then `workflow_dispatch` to verify the live cron path. (Analogous to the synced-poetry audio-QA deferral.)

**Staleness corrected (mechanical — applied inline where it matters, noted here otherwise):**

| Spec wording | Corrected to |
|---|---|
| CSS "§44 streams" (§7, §6 file layout) | **§46** (current max is §45 synced-poetry; §44 is the library redesign) |
| "16th / 17th linter pair" (§9); CI "42 → 46" (§12) | **22nd + 23rd** pairs (21 pairs today); CI **55 → ~60** named steps |
| New JS bundle implies ~9th entry (§8) | **11th** `js.Build` entry (10 today incl. works-umbrella + poetry); same minify+fingerprint+SRI pattern |
| `site.Data.streams-live` / `site.Data.streams-schedule.upcoming` dot syntax (§3, §6) | **`index site.Data "streams-live"`** etc. — hyphenated data filenames are not dot-addressable in Hugo (corrected inline below) |
| §10 `partials/cite/normalize-page.html` | No such file; cite is split into `normalize-ref.html` / `normalize-library-item.html` / `data-blob.html` / `meta-tags.html` / `fmt-bibtex.html` — plan targets the real partials + the real citable predicate |
| §16 "hard dependency: citation export must ship first" | **SATISFIED** — citation export merged 2026-05-14 (`4b2a75e`). Unblocked. |
| §15 "stream-aware page sidebar … n/a" | Page-sidebar shipped since; plan confirms `/streams/<slug>/` opts out of the cross-template rail consistently |

---

## 1. Scope

**Categories streamed** (all four — streams span the site's full content surface):
- game-dev — game design and prototyping sessions
- research — paper-reading, writing, drafting
- coding — general live coding (site work, side projects)
- creative — music, poetry, drawing, composition

**Platforms:** Twitch (primary live audience) + YouTube Live (simulcast for permanent archive). Site links/embeds YouTube for archive; Twitch only for live click-through.

**Workflow** (broadcaster's view):
1. User schedules a stream in `data/streams-schedule.yaml` (or on Twitch — falls back via API).
2. User goes live on both Twitch + YouTube simultaneously (OBS multi-output or Restream.io).
3. GitHub Action poll (cron */5min) detects the live state, writes `data/streams-live.yaml`, site rebuilds → header pill appears.
4. When stream ends, Action detects transition, creates `content/streams/<date-slug>/index.md` as a draft stub with title/date/category copied from the cached live state.
5. User edits the stub at their convenience: fills `vod_url`, writes show notes, adds `related_essays/garden/research/works`, flips `draft: false`.
6. Output pages (essays / garden / works / research) get an optional `source_stream:` field that auto-renders a "From the stream:" attribution. A linter validates the symmetry.

**Out of scope** (see §15): no live chat embed, no donation widgets, no follower counts, no captions/transcripts (Phase 3+).

---

## 2. Architecture overview

**Approach: fully GitHub-Action-driven (Approach A from brainstorming).** One cron Action polls Twitch + YouTube, mutates `data/streams-*.yaml` and creates auto-stubs in `content/streams/`. Each commit triggers the existing Pages deploy. No external infra; all secrets stay as repo secrets. 5-minute polling cadence with ~5–15 min real-world lag from `LIVE → site shows pill`.

**Decision rationale:**
- Matches the existing static-site model. Zero new external systems.
- 5-minute lag is acceptable for casual visitors (the live audience finds the user on Twitch directly).
- Approach B (Cloudflare Worker for sub-5-min live state) is a clean retrofit if lag becomes painful.

**Two-domain data split:**
- **User-authored**: `data/streams-schedule.yaml`, `content/streams/<slug>/index.md` (after stub is filled).
- **Action-authored**: `data/streams-twitch-cache.yaml`, `data/streams-live.yaml`, auto-stub files in `content/streams/`.
- The Action never modifies `data/streams-schedule.yaml` (preserves user-authored entries).

---

## 3. Data files

### `data/streams-schedule.yaml` (user-authored)

```yaml
upcoming:
  - title: "Game dev: hex grid prototype"
    date: 2026-05-15T19:00:00-04:00
    duration_estimate: 120         # minutes
    platforms: [twitch, youtube]
    category: game-dev             # game-dev | research | coding | creative
    summary: "Building out the hex coordinate system for the procgen roguelike."
    tags: [godot, hex-grid, prototype]
```

Sorted by `date` ascending. Past entries (date < now) ignored at render time. User commits manually when scheduling a stream.

### `data/streams-twitch-cache.yaml` (Action-authored)

Same shape as `streams-schedule.yaml`. Populated by polling Twitch's `/helix/schedule` endpoint hourly. Used only as a fallback for entries not present in the manual schedule (matched by date+title approximate equality).

### `data/streams-live.yaml` (Action-authored)

```yaml
last_polled: 2026-05-13T22:15:00Z
live:
  twitch:
    is_live: true
    title: "Game dev: hex grid"
    started_at: 2026-05-13T22:00:00Z
    url: "https://twitch.tv/a3madkour"
  youtube:
    is_live: true
    video_id: "abc123"
    title: "Game dev: hex grid"
    started_at: 2026-05-13T22:00:00Z
    url: "https://youtube.com/watch?v=abc123"
```

Rewritten on every poll. Hugo reads it once per build. If file missing, partials default to "not live."

### Schedule merge logic (Hugo build-time)

```hugo
{{- $manual := (index site.Data "streams-schedule").upcoming | default slice -}}
{{- $cache  := (index site.Data "streams-twitch-cache").upcoming | default slice -}}
{{- /* Manual wins. Match key = date (date-only) + lowercased title.
       Cache entries with a matching key are dropped. */ -}}
{{- $manual_keys := dict -}}
{{- range $manual -}}
  {{- $k := printf "%s|%s" (.date | dateFormat "2006-01-02") (lower .title) -}}
  {{- $manual_keys = merge $manual_keys (dict $k true) -}}
{{- end -}}
{{- $merged := $manual -}}
{{- range $cache -}}
  {{- $k := printf "%s|%s" (.date | dateFormat "2006-01-02") (lower .title) -}}
  {{- if not (index $manual_keys $k) -}}
    {{- $merged = $merged | append . -}}
  {{- end -}}
{{- end -}}
{{- $merged = sort $merged "date" "asc" -}}
```

Filter out past entries: `where $merged "date" "ge" now`.

---

## 4. Content + frontmatter

### Per-stream page frontmatter

`content/streams/<YYYY-MM-DD>-<slug>/index.md`:

```yaml
---
title: "Game dev: hex grid prototype"
date: 2026-05-13T19:00:00-04:00
duration: "2h 15m"
platforms: [twitch, youtube]
vod_url: "https://youtube.com/watch?v=abc123"
twitch_archive_url: ""           # expires after 14d; informational only
archive_url: ""                  # archive.org URL, optional, manual upload
archive_status: archived         # live | archived | removed | private
category: game-dev               # game-dev | research | coding | creative
tags: [godot, hex-grid, prototype]
summary: "Worked through axial vs offset coordinate systems."
related_essays: []               # slugs (no leading /essays/, no trailing /)
related_garden:  ["hex-coordinate-systems", "tile-neighbor-iteration"]
related_research: []
related_works: ["procgen-roguelike"]
draft: false
---

Show notes go here. Markdown body authored post-stream.
```

**Required fields**: `title`, `date`, `platforms` (list), `category` (enum), `archive_status` (enum), `draft` (bool).

**Optional fields**: `duration`, `vod_url`, `twitch_archive_url`, `archive_url`, `tags`, `summary`, `related_*`.

**`archive_status` rendering rules** (in `layouts/streams/single.html`):
- `live` — embed area shows "🔴 Currently live, watch on Twitch →" callout (no YouTube embed).
- `archived` — click-to-load YouTube embed visible; full page rendered.
- `removed` — embed area replaced with "Archive intentionally removed" placeholder; show notes + cross-refs still render.
- `private` — `build: render: never` in `cascade` block (set per-page); not published at all.

**Slug scheme:** `<YYYY-MM-DD>-<title-slug>`. Generated by Action from stream metadata. Date prefix keeps file listings naturally chronological.

### Cross-section frontmatter additions

One optional field added to essays / garden / research themes + questions / works fixtures:

```yaml
source_stream: 2026-05-13-game-dev-hex-coordinates
```

Type: string (must match an existing stream's slug). When set, the section template auto-renders a small attribution block beneath the title:

```html
<p class="from-stream">From the stream: <a href="/streams/<slug>/">2026-05-13 — Game dev: building hex coordinates</a></p>
```

Title pulled via `site.GetPage "/streams/<slug>/"`. If the stream page doesn't exist, the linter (§9) catches it at CI time.

---

## 5. GitHub Action workflow

### `.github/workflows/streams-poll.yaml` (new)

```yaml
name: streams poll
on:
  schedule:
    - cron: '*/5 * * * *'     # every 5 min (GitHub minimum)
  workflow_dispatch:           # manual trigger for testing

permissions:
  contents: write              # to commit polled data + auto-stubs

concurrency:
  group: streams-poll
  cancel-in-progress: false    # let any in-flight run finish before starting the next

jobs:
  poll:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 1 }
      - uses: actions/setup-python@v5
        with: { python-version: '3.x' }
      - name: Poll streams
        env:
          TWITCH_CLIENT_ID:     ${{ secrets.TWITCH_CLIENT_ID }}
          TWITCH_CLIENT_SECRET: ${{ secrets.TWITCH_CLIENT_SECRET }}
          YOUTUBE_API_KEY:      ${{ secrets.YOUTUBE_API_KEY }}
          TWITCH_USER_LOGIN:    ${{ vars.TWITCH_USER_LOGIN }}
          YOUTUBE_CHANNEL_ID:   ${{ vars.YOUTUBE_CHANNEL_ID }}
        run: python3 tools/poll_streams.py
      - name: Commit if changed
        run: |
          git config user.name  "streams-poll-bot"
          git config user.email "noreply@github.com"
          if git status --porcelain | grep -q .; then
            git add data/streams-live.yaml data/streams-twitch-cache.yaml content/streams/
            git commit -m "chore(streams): poll @ $(date -u +%FT%TZ)"
            git pull --rebase
            git push
          fi
```

### `tools/poll_streams.py` (new — Python stdlib only)

Responsibilities, in order:

1. **Twitch OAuth**: client-credentials grant against `https://id.twitch.tv/oauth2/token`. Cache token in-memory only (no persistence — re-acquire each run; tokens last ~60 days, but re-acquiring is cheap).
2. **Twitch live state**: `GET https://api.twitch.tv/helix/streams?user_login=<login>`. Parse `data[].type == "live"`, title, started_at.
3. **YouTube live state probe**: `HEAD https://www.youtube.com/channel/<id>/live` with `allow_redirects=False`. HTTP 200 or 30x = live; 404 = not live. **Avoids the YouTube Data API quota entirely on the hot path.**
4. **Hourly subtask**: if current `minute % 60 < 5` (effectively once per hour), poll Twitch `/helix/schedule?broadcaster_id=<id>` for upcoming streams. Write `data/streams-twitch-cache.yaml`.
5. **Compare to prior `data/streams-live.yaml`**:
    - not-live → live: rewrite live YAML. No content change.
    - live → not-live on either platform: rewrite live YAML AND create auto-stub for the just-ended stream.
6. **Auto-stub creation**:
    - Use the prior live state's title + started_at to compute slug + date.
    - Path: `content/streams/<YYYY-MM-DD>-<slug>/index.md`.
    - **Idempotency**: if file already exists, do not overwrite.
    - Frontmatter: `title`, `date`, `platforms: [twitch, youtube]`, `category: game-dev` (default; user edits), `archive_status: archived`, `vod_url: ""`, `draft: true`. Body is a single placeholder paragraph.
7. **Always exit 0 on transient API failures** (keep prior YAML state). Exit non-zero only on auth-config errors.

### Secrets & vars

Repo Settings → Secrets and variables → Actions:

| Type | Name | Source |
|---|---|---|
| Secret | `TWITCH_CLIENT_ID` | https://dev.twitch.tv/console/apps |
| Secret | `TWITCH_CLIENT_SECRET` | (same) |
| Secret | `YOUTUBE_API_KEY` | https://console.cloud.google.com → APIs → Credentials (Data API v3 enabled) |
| Var    | `TWITCH_USER_LOGIN` | e.g., `a3madkour` |
| Var    | `YOUTUBE_CHANNEL_ID` | e.g., `UCxxxxxxxx` |

Bootstrap path: set the four above, then trigger `workflow_dispatch` manually for the first run to verify before relying on cron.

### Cost & rate limits

- Twitch Helix: 800 requests/min limit. We do 2 requests per run (oauth + streams) + 1/hour for schedule. Well under.
- YouTube Data v3: 10,000 quota units/day. We use **0 units** on the polling hot path (HEAD probe bypasses the API). VOD URL discovery is deferred (see §15).
- GitHub Actions: ~288 runs/day × ~10s = ~48min/day. Public-repo unlimited free.
- Pages deploy: only triggered on commits, which happen on state transitions (typically 0–4 per day during stream weeks). Not on every poll.

---

## 6. Hugo templates + partials

### File layout

```
content/streams/_index.md             # section index frontmatter

layouts/streams/
  list.html                           # /streams/ index (upcoming + filter chips + archive)
  single.html                         # /streams/<slug>/ page
  rss.xml                             # per-section RSS

layouts/partials/streams/
  upcoming.html                       # schedule strip (used on /streams/ AND homepage)
  live-pill.html                      # header live indicator
  embed.html                          # click-to-load YouTube embed
  cross-refs.html                     # bidirectional related-outputs list
  stream-card.html                    # archive entry card (used in list.html)

layouts/partials/header.html          # modify — include live-pill + Streams nav item
layouts/home.html                     # modify — include partials/streams/upcoming.html
layouts/partials/scripts.html         # modify — wire new entry-streams bundle

assets/js/streams.js                  # click-to-load runtime
assets/js/entry-streams.js            # bundle entry
assets/css/main.css                   # append §44 streams

# Modified for source_stream attribution:
layouts/essays/single.html
layouts/garden/single.html
layouts/research-theme/single.html
layouts/research-question/single.html
layouts/works-games/single.html
layouts/works-music/single.html
layouts/works-poetry/single.html
```

### `live-pill.html`

```hugo
{{- $live := index site.Data "streams-live" -}}
{{- $tw := $live.live.twitch -}}
{{- $yt := $live.live.youtube -}}
{{- if or $tw.is_live $yt.is_live -}}
  {{- $url := cond $tw.is_live $tw.url $yt.url -}}
  <a class="header-live-pill" href="{{ $url }}" rel="noopener"
     aria-label="Currently live — watch on {{ cond $tw.is_live "Twitch" "YouTube" }}">
    <span class="header-live-pill-dot" aria-hidden="true"></span>
    <span class="header-live-pill-label">LIVE</span>
  </a>
{{- end -}}
```

Click target: Twitch wins (live audience). When only YouTube is live, link to YouTube. When `data/streams-live.yaml` is missing entirely, the partial emits nothing (no template error).

### `embed.html` (click-to-load YouTube)

```hugo
{{- $video_id := .video_id -}}
<div class="yt-embed" data-video-id="{{ $video_id }}">
  <button class="yt-embed-play" type="button"
          aria-label="Load and play YouTube video">
    <img class="yt-embed-thumb" loading="lazy" alt=""
         src="https://i.ytimg.com/vi/{{ $video_id }}/hqdefault.jpg">
    <span class="yt-embed-play-icon" aria-hidden="true">▶</span>
  </button>
</div>
```

Called from `layouts/streams/single.html` only when `archive_status == "archived"` and `vod_url` is non-empty. Video ID extracted from the YouTube URL in `single.html` via Hugo regex.

### `cross-refs.html`

Per-stream page renders four lists (essays / garden / research / works), each filtered to non-empty entries. Each related slug resolved via `site.GetPage` to render its title + link. Linter (§9) guarantees all slugs resolve.

### `home.html` upcoming-streams strip

New strip below the existing Currently widget. Uses the same merge logic (manual + Twitch cache) and slices the first 2 upcoming entries. Hidden when zero upcoming entries.

### Nav update

`layouts/partials/header.html` adds a 7th nav item between Library and About:

```
Essays · Garden · Research · Works · Library · Streams · About
```

`aria-current="page"` already auto-applied via `hasPrefix` match.

---

## 7. CSS §44

Append to `assets/css/main.css`:

- `.header-live-pill` with red pulsing `@keyframes` on the dot (prefers-reduced-motion → no pulse, static dot)
- `.yt-embed` 16:9 aspect-ratio container; `.yt-embed-thumb` lazy-loaded; `.yt-embed-play-icon` centered red play button
- `.streams-archive-list` grid: 1 col mobile, 2 col @960px (half-screen 1080p — per user feedback memory), 3 col @1280px
- `.stream-card` card visual (date + title + summary + category pill + output counts)
- `.home-streams-strip` matches existing `.home-currently`, `.home-research-strip`, `.home-garden-strip` patterns
- `.from-stream` left-bordered attribution block (burgundy accent)
- `.streams-archive-removed` and `.streams-archive-live` callout placeholders
- `.streams-category-pill` reusable category badge (4 distinct values; one accent per category sharing the tag-chip token palette)

No new tokens introduced. Reuses existing `--color-burgundy`, `--color-ink`, `--color-stone`, `--font-ui`, etc.

---

## 8. JS runtime

### `assets/js/streams.js`

Single responsibility: click-to-load YouTube embed.

```js
export function initStreams() {
  document.querySelectorAll('.yt-embed').forEach((el) => {
    el.addEventListener('click', () => {
      const id = el.dataset.videoId;
      if (!id) return;
      const iframe = document.createElement('iframe');
      iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1`;
      iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
      iframe.allowFullscreen = true;
      iframe.title = 'YouTube video';
      iframe.loading = 'lazy';
      el.replaceChildren(iframe);
      el.classList.add('yt-embed-loaded');
    });
  });
}
```

### `assets/js/entry-streams.js`

```js
import { initStreams } from './streams.js';
initStreams();
```

Output: `streams.<hash>.js`, ~1 KB minified. Loaded on `/streams/<slug>/` pages only:

```hugo
{{- if and (eq .Section "streams") (eq .Kind "page") -}}
  {{- /* same js.Build + minify + fingerprint pattern as other entries */ -}}
{{- end -}}
```

No live-state polling JS — the server-side YAML drives everything.

---

## 9. Linter pairs (two new)

### 16th pair: `check_streams_fixtures.py` + `test_check_streams_fixtures.py`

Validates per-stream fixture frontmatter shape:

- **Required**: `title`, `date`, `platforms` (list, each ∈ {`twitch`, `youtube`}), `category` (∈ enum), `archive_status` (∈ enum), `draft` (bool).
- **Optional with type**: `duration` (string), `vod_url` (string URL), `twitch_archive_url` (string), `archive_url` (string), `tags` (list of strings), `summary` (string), `related_*` (lists of strings).
- **archive_status enum**: `live | archived | removed | private`.
- **category enum**: `game-dev | research | coding | creative`.
- **Cross-validation**: `archive_status == archived` requires `vod_url` non-empty.
- **YAML shape**: `data/streams-schedule.yaml`, `data/streams-twitch-cache.yaml`, `data/streams-live.yaml` validated for top-level keys + entry types.

### 17th pair: `check_streams_links.py` + `test_check_streams_links.py`

Validates bidirectional cross-ref symmetry:

- For each stream X with `related_essays: [Y, Z, ...]`: each `Y` must be a real non-draft essay AND that essay must have `source_stream: X`.
- Repeat for `related_garden`, `related_research`, `related_works`.
- The inverse direction: for each output page with `source_stream: X`, X must be a real non-draft stream AND `X.related_<section>` must include this page's slug.
- Per the existing pattern in `check_works_links.py` (`lyrics_poem ↔ set_to_music`).

### Existing linter extensions

Add optional `source_stream` field to:
- `tools/check_essay_fixtures.py` (allowed field, type string)
- `tools/check_garden_fixtures.py` (same)
- `tools/check_research_fixtures.py` (same)
- `tools/check_works_fixtures.py` (same)

Each linter's unit-test sibling gets one new test asserting `source_stream: "..."` is accepted and an unknown extra field is still rejected.

---

## 10. Citation export integration (Feature 1 alignment)

**Citable predicate extends to streams** when archive is publicly available:

```hugo
{{- $citable_sections := slice "essays" "garden" "research" "works" "streams" -}}
{{- $is_citable := and (in $citable_sections .Section) (eq .Kind "page") -}}
{{- if eq .Section "streams" -}}
  {{- /* Live streams are not yet citable; removed archives ARE
         (the page itself is still authored content). Private = draft-like. */ -}}
  {{- $is_citable = and $is_citable (in (slice "archived" "removed") .Params.archive_status) -}}
{{- end -}}
```

`partials/cite/normalize-page.html` extension for `.Section == "streams"`:
- BibTeX type → `misc`
- BibTeX `note` → `"Live stream broadcast, <start-date>, archived on YouTube"` (or `"...archive intentionally removed"` when `archive_status: removed`)
- `pub_date` / `online_date` ← `.Date.Format "2006-01-02"`

`check_cite_meta.py` (15th linter from Feature 1) gets `streams` added to `CITABLE_PREFIXES`.

---

## 11. Pagefind + RSS + filter chips

### Pagefind

`layouts/streams/list.html` and `single.html` emit:
```html
<span data-pagefind-meta="section:streams" hidden></span>
<span data-pagefind-filter="section:streams" hidden></span>
<span data-pagefind-meta="category:<value>" hidden></span>
<span data-pagefind-meta="archive_status:<value>" hidden></span>
```

`partials/search-modal.html` adds "Streams" to the filter chip row (existing: All / Essays / Garden / Research / Works / Library).

Existing `tools/check_pagefind_meta.py` (13th linter) extends to know `streams` is a valid section value.

### RSS — SUPERSEDED (see §0, decision 2)

~~`layouts/streams/rss.xml` mirrors essays/garden patterns.~~ **No streams RSS.** RSS is essays-only site-wide (`hugo.yaml` `outputs:` + header hardcodes the essays feed; works + library have none by the same decision). Streams are discoverable via the `/streams/` index, the homepage upcoming strip, and Pagefind. No `rss.xml`, no RSS-XSL linter touch.

### Filter chips on `/streams/`

Dimensions:
- **category**: enum (game-dev / research / coding / creative). Always rendered if ≥2 distinct values.
- **year**: derived from `.Date.Year`. Always rendered.
- **tags**: two-tier (primary from `data/filter-chips.yaml` → `streams.primary_tags`; secondary in `<details>` disclosure with search).

Reuses the shared `partials/filter-chips.html`. `data/filter-chips.yaml` extended with a `streams` block (existing pattern from essays/garden/works). `tools/check_filter_chips_config.py` validates the new block.

---

## 12. CI workflow growth

Step count progression:
- After Phase 8 Slice 2: 40 steps.
- + Feature 1 (citation export, 15th linter pair): 40 → 42.
- + Feature 4 (streams, 16th + 17th linter pairs + extended existing linters): 42 → 46.

The streams-poll workflow runs separately on cron, not part of the build CI.

---

## 13. Page weight tier

Add a new tier to `tools/check_page_weights.py` classifier:
- `/streams/<slug>/` — **300 KB** (between essays' 100 KB and library's 500 KB).
  - YouTube thumbnail ~30 KB (lazy-loaded; counts toward weight when measured at full load).
  - Click-to-load JS ~1 KB.
  - Citation data blob ~2 KB.
  - Standard chrome + show notes.
- `/streams/` (the index) — uses default 100 KB.

Test sibling extended with assertions.

---

## 14. Frontmatter additions summary

Pure additive; no required-field changes anywhere.

| Section | New optional field | Type | Linter |
|---|---|---|---|
| Essays | `source_stream` | string (stream slug) | `check_essay_fixtures.py` + `check_streams_links.py` |
| Garden | `source_stream` | string | `check_garden_fixtures.py` + `check_streams_links.py` |
| Research themes | `source_stream` | string | `check_research_fixtures.py` + `check_streams_links.py` |
| Research questions | `source_stream` | string | `check_research_fixtures.py` + `check_streams_links.py` |
| Works (all 3) | `source_stream` | string | `check_works_fixtures.py` + `check_streams_links.py` |

Existing fixtures round-trip without changes.

---

## 15. Out of scope (deferred, fixture-seeded where applicable)

| Capability | Reason | Future trigger |
|---|---|---|
| Real-time live-state (sub-5-min latency) | Approach B retrofit (Cloudflare Worker `/live-state.json`) | If 5-min lag proves painful |
| Auto-discovery of YouTube VOD URLs after stream | YouTube Data API quota cost (search.list = 100 units/call); manual fill is fine for now | If empty `vod_url` stubs become a chore |
| OBS / Streamlabs go-live webhook → instant pill | External infra | If sub-5-min latency matters for the user's audience |
| Stream highlights / clips / chapters | Belongs in show notes initially | Future polish slice |
| Live chat embed on `/streams/<slug>/` | Out of scope; not a personal-site concern | Intentionally never |
| Donation / tip jar / follower count widgets | User explicitly skipped "presence / social links" | Same |
| Multi-language captions / transcripts | Phase 3+ (org-mode pipeline can produce these) | Phase 3 follow-up |
| `/streams/calendar.ics` iCal feed | Cheap; not initial scope | Polish slice |
| Auto archive.org upload on stream end | Manual workflow is fine for the rare "keep forever" stream | If user opts in |
| Per-stream view counts / analytics | Out of scope | Never (intentional) |
| Stream-aware page sidebar entries within stream pages | Per-stream pages are single-section; rail not needed | n/a |

---

## 16. Phase placement

**Independent of Phase 3** — no org-mode required. Show notes are authored directly in markdown.

**Big-slice characterization:**
- New top-level section (nav update, new layouts/partials).
- New GitHub Action workflow + Python poller (new infra).
- 2 new linter pairs + 4 existing linter extensions.
- Citation export integration (depends on Feature 1 having shipped).
- 7 cross-section template touches for `source_stream` attribution.
- CSS §44 + tiny JS bundle.

**Hard dependency:** Feature 1 (citation export) must ship before this slice, since this spec extends Feature 1's citable predicate + adds `streams` to the cite-meta linter's CITABLE_PREFIXES. — **SATISFIED**: citation export merged 2026-05-14 (`4b2a75e`). No longer a blocker.

**Slot options:**
- **β (parallel with Phase 3)** — recommended if the user wants to stream sooner. Phase 3 is independent infrastructure (org-mode pipeline); this is independent infrastructure (streaming pipeline). They can develop in parallel.
- **γ (after Phase 3)** — defer if the user wants to focus on Phase 3 first. Streaming workflow waits.

**Effort estimate** (informal): the action poller + auto-stub logic is ~half a day; the Hugo templates + 2 linter pairs + cross-section frontmatter wiring is ~a full day; CSS + JS + manual QA is ~half a day. ~2 days total + bootstrap time for the Twitch + YouTube API key setup.

**Implementation plan:** drafted only when the slice is actually scheduled (per the user's preference of "design now, implement per-slice later"). When that happens, invoke `superpowers:writing-plans` against this spec.
