# KaTeX math rendering — build-time server render

**Date:** 2026-07-23
**Status:** Designed (awaiting plan)
**Graduates:** the "KaTeX math rendering" row of `docs/superpowers/specs/2026-06-07-deferred-features-registry.md`

## Summary

Render the math that essays already author (canonical `\(...\)` inline and `\[...\]`
display forms, produced by ox-hugo + `org-math-lint`) into typeset output. Rendering
happens **at build time**, server-side, via Hugo's native `transform.ToMath` (embedded
KaTeX, available since Hugo 0.132; site pins 0.162.1). The site ships **zero JavaScript**
for math — no client runtime, no flash-of-unstyled-math, works with JS disabled, and
adds nothing to the JS bundle graph. The only shipped assets are KaTeX's CSS + woff2
fonts, self-hosted, loaded only on pages that declare `has_math`.

This supersedes the original "client-side KaTeX runtime" framing in `CLAUDE.md`'s math
pipeline section, which predated Hugo's native math support.

## Goals

- Essay body math (`\(...\)`, `\[...\]`) renders as typeset math in the built site.
- Math wrapped in the existing `{{< math >}}` shortcode renders identically — this is the
  authoring path for math nested inside other shortcodes (e.g. inside `{{< definition >}}`).
- Accessible by default: KaTeX `htmlAndMathml` output ships visual HTML **and** MathML.
- No npm, no CDN, no client JS. Self-hosted CSS + fonts, matching the existing font policy.
- Non-math pages pay zero added weight (LHCI gates every representative page).

## Non-goals (explicit, deferred)

- **Math outside essays.** Rendering is technically global (passthrough is site-wide markup
  config), but the KaTeX stylesheet loads only where `has_math` is set, and `has_math` lives
  only on the essay schema today. Garden/research/works math is out of scope; extending it
  means adding `has_math` to those schemas + linters — a separate slice.
- **Single-`$` delimiters.** Only the two canonical backslash forms are enabled, to avoid
  clobbering prose dollar signs (consistent with `check_math.py`'s conservative dollar rule).
- **Client-side re-rendering / interactivity.** Static typeset output only.

## Architecture

Two rendering paths cover the two positions math appears in:

| Position | Mechanism |
|---|---|
| Essay **body** — bare `\(...\)` / `\[...\]` | goldmark **passthrough** extension + a `render-passthrough.html` render hook calling `transform.ToMath` |
| **Inside another shortcode** — `{{< math >}}...{{< /math >}}` | the **`math` shortcode**, promoted from `data-pending` stub to a real `transform.ToMath` renderer |

Both call the same underlying `transform.ToMath`, so output is identical regardless of path.

### Components

1. **`hugo.yaml`** — enable `markup.goldmark.extensions.passthrough` with exactly two
   delimiter pairs:
   - inline: `\(` … `\)`
   - block: `\[` … `\]`

   Single-`$` and `$$` are **not** enabled.

2. **`layouts/_default/_markup/render-passthrough.html`** — the passthrough render hook.
   For each captured passthrough node:
   ```
   {{ transform.ToMath .Inner (dict "displayMode" (eq .Type "block")) }}
   ```
   Non-math passthrough (there is none configured beyond math) falls through as raw `.Inner`.
   `transform.ToMath` default `output` is `htmlAndMathml` — keep the default.

3. **`layouts/shortcodes/math.html`** — replaces the stub. Strips the wrapping delimiter
   from `.Inner`, detects display vs inline by which marker is present (`\[` → display,
   `\(` → inline), and calls `transform.ToMath` with the matching `displayMode`. Emits the
   rendered KaTeX HTML (via `safeHTML`). Retains the paired-shortcode form so
   `check_math.py`'s coupling still sees the inner markers pre-render.

4. **Vendored KaTeX assets**
   - `assets/css/katex.css` — the vendored KaTeX stylesheet, with `@font-face` `src` URLs
     rewritten to a local path (`/fonts/katex/…`).
   - `static/fonts/katex/*.woff2` — the KaTeX woff2 font files (woff2 only, matching the
     existing font subsetting policy; browsers download per-family on demand).
   - **Version pin:** the vendored CSS + fonts must match the KaTeX version Hugo 0.162.1
     embeds. Class names and DOM structure emitted by `transform.ToMath` are version-coupled
     to the CSS. The implementing plan verifies this by rendering a fixture and confirming the
     vendored CSS styles it correctly (no unstyled `.katex` boxes). Record the pinned version
     + upstream source URL in a provenance comment at the top of `katex.css` (sets the
     provenance convention the d3 vendor dir lacks).

5. **`assets/css/main.css` §50 "Math (KaTeX overrides)"** — a *small* hand-rolled block:
   - dark-mode-aware math color, driven by existing `--color-ink` / theme tokens
     (KaTeX defaults to `currentColor`, so this is mostly ensuring inheritance is correct);
   - `.katex-display { overflow-x: auto; }` so wide display math scrolls inside its own box
     rather than overflowing the page (mirrors the existing wide-content scroll pattern).

   The bulk machine-generated CSS stays in the separate vendored `katex.css`, out of the
   hand-rolled stylesheet.

### CSS delivery

`katex.css` is a **separate, conditionally-loaded** stylesheet — a `<link>` in
`layouts/partials/head.html` gated on `.Params.has_math`, run through the same
`minify | fingerprint` + SRI pipeline as `main.css` under production. Rationale:

- **Perf:** non-math pages load nothing extra; LHCI cold-loads every representative page.
- **Provenance:** vendored/generated CSS stays out of the hand-rolled `main.css`.
- **Trade-off accepted:** a second stylesheet is a minor break from the "single stylesheet"
  convention, justified by the two points above.

Because rendering is global but the stylesheet is `has_math`-gated (essays-only), authoring
math outside essays would produce unstyled output — acceptable because math authoring is
essays-only today and enforced as a non-goal above.

## Authoring contract

- **Body math:** bare delimiters — `\(x\)`, `\[ ... \]`.
- **Math inside another shortcode:** wrap in `{{< math >}}\(x\){{< /math >}}`.

Fixtures modelling both:
- `content/essays/example-one/` — already exercises bare inline, bare display, and the
  wrapped form. No change beyond confirming it renders.
- `content/essays/example-five/` — currently has **bare** math inside `{{< definition >}}`
  and `{{< proof >}}`. Update those to the wrapped `{{< math >}}` form so nested block math
  renders and the fixture models the contract.

Fixture math stays obviously-dummy (existing `\(E = mc^2\)`, `\(\alpha + \beta = \gamma\)`,
etc.) — no authored prose.

## Testing & CI

- **New E2E** `tests/e2e/math.spec.ts`:
  - `goto('/essays/example-one/')`
  - assert at least one `.katex` element is present (body math rendered);
  - assert a `.katex-display` element is present (the `\[...\]` display formula);
  - assert a MathML node (`.katex-mathml` / `<math>`) is present (a11y output);
  - assert no `.math-stub[data-pending]` remains and no raw `\(` text is visible.
- **Existing** `tools/check_math.py` + `tools/test_check_math.py` — unchanged; the
  `has_math` ↔ body-marker coupling now additionally guards correct CSS loading.
- **Page weight:** after fonts land, measure `example-one`; bump only that page's budget in
  the page-weight linter if the KaTeX woff2 subset pushes it over (recipe slice set the
  precedent for a per-page budget entry).
- CI wiring: the new E2E spec runs in the existing Playwright step; no new CI step.

## Known risks

- **KaTeX version pinning** (see Components #4) — resolved by verifying rendered output
  against the vendored CSS during implementation.
- **§50 collision** — the parked `recipes` branch also claims `main.css` §50. On `master`
  §50 is currently free. Reconciled (renumber one) when `recipes` merges. Noted, non-blocking.
- **Passthrough scope** — enabling passthrough changes global markdown handling of `\(` and
  `\[`. Verified against existing content (only essays use these; no unintended captures) as
  a plan step.

## Documentation to update on ship

- `CLAUDE.md` math pipeline section — replace the "KaTeX runtime — deferred / no math engine
  ships" note with the shipped build-time mechanism; note the new conditional `katex.css`
  and §50.
- `CLAUDE.md` CSS pipeline — note `katex.css` as the second (vendored, conditional) stylesheet.
- `docs/superpowers/specs/2026-06-07-deferred-features-registry.md` — move the KaTeX row to
  the SHIPPED section with a `project_*_complete.md` pointer.
