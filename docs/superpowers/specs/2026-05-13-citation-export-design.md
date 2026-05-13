# Citation export — design

**Phase:** Post-Phase-8 polish, before Phase 3 (slot α).
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md`.
**Origin:** `~/org/projects.org` TODO captured 2026-04-14 ("Figure out a way for folks to cite your notes, and for that to be easily done via zotero or a button on the website").

Expose citation metadata two ways: **(A)** for each page on the site, and **(B)** for each external work referenced by those pages. Five formats: BibTeX, APA, Chicago, MLA, RIS — plus Highwire Press `<meta>` tags for Zotero browser-connector auto-detect.

---

## 1. Scope

**Citable sections** (Half A — page-as-source):

- Essays (`.Section == "essays"`)
- Garden notes — all `growth_stage` values (seedling, budding, evergreen). Seedlings/budding flagged in the BibTeX `note` field; no other behavior difference.
- Research (themes + questions)
- Works (games / music / poetry)

**Not citable:** Home, About, Library leaves, umbrella indexes (`/research/`, `/works/`, `/garden/`), graph pages.

**Referenced-work cite** (Half B — pull from `data/citations.yaml`): wherever a `cite` shortcode appears. Today that's essays; any future section that uses `cite` inherits Half B automatically via the shared `essay-references.html` partial (or its equivalent).

---

## 2. Architecture

### File layout

```
layouts/partials/cite/
  meta-tags.html        # new — Highwire <meta> tags, called from head.html
  data-blob.html        # new — <script type=application/json id=cite-data>
  button.html           # new — "Cite this page" link beneath title
  modal.html            # new — <dialog id=cite-modal> markup, once per page
  static-fallback.html  # new — <section id=cite-this> for no-JS path
  normalize-page.html   # new — Page → citation dict
  normalize-ref.html    # new — citations.yaml entry → citation dict
  fmt-bibtex.html       # new — citation dict → BibTeX string
  fmt-apa.html          # new
  fmt-chicago.html      # new
  fmt-mla.html          # new
  fmt-ris.html          # new

layouts/_default/baseof.html      # modify — conditionally include cite/modal.html
layouts/partials/head.html        # modify — conditionally include cite/meta-tags.html
layouts/partials/essay-references.html  # modify — extend each <li> with .ref-cite-actions
layouts/essays/single.html        # modify — include cite/button.html + cite/data-blob.html + cite/static-fallback.html
layouts/garden/single.html        # modify — same
layouts/research-theme/single.html # modify — same
layouts/research-question/single.html # modify — same
layouts/works-games/single.html   # modify — same
layouts/works-music/single.html   # modify — same
layouts/works-poetry/single.html  # modify — same

assets/js/cite.js                 # new — modal + copy + download runtime
assets/js/entry-cite.js           # new — bundle entry, imports cite.js

assets/css/main.css               # append §43 citation export

layouts/partials/scripts.html     # modify — wire new entry-cite bundle
hugo.yaml                         # modify — add site Params.author if missing

tools/check_cite_meta.py          # new — 15th linter
tools/test_check_cite_meta.py     # new — unit-test sibling
.github/workflows/hugo.yaml       # modify — 2 new steps (linter + sibling test)
```

### Predicate for "is this page citable"

Defined once as a Hugo template helper (inline in `head.html` and `baseof.html`):

```
{{ $citable_sections := slice "essays" "garden" "research" "works" }}
{{ $is_citable := and (in $citable_sections .Section) (eq .Kind "page") }}
```

`.Kind == "page"` excludes list/section pages naturally. Library leaves are `.Section == "library"`, About is `.Section == "about"`, home is `.Kind == "home"` — all excluded.

---

## 3. Data shape

### Per-page citation dict (normalized)

Both `normalize-page.html` and `normalize-ref.html` return a dict of this shape, consumed by the five `fmt-*.html` partials:

```hugo
(dict
  "citekey"     "madkour-2026-on-knowing-tools"   # required
  "type"        "article"                          # article | misc | online (drives BibTeX entry type)
  "authors"     (slice "Madkour, Abdelrahman")     # always a slice
  "year"        2026                               # int
  "title"       "On Knowing One's Tools"
  "venue"       ""                                 # journal / publisher / "" for misc
  "url"         "https://a3madkour.github.io/essays/on-knowing-tools/"
  "doi"         ""                                 # optional
  "isbn"        ""                                 # optional
  "note"        "Garden note, seedling — in-progress thinking"  # optional, set for non-evergreen garden notes
  "pub_date"    "2026-05-13"                       # YYYY-MM-DD for meta tags
  "online_date" "2026-05-13"                       # YYYY-MM-DD (Lastmod)
)
```

### Identifier scheme

**Own pages (Half A):** `madkour-<year>-<slug>` where:

- `<year>`: `.Date.Year` if present; else `.Lastmod.Year`; else `time.AsTime .Params.last_modified | dateFormat "2006"`. Garden notes typically only have `last_modified`.
- `<slug>`: derived from `.RelPermalink` — strip leading section prefix + trim trailing slash, take the last URL path segment. Implementation: `index (last 1 (split (trim .RelPermalink "/") "/")) 0`. For pages with explicit `slug:` frontmatter, this still resolves correctly since `.RelPermalink` already reflects it. For index-bundle pages (the common case on this site), this returns the bundle directory name — `.File.BaseFileName` would incorrectly return `"index"`, so it is not used.

Linter regex: `^madkour-\d{4}-[a-z0-9-]+$`.

**Referenced works (Half B):** the existing key in `data/citations.yaml` (`example-source-1`, etc.). No renaming.

### JSON blob

Per citable page, embedded once at end of `<main>`:

```html
<script type="application/json" id="cite-data">
{
  "self": {
    "citekey": "madkour-2026-on-knowing-tools",
    "title": "On Knowing One's Tools",
    "formats": {
      "bibtex":  "@article{madkour-2026-on-knowing-tools,\n  author = {Madkour, Abdelrahman},\n  ...}",
      "apa":     "Madkour, A. (2026). On knowing one's tools. Retrieved from https://...",
      "chicago": "Madkour, Abdelrahman. \"On Knowing One's Tools.\" 2026. https://...",
      "mla":     "Madkour, Abdelrahman. \"On Knowing One's Tools.\" 2026, https://...",
      "ris":     "TY  - JOUR\nAU  - Madkour, Abdelrahman\n..."
    }
  },
  "refs": {
    "example-source-1": {
      "title": "Lorem ipsum dolor sit amet",
      "formats": { "bibtex": "...", "apa": "...", "chicago": "...", "mla": "...", "ris": "..." }
    }
  }
}
</script>
```

Only refs actually cited on the page appear in `refs` (read from `Page.Scratch.Get "cite-keys"` — already populated by the existing `cite` shortcode).

### Highwire meta tags (Half A only)

Emitted in `<head>` by `partials/cite/meta-tags.html` when the page is citable:

```html
<meta name="citation_title"            content="On Knowing One's Tools">
<meta name="citation_author"           content="Madkour, Abdelrahman">
<meta name="citation_publication_date" content="2026-05-13">
<meta name="citation_online_date"      content="2026-05-13">
<meta name="citation_public_url"       content="https://a3madkour.github.io/essays/on-knowing-tools/">
```

Multiple authors emit multiple `citation_author` tags (one per author). Optional tags: `citation_doi`, `citation_isbn`, `citation_pdf_url` (skipped when empty).

### `data/citations.yaml` schema extension

Existing required fields stay required: `authors`, `year`, `title`, `venue`, `url`, `notes_ref`.

New optional fields (skipped by formatters when empty, populated by ox-hugo in Phase 3):

- `doi` — string
- `publisher` — string (for books; distinct from `venue`)
- `volume` — string
- `issue` — string
- `pages` — string (e.g., "23–45")
- `isbn` — string
- `type` — string enum: `article` (default) | `book` | `inproceedings` | `misc` (drives `@article{}` vs `@book{}` etc.)

`tools/check_citations.py` extended to validate the new optional fields' types when present (no required-ness change).

---

## 4. Hugo partials — signatures + output

### `cite/meta-tags.html`

```hugo
{{- $cite := partial "cite/normalize-page.html" . -}}
<meta name="citation_title" content="{{ $cite.title }}">
{{- range $cite.authors -}}
<meta name="citation_author" content="{{ . }}">
{{- end -}}
<meta name="citation_publication_date" content="{{ $cite.pub_date }}">
<meta name="citation_online_date"      content="{{ $cite.online_date }}">
<meta name="citation_public_url"       content="{{ $cite.url }}">
{{- with $cite.doi -}}<meta name="citation_doi" content="{{ . }}">{{- end -}}
{{- with $cite.isbn -}}<meta name="citation_isbn" content="{{ . }}">{{- end -}}
```

### `cite/data-blob.html`

```hugo
{{- $self_dict := partial "cite/normalize-page.html" . -}}
{{- $self := dict
      "citekey" $self_dict.citekey
      "title"   $self_dict.title
      "formats" (dict
        "bibtex"  (partial "cite/fmt-bibtex.html"  $self_dict)
        "apa"     (partial "cite/fmt-apa.html"     $self_dict)
        "chicago" (partial "cite/fmt-chicago.html" $self_dict)
        "mla"     (partial "cite/fmt-mla.html"     $self_dict)
        "ris"     (partial "cite/fmt-ris.html"     $self_dict))
-}}
{{- $refs := dict -}}
{{- $used := .Scratch.Get "cite-keys" | default slice -}}
{{- range $used -}}
  {{- $entry := index site.Data.citations.citations . -}}
  {{- $ref_dict := partial "cite/normalize-ref.html" (dict "key" . "entry" $entry) -}}
  {{- $refs = merge $refs (dict . (dict
        "title"   $ref_dict.title
        "formats" (dict
          "bibtex"  (partial "cite/fmt-bibtex.html"  $ref_dict)
          "apa"     (partial "cite/fmt-apa.html"     $ref_dict)
          "chicago" (partial "cite/fmt-chicago.html" $ref_dict)
          "mla"     (partial "cite/fmt-mla.html"     $ref_dict)
          "ris"     (partial "cite/fmt-ris.html"     $ref_dict)))) -}}
{{- end -}}
<script type="application/json" id="cite-data">
{{ dict "self" $self "refs" $refs | jsonify }}
</script>
```

**Build-order constraint:** `data-blob.html` MUST be rendered *after* the page body, since the `cite` shortcode populates `Page.Scratch.cite-keys` during body rendering. Each per-section single template includes the body, then `cite/static-fallback.html`, then `cite/data-blob.html`, then `essay-references.html` (already last today).

**Minifier pitfall (per CLAUDE.md "Build-time graph data"):** `jsonify` MUST run inline at the `<script>` embed point — never inside a sub-partial that pre-serializes the dict. Pre-jsonifying then `safeHTML`-marking the string causes the production minifier to choke on HTML-escaped quotes inside `<script type="application/json">` (the same trap the garden graph hit). The `data-blob.html` design above already follows the safe pattern: each `fmt-*.html` returns a raw Hugo string, the dict is assembled raw, and `jsonify` is applied once at the final `<script>` body interpolation.

### `cite/button.html`

```hugo
<a class="cite-page-link" href="#cite-this" data-action="open-cite-modal">Cite this page</a>
```

Per-section single template inserts this beneath the meta row (date / read-time line).

### `cite/static-fallback.html`

```hugo
{{- $self := partial "cite/normalize-page.html" . -}}
<section id="cite-this" class="cite-static">
  <h2>Cite this page</h2>
  <details><summary>BibTeX</summary><pre>{{ partial "cite/fmt-bibtex.html"  $self }}</pre></details>
  <details><summary>APA</summary><pre>{{ partial "cite/fmt-apa.html"     $self }}</pre></details>
  <details><summary>Chicago</summary><pre>{{ partial "cite/fmt-chicago.html" $self }}</pre></details>
  <details><summary>MLA</summary><pre>{{ partial "cite/fmt-mla.html"     $self }}</pre></details>
  <details><summary>RIS</summary><pre>{{ partial "cite/fmt-ris.html"     $self }}</pre></details>
</section>
```

Stays visible with JS on — accessibility + redundancy. Inside the modal the same content gets tab-style affordances.

### `cite/modal.html` (included once from `baseof.html` when citable)

```html
<dialog id="cite-modal" class="cite-modal" aria-labelledby="cite-modal-title">
  <header class="cite-modal-header">
    <h2 id="cite-modal-title">Cite</h2>
    <p class="cite-modal-subtitle" id="cite-modal-subtitle"></p>
    <button class="cite-modal-close" aria-label="Close">×</button>
  </header>
  <nav class="cite-modal-tabs" role="tablist" aria-label="Citation format">
    <button role="tab" data-format="bibtex"  aria-selected="true">BibTeX</button>
    <button role="tab" data-format="apa"     aria-selected="false">APA</button>
    <button role="tab" data-format="chicago" aria-selected="false">Chicago</button>
    <button role="tab" data-format="mla"     aria-selected="false">MLA</button>
    <button role="tab" data-format="ris"     aria-selected="false">RIS</button>
  </nav>
  <pre class="cite-modal-output" id="cite-modal-output" tabindex="0"></pre>
  <div class="cite-modal-actions">
    <button class="cite-modal-copy" type="button">Copy</button>
    <a class="cite-modal-download" download>Download .bib</a>
    <span class="cite-modal-toast" role="status" aria-live="polite"></span>
  </div>
</dialog>
```

### Extended `essay-references.html`

Each `<li>` gains a `.ref-cite-actions` span:

```hugo
<li id="ref-{{ . }}">
  {{ delimit $entry.authors ", " }} ({{ $entry.year }}).
  <em>{{ $entry.title }}</em>.
  {{ $entry.venue }}.
  {{ with $entry.url }}<a href="{{ . }}" rel="noopener">source</a>{{ end }}
  {{ with $entry.notes_ref }}<a href="/garden/{{ . }}/" class="ref-note">related note</a>{{ end }}
  <span class="ref-cite-actions" aria-label="Cite this reference">
    <button class="ref-cite-copy" data-cite-key="{{ . }}" data-format="bibtex">BibTeX</button>
    <button class="ref-cite-copy" data-cite-key="{{ . }}" data-format="apa">APA</button>
    <button class="ref-cite-copy" data-cite-key="{{ . }}" data-format="ris">.ris</button>
    <a class="ref-cite-full" href="#ref-{{ . }}" data-cite-key="{{ . }}">More →</a>
  </span>
</li>
```

Because `citation-card.js` clones `<li>.innerHTML` for the hover-card (line 62 today), `.ref-cite-actions` appears in the hover-card automatically. Same delegated click handler (`document.addEventListener('click', ...)`) covers both surfaces.

---

## 5. JS module

### `assets/js/cite.js`

Responsibilities:

1. Parse `#cite-data` JSON blob once on init. Cache `data.self` and `data.refs`.
2. Click handler on `.cite-page-link` → `preventDefault()`, open modal with `data.self`.
3. Click handler on `.ref-cite-full` → `preventDefault()`, open modal with `data.refs[key]`.
4. Click handler on `.ref-cite-copy` → copy `data.refs[key].formats[format]` to clipboard, show 2-second toast.
5. Modal tab switching: clicking a tab updates `aria-selected`, writes the right format string to `#cite-modal-output`, updates the Download link's `data:` URI + extension.
6. Modal Copy button: clipboard write of current `<pre>` text.
7. Last-used format persisted to `localStorage` under key `cite-format-pref` (`bibtex` default). Modal opens to that tab.
8. `Escape` and backdrop click close modal (native `<dialog>` close + manual `closest('dialog')` check).
9. Clipboard fallback: try `navigator.clipboard.writeText`; on failure, select the `<pre>` and prompt `Ctrl+C`. Toast text differs ("Copied" vs "Press Ctrl+C to copy").

Bail conditions:
- `#cite-data` absent → silently return (page isn't citable).
- `<dialog>` not supported (very old browsers) → modal click → fall back to anchor jump to `#cite-this`.

### `entry-cite.js`

```js
import { initCite } from './cite.js';
initCite();
```

Wired in `scripts.html`:

```hugo
{{- $citable_sections := slice "essays" "garden" "research" "works" -}}
{{- if and (in $citable_sections .Section) (eq .Kind "page") -}}
  {{- $cite := resources.Get "js/entry-cite.js" | js.Build (dict ...) -}}
  ...
{{- end -}}
```

Output: `cite.<hash>.js`, ~3–4 KB minified. SRI + classic-script, matching the existing bundle pattern.

---

## 6. CSS — new §43

Append to `assets/css/main.css`:

```css
/* §43 — citation export ----------------------------------------------- */

/* "Cite this page" link beneath title */
.cite-page-link {
  font-size: 0.75rem;
  color: var(--color-burgundy);
  text-decoration: underline;
  text-underline-offset: 2px;
  margin-left: 0.5rem;
}
.cite-page-link:hover { text-decoration-thickness: 2px; }

/* Static fallback section at page bottom */
.cite-static {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px dashed var(--color-ink-soft);
}
.cite-static h2 {
  font-family: var(--font-ui);
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-ink-soft);
  margin-bottom: 0.75rem;
}
.cite-static details { margin-bottom: 0.5rem; }
.cite-static summary {
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 0.85rem;
  color: var(--color-burgundy);
}
.cite-static pre {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  background: var(--color-paper);
  padding: 0.75rem 1rem;
  margin: 0.5rem 0;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Modal — reuses --color-paper from search modal */
.cite-modal {
  background: var(--color-paper);
  color: var(--color-ink);
  border: 1px solid var(--color-ink-soft);
  border-radius: 6px;
  max-width: 640px;
  width: min(640px, 92vw);
  padding: 0;
}
.cite-modal::backdrop { background: rgba(0,0,0,0.4); }
.cite-modal-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 1rem 1.25rem 0.5rem;
}
.cite-modal-header h2 { margin: 0; font-size: 1rem; }
.cite-modal-subtitle { color: var(--color-ink-soft); font-size: 0.85rem; margin: 0; }
.cite-modal-close {
  background: none; border: none; font-size: 1.5rem; cursor: pointer;
  color: var(--color-ink-soft); padding: 0; line-height: 1;
}
.cite-modal-tabs {
  display: flex; gap: 0.5rem;
  padding: 0 1.25rem;
  border-bottom: 1px solid var(--color-ink-soft);
}
.cite-modal-tabs button {
  background: none; border: none; padding: 0.4rem 0.6rem;
  font-family: var(--font-ui); font-size: 0.85rem;
  color: var(--color-ink-soft); cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
.cite-modal-tabs button[aria-selected="true"] {
  color: var(--color-burgundy);
  border-bottom-color: var(--color-burgundy);
}
.cite-modal-output {
  font-family: var(--font-mono); font-size: 0.8rem;
  padding: 1rem 1.25rem;
  margin: 0;
  max-height: 50vh;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.cite-modal-actions {
  display: flex; gap: 0.5rem; align-items: center;
  padding: 0.5rem 1.25rem 1rem;
}
.cite-modal-copy, .cite-modal-download {
  font-family: var(--font-ui); font-size: 0.85rem;
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--color-burgundy);
  background: transparent; color: var(--color-burgundy);
  border-radius: 3px; cursor: pointer; text-decoration: none;
}
.cite-modal-toast { font-size: 0.8rem; color: var(--color-ink-soft); }

/* Mobile = bottom-sheet */
@media (max-width: 720px) {
  .cite-modal {
    width: 100vw; max-width: none; margin: 0 auto;
    position: fixed; bottom: 0; left: 0; right: 0; top: auto;
    border-radius: 8px 8px 0 0;
  }
}

/* Half B inline actions inside ref <li> */
.ref-cite-actions {
  display: inline-flex; gap: 0.4rem; margin-left: 0.5rem;
  align-items: baseline;
}
.ref-cite-copy {
  font-family: var(--font-ui); font-size: 0.7rem;
  padding: 1px 6px;
  background: transparent; color: var(--color-burgundy);
  border: 1px solid var(--color-ink-soft); border-radius: 99px;
  cursor: pointer;
}
.ref-cite-copy:hover { border-color: var(--color-burgundy); }
.ref-cite-full {
  font-size: 0.75rem; color: var(--color-burgundy);
  text-decoration: underline;
}
```

No new tokens. Reuses `--color-paper` (search-modal token), `--color-burgundy`, `--color-ink-soft`, `--font-ui`, `--font-mono`.

---

## 7. Format generators

Each `fmt-*.html` takes the normalized citation dict from §3 and returns a single string. Implementations are mostly string interpolation. Key rules:

### BibTeX (`fmt-bibtex.html`)

```bibtex
@<type>{<citekey>,
  author    = {<author> and <author>},
  title     = {<title>},
  year      = {<year>},
  url       = {<url>},
  <optional fields here, one per line, skipped if empty>
  note      = {<note>}
}
```

- `type` map: `article` (essays), `misc` (garden + works), `online` (research). Fallback `misc`.
- Authors joined with ` and ` (BibTeX convention).
- Optional fields emitted only when non-empty: `journal`/`venue`, `doi`, `isbn`, `publisher`, `volume`, `issue`, `pages`.
- **Special-character escaping** in author / title / venue strings: `&` → `\&`, `%` → `\%`, `#` → `\#`, `_` → `\_`, `$` → `\$`. Curly braces in titles are preserved (they are BibTeX grouping markers — fixtures should not contain literal `{` `}` in titles, and ox-hugo output will follow the same convention). Linter validates the round-trip by re-parsing emitted BibTeX with a minimal stdlib parser (regex-based; no `pybtex` dependency).

### APA (`fmt-apa.html`)

```
<authors-apa-formatted> (<year>). <title>. <venue>. <url>
```

Author list: first author "Last, F. M." with optional & before final; ≥3 use "Last, F. M., Last, F. M., & Last, F. M."; ≥21 truncate after 19 + ellipsis + final.

### Chicago notes-bibliography (`fmt-chicago.html`)

```
<First Last>, "<Title>," <Venue>, <year>, <url>.
```

### MLA (`fmt-mla.html`)

```
<Last, First>. "<Title>." <Venue>, <year>, <url>.
```

### RIS (`fmt-ris.html`)

```
TY  - <type-code>
AU  - <author>
PY  - <year>
TI  - <title>
JO  - <venue>
UR  - <url>
ER  -
```

- `type-code` map: `article → JOUR`, `misc → GEN`, `online → ELEC`, `book → BOOK`, `inproceedings → CONF`.
- One `AU` line per author.

---

## 8. Linter — 15th pair

### `tools/check_cite_meta.py`

Walks `public/`. For each HTML file whose path matches a citable section (`/essays/<slug>/`, `/garden/<slug>/`, `/research/themes/<slug>/`, `/research/questions/<slug>/`, `/works/<sub>/<slug>/`):

1. Parse with stdlib `html.parser.HTMLParser`.
2. Assert `<meta name="citation_title">`, `citation_author` (≥1), `citation_publication_date`, `citation_online_date`, `citation_public_url` are all present.
3. Assert `<script type="application/json" id="cite-data">` exists, parses as JSON, and:
   - `self.citekey` matches `^madkour-\d{4}-[a-z0-9-]+$`
   - `self.formats` has all 5 keys; each is non-empty string
   - Every key in `refs` exists in `data/citations.yaml` (load once at top of run)
4. Assert `<section id="cite-this">` present.
5. For pages with refs (i.e., `refs` non-empty): assert each `ref-cite-actions` span exists in the references list, with one `.ref-cite-copy` button per format.

Non-citable pages (`/about/`, `/library/...`, `/`, umbrellas, graph pages) MUST NOT have any of these. Linter also asserts absence on a sampled set of non-citable pages.

Exit non-zero on any violation. Output one line per offending file.

### `tools/test_check_cite_meta.py`

Unit-test sibling. Synthetic HTML fixtures cover:

- Happy path: citable page with full meta + blob + static block + refs
- Missing one meta tag → fail
- Bad citekey shape → fail
- Ref key missing from citations.yaml → fail
- Non-citable page leaking a meta tag → fail
- Page with no refs (empty `refs`) → pass

Follows the existing test layout in `tools/test_check_pagefind_meta.py`.

### CI workflow

`.github/workflows/hugo.yaml` adds two steps after the existing Pagefind metadata steps:

```yaml
- name: Lint cite_meta linter
  run: python3 tools/test_check_cite_meta.py
- name: Verify cite_meta on built pages
  run: python3 tools/check_cite_meta.py
```

Step count: 40 → 42.

---

## 9. Page-weight implications

Added per citable page:

| Asset                              | Size       |
|------------------------------------|-----------:|
| Highwire meta tags                 | ~500 B     |
| JSON blob (typical 3–5 refs)       | ~1.5 KB    |
| Static fallback `<section>`        | ~1.5 KB    |
| `cite.<hash>.js` (shared, cached)  | ~3–4 KB    |

Within existing per-page budgets — essay 100 KB, garden 100 KB, research 600 KB, works 100 KB. `tools/check_page_weights.py` budgets unchanged.

---

## 10. Frontmatter additions

New optional field on essay / garden / research / works frontmatter:

- `cite_author` — string or list of strings. Overrides the site-default author. Used for the rare co-authored item. Default = `site.Params.author.name`.

When `cite_author` is a list, each entry emits its own `citation_author` meta tag and joins with ` and ` in BibTeX, with proper APA/MLA formatting.

`hugo.yaml` requires (add if missing):

```yaml
params:
  author:
    name: "Madkour, Abdelrahman"
    given: "Abdelrahman"
    family: "Madkour"
```

(`given` and `family` used by formatters for "F. M." initials in APA / Chicago / MLA.)

No required-field additions. All existing fixtures round-trip without changes.

---

## 11. Out of scope (deferred, with fixture seed when applicable)

| Capability | Reason | Future trigger |
|---|---|---|
| DOI assignment via CrossRef | No DOI infrastructure for personal site | If author opts into a registrar |
| ORCID `citation_author_orcid` meta tag | Author has no ORCID yet | Add when ORCID exists; meta-tags partial scaffolds the slot already |
| Library item cite export | Library entries have their own external metadata paths (ISBN/MBID/IGDB/TMDB); cite-via-source is already feasible | Separate slice if reader appetite shows up |
| Bulk export (one .bib for all refs on a page) | Nice-to-have, not initial scope | If reader feedback requests it |
| Bilingual / Arabic-aware citation formats | Gated on real Arabic content landing | Phase 3 follow-up |
| `<link rel="alternate" type="application/x-bibtex">` programmatic endpoint | Meta tags cover Zotero path | If a citation manager other than Zotero needs static `.bib` URLs |
| Auto-suggest the right format based on referer (e.g., Overleaf → BibTeX) | Too magical | Never |

---

## 12. Phase placement

This is a **post-Phase-8 polish slice**, landing **before Phase 3 starts**.

**Slot rationale:** Independent of Phase 3 (org-mode pipeline) — works on current fixtures. The per-page citation dict uses Hugo's existing `.Date` / `.Lastmod` / `.Params.last_modified` / `.Permalink` / `.File.BaseFileName`, all populated today. ox-hugo will eventually populate richer `data/citations.yaml` entries (DOI, ISBN, publisher); the formatters skip those fields when empty, so they round-trip without renumbering anywhere.

**Sequence with other queued work:**

1. Finish Phase 8 Slice 3 QA close-out (remaining checklist items §1.1–1.5, §1.7–1.9, §2–§5).
2. Citation export slice (this spec).
3. Phase 3 (org-mode pipeline) — when it lands, the formatters automatically pick up any new optional fields ox-hugo populates.

**Effort estimate:** ~half a day's implementation + tests. The org TODO tagged 2h was the optimistic side; the linter pair + 5 format generators + modal UX push it closer to a full afternoon. Single slice, single PR.
