# Time-synced poetry — design

**Phase:** Independent works/poetry runtime slice. Self-contained — no dependencies on other queued features. Naturally slots after Phase 8 close-out + Feature 1 (citation export).
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md`.
**Origin:** `~/org/projects.org` TODO captured 2026-05-03 ("Pages on the website that are design for poetry where the words show up to the time", 1h effort).

Poetry pages where words appear synced to a timeline. The author embeds `[mm:ss]` markers in the poem body; the site auto-detects them and switches the page into a synced rendering mode with a Play/Pause/Reset/Scrub player + a "Show all" accessibility toggle. Two playback modes from one markup: **audio-driven** when an `audio_url` is set (author recorded themselves reading), **animation-driven** otherwise (silent reveal on a timeline).

Foundation laid here also serves the deferred "Synced-lyrics runtime + two-column lyrics layout" feature — both reuse the same parser + DOM shape.

---

## 1. Scope

**Applies to:** `/works/poetry/<slug>/` pages where the body contains any `[mm:ss]` marker. Poetry without markers continues to render via the existing `works-poetry/single.html` template — no behavior change.

**Two playback modes** from a single markup, auto-selected at runtime:
- **Audio-driven**: `audio_url` frontmatter set + audio file loadable → audio playback drives the reveal. Scrub bar reflects audio currentTime.
- **Animation-driven**: no `audio_url` (or file fails to load) → `requestAnimationFrame` loop drives the reveal. Total duration = highest `[mm:ss]` value in the body.

**Player UI** (consistent across modes):
- ▶ Play / ⏸ Pause button
- ↻ Reset button (rewind to start; audio paused if present)
- Scrub bar (click + drag to seek)
- Time display (`0:16 / 0:42` format, monospace)
- 👁 Show-all toggle (accessibility escape hatch — reveals full poem instantly; audio keeps playing if active)

**Animation style:** fade-in (CSS `opacity` transition over 600ms). Each newly-revealed word gets a brief italic flourish (`@keyframes`, 600ms) before settling to normal.

**Out of scope** (see §10): typewriter / slide-in / karaoke-color variants, speed controls, auto-replay, URL-fragment timestamp share, captions.

---

## 2. Architecture overview

**Approach: Hugo-side parsing + DOM-first runtime (Approach A from brainstorming).**

Hugo template detects `[mm:ss]` markers in `.RawContent`. When found, the template routes through a new partial that parses the body line-by-line and emits structured DOM with `data-t` attributes on word/line spans. JS reads `data-t`, manages playback state, toggles opacity classes. No client-side parsing; no FOUC; no-JS fallback is plain text (markers consumed at build time, never re-emitted).

**Two-mode runtime** is a JS decision based on the presence of `data-audio-src` on the wrapper. No frontmatter flag controls mode.

**Why Hugo-side parsing**: structured data at build time means tiny JS, clean Pagefind indexing, deterministic page weight, and no flash-of-unparsed-markers on initial render.

---

## 3. Marker grammar

**Regex** (single pattern, shared by parser + linter):
```
\[(\d{1,2}):(\d{2})(?:\.(\d{1,2}))?\]
```

**Examples:**
- `[00:03]` — 3 seconds
- `[00:03.5]` — 3.5 seconds
- `[00:03.50]` — 3.5 seconds (1- or 2-digit fractional accepted)
- `[12:34]` — 754 seconds

**Format constraints** (linter-enforced):
- Minutes: 0–99
- Seconds: 0–59
- Fractional: 1–2 digits

**Placement:**
- **Line-level marker**: at the start of a line (after optional leading whitespace). Applies as the line's `data-t`.
- **Word-level marker**: mid-line, immediately preceding the word(s) it times. Applies until the next mid-line marker or end of line.
- **Escape hatch**: `\[mm:ss]` (backslash-prefixed) emits a literal `[mm:ss]` in the rendered output. For the rare poem that legitimately contains bracket-pair text.

**Edge cases:**

| Case | Behavior |
|---|---|
| Untimed line within a synced poem | Inherits the previous line's `data-t` + 0.5s offset. Linter warns. |
| Non-monotonic markers (later marker has smaller value) | Linter warns; runtime plays in marker order — visual jumps possible. |
| Duplicate consecutive markers | Words share a timestamp. No warning. |
| Marker at end-of-line with no following word | Marker ignored. Linter warns. |
| Audio file shorter than last marker | Last words revealed when audio ends (timestamps clamped to audio duration). |
| Audio file longer than last marker | Audio keeps playing past last reveal. Reveal complete; player still active. |
| `audio_url` set but file 404s | Runtime falls back to animation mode. Console warning. |
| Backslash-escaped marker | Emitted as literal `[mm:ss]` in HTML. Not a timing event. |

---

## 4. Hugo parsing + DOM emission

### Auto-detection routing

`layouts/works-poetry/single.html` extension:

```hugo
{{ define "main" }}
<article class="page works-poem-page">
  <span data-pagefind-meta="section:works" hidden></span>
  <span data-pagefind-meta="medium:poetry" hidden></span>
  <span data-pagefind-filter="section:works" hidden></span>
  <header class="works-poem-header">
    <h1>{{ .Title }}</h1>
    <p class="works-poem-meta">
      <time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date.Format "Jan 2006" }}</time>
      {{- with .Params.collection }} · <span class="works-poem-collection">{{ . }}</span>{{- end }}
    </p>
    {{- with .Params.set_to_music }}
      {{ partial "works/audio-pill.html" . }}
    {{- end }}
  </header>

  <section class="works-poem-body">
    {{- $markers := findRE `\[\d{1,2}:\d{2}(?:\.\d{1,2})?\]` .RawContent 1 -}}
    {{- if gt (len $markers) 0 -}}
      {{ partial "works/poem-synced.html" . }}
    {{- else -}}
      {{ .Content }}
    {{- end -}}
  </section>
</article>
{{ end }}
```

`findRE ... 1` short-circuits after the first match. Presence of any marker is sufficient to switch modes. Poems without markers fall through to the existing `.Content` path — zero behavior change.

### Partial signatures

```
layouts/partials/works/
  poem-synced.html              # new — entry partial; takes Page, returns full DOM
  synced-text-parser.html       # new — shared parser; takes raw body + audio URL,
                                 #       returns parsed DOM. Reused by the future
                                 #       music-lyrics layout.
```

Caller:
```hugo
{{ partial "works/poem-synced.html" . }}
```

`poem-synced.html` strips the frontmatter from `.RawContent`, then calls `synced-text-parser.html` with `(dict "raw" $body "audio_url" .Params.audio_url)`.

### DOM emitted

```html
<div class="poem-synced"
     data-duration="42.5"
     {{ with .audio_url }}data-audio-src="{{ . }}"{{ end }}>
  <p class="poem-stanza">
    <span class="poem-line" data-t="3.0">
      <span class="poem-word" data-t="3.0">Lorem </span>
      <span class="poem-word" data-t="3.0">ipsum </span>
      <span class="poem-word" data-t="3.0">dolor </span>
      <span class="poem-word" data-t="3.0">sit </span>
      <span class="poem-word" data-t="3.0">amet,</span>
    </span>
    <br>
    <span class="poem-line" data-t="6.0">…</span>
  </p>

  <p class="poem-stanza">
    <span class="poem-line" data-t="14.0">
      <span class="poem-word" data-t="14.0">ut </span>
      <span class="poem-word" data-t="14.0">labore </span>
      <span class="poem-word" data-t="16.0">et </span>
      <span class="poem-word" data-t="18.0">dolore </span>
      <span class="poem-word" data-t="18.0">magna </span>
      <span class="poem-word" data-t="18.0">aliqua.</span>
    </span>
  </p>
</div>
```

**Structural rules:**
- `data-duration` = max `[mm:ss]` value in the body (in seconds). Overridden client-side by `audio.duration` if `data-audio-src` is set and the file loads.
- Stanzas (separated by blank lines in source) become `<p class="poem-stanza">`.
- Lines within a stanza become `<span class="poem-line">`, separated by `<br>`.
- `<span class="poem-word">` exists when the line has mid-line markers OR the line has no inline markdown features. Per-word granularity preserved.
- When a line has inline markdown features (italic, strong, etc.) and no mid-line markers: the entire line renders via `markdownify` inside a single `<span class="poem-line" data-t="X">`, no word spans. Markdown survives.

### Per-line vs per-word emission logic

For each line in the body (in pseudocode for clarity; implementation in Hugo template syntax):

```
1. Strip leading [mm:ss] if present → becomes line's $data_t.
2. If line has any mid-line [mm:ss] markers:
   a. Tokenize on whitespace.
   b. For each token, assign the most recent $current_t (line $data_t initially).
   c. Update $current_t when an embedded marker is encountered.
   d. Wrap each token in <span class="poem-word" data-t="...">.
   e. Wrap the line in <span class="poem-line" data-t="$data_t">.
3. Else (no mid-line markers):
   a. markdownify the line text (preserves italic/strong).
   b. Wrap result in <span class="poem-line" data-t="$data_t">.
4. Blank lines between content lines → close current <p>, open new <p>.
5. Adjacent content lines within a stanza → emit <br> between them.
```

### Build-time marker stripping

Markers are consumed during parse and never appear in the rendered HTML. The no-JS fallback shows the same word/line text without `[mm:ss]` brackets. Pagefind indexes clean text.

---

## 5. Frontmatter additions

One new optional field on `/works/poetry/*/index.md`:

```yaml
audio_url: "reading.mp3"
```

- **Relative path**: resolved as a page-bundle asset (file lives next to `index.md`).
- **Absolute URL** (`https?://...`): used as-is.
- **Absent or empty string**: runtime uses animation mode.

Existing required fields unchanged. All current poetry fixtures round-trip without modification.

---

## 6. JS runtime

### Module: `assets/js/poem-synced.js`

Responsibilities:

1. **Init**: `querySelectorAll('.poem-synced')` — bail if none.
2. **Per-wrapper setup**: discover `.poem-word` (preferred) or `.poem-line[data-t]` (fallback when no word spans), sort by `data-t`.
3. **Mode selection**: if `data-audio-src` set → audio mode; create `new Audio(src)`, set `audio.preload = 'none'`. Else animation mode.
4. **Player rendering**: build the player DOM in JS (so it's invisible to no-JS readers — no flash of broken controls):
   - Container `<div class="poem-player">`
   - Children: Play button, Reset button, progress bar (with fill + thumb children), time display, "Show all" toggle
   - Optional audio-pill below the player when in audio mode
5. **Play / Pause**:
   - Audio mode: `audio.play()` / `audio.pause()`. Bind to `audio.timeupdate` for tick.
   - Animation mode: `requestAnimationFrame` loop, elapsed = `performance.now() - startedAt + elapsedAt`.
6. **Reveal logic on each tick**: walk sorted spans; for each with `parseFloat(data-t) <= currentTime`:
   - Add `.is-current` (triggers italic flourish animation).
   - After 600ms (the animation duration), remove `.is-current` and add `.is-visible` (full opacity, normal style).
   - Skip if already revealed (idempotent).
7. **Reset**: pause audio (if any), rewind `currentTime`/`elapsedAt` to 0, remove `.is-visible` and `.is-current` from all spans, update progress bar to 0%.
8. **Seek (scrub bar)**: click or drag → calculate target time from cursor position over bar width × duration; set `audio.currentTime` (audio mode) or recompute `elapsedAt` (animation mode); re-evaluate all spans (those before new time → visible; those after → hidden).
9. **Show-all toggle**: toggles `.is-show-all` on wrapper. CSS overrides span opacity. Does NOT pause audio. Re-clicking removes the class — words snap back to whatever their reveal state should be at current time.
10. **Audio failure fallback**: `audio.onerror` → console warning, swap mode to animation, repurpose progress bar with `data-duration`.

### Bundle entry: `assets/js/entry-poetry.js`

```js
import { initPoemSynced } from './poem-synced.js';
initPoemSynced();
```

Output: `poetry.<hash>.js`, ~6–7 KB minified estimate. SRI + classic-script, matching the existing bundle pattern.

### Wiring in `layouts/partials/scripts.html`

Loaded narrowly via:

```hugo
{{- if and (eq .Section "works") (eq .Kind "page") (eq .Type "works-poetry") -}}
  {{- /* same js.Build + minify + fingerprint pattern as other entries */ -}}
{{- end -}}
```

Games and music per-item pages don't load this bundle. The existing `entry-works.js` (filter chips) continues to load on all per-item works pages independently.

---

## 7. CSS — new §45

Append to `assets/css/main.css`. Reuses existing tokens; no new tokens introduced.

```css
/* §45 — synced poetry runtime --------------------------------------- */

.poem-synced { margin: 1.4rem 0 2rem; }

.poem-stanza {
  margin: 0 0 1em 0;
  line-height: 1.85;
  font-size: 1.05rem;
  font-family: var(--font-body);
}

.poem-word,
.poem-line[data-t] {
  opacity: 0.06;
  transition: opacity 600ms ease-out;
}
.poem-word.is-visible,
.poem-line.is-visible {
  opacity: 1;
}

.poem-word.is-current {
  animation: poem-current-flourish 600ms ease-out forwards;
}
@keyframes poem-current-flourish {
  0%   { font-style: italic; opacity: 0.5; }
  60%  { font-style: italic; opacity: 1; }
  100% { font-style: normal; opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
  .poem-word, .poem-line[data-t] { transition: none; }
  .poem-word.is-current { animation: none; font-style: normal; opacity: 1; }
}

.poem-synced.is-show-all .poem-word,
.poem-synced.is-show-all .poem-line[data-t] {
  opacity: 1 !important;
  transition: none;
}

.poem-player {
  display: flex; align-items: center; gap: 0.7rem;
  padding: 0.5rem 0.85rem;
  background: var(--color-paper);
  border: 1px solid var(--color-ink-soft);
  border-radius: 4px;
  margin: 0.5rem 0 1.2rem;
  font-family: var(--font-ui);
  font-size: 0.8rem;
}

.poem-player-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px;
  background: transparent;
  border: 1px solid var(--color-ink-soft);
  color: var(--color-burgundy);
  border-radius: 50%;
  cursor: pointer;
}
.poem-player-btn--primary {
  background: var(--color-burgundy); color: white;
  border-color: var(--color-burgundy);
  width: 34px; height: 34px;
}

.poem-player-progress {
  flex: 1; height: 4px;
  background: rgba(138,58,58,0.12);
  border-radius: 2px;
  cursor: pointer;
  position: relative;
}
.poem-player-progress-fill {
  position: absolute; top: 0; left: 0; height: 100%;
  background: var(--color-burgundy);
  border-radius: 2px;
}
.poem-player-progress-thumb {
  position: absolute; top: 50%;
  width: 11px; height: 11px;
  background: var(--color-burgundy);
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

.poem-player-time {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--color-ink-soft);
  min-width: 70px; text-align: right;
}

.poem-player-show-all {
  display: inline-flex; align-items: center; gap: 0.3rem;
  padding: 4px 9px;
  background: transparent;
  border: 1px solid var(--color-ink-soft);
  color: var(--color-ink-soft);
  border-radius: 99px;
  cursor: pointer;
  font-size: 0.7rem;
}
.poem-player-show-all.is-active {
  background: var(--color-burgundy); color: white;
  border-color: var(--color-burgundy);
}

.poem-audio-pill {
  display: inline-flex; align-items: center; gap: 0.4rem;
  margin-top: 0.4rem;
  padding: 0.4rem 0.7rem;
  background: rgba(138,58,58,0.06);
  border-left: 2px solid var(--color-ink-soft);
  border-radius: 0 3px 3px 0;
  font-size: 0.7rem;
  color: var(--color-ink-soft);
  font-family: var(--font-mono);
}

@media (max-width: 480px) {
  .poem-player { flex-wrap: wrap; }
  .poem-player-progress { order: 99; width: 100%; }
}
```

---

## 8. Linter pair

**New pair** (numbering depends on slice ordering with Feature 1 + Feature 4 — see §11):

`tools/check_poetry_synced.py` + `tools/test_check_poetry_synced.py`:

For every `/content/works/poetry/*/index.md` fixture whose body contains any `[mm:ss]` marker, assert:

1. **Marker shape**: every match conforms to `\[\d{1,2}:\d{2}(?:\.\d{1,2})?\]`. Minutes 0–99, seconds 0–59 (so `[00:60]` fails; `[03:5]` fails). Fractional ≤ 2 digits.
2. **Marker placement**: each marker is at line start OR preceded by whitespace. No embedded `text[00:03]more` without separator.
3. **Audio URL validity** (when `audio_url` set):
   - Relative path → file exists in page bundle directory.
   - Absolute URL → matches `^https?://[^\s]+$`.
4. **Escape round-trip**: backslash-escaped `\[mm:ss]` markers are recognized as escapes (don't trip the marker counter).
5. **Monotonic ordering** (warning only — non-monotonic builds succeed but emit a stderr note).
6. **Empty-line / stanza handling**: at least one stanza must contain content (no empty poems).

Unit-test sibling exercises happy path + each failure mode with synthetic markdown bodies. Pure stdlib (no PyYAML, no markdown parser — regex + line scanning).

**Existing linter extensions:**

- `tools/check_works_fixtures.py` accepts new optional `audio_url` on poetry frontmatter. Existing test sibling gets two new cases (relative + absolute accepted; malformed rejected).

---

## 9. Citation export integration (Feature 1 alignment)

No changes to Feature 1's citable predicate — poetry pages are already covered as `works` + `Kind == "page"`.

One small extension to `partials/cite/normalize-page.html`:

```hugo
{{- if and (eq .Section "works") (eq .Type "works-poetry") .Params.audio_url -}}
  {{- $note = "With audio reading." -}}
{{- end -}}
```

Appended to the BibTeX `note` field (and surfaces in APA/Chicago/MLA via the same path). Lets citing researchers know the work includes a recorded performance.

`check_cite_meta.py` (15th linter from Feature 1) — no changes needed; poetry already validates.

---

## 10. Out of scope (deferred, fixture-seeded where applicable)

| Capability | Reason | Future trigger |
|---|---|---|
| Visual variants beyond fade-in (slide-in, typewriter, etc.) | Initial fade-in covers the dominant case; CSS class hooks reserved for future | Author asks for it |
| Per-word color highlighting (karaoke style) | Visually heavy for poetry; better fit for music lyrics | Lyrics runtime slice |
| Speed controls (0.5x / 1.5x / 2x) | Not in scope; doable later via `audio.playbackRate` | If users request |
| Auto-replay / loop on end | Polish | Same |
| URL-fragment timestamp share (`#t=15`) | Deep-link affordance | Polish slice |
| Captions / closed-captioned audio sync | Phase 3+ (org-mode pipeline produces CC tracks) | Phase 3 follow-up |
| Lyrics runtime + two-column music layout | Already-deferred feature; this spec lays the parser groundwork | Future works runtime slice — reuses `synced-text-parser.html` |
| Custom audio waveform / spectrum visualization | Not a personal-site concern | Never (intentional) |
| Pause-on-page-leave (visibility API) | Could be added; not core | Polish |
| Keyboard shortcuts (space = play/pause) | Polish | Same |

---

## 11. Phase placement

**Independent slice.** No dependency on:
- Feature 1 (citation export) — though it integrates cleanly when both have shipped (§9).
- Feature 4 (streams section) — unrelated.
- Phase 3 (org-mode pipeline) — works with existing markdown fixtures.

**Touches** (file count):
- `layouts/works-poetry/single.html` (modify — 1 line guard + partial call)
- `layouts/partials/works/poem-synced.html` (create)
- `layouts/partials/works/synced-text-parser.html` (create — shared with future lyrics slice)
- `assets/js/poem-synced.js` (create)
- `assets/js/entry-poetry.js` (create)
- `layouts/partials/scripts.html` (modify — wire bundle)
- `assets/css/main.css` (append §45)
- `tools/check_poetry_synced.py` (create)
- `tools/test_check_poetry_synced.py` (create)
- `tools/check_works_fixtures.py` (extend — accept `audio_url`)
- `tools/test_check_works_fixtures.py` (extend)
- `partials/cite/normalize-page.html` (extend if Feature 1 has shipped)
- `.github/workflows/hugo.yaml` (modify — 2 new linter steps)
- 1 new fixture poem under `content/works/poetry/` exercising the synced markup end-to-end

**Effort estimate** (informal): the parser partial is the hardest part (~3 hours); JS runtime ~2 hours; linter ~1 hour; CSS + fixture + plan integration ~2 hours. The original TODO tagged 1h was optimistic for the player-rich interpretation the user landed on — realistic estimate is **one focused day**.

**Slice ordering with other queued features:**

1. Phase 8 close-out (still open — remaining QA checklist items).
2. Feature 1 (citation export) — recommended first since this spec optionally integrates with it.
3. **This slice** — small, self-contained, no blockers.
4. Feature 4 (streams section) — bigger, depends on Feature 1.
5. Feature 2 (org → multi-target export pipeline) — Phase 3-aligned.

If the user wants to ship this slice first instead of in the recommended order, the only minor cost is the `note` field BibTeX integration in §9 — easily added later when Feature 1 lands.

**Implementation plan:** drafted only when the slice is actually scheduled (per the user's preference of "design now, implement per-slice later"). When that happens, invoke `superpowers:writing-plans` against this spec.
