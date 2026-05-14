# Multi-target literate export pipeline — design

**Phase:** Phase 3 Slice 3 — extends the standard essay-publish command with multi-target dispatch.
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §14 Phase 3.
**Origin:** `~/org/projects.org` TODO captured 2026-04-14 ("Set up templates to export big literate org documents to both doc and technical report for pdf/paper/interactive article").

Take one literate org document and publish it to three targets in one Emacs interactive command: a Hugo essay (the interactive web article), a PDF technical report (academic paper or self-distribution), and a Word document (collaboration round-trip or forced-conversion submission). All three derive from the same org source via per-target visibility tags; the orchestrator dispatches to ox-hugo + ox-latex + pandoc, runs the external tools (xelatex, biber, rsvg-convert, pandoc), and lands PDF + Word as page-bundle assets alongside the Hugo essay markdown.

Site-side change is small: an existing essay opts in via `multi_export: true` frontmatter, the essay-meta row gains a small `↓ PDF / ↓ Word` cluster next to the Cite-this-page link from Feature 1. All other essay UX is unchanged.

**Explorable explainables** (interactive web articles with sliders, live code, reactive visualizations) are explicitly out of scope here — see §10. That capability composes cleanly with this pipeline when its own spec ships.

---

## 1. Scope

**The pipeline produces three artifacts from one org source:**
1. **Hugo essay** — interactive web article published at `/essays/<slug>/`. Existing essay format; uses existing `widget`, `figure`, `cite`, `sidenote` shortcodes when present in the source.
2. **PDF technical report** — academic paper submission (per `#+latex_class:` override like `acmart`) OR self-distribution report (default `madkour-paper` / `madkour-report` classes). Same source supports both via per-doc class selection.
3. **Word document** — collaboration round-trip (collaborator edits return manually) OR forced-conversion (some portals require .docx).

**Authoring stays inside Emacs.** One interactive command runs all three backends. Selective rebuild commands exist for fast iteration on individual outputs.

**Out of scope** (see §10): explorable explainables, CI-side PDF builds, automatic Word round-trip back into org, arXiv/OSF auto-submission.

---

## 2. Authoring contract

### Opt-in keyword

At the top of the org file:

```org
#+multi_export: t
```

Without this keyword the document goes through the standard essay-publish path (single output: Hugo essay). With it, the literate pipeline activates and produces all three.

### Per-doc backend configuration

All standard org keywords plus one custom (`#+word_reference:`):

```org
#+title:                Generative Storytelling in Procedural Worlds
#+date:                 2026-05-13
#+author:               Abdelrahman Madkour
#+multi_export:         t
#+latex_class:          madkour-paper                       # ships with project
#+latex_class_options:  [acmsmall,review,anonymous]         # passed to \documentclass
#+word_reference:       tools/templates/reference.docx      # project default
#+bibliography:         ~/org/bibliography.bib              # optional override; default per defcustom
#+filetags:             :essay:
#+export_file_name:     generative-storytelling             # optional; otherwise slugified title
```

**Class fallback:** if `#+latex_class:` is missing, the orchestrator defaults to `madkour-paper`. Conference submissions override with the venue's class (`acmart`, `IEEEtran`, etc.) — the orchestrator copies the class file to the temp build directory or relies on the system TeXLive installation.

### Per-target visibility tags

Custom tag convention applied by `filters/visibility-tags.el` before each backend export:

| Tag | Behavior |
|---|---|
| `:NOEXPORT_PDF:` | Skip this subtree during PDF export |
| `:NOEXPORT_WEB:` | Skip during Hugo/web export |
| `:NOEXPORT_WORD:` | Skip during Word export |
| `:WEB_ONLY:` | Shorthand for `:NOEXPORT_PDF:` + `:NOEXPORT_WORD:` |
| `:PAPER_ONLY:` | Shorthand for `:NOEXPORT_WEB:` + `:NOEXPORT_WORD:` |
| `:noexport:` (standard org) | Skip everywhere — already supported by ox-hugo |

Tags inherit down the tree per org's standard behavior.

**Example:**

```org
* Abstract                                        :NOEXPORT_WEB:
The paper abstract — web essay uses #+summary frontmatter instead.

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

### Inherited conventions (standard org; this spec does not change them)

- **Figures**: same source SVG/PNG with `#+attr_latex:` / `#+attr_html:` per-backend attributes. SVG → SVG for web; SVG → PDF (via `rsvg-convert`) for LaTeX; SVG → PNG (via `rsvg-convert`) embedded for Word.
- **Code blocks**: `:exports {code, results, both, none}` per block. Same setting applies across all backends.
- **Citations**: `org-cite` `[cite:@key]` references. Bibliography from `~/org/bibliography.bib` or per-doc `#+bibliography:`. Web → existing `cite` shortcode; PDF → biblatex; Word → pandoc citeproc.

### Asset placement

Hugo essay bundle layout (post-export):

```
content/essays/<slug>/
  index.md                              # Hugo essay (from ox-hugo)
  <slug>.pdf                            # PDF tech report
  <slug>.docx                           # Word document
  figures/
    figure-1.svg                        # web source
    figure-1.pdf                        # rsvg-converted for LaTeX (built artifact; gitignored)
    figure-1.png                        # rsvg-converted for Word (built artifact; gitignored)
```

PDF/Word artifacts ARE committed (small, infrequent, part of the publishable bundle). Intermediate format-conversion artifacts (`.pdf` / `.png` of figures already source-controlled as `.svg`) are gitignored.

### Auto-injected Hugo frontmatter

After successful export, the orchestrator patches the Hugo essay markdown's frontmatter:

```yaml
multi_export: true
downloads:
  pdf:  "generative-storytelling.pdf"
  word: "generative-storytelling.docx"
```

`downloads` keys are conditionally written — if PDF export fails, the `pdf:` key is omitted (clean degradation; the essay still publishes with whatever backends succeeded).

---

## 3. Pipeline orchestrator

### File layout (in this repo)

```
tools/elisp/
  madkour-literate.el                # main entrypoint — interactive commands + defcustom
  exporters/
    web.el                            # ox-hugo backend + frontmatter patch
    pdf.el                            # ox-latex + xelatex + biber orchestration
    word.el                           # pandoc org → docx
  filters/
    visibility-tags.el                # per-target tag filter

tools/templates/
  madkour-paper.cls                   # generic article LaTeX class (default)
  madkour-report.cls                  # front-matter + TOC variant
  reference.docx                      # pandoc Word reference template

tools/elisp/README.md                 # install + first-run instructions
```

Templates + elisp live in the site repo (versioned alongside the contract they implement). User's personal config does `(add-to-list 'load-path "<site>/tools/elisp")` + `(require 'madkour-literate)` to wire up the commands.

### Interactive commands

```elisp
M-x madkour/publish-literate-essay          ; all three backends (the daily-driver command)
M-x madkour/publish-literate-web-only       ; selective rebuild
M-x madkour/publish-literate-pdf-only       ; fast PDF iteration during paper polish
M-x madkour/publish-literate-word-only      ; selective rebuild
```

The full command runs each backend in sequence; each is wrapped in `condition-case` so a failure in one doesn't abort the others.

### Per-backend flow

**`exporters/web.el`**:
1. Apply visibility filter (skip `:NOEXPORT_WEB:` / `:PAPER_ONLY:`).
2. Run ox-hugo export.
3. Resolve output slug from `#+export_file_name:` or slugified `#+title:`.
4. Read the produced `<slug>/index.md`, patch frontmatter: add `multi_export: true` + `downloads:` block populated with paths to whichever sibling outputs exist on disk.
5. Copy SVG figures into `content/essays/<slug>/figures/`.

**`exporters/pdf.el`**:
1. Apply visibility filter (skip `:NOEXPORT_PDF:` / `:WEB_ONLY:`).
2. Run ox-latex export to `/tmp/<slug>.tex`.
3. Convert each SVG figure to `.pdf` via `rsvg-convert` (the `graphicx` package can't `\includegraphics` SVG directly).
4. Run `xelatex` → `biber` → `xelatex` → `xelatex` (standard 4-pass dance for cross-refs + bibliography).
5. Copy `<slug>.pdf` into `content/essays/<slug>/`.

**`exporters/word.el`**:
1. Apply visibility filter (skip `:NOEXPORT_WORD:` / `:WEB_ONLY:` / `:PAPER_ONLY:`).
2. Write filtered org buffer to `/tmp/<slug>-filtered.org` (pandoc doesn't see Emacs export filters, so we serialize the filtered tree to disk before invoking pandoc).
3. Run `pandoc -f org -t docx --reference-doc=<reference.docx> --citeproc --bibliography=<bib> /tmp/<slug>-filtered.org -o /tmp/<slug>.docx`.
4. Copy `<slug>.docx` into `content/essays/<slug>/`.

### External tool dependencies

| Tool | Required for | Install hint |
|---|---|---|
| `xelatex` (TeXLive ≥ 2022 / MacTeX) | PDF backend | `pacman -S texlive-xetex` / `brew install --cask mactex` |
| `biber` | PDF citations (biblatex) | Bundled with TeXLive |
| `rsvg-convert` (librsvg) | SVG → PDF + SVG → PNG | `pacman -S librsvg` / `brew install librsvg` |
| `pandoc` ≥ 3.x | Word backend | `pacman -S pandoc` / `brew install pandoc` |

The orchestrator checks for each tool's presence at first run; missing tools result in a clear error message in `*literate-export*` pointing at the install command for the user's OS (or a generic "consult your package manager" fallback).

### Customization variables (defcustom)

```elisp
(defcustom madkour-site-root "~/Workspace/a3madkour.github.io"
  "Root of the Hugo site repo.")
(defcustom madkour-essays-dir "content/essays")
(defcustom madkour-templates-dir "tools/templates")
(defcustom madkour-bibliography "~/org/bibliography.bib")
(defcustom madkour-xelatex-command "xelatex")
(defcustom madkour-pandoc-command "pandoc")
(defcustom madkour-rsvg-convert-command "rsvg-convert")
(defcustom madkour-biber-command "biber")
```

User overrides any of these in their personal init.el. Reasonable defaults work for a typical setup.

### Process model

Each backend's external-tool invocation runs in an `async-shell-command` wrapped inside an elisp coordinator. The orchestrator awaits all three backends via process sentinels, then writes the final summary buffer. Emacs stays responsive; the author can keep editing the org buffer (Emacs uses the current buffer state at the moment the export starts, not whatever the buffer looks like when the external tools finish).

### Error reporting — `*literate-export*` buffer

Dedicated buffer (re-used across runs; cleared at start). Format:

```
literate export — Generative Storytelling in Procedural Worlds
started: 2026-05-13T22:15:00-04:00
slug:    generative-storytelling

  [✓] web    → content/essays/generative-storytelling/index.md           (0.4s)
  [✓] pdf    → content/essays/generative-storytelling/generative-storytelling.pdf  (8.2s)
  [✗] word   → pandoc exit 1
              pandoc: error converting org → docx
              [pandoc stderr snippet, foldable; expand with TAB]

elapsed: 9.1s
2 of 3 backends succeeded.

Output (RET to open):
  - content/essays/generative-storytelling/index.md
  - content/essays/generative-storytelling/generative-storytelling.pdf

Re-run failed backend:
  M-x madkour/publish-literate-word-only
```

Output paths are buttonized; stderr blocks fold to one line by default.

### Idempotency + git

Re-running on a previously-exported literate doc overwrites all three outputs in place. The orchestrator does NOT auto-commit — matches the parent spec's "essay publish is a deliberate publishing event" rule. User reviews diffs in their git client and commits manually.

### LaTeX class details

**`madkour-paper.cls`** — thin wrapper over `article.cls`. Provides:
- Default margins / fonts matching academic norms
- Common `\usepackage{}` imports: `graphicx`, `hyperref`, `biblatex` (backend=biber), `listings`, `microtype`, `csquotes`
- `\maketitle` that handles `\author{}` + optional `\affil{}`
- A no-op `\noexport{...}` macro so the elisp filter handles per-target before LaTeX sees anything

Author overrides via `#+latex_class:` per-doc for actual conference submissions (`acmart`, `IEEEtran`, etc.).

**`madkour-report.cls`** — adds:
- TOC generation
- Front matter pages (abstract page, table of contents, list of figures)
- Chapter-style numbering for longer documents

### Word reference template

**`tools/templates/reference.docx`** — Word document carrying style definitions only (no body content). pandoc reads it and applies its styles (headings, body, quote, code) to the converted document. Author edits Word styles directly in `reference.docx` to evolve the visual identity. Per-doc override via `#+word_reference: <path>`.

### Visibility-tag filter implementation

`filters/visibility-tags.el` registers as `org-export-filter-headline-functions` (or equivalent hook). Examines `org-export-current-backend` and the headline's tags:

- For `hugo` / `md` backend: drop headlines with `:NOEXPORT_WEB:` or `:PAPER_ONLY:` (web-side filter).
- For `latex` backend: drop `:NOEXPORT_PDF:` or `:WEB_ONLY:` (PDF-side filter).
- For pandoc-via-buffer-serialization: filter applied in elisp BEFORE writing `/tmp/<slug>-filtered.org` (so pandoc sees an already-filtered tree).

---

## 4. Site integration

### Hugo essay template change — `layouts/partials/essay-meta.html`

The downloads cluster slots into the existing meta row alongside the "Cite this page" link from Feature 1:

```hugo
<p class="essay-meta">
  <time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date.Format "2 January 2006" }}</time>
  <span class="meta-sep">·</span>
  <span class="meta-reading-time">{{ .ReadingTime }} min</span>
  {{ with .Params.tags }}…{{ end }}
  {{ with .Params.series }}…{{ end }}
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
  {{- /* Feature 1's cite-page-link continues here when shipped */ -}}
</p>
```

Cluster appears only when `multi_export: true`. Each `<a>` is conditional on its key being present in the `downloads` dict — failed backends gracefully omit their link.

### CSS — small additions to existing essay-meta block

Append to the existing `.essay-meta` rules in `assets/css/main.css`:

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
}
.download-link:hover { border-color: var(--color-burgundy); }
```

Reuses existing tokens. No new section number — extends the existing essay-meta style block.

### Frontmatter contract additions for essays

Two new optional fields (no required-field changes):

| Field | Type | Notes |
|---|---|---|
| `multi_export` | bool | Defaults to `false` when absent. Existing essays round-trip unchanged. |
| `downloads` | dict | Optional. Keys: `pdf`, `word` (both strings; page-bundle-relative paths). |

### Existing essay linter extension

`tools/check_essay_fixtures.py` + sibling `test_check_essay_fixtures.py`:

- Accept `multi_export` (bool) + `downloads` (dict with optional `pdf` / `word` string keys).
- If `multi_export: true`, at least one of `downloads.pdf` or `downloads.word` must be set.
- If `downloads.pdf` is set, the file must exist next to `index.md` in the page bundle. (Filesystem check — same pattern as `tools/check_library_covers.py` uses for cover files.)
- If `downloads.word` is set, same filesystem check.

**No new linter pair.** Extension to an existing one. CI step count unchanged.

### Page weight

PDFs and Word files sit in the bundle directory but aren't fetched at page load (downloads are user-initiated). `tools/check_page_weights.py` already excludes non-preloaded bundle assets (matches how essay heroes + audio files are handled). **No tier change needed.**

### Pagefind

Web essay indexed normally. PDF / Word not indexed — Pagefind is HTML-only. The on-site web essay is what readers find via search; the downloads are for after they're already on the page.

### Citation export integration (Feature 1 alignment)

No special handling required. Multi-export essays cite the same way as any essay — the canonical citation points to the web essay URL. Authors who publish the paper version through a venue produce a separate bib entry for that venue's publication (with its own DOI, venue name, etc.) — that's outside this spec.

---

## 5. Phase placement + sequencing

### Phase 3 territory

**This is Phase 3 Slice 3.** Sequence within Phase 3:

1. **Phase 3 Slice 1** — standard garden / library / research publish command (frequent + idempotent).
2. **Phase 3 Slice 2** — standard essay publish command (per-post + deliberate).
3. **Phase 3 Slice 3 (this spec)** — literate essay publish; extends Slice 2 with multi-target dispatch + filters + LaTeX/pandoc orchestration.

**Hard dependency on Slice 2.** Slice 3 reuses Slice 2's slug resolution, frontmatter patching, and bundle-path conventions. Build Slice 2 first; Slice 3 extends.

### Effort estimate (informal)

| Component | Estimate |
|---|---|
| `tools/elisp/madkour-literate.el` + 3 backend modules + visibility-tag filter | ~2 days |
| `madkour-paper.cls` + `madkour-report.cls` + `reference.docx` (initial style passes) | ~1 day |
| Hugo template + CSS additions + essay linter extension + tests | ~0.5 day |
| First-run integration testing across the three backends + external tool error paths | ~1 day |
| **Total** | **~4–5 days of focused work** |

The original org TODO tagged 2h was wildly optimistic; the realistic estimate matches what writing the LaTeX class + tuning the Word reference doc actually demands.

### Sequencing across the brainstorm batch

This is the **only feature in the batch that's not independent** of Phase 3. Recommended overall order across the 4 feature specs:

1. Phase 8 close-out (still open).
2. **Feature 1** (citation export) — standalone polish.
3. **Feature 3** (time-synced poetry) — standalone works/poetry runtime.
4. Phase 3 Slice 1 (garden/library/research publish) — when the user's elisp work is ready.
5. Phase 3 Slice 2 (standard essay publish).
6. **Feature 2 — this spec** (Phase 3 Slice 3 — literate essay publish).
7. **Feature 4** (streams section) — has a soft dependency on Feature 1; independent of Phase 3.

Features 1, 3, 4 are independent and can land in any order. This spec waits for Phase 3 Slices 1 + 2.

---

## 6. Out of scope (deferred, with explicit forward-compat where relevant)

| Capability | Reason | Future trigger |
|---|---|---|
| **Explorable explainables** — interactive web articles with sliders, live code, reactive visualizations | Different problem, different infra, different maturity timeline. The existing `widget` shortcode stub + `has_widgets` essay flag are pre-work for that future spec. Composes cleanly with this pipeline when both ship (see §7 below). | Separate brainstorm + spec |
| Auto-submit PDF to arXiv / OSF | External submission infrastructure; out of personal-site scope | Manual upload is fine |
| Round-trip Word edits back into org | Pandoc docx → org is lossy; manual integration preferred. Collaborators' Word edits get manually merged into the org master. | If user finds the workflow worth automating |
| LaTeX class auto-selection from conference target | Per-doc `#+latex_class:` override is enough | n/a |
| Multi-language (RTL, Arabic) PDF support | Gated on real Arabic content + author need | Phase 3 follow-up |
| Code-execution during export (live notebook style) | Out of scope; explorables is the right home for this | Explorables spec |
| CI-side export (build PDF in GitHub Actions) | Author-machine export is sufficient; CI doesn't need the LaTeX toolchain | If desired later (heavy CI investment) |
| BibTeX `note` field marker for "literate doc" | Info not useful in citations | n/a |
| Auto-versioning of PDFs (e.g., `<slug>-v2.pdf`) | Author can do this manually if needed | Author preference |
| Pre-commit hook validating the export contract | Future polish | If failed exports become a recurring footgun |

---

## 7. Forward-compatibility hook for explorable explainables

When the explorable-explainables spec ships, it will define:
- A real runtime (TBD by that spec — Idyll / Observable / vanilla / Lit)
- Org authoring for `#+begin_explorable` blocks (or similar)
- Cross-format degradation: explorable blocks become static screenshots + a "View interactive version at `<URL>`" caption in PDF and Word

**This pipeline's contract for that future:**

1. If `#+explorable: t` appears in a `#+multi_export: t` org doc:
   - Web export proceeds normally; the explorable runtime (when built) renders the interactive blocks. Until then, blocks fall through as static placeholders (existing `widget` shortcode stub pattern).
   - PDF + Word exports skip explorable blocks (treated as `:NOEXPORT_PDF:` + `:NOEXPORT_WORD:` automatically).
2. The orchestrator's `web.el` doesn't need to change to support explorables — the runtime ships independently and binds to existing DOM hooks emitted by ox-hugo.
3. The orchestrator's `pdf.el` + `word.el` add one filter rule: skip blocks tagged `:explorable:` (since they have no static rendering yet beyond the screenshot fallback that the explorables spec will define).

This means: **this spec ships without explorables**, and the explorables spec ships later without forcing this pipeline to change.

---

**Implementation plan:** drafted only when the slice is actually scheduled (per the user's preference of "design now, implement per-slice later"). When that happens — and Phase 3 Slices 1 + 2 have shipped — invoke `superpowers:writing-plans` against this spec.
