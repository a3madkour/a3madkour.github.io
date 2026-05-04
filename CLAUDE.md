# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Personal website for Abdelrahman Madkour, built as a Hugo static site with hand-rolled CSS and deployed to GitHub Pages. Long-form essays are the centerpiece, supported by a Zettelkasten-style knowledge garden, research surface, and creative output (games / music / poetry). All content authored in org-mode + org-roam, exported via ox-hugo.

## Commands

- `hugo server --buildDrafts` — dev server with drafts visible
- `hugo --minify` — production build to `public/`
- `python3 tools/check-contrast.py` — WCAG 2.1 contrast verifier (also runs as a required CI gate)

There is no npm step. There is no test suite or linter beyond the contrast checker.

Hugo **extended** (≥ 0.148.0) is required — the GitHub Actions workflow pins `HUGO_VERSION=0.148.0`.

## Architecture

### CSS pipeline — hand-rolled, processed by Hugo

`assets/css/main.css` is a single hand-rolled stylesheet, organized into numbered sections (reset → tokens → typography → layout primitives → header → footer → hero → reduced-motion → page-list/meta). It is consumed by `layouts/partials/head.html` via `resources.Get` + (production) `minify | fingerprint` with SRI integrity.

- **Tokens** are CSS custom properties on `:root` (light) and `:root[data-theme="dark"]` (dark). System dark is handled by `@media (prefers-color-scheme: dark) :root:not([data-theme])`. The `:root[data-theme="dark"]` block and the media-query block carry duplicate values — both must be updated together when the palette changes.
- **WCAG contrast**: `tools/check-contrast.py` parses the `:root` blocks and verifies four documented pairings (ink/stone AAA, ink-soft/stone AA, burgundy/stone AA, steel/stone AA) in both modes. Failure blocks deploy.
- **No Tailwind, no PostCSS, no Node.** Class names are semantic (`.site-header`, `.reading-column`, `.page-list`, `.icon-button`, `.rss-link`, `.colophon`, `.role`, `.is-active`).

### JS pipeline

`assets/js/index.js` is bundled by Hugo's `js.Build` (esbuild) into `js/bundle.<hash>.js`, minified, fingerprinted, and loaded with `defer`. Entry imports `toggle-theme.js` and `nav.js`.

### Theme toggle

Three-state cycle: **system → light → dark → system**.

- Storage key: `theme-pref` in `localStorage` (absent = system mode).
- The CSS responds to a `data-theme` attribute on `<html>` (not a class).
- An inline `<script>` at the very top of `<head>` (in `head.html`) reads `theme-pref` synchronously during HTML parse and applies `data-theme` before any rendering — prevents FOUC for users with a stored preference. Storage access is wrapped in `try/catch` so restricted contexts (private browsing strict, sandboxed iframes) degrade gracefully.
- The bundled `toggle-theme.js` handles the click cycle, button label updates, and an idempotent re-apply.

### Content & layouts

- **Content sections** (in `content/`): `_index.html` (homepage), `about/`, `blog/` (legacy, replaced by `essays/` in Phase 2), and stubs for `essays/`, `garden/`, `research/`, `works/` (each with a placeholder `_index.md` so the top-nav links resolve).
- **Layouts**: `layouts/_default/{baseof,single,list}.html` plus `layouts/blog/{list,single}.html` and `layouts/404.html`. `baseof.html` is a thin semantic wrapper (`.page` div around header/main/footer); per-section layouts override `{{ block "main" }}`.
- **Partials**: `head.html` (inline FOUC script + Google Fonts + main.css link), `header.html` (brand + 5-item top nav + RSS + theme toggle, all icon-driven via inline SVGs from `assets/images/icons/`), `footer.html` (colophon line including "Words are mine; not generated" + social row), `scripts.html` (the JS bundle).
- **Top nav** (locked): Essays / Garden / Research / Works / About. Active item gets `aria-current="page"` via `hasPrefix` match.

### Typography

Three Google Fonts loaded in a single `<link>`: **Petrona** (body, italic + upright at 400/600/700), **Inter** (UI labels), **JetBrains Mono** (code). Display = swap. Token names: `--font-body`, `--font-ui`, `--font-mono`.

### Deployment

`.github/workflows/hugo.yaml` builds with Hugo extended and deploys `public/` to GitHub Pages on pushes to `master`. The build job runs: Install Hugo CLI → Checkout → Setup Pages → **Verify CSS contrast (WCAG)** → Build with Hugo → Upload artifact → Deploy.

## Reference docs

- **Design spec** (visual identity, content architecture, per-page layouts, org-mode contract, build pipeline): `docs/superpowers/specs/2026-05-03-personal-site-design.md`
- **Phase 0+1 implementation plan** (this rebuild): `docs/superpowers/plans/2026-05-04-foundation-and-visual-identity.md`
- The spec's §14 lists the Phase 2+ work still to do (Essays grid, Garden tiles, Research themes, Works pages, Library, Pagefind search).

## Hard constraints (from spec §1)

- **No AI-generated text** anywhere on the site. AI is permitted only for site/app code and code for interactive explorables.
- **No AI-generated illustrations.** SVG icons are hand-authored under `assets/images/icons/`.
- **Privacy by org-export boundary**: content not exported never reaches the site.
- **Accessibility**: WCAG 2.1 AAA for body text, AA for accents; CB-safe palette; never color-only meaning.
