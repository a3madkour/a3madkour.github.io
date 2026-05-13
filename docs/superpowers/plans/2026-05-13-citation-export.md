# Citation Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose citation metadata for every page on the site (Half A) and for each external work referenced on those pages (Half B), in five formats — BibTeX, APA, Chicago, MLA, RIS — plus Highwire Press `<meta>` tags for Zotero browser-connector auto-detect.

**Architecture:** Build-time Hugo partials generate all citation strings server-side. A single inline JSON blob (`<script type="application/json" id="cite-data">`) carries `self` + `refs` payloads to the client. A `<dialog>` modal (same pattern as the existing search modal) opens via a "Cite this page" link beneath the title or via per-reference "More →" links in the references list. Inline copy buttons in each ref `<li>` also surface inside the citation hover-card (which already clones `<li>.innerHTML`). With JS off, a static `<section id="cite-this">` at page bottom exposes all 5 formats inside native `<details>`, and Zotero's `<meta>` tags still work.

**Tech Stack:** Hugo extended ≥ 0.148.0, hand-rolled CSS appended to `assets/css/main.css` §43, vanilla JS via Hugo's `js.Build` (esbuild) emitting a new `cite.<hash>.js` bundle (~3–4 KB), Python stdlib only for the 15th linter pair, no npm.

**Parent spec:** `docs/superpowers/specs/2026-05-13-citation-export-design.md`.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `hugo.yaml` | Modify | Add `params.author` block (name / given / family). |
| `layouts/partials/cite/normalize-page.html` | Create | Page → normalized citation dict (handles section field diffs). |
| `layouts/partials/cite/normalize-ref.html` | Create | `data/citations.yaml` entry → normalized citation dict. |
| `layouts/partials/cite/fmt-bibtex.html` | Create | Citation dict → BibTeX string. |
| `layouts/partials/cite/fmt-apa.html` | Create | Citation dict → APA plain-text string. |
| `layouts/partials/cite/fmt-chicago.html` | Create | Citation dict → Chicago notes-bibliography string. |
| `layouts/partials/cite/fmt-mla.html` | Create | Citation dict → MLA string. |
| `layouts/partials/cite/fmt-ris.html` | Create | Citation dict → RIS string. |
| `layouts/partials/cite/meta-tags.html` | Create | Emits Highwire `citation_*` `<meta>` tags. |
| `layouts/partials/cite/data-blob.html` | Create | Emits `<script type=application/json id=cite-data>` with `self` + `refs`. |
| `layouts/partials/cite/button.html` | Create | "Cite this page" link beneath title. |
| `layouts/partials/cite/static-fallback.html` | Create | No-JS `<section id="cite-this">` at page bottom. |
| `layouts/partials/cite/modal.html` | Create | `<dialog id="cite-modal">` markup; included once from `baseof.html` on citable pages. |
| `layouts/partials/head.html` | Modify | Conditionally include `cite/meta-tags.html` on citable pages. |
| `layouts/_default/baseof.html` | Modify | Conditionally include `cite/modal.html` on citable pages. |
| `layouts/partials/essay-references.html` | Modify | Extend each `<li>` with `.ref-cite-actions` (Half B). |
| `layouts/essays/single.html` | Modify | Insert button + static-fallback + data-blob calls. |
| `layouts/garden/single.html` | Modify | Same. |
| `layouts/research-theme/single.html` | Modify | Same. |
| `layouts/research-question/single.html` | Modify | Same. |
| `layouts/works-games/single.html` | Modify | Same. |
| `layouts/works-music/single.html` | Modify | Same. |
| `layouts/works-poetry/single.html` | Modify | Same. |
| `assets/js/cite.js` | Create | Runtime: parse blob, open/close modal, tab switch, copy/download. |
| `assets/js/entry-cite.js` | Create | Bundle entry. |
| `layouts/partials/scripts.html` | Modify | Wire new `entry-cite.js` bundle for citable pages. |
| `assets/css/main.css` | Append | §43 — citation export. |
| `tools/check_cite_meta.py` | Create | 15th linter; validates built pages have meta tags + blob + static block + ref actions. |
| `tools/test_check_cite_meta.py` | Create | Unit-test sibling. |
| `.github/workflows/hugo.yaml` | Modify | +2 steps: linter unit test + linter run. |
| `tools/check_citations.py` | Modify | Accept new optional fields (`doi`, `publisher`, `volume`, `issue`, `pages`, `isbn`, `type`). |
| `CLAUDE.md` | Modify | Document new partial layout, JS bundle, linter pair, CI step count. |

---

## Working Directory & Branch

Work happens on a slice branch `slice/citation-export` off `master`. Before Task 1:

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git status   # confirm clean working tree on master
git checkout -b slice/citation-export
```

All task commits land on this branch. Final merge happens via the existing slice-finishing flow after the dev-server spot-check in Task 21.

**Reminder (from CLAUDE.md):** never run `hugo --minify` while a dev server is alive. Kill the dev server before any production build inside this plan.

---

### Task 1: Bootstrap site author config

**Files:**
- Modify: `hugo.yaml`

- [ ] **Step 1: Read current `hugo.yaml`**

Run: `cat hugo.yaml`
Expected: no existing `params.author` block.

- [ ] **Step 2: Append `params.author` block at end of `hugo.yaml`**

Append (preserving existing content):

```yaml

params:
  author:
    name: "Madkour, Abdelrahman"
    given: "Abdelrahman"
    family: "Madkour"
```

- [ ] **Step 3: Verify Hugo parses the new config**

Run: `hugo config | grep -A 3 author`
Expected: prints the three author keys with the correct values.

- [ ] **Step 4: Commit**

```bash
git add hugo.yaml
git commit -m "cite: add site Params.author for citation export"
```

---

### Task 2: Normalized citation dict — `normalize-page.html`

**Files:**
- Create: `layouts/partials/cite/normalize-page.html`

- [ ] **Step 1: Create the partial**

Write `layouts/partials/cite/normalize-page.html`:

```hugo
{{- /* Normalizes a Page into a citation dict consumed by fmt-* partials.

       Inputs: . (a Page)
       Output: dict {citekey, type, authors, year, title, venue, url,
                     doi, isbn, note, pub_date, online_date}
*/ -}}

{{- /* Authors: per-page cite_author overrides; otherwise site default. */ -}}
{{- $authors := slice -}}
{{- with .Params.cite_author -}}
  {{- if reflect.IsSlice . -}}
    {{- range . -}}{{- $authors = $authors | append . -}}{{- end -}}
  {{- else -}}
    {{- $authors = $authors | append . -}}
  {{- end -}}
{{- else -}}
  {{- $authors = $authors | append site.Params.author.name -}}
{{- end -}}

{{- /* Year: .Date.Year if set, else Lastmod.Year, else from Params.last_modified. */ -}}
{{- $year := 0 -}}
{{- if not .Date.IsZero -}}{{- $year = .Date.Year -}}
{{- else if not .Lastmod.IsZero -}}{{- $year = .Lastmod.Year -}}
{{- else with .Params.last_modified -}}
  {{- $year = int (dateFormat "2006" (time.AsTime .)) -}}
{{- end -}}

{{- /* Slug: last URL path segment of .RelPermalink. */ -}}
{{- $segments := split (trim .RelPermalink "/") "/" -}}
{{- $slug := index $segments (sub (len $segments) 1) -}}
{{- $citekey := printf "madkour-%d-%s" $year $slug -}}

{{- /* Type map by section. */ -}}
{{- $type := "misc" -}}
{{- if eq .Section "essays" -}}{{- $type = "article" -}}
{{- else if eq .Section "research" -}}{{- $type = "online" -}}
{{- end -}}

{{- /* Note: stage flag for non-evergreen garden notes. */ -}}
{{- $note := "" -}}
{{- if eq .Section "garden" -}}
  {{- with .Params.growth_stage -}}
    {{- if or (eq . "seedling") (eq . "budding") -}}
      {{- $note = printf "Garden note, %s — in-progress thinking" . -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{- /* Dates as YYYY-MM-DD for meta tags. */ -}}
{{- $pub_date := "" -}}
{{- if not .Date.IsZero -}}{{- $pub_date = .Date.Format "2006-01-02" -}}
{{- else with .Params.last_modified -}}{{- $pub_date = dateFormat "2006-01-02" (time.AsTime .) -}}{{- end -}}
{{- $online_date := $pub_date -}}
{{- if not .Lastmod.IsZero -}}{{- $online_date = .Lastmod.Format "2006-01-02" -}}{{- end -}}

{{- return dict
      "citekey"     $citekey
      "type"        $type
      "authors"     $authors
      "year"        $year
      "title"       .Title
      "venue"       ""
      "url"         .Permalink
      "doi"         ""
      "isbn"        ""
      "note"        $note
      "pub_date"    $pub_date
      "online_date" $online_date
-}}
```

- [ ] **Step 2: Sanity-check that Hugo accepts the partial syntax**

Run: `hugo --renderToMemory --quiet 2>&1 | head -20`
Expected: no errors mentioning `cite/normalize-page.html`. (The partial is not yet called by any template, but Hugo still parses all partials on build.)

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/cite/normalize-page.html
git commit -m "cite: normalize-page partial — Page → citation dict"
```

---

### Task 3: Normalized citation dict — `normalize-ref.html`

**Files:**
- Create: `layouts/partials/cite/normalize-ref.html`

- [ ] **Step 1: Create the partial**

Write `layouts/partials/cite/normalize-ref.html`:

```hugo
{{- /* Normalizes a data/citations.yaml entry into a citation dict.

       Inputs: dict {key, entry}
         .key   — string, the citations.yaml key
         .entry — the citations.yaml value (authors, year, title, venue, url, ...)

       Output: dict matching normalize-page.html's shape.
*/ -}}

{{- $entry := .entry -}}
{{- $type := default "article" $entry.type -}}

{{- return dict
      "citekey"     .key
      "type"        $type
      "authors"     $entry.authors
      "year"        $entry.year
      "title"       $entry.title
      "venue"       (default "" $entry.venue)
      "url"         (default "" $entry.url)
      "doi"         (default "" $entry.doi)
      "isbn"        (default "" $entry.isbn)
      "note"        ""
      "pub_date"    (printf "%d-01-01" $entry.year)
      "online_date" (printf "%d-01-01" $entry.year)
-}}
```

- [ ] **Step 2: Sanity build**

Run: `hugo --renderToMemory --quiet 2>&1 | head -20`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/cite/normalize-ref.html
git commit -m "cite: normalize-ref partial — citations.yaml entry → citation dict"
```

---

### Task 4: BibTeX format generator

**Files:**
- Create: `layouts/partials/cite/fmt-bibtex.html`

- [ ] **Step 1: Create the partial**

Write `layouts/partials/cite/fmt-bibtex.html`:

```hugo
{{- /* Renders a citation dict as a BibTeX entry string.

       Input: dict matching normalize-page.html / normalize-ref.html shape.
       Output: string (single multi-line BibTeX entry).

       Escapes: & % # _ $ in text fields.
*/ -}}

{{- $cite := . -}}
{{- $escape := func -}}{{- /* Hugo has no inline functions; use a helper */ -}}
{{- /* Manual escape via replacements: */ -}}
{{- $escaped_title := replace (replace (replace (replace (replace $cite.title "\\" "\\\\") "&" "\\&") "%" "\\%") "#" "\\#") "_" "\\_" -}}
{{- $escaped_venue := replace (replace (replace (replace (replace $cite.venue "\\" "\\\\") "&" "\\&") "%" "\\%") "#" "\\#") "_" "\\_" -}}

{{- $authors_str := delimit $cite.authors " and " -}}

{{- $lines := slice -}}
{{- $lines = $lines | append (printf "@%s{%s," $cite.type $cite.citekey) -}}
{{- $lines = $lines | append (printf "  author    = {%s}," $authors_str) -}}
{{- $lines = $lines | append (printf "  title     = {%s}," $escaped_title) -}}
{{- $lines = $lines | append (printf "  year      = {%d}," $cite.year) -}}
{{- with $cite.venue -}}{{- $lines = $lines | append (printf "  journal   = {%s}," $escaped_venue) -}}{{- end -}}
{{- with $cite.url -}}{{- $lines = $lines | append (printf "  url       = {%s}," .) -}}{{- end -}}
{{- with $cite.doi -}}{{- $lines = $lines | append (printf "  doi       = {%s}," .) -}}{{- end -}}
{{- with $cite.isbn -}}{{- $lines = $lines | append (printf "  isbn      = {%s}," .) -}}{{- end -}}
{{- with $cite.note -}}{{- $lines = $lines | append (printf "  note      = {%s}," .) -}}{{- end -}}
{{- $lines = $lines | append "}" -}}

{{- return delimit $lines "\n" -}}
```

- [ ] **Step 2: Sanity build**

Run: `hugo --renderToMemory --quiet 2>&1 | head -20`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/cite/fmt-bibtex.html
git commit -m "cite: BibTeX format generator"
```

---

### Task 5: APA format generator

**Files:**
- Create: `layouts/partials/cite/fmt-apa.html`

- [ ] **Step 1: Create the partial**

Write `layouts/partials/cite/fmt-apa.html`:

```hugo
{{- /* Renders a citation dict as an APA-7 plain-text citation.
       Format: <authors> (<year>). <title>. <venue>. <url>
*/ -}}

{{- $cite := . -}}

{{- /* Authors: "Last, F. M." each; join with ", " and final "& " for 2-20,
       truncate at 19 + ellipsis + final for 21+. citations.yaml already
       stores "Lastname, F." form, so we use entries as-is here. */ -}}
{{- $authors := $cite.authors -}}
{{- $n := len $authors -}}
{{- $authors_str := "" -}}
{{- if eq $n 1 -}}{{- $authors_str = index $authors 0 -}}
{{- else if le $n 20 -}}
  {{- $head := first (sub $n 1) $authors -}}
  {{- $last := index $authors (sub $n 1) -}}
  {{- $authors_str = printf "%s, & %s" (delimit $head ", ") $last -}}
{{- else -}}
  {{- $head := first 19 $authors -}}
  {{- $last := index $authors (sub $n 1) -}}
  {{- $authors_str = printf "%s, ... %s" (delimit $head ", ") $last -}}
{{- end -}}

{{- $parts := slice (printf "%s (%d). %s." $authors_str $cite.year $cite.title) -}}
{{- with $cite.venue -}}{{- $parts = $parts | append (printf "%s." .) -}}{{- end -}}
{{- with $cite.url -}}{{- $parts = $parts | append . -}}{{- end -}}

{{- return delimit $parts " " -}}
```

- [ ] **Step 2: Sanity build**

Run: `hugo --renderToMemory --quiet 2>&1 | head -20`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/cite/fmt-apa.html
git commit -m "cite: APA format generator"
```

---

### Task 6: Chicago format generator

**Files:**
- Create: `layouts/partials/cite/fmt-chicago.html`

- [ ] **Step 1: Create the partial**

Write `layouts/partials/cite/fmt-chicago.html`:

```hugo
{{- /* Renders a citation dict as a Chicago notes-bibliography citation.
       Format: <First Last>, "<Title>," <Venue>, <year>, <url>.
*/ -}}

{{- $cite := . -}}

{{- /* Authors: First Last ordering for Chicago notes form. citations.yaml
       stores "Last, F." — flip first-author "Last, F." → "F. Last"; pass
       subsequent authors through "F. Last" the same way. */ -}}
{{- $flipped := slice -}}
{{- range $cite.authors -}}
  {{- $parts := split . ", " -}}
  {{- if eq (len $parts) 2 -}}
    {{- $flipped = $flipped | append (printf "%s %s" (index $parts 1) (index $parts 0)) -}}
  {{- else -}}
    {{- $flipped = $flipped | append . -}}
  {{- end -}}
{{- end -}}
{{- $authors_str := delimit $flipped ", " -}}

{{- $parts := slice (printf "%s, \"%s,\"" $authors_str $cite.title) -}}
{{- with $cite.venue -}}{{- $parts = $parts | append (printf "%s," .) -}}{{- end -}}
{{- $parts = $parts | append (printf "%d," $cite.year) -}}
{{- with $cite.url -}}{{- $parts = $parts | append (printf "%s." .) -}}{{- else -}}{{- $parts = $parts | append "." -}}{{- end -}}

{{- return delimit $parts " " -}}
```

- [ ] **Step 2: Sanity build**

Run: `hugo --renderToMemory --quiet 2>&1 | head -20`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/cite/fmt-chicago.html
git commit -m "cite: Chicago format generator"
```

---

### Task 7: MLA format generator

**Files:**
- Create: `layouts/partials/cite/fmt-mla.html`

- [ ] **Step 1: Create the partial**

Write `layouts/partials/cite/fmt-mla.html`:

```hugo
{{- /* Renders a citation dict as an MLA-9 citation.
       Format: <Last, First>. "<Title>." <Venue>, <year>, <url>.
*/ -}}

{{- $cite := . -}}

{{- /* MLA keeps the first author Last-comma-First form. Convert "Last, F." to
       "Last, First" if frontmatter uses full given name; citations.yaml stores
       initial form — use as-is. Subsequent authors flipped to "First Last". */ -}}
{{- $authors := $cite.authors -}}
{{- $first_author := index $authors 0 -}}
{{- $rest_flipped := slice -}}
{{- if gt (len $authors) 1 -}}
  {{- $rest := after 1 $authors -}}
  {{- range $rest -}}
    {{- $parts := split . ", " -}}
    {{- if eq (len $parts) 2 -}}
      {{- $rest_flipped = $rest_flipped | append (printf "%s %s" (index $parts 1) (index $parts 0)) -}}
    {{- else -}}
      {{- $rest_flipped = $rest_flipped | append . -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{- $authors_str := $first_author -}}
{{- if gt (len $rest_flipped) 0 -}}
  {{- $authors_str = printf "%s, and %s" $first_author (delimit $rest_flipped ", and ") -}}
{{- end -}}

{{- $parts := slice (printf "%s. \"%s.\"" $authors_str $cite.title) -}}
{{- with $cite.venue -}}{{- $parts = $parts | append (printf "%s," .) -}}{{- end -}}
{{- $parts = $parts | append (printf "%d," $cite.year) -}}
{{- with $cite.url -}}{{- $parts = $parts | append (printf "%s." .) -}}{{- else -}}{{- $parts = $parts | append "." -}}{{- end -}}

{{- return delimit $parts " " -}}
```

- [ ] **Step 2: Sanity build**

Run: `hugo --renderToMemory --quiet 2>&1 | head -20`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/cite/fmt-mla.html
git commit -m "cite: MLA format generator"
```

---

### Task 8: RIS format generator

**Files:**
- Create: `layouts/partials/cite/fmt-ris.html`

- [ ] **Step 1: Create the partial**

Write `layouts/partials/cite/fmt-ris.html`:

```hugo
{{- /* Renders a citation dict as an RIS export string.

       Type-code map: article→JOUR, book→BOOK, inproceedings→CONF,
                      online→ELEC, misc→GEN.
*/ -}}

{{- $cite := . -}}

{{- $type_map := dict
      "article"       "JOUR"
      "book"          "BOOK"
      "inproceedings" "CONF"
      "online"        "ELEC"
      "misc"          "GEN" -}}
{{- $type_code := default "GEN" (index $type_map $cite.type) -}}

{{- $lines := slice (printf "TY  - %s" $type_code) -}}
{{- range $cite.authors -}}
  {{- $lines = $lines | append (printf "AU  - %s" .) -}}
{{- end -}}
{{- $lines = $lines | append (printf "PY  - %d" $cite.year) -}}
{{- $lines = $lines | append (printf "TI  - %s" $cite.title) -}}
{{- with $cite.venue -}}{{- $lines = $lines | append (printf "JO  - %s" .) -}}{{- end -}}
{{- with $cite.url -}}{{- $lines = $lines | append (printf "UR  - %s" .) -}}{{- end -}}
{{- with $cite.doi -}}{{- $lines = $lines | append (printf "DO  - %s" .) -}}{{- end -}}
{{- with $cite.isbn -}}{{- $lines = $lines | append (printf "SN  - %s" .) -}}{{- end -}}
{{- $lines = $lines | append "ER  -" -}}

{{- return delimit $lines "\n" -}}
```

- [ ] **Step 2: Sanity build**

Run: `hugo --renderToMemory --quiet 2>&1 | head -20`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/cite/fmt-ris.html
git commit -m "cite: RIS format generator"
```

---

### Task 9: Meta-tags partial + head.html wiring

**Files:**
- Create: `layouts/partials/cite/meta-tags.html`
- Modify: `layouts/partials/head.html`

- [ ] **Step 1: Create the meta-tags partial**

Write `layouts/partials/cite/meta-tags.html`:

```hugo
{{- /* Emits Highwire Press citation_* meta tags for Zotero auto-detect.
       Input: . (a Page) */ -}}

{{- $cite := partial "cite/normalize-page.html" . -}}
<meta name="citation_title" content="{{ $cite.title }}">
{{- range $cite.authors }}
<meta name="citation_author" content="{{ . }}">
{{- end }}
<meta name="citation_publication_date" content="{{ $cite.pub_date }}">
<meta name="citation_online_date" content="{{ $cite.online_date }}">
<meta name="citation_public_url" content="{{ $cite.url }}">
{{- with $cite.doi }}
<meta name="citation_doi" content="{{ . }}">
{{- end }}
{{- with $cite.isbn }}
<meta name="citation_isbn" content="{{ . }}">
{{- end }}
```

- [ ] **Step 2: Read existing `layouts/partials/head.html` to find the right insertion point**

Run: `grep -n '</head>' layouts/partials/head.html`
Expected: prints the line containing `</head>`.

- [ ] **Step 3: Insert conditional include just before `</head>`**

Find the line containing `</head>` and insert immediately before it:

```hugo
{{- $citable_sections := slice "essays" "garden" "research" "works" -}}
{{- if and (in $citable_sections .Section) (eq .Kind "page") -}}
  {{- partial "cite/meta-tags.html" . }}
{{- end -}}
```

- [ ] **Step 4: Build and verify meta tags appear on a citable page**

```bash
hugo --quiet
grep -c 'citation_title' public/essays/example-essay-one/index.html
```
Expected: ≥ 1.

```bash
grep -c 'citation_title' public/about/index.html
```
Expected: `0` (About is not citable).

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/cite/meta-tags.html layouts/partials/head.html
git commit -m "cite: emit Highwire meta tags on citable pages"
```

---

### Task 10: Data-blob partial

**Files:**
- Create: `layouts/partials/cite/data-blob.html`

- [ ] **Step 1: Create the partial**

Write `layouts/partials/cite/data-blob.html`:

```hugo
{{- /* Emits <script type=application/json id=cite-data> with self + refs.

       Must be rendered AFTER the page body (so Page.Scratch.cite-keys is
       populated by the cite shortcode). Caller (per-section single template)
       is responsible for ordering.

       jsonify runs inline at the <script> embed point to avoid the minifier
       trap documented in CLAUDE.md's "Build-time graph data" section.
*/ -}}

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
  {{- if $entry -}}
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
{{- end -}}

<script type="application/json" id="cite-data">
{{ dict "self" $self "refs" $refs | jsonify }}
</script>
```

- [ ] **Step 2: Commit (build verification happens in Task 13 when wired in)**

```bash
git add layouts/partials/cite/data-blob.html
git commit -m "cite: data-blob partial — JSON blob with self + refs"
```

---

### Task 11: Static-fallback + button partials

**Files:**
- Create: `layouts/partials/cite/static-fallback.html`
- Create: `layouts/partials/cite/button.html`

- [ ] **Step 1: Create the static-fallback partial**

Write `layouts/partials/cite/static-fallback.html`:

```hugo
{{- /* No-JS fallback. Renders all 5 formats inline at page bottom under
       native <details> elements. Stays visible with JS on too — the modal
       is a shortcut to the same content, not a replacement. */ -}}

{{- $self := partial "cite/normalize-page.html" . -}}
<section id="cite-this" class="cite-static" aria-labelledby="cite-this-heading">
  <h2 id="cite-this-heading">Cite this page</h2>
  <details><summary>BibTeX</summary><pre>{{ partial "cite/fmt-bibtex.html"  $self }}</pre></details>
  <details><summary>APA</summary><pre>{{ partial "cite/fmt-apa.html"     $self }}</pre></details>
  <details><summary>Chicago</summary><pre>{{ partial "cite/fmt-chicago.html" $self }}</pre></details>
  <details><summary>MLA</summary><pre>{{ partial "cite/fmt-mla.html"     $self }}</pre></details>
  <details><summary>RIS</summary><pre>{{ partial "cite/fmt-ris.html"     $self }}</pre></details>
</section>
```

- [ ] **Step 2: Create the button partial**

Write `layouts/partials/cite/button.html`:

```hugo
{{- /* "Cite this page" link. Inserted by per-section single templates
       inside the meta row beneath the title. JS will preventDefault on
       click and open the modal; with no JS, the href anchors to the
       static fallback section at page bottom. */ -}}
<a class="cite-page-link" href="#cite-this" data-action="open-cite-modal">Cite this page</a>
```

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/cite/static-fallback.html layouts/partials/cite/button.html
git commit -m "cite: static-fallback + button partials"
```

---

### Task 12: Modal partial + baseof wiring

**Files:**
- Create: `layouts/partials/cite/modal.html`
- Modify: `layouts/_default/baseof.html`

- [ ] **Step 1: Create the modal partial**

Write `layouts/partials/cite/modal.html`:

```html
<dialog id="cite-modal" class="cite-modal" aria-labelledby="cite-modal-title">
  <header class="cite-modal-header">
    <h2 id="cite-modal-title">Cite</h2>
    <p class="cite-modal-subtitle" id="cite-modal-subtitle"></p>
    <button class="cite-modal-close" type="button" aria-label="Close">×</button>
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
    <a class="cite-modal-download" download href="#">Download .bib</a>
    <span class="cite-modal-toast" role="status" aria-live="polite"></span>
  </div>
</dialog>
```

- [ ] **Step 2: Read `layouts/_default/baseof.html` to find the right insertion point**

Run: `grep -n 'search-modal\|</body>' layouts/_default/baseof.html`
Expected: shows where the existing `search-modal` partial is included (singleton dialog) — insert immediately after.

- [ ] **Step 3: Insert conditional modal include after search-modal**

Find the line including the `search-modal` partial and add immediately after:

```hugo
{{- $citable_sections := slice "essays" "garden" "research" "works" -}}
{{- if and (in $citable_sections .Section) (eq .Kind "page") -}}
  {{- partial "cite/modal.html" . }}
{{- end -}}
```

- [ ] **Step 4: Build and verify the modal markup is emitted on a citable page**

```bash
hugo --quiet
grep -c 'id="cite-modal"' public/essays/example-essay-one/index.html
```
Expected: `1`.

```bash
grep -c 'id="cite-modal"' public/about/index.html
```
Expected: `0`.

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/cite/modal.html layouts/_default/baseof.html
git commit -m "cite: modal partial + baseof wiring on citable pages"
```

---

### Task 13: Per-section single template wiring

**Files:**
- Modify: `layouts/essays/single.html`
- Modify: `layouts/garden/single.html`
- Modify: `layouts/research-theme/single.html`
- Modify: `layouts/research-question/single.html`
- Modify: `layouts/works-games/single.html`
- Modify: `layouts/works-music/single.html`
- Modify: `layouts/works-poetry/single.html`

Two changes per template:

1. Insert `{{ partial "cite/button.html" . }}` into the meta row beneath the title.
2. After the page body + references, add `{{ partial "cite/static-fallback.html" . }}` and `{{ partial "cite/data-blob.html" . }}` (data-blob MUST be last so `Scratch.cite-keys` is populated by body + references).

- [ ] **Step 1: Insert button in essays/single.html**

In `layouts/essays/single.html`, find the line:
```
    {{ partial "essay-meta.html" . }}
```
Add immediately after:
```
    {{ partial "cite/button.html" . }}
```

Then at the very end of the `<article>` block (before `</article>`), add:
```
  <div class="reading-column">{{ partial "cite/static-fallback.html" . }}</div>
  {{ partial "cite/data-blob.html" . }}
```

- [ ] **Step 2: Read `layouts/garden/single.html`**

Run: `cat layouts/garden/single.html | head -40`
Expected: shows the structure; find the analogous meta row and post-body location.

- [ ] **Step 3: Insert button + static-fallback + data-blob in garden/single.html**

Find the partial call for the garden note-header (likely `{{ partial "garden/note-header.html" . }}` or similar). Add `{{ partial "cite/button.html" . }}` adjacent to the meta. At the end of the page body block, add:

```
{{ partial "cite/static-fallback.html" . }}
{{ partial "cite/data-blob.html" . }}
```

- [ ] **Step 4: Repeat for research-theme, research-question, works-games, works-music, works-poetry**

For each of:
- `layouts/research-theme/single.html`
- `layouts/research-question/single.html`
- `layouts/works-games/single.html`
- `layouts/works-music/single.html`
- `layouts/works-poetry/single.html`

Add `{{ partial "cite/button.html" . }}` in the meta area beneath the title and the two post-body partials:

```
{{ partial "cite/static-fallback.html" . }}
{{ partial "cite/data-blob.html" . }}
```

- [ ] **Step 5: Build and verify across all 7 sections**

```bash
hugo --quiet
for f in \
  public/essays/example-essay-one/index.html \
  public/garden/index.html \
  public/research/themes/*/index.html \
  public/research/questions/*/index.html \
  public/works/games/*/index.html \
  public/works/music/*/index.html \
  public/works/poetry/*/index.html ; do
  echo "$f: $(grep -c 'id=\"cite-data\"' "$f") cite-data, $(grep -c 'cite-page-link' "$f") button"
done
```
Expected: every per-page output has `1 cite-data, 1 button`. Section umbrella pages may have `0 cite-data, 0 button`.

- [ ] **Step 6: Commit**

```bash
git add layouts/essays/single.html layouts/garden/single.html \
        layouts/research-theme/single.html layouts/research-question/single.html \
        layouts/works-games/single.html layouts/works-music/single.html \
        layouts/works-poetry/single.html
git commit -m "cite: wire button + static-fallback + data-blob into 7 single templates"
```

---

### Task 14: Half B markup in essay-references.html

**Files:**
- Modify: `layouts/partials/essay-references.html`

- [ ] **Step 1: Replace the `<li>` body with the extended version**

In `layouts/partials/essay-references.html`, find the existing `<li id="ref-{{ . }}">` block (lines 11–17 today) and replace it with:

```hugo
<li id="ref-{{ . }}">
  {{ delimit $entry.authors ", " }} ({{ $entry.year }}).
  <em>{{ $entry.title }}</em>.
  {{ $entry.venue }}.
  {{ with $entry.url }}<a href="{{ . }}" rel="noopener">source</a>{{ end }}
  {{ with $entry.notes_ref }}<a href="/garden/{{ . }}/" class="ref-note">related note</a>{{ end }}
  <span class="ref-cite-actions" aria-label="Cite this reference">
    <button class="ref-cite-copy" data-cite-key="{{ . }}" data-format="bibtex" type="button">BibTeX</button>
    <button class="ref-cite-copy" data-cite-key="{{ . }}" data-format="apa" type="button">APA</button>
    <button class="ref-cite-copy" data-cite-key="{{ . }}" data-format="ris" type="button">.ris</button>
    <a class="ref-cite-full" href="#ref-{{ . }}" data-cite-key="{{ . }}">More →</a>
  </span>
</li>
```

- [ ] **Step 2: Build and verify ref-cite-actions appears in the references list**

```bash
hugo --quiet
grep -c 'ref-cite-actions' public/essays/example-essay-one/index.html
```
Expected: ≥ 1 (one per reference in the essay).

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/essay-references.html
git commit -m "cite: Half B — per-reference cite actions in <li>"
```

---

### Task 15: JS runtime — `cite.js`

**Files:**
- Create: `assets/js/cite.js`

- [ ] **Step 1: Create the module**

Write `assets/js/cite.js`:

```js
// Citation export runtime. Reads the inline #cite-data JSON blob,
// opens the modal on "Cite this page" / "More →" clicks, handles
// tab switching, copy-to-clipboard, and download links.
//
// Bails silently if #cite-data is absent (page isn't citable).

const STORAGE_KEY = 'cite-format-pref';
const EXT_MAP = {
  bibtex: '.bib',
  apa: '.txt',
  chicago: '.txt',
  mla: '.txt',
  ris: '.ris',
};
const MIME_MAP = {
  bibtex: 'application/x-bibtex',
  apa: 'text/plain',
  chicago: 'text/plain',
  mla: 'text/plain',
  ris: 'application/x-research-info-systems',
};

let citeData = null;
let modal = null;
let outputEl = null;
let subtitleEl = null;
let toastEl = null;
let downloadEl = null;
let currentSource = null;  // { citekey, title, formats }
let currentFormat = 'bibtex';

function parseDataBlob() {
  const el = document.getElementById('cite-data');
  if (!el) return null;
  try {
    return JSON.parse(el.textContent);
  } catch (e) {
    console.warn('cite: failed to parse #cite-data', e);
    return null;
  }
}

function loadFormatPref() {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v && EXT_MAP[v]) return v;
  } catch (_) {}
  return 'bibtex';
}

function saveFormatPref(format) {
  try { localStorage.setItem(STORAGE_KEY, format); } catch (_) {}
}

function setActiveTab(format) {
  modal.querySelectorAll('[role="tab"]').forEach((btn) => {
    btn.setAttribute('aria-selected', btn.dataset.format === format ? 'true' : 'false');
  });
  currentFormat = format;
  const str = currentSource.formats[format];
  outputEl.textContent = str;
  const ext = EXT_MAP[format];
  const mime = MIME_MAP[format];
  const filename = `${currentSource.citekey}${ext}`;
  downloadEl.href = `data:${mime};charset=utf-8,${encodeURIComponent(str)}`;
  downloadEl.setAttribute('download', filename);
  downloadEl.textContent = `Download ${ext}`;
  saveFormatPref(format);
}

function openModal(source, subtitle) {
  if (!source) return;
  currentSource = source;
  subtitleEl.textContent = subtitle || '';
  const pref = loadFormatPref();
  setActiveTab(pref);
  if (typeof modal.showModal === 'function') {
    modal.showModal();
  } else {
    modal.setAttribute('open', '');
  }
}

function closeModal() {
  if (modal.hasAttribute('open')) modal.removeAttribute('open');
  if (typeof modal.close === 'function') modal.close();
}

function copyToClipboard(text) {
  const writeToast = (msg) => {
    toastEl.textContent = msg;
    setTimeout(() => { toastEl.textContent = ''; }, 2000);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(
      () => writeToast('Copied'),
      () => writeToast('Press Ctrl+C to copy'),
    );
  } else {
    writeToast('Press Ctrl+C to copy');
  }
}

function onDocumentClick(e) {
  // Cite this page link
  const pageLink = e.target.closest('.cite-page-link');
  if (pageLink) {
    e.preventDefault();
    openModal(citeData.self, 'This page');
    return;
  }
  // Half B "More →" full picker
  const fullBtn = e.target.closest('.ref-cite-full');
  if (fullBtn) {
    const key = fullBtn.dataset.citeKey;
    const ref = citeData.refs && citeData.refs[key];
    if (ref) {
      e.preventDefault();
      openModal({ citekey: key, title: ref.title, formats: ref.formats }, `Reference: ${ref.title}`);
    }
    return;
  }
  // Half B inline quick-copy buttons (live in ref <li> AND inside hover-card)
  const copyBtn = e.target.closest('.ref-cite-copy');
  if (copyBtn) {
    const key = copyBtn.dataset.citeKey;
    const fmt = copyBtn.dataset.format;
    const ref = citeData.refs && citeData.refs[key];
    if (ref && ref.formats && ref.formats[fmt]) {
      copyToClipboard(ref.formats[fmt]);
    }
    return;
  }
  // Modal tab
  const tab = e.target.closest('.cite-modal-tabs [role="tab"]');
  if (tab && modal.contains(tab)) {
    setActiveTab(tab.dataset.format);
    return;
  }
  // Modal close
  if (e.target.closest('.cite-modal-close')) {
    closeModal();
    return;
  }
  // Modal copy
  if (e.target.closest('.cite-modal-copy')) {
    copyToClipboard(outputEl.textContent);
    return;
  }
  // Backdrop click
  if (e.target === modal) {
    closeModal();
  }
}

function onKeydown(e) {
  if (e.key === 'Escape' && modal && modal.hasAttribute('open')) {
    closeModal();
  }
}

export function initCite() {
  citeData = parseDataBlob();
  if (!citeData) return;
  modal = document.getElementById('cite-modal');
  if (!modal) return;
  outputEl = document.getElementById('cite-modal-output');
  subtitleEl = document.getElementById('cite-modal-subtitle');
  toastEl = modal.querySelector('.cite-modal-toast');
  downloadEl = modal.querySelector('.cite-modal-download');
  document.addEventListener('click', onDocumentClick);
  document.addEventListener('keydown', onKeydown);
}
```

- [ ] **Step 2: Commit**

```bash
git add assets/js/cite.js
git commit -m "cite: JS runtime — modal, tabs, copy, download"
```

---

### Task 16: Bundle entry + scripts.html wiring

**Files:**
- Create: `assets/js/entry-cite.js`
- Modify: `layouts/partials/scripts.html`

- [ ] **Step 1: Create the bundle entry**

Write `assets/js/entry-cite.js`:

```js
import { initCite } from './cite.js';
initCite();
```

- [ ] **Step 2: Read existing scripts.html for the pattern**

Run: `cat layouts/partials/scripts.html`
Expected: shows existing `js.Build` calls for index, essay, garden, research, works, library, search.

- [ ] **Step 3: Add the new entry to scripts.html**

Find the existing bundle for `entry-search.js` (loaded on every page). Add a new conditional bundle for cite at the end of the file (or alongside the section-scoped bundles). Use the same `js.Build` + `minify` + `fingerprint` + SRI pattern as the existing entries:

```hugo
{{- $citable_sections := slice "essays" "garden" "research" "works" -}}
{{- if and (in $citable_sections .Section) (eq .Kind "page") -}}
  {{- $opts := dict "minify" hugo.IsProduction "format" "iife" "target" "es2017" -}}
  {{- $cite := resources.Get "js/entry-cite.js" | js.Build $opts -}}
  {{- if hugo.IsProduction -}}
    {{- $cite = $cite | fingerprint "sha512" -}}
    <script src="{{ $cite.RelPermalink }}" integrity="{{ $cite.Data.Integrity }}" crossorigin="anonymous"></script>
  {{- else -}}
    <script src="{{ $cite.RelPermalink }}"></script>
  {{- end -}}
{{- end -}}
```

(Adjust the exact dict keys + minify/fingerprint pattern to match the existing entries in the file — they all share a helper-like structure.)

- [ ] **Step 4: Build and verify the bundle is emitted on a citable page**

```bash
hugo --quiet
grep -c 'cite\.' public/essays/example-essay-one/index.html
```
Expected: ≥ 1 (cite.<hash>.js reference).

```bash
grep -c 'cite\.' public/about/index.html
```
Expected: `0`.

- [ ] **Step 5: Commit**

```bash
git add assets/js/entry-cite.js layouts/partials/scripts.html
git commit -m "cite: bundle entry + scripts.html wiring for citable pages"
```

---

### Task 17: CSS §43

**Files:**
- Modify: `assets/css/main.css` (append at end)

- [ ] **Step 1: Read the end of `assets/css/main.css` to confirm current section number**

Run: `grep -E '^/\* §[0-9]+' assets/css/main.css | tail -3`
Expected: shows §41 and §42 (page sidebar, search modal) as the last sections.

- [ ] **Step 2: Append §43 at the end of `assets/css/main.css`**

```css

/* §43 — citation export ----------------------------------------------- */

.cite-page-link {
  font-size: 0.75rem;
  color: var(--color-burgundy);
  text-decoration: underline;
  text-underline-offset: 2px;
  margin-left: 0.5rem;
}
.cite-page-link:hover { text-decoration-thickness: 2px; }

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

@media (max-width: 720px) {
  .cite-modal {
    width: 100vw; max-width: none; margin: 0 auto;
    position: fixed; bottom: 0; left: 0; right: 0; top: auto;
    border-radius: 8px 8px 0 0;
  }
}

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

- [ ] **Step 3: Update the section index at the top of `main.css`**

Find the top-of-file index (which lists §1–§42). Add a `§43 — citation export` entry preserving the existing format.

- [ ] **Step 4: Verify contrast linter still passes**

Run: `python3 tools/check-contrast.py`
Expected: exits 0 (the new section uses existing tokens; nothing changes for the four checked pairings).

- [ ] **Step 5: Commit**

```bash
git add assets/css/main.css
git commit -m "cite: CSS §43 — modal, button, static fallback, ref actions"
```

---

### Task 18: Linter — write failing tests

**Files:**
- Create: `tools/test_check_cite_meta.py`

- [ ] **Step 1: Read an existing linter test sibling for the layout**

Run: `head -60 tools/test_check_pagefind_meta.py`
Expected: shows the stdlib-only `unittest.TestCase` pattern with synthetic HTML fixtures.

- [ ] **Step 2: Create `tools/test_check_cite_meta.py`**

Write:

```python
"""Unit tests for check_cite_meta.py.

Mirrors the layout of test_check_pagefind_meta.py: synthetic HTML strings,
no Hugo dependency, stdlib only.
"""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from check_cite_meta import (
    inspect_html,
    is_citable_path,
    REQUIRED_META,
    CITEKEY_RE,
)

CITATIONS_FIXTURE = {
    "example-source-1": {"authors": ["Lastname, F."], "year": 2020,
                         "title": "Lorem", "venue": "Journal", "url": ""},
}

HAPPY = """
<html><head>
<meta name="citation_title" content="A">
<meta name="citation_author" content="Madkour, Abdelrahman">
<meta name="citation_publication_date" content="2026-05-13">
<meta name="citation_online_date" content="2026-05-13">
<meta name="citation_public_url" content="https://x/y/">
</head><body>
<section id="cite-this"><details></details></section>
<script type="application/json" id="cite-data">
{"self":{"citekey":"madkour-2026-my-slug","title":"A","formats":{"bibtex":"x","apa":"x","chicago":"x","mla":"x","ris":"x"}},"refs":{}}
</script>
</body></html>
"""


class TestCiteMeta(unittest.TestCase):
    def test_happy_path_passes(self):
        issues = inspect_html(HAPPY, citations=CITATIONS_FIXTURE)
        self.assertEqual(issues, [])

    def test_missing_meta_tag_fails(self):
        broken = HAPPY.replace('<meta name="citation_title" content="A">', '')
        issues = inspect_html(broken, citations=CITATIONS_FIXTURE)
        self.assertTrue(any('citation_title' in i for i in issues))

    def test_bad_citekey_shape_fails(self):
        broken = HAPPY.replace('madkour-2026-my-slug', 'wrong_format')
        issues = inspect_html(broken, citations=CITATIONS_FIXTURE)
        self.assertTrue(any('citekey' in i for i in issues))

    def test_missing_cite_data_fails(self):
        broken = HAPPY.replace('<script type="application/json" id="cite-data">', '<script type="application/json" id="something-else">')
        issues = inspect_html(broken, citations=CITATIONS_FIXTURE)
        self.assertTrue(any('cite-data' in i for i in issues))

    def test_missing_static_section_fails(self):
        broken = HAPPY.replace('<section id="cite-this"><details></details></section>', '')
        issues = inspect_html(broken, citations=CITATIONS_FIXTURE)
        self.assertTrue(any('cite-this' in i for i in issues))

    def test_ref_key_not_in_citations_fails(self):
        broken = HAPPY.replace(
            '"refs":{}',
            '"refs":{"unknown-key":{"title":"x","formats":{"bibtex":"y","apa":"y","chicago":"y","mla":"y","ris":"y"}}}'
        )
        issues = inspect_html(broken, citations=CITATIONS_FIXTURE)
        self.assertTrue(any('unknown-key' in i for i in issues))

    def test_is_citable_path_essays(self):
        self.assertTrue(is_citable_path('public/essays/some-slug/index.html'))

    def test_is_citable_path_about_not_citable(self):
        self.assertFalse(is_citable_path('public/about/index.html'))

    def test_is_citable_path_library_not_citable(self):
        self.assertFalse(is_citable_path('public/library/reading/index.html'))

    def test_is_citable_path_garden_note_yes_index_no(self):
        self.assertTrue(is_citable_path('public/garden/some-note/index.html'))
        self.assertFalse(is_citable_path('public/garden/index.html'))

    def test_citekey_re_accepts_kebab_slug(self):
        self.assertRegex('madkour-2026-on-knowing-tools', CITEKEY_RE)

    def test_citekey_re_rejects_underscore(self):
        self.assertNotRegex('madkour-2026-on_knowing_tools', CITEKEY_RE)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 3: Verify tests fail with "module not found"**

Run: `python3 tools/test_check_cite_meta.py`
Expected: `ModuleNotFoundError: No module named 'check_cite_meta'` (linter doesn't exist yet — failure is expected).

- [ ] **Step 4: Commit**

```bash
git add tools/test_check_cite_meta.py
git commit -m "cite: failing tests for check_cite_meta linter"
```

---

### Task 19: Linter — implement `check_cite_meta.py`

**Files:**
- Create: `tools/check_cite_meta.py`

- [ ] **Step 1: Create the linter**

Write `tools/check_cite_meta.py`:

```python
"""Verify citation export markup on every citable page in public/.

Asserts each citable page (essays/garden/research/works single pages) has:
- citation_title, citation_author, citation_publication_date,
  citation_online_date, citation_public_url meta tags
- <script type="application/json" id="cite-data"> that parses, with:
    - self.citekey matching `madkour-<year>-<slug>`
    - self.formats with all 5 keys (bibtex, apa, chicago, mla, ris)
    - every refs key existing in data/citations.yaml
- <section id="cite-this"> static fallback

Non-citable pages (About, Library, Home, umbrellas, graph pages) MUST NOT
have these markers.

Stdlib only. Exits non-zero on any violation.
"""
from __future__ import annotations
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

PUBLIC = Path('public')

REQUIRED_META = [
    'citation_title',
    'citation_author',
    'citation_publication_date',
    'citation_online_date',
    'citation_public_url',
]
REQUIRED_FORMATS = ['bibtex', 'apa', 'chicago', 'mla', 'ris']
CITEKEY_RE = re.compile(r'^madkour-\d{4}-[a-z0-9-]+$')

CITABLE_PREFIXES = (
    'public/essays/',
    'public/garden/',
    'public/research/themes/',
    'public/research/questions/',
    'public/works/games/',
    'public/works/music/',
    'public/works/poetry/',
)

NON_CITABLE_EXACT = {
    'public/index.html',
    'public/about/index.html',
    'public/library/index.html',
    'public/library/reading/index.html',
    'public/library/listening/index.html',
    'public/library/playing/index.html',
    'public/library/watching/index.html',
    'public/essays/index.html',
    'public/garden/index.html',
    'public/garden/graph/index.html',
    'public/research/index.html',
    'public/research/graph/index.html',
    'public/works/index.html',
    'public/works/graph/index.html',
}


def is_citable_path(p: str) -> bool:
    p = p.replace('\\', '/')
    if p in NON_CITABLE_EXACT:
        return False
    if not any(p.startswith(prefix) for prefix in CITABLE_PREFIXES):
        return False
    # Exclude section indexes within citable prefixes (e.g., /essays/index.html)
    rest = p[len('public/'):]
    parts = rest.split('/')
    # Citable pages are bundled: /essays/<slug>/index.html or
    # /research/themes/<slug>/index.html, etc. So path must have a
    # named bundle slug before the trailing /index.html.
    if parts[-1] != 'index.html':
        return False
    # Need at least: <section>/<slug>/index.html (3 parts) or deeper.
    return len(parts) >= 3


class _MetaCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.metas = []
        self.cite_data = None
        self.has_cite_this = False
        self._in_cite_data = False
        self._cite_data_buf = []

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        if tag == 'meta' and attrs_d.get('name', '').startswith('citation_'):
            self.metas.append((attrs_d['name'], attrs_d.get('content', '')))
        elif tag == 'script' and attrs_d.get('id') == 'cite-data':
            self._in_cite_data = True
        elif tag == 'section' and attrs_d.get('id') == 'cite-this':
            self.has_cite_this = True

    def handle_endtag(self, tag):
        if tag == 'script' and self._in_cite_data:
            self._in_cite_data = False
            self.cite_data = ''.join(self._cite_data_buf).strip()

    def handle_data(self, data):
        if self._in_cite_data:
            self._cite_data_buf.append(data)


def inspect_html(html: str, citations: dict) -> list[str]:
    issues = []
    p = _MetaCollector()
    p.feed(html)

    meta_names = [m[0] for m in p.metas]
    for required in REQUIRED_META:
        if required not in meta_names:
            issues.append(f'missing <meta name="{required}">')

    if p.cite_data is None:
        issues.append('missing <script id="cite-data">')
    else:
        try:
            blob = json.loads(p.cite_data)
        except json.JSONDecodeError as e:
            issues.append(f'cite-data JSON parse error: {e}')
            blob = None
        if blob is not None:
            self_obj = blob.get('self')
            if not isinstance(self_obj, dict):
                issues.append('cite-data.self missing or not a dict')
            else:
                key = self_obj.get('citekey', '')
                if not CITEKEY_RE.match(key):
                    issues.append(f'bad citekey shape: {key!r}')
                formats = self_obj.get('formats', {})
                for f in REQUIRED_FORMATS:
                    if not formats.get(f):
                        issues.append(f'self.formats.{f} missing or empty')
            refs = blob.get('refs', {})
            if isinstance(refs, dict):
                for key in refs:
                    if key not in citations:
                        issues.append(f'refs.{key} not found in data/citations.yaml')

    if not p.has_cite_this:
        issues.append('missing <section id="cite-this">')

    return issues


def load_citations() -> dict:
    """Stdlib-only YAML key extraction. Returns {key: {}} for each
    top-level entry under `citations:` in data/citations.yaml."""
    path = Path('data/citations.yaml')
    text = path.read_text()
    keys = set()
    in_citations = False
    for line in text.splitlines():
        if line.strip().startswith('#') or not line.strip():
            continue
        if line.startswith('citations:'):
            in_citations = True
            continue
        if in_citations and re.match(r'^  [a-zA-Z0-9_-]+:\s*$', line):
            keys.add(line.strip().rstrip(':'))
    return {k: {} for k in keys}


def main() -> int:
    if not PUBLIC.exists():
        print('public/ not found — run `hugo --minify` first.', file=sys.stderr)
        return 2
    citations = load_citations()
    failures = 0
    for html_path in PUBLIC.rglob('*.html'):
        rel = str(html_path).replace('\\', '/')
        if not is_citable_path(rel):
            continue
        html = html_path.read_text(encoding='utf-8', errors='replace')
        issues = inspect_html(html, citations=citations)
        if issues:
            failures += 1
            print(f'{rel}:')
            for issue in issues:
                print(f'  - {issue}')
    if failures:
        print(f'\n{failures} citable page(s) failed cite-meta validation.', file=sys.stderr)
        return 1
    print('cite-meta: OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 2: Run the unit tests**

Run: `python3 tools/test_check_cite_meta.py`
Expected: all 11 tests pass.

- [ ] **Step 3: Run the linter against the live `public/` build**

```bash
hugo --quiet
python3 tools/check_cite_meta.py
```
Expected: `cite-meta: OK` and exit code 0.

- [ ] **Step 4: Commit**

```bash
git add tools/check_cite_meta.py
git commit -m "cite: 15th linter pair — check_cite_meta validates built pages"
```

---

### Task 20: CI workflow integration

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Find the existing Pagefind metadata steps**

Run: `grep -n 'pagefind_meta\|check_pagefind' .github/workflows/hugo.yaml`
Expected: shows existing steps named like "Lint pagefind metadata linter" and "Verify pagefind metadata on built pages".

- [ ] **Step 2: Insert two new steps after the pagefind metadata steps**

After the "Verify pagefind metadata on built pages" step, insert:

```yaml
      - name: Lint cite_meta linter
        run: python3 tools/test_check_cite_meta.py
      - name: Verify cite_meta on built pages
        run: python3 tools/check_cite_meta.py
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "cite: CI — wire check_cite_meta linter + unit-test sibling"
```

---

### Task 21: Extend `check_citations.py` for new optional fields

**Files:**
- Modify: `tools/check_citations.py`
- Modify: `tools/test_check_citations.py`

- [ ] **Step 1: Read the existing linter to find the field-validation block**

Run: `grep -n 'REQUIRED\|OPTIONAL\|allowed' tools/check_citations.py | head -10`
Expected: shows where required/allowed keys are defined.

- [ ] **Step 2: Add new optional fields to the allowed-keys set**

In `tools/check_citations.py`, find the keys-validation block and add the new optional fields:

```python
OPTIONAL_FIELDS = OPTIONAL_FIELDS | {'doi', 'publisher', 'volume', 'issue', 'pages', 'isbn', 'type'}
```

(Adjust to match the existing variable name in the linter.)

- [ ] **Step 3: Add unit tests for the new optional fields**

In `tools/test_check_citations.py`, add tests asserting an entry with `doi`, `publisher`, `volume`, `issue`, `pages`, `isbn`, or `type` set passes validation:

```python
def test_optional_doi_passes(self):
    data = {'citations': {'k': {'authors': ['A'], 'year': 2020, 'title': 't', 'venue': 'v', 'url': '', 'notes_ref': '', 'doi': '10.x/y'}}}
    self.assertEqual(validate(data), [])

def test_optional_type_passes(self):
    data = {'citations': {'k': {'authors': ['A'], 'year': 2020, 'title': 't', 'venue': 'v', 'url': '', 'notes_ref': '', 'type': 'book'}}}
    self.assertEqual(validate(data), [])

def test_unknown_field_still_fails(self):
    data = {'citations': {'k': {'authors': ['A'], 'year': 2020, 'title': 't', 'venue': 'v', 'url': '', 'notes_ref': '', 'made_up_key': 'x'}}}
    self.assertTrue(validate(data))
```

- [ ] **Step 4: Run tests**

Run: `python3 tools/test_check_citations.py`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tools/check_citations.py tools/test_check_citations.py
git commit -m "cite: extend citations linter for new optional fields"
```

---

### Task 22: Full local build + linter sweep

**Files:** none (verification only)

- [ ] **Step 1: Kill any active dev server**

If a `hugo server` is running in another terminal, stop it. Hugo `--minify` cannot be run while a dev server is alive (CLAUDE.md note: MIME mismatch on CSS).

- [ ] **Step 2: Clean rebuild**

```bash
rm -rf public/ resources/_gen/
hugo --minify
```
Expected: build succeeds with no errors.

- [ ] **Step 3: Run every linter in CI order**

```bash
python3 tools/check-contrast.py
python3 tools/test_check_essay_fixtures.py && python3 tools/check_essay_fixtures.py
python3 tools/test_check_garden_fixtures.py && python3 tools/check_garden_fixtures.py
python3 tools/test_check_garden_links.py && python3 tools/check_garden_links.py
python3 tools/test_check_filter_chips_config.py && python3 tools/check_filter_chips_config.py
python3 tools/test_check_research_fixtures.py && python3 tools/check_research_fixtures.py
python3 tools/test_check_research_links.py && python3 tools/check_research_links.py
python3 tools/test_check_citations.py && python3 tools/check_citations.py
python3 tools/test_check_works_fixtures.py && python3 tools/check_works_fixtures.py
python3 tools/test_check_works_links.py && python3 tools/check_works_links.py
python3 tools/test_check_library_fixtures.py && python3 tools/check_library_fixtures.py
python3 tools/test_check_library_links.py && python3 tools/check_library_links.py
python3 tools/test_check_library_covers.py && python3 tools/check_library_covers.py
python3 tools/test_check_pagefind_meta.py
python3 tools/test_check_cite_meta.py && python3 tools/check_cite_meta.py
python3 tools/check_smoke.py
python3 tools/test_check_page_weights.py && python3 tools/check_page_weights.py
```
Expected: each exits 0.

- [ ] **Step 4: Spot-check page sizes**

```bash
ls -lh public/essays/example-essay-one/index.html
ls -lh public/garden/example-concept-note/index.html  # adjust slug to a real fixture
ls -lh public/research/themes/*/index.html
```
Expected: each well under its budget tier (essay/garden 100 KB, research 600 KB).

- [ ] **Step 5: Spot-check bundle output**

```bash
ls -lh public/*.js | grep cite
```
Expected: one `cite.<hash>.js` file, 3–6 KB.

- [ ] **Step 6: No commit** — verification only.

---

### Task 23: Dev-server walkthrough

**Files:** none (manual verification)

- [ ] **Step 1: Start the dev server**

```bash
hugo server --buildDrafts
```
Expected: serves on `http://localhost:1313`.

- [ ] **Step 2: Walk the citable pages at full viewport**

Open each in your browser and verify:

- `/essays/example-essay-one/` — "Cite this page" link appears under the title/date row. Click → modal opens with BibTeX active tab.
  - Switch each tab: BibTeX / APA / Chicago / MLA / RIS. Each displays a non-empty, plausibly-formatted citation.
  - Click "Copy" — toast says "Copied"; paste somewhere to verify clipboard.
  - Click "Download" — download triggers a file named `madkour-<year>-example-essay-one.<ext>`.
  - Close modal via × button. Close via Escape. Close via backdrop click.
  - Scroll to references list. Each entry has 3 inline copy buttons + "More →" link. Click "More →" — modal opens with that reference's data, subtitle reads `Reference: <title>`.
  - Click one of the inline `BibTeX` buttons — clipboard receives the BibTeX string (no modal opens).
  - Hover an inline `[1]` citation marker — hover-card appears with the same inline copy buttons inside it. Click one — clipboard receives the string.
- `/garden/<some-seedling>/` — modal opens; BibTeX `note` field contains "Garden note, seedling — in-progress thinking".
- `/garden/<some-evergreen>/` — modal opens; BibTeX has no `note` line.
- `/research/themes/<some-slug>/` and `/research/questions/<some-slug>/` — modal works.
- `/works/games/<slug>/` and `/works/music/<slug>/` and `/works/poetry/<slug>/` — modal works.
- `/about/` — no "Cite this page" link; no modal markup.
- `/library/reading/` — no modal.
- `/` — no modal.

- [ ] **Step 3: Half-screen 1080p check (~960px wide)**

Resize the browser to ~960px (one half of a 1080p tile). On a citable page:
- "Cite this page" link still appears and works.
- Modal opens centered; max-width 640px applied; no horizontal scroll.

- [ ] **Step 4: Narrow viewport (≤720px) bottom-sheet check**

Resize to ~400px. On a citable page:
- Modal opens as a bottom-sheet (`position: fixed; bottom: 0`).
- Tabs scrollable or wrap if cramped.
- Copy + Download buttons remain reachable.

- [ ] **Step 5: No-JS verification**

In browser DevTools, disable JavaScript. Reload a citable page.
- Click "Cite this page" — page jumps to bottom-of-page static fallback section.
- Static section shows 5 `<details>` elements; each expands to reveal the citation string.
- References list inline copy buttons are inert (no handler) — expected.

- [ ] **Step 6: Zotero auto-detect (if installed)**

If the Zotero browser connector is installed:
- Visit a citable page.
- Click the Zotero icon in the browser toolbar.
- Confirm Zotero recognizes the page (icon shows the citation icon, not the generic webpage icon).
- Save the citation — verify the entry imports with title + author + date + URL.

- [ ] **Step 7: Kill the dev server**

Stop with Ctrl-C in the dev-server terminal.

- [ ] **Step 8: No commit** — verification only.

---

### Task 24: Update CLAUDE.md + close out

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CSS pipeline section**

In `CLAUDE.md`, find the "CSS pipeline" section. Update the section-list reference to add `§43`:

```
... §41 covers the cross-template page sidebar; §42 covers the search modal; §43 covers citation export.
```

- [ ] **Step 2: Update JS pipeline table**

In `CLAUDE.md`, find the JS bundling table. Add a new row for the cite bundle:

```
| `js/entry-cite.js` | `cite.<hash>.js` (~3–4 KB) | `.Section in {essays, garden, research, works}` AND `.Kind == "page"` | `cite.js` — citation modal runtime |
```

Update the count of bundles at the top of the section (was eight, now nine).

- [ ] **Step 3: Update the linter-pair count**

Find the line "Fourteen linter pairs under `tools/check_*.py`..." and change to **Fifteen**, adding `cite metadata` to the explicit list.

- [ ] **Step 4: Update CI step count**

Find references to "40 named steps" / "40 steps" and update to **42**.

- [ ] **Step 5: Add a Phase summary entry**

In the "Project status" section, add a bullet to "Shipped — Phases 0–6 plus targeted polish":

```
- **Citation export** (post-Phase-8 polish): page-level cite metadata + per-reference cite affordances. Highwire <meta> tags for Zotero auto-detect on all citable pages (essays/garden/research/works single pages). <dialog>-driven modal with five formats (BibTeX/APA/Chicago/MLA/RIS), tabbed picker, copy + download. Hover-card extended with quick-copy buttons (free via existing innerHTML clone). Static `<section id="cite-this">` no-JS fallback at page bottom. 15th linter pair gates the markup. CSS §43. New `cite.<hash>.js` bundle (~3–4 KB) loaded on citable pages only.
```

- [ ] **Step 6: Add deferred-features rows**

In the "Deferred features" table, add these specific rows:

```
| ORCID `citation_author_orcid` meta | Add when an ORCID exists; partial already scaffolds the slot | n/a |
| Library item cite export | Reader appetite; library items already have ISBN/MBID/IGDB/TMDB external metadata | n/a |
| DOI / CrossRef integration | When a DOI registrar is in scope | n/a |
| Bulk export (single .bib for all refs on a page) | Reader feedback if requested | n/a |
| Bilingual / Arabic-aware citation formats | Gated on real Arabic content (Phase 3 follow-up) | n/a |
```

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md
git commit -m "claude.md: document citation export — §43, 15th linter pair, 42 CI steps"
```

- [ ] **Step 8: Final slice check**

Run: `git log --oneline master..HEAD`
Expected: ~20+ small commits on `slice/citation-export`, each implementing one task.

- [ ] **Step 9: Offer dev-server spot-check + merge**

Tell the user:

> Slice ready on `slice/citation-export`. Dev-server walkthrough is in Task 23 — give it a final eyeball at full viewport, 960px, and 400px, plus a no-JS sanity check. Want me to merge to `master` and push, or hold for changes?

Wait for explicit user authorization before merging or pushing — per the memory entry "Always offer dev-server spot-check before merging."
