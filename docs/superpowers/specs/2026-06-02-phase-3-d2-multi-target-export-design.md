# Phase 3 sub-project D.2 — multi-target export — design

**Phase:** Phase 3 sub-project D, second slice. Picks up the existing 2026-05-13 multi-target export spec and adds D.1's semantic-block vocabulary to the cross-target rendering contract.
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §14 Phase 3.
**Prior art:** `docs/superpowers/specs/2026-05-13-multi-target-export-design.md` (446 lines, designed but not implemented; pre-dates D.1 and the dotfiles-publisher convention). This spec supersedes it.
**Depends on:** B.4 (essays publisher; shipped 2026-05-31), D.1 (semantic blocks vocabulary; shipped 2026-06-01), F (citation pipeline; shipped 2026-06-01).

Take one literate org document and publish it to three artifacts in one event: the existing Hugo essay, a PDF technical report, and a Word document. The 12-kind D.1 vocabulary (theorem / lemma / corollary / proposition / definition / proof / remark / example / note / claim / conjecture / axiom) renders correctly across all three targets. Triggering UX is **stock org dispatcher** (`C-c C-e l p` / `C-c C-e o` / `C-c C-e H`) for per-target iteration; the full publish event auto-fires via the existing `M-x a3-publish-deliberate` command when the source carries `#+multi_export: t`.

---

## 1. Scope

**Three artifacts from one org source:**
1. **Hugo essay** — already shipped (B.4 + D.1).
2. **PDF technical report** — via ox-latex + xelatex + biber, using `madkour-paper.cls` (default).
3. **Word document** — via pandoc org → docx, using `reference.docx` (default styles) + `d2-blocks.lua` (D.1 vocab Lua filter).

**Authoring stays inside Emacs.** The standard dispatcher does per-target iteration; the standard `a3-publish-deliberate` command does the full multi-target publish + bundle placement when the source opts in.

**In scope for this slice:**
- One LaTeX class file (`madkour-paper.cls`) covering generic article + amsthm theorem environments + biblatex.
- One Word reference (`reference.docx`) defining paragraph styles for the 12 D.1 block kinds.
- One pandoc Lua filter (`d2-blocks.lua`) that walks `Div.<kind>` elements, applies numbering matching D.1's family-counter logic, and styles per `reference.docx`.
- 5-tag per-target visibility scheme + stock `:noexport:`.
- Site-side downloads cluster + frontmatter contract extension + linter extension.
- One end-to-end fixture (`essay-example-multi.org`) verified via author-machine integration test.

**Out of scope:**
- Cross-reference auto-formatting (`{{< ref-block "thm-foo" >}}` → "Theorem 1"). Deferred to D.x; D.2 maintains D.1's manual reference text convention.
- Section-prefixed numbering ("Theorem 3.2"). D.x.
- `madkour-report.cls` (TOC + front-matter variant). Gated on a real self-distribution trigger.
- Conference LaTeX classes (`acmart`, `IEEEtran`, etc.). Gated on a real submission trigger; author overrides via `#+latex_class:` per-doc.
- Explorable explainables. Sub-project E.
- CI-side LaTeX/pandoc builds. Author-machine sufficient.
- Auto-submit to arXiv / OSF.
- Pandoc docx → org round-trip.
- Multi-language / Arabic-aware PDF.
- Bulk per-page .bib export.

---

## 2. Authoring contract

### Opt-in keyword

At the top of the org file:

```org
#+multi_export: t
```

Without this keyword, the existing B.4 essay path applies unchanged (single output: Hugo essay). With it, D.2's pipeline activates and produces all three.

### Per-doc backend configuration (stock org keywords)

```org
#+title:                Generative Storytelling in Procedural Worlds
#+date:                 2026-05-13
#+author:               Abdelrahman Madkour
#+multi_export:         t
#+latex_class:          madkour-paper                       ; default; ships with the site
#+latex_class_options:  [acmsmall,review,anonymous]         ; only meaningful when overriding the default class (e.g., #+latex_class: acmart)
#+word_reference:       tools/templates/reference.docx      ; default; per-doc override allowed
#+bibliography:         ~/org/bibliography.bib              ; optional; defcustom default
#+csl:                  ~/org/styles/chicago-author-date.csl ; optional pandoc CSL override
#+filetags:             :essay:
#+export_file_name:     generative-storytelling             ; optional; otherwise slugified title
```

**Class fallback:** if `#+latex_class:` is missing, the orchestrator defaults to `madkour-paper`. Conference overrides per-doc.

### Per-target visibility tags

Applied to org subtrees; tags inherit per stock org behavior:

| Tag | Behavior |
|---|---|
| `:NOEXPORT_PDF:` | Skip this subtree during PDF export |
| `:NOEXPORT_WEB:` | Skip during Hugo/web export |
| `:NOEXPORT_WORD:` | Skip during Word export |
| `:WEB_ONLY:` | Shorthand for `:NOEXPORT_PDF:` + `:NOEXPORT_WORD:` |
| `:PAPER_ONLY:` | Shorthand for `:NOEXPORT_WEB:` + `:NOEXPORT_WORD:` |
| `:noexport:` (stock) | Skip everywhere |

Example:

```org
* Abstract                                        :NOEXPORT_WEB:
The paper abstract — the web essay uses #+summary frontmatter instead.

* Introduction
Universal text.

* Code listings                                   :WEB_ONLY:
#+begin_src python :exports both
def foo(): return 42
#+end_src

* Results
Universal.

* Acknowledgements                                :PAPER_ONLY:
Funded by ...
```

### D.1 semantic blocks (no authoring change)

`#+begin_<kind>` blocks with optional `#+attr_shortcode: :title <name> :id <slug>` work exactly as in D.1. The D.2 filter expands the same `:title` + `:id` annotations into per-backend equivalents (Hugo shortcode attrs, LaTeX `\begin{<kind>}[<title>]` + `\label{<id>}`, pandoc `Div[id=<id>, class=<kind>, title=<name>]`).

The 12 kinds: theorem / lemma / corollary / proposition / definition / proof / remark / example / note / claim / conjecture / axiom.

Cross-refs: `[[#thm-ivt][some text]]` org-link. Author-managed reference text — manual, same as D.1. Cross-format expansion:
- Hugo: existing D.1 anchor link.
- LaTeX: `\hyperref[thm-ivt]{some text}`.
- Word: pandoc internal link (`<a href="#thm-ivt">some text</a>`); Word bookmark machinery resolves.

### Inherited conventions (stock org; D.2 does not change them)

- **Figures**: same SVG/PNG source with `#+attr_latex:` / `#+attr_html:` per-backend attributes. Format conversions handled by the orchestrator (see §4.4).
- **Code blocks**: `:exports {code, results, both, none}` per block; same setting across backends.
- **Citations**: org-cite `[cite:@key]`. Bibliography from `#+bibliography:` or defcustom. Same `~/org/bibliography.bib` source feeds all three backends; F.1's bib config is reused verbatim.

### Auto-injected Hugo frontmatter

After successful multi-export run, the orchestrator patches the just-emitted `<bundle>/index.md` frontmatter:

```yaml
multi_export: true
downloads:
  pdf:  generative-storytelling.pdf       # omitted if PDF backend failed
  word: generative-storytelling.docx      # omitted if Word backend failed
```

If **both** backends fail, `multi_export` is set to `false` (downgrades cleanly to plain essay rendering — the downloads cluster never appears, no broken link surface). Partial success (one of two backends) still emits `multi_export: true` with whichever downloads succeeded.

### Asset placement

Hugo essay bundle layout (post-export):

```
content/essays/<slug>/
  index.md                              ; Hugo essay (B.4 emission)
  <slug>.pdf                            ; PDF tech report (D.2; committed)
  <slug>.docx                           ; Word document (D.2; committed)
  figures/
    figure-1.svg                        ; web source (B.4-copied)
```

Format conversions (`figure-1.pdf` for LaTeX, `figure-1.png` for Word) live in `/tmp/multi-export-<slug>/figures/` — never copied to the Hugo bundle, never committed.

PDF/Word artifacts ARE committed to git: small, infrequent, part of the publishable bundle. Stable across re-runs of the same source.

---

## 3. Dispatcher integration + orchestrator

### Standard dispatcher works on multi-export essays

Stock org commands "just work" on a source with `#+multi_export: t`:

| Command | Output |
|---|---|
| `C-c C-e l p` (`org-latex-export-to-pdf`) | `<source>.pdf` in source dir |
| `C-c C-e o o` (`org-odt-export-to-odt`) or pandoc invocation | `<source>.docx` in source dir |
| `C-c C-e H` (`org-hugo-export-to-md`) | Hugo bundle markdown via ox-hugo |

The D.2 hooks apply the visibility filter + D.1 vocab translation automatically when the source has the opt-in keyword. Output goes to org's default location (source-dir-relative); the orchestrator is the only path that moves artifacts into the Hugo bundle.

### Full publish event — `M-x a3-publish-deliberate`

The existing B.4 deliberate-publish command detects `#+multi_export: t` and auto-runs the full pipeline:

```
a3-publish-deliberate <file-or-id>
  └─ existing B.4 essays handler
       └─ a3madkour-pub-essays/publish-essay-file
            └─ standard ox-hugo run → content/essays/<slug>/index.md
            └─ B.4 asset copy (SVGs into bundle)

  └─ if note-metadata has #+multi_export: t
       └─ a3madkour-pub-multi/orchestrate <file> <slug> <bundle-dir>
            ├─ multi-pdf/run         (sequential; each in condition-case)
            ├─ multi-word/run
            └─ multi/patch-downloads-frontmatter <bundle-dir>/index.md
```

Each backend runs in `condition-case`; partial success is the norm. The `downloads:` dict only contains keys whose artifacts exist on disk after the run.

### Hook registration

`a3madkour-publish-multi-filter.el` registers:

- `org-export-before-processing-hook` — checks if buffer-local `#+multi_export:` is `t`. If yes, applies the visibility-tag filter (drops the appropriate subtrees per `org-export-current-backend`). For pandoc (which doesn't see Emacs export filters), the filter is applied in elisp before writing `/tmp/<slug>-filtered.org`.
- `org-export-filter-special-block-functions` — expands `#+attr_shortcode:` annotations into per-backend equivalents for any of the 12 D.1 kinds.

The hooks are no-ops on documents without `#+multi_export: t` — they exit early. Non-multi-export essays go through stock org and B.4 with zero D.2 surface.

### Visibility-tag filter logic

Per-backend skip rules — `:WEB_ONLY:` is shorthand for `:NOEXPORT_PDF:` + `:NOEXPORT_WORD:`; `:PAPER_ONLY:` is shorthand for `:NOEXPORT_WEB:` + `:NOEXPORT_WORD:`.

| Backend | Drop subtrees tagged |
|---|---|
| `hugo` / `md` | `:NOEXPORT_WEB:` or `:PAPER_ONLY:` |
| `latex` | `:NOEXPORT_PDF:` or `:WEB_ONLY:` |
| pandoc (filter applied in elisp before serializing) | `:NOEXPORT_WORD:` or `:WEB_ONLY:` or `:PAPER_ONLY:` |

Stock `:noexport:` is dropped by ox-hugo / ox-latex / pandoc-org natively (no D.2 filter needed).

### Orchestrator command details

**`a3madkour-publish-multi/orchestrate (source-file slug bundle-dir)`** — dispatched by `a3-publish-deliberate` after the Hugo essay handler returns successfully.

1. Probe external tools (`xelatex`, `biber`, `rsvg-convert`, `pandoc`). Missing tools degrade silently — the corresponding backend logs an error to `*a3madkour-pub*` and skips. (Tool paths come from defcustoms; user override is the safety valve.)
2. Probe bibliography (`a3madkour-pub-bib-path` from F.1). If missing AND source has `[cite:@…]` refs, log a clear error and skip the citation-dependent backends. If no citations, skip the probe.
3. Run `multi-pdf/run` in `condition-case`.
4. Run `multi-word/run` in `condition-case`.
5. Run `multi/patch-downloads-frontmatter` against the bundle's `index.md` — only writes if at least one backend produced an artifact AND the resulting content differs from current (idempotent).

### `multi-pdf/run` sequence

1. Resolve org source, slug, bundle dir from orchestrator args.
2. Apply visibility-tag filter + D.1 vocab translation (hooks already registered, so this happens via standard org export-prep).
3. SVG → PDF via `rsvg-convert` for each figure referenced by `[[file:…]]` org-links. Writes to `/tmp/multi-export-<slug>/figures/`.
4. ox-latex export to `/tmp/multi-export-<slug>/<slug>.tex` (using class from `#+latex_class:` or default `madkour-paper`).
5. Run `xelatex → biber → xelatex → xelatex` (4-pass for cross-refs + bibliography).
6. On success, move `/tmp/multi-export-<slug>/<slug>.pdf` → `<bundle-dir>/<slug>.pdf`.
7. On failure, log to `*a3madkour-pub*` with stderr snippet (foldable). Return non-nil for orchestrator to record skip.

### `multi-word/run` sequence

1. Apply visibility-tag filter + D.1 vocab translation. **Serialize the filtered tree** to `/tmp/multi-export-<slug>/<slug>-filtered.org` (pandoc can't see Emacs export filters).
2. SVG → PNG via `rsvg-convert -d 192` for each referenced figure into `/tmp/multi-export-<slug>/figures/`.
3. Run `pandoc -f org -t docx --reference-doc=<site>/tools/templates/reference.docx --lua-filter=<site>/tools/templates/d2-blocks.lua --citeproc --bibliography=<bib> /tmp/multi-export-<slug>/<slug>-filtered.org -o /tmp/multi-export-<slug>/<slug>.docx`.
4. On success, move `/tmp/multi-export-<slug>/<slug>.docx` → `<bundle-dir>/<slug>.docx`.
5. On failure, log + return.

### `multi/patch-downloads-frontmatter`

After backends run, the orchestrator reads `<bundle-dir>/index.md`, parses YAML frontmatter, and adds:

```yaml
multi_export: true
downloads:
  pdf:  <slug>.pdf       # omitted if PDF artifact missing
  word: <slug>.docx      # omitted if Word artifact missing
```

If both artifacts are missing, sets `multi_export: false` (downgrade clean). Uses B.4's existing `write-if-different` helper to avoid spurious mtime touches.

### Error reporting

The existing `*a3madkour-pub*` log buffer (used by B.4) gains a new section per multi-export run:

```
multi-export — Generative Storytelling in Procedural Worlds
slug:   generative-storytelling
bundle: content/essays/generative-storytelling/

  [✓] hugo   → content/essays/generative-storytelling/index.md           (B.4; 0.4s)
  [✓] pdf    → content/essays/generative-storytelling/generative-storytelling.pdf  (8.2s)
  [✗] word   → pandoc exit 1
              [pandoc stderr snippet, foldable; expand with TAB]

elapsed: 9.1s
2 of 3 backends produced output.
```

Output paths buttonize; stderr blocks fold by default. Re-run failed backend via stock dispatcher (e.g., `C-c C-e o` for Word-only retry — the hooks still apply).

### Customization variables (defcustom)

```elisp
(defcustom a3madkour-pub-multi-templates-dir nil
  "Directory containing `madkour-paper.cls`, `reference.docx`, `d2-blocks.lua`.
Defaults to `<site-root>/tools/templates/` where site-root is resolved via
`a3madkour-pub-essays--site-root` (existing helper).")

(defcustom a3madkour-pub-multi-xelatex-command "xelatex" "")
(defcustom a3madkour-pub-multi-biber-command "biber" "")
(defcustom a3madkour-pub-multi-pandoc-command "pandoc" "")
(defcustom a3madkour-pub-multi-rsvg-convert-command "rsvg-convert" "")
```

`a3madkour-pub-bib-path` (already exists per F.1) is reused. No new bib defcustom. Site-root resolution reuses B.4's existing `a3madkour-pub-essays--site-root` helper — D.2 does not introduce a new env var.

### Process model

Each external-tool invocation runs synchronously inside `multi-pdf/run` or `multi-word/run` (the orchestrator awaits each before moving to the next). Emacs is briefly blocked during xelatex/pandoc runs — but `a3-publish-deliberate` is itself an explicit, deliberate command (matches the "essay publish is a deliberate event" rule). For background async, the user can run individual backends via the stock dispatcher.

### Idempotency + git

Re-running `a3-publish-deliberate` on a multi-export essay overwrites all three outputs in place. PDF + Word artifacts ARE committed. Conversion artifacts in `/tmp/` are never copied to the bundle.

---

## 4. D.1 vocab translation across backends

### Hugo

Unchanged. D.1's `org-hugo-paired-shortcodes` config (in `a3madkour-publish-export.el`) already translates `#+begin_theorem` → `{{< theorem >}}…{{< /theorem >}}`. `#+attr_shortcode: :title T :id thm-ivt` translates to `{{< theorem title="T" id="thm-ivt" >}}`. D.2 changes nothing on this path beyond the visibility-tag filter.

### LaTeX (`madkour-paper.cls`)

`#+begin_theorem` → `\begin{theorem}…\end{theorem}` via ox-latex defaults. The class file enables this:

```latex
\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath, amssymb, amsthm}
\usepackage{microtype, csquotes, hyperref}
\usepackage[backend=biber, style=authoryear]{biblatex}
\usepackage{graphicx, listings}

% theorem-family — shared counter per AMS convention; \theoremstyle{plain} = italic body
\theoremstyle{plain}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{claim}[theorem]{Claim}
\newtheorem{conjecture}{Conjecture}
\newtheorem{axiom}{Axiom}

% definition-style — upright body, bold header
\theoremstyle{definition}
\newtheorem{definition}{Definition}
\newtheorem{example}{Example}

% remark-style — upright body, italic header
\theoremstyle{remark}
\newtheorem{remark}{Remark}
\newtheorem{note}{Note}

% proof — amsthm built-in; auto-appends ∎
```

Note: LaTeX style grouping follows standard AMS convention rather than mirroring D.1's CSS §47 visual tiering exactly. The "full parity" rule from the brainstorm means semantic parity (a theorem is still a theorem across all three targets) with format-appropriate rendering. The Word target's `reference.docx` styles match D.1's §47 visual tiers more directly via paragraph styles (see §4 Word subsection).

Filter expands `#+attr_shortcode: :title T :id thm-ivt` into the equivalent org annotations ox-latex understands:
- `#+attr_latex: :options [T]` → `\begin{theorem}[T]`
- `#+name: thm-ivt` → `\label{thm-ivt}`

Cross-ref `[[#thm-ivt][some text]]` → filter emits `\hyperref[thm-ivt]{some text}` via an explicit `(org-export-data ...)` substitution at the link-filter level for the `latex` backend.

### Word (pandoc + `d2-blocks.lua` + `reference.docx`)

Pandoc-org reads `#+begin_theorem` as a `Div` element with class `theorem`. The Lua filter runs two passes:

**Pass 1 — numbering**: walks all `Div` nodes in document order, mirrors D.1's family-counter logic:

```lua
-- pseudocode
local family_counter = 0
local own_counters = {definition=0, remark=0, example=0, note=0,
                     claim=0, conjecture=0, axiom=0}

function Div(el)
  local kind = el.classes[1]
  local n
  if kind == "theorem" or kind == "lemma" or kind == "corollary" or kind == "proposition" then
    family_counter = family_counter + 1
    n = family_counter
  elseif own_counters[kind] then
    own_counters[kind] = own_counters[kind] + 1
    n = own_counters[kind]
  elseif kind == "proof" then
    n = nil  -- unnumbered per AMS
  else
    return  -- not a D.1 kind; pass through
  end
  el.attributes["d2-num"] = tostring(n or "")
  return el
end
```

**Pass 2 — styling**: for each `Div.<kind>`, prepend a header paragraph (`<Kind> <N>: <Title>` or just `<Kind> <N>.` if no title; just `Proof.` for proof) with the corresponding `reference.docx` named style (`Theorem Header`, `Definition Header`, etc.), wrap body in `<Kind> Body` style. Proof auto-appends `∎` at the end of its last paragraph.

Cross-ref `[[#thm-ivt][some text]]` → pandoc emits `<a href="#thm-ivt">some text</a>`; Word's bookmark machinery resolves at open. No special filter handling needed.

### `reference.docx` style definitions

12 header styles (`Theorem Header`, `Lemma Header`, `Corollary Header`, `Proposition Header`, `Definition Header`, `Proof Header`, `Remark Header`, `Example Header`, `Note Header`, `Claim Header`, `Conjecture Header`, `Axiom Header`) + 12 body styles (`<Kind> Body`).

Three visual tiers matching D.1's CSS §47 treatment:
- **Strong tier** (theorem family + definition): header in bold burgundy, italicized title, indented body in slightly larger font.
- **Soft tier** (remark / example / note / claim / conjecture / axiom): header in semi-bold ink-soft, italicized title, body in standard.
- **Chrome-less** (proof): header in italic "Proof." (no number), body plain, `∎` appended.

Initial styles authored by hand in Word/LibreOffice once; iterated after first end-to-end run rather than perfecting up front. The `reference.docx` is committed to the repo under `tools/templates/`.

---

## 5. Bibliography + asset coordination

### Bibliography

`~/org/bibliography.bib` (defcustom `a3madkour-pub-bib-path`, shipped by F.1) is the canonical bib source for all three backends:

- **Hugo**: F.1's existing `data/citations.yaml` emission + `{{< cite >}}` shortcode.
- **LaTeX**: `\addbibresource{<bib>}` in `madkour-paper.cls`; org-cite + ox-biblatex translates `[cite:@key]` to `\cite{key}` (or `\textcite{}`, `\parencite{}` per `[cite:@key]` variant); biber resolves at compile.
- **Word**: pandoc `--citeproc --bibliography=<bib>` flag; CSL style from `#+csl:` (per-doc) or pandoc's built-in default (Chicago author-date). No D.2 defcustom for CSL — author overrides per-doc when needed.

Cite-key vocabulary is shared — a key valid on the web is valid in PDF and Word. F.1's `check_citations.py` covers all three targets uniformly (a missing key fails consistently across backends).

Citation rendering is **not** enforced to visual parity — the canonical web essay's citation appearance is the primary reader experience; PDF/Word follow their respective conventions (biblatex format / pandoc CSL). Same semantic content, format-appropriate rendering. Mirrors D.1's vocab parity rule.

### Asset pipeline

B.4's existing asset walker (`a3madkour-pub-assets/list-referenced-files <source-file>`) returns the canonical figure list. D.2 backends iterate that list and produce per-backend format conversions into `/tmp/multi-export-<slug>/figures/`:

| Source | Web (Hugo) | PDF (LaTeX) | Word (pandoc) |
|---|---|---|---|
| `figure.svg` | copy as-is (B.4) | `rsvg-convert -f pdf` (D.2 PDF) | `rsvg-convert -f png -d 192` (D.2 Word) |
| `figure.png` | copy as-is (B.4) | copy as-is (D.2 PDF; LaTeX `graphicx` accepts PNG) | copy as-is (D.2 Word) |
| `figure.jpg` | copy as-is (B.4) | copy as-is | copy as-is |

Format conversions in `/tmp/` are consumed by `xelatex`/`pandoc` during their respective runs and discarded. Hugo bundle only contains the SVG source (no conversion artifacts committed).

The asset-ref linter (`tools/check_org_asset_refs.py`, 24th linter pair from A.1.c) **already covers D.2** — same source figures, same validation. No linter extension needed.

---

## 6. Site integration

### `layouts/partials/essay-meta.html` — downloads cluster

Append after the existing series pill block, gated on `.Params.multi_export`:

```html
{{- if .Params.multi_export -}}
  <span class="meta-sep">·</span>
  <span class="essay-downloads" aria-label="Download other formats">
    {{- with .Params.downloads.pdf -}}
      <a href="{{ . | relURL }}" class="download-link download-pdf" download>↓ PDF</a>
    {{- end -}}
    {{- with .Params.downloads.word -}}
      <a href="{{ . | relURL }}" class="download-link download-word" download>↓ Word</a>
    {{- end -}}
  </span>
{{- end -}}
```

Each `<a>` is conditional on its key being present — partial-success cleanly emits only the link it has. The `download` attribute hints save-rather-than-navigate.

The `↓` glyph denotes "download"; consistent with the citation-export slice's existing `↓ BibTeX` etc. vocabulary (CSS §43). Does not violate the no-`→`-arrow rule (different glyph, different semantics).

### CSS extension to `assets/css/main.css`

Append to existing `.essay-meta` rules (no new numbered section):

```css
.essay-downloads {
  display: inline-flex;
  gap: 0.35rem;
}
.download-link {
  font-size: 0.7rem;
  padding: 1px 7px;
  background: transparent;
  color: var(--color-burgundy);
  border: 1px solid var(--color-ink-soft);
  border-radius: 99px;
  text-decoration: none;
  white-space: nowrap;
  line-height: 1.4;
}
.download-link:hover { border-color: var(--color-burgundy); }
```

Reuses existing tokens. `--color-burgundy` on `--color-stone` already clears AAA in the contrast linter; no new pairings.

### Frontmatter contract additions for essays

Two new optional fields:

| Field | Type | Notes |
|---|---|---|
| `multi_export` | bool | Defaults `false` when absent. Existing essays round-trip unchanged. |
| `downloads` | dict | Optional. Keys: `pdf`, `word` (both strings; page-bundle-relative paths). |

### Linter extension (no new pair)

`tools/check_essay_fixtures.py` + `tools/test_check_essay_fixtures.py` grow:

- Accept `multi_export` (bool) + `downloads` (dict with optional `pdf` / `word` string keys).
- If `multi_export: true`, at least one of `downloads.pdf` / `downloads.word` MUST be set. (Both-failed case downgrades to `multi_export: false` per the orchestrator's frontmatter patch rule.)
- If `downloads.pdf` is set, `<slug>.pdf` must exist next to `index.md` in the bundle (filesystem check, mirrors `tools/check_library_covers.py`).
- If `downloads.word` is set, `<slug>.docx` must exist.

**No new linter pair; no CI step bump.** CI step count: 63 → 63.

### Page weight, Pagefind, sitemap

- **Page weight**: PDFs/Word files are bundle assets, not preloaded. `tools/check_page_weights.py` already excludes them (same pattern as essay heroes + audio files). No tier change.
- **Pagefind**: web essay indexed; PDF/Word not (Pagefind is HTML-only).
- **Sitemap**: PDFs/Word not in sitemap (Hugo doesn't serve them as pages).
- **LHCI**: ~50 bytes added to essay pages. No representative-pages impact.

---

## 7. Module layout

### Dotfiles (`~/dotfiles/emacs-configs/custom/lisp/`)

```
a3madkour-publish-multi.el            ; orchestrator + #+multi_export detection + frontmatter patch
a3madkour-publish-multi-test.el

a3madkour-publish-multi-filter.el     ; shared visibility-tag + D.1 vocab translation hooks
a3madkour-publish-multi-filter-test.el

a3madkour-publish-multi-pdf.el        ; ox-latex backend + xelatex/biber + SVG→PDF
a3madkour-publish-multi-pdf-test.el

a3madkour-publish-multi-word.el       ; pandoc org→docx + Lua filter + SVG→PNG
a3madkour-publish-multi-word-test.el
```

Matches B.4/C/F dotfiles convention. `a3-pub.sh` wrapper gains explicit `-l a3madkour-publish-multi` (and submodule loads). Per memory `feedback_plan_wrapper_script_updates`.

### Site repo (`~/Sync/Workspace/a3madkour.github.io/tools/templates/`)

```
madkour-paper.cls                    ; LaTeX class (article + amsthm + biblatex; 12 theorem envs)
reference.docx                       ; Word reference (12 header + 12 body styles)
d2-blocks.lua                        ; pandoc filter (numbering + styling pass)
```

Templates ship in the site repo because they encode the publishing contract.

### Site repo deliverables (non-template)

```
content/essays/example-multi/        ; fixture bundle (B.4 + D.2 emission)
  index.md
  example-multi.pdf
  example-multi.docx
  figures/
    diagram-1.svg
```

Plus the linter extension to `tools/check_essay_fixtures.py` + sibling test.

---

## 8. Testing strategy + fixtures

### Fixture: `~/org/notes/essay-example-multi.org`

Exercises:
- `#+multi_export: t` keyword
- At least one of each visibility tag (`:NOEXPORT_PDF:`, `:NOEXPORT_WEB:`, `:NOEXPORT_WORD:`, `:WEB_ONLY:`, `:PAPER_ONLY:`)
- 4–6 D.1 block kinds (example-five covers all 12; example-multi only needs to exercise the multi-export pathway)
- One `[[#thm-X][text]]` cross-ref
- One `[cite:@key]` against a known `library.bib` entry
- One `[[file:diagram-1.svg]]` SVG figure reference

### Test surface — dotfiles ert (+~25 tests; 481 → ~506)

- **`a3madkour-publish-multi-filter-test.el`** — unit tests for each visibility tag (verify subtree dropped per backend); D.1 vocab translation (apply `#+attr_shortcode:` → verify per-backend annotations).
- **`a3madkour-publish-multi-pdf-test.el`** — unit tests with mocked `rsvg-convert` / `xelatex` / `biber` shell calls; verify command construction, path handling, condition-case error capture.
- **`a3madkour-publish-multi-word-test.el`** — unit tests with mocked `rsvg-convert` / `pandoc`; verify Lua filter path + reference doc + .bib paths passed correctly.
- **`a3madkour-publish-multi-test.el`** — orchestrator dispatch tests; partial-success scenarios (PDF fails / Word fails / both fail / both succeed); frontmatter patch assertions.
- **Integration test** — publish `essay-example-multi.org` end-to-end via `a3-publish-deliberate`. Marked passing only when xelatex + pandoc + rsvg-convert + biber are on PATH; otherwise `(ert-skip "<tool> not found")`. Mirrors the org-math-lint venv check pattern.

### Test surface — site Python

- `tools/test_check_essay_fixtures.py` grows positive + negative cases for `multi_export` + `downloads` (valid pdf-only / valid word-only / valid both / invalid downloads-missing-file / invalid multi_export-true-but-no-downloads-keys).

### CI surface change: zero

CI does NOT run xelatex / pandoc. The committed `.pdf` + `.docx` artifacts are validated via the linter's filesystem-existence check. Authors run the full toolchain locally; CI verifies the contract.

CI step count: 63 → 63. Pre-build linter count: 26 pairs unchanged (essay fixtures extended in-place).

---

## 9. Effort estimate (informal)

| Component | Estimate |
|---|---|
| `a3madkour-publish-multi-filter.el` (visibility + D.1 vocab translation) + tests | 1.5d |
| `madkour-paper.cls` (amsthm + 12 envs + biblatex wiring) | 0.5d |
| `reference.docx` (12 header + 12 body styles) + `d2-blocks.lua` (numbering + styling pass) + tests | 2d (novel piece — Lua filter for stateful numbering is the highest-risk task) |
| `a3madkour-publish-multi-pdf.el` (xelatex orchestration + SVG→PDF) + tests | 1d |
| `a3madkour-publish-multi-word.el` (pandoc orchestration + SVG→PNG) + tests | 0.5d |
| `a3madkour-publish-multi.el` (orchestrator + auto-trigger in deliberate + frontmatter patch) + tests | 0.5d |
| Site-side: essay-meta cluster + CSS + frontmatter contract + linter extension + tests | 0.5d |
| End-to-end fixture (`essay-example-multi.org` + B/D.2 emission verification) | 0.5d |
| Tool-dep probes + error reporting + `*a3madkour-pub*` log extension | 0.5d |
| **Total** | **~7 days focused work** |

Old spec's 4–5d estimate didn't account for D.1 vocab parity (the Lua filter and amsthm declarations weren't on the table); current estimate is realistic.

---

## 10. Risks

- **Pandoc Lua filter numbering pass.** Stateful tree-walk in Lua is well-documented but verbose. The theorem-family counter (lemma/corollary/proposition share with theorem per AMS) needs careful implementation matching D.1's Hugo Scratch logic. Dedicated subagent task with isolated fixtures.
- **amsthm + biblatex interaction.** Both standard packages but can surprise at edge cases (proof environment + footnote citations). Verify in a smoke build before locking the class file.
- **`rsvg-convert` not on PATH on clean macOS install.** Degrades whole multi-export pipeline. Defcustom override + clear error message ("install librsvg via Homebrew") is the mitigation.
- **`reference.docx` style authoring tedious.** First-pass styles via LibreOffice/Word are quick; tuning paragraph spacing + colors to match D.1 web aesthetic takes iteration. Don't perfect up front; ship working styles + iterate post-real-essay.

---

## 11. Phase placement + sequencing

**Phase 3 sub-project D — second slice (D.2).** D.1 (semantic blocks vocabulary) shipped 2026-06-01. After D.2, recommended next sub-project is **E (explorable explainables)** per the existing decomposition.

D.2 depends on:
- **B.4** (essays publisher) — for `a3-publish-deliberate` integration + bundle path resolution + asset walker + frontmatter write-if-different helper.
- **D.1** (semantic blocks) — for the 12-kind vocabulary the LaTeX class + Lua filter render.
- **F** (citation pipeline) — for `a3madkour-pub-bib-path` defcustom + `library.bib` source.
- **A.1.c** (asset linter) — already covers D.2's SVG validation.

D.2 enables:
- Real paper / report writing from the same org sources that produce web essays.
- Future conference-class additions (`acmart`, `IEEEtran`) via author overrides.
- Future `madkour-report.cls` variant (TOC + front-matter) if a real self-distribution trigger arrives.

---

## 12. Forward-compat with explorable explainables (sub-project E)

When sub-project E ships, its runtime will define interactive web blocks (sliders, live code, reactive visualizations). The D.2 pipeline accommodates:

1. Web export proceeds normally; the explorable runtime renders interactive blocks. Until then, blocks fall through as static placeholders (the `widget` shortcode stub pattern from §10 of the parent spec).
2. PDF + Word backends skip explorable blocks (treated as `:NOEXPORT_PDF:` + `:NOEXPORT_WORD:` automatically — the filter recognizes a `:explorable:` tag class).
3. No changes required to `a3madkour-publish-multi*` modules when E ships — E binds to existing DOM hooks emitted by ox-hugo; D.2's filter just gains one more skip rule for the explorable class.

This means: **D.2 ships without explorables**, and E ships later without forcing D.2 to change.

---

**Implementation plan:** drafted via `superpowers:writing-plans` against this spec when the slice is actually scheduled. Per memory `feedback_design_batch_no_plan_until_implement`, the plan waits until implementation begins.
