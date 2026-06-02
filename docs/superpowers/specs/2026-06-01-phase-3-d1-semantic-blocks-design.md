# Phase 3 sub-project D.1 — AMS-style semantic blocks (Hugo-only)

**Status:** design (brainstormed 2026-06-01)
**Parent spec:** `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` (sub-project A — access control + link semantics)
**Sequence:** A → B → F → C → **D.1** → D.2 → E (per [[phase-3-decomposition]])
**Prior slice memories:** [[c-complete]] (math validator shipped 2026-06-01), [[next-slice]] (queued pointer), [[citation-export-slice]] (Hugo shortcode + scratch-counter pattern precedent).

---

## 1 — Goals & non-goals

### Goals

Add an AMS-style **authoring vocabulary** for rigorous prose — `theorem`, `lemma`, `corollary`, `proposition`, `definition`, `proof`, `remark`, `example`, `note`, `claim`, `conjecture`, `axiom` — as new Hugo shortcodes. Render to Hugo only at first; multi-target render (PDF + Word) is D.2's job. The 12 blocks join the existing `sidenote` / `figure` / `spoiler` family.

Decomposition rationale: CLAUDE.md's "D" entry bundles (i) a unified semantic markup vocabulary and (ii) multi-target export. Those are independent subsystems with different shapes — D.1 is mostly small Hugo shortcodes and CSS; D.2 (next slice) is the orchestrator picking up the existing `2026-05-13-multi-target-export-design.md`. Splitting them lets D.1 ship value (rigorous essays become writable) without waiting on the bigger pipeline work.

### In scope

- 12 new Hugo shortcodes in `layouts/shortcodes/` (one per block kind).
- New CSS §47 in `assets/css/main.css` — three-tier visual treatment (strong / soft / chrome-less) using only existing color tokens (`--color-burgundy`, `--color-stone`, `--color-ink-soft`).
- ox-hugo configuration in dotfiles (`org-hugo-special-block-type-properties`) that maps `#+begin_<kind>` org blocks to `{{< <kind> >}}…{{< /<kind> >}}` markdown emission.
- Optional title and cross-reference ID via `#+attr_shortcode: :title <name> :id <slug>` header line above the block. (Both as named args because ox-hugo's paired-shortcode path can't mix positional and named — see §3.2.)
- Numbering: per-essay scratch counters following AMS conventions — `theorem` / `lemma` / `corollary` / `proposition` share one counter (`theorem-family`); each of `definition` / `remark` / `example` / `note` / `claim` / `conjecture` / `axiom` has its own; `proof` is unnumbered.
- New essay fixture `content/essays/example-five/index.md` exercising all 12 block kinds.
- `+1` ert test in B.4 essays handler: round-trip integration that `#+begin_theorem` → `{{< theorem >}}` markdown.
- CLAUDE.md updates — new "Semantic blocks" subsection under "Content & layouts" + linter-pair count remains 25 (no new pair).

### Non-goals

- **Multi-target render (PDF + Word) of these blocks** — D.2. Picks up `docs/superpowers/specs/2026-05-13-multi-target-export-design.md` as the orchestrator spec.
- **Cross-reference auto-formatting** (`{{< ref-block "thm-foo" >}}` → "Theorem 1"). Authors type visible reference text manually: `[[#thm-foo][Theorem 1]]`. Renumber-induced drift is a documented limitation; revisit when the first real essay hits it.
- **Section-prefixed numbering** ("Theorem 3.2"). Per-essay continuous counters only.
- **Custom theorem environments beyond the 12.** Authors who want `principle` or `metatheorem` patch the spec + ship a new shortcode. No registration mechanism.
- **Block-kind Pagefind filter dimension.** Filter chips on theorem-only / definition-only are theoretically possible but premature.
- **New `has_*` frontmatter flag.** CSS §47 loads on every essay page; no opt-in gating.
- **New site-side linter pair** (no 26th pair). The existing CI gates (Hugo build, `check_fixtures.py`, `check_smoke.py`, `check_page_weights.py`, LHCI) cover regressions; a dedicated linter would mostly duplicate Hugo's own build-time validation.
- **KaTeX runtime.** Still in the deferred-features table. Block bodies with `\(...\)` markers render the markers verbatim until KaTeX ships as its own future slice.
- **Math validator extension.** C's chain already covers `\(`, `\[`, `\begin{` in essay bodies regardless of whether they appear inside a theorem or standalone.
- **Explorables / per-page widgets** — sub-project E.

---

## 2 — Module structure

```
~/Sync/Workspace/a3madkour.github.io/
├── layouts/shortcodes/
│   ├── theorem.html       [NEW]
│   ├── lemma.html         [NEW]
│   ├── corollary.html     [NEW]
│   ├── proposition.html   [NEW]
│   ├── definition.html    [NEW]
│   ├── proof.html         [NEW]  ∎ tombstone auto-append
│   ├── remark.html        [NEW]
│   ├── example.html       [NEW]
│   ├── note.html          [NEW]
│   ├── claim.html         [NEW]
│   ├── conjecture.html    [NEW]
│   └── axiom.html         [NEW]
├── assets/css/main.css                              [MOD]  +§47 "Semantic blocks" ~80 LoC
├── content/essays/example-five/index.md             [NEW]  kitchen-sink fixture
├── CLAUDE.md                                        [MOD]  Content & layouts / semantic blocks subsection
└── docs/superpowers/specs/2026-06-01-phase-3-d1-semantic-blocks-design.md  [NEW]

~/dotfiles/
├── emacs-configs/custom/lisp/a3madkour-publish-export.el        [MOD]  set org-hugo-special-block-type-properties
└── emacs-configs/custom/lisp/a3madkour-publish-essays-test.el   [MOD]  +1 round-trip integration ert
```

**Why no new elisp module.** The configuration is a single defcustom assignment — fewer than 30 lines including docstrings. Putting it next to the existing ox-hugo configuration in `a3madkour-publish-export.el` keeps related concerns together. If the configuration grows substantially in D.2 (multi-target adds more emit hooks), promoting it to its own `a3madkour-publish-blocks.el` becomes the natural refactor.

**Why no new Hugo shortcode helper.** Each shortcode is ~10 LoC — the per-kind specialization (counter name, label text) is small enough that duplication beats abstraction. A single generic `{{< block >}}` would save maybe 80 LoC but make source markdown harder to read.

---

## 3 — Source-side contract

### 3.1 Org block syntax

The base shape is an org special block. Title and cross-reference ID are both **optional named arguments via `#+attr_shortcode:`** — see §3.2 below for the why.

```org
#+attr_shortcode: :title Pythagorean :id thm-pythagorean
#+begin_theorem
For any right triangle with legs ~a~, ~b~ and hypotenuse ~c~, ~a^2 + b^2 = c^2~.
#+end_theorem
```

Without title or ID:

```org
#+begin_theorem
The simplest case.
#+end_theorem
```

Title-only:

```org
#+attr_shortcode: :title Continuity
#+begin_definition
A function `f` is continuous at `x₀` if …
#+end_definition
```

### 3.2 Why `#+attr_shortcode:` rather than `:CUSTOM_ID:` + block arg

This was the first plan-of-attack during brainstorming, but a check of ox-hugo's source (`ox-hugo.el` `org-hugo-special-block` ~L3674-3756) showed two constraints:

1. **The block-line argument is ignored in the paired-shortcode emission path.** `#+begin_theorem Pythagorean` would emit `{{< theorem >}}…{{< /theorem >}}` with the "Pythagorean" string dropped. Args come only from `#+attr_shortcode:` headers.
2. **Positional and named `#+attr_shortcode:` args can't mix on a single line.** If any token has a leading colon, ox-hugo parses the whole line as named args; otherwise as positional.

So the cleanest design that supports both an optional title and an optional cross-ref ID is to make **both** named args on a single `#+attr_shortcode:` line. `:CUSTOM_ID:` property drawers on special blocks aren't translated into shortcode args by ox-hugo — they apply to org headings only. Authors who try the heading-style idiom would get a silently dropped ID.

`:CUSTOM_ID:` continues to work as-is for **headings** (used by B.1.1's id-link rewriter — unchanged).

### 3.3 ox-hugo block mapping

Configured in `a3madkour-publish-export.el` via two changes:

```elisp
;; D.1: enable 12 AMS-style block kinds as paired Hugo shortcodes.
(setq org-hugo-paired-shortcodes
      "theorem lemma corollary proposition definition proof remark example note claim conjecture axiom")

;; D.1: trim leading/trailing whitespace around each block in emitted markdown.
(setq org-hugo-special-block-type-properties
      '(("theorem"     :trim-pre t :trim-post t)
        ("lemma"       :trim-pre t :trim-post t)
        ("corollary"   :trim-pre t :trim-post t)
        ("proposition" :trim-pre t :trim-post t)
        ("definition"  :trim-pre t :trim-post t)
        ("proof"       :trim-pre t :trim-post t)
        ("remark"      :trim-pre t :trim-post t)
        ("example"     :trim-pre t :trim-post t)
        ("note"        :trim-pre t :trim-post t)
        ("claim"       :trim-pre t :trim-post t)
        ("conjecture"  :trim-pre t :trim-post t)
        ("axiom"       :trim-pre t :trim-post t)))
```

The first defcustom (`org-hugo-paired-shortcodes`) is what actually drives the shortcode emission — ox-hugo checks the block type against this space-separated list and, when matched, emits `{{< <kind> [args] >}}…{{< /<kind> >}}` instead of the default `<div class="theorem">…</div>`. The second defcustom handles whitespace trimming.

Round-trip:

```
org:                #+attr_shortcode: :title Pythagorean :id thm-pythagorean
                    #+begin_theorem
                    For any right triangle…
                    #+end_theorem

post-export md:     {{< theorem title="Pythagorean" id="thm-pythagorean" >}}
                    For any right triangle…
                    {{< /theorem >}}

no attrs:           {{< theorem >}}
                    For any right triangle…
                    {{< /theorem >}}
```

---

## 4 — Shortcode contract + numbering mechanics

Each shortcode follows a uniform shape. Template skeleton (theorem.html shown; others differ only in counter name and label text):

```go
{{- /* AMS-style block: theorem.
       Numbering shares counter "theorem-family" with lemma/corollary/proposition.
       Optional title + anchor id are both named args (ox-hugo limitation). */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "theorem-family" | default 0)) 1 -}}
{{- $page.Scratch.Set "theorem-family" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-theorem block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Theorem {{ $n }}{{ with $title }} ({{ . }}){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

### 4.1 Counter routing

| Block kind | Counter | Label | CSS tier |
|---|---|---|---|
| `theorem` | `theorem-family` | `Theorem N` | strong |
| `lemma` | `theorem-family` | `Lemma N` | strong |
| `corollary` | `theorem-family` | `Corollary N` | strong |
| `proposition` | `theorem-family` | `Proposition N` | strong |
| `definition` | `definition-counter` | `Definition N` | strong |
| `proof` | — (no counter) | `Proof.` | chrome-less |
| `remark` | `remark-counter` | `Remark N` | soft |
| `example` | `example-counter` | `Example N` | soft |
| `note` | `note-counter` | `Note N` | soft |
| `claim` | `claim-counter` | `Claim N` | soft |
| `conjecture` | `conjecture-counter` | `Conjecture N` | soft |
| `axiom` | `axiom-counter` | `Axiom N` | soft |

Counters are per-page Hugo `$page.Scratch` values. They reset implicitly when Hugo renders the next page (Scratch is page-scoped).

### 4.2 Proof shortcode (special case)

```go
{{- $page := .Page -}}
{{- $of := .Get "of" -}}
{{- $id := .Get "id" -}}
<div class="block-proof"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header"><em>Proof{{ with $of }} of {{ . }}{{ end }}.</em></h4>
  <div class="block-body">{{ .Inner | markdownify }}<span class="proof-tombstone" aria-hidden="true"> ∎</span></div>
</div>
```

No counter. Optional `:of <name>` (named arg) denotes which theorem this proof targets: "Proof of Pythagorean." When absent: bare "Proof." Tombstone `∎` auto-appended at end via the template (not author-typed in body).

Org idiom:

```org
#+attr_shortcode: :of Pythagorean
#+begin_proof
…
#+end_proof
```

### 4.3 Title rendering format

AMS-style with parenthetical when title present:

| State | Output |
|---|---|
| no title | `Theorem 1.` |
| with title | `Theorem 1 (Pythagorean).` |
| proof, no title | `Proof.` (italic) |
| proof, with target | `Proof of Pythagorean.` (italic) |

Title parenthetical renders in `--color-ink-soft` for visual demotion; full color rules in §5.

### 4.4 Anchored block

If the org `#+attr_shortcode: :id thm-foo` was set, the rendered `<div>` carries `id="thm-foo"`. Org `[[#thm-foo][Theorem 1]]` becomes a markdown link `[Theorem 1](#thm-foo)` which Hugo emits as `<a href="#thm-foo">Theorem 1</a>`. The anchor resolves at view time — no shortcode logic needed for cross-ref consumption.

---

## 5 — Visual styling (CSS §47)

New section in `assets/css/main.css`, placed after §46 (streams). Approximately 80 LoC.

### 5.1 Three visual tiers

| Tier | Blocks | Border accent | Body font | Background |
|---|---|---|---|---|
| **Strong** | theorem, lemma, corollary, proposition, definition | 3px solid `--color-burgundy` | regular body | transparent |
| **Soft** | remark, example, note, claim, conjecture, axiom | 2px solid `--color-stone` | regular body | transparent |
| **Chrome-less** | proof | none | italic | transparent |

All tiers share:
- 1rem left padding inside border (where present).
- `margin-block: 1.25rem 1.25rem` vertical rhythm.
- `.block-header` rendered bold at body size (no oversize heading — keeps blocks visually subordinate to essay H3/H4).
- Parenthetical title in `--color-ink-soft`.
- Anchored block (`<div id="…">`) inherits the existing deep-link hover affordance from §11.

### 5.2 Token reuse

No new color tokens. CSS §47 references the existing palette:

- `--color-burgundy` — strong-tier accent (already used for essay accents).
- `--color-stone` — soft-tier accent.
- `--color-ink-soft` — demoted title parenthetical.

Dark-mode pairings already exist for all three; no `tools/check-contrast.py` additions needed (the existing 9 pairings cover these tokens against their stone backgrounds).

### 5.3 Proof tombstone

`.proof-tombstone` floats right-aligned at the end of the last paragraph in `.block-proof > .block-body`, separated by a non-breaking space. `aria-hidden="true"` keeps it out of screen reader announcement (the italic header already conveys "proof").

### 5.4 What is not styled

- No animations or transitions.
- No interactive states (theorem blocks aren't clickable beyond the anchor link).
- No theme-toggle-specific tuning; the existing dark/light token pairings handle both.

---

## 6 — Fixture + test plan

### 6.1 New fixture: `content/essays/example-five/index.md`

Kitchen-sink demonstration — one of each block kind, exercising title+id+no-title branches:

- `definition` with title "Continuity"
- `theorem` with `:title "Intermediate Value" :id thm-ivt` (cross-ref target exercised by a `[[#thm-ivt][Theorem 2]]` link elsewhere in the same essay)
- `proof` (no title; pure tombstone case)
- `lemma`, `corollary`, `proposition` — title-less (exercises theorem-family shared counter)
- `remark`, `example`, `note`, `claim`, `conjecture`, `axiom` — one each, mostly title-less

Frontmatter matches the essay schema (per `check_fixtures.py`). `has_math: true` (block bodies use `\(...\)` markers); `has_citations: false`; rest of `has_*` flags false.

### 6.2 ert delta (dotfiles)

One new integration test in `a3madkour-publish-essays-test.el`:

```
a3madkour-pub-essays-test/special-block-round-trip
  Inserts a `#+begin_theorem` block with `#+attr_shortcode: :title Foo :id thm-foo`,
  runs the export pipeline, asserts post-export markdown contains
  `{{< theorem title="Foo" id="thm-foo" >}}...{{< /theorem >}}`.
```

Total: 480 → 481.

### 6.3 No site-side Python tests

No new linter pair. Existing CI gates handle regressions:

| Gate | Catches |
|---|---|
| `hugo --minify` | Bad Go-template syntax in any new shortcode; unknown shortcode references in markdown bodies |
| `check_fixtures.py` (essay frontmatter linter) | example-five frontmatter conformance |
| `check_smoke.py` | Built pages exist with non-empty bodies |
| `check_page_weights.py` | CSS §47 stays under page-weight budget |
| LHCI desktop + mobile | Perf regression on example-five |
| Author dev-server check | Visual rendering matches §5 |

### 6.4 Edge cases manually verified

After implementation, author walks through:

1. Block with no `#+attr_shortcode:` — minimal case, "Theorem 1." renders.
2. Block with title only — "Theorem 1 (Pythagorean).".
3. Block with title + ID — anchor link from elsewhere in body navigates correctly.
4. Two theorems + a lemma + a corollary — shared counter increments 1, 2, 3, 4.
5. Two definitions — separate counter, each numbered 1, 2.
6. Proof with no title — "Proof." with `∎` tombstone.
7. Proof with target name — "Proof of Pythagorean." with `∎`.
8. Math inside theorem body — `\(\alpha\)` markers survive ox-hugo + Hugo + render correctly (C-validated).
9. Sidenote inside theorem body — sidenote scratch counter independent; sidenote N renders correctly.
10. Cite inside theorem body — `{{< cite >}}` works inside `.Inner | markdownify`.

---

## 7 — CLAUDE.md updates

### 7.1 New "Semantic blocks" subsection

Goes under "Content & layouts" (parallel to "Bento variable-tile grid" and "Filter chips"). Body:

> ### Semantic blocks (AMS-style)
>
> Essays can use 12 AMS-style block shortcodes for rigorous prose: `theorem`, `lemma`, `corollary`, `proposition`, `definition`, `proof`, `remark`, `example`, `note`, `claim`, `conjecture`, `axiom`. Each is a Hugo shortcode in `layouts/shortcodes/` with per-page auto-numbering via `$page.Scratch`.
>
> Authors write `#+begin_theorem` blocks in org, with optional `#+attr_shortcode: :title <name> :id <slug>` header line for title and cross-reference ID. ox-hugo's `org-hugo-paired-shortcodes` config (in `a3madkour-publish-export.el`) emits the matching `{{< theorem title="…" id="…" >}}…{{< /theorem >}}` markdown.
>
> **Numbering follows AMS conventions:** theorem/lemma/corollary/proposition share one counter (`theorem-family`); definition/remark/example/note/claim/conjecture/axiom each have independent counters; proof is unnumbered (auto-appends `∎` tombstone).
>
> **Cross-references** use the block's `#+attr_shortcode: :id <slug>` + org's `[[#id][text]]` link syntax. Visible reference text is author-managed (renumber-induced drift is a documented limitation; auto-formatting is a D.x follow-up). `:CUSTOM_ID:` property drawers continue to work for headings (B.1.1 unchanged) but are silently dropped by ox-hugo on special blocks.
>
> **CSS §47** styles three visual tiers (strong / soft / chrome-less) using existing color tokens. No new `has_*` frontmatter flag — the CSS loads on every essay page.

### 7.2 No count bumps

Linter-pair count stays at 25 (no new linter). CI step count stays at 63 (no new CI step). Hugo shortcode list in the project description grows from 4 named (cite, sidenote, figure, spoiler, plus 4 stubs) to 4 + 12 named = 16 active shortcodes plus the 4 deferred stubs.

---

## 8 — Open questions resolved by user

| Question | Choice | Notes |
|---|---|---|
| Scope (D bundles vocab + multi-target) | D.1 = vocab Hugo-only; D.2 picks up multi-target later | Decomposition during brainstorm |
| Source syntax | `#+begin_<kind>` … `#+end_<kind>` blocks | Standard org custom-block syntax |
| Vocabulary list | Full AMS-style set (12 blocks) | Larger than the recommended core 5 |
| Numbering | AMS-style — theorem family shares; others independent; proof unnumbered | Per-essay reset, no section prefix |
| Title + ID syntax | Both via `#+attr_shortcode: :title <name> :id <slug>` named args | ox-hugo limitation: positional and named attr args can't mix; block-line arg is dropped in paired-shortcode path |
| Cross-reference UX | Plain anchor link, author-typed visible text | Drift on renumber is a documented limitation |
| Render mechanism | 12 Hugo shortcodes (per-kind specialization) | Established pattern from sidenote/figure |

---

## 9 — Failure modes / follow-ups

### Logged for later (D.x)

1. **Cross-reference auto-formatting.** `{{< ref-block "thm-foo" >}}` → "Theorem 1" via per-page lookup. Requires two-pass Hugo build OR carefully ordered scratch population. Trigger: first real essay that hits renumber drift.
2. **Section-prefixed numbering** ("Theorem 3.2"). Trigger: an essay long enough that bare integers become hard to navigate by — author judgment.
3. **Custom block kinds beyond the 12.** Some authors want `principle`, `metatheorem`, `observation`. Trigger: spec request from real usage. Out-of-band patch to spec + new shortcode.
4. **Per-essay numbering reset point** ("reset theorem-family at this H2"). Trigger: long essays where two unrelated arguments share theorem numbering. Same as (2) — author judgment.
5. **Block-kind Pagefind filter dimension** ("show only essays with proofs"). Trigger: ≥3 essays exist with non-trivial theorem content.
6. **D.2 multi-target export.** The blocks ship Hugo-only in D.1; D.2 picks up `2026-05-13-multi-target-export-design.md` and wires ox-latex + pandoc to emit the same vocabulary into PDF + Word. Each shortcode kind gets a matching LaTeX env / Word style.

### Not on the follow-up list

- Theorem-kind-specific JS interaction (collapse / expand / hover-preview). Out: pure-CSS treatment is sufficient.
- Site-wide theorem index / list-all-theorems page. Out: not in the original CLAUDE.md scope; speculative.
- Special handling for `\begin{align}` inside a theorem body. Math is independent — block bodies pass through `markdownify`; math markers survive to the eventual KaTeX renderer.

---

## 10 — Commit shape

Expected commits (subagent-driven plan will lay these out in detail):

**Site (5-6 commits):**
1. `feat(d-1): 12 AMS-style semantic-block shortcodes`
2. `feat(d-1): CSS §47 — semantic block styling (three-tier visual treatment)`
3. `chore(d-1): example-five fixture exercises all 12 blocks + numbering`
4. `docs(d-1): CLAUDE.md — semantic blocks subsection under Content & layouts`

**Dotfiles (2 commits):**
5. `feat(d-1): ox-hugo special-block mappings for 12 AMS shortcodes`
6. `test(d-1): essays handler round-trip for theorem block emission`

Total: ~6-7 commits, smaller than C (14 commits). Mostly CSS + small Hugo templates + a dotfiles defcustom; no new modules, no new validators.

---

## 11 — Sequencing context

Per parent decomposition [[phase-3-decomposition]]:

| Slice | Status |
|---|---|
| A — Access control + link semantics | shipped 2026-05-24 |
| B — Per-content-type publishers | shipped 2026-05-25 → 2026-05-31 |
| F — Citation pipeline | shipped 2026-06-01 |
| C — Math validator | shipped 2026-06-01 |
| **D.1 — Semantic blocks (Hugo-only)** | **this spec — designed 2026-06-01** |
| D.2 — Multi-target export (Hugo + PDF + Word) | queued; picks up `2026-05-13-multi-target-export-design.md` |
| E — Explorables / per-page widgets | queued; independent of D.x |

D.1 has **no dependencies** beyond what's already shipped. Math, citations, sidenotes, figures are all reused as-is; the only new wire is the ox-hugo defcustom in `a3madkour-publish-export.el`. D.2 explicitly waits for D.1 — multi-target wants the same vocabulary across all three targets.
