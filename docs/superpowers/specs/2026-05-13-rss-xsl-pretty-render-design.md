# RSS XSL pretty-render — design

**Phase:** Post-Phase-8 polish slice (standalone). Not a Phase 3 dependency.
**Parent context:** Phase 8 Slice 3 QA walkthrough, item 1.6.
**Filed:** 2026-05-13.

---

## 1. Problem

Clicking the header RSS icon on an essays page navigates to `/essays/index.xml`. Browsers render the raw XML in their default tree-view: monospace, gray indentation, no styling. Functional for RSS-literate visitors (it's a valid feed, readers accept it), but visually disconnected from the rest of the site — the page reads as a debug dump, not as something intentional.

This slice adds an XSL stylesheet that pretty-renders the essays feed as a styled HTML page when viewed in a browser, while keeping the underlying XML a valid RSS 2.0 feed for actual RSS readers.

## 2. Goals

- The essays RSS feed (`/essays/index.xml`) opens in a browser as a styled HTML page using the site's typography and color tokens.
- The feed continues to parse correctly in standard RSS readers (no breaking changes to the channel/item XML shape).
- The slice is self-contained (no JavaScript, no theme-toggle button, no external dependencies beyond what `main.css` already pulls in).
- A CI linter pair gates future regressions.

## 3. Non-goals

- Pretty-rendering the garden feed (`/garden/index.xml`) — stays raw XML. The garden is a living surface where the granular firehose suits RSS-literate readers; pretty-rendering it implies an alternate front-end this slice does not want to build.
- Pretty-rendering the site-wide home feed (`/index.xml`).
- An on-page theme toggle button on the XSL-rendered page (would require JS + DOM access to `localStorage` that can't easily be served from XSL without doubling the slice size).
- External reader links ("Open in Feedly / Inoreader / NetNewsWire") — the user's goal is "just look nicer," not RSS onboarding.
- Reading time, tag chips, hero illustrations per item — the feed is a list of items, not a second essays index.
- XSL fingerprinting or content-hashed URLs — content rarely changes; HTTP caching is sufficient.

## 4. Files

```
assets/feed/feed.xsl                              # new — XSL stylesheet (hand-authored)
layouts/essays/rss.xml                            # modify — prepend <?xml-stylesheet ?> processing instruction
tools/check_rss_xsl.py                            # new — linter (RSS XSL linter pair)
tools/test_check_rss_xsl.py                       # new — sibling test (spec §3.1 paired-test pattern)
.github/workflows/hugo.yaml                       # modify — add 2 CI steps (linter + sibling test)
```

No changes to `layouts/partials/header.html`. No changes to `hugo.yaml`. No new section in `assets/css/main.css`. Garden and site-wide feeds untouched.

**Linter pair numbering:** the citation export spec (`2026-05-13-citation-export-design.md`) already reserves "15th linter pair" for `check_cite_meta.py`. This slice's pair number depends on shipping order — written here as "RSS XSL linter pair" without binding to a specific N.

## 5. XSL stylesheet shape (`assets/feed/feed.xsl`)

### 5.1 Document structure

The stylesheet defines an `xsl:stylesheet` root with a single `<xsl:template match="/">` that transforms the document root.

The rendered output is an HTML5 page:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{ channel title }</title>
    <style>{ inline CSS, ~50 lines }</style>
  </head>
  <body>
    <main class="feed">
      <header class="feed-header">
        <h1>{ channel title }</h1>
        <p class="feed-hint">Subscribe in any RSS reader — copy this page's URL.</p>
      </header>
      <ul class="feed-items">
        <xsl:for-each select="/rss/channel/item">
          <li class="feed-item">
            <article>
              <h2><a href="{ item/link }">{ item/title }</a></h2>
              <time datetime="{ ISO-8601 from item/pubDate }">{ formatted date }</time>
              <p>{ item/description }</p>
            </article>
          </li>
        </xsl:for-each>
      </ul>
    </main>
  </body>
</html>
```

### 5.2 Date handling

The RSS template emits dates in RFC-822 form: `Mon, 02 Jan 2006 15:04:05 -0700`. The XSL must render them in two places:

- `<time datetime="...">` — needs ISO-8601 (`2026-05-08`).
- Visible body text — readable form (`2026-05-08` or `May 8, 2026`; pick whichever falls out of XPath string ops most cleanly).

XSL 1.0's `substring` + `translate` functions parse RFC-822 to ISO-8601 by string slicing on the documented format (the feed template's `Format "Mon, 02 Jan 2006 15:04:05 -0700"` is fixed, so positional slicing is safe). If the slicing grows complex, an `<xsl:template name="format-date">` helper keeps the for-each tidy.

### 5.3 Inline CSS — tokens cloned from main.css

The inline `<style>` block carries tokens copied verbatim from `assets/css/main.css`'s `:root` and `:root[data-theme="dark"]` blocks (the same drift-prone pair the site already maintains). Tokens used:

| Use | Light value | Dark value |
|---|---|---|
| Page background | `--color-stone` (`#f6f3eb`) | `--color-stone` dark (`#1a1a1a`) |
| Body text | `--color-ink` (`#1f1d1a`) | `--color-ink` dark (`#e8e6e0`) |
| Secondary text (date) | `--color-ink-soft` | `--color-ink-soft` dark |
| Link | `--color-burgundy` | `--color-burgundy` dark |
| Body font | `--font-body` (Petrona) | same |

Dark mode is gated by `@media (prefers-color-scheme: dark)`. There is no `[data-theme="dark"]` honor on this page because no `<script>` is allowed to run from XSL output (and `localStorage` is not consulted). The page tracks the OS-level setting only.

Google Fonts is loaded with the same `<link rel="stylesheet" href="https://fonts.googleapis.com/...">` URL that `layouts/partials/head.html` uses for Petrona. If blocked or unavailable, CSS `font-family` falls back to `Georgia, serif` (already the site's body fallback).

The inline block is small enough to read in full from the file — ~50 lines including selectors for `body`, `.feed`, `.feed-header`, `.feed-hint`, `.feed-items`, `.feed-item`, `h1`, `h2 a`, `time`, `p`, plus the dark-mode media query.

### 5.4 Layout

- Single centered column. `.feed` width: `min(680px, 90vw)`, margin auto, padding-block: `4rem`.
- Items: vertical list, ~2rem gap between. No card chrome (matches the "look nicer, not a second front-end" framing).
- Heading hierarchy: `h1` (feed title) → `h2` (per-item title). No h3+.
- Mobile: column re-narrows to 90vw, padding-block shrinks to `2rem` below 600px.

## 6. Hugo wiring — `layouts/essays/rss.xml`

Insert one line immediately before the literal `<rss version="2.0" …>` opening tag, so the PI is the first line of rendered output. The existing `{{- $pages := … -}}` data-lookup directives at the top of `layouts/essays/rss.xml` produce no output (the `{{- … -}}` hyphens strip surrounding whitespace), so they can stay above the PI line.

```
{{- printf "<?xml-stylesheet type=\"text/xsl\" href=\"%s\"?>" ((resources.Get "feed/feed.xsl").RelPermalink) | safeHTML }}
```

Why this form:

- `resources.Get "feed/feed.xsl"` reads `assets/feed/feed.xsl`. Hugo's resource pipeline copies it into `public/feed/feed.xsl` at build time.
- `RelPermalink` resolves to a root-relative path (`/feed/feed.xsl` under the default `baseURL`).
- `safeHTML` prevents Hugo from escaping the `<?…?>` angle brackets.
- The PI must precede the `<rss>` root element. Both major browsers (Firefox, Chromium) require this ordering. The linter's PI-placement check (§7.1.6) enforces it.

The garden feed template (`layouts/garden/rss.xml`) is **not** modified — scope guard.

## 7. Linter — RSS XSL pair (`tools/check_rss_xsl.py` + `tools/test_check_rss_xsl.py`)

### 7.1 What the linter asserts

1. `assets/feed/feed.xsl` exists.
2. It parses as XML with `xml.etree.ElementTree`. (XSL is XML.)
3. The root element is `{http://www.w3.org/1999/XSL/Transform}stylesheet`.
4. At least one `<xsl:template match="/">` child exists.
5. The transformation emits an HTML `<style>` element somewhere in the output template (sentinel: if a future refactor accidentally drops the inline style block, this fails).
6. `layouts/essays/rss.xml` (Hugo template source) contains a line emitting the `<?xml-stylesheet` PI before any literal `<rss` substring. Implementation: regex against the file's raw text, looking for `xml-stylesheet` AND `feed/feed.xsl` substrings in any line whose position precedes the first `<rss` occurrence. The template uses Hugo `{{ … }}` directives (not valid XML), so XML parsing is not an option here — text regex is the right tool.
7. `layouts/garden/rss.xml` does **NOT** contain `<?xml-stylesheet` — scope guard so future refactors don't accidentally apply the stylesheet to garden.

### 7.2 Sibling test (`tools/test_check_rss_xsl.py`)

Fixture-driven test pattern per spec §3.1:

1. **happy path** — well-formed XSL + essays PI present before `<rss>` + garden PI absent → exits 0.
2. **missing XSL** — `assets/feed/feed.xsl` does not exist → exits non-zero with a clear message.
3. **missing essays PI** — XSL present but `layouts/essays/rss.xml` has no `<?xml-stylesheet` → exits non-zero.
4. **essays PI after `<rss>`** — PI exists but appears after the `<rss>` opening tag (invalid placement) → exits non-zero (§7.1.6 anchored-regex enforcement).
5. **garden has PI** — scope guard triggered → exits non-zero.

The test uses `pathlib` + `subprocess` to invoke the linter against a `tempfile.TemporaryDirectory()` mirror of the necessary files. Stdlib-only; no pytest dep (matches the existing linter-pair pattern).

### 7.3 CI wiring

`.github/workflows/hugo.yaml` gains 2 named steps in the pre-build linter block (alphabetical by linter name, where existing ordering allows):

```yaml
- name: Check RSS XSL
  run: python3 tools/check_rss_xsl.py
- name: Test RSS XSL linter
  run: python3 tools/test_check_rss_xsl.py
```

Total workflow steps: 40 → 42. Total time impact: <5 seconds (both linters are stdlib + tiny file reads).

## 8. Accessibility

- `<html lang="en">`.
- `<title>` set from `/rss/channel/title`.
- Items use semantic `<article>` > `<h2>` > `<time datetime>` + `<p>`.
- Contrast: `--color-ink` on `--color-stone` is AAA in both modes; already enforced site-wide by `tools/check-contrast.py` on the source tokens.
- No interactive controls, so no focus management needed. Tab order is intrinsic (links only).
- No skip-link needed (single-section page).
- `prefers-reduced-motion` is moot — there are no animations.

## 9. Risks

- **XSL token drift from `main.css`**: tokens are copied into XSL by hand and could drift if the palette changes. Mitigation: the linter's "inline `<style>` exists" check is a regression sentinel but not a value-drift check. Manual sync is acceptable given how rarely the palette token values change (last revision: Phase 0).
- **Google Fonts unavailable**: `font-family: var(--font-body), 'Petrona', Georgia, serif` cascade gives a clean fallback. Acceptable.
- **Browser support**: XSL 1.0 is supported by Firefox + Chromium + Safari. IE/legacy Edge ignored (the rest of the site is `<dialog>`-based already, which has the same baseline). No fallback strategy needed.
- **Pagefind index**: Pagefind indexes `<main data-pagefind-body>` HTML pages only. Feed XML files are not indexed. XSL-rendered output is a transformation of the XML, not a separate URL — Pagefind won't see it. No change needed; no scope adjustment.
- **Linter false positives on raw-text PI match**: regex anchors require care. The test fixtures include a "PI present but not before `<rss>`" case to confirm the linter catches malformed placement.

## 10. Out of scope (deferred)

- Pretty-rendering the garden feed — separate slice if appetite ever shows up. Garden's living/granular tempo arguably reads better as raw RSS for the audience that actually subscribes.
- Per-item RSS images / `media:content` extensions — current feed doesn't carry them; not a regression.
- Pretty-rendering future feeds (works, library, research, streams) — each gets its own decision when shipped.
- An XSL-rendered "open in reader" picker — explicitly out-of-scope per goals §2.
- Internationalization — site is English-only.

## 11. Effort estimate

~30 minutes implementation + 30 minutes linter pair + 30 minutes manual verification (Firefox + Chromium, light + dark mode). Single slice, single PR.

---

*End of design. Plan via `superpowers:writing-plans` when ready to ship.*
