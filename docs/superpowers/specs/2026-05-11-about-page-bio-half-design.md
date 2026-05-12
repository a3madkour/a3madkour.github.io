# About page (bio half) — slice design

**Status:** drafted · **Date:** 2026-05-11 · **Slice:** Phase 2 leftover — About page layout + scaffolding
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §4.2

---

## 0. Context for future Claude sessions

The parent spec §4.2 locks the About page as a narrow-column page with six sections: **Hero / Bio / Now / Where / Connect / Colophon**. The Now widget is Phase 3-blocked (pulls from `data/now.yaml`, which the org-mode pipeline will write). This slice ships the other five sections — the "bio half" — as layout-only scaffolding with self-describing marker placeholders that a visitor can read as "this page is mid-build, here is where each part goes." The Now widget will land in a later slice once the org-mode pipeline can populate it.

The site has a hard "no AI text" constraint (parent spec §1, feedback memory). The user explicitly chose **layout-only with marker placeholders** for prose: I do not author the bio, affiliations, colophon, or privacy disclosure. The few values I can verify (the user's email from git config, the GitHub username `a3madkour` from the repo URL, the RSS feed location, the role line already real on the homepage) are populated; everything else renders as a `.placeholder` element with text like "Bio paragraph 1 — to be authored in org-mode."

The slice is small. One new layout, one new hand-authored SVG, one new CSS section (§29), and a frontmatter edit to `content/about/index.md` to strip the inline placeholder body. No new linter, no new fixtures, no new data files.

**Decisions made during brainstorm** (expanded in §2):
- Layout-only with self-describing muted placeholders (`.placeholder` class), not lorem ipsum, not em-dash markers
- Hand-authored SVG monogram (`AM`) in the hero, matching the stage-glyph pattern (`currentColor` stroke)
- Connect block populates email + GitHub + RSS; leaves Bluesky / Mastodon / itch.io as marker rows
- Colophon entirely marker-only (the user did not want me to author even verifiable build facts)
- No portrait photo, no real avatar; the monogram is the permanent first-impression element until the user adds a real avatar themselves
- Now widget deferred entirely (Phase 3-dependent)

---

## 1. Slice scope

### In scope

1. **Layout:** new `layouts/about/single.html` (Hugo resolves `content/about/index.md`'s `type: about` to this). Single template, no partials beyond what already exists (header, footer, scripts). Hugo's lookup order picks this up automatically.
2. **Monogram SVG:** new `assets/images/icons/monogram-am.svg`, hand-authored. ~96px viewBox, the letters `AM` rendered as paths inside a soft burgundy circle stroke, `currentColor` for stroke so theme switching works. Same conventions as the stage glyphs in `assets/images/icons/`. Inlined into the template via `resources.Get | .Content | safeHTML` (matches header.html's RSS/sun icon pattern).
3. **CSS:** new section §29 "About page" in `assets/css/main.css` with these rules:
   - `.about-page` — narrow column wrapper, max-width `~720px`, centered
   - `.about-hero` — flex row (monogram + identity stack), gap, vertical alignment
   - `.about-hero .monogram` — sizing + color
   - `.about-hero h1` — name styling
   - `.about-hero .role` — role-line styling (reuses homepage role-line look or just inherits)
   - `.about-section` — section spacing
   - `.about-section h2` — heading style
   - `.about-section h3` — sub-heading style for Where's two sub-blocks
   - `.placeholder` — muted color, dotted-underline (text-decoration), inherits font; signals "to be filled in" without being noisy
   - `.connect-list` — definition-list styling (label + value rows)
   - `.about-licenses` — small-print footer line (license/copyright row)
4. **Content edit:** `content/about/index.md` keeps its frontmatter (`title`, `description`, `type: about`) but the body (currently the role-line + a parenthetical placeholder) is removed. The new layout renders the page entirely from its own structure; the body content was only there to give the default template something to render.
5. **CLAUDE.md update:** add `layouts/about/single.html` to the layouts list; document the `.placeholder` CSS class (so a future contributor knows it's a load-bearing scaffold marker, not decoration); update the project-status section to note "About page bio half complete; Now widget still Phase 3-blocked."
6. **No CI gates added.** The About page is a singleton; there's no fixture set to lint. The five existing linters keep guarding everything else they already guard.

### Deferred (kept as round-trippable hooks)

| Item | Marker shape today | Round-trip when real lands |
|---|---|---|
| Bio (3 paragraphs) | `<p class="placeholder">Bio paragraph 1 — to be authored in org-mode</p>` × 3 | Org `:BODY:` populates the section; placeholders replaced by the rendered prose |
| Pronouns + location | One `.placeholder` line in the hero ("Pronouns — to be added · Location — to be added") | Two frontmatter fields (`pronouns`, `location`) — when present, render in place; otherwise hide |
| Affiliation list (2 rows) | `<li class="placeholder">Affiliation 1 — to be added</li>` × 2 | Frontmatter `affiliations:` slice, each entry `{name, role, url}` — render real items, drop placeholders |
| "Other places I keep things" (CV / Google Scholar / ORCID / DBLP) | Labels visible, links `.placeholder` | Frontmatter `other_places:` map keyed by label; real entries replace placeholders |
| Connect — Bluesky / Mastodon / itch.io | Three `.placeholder` `<dd>`s | Frontmatter `connect:` map — real entries replace placeholders, the page renders only the channels that exist |
| Colophon — all six rows | All marker | Frontmatter `colophon:` map for build-with / authored-in / set-in / hosted-on / no-AI / privacy |
| Licenses / copyright footer line | `.placeholder` | Frontmatter or site config |
| Real portrait | Monogram (permanent fallback) | `assets/images/about/portrait.{jpg,svg}` — when present, replaces the monogram; the monogram stays for users who omit |
| Now widget (section 3 in spec §4.2) | Section entirely omitted from this slice | Phase 3 slice — `data/now.yaml` populated by ox-hugo, new section template |

### Out of slice (explicit)

- The Now widget. Phase 3-blocked.
- Real bio prose. The user is the only author per the no-AI constraint.
- Real Bluesky / Mastodon / itch.io handles. The user adds these when they have accounts.
- Real affiliation names + URLs. The user adds these.
- A real portrait photo. The monogram is the v1 hero element; the user can add a portrait later by dropping an image and updating the template.
- Frontmatter coercion / data-driven rendering for the placeholder fields. The slice template hard-codes the marker shape in the layout; a later slice (probably the Phase 3 one) wires the frontmatter contract that swaps placeholders for real values.

---

## 2. Decisions captured during brainstorm

| Decision | Reasoning | Where it lives |
|---|---|---|
| Layout-only with marker placeholders over real authored content now | The user is the only author per the no-AI constraint. Marker scaffolding lets the layout ship now; real prose lands via org-mode later. | every section of the template |
| Self-describing muted placeholders (`.placeholder` class) over lorem ipsum or em-dash markers | A visitor opening the page mid-build should be able to tell what each section will contain. Lorem ipsum reads as cargo-culted fixture; em-dashes read as broken. | `assets/css/main.css` §29 |
| Hand-authored SVG monogram over no portrait or generic stock placeholder | The hero needs a visual anchor and the no-AI constraint forbids generated illustrations. A monogram is the lightest hand-authored option and reuses the existing stage-glyph SVG pattern (`currentColor`, theme-aware). | `assets/images/icons/monogram-am.svg` |
| Connect block populates verifiable data (email + GitHub + RSS) and marks the rest | Email + GitHub are knowable from git config / the repo URL. RSS is the site's own. Populating them makes the page useful as a contact card on day one; the unknown handles stay scaffolded. | `layouts/about/single.html` Connect section |
| Colophon all-markers despite verifiable build facts | The user wanted maximally consistent "layout only" behavior; populating only some sections risked drift. The build facts are knowable from CLAUDE.md when the real colophon is written. | `layouts/about/single.html` Colophon section |
| Now widget entirely omitted from this slice over a marker-only Now section | The Now widget's value is freshness — a placeholder Now signals "this site doesn't update," which actively hurts. Better to omit the section heading entirely until the real widget lands. | layout has no Now section |
| Narrow `.reading-column` reuse over a new About-specific column | The reading-column class already exists for essays/garden notes at the right max-width. Adding a new wrapper would just duplicate the rule. | `layouts/about/single.html` root element |
| No new linter | The About page is a singleton; there's no fixture set to validate. The marker placeholders are static template strings; if the user removes one they'll see the page break visually. | (no addition to `tools/`) |

---

## 3. Architecture

### 3.1 Page structure

```
<main class="reading-column about-page">

  <!-- Hero -->
  <section class="about-hero">
    <div class="monogram" aria-hidden="true">
      {{ inlined monogram-am.svg }}
    </div>
    <div class="about-hero-text">
      <h1>Abdelrahman Madkour</h1>
      <p class="role">Games researcher, writer, occasional maker of music and poems.</p>
      <p class="placeholder">Pronouns — to be added · Location — to be added</p>
    </div>
  </section>

  <!-- Bio -->
  <section class="about-section">
    <h2>Bio</h2>
    <p class="placeholder">Bio paragraph 1 — to be authored in org-mode.</p>
    <p class="placeholder">Bio paragraph 2 — to be authored in org-mode.</p>
    <p class="placeholder">Bio paragraph 3 — to be authored in org-mode.</p>
  </section>

  <!-- Where -->
  <section class="about-section">
    <h2>Where</h2>

    <h3>Affiliations</h3>
    <ul>
      <li class="placeholder">Affiliation 1 — to be added</li>
      <li class="placeholder">Affiliation 2 — to be added</li>
    </ul>

    <h3>Other places I keep things</h3>
    <ul>
      <li>CV — <span class="placeholder">link to be added</span></li>
      <li>Google Scholar — <span class="placeholder">link to be added</span></li>
      <li>ORCID — <span class="placeholder">link to be added</span></li>
      <li>DBLP — <span class="placeholder">link to be added</span></li>
    </ul>
  </section>

  <!-- Connect -->
  <section class="about-section">
    <h2>Connect</h2>
    <dl class="connect-list">
      <dt>Email</dt>
      <dd><a href="mailto:a3madkour@gmail.com">a3madkour@gmail.com</a>
          — preferred for substantial things</dd>
      <dt>GitHub</dt>
      <dd><a href="https://github.com/a3madkour">@a3madkour</a></dd>
      <dt>RSS</dt>
      <dd><a href="/index.xml">/index.xml</a> — site-wide;
          per-section feeds at <a href="/essays/index.xml">/essays/</a> and
          <a href="/garden/index.xml">/garden/</a></dd>
      <dt>Bluesky</dt>
      <dd><span class="placeholder">handle to be added</span></dd>
      <dt>Mastodon</dt>
      <dd><span class="placeholder">handle to be added</span></dd>
      <dt>itch.io</dt>
      <dd><span class="placeholder">handle to be added</span></dd>
    </dl>
  </section>

  <!-- Colophon -->
  <section class="about-section">
    <h2>Colophon</h2>
    <ul>
      <li>Built with — <span class="placeholder">to be authored</span></li>
      <li>Authored in — <span class="placeholder">to be authored</span></li>
      <li>Set in — <span class="placeholder">to be authored</span></li>
      <li>Hosted on — <span class="placeholder">to be authored</span></li>
      <li class="placeholder">No-AI claim — to be authored</li>
      <li class="placeholder">Privacy disclosure — to be authored</li>
    </ul>
    <p class="about-licenses placeholder">© year · CC BY-NC-SA 4.0 (writing) · MIT (code)</p>
  </section>

</main>
```

The site's `header.html` and `footer.html` partials wrap this via `baseof.html`. No partial changes.

### 3.2 Monogram SVG

Single-file SVG, ~96 × 96 viewBox. The "AM" glyphs are hand-drawn paths (not a system font, not a webfont call), inside a circle. Stroke uses `currentColor` so theme switching tints the monogram correctly. Style mirrors the existing stage glyphs in `assets/images/icons/`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" role="img" aria-label="AM monogram">
  <circle cx="48" cy="48" r="42" fill="none" stroke="currentColor" stroke-width="2.5"/>
  <!-- A glyph + M glyph as hand-drawn paths -->
  <path ... stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

The exact path data is for the plan to nail down; the design constraint is "looks hand-drawn, not vector-perfect" — same vibe as the seedling/budding/evergreen stage glyphs.

The SVG is inlined into the template via `{{ with resources.Get "images/icons/monogram-am.svg" }}{{ .Content | safeHTML }}{{ end }}` (matching the RSS / sun icon pattern in `header.html`). Inlining lets the `currentColor` stroke pick up the page's text color.

### 3.3 CSS — new §29

Roughly 50–80 lines. Key rules:

```css
/* §29 About page */

.about-page {
  /* .reading-column already gives us max-width + centering;
     about-specific tweaks ride this class. */
  padding-top: 2rem;
  padding-bottom: 4rem;
}

.about-hero {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
}
.about-hero .monogram {
  flex-shrink: 0;
  width: 96px;
  height: 96px;
  color: var(--color-burgundy);
}
.about-hero .monogram svg { display: block; }
.about-hero h1 {
  margin: 0;
  font-size: var(--text-2xl);
}
.about-hero .role {
  margin: 0.25rem 0 0;
  font-style: italic;
  color: var(--color-ink-soft);
}

.about-section {
  margin-top: 2.5rem;
}
.about-section h2 {
  margin: 0 0 0.5rem;
  font-size: var(--text-xl);
}
.about-section h3 {
  margin: 1.25rem 0 0.4rem;
  font-size: var(--text-base);
  color: var(--color-ink-soft);
}

.placeholder {
  /* --color-ink-soft passes AA on --color-stone in both modes (6.27:1 light,
     7.83:1 dark). --color-ink-fade fails AA in light mode (2.56:1) and was
     the original proposal; rejected. The dotted underline + italic style
     differentiate the placeholder from regular muted text. */
  color: var(--color-ink-soft);
  font-style: italic;
  text-decoration: underline dotted var(--color-rule);
  text-underline-offset: 3px;
}

.connect-list { margin: 0; }
.connect-list dt {
  font-weight: 600;
  margin-top: 0.4rem;
}
.connect-list dd {
  margin: 0 0 0.4rem;
}

.about-licenses {
  margin-top: 2rem;
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
}
```

Plan task can refine values when checking actual rendering; these are the shape, not the final pixels.

### 3.4 Hugo lookup

`content/about/index.md` declares `type: about` (already present). Hugo's lookup for a leaf-bundle page picks up `layouts/about/single.html` before `layouts/_default/single.html`. No `hugo.yaml` edit needed.

The body of `content/about/index.md` is stripped to empty (frontmatter only). The new layout renders the page entirely from its own structure; `.Content` is unused (or rendered only as a safety net if the user later types body content, in which case it appears in the bio section). For v1 we just ignore `.Content`.

---

## 4. Anticipated org-mode contract (Phase 3 round-trip)

When the org-mode pipeline lands, the About page's source becomes an org file that ox-hugo exports with this frontmatter shape:

```yaml
title: About
type: about
pronouns: he/him
location: Atlanta, GA
affiliations:
  - { name: "Lab Name", role: "Researcher", url: "https://..." }
  - { name: "Department Name", role: "PhD candidate", url: "https://..." }
other_places:
  cv: "https://..."
  google_scholar: "https://..."
  orcid: "https://..."
  dblp: "https://..."
connect:
  bluesky: "@handle.bsky.social"
  mastodon: "@handle@instance"
  itch: "https://a3madkour.itch.io"
colophon:
  built_with: "Hugo extended ≥ 0.148"
  authored_in: "Emacs + org-mode + org-roam + ox-hugo + org-cite + org-roam-bibtex"
  set_in: "Petrona (body) · Inter (UI) · JetBrains Mono (code)"
  hosted_on: "GitHub Pages"
  no_ai: "No AI wrote any text or made any illustration on this site."
  privacy: "..."
```

And the body of the org file becomes the bio paragraphs (rendered as `.Content` in the bio section).

The layout's render logic (in the Phase 3 slice, not this one) becomes: *if* the frontmatter field exists, render the real value; *else* render the `.placeholder` element. This slice freezes the placeholder shape so the conditional branch can be added without touching the surrounding markup.

---

## 5. Files touched

**New:**
- `layouts/about/single.html`
- `assets/images/icons/monogram-am.svg`

**Modified:**
- `assets/css/main.css` — append §29 (after §28)
- `content/about/index.md` — strip body, keep frontmatter
- `CLAUDE.md` — layouts list addition, `.placeholder` class note, Phase 2 status update

**Not modified:**
- `hugo.yaml` (Hugo's default lookup handles `type: about`)
- Any data file
- Any other layout / partial / shortcode
- Any of the five linter scripts or their unit tests

---

## 6. Acceptance criteria

1. Visiting `/about/` renders the five sections — Hero, Bio, Where, Connect, Colophon — in the order above, in a narrow centered column.
2. The monogram appears in the hero, theme-tinted (burgundy in light mode, theme-adjusted in dark mode).
3. The role line ("Games researcher, writer, occasional maker of music and poems.") matches the homepage's role line verbatim.
4. The Connect block renders real email + GitHub + RSS links (clickable, correct destinations) and shows three `.placeholder` rows for Bluesky / Mastodon / itch.io.
5. Every other prose-content section uses a `.placeholder` element with self-describing text. Reading the page top to bottom, a visitor can tell what each section will eventually contain.
6. All five CI linters pass; their unit tests pass.
7. `hugo --minify` builds cleanly with no warnings (modulo the pre-existing `.Site.Data` deprecation).
8. CSS contrast verifier still passes. The `.placeholder` color (`--color-ink-soft`) is already in the verifier's checked set and clears AA against `--color-stone` in both modes (verified: 6.27:1 light, 7.83:1 dark) — no contrast-tool change is needed.
9. The Now widget (parent spec §4.2 section 3) is intentionally absent; no marker, no heading. Phase 3 adds it.

---

*End of spec.*
