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
- Bare math nested inside AMS block shortcodes (e.g. inside `{{< definition >}}` /
  `{{< proof >}}`) also renders, with **no wrapper required** — `layouts/partials/ams-block.html`
  and `proof.html` pipe their `.Inner` through `markdownify`, which re-runs Goldmark (passthrough
  extension + render hook included) over the nested content. The `{{< math >}}` shortcode
  remains only as an escape hatch for any shortcode that emits `.Inner` raw (not markdownified).
- Accessible by default: KaTeX `htmlAndMathml` output ships visual HTML **and** MathML.
- No npm, no CDN, no client JS. Self-hosted CSS + fonts, matching the existing font policy.
- Non-math pages pay zero added weight (LHCI gates every representative page).

## Non-goals (explicit, deferred)

- **Math outside essays.** Rendering is technically global (passthrough is site-wide markup
  config), but the KaTeX stylesheet loads only where `has_math` is set, and `has_math` lives
  only on the essay schema today. Garden/research/works math is out of scope; extending it
  means adding `has_math` to those schemas + dropping the section from `check_math.py`'s
  `SCOPE_SKIP` — a separate slice. The out-of-scope state is **enforced**, not merely
  documented: `check_math.py`'s scope check fails CI if rendered-math markers appear outside
  `content/essays/`, so unstyled non-essay math can never ship.
- **Single-`$` delimiters.** Only the two canonical backslash forms are enabled, to avoid
  clobbering prose dollar signs (consistent with `check_math.py`'s conservative dollar rule).
- **Client-side re-rendering / interactivity.** Static typeset output only.

## Architecture

One rendering mechanism covers essay body math, and it also covers math nested inside AMS
block shortcodes for free — `{{< math >}}` is a narrow escape hatch, not a separate path:

| Position | Mechanism |
|---|---|
| Essay **body** — bare `\(...\)` / `\[...\]` | goldmark **passthrough** extension + a `render-passthrough.html` render hook calling `transform.ToMath` |
| **Nested inside AMS block shortcodes** (`{{< definition >}}`, `{{< proof >}}`, etc.) — bare `\(...\)` / `\[...\]`, no wrapper | the same passthrough render hook, invoked a second time because `layouts/partials/ams-block.html` (and `proof.html`) pipe `.Inner` through `markdownify`, re-running Goldmark over the nested content |
| **Inside a shortcode that emits `.Inner` raw** (not markdownified) — `{{< math >}}...{{< /math >}}` | the **`math` shortcode**, promoted from `data-pending` stub to a real `transform.ToMath` renderer; escape hatch only, needed when there is no markdownify pass to ride on |

All three call the same underlying `transform.ToMath`, so output is identical regardless of path.

### Components

1. **`hugo.yaml`** — enable `markup.goldmark.extensions.passthrough` with exactly two
   delimiter pairs:
   - inline: `\(` … `\)`
   - block: `\[` … `\]`

   Single-`$` and `$$` are **not** enabled.

2. **`layouts/_default/_markup/render-passthrough.html`** — the passthrough render hook. It
   delegates to a shared `partials/render-math.html` (the single place the `transform.ToMath`
   + `throwOnError` + error-reporting dance lives), passing `inner`, `display` (`eq .Type
   "block"`), and `page`. Rendering is **unconditional** (every captured passthrough node is
   rendered): the hook cannot gate on the page's `has_math`, because when an AMS block pipes
   its `.Inner` through `markdownify`, the hook's `.Page`/`.PageInner` resolve to the home
   page, not the essay, so the flag reads empty there. The essays-only invariant is instead
   enforced by `check_math.py`'s scope check (see §Non-goals). `transform.ToMath` output is
   `htmlAndMathml` (visual + screen-reader MathML). `throwOnError: true` makes invalid LaTeX
   fail the build — the build is the authoritative validity gate in this repo (org-math-lint
   is a pre-publish guard in the authoring pipeline, not part of site CI).

3. **`partials/render-math.html`** — shared render helper. Params (dict): `inner` (LaTeX,
   delimiters stripped), `display` (bool), `page` (for the error message). Calls
   `transform.ToMath` with `throwOnError` and emits its `.Value` directly (ToMath returns
   already-safe `template.HTML`; no `safeHTML` wrapper needed). Both the render hook and the
   `math` shortcode call this, so the error message and options live in one place.

4. **`layouts/shortcodes/math.html`** — replaces the stub. Requires a canonical delimiter
   pair in `.Inner` (`errorf`s otherwise), strips it, detects display vs inline by which
   marker is present (`\[` → display, `\(` → inline), and delegates to `render-math.html`.
   Retains the paired-shortcode form so `check_math.py`'s coupling still sees the inner
   markers pre-render. **Escape hatch only:**
   most content — including math nested inside AMS blocks — never needs this shortcode,
   because it renders via the passthrough render hook directly (body) or via a second
   Goldmark pass triggered by `markdownify` (AMS blocks). It exists for the narrower case of
   a shortcode that emits its `.Inner` as raw HTML with no markdownify step in between.

5. **Vendored KaTeX assets**
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

6. **`assets/css/main.css` §50 "Math (KaTeX overrides)"** — a *small* hand-rolled block:
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
math outside essays *would* produce unstyled output — so it is disallowed and enforced:
`check_math.py`'s scope check fails CI if rendered-math markers (`\(...\)`, `\[...\]`, or
`{{< math >}}`) appear anywhere outside `content/essays/`. Unpaired look-alikes such as the
poems' `\[00:99]` synced-lyric timestamps are not flagged (no matching `\]`, so passthrough
never captures them as math — the check mirrors the renderer by requiring matched delimiters).

## Authoring contract

- **Write bare `\(...\)` / `\[...\]` anywhere in essay content** — body text and inside AMS
  block shortcodes (`{{< definition >}}`, `{{< proof >}}`, etc.) alike. No wrapper needed for
  either case; both render via the same passthrough render hook (directly for body text, via
  a second Goldmark pass for markdownified block inner content).
- **`{{< math >}}...{{< /math >}}`** is reserved for the narrow case of a shortcode that emits
  `.Inner` raw, with no markdownify step to carry the passthrough hook along. None of the
  existing AMS block shortcodes need it.

Fixtures modelling this:
- `content/essays/example-one/` — already exercises bare inline, bare display, and the
  wrapped `{{< math >}}` form (escape-hatch case). No change beyond confirming it renders.
- `content/essays/example-five/` — has **bare** math inside `{{< definition >}}` and
  `{{< proof >}}`, unchanged. The Task 3 addition is a new E2E regression test
  (`tests/e2e/math.spec.ts`, "math nested in AMS blocks renders on example-five") asserting
  this bare-nested-math mechanism actually renders — the fixture itself needed no edit.

Fixture math stays obviously-dummy (existing `\(E = mc^2\)`, `\(\alpha + \beta = \gamma\)`,
etc.) — no authored prose.

## Testing & CI

- **New E2E** `tests/e2e/math.spec.ts`:
  - `goto('/essays/example-one/')`
  - assert at least one `.katex` element is present (body math rendered);
  - assert a `.katex-display` element is present (the `\[...\]` display formula);
  - assert a MathML node (`.katex-mathml` / `<math>`) is present (a11y output);
  - assert no `.math-stub[data-pending]` remains (stub fully promoted) and no raw `\(` / `\[`
    text is visible;
  - `goto('/essays/example-five/')` — regression case guarding the bare-nested-math
    mechanism: assert `.block-definition .katex` and `.block-proof .katex` both render
    (unwrapped `\(x_0\)` / `\(\alpha + \beta = \gamma\)` inside AMS blocks) and no raw `\(`
    leaks into `main`.
- **`tools/check_math.py` + `tools/test_check_math.py`** — the `has_math` ↔ body-marker
  coupling (essays) now uses matched-delimiter detection (mirroring the renderer; `$$` / `$`
  / bare `\begin{}` dropped since none are enabled delimiters), **plus** a new scope check
  that fails CI on rendered-math markers outside `content/essays/`. Both guard correct CSS
  loading.
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
