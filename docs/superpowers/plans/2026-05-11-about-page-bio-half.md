# About page (bio half) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship 5 of the 6 About-page sections from parent spec §4.2 (Hero / Bio / Where / Connect / Colophon — Now widget deferred to Phase 3) as layout-only scaffolding with self-describing `.placeholder` elements; verifiable identity facts (email, GitHub, RSS, role line) are populated, everything else is markered for later org-mode authoring.

**Architecture:** One new Hugo layout (`layouts/about/single.html`) renders the entire page; one new hand-authored SVG (`monogram-am.svg`) anchors the hero; one new CSS section (§29 in `main.css`) styles the page and introduces the load-bearing `.placeholder` class. `content/about/index.md`'s body is stripped (frontmatter only) since the layout owns the markup.

**Tech Stack:** Hugo extended ≥ 0.148, hand-authored CSS, hand-authored SVG. No JS changes. No new linter. No new fixtures.

**Slice spec:** `docs/superpowers/specs/2026-05-11-about-page-bio-half-design.md` (commits `482785f`, `0c4fae5`).

---

## File structure

**New files:**
- `assets/images/icons/monogram-am.svg` — hand-authored SVG monogram, 96×96 viewBox, `currentColor` stroke. Sole responsibility: visual hero anchor that themes correctly.
- `layouts/about/single.html` — full About-page template (one file, no sub-partials beyond the existing site shell). Sole responsibility: render the 5 sections with their markup + populated facts + `.placeholder` scaffolding.

**Modified files:**
- `assets/css/main.css` — append §29 "About page" (after existing §28). Sole responsibility: about-specific layout rules + the site-wide `.placeholder` class (kept in §29 because it ships with the About slice and lives near its only consumer for now — can be promoted to §3 typography later if other sections start using it).
- `content/about/index.md` — strip body to frontmatter only.
- `CLAUDE.md` — layouts list addition; `.placeholder` class note; project-status update.

---

## Task 1: Create the monogram SVG

**Files:**
- Create: `assets/images/icons/monogram-am.svg`

- [ ] **Step 1: Author the SVG**

Write to `assets/images/icons/monogram-am.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 96 96"
     role="img"
     aria-label="A M monogram"
     fill="none"
     stroke="currentColor"
     stroke-linecap="round"
     stroke-linejoin="round">
  <circle cx="48" cy="48" r="42" stroke-width="2.5"/>
  <!-- A: left leg up to apex, down to right leg, then crossbar -->
  <path d="M 22 70 L 34 22 L 46 70 M 28 52 L 42 52" stroke-width="3"/>
  <!-- M: left down-stroke up to peak, valley, peak, right down-stroke -->
  <path d="M 52 70 L 52 22 L 62 50 L 72 22 L 72 70" stroke-width="3"/>
</svg>
```

The two letters live in adjacent halves of the 96×96 viewBox (A: x=22..46, M: x=52..72). The circle and letters both use `currentColor` so the consuming element's `color` property tints the whole monogram.

- [ ] **Step 2: Sanity-check the SVG renders**

Run: `python3 -c "import xml.etree.ElementTree as ET; ET.parse('assets/images/icons/monogram-am.svg'); print('parses')"`
Expected: `parses`

- [ ] **Step 3: Commit**

```bash
git add assets/images/icons/monogram-am.svg
git commit -m "Monogram: hand-authored AM SVG for About hero

96x96 viewBox, currentColor stroke (theme-aware), matches stage-glyph
conventions in assets/images/icons/. Inlined into the About layout
via resources.Get | .Content | safeHTML."
```

---

## Task 2: Strip `content/about/index.md` body

**Files:**
- Modify: `content/about/index.md`

- [ ] **Step 1: Rewrite the file (frontmatter only)**

Replace the entire file contents with:

```markdown
---
title: 'About'
description: 'About Abdelrahman Madkour.'
type: 'about'
---
```

The layout owns all rendering; the body content (currently a role line + parenthetical placeholder note) was only needed to give the default template something to render. After this slice, `.Content` is empty.

- [ ] **Step 2: Verify Hugo still parses it**

Run: `hugo --quiet 2>&1 | head -5`
Expected: build succeeds (the about page will still render via the default template until Task 5 lands the new layout — that's fine for this intermediate state).

- [ ] **Step 3: Commit**

```bash
git add content/about/index.md
git commit -m "About content: strip body to frontmatter only

The new layouts/about/single.html (Task 5 of this slice) owns all
markup. .Content is unused on the About page going forward."
```

---

## Task 3: Add CSS §29 — placeholder class + about-page rules

**Files:**
- Modify: `assets/css/main.css` (append after §28, which ends near line ~1462)

- [ ] **Step 1: Find the end of §28 to append after**

Run: `grep -n "^/\* -\+$\|^ \* 2[0-9]\." assets/css/main.css | tail -10`
Expected: shows section 28 marker; note the line number where §28 content ends (just before EOF if §28 is the last section).

Run: `tail -5 assets/css/main.css`
Expected: shows the last few CSS rules; new content appends after them.

- [ ] **Step 2: Append §29 to `assets/css/main.css`**

Append the following at the very end of the file:

```css

/* ------------------------------------------------------------------
 * 29. About page
 *
 * The .placeholder class is load-bearing scaffolding for the About
 * page (Phase 2 leftover slice): it visibly marks the prose blocks
 * that need real authored content via org-mode. Muted color +
 * italic + dotted underline so a visitor reads the page as
 * mid-build, not broken. --color-ink-soft was chosen for AA
 * contrast against --color-stone (6.27:1 light / 7.83:1 dark);
 * --color-ink-fade fails AA in light mode.
 * ------------------------------------------------------------------ */

.about-page {
  padding-top: 2rem;
  padding-bottom: 4rem;
}

.about-hero {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2.5rem;
}
.about-hero .monogram {
  flex-shrink: 0;
  width: 96px;
  height: 96px;
  color: var(--color-burgundy);
}
.about-hero .monogram svg {
  display: block;
  width: 100%;
  height: 100%;
}
.about-hero h1 {
  margin: 0;
  font-size: var(--text-2xl);
}
.about-hero .role {
  margin: 0.35rem 0 0;
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
.about-section ul {
  margin: 0;
  padding-left: 1.25rem;
}
.about-section li {
  margin: 0.2rem 0;
}

.placeholder {
  color: var(--color-ink-soft);
  font-style: italic;
  text-decoration: underline dotted var(--color-rule);
  text-underline-offset: 3px;
}

.connect-list {
  margin: 0;
  display: grid;
  grid-template-columns: max-content 1fr;
  column-gap: 1rem;
  row-gap: 0.35rem;
}
.connect-list dt {
  font-weight: 600;
  color: var(--color-ink);
}
.connect-list dd {
  margin: 0;
}

.about-licenses {
  margin-top: 2.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-rule);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
}
```

- [ ] **Step 3: Re-run the contrast verifier — must still pass**

Run: `python3 tools/check-contrast.py`
Expected: all four documented pairings still PASS in both modes. (`.placeholder` uses `--color-ink-soft`, which is already in the verifier's checked set, so no new pairing is needed.)

- [ ] **Step 4: Commit**

```bash
git add assets/css/main.css
git commit -m "CSS §29: About page rules + .placeholder scaffolding class

New section for About-page-specific layout. .placeholder is the
load-bearing class used throughout the About template to mark prose
content awaiting org-mode authoring; styled with --color-ink-soft
(AA-compliant) + italic + dotted underline. Contrast verifier still
green in both modes."
```

---

## Task 4: Build the layout shell + Hero section

**Files:**
- Create: `layouts/about/single.html`

- [ ] **Step 1: Write the layout file with hero only**

Create `layouts/about/single.html`:

```html
{{ define "main" }}
<main class="reading-column about-page">

  <section class="about-hero">
    <div class="monogram" aria-hidden="true">
      {{ with resources.Get "images/icons/monogram-am.svg" }}{{ .Content | safeHTML }}{{ end }}
    </div>
    <div class="about-hero-text">
      <h1>Abdelrahman Madkour</h1>
      <p class="role">Games researcher, writer, occasional maker of music and poems.</p>
      <p class="placeholder">Pronouns — to be added · Location — to be added</p>
    </div>
  </section>

</main>
{{ end }}
```

- [ ] **Step 2: Build + visit `/about/` in the dev server**

The dev server should already be running (per earlier session). If not, run: `hugo server --buildDrafts --port 1313 &`

Open: `http://localhost:1313/about/`
Expected: page renders with the AM monogram on the left (burgundy in light mode), name + role + placeholder pronouns/location stacked to the right of it. The Bio / Where / Connect / Colophon sections are NOT yet present (next tasks add them).

- [ ] **Step 3: Verify Hugo build still passes (production minify path)**

Run: `rm -rf public resources && hugo --minify 2>&1 | tail -5`
Expected: build succeeds with no errors.

- [ ] **Step 4: Commit**

```bash
git add layouts/about/single.html
git commit -m "About layout: hero with monogram + name + role + placeholders

First section of the About-page layout. Monogram inlined via
resources.Get so the currentColor stroke picks up the page's text
color. Role line is verbatim the homepage role line."
```

---

## Task 5: Add Bio + Where sections

**Files:**
- Modify: `layouts/about/single.html`

- [ ] **Step 1: Append the Bio and Where sections inside `<main>`**

Edit `layouts/about/single.html` — between the closing `</section>` of `.about-hero` and the closing `</main>`, insert:

```html
  <section class="about-section">
    <h2>Bio</h2>
    <p class="placeholder">Bio paragraph 1 — to be authored in org-mode.</p>
    <p class="placeholder">Bio paragraph 2 — to be authored in org-mode.</p>
    <p class="placeholder">Bio paragraph 3 — to be authored in org-mode.</p>
  </section>

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
```

- [ ] **Step 2: Visit `/about/` and verify**

Open: `http://localhost:1313/about/`
Expected: Bio section shows 3 italic dotted-underlined "Bio paragraph N — to be authored" lines. Where section shows the "Affiliations" sub-heading with 2 placeholder list items, then "Other places I keep things" with 4 items each having a real label and a placeholder link span.

- [ ] **Step 3: Commit**

```bash
git add layouts/about/single.html
git commit -m "About layout: Bio + Where sections

Bio is three p.placeholder rows; Where has two sub-blocks
(Affiliations list, Other places I keep things list with CV /
Google Scholar / ORCID / DBLP labels visible, links markered)."
```

---

## Task 6: Add Connect section (real where verifiable, markers otherwise)

**Files:**
- Modify: `layouts/about/single.html`

- [ ] **Step 1: Append the Connect section before `</main>`**

Edit `layouts/about/single.html` — insert after the Where `</section>`:

```html
  <section class="about-section">
    <h2>Connect</h2>
    <dl class="connect-list">
      <dt>Email</dt>
      <dd><a href="mailto:a3madkour@gmail.com">a3madkour@gmail.com</a> — preferred for substantial things</dd>

      <dt>GitHub</dt>
      <dd><a href="https://github.com/a3madkour">@a3madkour</a></dd>

      <dt>RSS</dt>
      <dd><a href="/index.xml">/index.xml</a> — site-wide; per-section feeds at
        <a href="/essays/index.xml">/essays/</a> and
        <a href="/garden/index.xml">/garden/</a></dd>

      <dt>Bluesky</dt>
      <dd><span class="placeholder">handle to be added</span></dd>

      <dt>Mastodon</dt>
      <dd><span class="placeholder">handle to be added</span></dd>

      <dt>itch.io</dt>
      <dd><span class="placeholder">handle to be added</span></dd>
    </dl>
  </section>
```

- [ ] **Step 2: Click the real links to verify**

Open: `http://localhost:1313/about/`
Click Email → triggers a mailto: in your browser (or shows the link target).
Click GitHub → opens `https://github.com/a3madkour`.
Click `/index.xml` → opens the site-wide RSS feed XML.
Click `/essays/index.xml` and `/garden/index.xml` → both open valid RSS feeds (already exist from prior slices).
Verify the three placeholder rows render as italic dotted-underline "handle to be added" text.

Expected: every real link resolves; placeholders are visually distinct.

- [ ] **Step 3: Commit**

```bash
git add layouts/about/single.html
git commit -m "About layout: Connect section with real email/GitHub/RSS

Three real channels (email mailto, GitHub @a3madkour, site-wide
+ per-section RSS feeds) populated from verifiable sources; Bluesky
/ Mastodon / itch.io are markered until the user adds handles.
Uses .connect-list dl grid for label/value alignment."
```

---

## Task 7: Add Colophon section + licenses footer

**Files:**
- Modify: `layouts/about/single.html`

- [ ] **Step 1: Append the Colophon section before `</main>`**

Edit `layouts/about/single.html` — insert after the Connect `</section>`:

```html
  <section class="about-section">
    <h2>Colophon</h2>
    <ul>
      <li><span class="placeholder">Built with — to be authored</span></li>
      <li><span class="placeholder">Authored in — to be authored</span></li>
      <li><span class="placeholder">Set in — to be authored</span></li>
      <li><span class="placeholder">Hosted on — to be authored</span></li>
      <li><span class="placeholder">No-AI claim — to be authored</span></li>
      <li><span class="placeholder">Privacy disclosure — to be authored</span></li>
    </ul>
    <p class="about-licenses placeholder">© year · CC BY-NC-SA 4.0 (writing) · MIT (code)</p>
  </section>
```

- [ ] **Step 2: Verify full-page render**

Open: `http://localhost:1313/about/`
Expected: page now has all 5 sections in order — Hero, Bio, Where, Connect, Colophon. The Colophon's 6 list items are all `.placeholder`, and the licenses footer line is a separate `<p>` with both `.about-licenses` (top border, smaller text) and `.placeholder` (italic + dotted underline + muted color).

Toggle theme to dark mode (top-right toggle). Verify:
- Monogram tints correctly (still readable).
- All `.placeholder` text stays legible (AA contrast).
- Section borders and the about-licenses top border are visible.

- [ ] **Step 3: Commit**

```bash
git add layouts/about/single.html
git commit -m "About layout: Colophon section + licenses footer

Six placeholder rows for build-with / authored-in / set-in /
hosted-on / no-AI claim / privacy. License/copyright footer line is
.about-licenses (top border, small text) and .placeholder (muted)."
```

---

## Task 8: CLAUDE.md update + final CI sweep

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Find and update the layouts list**

Open `CLAUDE.md` and locate the **Content & layouts → Layouts** sub-list (under "Architecture"). Find the line listing `layouts/_default/{baseof,single,list}.html` and the per-section layouts.

Insert a new bullet under the layouts list (after `layouts/blog/{list,single}.html` and before `layouts/404.html`):

```markdown
  - `layouts/about/single.html` — About page (Phase 2 bio half — Hero / Bio / Where / Connect / Colophon; Now widget deferred to Phase 3). All prose content rendered as `.placeholder` scaffolding awaiting org-mode authoring; Email / GitHub / RSS populated from verifiable sources.
```

- [ ] **Step 2: Update the project-status section**

Locate the **Project status (2026-05-08)** section in `CLAUDE.md`. Find the line in the "Phase 2 — remaining slices" section that mentions the About page rewrite. Append a new paragraph above the existing list:

```markdown
**Phase 2 — About page (bio half) complete (2026-05-11).** Five of six sections from parent spec §4.2 shipped (Hero, Bio, Where, Connect, Colophon); Now widget remains Phase 3-blocked. New `layouts/about/single.html` renders the page; new hand-authored `assets/images/icons/monogram-am.svg` anchors the hero; new CSS §29 introduces the load-bearing `.placeholder` class (muted + italic + dotted underline, `--color-ink-soft` AA-compliant). Email + GitHub + RSS are populated from verifiable sources; everything else is a marker placeholder for later org-mode authoring. No new CI gates (About is a singleton page).
```

Also update the "About page rewrite..." bullet to reflect that the bio half is now done — change `About page rewrite (real bio, Now widget, affiliations, connect block, full colophon) — Phase 3-dependent for the Now widget.` to:

```markdown
- About page **Now widget** (the one section from spec §4.2 not yet shipped) — Phase 3-dependent. The other five sections shipped 2026-05-11 as scaffolding.
```

- [ ] **Step 3: Run every CI gate**

Run all six CI-equivalent commands:

```bash
python3 tools/check-contrast.py
python3 tools/check_fixtures.py
python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -3
python3 tools/check_garden_fixtures.py
python3 -m unittest tools/test_check_garden_fixtures.py -v 2>&1 | tail -3
python3 tools/check_garden_links.py
python3 -m unittest tools/test_check_garden_links.py -v 2>&1 | tail -3
python3 tools/check_filter_chips_config.py
python3 -m unittest tools/test_check_filter_chips_config.py -v 2>&1 | tail -3
```

Expected: all pass — contrast verifier green in both modes, fixture linters report 0 problems, unit tests (53 total) all OK.

- [ ] **Step 4: Production build sanity-check**

Run: `rm -rf public resources && hugo --minify 2>&1 | tail -5`
Expected: build succeeds (one `.Site.Data` deprecation warning is pre-existing, OK to ignore).

Confirm the About page rendered correctly:
```bash
grep -c "about-hero\|about-section\|placeholder\|connect-list\|about-licenses" public/about/index.html
```
Expected: > 5 (all the about-specific classes appear in the rendered HTML).

- [ ] **Step 5: Verify the About page bundle is the right size**

The About section has no special JS — it should only ship the core bundle.

Run: `grep -oE 'src=[^ >]+\.js' public/about/index.html`
Expected: only `src=/js/core.<hash>.js` (one line). No essay bundle, no garden bundle.

- [ ] **Step 6: Commit CLAUDE.md and final verification**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md: document About page bio-half slice

Layouts list gets layouts/about/single.html; project status notes
the slice is complete and the Now widget is the remaining piece
for Phase 3."
```

---

## Self-review checklist

- [ ] **Spec coverage:** every requirement in `docs/superpowers/specs/2026-05-11-about-page-bio-half-design.md` maps to a task
  - §1 in-scope item 1 (layout) → Tasks 4, 5, 6, 7
  - §1 in-scope item 2 (monogram SVG) → Task 1
  - §1 in-scope item 3 (CSS §29) → Task 3
  - §1 in-scope item 4 (content frontmatter) → Task 2
  - §1 in-scope item 5 (CLAUDE.md) → Task 8
  - §1 in-scope item 6 (no new linter) → unchanged, validated by Task 8 step 3
  - §3.1 page structure → Tasks 4–7 follow the HTML literally
  - §3.2 monogram → Task 1 contains the full SVG
  - §3.3 CSS → Task 3 contains the full §29
  - §3.4 Hugo lookup → Task 4 step 2 verifies the layout resolves
  - §4 org-mode contract → not implemented this slice (round-trip hook; documented in spec)
  - §6 acceptance criteria 1–9 → each criterion is verifiable from Task 7 step 2 + Task 8 step 3/4/5
- [ ] **No placeholders:** no TBD, no "fill in details", every step shows the actual code/command/expected output. The marker text in the layout (`Bio paragraph 1 — to be authored`) is the literal product, not a plan placeholder.
- [ ] **Type consistency:** CSS class names match between the spec §3.3, the plan's Task 3, and the layout tasks (`.about-page`, `.about-hero`, `.monogram`, `.about-hero-text`, `.role`, `.about-section`, `.placeholder`, `.connect-list`, `.about-licenses` — all consistent).
- [ ] **Acceptance criteria coverage from spec §6:**
  - 1 (five sections in order) — Tasks 4–7, verified by Task 7 step 2
  - 2 (monogram theme-tinted) — Task 7 step 2 (toggle dark mode)
  - 3 (role line matches homepage) — Task 4 step 1 (literal copy)
  - 4 (Connect real links) — Task 6 step 2
  - 5 (every section's prose is a `.placeholder` element) — visible from Task 7 step 2
  - 6 (all CI linters pass) — Task 8 step 3
  - 7 (`hugo --minify` clean) — Task 8 step 4
  - 8 (contrast verifier) — Task 3 step 3 (immediate) + Task 8 step 3 (final)
  - 9 (Now widget intentionally absent) — no Now markup is in the layout (Tasks 4–7); verified visually in Task 7 step 2

---

*End of plan.*
