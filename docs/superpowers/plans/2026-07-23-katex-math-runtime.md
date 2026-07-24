# KaTeX Math Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render essay math (`\(...\)` inline, `\[...\]` display) to typeset output at build time, shipping zero JavaScript.

**Architecture:** Hugo's native `transform.ToMath` (embedded KaTeX) renders math server-side during `hugo --minify`. Body math is captured by the goldmark passthrough extension + a `render-passthrough.html` hook; math inside other shortcodes goes through a promoted `{{< math >}}` shortcode. KaTeX's CSS + woff2 fonts are self-hosted and loaded only on pages with `has_math`.

**Tech Stack:** Hugo 0.162.1 extended (`transform.ToMath`, goldmark passthrough), vendored KaTeX 0.16.x CSS + woff2, Playwright E2E, Python stdlib linters.

## Global Constraints

- Hugo **extended ≥ 0.162.1** — `transform.ToMath` + passthrough require it (CI pins `HUGO_VERSION=0.162.1`).
- **No npm for the shipped site, no CDN.** KaTeX CSS + fonts are vendored into the repo and self-hosted (same rule as existing fonts). No `<link>` to `cdn.jsdelivr.net` / `fonts.googleapis.com`.
- **woff2 only** for fonts (matches existing subsetting policy); strip woff/ttf `src` entries to avoid console 404s (LHCI errors-in-console audit).
- **Fixture content stays obviously-dummy** — reuse existing `\(E = mc^2\)` / `\(\alpha + \beta = \gamma\)` style; never author prose.
- **Do NOT run `hugo --minify` while a dev server is alive** — it poisons dev-server CSS via MIME mismatch. Kill any dev server first; clean `public/` before building for E2E.
- Production CSS/JS go through `minify | fingerprint` + SRI, matching `main.css`.
- KaTeX output must be `htmlAndMathml` (visual HTML for sighted users + MathML for screen readers) — the site's a11y bar.

---

### Task 1: Passthrough config + render hook (body math renders)

**Files:**
- Modify: `hugo.yaml:37-50` (the `markup.goldmark` block)
- Create: `layouts/_default/_markup/render-passthrough.html`
- Test: `tests/e2e/math.spec.ts`

**Interfaces:**
- Produces: rendered KaTeX HTML (`.katex`, `.katex-display`, `.katex-mathml`) in place of bare `\(...\)` / `\[...\]` in essay body markdown.

- [ ] **Step 1: Write the failing E2E test**

Create `tests/e2e/math.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test('essay body inline + display math renders to KaTeX', async ({ page }) => {
  await page.goto('/essays/example-one/');
  // At least one rendered KaTeX node (inline \(...\)).
  await expect(page.locator('.katex').first()).toBeVisible();
  // The \[...\] display formula renders as a display block.
  await expect(page.locator('.katex-display').first()).toBeVisible();
  // MathML is emitted for assistive tech (htmlAndMathml output).
  await expect(page.locator('.katex-mathml, math').first()).toBeAttached();
  // No raw delimiter leaks into the visible body text.
  await expect(page.locator('main')).not.toContainText('\\(');
  await expect(page.locator('main')).not.toContainText('\\[');
});
```

- [ ] **Step 2: Build and run the test to verify it fails**

Run:
```bash
rm -rf public && hugo --minify && npx playwright test math.spec.ts
```
Expected: FAIL — bare `\(...\)` is not yet captured; no `.katex` nodes exist (raw delimiters still visible in `main`).

- [ ] **Step 3: Enable the passthrough extension in `hugo.yaml`**

Replace the `markup:` block (`hugo.yaml:37-50`) so `goldmark` gains an `extensions.passthrough` entry. The full new `markup` block:

```yaml
markup:
    goldmark:
        renderer:
            # B.1.1: ox-hugo emits `@@html:<a>...</a>@@` snippets for rewritten
            # org-roam links; without unsafe:true Goldmark strips the anchors
            # and shows `<!-- raw HTML omitted -->` in their place.  All site
            # content is author-controlled (no user submissions), so unsafe is fine.
            unsafe: true
        extensions:
            # Build-time math: capture the two canonical delimiter pairs
            # (ox-hugo / org-math-lint output) and hand them to the
            # render-passthrough hook -> transform.ToMath. Single-$ is
            # deliberately NOT enabled (would clobber prose dollar signs).
            passthrough:
                enable: true
                delimiters:
                    block:
                        - ['\[', '\]']
                    inline:
                        - ['\(', '\)']
    highlight:
        style: dracula
    tableOfContents:
        startLevel: 2
        endLevel: 6
        ordered: false
```

- [ ] **Step 4: Create the passthrough render hook**

Create `layouts/_default/_markup/render-passthrough.html`:

```go-html-template
{{- /* Build-time math render hook. .Inner is the math source with delimiters
       already stripped by the passthrough extension; .Type is "inline" or
       "block". transform.ToMath (embedded KaTeX) renders it server-side.
       throwOnError fails the build on invalid LaTeX (org-math-lint should
       have caught it pre-publish; this is the backstop). */ -}}
{{- $opts := dict "displayMode" (eq .Type "block") "throwOnError" true "output" "htmlAndMathml" -}}
{{- with try (transform.ToMath .Inner $opts) -}}
  {{- with .Err -}}
    {{- errorf "render-passthrough: cannot render math in %q: %s" $.Page.File.Path . -}}
  {{- else -}}
    {{- .Value -}}
  {{- end -}}
{{- end -}}
```

- [ ] **Step 5: Verify no unintended passthrough captures outside essays**

Run:
```bash
grep -rn --include='*.md' -E '\\\(|\\\[' content/ | grep -v '/essays/' || echo "no non-essay math markers"
```
Expected: `no non-essay math markers` (confirms enabling passthrough site-wide only affects essays today). If any appear, note them — they will render but be unstyled (CSS is essays-gated); acceptable per spec non-goals, but flag in the commit message.

- [ ] **Step 6: Rebuild and run the test to verify it passes**

Run:
```bash
rm -rf public && hugo --minify && npx playwright test math.spec.ts
```
Expected: PASS — `.katex` and `.katex-display` present, no raw delimiters in `main`.

- [ ] **Step 7: Commit**

```bash
git add hugo.yaml layouts/_default/_markup/render-passthrough.html tests/e2e/math.spec.ts
git commit -m "feat(math): build-time body math via passthrough + transform.ToMath"
```

---

### Task 2: Promote the `math` shortcode to a real renderer

**Files:**
- Modify: `layouts/shortcodes/math.html` (replace the stub)
- Test: `tests/e2e/math.spec.ts` (add a case)

**Interfaces:**
- Consumes: `.Inner` = raw math *including* delimiters, e.g. `\(a^2 + b^2 = c^2\)` or `\[...\]`.
- Produces: rendered KaTeX HTML; the `.math-stub[data-pending]` container no longer appears in output.

- [ ] **Step 1: Write the failing test case**

Append to `tests/e2e/math.spec.ts`:

```typescript
test('wrapped {{< math >}} shortcode renders and stub is gone', async ({ page }) => {
  await page.goto('/essays/example-one/');
  // The stub container must no longer exist anywhere.
  await expect(page.locator('.math-stub[data-pending]')).toHaveCount(0);
  // example-one has three math spots; all three render as KaTeX.
  expect(await page.locator('.katex').count()).toBeGreaterThanOrEqual(3);
});
```

- [ ] **Step 2: Build and run to verify it fails**

Run:
```bash
rm -rf public && hugo --minify && npx playwright test math.spec.ts
```
Expected: FAIL — `.math-stub[data-pending]` still present (wrapped form still stubbed); `.katex` count is 2, not ≥3.

- [ ] **Step 3: Replace the shortcode**

Overwrite `layouts/shortcodes/math.html`:

```go-html-template
{{- /* Math shortcode. Renders math nested inside other shortcodes (the wrapped
       authoring form, e.g. inside {{</* definition */>}}). .Inner carries the
       delimiters; strip them, detect display vs inline from the marker, and
       render server-side via transform.ToMath (embedded KaTeX). Body-level math
       goes through the passthrough render hook instead. */ -}}
{{- $raw := .Inner | strings.TrimSpace -}}
{{- $display := hasPrefix $raw "\\[" -}}
{{- $inner := $raw -}}
{{- if $display -}}
  {{- $inner = strings.TrimSuffix "\\]" (strings.TrimPrefix "\\[" $raw) -}}
{{- else -}}
  {{- $inner = strings.TrimSuffix "\\)" (strings.TrimPrefix "\\(" $raw) -}}
{{- end -}}
{{- $opts := dict "displayMode" $display "throwOnError" true "output" "htmlAndMathml" -}}
{{- with try (transform.ToMath $inner $opts) -}}
  {{- with .Err -}}
    {{- errorf "math shortcode: cannot render %q: %s" $inner . -}}
  {{- else -}}
    {{- .Value -}}
  {{- end -}}
{{- end -}}
```

- [ ] **Step 4: Rebuild and run to verify it passes**

Run:
```bash
rm -rf public && hugo --minify && npx playwright test math.spec.ts
```
Expected: PASS — no stub, `.katex` count ≥ 3.

- [ ] **Step 5: Confirm the `has_math` coupling linter still passes**

Run:
```bash
python3 tools/check_math.py && python3 tools/test_check_math.py
```
Expected: both OK — the shortcode still contains `\(` markers pre-render, so coupling is unchanged.

- [ ] **Step 6: Commit**

```bash
git add layouts/shortcodes/math.html tests/e2e/math.spec.ts
git commit -m "feat(math): promote math shortcode from stub to transform.ToMath renderer"
```

---

### Task 3: Wrap example-five nested block math (authoring contract)

**Files:**
- Modify: `content/essays/example-five/index.md:23,27`
- Test: `tests/e2e/math.spec.ts` (add a case)

**Interfaces:**
- Consumes: the `math` shortcode from Task 2.
- Produces: rendered math inside `.block-definition` and `.block-proof` on `/essays/example-five/`.

- [ ] **Step 1: Write the failing test case**

Append to `tests/e2e/math.spec.ts`:

```typescript
test('math nested in AMS blocks renders on example-five', async ({ page }) => {
  await page.goto('/essays/example-five/');
  // Definition block contains rendered math (was bare \(x_0\)).
  await expect(page.locator('.block-definition .katex').first()).toBeVisible();
  // Proof block contains rendered math (was bare \(\alpha + \beta = \gamma\)).
  await expect(page.locator('.block-proof .katex').first()).toBeVisible();
  // No raw delimiter leaks anywhere in the body.
  await expect(page.locator('main')).not.toContainText('\\(');
});
```

- [ ] **Step 2: Build and run to verify it fails**

Run:
```bash
rm -rf public && hugo --minify && npx playwright test math.spec.ts
```
Expected: FAIL — bare `\(x_0\)` inside the definition is emitted as raw HTML by `ams-block.html`, so passthrough never sees it; `.block-definition .katex` does not exist.

- [ ] **Step 3: Wrap the nested math in the fixture**

In `content/essays/example-five/index.md`, line 23, change:
```
{{< definition title="Continuity" >}}A function `f` is continuous at \(x_0\) if for every `ε > 0` there exists `δ > 0` such that `|x - x_0| < δ` implies `|f(x) - f(x_0)| < ε`.{{< /definition >}}
```
to:
```
{{< definition title="Continuity" >}}A function `f` is continuous at {{< math >}}\(x_0\){{< /math >}} if for every `ε > 0` there exists `δ > 0` such that `|x - x_0| < δ` implies `|f(x) - f(x_0)| < ε`.{{< /definition >}}
```

And line 27, change:
```
{{< proof of="Intermediate Value" >}}Suppose without loss of generality that `f(a) < c < f(b)`. Lorem ipsum proof sketch \(\alpha + \beta = \gamma\).{{< /proof >}}
```
to:
```
{{< proof of="Intermediate Value" >}}Suppose without loss of generality that `f(a) < c < f(b)`. Lorem ipsum proof sketch {{< math >}}\(\alpha + \beta = \gamma\){{< /math >}}.{{< /proof >}}
```

- [ ] **Step 4: Rebuild and run to verify it passes**

Run:
```bash
rm -rf public && hugo --minify && npx playwright test math.spec.ts
```
Expected: PASS — both block-nested formulas render; no raw delimiters.

- [ ] **Step 5: Confirm fixture + coupling linters still pass**

Run:
```bash
python3 tools/check_math.py && python3 tools/check_fixtures.py
```
Expected: both OK (`has_math: true` still matches the `\(` markers now inside the shortcode).

- [ ] **Step 6: Commit**

```bash
git add content/essays/example-five/index.md tests/e2e/math.spec.ts
git commit -m "feat(math): wrap example-five block-nested math in math shortcode"
```

---

### Task 4: Vendor KaTeX CSS + fonts, conditional load, §50 overrides

**Files:**
- Create: `assets/css/katex.css` (vendored, path-rewritten)
- Create: `static/fonts/katex/*.woff2`
- Modify: `layouts/partials/head.html:41` (add conditional `<link>` after the main.css block)
- Modify: `assets/css/main.css` (append §50)
- Test: `tests/e2e/math.spec.ts` (add a case)

**Interfaces:**
- Consumes: rendered `.katex` markup from Tasks 1–3.
- Produces: styled math on `has_math` pages; zero added CSS on non-math pages.

- [ ] **Step 1: Write the failing test case**

Append to `tests/e2e/math.spec.ts`:

```typescript
test('katex stylesheet loads on math pages only', async ({ page }) => {
  await page.goto('/essays/example-one/');
  await expect(page.locator('link[rel="stylesheet"][href*="katex"]')).toHaveCount(1);
  // Rendered math is actually styled: KaTeX applies a KaTeX font-family.
  const ff = await page.locator('.katex').first().evaluate(
    (el) => getComputedStyle(el).fontFamily,
  );
  expect(ff.toLowerCase()).toContain('katex');

  // Non-math page (homepage) must NOT pull the katex stylesheet.
  await page.goto('/');
  await expect(page.locator('link[rel="stylesheet"][href*="katex"]')).toHaveCount(0);
});
```

- [ ] **Step 2: Build and run to verify it fails**

Run:
```bash
rm -rf public && hugo --minify && npx playwright test math.spec.ts
```
Expected: FAIL — no katex stylesheet linked anywhere; `.katex` font-family is inherited (not a KaTeX font).

- [ ] **Step 3: Fetch and vendor KaTeX CSS + woff2 fonts**

Download a pinned KaTeX 0.16.x release (no npm — a release tarball). Use `0.16.22` (latest 0.16.x; class names `.katex`, `.katex-display`, `.katex-mathml`, `.katex-html` are stable across all 0.16.x, so this pairs with Hugo 0.162.1's embedded KaTeX):

```bash
cd /tmp
curl -sL -o katex.tar.gz https://github.com/KaTeX/KaTeX/releases/download/v0.16.22/katex.tar.gz
tar xzf katex.tar.gz          # -> /tmp/katex/katex.min.css, /tmp/katex/fonts/*.woff2 (+ .woff/.ttf)
```

Vendor woff2 fonts:
```bash
mkdir -p static/fonts/katex
cp /tmp/katex/fonts/*.woff2 static/fonts/katex/
ls static/fonts/katex/        # ~20 KaTeX_*.woff2 files
```

Create `assets/css/katex.css` from `katex.min.css` with two edits: (a) a provenance header comment, (b) `@font-face` `src` rewritten to woff2-only, absolute `/fonts/katex/` paths. Do the rewrite mechanically, then hand-prepend the header:

```bash
# Rewrite: keep only the woff2 url, repoint it at /fonts/katex/, drop woff/ttf.
sed -E "s#url\(fonts/(KaTeX_[A-Za-z0-9-]+)\.woff2\) format\('woff2'\)[^;]*#url(/fonts/katex/\1.woff2) format('woff2')#g" \
    /tmp/katex/katex.min.css > assets/css/katex.css
```

Then prepend this provenance header to `assets/css/katex.css` (sets the vendor-provenance convention the d3 dir lacks):

```css
/* Vendored KaTeX 0.16.22 stylesheet. Source:
   https://github.com/KaTeX/KaTeX/releases/download/v0.16.22/katex.tar.gz
   Edits from upstream katex.min.css:
     - @font-face src rewritten to woff2-only, absolute /fonts/katex/ paths
       (woff/ttf dropped; all target browsers support woff2).
   Fonts live in static/fonts/katex/. Loaded conditionally on has_math pages
   via layouts/partials/head.html. Pairs with Hugo's embedded KaTeX
   (transform.ToMath); verify rendering if bumping Hugo or this version. */
```

Verify the rewrite left no `woff)`/`ttf)` or relative `url(fonts/` references:
```bash
grep -E "url\(fonts/|format\('(woff|truetype)'\)" assets/css/katex.css || echo "clean: woff2-only, absolute paths"
```
Expected: `clean: woff2-only, absolute paths`.

- [ ] **Step 4: Add the conditional stylesheet link in `head.html`**

In `layouts/partials/head.html`, immediately after the main.css block (after line 41, before the citation block on line 43), insert:

```go-html-template
  {{/* KaTeX CSS — vendored, self-hosted; loaded only on pages that render math.
       Fonts in static/fonts/katex/. See assets/css/katex.css provenance header. */}}
  {{ if .Params.has_math }}
    {{ with resources.Get "css/katex.css" }}
      {{ $katex := . }}
      {{ if hugo.IsProduction }}
        {{ $katex = $katex | minify | fingerprint }}
      {{ end }}
      <link href="{{ $katex.RelPermalink }}" rel="stylesheet"
        {{ with $katex.Data.Integrity }} integrity="{{ . }}" crossorigin="anonymous"{{ end }}>
    {{ end }}
  {{ end }}
```

- [ ] **Step 5: Append §50 hand-rolled overrides to `main.css`**

Append to the end of `assets/css/main.css`:

```css
/* ============================================================
 * §50 Math (KaTeX overrides)
 * Vendored KaTeX CSS (assets/css/katex.css) does the heavy lifting;
 * these are the only hand-rolled tweaks. KaTeX inherits currentColor,
 * so math tracks the theme ink automatically — this just guarantees it
 * and lets wide display math scroll inside its own box.
 * ============================================================ */
.katex { color: var(--color-ink); }
.katex-display {
  overflow-x: auto;
  overflow-y: hidden;
  padding: var(--space-1) 0;
}
```

- [ ] **Step 6: Rebuild and run to verify it passes**

Run:
```bash
rm -rf public && hugo --minify && npx playwright test math.spec.ts
```
Expected: PASS — katex stylesheet present on example-one (count 1), `.katex` font-family contains "katex", stylesheet absent on homepage (count 0).

- [ ] **Step 7: Commit**

```bash
git add assets/css/katex.css static/fonts/katex/ layouts/partials/head.html assets/css/main.css tests/e2e/math.spec.ts
git commit -m "feat(math): vendor self-hosted KaTeX CSS + woff2, conditional load, §50 overrides"
```

---

### Task 5: Page-weight budget, full CI, docs

**Files:**
- Possibly modify: `tools/check_page_weights.py:25-44` (add a per-page budget only if example-one exceeds `/essays/` 200K)
- Modify: `CLAUDE.md` (math pipeline + CSS pipeline sections)
- Modify: `docs/superpowers/specs/2026-06-07-deferred-features-registry.md` (move KaTeX row to SHIPPED)

**Interfaces:** none produced; this task finalizes.

- [ ] **Step 1: Measure page weight after fonts land**

Run:
```bash
rm -rf public && hugo --minify && python3 tools/check_page_weights.py
```
Expected: OK. If `check_page_weights` reports `/essays/example-one/` over its 200K budget (the KaTeX woff2 subset the page pulls may push it over), proceed to Step 2; otherwise skip to Step 3.

- [ ] **Step 2: (Only if over budget) add a per-page budget entry**

In `tools/check_page_weights.py`, in the `BUDGETS_PREFIX` list (`:25`), add a more-specific entry **before** the `("/essays/", 200_000)` line (first-match-wins ordering):

```python
    ("/essays/example-one/", 260_000),  # math kitchen-sink: KaTeX woff2 subset on top of essay CSS
```
Set the number to the measured actual, rounded up to the next 10K. Then update `tools/test_check_page_weights.py` if it asserts the exact table contents (run it: `python3 tools/test_check_page_weights.py`), and re-run `python3 tools/check_page_weights.py` → OK.

- [ ] **Step 3: Run the full local CI mirror**

Run:
```bash
tools/ci-local.sh
```
Expected: all linters green, Hugo build clean, Playwright suite (including `math.spec.ts`) green, LHCI within thresholds. Investigate any failure before proceeding.

- [ ] **Step 4: Update CLAUDE.md**

In the **Math pipeline** section, replace item 4 ("KaTeX runtime — deferred. No math engine ships…") with:

```markdown
4. **KaTeX runtime — build-time, server-side.** Math renders during `hugo --minify` via Hugo's native `transform.ToMath` (embedded KaTeX): the goldmark `passthrough` extension (delimiters `\(...\)` / `\[...\]`) + `layouts/_default/_markup/render-passthrough.html` handle essay-body math; the `{{< math >}}` shortcode (`layouts/shortcodes/math.html`) handles math nested inside other shortcodes (the wrapped authoring form). Output is `htmlAndMathml` (visual + screen-reader MathML). Zero client JS. KaTeX CSS is vendored self-hosted (`assets/css/katex.css` + `static/fonts/katex/*.woff2`), loaded via a conditional `<head>` link gated on `.Params.has_math` (essays only). §50 in main.css holds the small hand-rolled overrides. Extending math to non-essay sections requires adding `has_math` to those schemas (deferred).
```

In the **CSS pipeline** section, add a note that `assets/css/katex.css` is a second, vendored, conditionally-loaded stylesheet (the only exception to the single-stylesheet rule), and add `§50 covers the math (KaTeX) overrides` to the §-list sentence.

Verify referential-integrity linters still pass:
```bash
python3 tools/check_css_refs.py
```
Expected: OK (`.katex*` classes come from vendored CSS; if the scanner flags them, add `katex` prefixes to `tools/css-refs-allowlist.txt` and note why).

- [ ] **Step 5: Graduate the deferred-features registry row**

In `docs/superpowers/specs/2026-06-07-deferred-features-registry.md`, remove the "KaTeX math rendering" row from the pending "Runtime / interactive capabilities" table and add a line under the SHIPPED section pointing to this slice (`docs/superpowers/plans/2026-07-23-katex-math-runtime.md`) and the memory pointer to be written on ship.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md docs/superpowers/specs/2026-06-07-deferred-features-registry.md tools/check_page_weights.py tools/test_check_page_weights.py tools/css-refs-allowlist.txt
git commit -m "docs(math): CLAUDE.md + registry; page-weight budget for math"
```

---

## Self-Review

**Spec coverage:**
- Passthrough + render hook (spec Components #1–2) → Task 1. ✓
- `math` shortcode promotion (Components #3) → Task 2. ✓
- Authoring contract + example-five fixture (spec Authoring contract) → Task 3. ✓
- Vendored CSS/fonts + conditional load + §50 (Components #4–5, CSS delivery) → Task 4. ✓
- Testing/E2E (spec Testing) → Tasks 1–4 each add a `math.spec.ts` case; coupling lint re-run in Tasks 2–3. ✓
- Page weight (spec Testing) → Task 5 Steps 1–2. ✓
- Version-pin risk (spec Known risks) → Task 4 Step 3 (pinned release + provenance + verify). ✓
- Passthrough-scope risk (spec Known risks) → Task 1 Step 5 (grep guard). ✓
- Docs + registry graduation (spec Documentation to update) → Task 5 Steps 4–5. ✓
- §50 collision (spec Known risks) → documented; §50 is free on master, reconcile at recipe merge. ✓

**Placeholder scan:** none — every code/config step shows full content; the only conditional step (Task 5 Step 2) is gated on a measured outcome with an explicit "otherwise skip" branch.

**Type/name consistency:** `transform.ToMath` options dict (`displayMode`/`throwOnError`/`output`) identical in Task 1 hook and Task 2 shortcode; `.Params.has_math` gate identical in Task 4 head link and spec; `.katex` / `.katex-display` / `.katex-mathml` selectors consistent across all test cases; `static/fonts/katex/` and `assets/css/katex.css` paths consistent between Task 4 vendoring, head link, and CLAUDE.md note.
