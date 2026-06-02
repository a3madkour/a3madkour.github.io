# Phase 3 D.1 — semantic blocks implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 12 AMS-style semantic-block shortcodes (`theorem`, `lemma`, `corollary`, `proposition`, `definition`, `proof`, `remark`, `example`, `note`, `claim`, `conjecture`, `axiom`) to the Hugo site, with three-tier visual styling in CSS §47, an end-to-end fixture exercising all 12 blocks plus cross-ref, and the ox-hugo config that drives `#+begin_<kind>` blocks to emit as paired Hugo shortcodes.

**Architecture:** Each shortcode follows the established `sidenote.html` pattern — `$page.Scratch` counter, `.Inner | markdownify`, semantic `<div>` wrapper with class hooks. The theorem-family (theorem/lemma/corollary/proposition) shares one counter; each other counted kind has its own; proof is unnumbered (auto-appends ∎ tombstone). CSS §47 styles three tiers (strong / soft / chrome-less) using only existing color tokens. ox-hugo emission is driven by setting `org-hugo-paired-shortcodes` in `a3madkour-publish-export.el`.

**Tech Stack:** Hugo Go templates (12 small files, ~10 LoC each), hand-rolled CSS (~80 LoC §47), Emacs Lisp (one defcustom assignment + 1 ert integration test), Python stdlib (existing `check_fixtures.py` validates example-five frontmatter — no new tooling).

**Spec:** `docs/superpowers/specs/2026-06-01-phase-3-d1-semantic-blocks-design.md`

**Working directories:**
- Site: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/`
- Dotfiles: `/Users/a3madkour/dotfiles/`

**Test commands (used throughout):**
- Site Python tests: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -5`
- Site smoke (essay frontmatter linter against real fixtures): `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_fixtures.py`
- Hugo prod build: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && hugo --minify 2>&1 | tail -10`
- Dotfiles ert: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -20`

**Baseline counts before D.1:** 480 ert (post-C per [[c-complete]]) + 25 linter pairs + 1 sibling-less linter. Total CI step count: 63.
**Targets after D.1:** 481 ert (+1 round-trip test) + 25 linter pairs (unchanged) + 1 sibling-less linter (unchanged). CI step count: 63 (unchanged).

**Dotfiles repo discipline (IMPORTANT — applies to every dotfiles task):** There are 5 pre-existing dirty tracked files in `~/dotfiles/` that are the author's in-progress local work: `.gitignore`, `.zshrc`, `emacs-configs/custom/bookmarks`, `emacs-configs/custom/early-init.el`, `emacs-configs/custom/init.el`. **NEVER stage or commit these.** Use `git add <specific files>` (the ones in the task), NOT `git add -A` or `git add .`.

---

## Task 1 — example-five frontmatter stub (passes check_fixtures.py)

**Files:**
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-five/index.md`

The fixture starts as a frontmatter-only stub. The full body (with all 12 blocks) goes in Task 4 — splitting it lets the shortcodes ship in Task 2 before the fixture exercises them.

- [ ] **Step 1: Create the fixture file with minimal valid frontmatter**

```bash
mkdir -p /Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-five
```

Write the file `content/essays/example-five/index.md`:

```markdown
---
date: 2026-06-01
draft: false
has_citations: false
has_footnotes: false
has_math: true
has_sidenotes: false
has_video_sync: false
has_widgets: false
lastmod: 2026-06-01
series: ""
series_order: 0
summary: "Lorem ipsum — AMS-style block kitchen sink for D.1."
tags: []
title: "Example Five"
toc: true
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
```

`has_math: true` is set up front so the C math-coupling linter passes once Task 4 inserts actual LaTeX markers. Body is placeholder prose until Task 4.

- [ ] **Step 2: Run check_fixtures.py to verify the frontmatter validates**

Run:
```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_fixtures.py 2>&1 | tail -5
```

Expected: `OK — N essay fixtures validate.` (no errors). N goes up by 1 from the previous run.

- [ ] **Step 3: Run check_math.py — should pass (has_math: true with no markers yet would fail; but task body line is plain prose so coupling check sees no markers AND has_math: true → ERROR)**

Wait, run it and see — this is a known intermediate state:

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_math.py
```

Expected: `1 math coupling issue(s).` with error mentioning `example-five` — has_math: true but no markers in body yet. This is OK between Task 1 and Task 4; Task 4 adds the math markers.

**If you stop here mid-slice, the linter would fail. Don't commit Task 1 alone in production CI; this task only exists to let Tasks 2-3 be visually verifiable against an essay page that exists. Task 4 closes the linter gap.**

- [ ] **Step 4: Sibling unit tests still pass**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -3
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add content/essays/example-five/index.md
git commit -m "$(cat <<'EOF'
chore(d-1): example-five frontmatter stub for AMS blocks fixture

Body filled in Task 4 (after Tasks 2-3 ship the shortcodes + CSS).
has_math: true is set up front to match the eventual body content;
between this commit and Task 4 the math coupling linter fails on
example-five — intentional intermediate state.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2 — 12 semantic-block Hugo shortcodes

**Files:**
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/theorem.html`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/lemma.html`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/corollary.html`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/proposition.html`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/definition.html`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/proof.html`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/remark.html`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/example.html`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/note.html`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/claim.html`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/conjecture.html`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/axiom.html`

12 small Go-template files, ~10 LoC each. Counter routing per spec §4.1:

| Block | Counter | Label | CSS tier classes |
|---|---|---|---|
| theorem | `theorem-family` | `Theorem N` | `block-theorem block-strong` |
| lemma | `theorem-family` | `Lemma N` | `block-lemma block-strong` |
| corollary | `theorem-family` | `Corollary N` | `block-corollary block-strong` |
| proposition | `theorem-family` | `Proposition N` | `block-proposition block-strong` |
| definition | `definition-counter` | `Definition N` | `block-definition block-strong` |
| proof | — | `Proof` (special) | `block-proof` (chrome-less) |
| remark | `remark-counter` | `Remark N` | `block-remark block-soft` |
| example | `example-counter` | `Example N` | `block-example block-soft` |
| note | `note-counter` | `Note N` | `block-note block-soft` |
| claim | `claim-counter` | `Claim N` | `block-claim block-soft` |
| conjecture | `conjecture-counter` | `Conjecture N` | `block-conjecture block-soft` |
| axiom | `axiom-counter` | `Axiom N` | `block-axiom block-soft` |

- [ ] **Step 1: Write the theorem-family + definition shortcodes (5 files, share the same shape)**

Write `layouts/shortcodes/theorem.html`:

```go
{{- /* AMS-style block: theorem.
       Numbering shares counter "theorem-family" with lemma/corollary/proposition.
       Optional title + anchor id are both named args (ox-hugo limitation; see spec §3.2). */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "theorem-family" | default 0)) 1 -}}
{{- $page.Scratch.Set "theorem-family" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-theorem block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Theorem {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

Write `layouts/shortcodes/lemma.html` (same shape; counter unchanged, label changes):

```go
{{- /* AMS-style block: lemma. Shares "theorem-family" counter. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "theorem-family" | default 0)) 1 -}}
{{- $page.Scratch.Set "theorem-family" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-lemma block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Lemma {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

Write `layouts/shortcodes/corollary.html`:

```go
{{- /* AMS-style block: corollary. Shares "theorem-family" counter. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "theorem-family" | default 0)) 1 -}}
{{- $page.Scratch.Set "theorem-family" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-corollary block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Corollary {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

Write `layouts/shortcodes/proposition.html`:

```go
{{- /* AMS-style block: proposition. Shares "theorem-family" counter. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "theorem-family" | default 0)) 1 -}}
{{- $page.Scratch.Set "theorem-family" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-proposition block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Proposition {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

Write `layouts/shortcodes/definition.html` (separate counter, but still strong tier):

```go
{{- /* AMS-style block: definition. Own counter; strong tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "definition-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "definition-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-definition block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Definition {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 2: Write the proof shortcode (chrome-less, no counter, tombstone)**

Write `layouts/shortcodes/proof.html`:

```go
{{- /* AMS-style block: proof. No counter. Optional :of <name> denotes target theorem.
       Auto-appends ∎ tombstone via .proof-tombstone span. */ -}}
{{- $page := .Page -}}
{{- $of := .Get "of" -}}
{{- $id := .Get "id" -}}
<div class="block-proof"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header"><em>Proof{{ with $of }} of <span class="block-title">{{ . }}</span>{{ end }}.</em></h4>
  <div class="block-body">{{ .Inner | markdownify }}<span class="proof-tombstone" aria-hidden="true"> ∎</span></div>
</div>
```

- [ ] **Step 3: Write the 6 soft-tier shortcodes (remark, example, note, claim, conjecture, axiom — each with its own counter)**

Write `layouts/shortcodes/remark.html`:

```go
{{- /* AMS-style block: remark. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "remark-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "remark-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-remark block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Remark {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

Write `layouts/shortcodes/example.html`:

```go
{{- /* AMS-style block: example. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "example-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "example-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-example block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Example {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

Write `layouts/shortcodes/note.html`:

```go
{{- /* AMS-style block: note. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "note-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "note-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-note block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Note {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

Write `layouts/shortcodes/claim.html`:

```go
{{- /* AMS-style block: claim. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "claim-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "claim-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-claim block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Claim {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

Write `layouts/shortcodes/conjecture.html`:

```go
{{- /* AMS-style block: conjecture. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "conjecture-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "conjecture-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-conjecture block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Conjecture {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

Write `layouts/shortcodes/axiom.html`:

```go
{{- /* AMS-style block: axiom. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "axiom-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "axiom-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-axiom block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Axiom {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 4: Verify Hugo parses all 12 templates without error**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && hugo --minify 2>&1 | tail -15
```

Expected: build completes successfully (no "template not found" or "parse error" lines). example-five renders as a normal essay page (no blocks yet — Task 4 inserts them).

If Hugo build fails with a parse error in one of the new shortcodes, fix the syntax in that template, re-run.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add layouts/shortcodes/theorem.html layouts/shortcodes/lemma.html layouts/shortcodes/corollary.html layouts/shortcodes/proposition.html layouts/shortcodes/definition.html layouts/shortcodes/proof.html layouts/shortcodes/remark.html layouts/shortcodes/example.html layouts/shortcodes/note.html layouts/shortcodes/claim.html layouts/shortcodes/conjecture.html layouts/shortcodes/axiom.html
git commit -m "$(cat <<'EOF'
feat(d-1): 12 AMS-style semantic-block shortcodes

theorem, lemma, corollary, proposition, definition, proof, remark,
example, note, claim, conjecture, axiom — each ~10 LoC, follows the
sidenote.html scratch-counter pattern.

theorem/lemma/corollary/proposition share `theorem-family` counter;
definition has its own (strong-tier visual); remark/example/note/
claim/conjecture/axiom each independent (soft-tier visual); proof is
unnumbered and auto-appends ∎ tombstone (chrome-less tier).

Title and ID via named `:title` / `:id` shortcode args (ox-hugo
limitation; see spec §3.2). CSS for the class hooks comes in Task 3.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3 — CSS §47: semantic block styling

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/assets/css/main.css` (append §47 at the end of file, after the last `from-stream` rule)

- [ ] **Step 1: Find the end of the existing CSS (after §46 streams)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && tail -5 assets/css/main.css
```

Expected: the last few lines should be the `.from-stream a { color: inherit; }` rule from §46.

- [ ] **Step 2: Append the new §47 section to `assets/css/main.css`**

Append (you can pipe via a heredoc if convenient, or use the Edit tool to add the block at the end of the file):

```css

/* §47 Semantic blocks (AMS-style) — D.1
   Three tiers: strong (theorem family + definition), soft (remark / example /
   note / claim / conjecture / axiom), chrome-less (proof).
   Uses only existing color tokens — no new contrast pairings added.
*/

.block-strong,
.block-soft,
.block-proof {
  margin-block: 1.25rem;
}

.block-strong > .block-body,
.block-soft > .block-body,
.block-proof > .block-body {
  margin-top: 0.4rem;
}

.block-strong > .block-body > *:first-child,
.block-soft > .block-body > *:first-child,
.block-proof > .block-body > *:first-child {
  margin-top: 0;
}

.block-strong > .block-body > *:last-child,
.block-soft > .block-body > *:last-child,
.block-proof > .block-body > *:last-child {
  margin-bottom: 0;
}

.block-strong {
  padding-left: 1rem;
  border-left: 3px solid var(--color-burgundy);
}

.block-soft {
  padding-left: 1rem;
  border-left: 2px solid var(--color-stone);
}

.block-proof {
  /* No border; italic body conveys the kind. */
}

.block-header {
  margin: 0;
  font-family: var(--font-body);
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.4;
}

.block-proof > .block-header {
  font-weight: 400; /* italic via the inline <em> wrapper inside the template */
}

.block-title {
  color: var(--color-ink-soft);
  font-weight: 400;
}

.block-proof > .block-body {
  font-style: italic;
}

.proof-tombstone {
  margin-left: 0.4em;
  font-style: normal; /* keep ∎ upright even though body is italic */
}

/* Deep-link affordance: anchored blocks (id attr present) get the same
   hover # affordance as headings in §11. The selector mirrors the heading
   pattern: a sibling-of nothing trick, so we use direct id presence.
*/
.block-strong[id]:hover::after,
.block-soft[id]:hover::after,
.block-proof[id]:hover::after {
  content: " #";
  color: var(--color-ink-soft);
  font-weight: 400;
  margin-left: 0.4em;
}
```

- [ ] **Step 3: Verify the CSS compiles into the Hugo bundle**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && hugo --minify 2>&1 | tail -10
```

Expected: build succeeds. `public/css/main.<hash>.css` exists and is non-empty:

```bash
ls -la /Users/a3madkour/Sync/Workspace/a3madkour.github.io/public/assets/css/main.*.css 2>&1 | head
```

(Path may vary slightly depending on Hugo version; the `main.<hash>.css` file under `public/` should exist.)

- [ ] **Step 4: Run contrast check to verify no token regression**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check-contrast.py
```

Expected: `OK` — §47 only uses existing tokens (`--color-burgundy`, `--color-stone`, `--color-ink-soft`), all already covered by the existing 9 pairings.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add assets/css/main.css
git commit -m "$(cat <<'EOF'
feat(d-1): CSS §47 — semantic block styling

Three visual tiers using existing color tokens:
- Strong (theorem/lemma/corollary/proposition/definition): 3px
  left-border in --color-burgundy, regular body.
- Soft (remark/example/note/claim/conjecture/axiom): 2px left-border
  in --color-stone, regular body.
- Chrome-less (proof): no border, italic body, ∎ tombstone upright.

Anchored blocks (id attr set) get the heading-style hover # deep-link
affordance from §11.

~80 LoC, no new color tokens or contrast pairings.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4 — Fill example-five body with all 12 block kinds

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-five/index.md`

Replace the body (everything after the `---` closer of the frontmatter) with the full kitchen-sink demonstration.

- [ ] **Step 1: Replace the body section of example-five/index.md**

The full file should now read:

```markdown
---
date: 2026-06-01
draft: false
has_citations: false
has_footnotes: false
has_math: true
has_sidenotes: false
has_video_sync: false
has_widgets: false
lastmod: 2026-06-01
series: ""
series_order: 0
summary: "Lorem ipsum — AMS-style block kitchen sink for D.1."
tags: []
title: "Example Five"
toc: true
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Demonstration essay for the AMS-style semantic blocks (D.1).

## Section one — definitions and theorems

{{< definition title="Continuity" >}}A function `f` is continuous at \(x_0\) if for every `ε > 0` there exists `δ > 0` such that `|x - x_0| < δ` implies `|f(x) - f(x_0)| < ε`.{{< /definition >}}

{{< theorem title="Intermediate Value" id="thm-ivt" >}}If `f` is continuous on the closed interval `[a, b]` and `c` is any value between `f(a)` and `f(b)`, then there exists `x ∈ [a, b]` with `f(x) = c`.{{< /theorem >}}

{{< proof of="Intermediate Value" >}}Suppose without loss of generality that `f(a) < c < f(b)`. Lorem ipsum proof sketch \(\alpha + \beta = \gamma\).{{< /proof >}}

{{< lemma >}}Lemma without a title — shares the theorem-family counter with theorem above.{{< /lemma >}}

{{< corollary >}}Corollary without a title — also shares the theorem-family counter.{{< /corollary >}}

{{< proposition title="Trivial proposition" >}}A proposition with a title — counter continues from the theorem family.{{< /proposition >}}

## Section two — supporting prose

{{< remark >}}Remark without a title — separate counter.{{< /remark >}}

{{< example title="Counterexample" >}}Example with a title — independent counter.{{< /example >}}

{{< note >}}Note without a title — independent counter.{{< /note >}}

{{< claim >}}Claim without a title — independent counter.{{< /claim >}}

{{< conjecture title="Riemann-style" >}}Conjecture with a title — independent counter.{{< /conjecture >}}

{{< axiom >}}Axiom without a title — independent counter.{{< /axiom >}}

## Section three — cross-reference

By the [Intermediate Value Theorem](#thm-ivt), the equation `f(x) = c` has a solution in `[a, b]`. The visible link text "Intermediate Value Theorem" is author-typed (V1 does not auto-format cross-references; see D.x follow-ups).
```

- [ ] **Step 2: Run check_math.py — should now pass (body has `\(...\)` markers + has_math: true)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_math.py
```

Expected: `OK — math frontmatter coupling validates.`

- [ ] **Step 3: Run hugo --minify to verify all blocks render without template errors**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && hugo --minify 2>&1 | tail -10
```

Expected: build succeeds. example-five appears in `public/essays/example-five/index.html` with all 12 block kinds rendered as HTML `<div>` elements with the correct `block-<kind>` classes.

Spot-check the output:

```bash
grep -E "Theorem 1|Lemma 2|Corollary 3|Proposition 4|Definition 1|Proof of|Remark 1|Example 1|Note 1|Claim 1|Conjecture 1|Axiom 1" /Users/a3madkour/Sync/Workspace/a3madkour.github.io/public/essays/example-five/index.html | head
```

Expected: each label appears once (theorem family counts 1→4 across theorem/lemma/corollary/proposition; definition starts its own counter at 1; the 6 soft kinds each have their own counter starting at 1).

- [ ] **Step 4: Run the essay-frontmatter linter + smoke test**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_fixtures.py && python3 tools/check_smoke.py 2>&1 | tail -5
```

Expected: both pass. (Smoke walks `public/` and checks pages exist + bodies are non-empty.)

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add content/essays/example-five/index.md
git commit -m "$(cat <<'EOF'
chore(d-1): example-five body — kitchen-sink AMS blocks fixture

Exercises all 12 block kinds in one essay:
- definition + theorem (with id) + proof (of) demonstrating the
  classic statement → claim → justification chain.
- lemma + corollary + proposition (no titles) verify the
  theorem-family shared counter continues 2→3→4 after the lone
  theorem at #1.
- 6 soft-tier blocks (remark/example/note/claim/conjecture/axiom)
  each on independent counters.
- Cross-ref via [#thm-ivt] verifies the anchor wiring.

has_math: true now matches body content (\(...\) markers present),
so check_math.py passes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5 — CLAUDE.md "Semantic blocks" subsection

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/CLAUDE.md`

Add a new "Semantic blocks (AMS-style)" subsection under the existing "Content & layouts" architecture section.

- [ ] **Step 1: Locate the insertion point in CLAUDE.md**

Find the "### Content & layouts" heading (around line 95-100 in CLAUDE.md):

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && grep -n "^### " CLAUDE.md | head -10
```

The list of architecture subsections includes (in order): CSS pipeline / JS pipeline / Theme toggle / Search modal / Math pipeline / Content & layouts / Frontmatter contracts / Bento variable-tile grid / Filter chips / etc.

D.1's subsection goes immediately AFTER "### Content & layouts" but BEFORE "### Frontmatter contracts" (or wherever the next `### ` heading is — verify by reading the section ordering).

- [ ] **Step 2: Insert the new subsection**

Use the Edit tool to insert the following block. The placement is: locate the END of the "### Content & layouts" subsection (the paragraph that finishes describing content/, layouts/, partials/, shortcodes/, top nav) and insert the new heading + body immediately after it (before the next `### ` heading).

```markdown
### Semantic blocks (AMS-style)

Essays can use 12 AMS-style block shortcodes for rigorous prose: `theorem`, `lemma`, `corollary`, `proposition`, `definition`, `proof`, `remark`, `example`, `note`, `claim`, `conjecture`, `axiom`. Each is a Hugo shortcode in `layouts/shortcodes/` with per-page auto-numbering via `$page.Scratch`.

Authors write `#+begin_theorem` blocks in org, with optional `#+attr_shortcode: :title <name> :id <slug>` header line for title and cross-reference ID. ox-hugo's `org-hugo-paired-shortcodes` config (in `a3madkour-publish-export.el`) emits the matching `{{< theorem title="…" id="…" >}}…{{< /theorem >}}` markdown.

**Numbering follows AMS conventions:** theorem/lemma/corollary/proposition share one counter (`theorem-family`); definition/remark/example/note/claim/conjecture/axiom each have independent counters; proof is unnumbered (auto-appends ∎ tombstone).

**Cross-references** use the block's `#+attr_shortcode: :id <slug>` + org's `[[#id][text]]` link syntax. Visible reference text is author-managed (renumber-induced drift is a documented limitation; auto-formatting is a D.x follow-up). `:CUSTOM_ID:` property drawers continue to work for headings (B.1.1 unchanged) but are silently dropped by ox-hugo on special blocks.

**CSS §47** styles three visual tiers (strong / soft / chrome-less) using existing color tokens. No new `has_*` frontmatter flag — the CSS loads on every essay page.
```

- [ ] **Step 3: Verify the subsection appears in the right place**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && grep -n "^### " CLAUDE.md | head -15
```

Expected: `### Semantic blocks (AMS-style)` appears between `### Content & layouts` and the next existing `### ` heading.

- [ ] **Step 4: Sanity-check no counts need updating**

Per spec §7.2, no count bumps in CLAUDE.md for D.1 — linter pair count stays at 25, CI step count stays at 63. Confirm by grep:

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && grep -E "Twenty-five linter pairs|Total: 63 named steps|25 linter pairs \+ 1 sibling-less = 52 steps" CLAUDE.md
```

Expected: each pattern matches at least once (left over from C — not changed by D.1).

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(d-1): CLAUDE.md — semantic blocks subsection

New "Semantic blocks (AMS-style)" subsection under Architecture
explains the 12 AMS shortcodes, the org-side authoring contract
(#+begin_<kind> + #+attr_shortcode), AMS numbering conventions,
cross-ref UX, and CSS §47 visual treatment.

No count bumps (D.1 adds no linter pair, no CI step).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6 — Dotfiles: ox-hugo paired-shortcodes config + ert round-trip test

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export.el` (top-level configuration)
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays-test.el` (append +1 round-trip ert)

TDD: write the failing test first, then add the config that makes it pass.

- [ ] **Step 1: Write the failing ert round-trip test**

Open `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays-test.el` and append a new test at the end (before the final `;;; ... ends here` line if present):

```elisp
;; -- D.1: ox-hugo paired-shortcodes for AMS blocks --

(ert-deftest a3madkour-pub-essays-test/special-block-round-trip ()
  "An org `#+begin_theorem' block with `#+attr_shortcode: :title Foo :id thm-foo'
must emit as a paired Hugo shortcode `{{< theorem title=\"Foo\" id=\"thm-foo\" >}}
... {{< /theorem >}}' in the post-export markdown body."
  (require 'a3madkour-publish-export)
  (let* ((tmp (make-temp-file "essays-special-block-" nil ".org"))
         (body (concat "#+title: T\n"
                       "#+date: <2026-06-01>\n"
                       "\n"
                       "#+attr_shortcode: :title Foo :id thm-foo\n"
                       "#+begin_theorem\n"
                       "Body content.\n"
                       "#+end_theorem\n")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert body))
          (let* ((result (a3madkour-pub-export/export-file tmp))
                 (md     (plist-get result :body)))
            (should (string-match-p "{{< theorem title=\"Foo\" id=\"thm-foo\" >}}" md))
            (should (string-match-p "{{< /theorem >}}" md))))
      (delete-file tmp))))
```

- [ ] **Step 2: Run ert — verify the new test fails**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "special-block-round-trip|Ran" | tail -5
```

Expected: `special-block-round-trip` reports `FAILED` because ox-hugo's `org-hugo-paired-shortcodes` is currently empty, so the `#+begin_theorem` block emits as `<div class="theorem">…</div>` instead of as a paired shortcode.

(If the test fails for a different reason — e.g., `export-file` errors out — the configuration may already partially be set; read the failure output before proceeding.)

- [ ] **Step 3: Add the ox-hugo paired-shortcodes config to a3madkour-publish-export.el**

Open `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export.el`. After the `(require 'ox-hugo)` line at the top of the file (around line 25), insert:

```elisp
;; D.1: enable 12 AMS-style block kinds as paired Hugo shortcodes.
;; #+begin_<kind> blocks emit as {{< <kind> >}}…{{< /<kind> >}} markdown
;; instead of the default <div class="<kind>">…</div>.
;; Title + cross-ref ID come via #+attr_shortcode: :title <name> :id <slug>
;; on a header line above the block (positional args are dropped in the
;; paired-shortcode path; see spec §3.2).
(setq org-hugo-paired-shortcodes
      "theorem lemma corollary proposition definition proof remark example note claim conjecture axiom")

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

- [ ] **Step 4: Run ert — verify the new test passes; existing 480 tests still pass**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "special-block-round-trip|Ran" | tail -5
```

Expected: `special-block-round-trip` reports `passed`. Total: `Ran 481 tests` (was 480) with `0 unexpected`.

- [ ] **Step 5: Commit (one commit covering both the config + test)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-export.el emacs-configs/custom/lisp/a3madkour-publish-essays-test.el
git commit -m "$(cat <<'EOF'
feat(d-1): ox-hugo paired-shortcodes for 12 AMS block kinds

Sets `org-hugo-paired-shortcodes` to the space-separated list of all
12 block kinds. After this change, `#+begin_<kind>' blocks emit as
paired Hugo shortcodes `{{< <kind> >}}…{{< /<kind> >}}` instead of
the default `<div class="<kind>">…</div>`. Title and cross-ref ID
come via `#+attr_shortcode: :title <name> :id <slug>' header line.

Also sets `org-hugo-special-block-type-properties' :trim-pre /
:trim-post for the 12 block kinds — keeps emitted markdown tidy.

+1 ert: `special-block-round-trip' (480 → 481).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7 — End-to-end spot-check + memory note

**Files:**
- No code edits in this task. Output: a memory note documenting findings + any in-slice fix-ups.

Final integration verification — same pattern as C's T10.

- [ ] **Step 1: Run the full site-side CI checks locally**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_fixtures.py && python3 tools/check_math.py && python3 tools/check_smoke.py 2>&1 | tail -5
```

Expected: all three exit 0 with success messages. The smoke test specifically should walk `public/essays/example-five/index.html` and find non-empty body content.

- [ ] **Step 2: Run dotfiles ert suite**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -5
```

Expected: `Ran 481 tests, 481 results as expected, 0 unexpected`.

- [ ] **Step 3: Visual spot-check example-five in the dev server**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && hugo server --buildDrafts &
```

Then open `http://localhost:1313/essays/example-five/` in a browser. Verify:

1. All 12 block kinds render with the correct labels (Theorem 1, Lemma 2, Corollary 3, Proposition 4, Definition 1, Proof of Intermediate Value, Remark 1, Example 1, Note 1, Claim 1, Conjecture 1, Axiom 1).
2. Strong-tier blocks (theorem/lemma/corollary/proposition/definition) show a 3px burgundy left border.
3. Soft-tier blocks (remark/example/note/claim/conjecture/axiom) show a 2px stone left border.
4. Proof block has no border but italic body + a ∎ tombstone at the end.
5. The cross-ref link "Intermediate Value Theorem" navigates to `#thm-ivt` and the theorem block scrolls into view.
6. Theme toggle (light/dark) renders the borders correctly in both modes.

Kill the dev server (Ctrl-C) when done.

- [ ] **Step 4: Negative-path verification**

Edit `content/essays/example-five/index.md`; change `has_math: true` to `has_math: false`; run `python3 tools/check_math.py`; verify it errors about example-five (math markers found but has_math is false); revert the edit.

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
sed -i.bak 's/^has_math: true/has_math: false/' content/essays/example-five/index.md
python3 tools/check_math.py
# Expected: 1 math coupling issue(s). … "math markers found … but has_math is false"
mv content/essays/example-five/index.md.bak content/essays/example-five/index.md
python3 tools/check_math.py
# Expected: OK — math frontmatter coupling validates.
```

- [ ] **Step 5: Write the memory note + update next-slice pointer**

Create `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/.claude/memory/project_d1_complete.md`:

```markdown
---
name: d1-complete
description: "D.1 semantic blocks — shipped 2026-06-0X (TBD when this lands). 12 AMS-style Hugo shortcodes (theorem family + definition strong-tier; 6 soft-tier; proof chrome-less with ∎). CSS §47 three-tier visual treatment using existing tokens. ox-hugo `org-hugo-paired-shortcodes` config drives `#+begin_<kind>' → `{{< <kind> >}}'. example-five fixture exercises all 12 kinds + cross-ref. +1 ert (480 → 481). No new linter pair; no CI step bump."
metadata:
  node_type: memory
  type: project
---

**Shipped (code-complete 2026-06-0X):** D.1 — semantic blocks per `docs/superpowers/specs/2026-06-01-phase-3-d1-semantic-blocks-design.md` + `docs/superpowers/plans/2026-06-01-phase-3-d1-semantic-blocks.md`. 7 tasks, ~6 site + 1 dotfiles commits.

## What ships in D.1

### Site (~/Sync/Workspace/a3madkour.github.io/)
- 12 new shortcodes in `layouts/shortcodes/` — theorem / lemma / corollary / proposition / definition / proof / remark / example / note / claim / conjecture / axiom.
- CSS §47 (~80 LoC) — three-tier styling using --color-burgundy, --color-stone, --color-ink-soft.
- `content/essays/example-five/index.md` — kitchen-sink fixture exercising all 12 kinds + a `[#thm-ivt]` cross-ref.
- `CLAUDE.md` — new "Semantic blocks (AMS-style)" subsection under Architecture.

### Dotfiles (~/dotfiles/)
- `a3madkour-publish-export.el` — `org-hugo-paired-shortcodes` set to the 12-kind space-separated list; `org-hugo-special-block-type-properties` :trim-pre / :trim-post.
- `a3madkour-publish-essays-test.el` — +1 ert (`special-block-round-trip`).

## In-slice fix-ups

[List any commits beyond the 7 plan tasks. Examples:
 - "Spot-check found X; shipped Y commit"
 - "Manual integration revealed Z; fixed in commit ABC"]

## Why this slice mattered

The site has shipped the existing semantic primitives (sidenote, figure, spoiler) since Phase 1, but had no vocabulary for the rigorous-prose constructs an academic essay needs — theorems, definitions, proofs. D.1 closes that gap. The next slice (D.2) picks up the existing multi-target export spec and wires the same vocabulary into PDF + Word render targets.

## Known follow-ups (D.x)

- **Cross-reference auto-formatting** (`{{< ref-block "thm-foo" >}}` → "Theorem 1") via two-pass scratch. Trigger: first real essay that hits renumber drift.
- **Section-prefixed numbering** ("Theorem 3.2"). Trigger: a long essay where bare integers are hard to navigate.
- **Custom block kinds beyond the 12** (e.g., `principle`). Trigger: spec request from real essay usage.
- **Per-essay numbering reset point.** Trigger: long essays where two unrelated arguments share theorem numbering.
- **D.2 multi-target export.** Picks up `2026-05-13-multi-target-export-design.md`; same vocabulary in PDF + Word.

## End-of-slice test inventory

- ert (dotfiles): 480 → 481 (+1 round-trip integration).
- Site Python unit tests: unchanged.
- Linter pairs: 25 (unchanged).
- CI step count: 63 (unchanged).
- Shortcode count: 8 → 20 (existing cite/sidenote/figure/spoiler + math stub retired in C + 4 deferred stubs unchanged + 12 new semantic blocks).
```

Update `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/.claude/memory/MEMORY.md` — append a one-line entry near the bottom (consistent with the existing pattern):

```
- [D.1 semantic blocks — shipped](project_d1_complete.md) — **shipped 2026-06-0X**; 12 AMS-style Hugo shortcodes (theorem family + definition strong-tier, 6 soft-tier, proof chrome-less with ∎); CSS §47 three-tier treatment using existing tokens; ox-hugo paired-shortcodes config; example-five kitchen-sink fixture; +1 ert (480 → 481); no new linter pair or CI step bump
```

Update `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/.claude/memory/project_next_slice.md` — flip the pointer from D.1 → D.2 (multi-target export, picks up the existing spec). Rewrite the file body to describe D.2's scope as the new next slice; preserve the format used after C.

Commit:

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add .claude/memory/project_d1_complete.md .claude/memory/MEMORY.md .claude/memory/project_next_slice.md
git commit -m "$(cat <<'EOF'
docs(memory): D.1 semantic blocks shipped — next slice = D.2

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review checklist (for plan author / reviewer)

- [ ] Each task has 5 micro-steps ending in a commit.
- [ ] Every code block compiles / runs as-is (no `TBD` / `TODO` / `...`).
- [ ] All file paths are absolute.
- [ ] Test commands include expected output.
- [ ] Function / property / shortcode names are consistent across tasks (`block-strong`, `block-soft`, `block-proof`, `block-header`, `block-title`, `proof-tombstone`, `theorem-family`, etc.).
- [ ] No task implements something a later task should implement.
- [ ] Spec coverage:
  - §3 (source-side contract) → Task 6 (ox-hugo config).
  - §4 (shortcode contract + numbering) → Task 2.
  - §5 (CSS §47) → Task 3.
  - §6 (fixture + test plan) → Tasks 1 + 4 + 6 (ert) + 7 (manual).
  - §7 (CLAUDE.md docs) → Task 5.
  - §10 (commit shape estimate ~7 commits) → 7 tasks here, each one commit.
  - §11 (sequencing) → memory note in Task 7.

---

## Out-of-band notes for the executor

- **Task ordering matters in a different way than C.** Task 1 (fixture stub) intentionally leaves `check_math.py` in a failing state until Task 4 fills the body. If you stop the slice between Tasks 1-3, the site CI would fail on that linter. Push as a unit, not incrementally to origin, OR push to a feature branch only.
- **No new linter pair (matches the C pattern for non-grammar slices).** Hugo's build is the implicit gate; existing `check_fixtures.py` catches frontmatter regressions; `check_smoke.py` catches missing pages.
- **Dotfiles repo discipline.** Never `git add -A` / `git add .`. Explicit file paths only (5 pre-existing dirty tracked files must not be committed).
- **Push discipline.** Hold push until end of slice per the established session policy. The ~7 commits stay local until then.
- **org-math-lint venv reminder** (from C). If the math validator is needed for any new authoring work (e.g., the dev-server spot-check in Task 7 Step 3 — although this slice doesn't drive a3-pub.sh publish), the venv may still need recreating. See `[[reference-org-math-lint-venv-platform]]`. D.1's tasks don't directly invoke a3-pub.sh, so this is informational.
