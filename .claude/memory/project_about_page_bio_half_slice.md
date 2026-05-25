---
name: About page bio half slice — merged
description: Phase 2 leftover (About page minus Now widget) shipped to master 2026-05-11 (merge 4f2df6d, pushed). Layout-only with self-describing .placeholder scaffolding; Now widget still Phase 3-blocked.
type: project
originSessionId: cfd5e26b-590f-4577-aed6-8c8b9f757692
---
**Status:** MERGED + PUSHED on 2026-05-11. Merge commit `4f2df6d`. Branch `about-page-bio-half` deleted.

**What shipped (9 slice commits):**
- `a9e84ee` Hand-authored AM monogram SVG (96×96, currentColor, matches stage-glyph pattern)
- `11ed8d2` content/about/index.md stripped to frontmatter only (layout owns markup)
- `8c28ee9` CSS §29: about-page rules + load-bearing `.placeholder` class (--color-ink-soft, italic + dotted underline; AA-clean in both modes)
- `b946215` Hero with monogram + name + role + pronouns/location placeholder
- `c343928` Bio (3 placeholder paragraphs) + Where (Affiliations + Other places sub-blocks)
- `38c641d` Connect with real email (a3madkour@gmail.com) + GitHub (@a3madkour) + RSS (site-wide + per-section); 3 placeholder rows for Bluesky/Mastodon/itch.io
- `bccff27` Colophon (6 marker rows) + licenses footer
- `5897f51` CLAUDE.md: layouts list + project status entry
- `5d682dc` Licenses footer renders real copyright year via `{{ now.Year }}` (range from 2026); dropped .placeholder class since year is now real and licenses are spec-locked

**Spec + plan committed earlier on master before slice work began:**
- Spec: `docs/superpowers/specs/2026-05-11-about-page-bio-half-design.md` (commits `482785f` + `0c4fae5` contrast fix)
- Plan: `docs/superpowers/plans/2026-05-11-about-page-bio-half.md` (commit `a48eaae`)

**One thing caught during plan-writing worth keeping handy:** the spec originally proposed `--color-ink-fade` for `.placeholder` color, which fails WCAG AA against `--color-stone` in light mode (2.56:1). Switched to `--color-ink-soft` (6.27 light / 7.83 dark). Verified numerically before authoring the plan. The contrast-verifier tool's checked-pair set already covers `--color-ink-soft`/`--color-stone`, so no tool change was needed.

**One thing caught during user verification:** copyright year `© year` was originally a marker placeholder; user asked if it should be dynamic. Switched to `© 2026{{ if gt now.Year 2026 }}–{{ now.Year }}{{ end }}` — proper copyright range form that auto-extends each year. Drop the .placeholder class on that line since the value is now real.

**Why:** Closes the longest-pending Phase 2 leftover. The About page is the only top-nav link that was a stub for the whole project history; it now has structure even though prose authoring waits for the org-mode pipeline.

**How to apply:**
- The `.placeholder` class is the established pattern for "scaffolding awaiting org-mode authoring." Future slices that need similar markers should reuse it rather than introduce a new class.
- The Now widget on /about/ is the one remaining piece from spec §4.2. When Phase 3 lands and `data/now.yaml` exists, add a new `<section class="about-section">` between Bio and Where; populate from data. The rest of the layout doesn't change.
- For the "real prose lands via org-mode" round-trip pattern: the spec's §4 documents the anticipated frontmatter shape (`pronouns`, `location`, `affiliations`, `other_places`, `connect`, `colophon`). When ox-hugo writes those keys, the layout's template logic gets a conditional branch per section: render real values when present, else render the existing `.placeholder` element. The layout doesn't need to be rewritten — just augmented with `{{ if ... }}` guards.

**Pointers:**
- Merge commit: `4f2df6d`
- Files touched: `layouts/about/single.html` (new, ~80 lines), `assets/images/icons/monogram-am.svg` (new, 14 lines), `assets/css/main.css` §29 (new, ~94 lines), `content/about/index.md` (stripped to frontmatter), `CLAUDE.md` (layouts list + status)
