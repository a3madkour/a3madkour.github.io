# TOC Collapsible Subsections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In the essay TOC, keep only the active top-level section's subtree expanded and collapse the rest, driven by the existing scrollspy, with manual chevrons the scrollspy re-asserts on the next scroll.

**Architecture:** Pure client-side progressive enhancement folded into the TOC scrollspy already in `assets/js/nav.js` (it early-returns off-essay). Hugo's `.TableOfContents` HTML is unchanged; JS injects `<button class="toc-toggle">` per section and wraps each child `<ul>` in an animatable `.toc-disclosure`. No-JS → full tree. A new deep-TOC fixture exercises it; a new linter pair guards the fixture's depth.

**Tech Stack:** Hugo (extended ≥0.148.0), hand-rolled CSS (`assets/css/main.css`), vanilla ES modules (no npm), Python stdlib linters.

**Branch:** `feature/toc-collapsible-subsections` (already created; spec committed at `f12de99`).

**Spec:** `docs/superpowers/specs/2026-05-14-toc-collapsible-subsections-design.md`.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `content/essays/example-deep-toc-essay/index.md` | Create | Dummy essay with h2›h3›h4 tree — the only fixture exercising collapse. |
| `tools/check_toc_depth.py` | Create | Linter: assert ≥1 non-draft essay reaches ≥3 distinct heading levels. |
| `tools/test_check_toc_depth.py` | Create | Unit tests for the linter (temp-repo pattern). |
| `.github/workflows/hugo.yaml` | Modify | 2 new CI steps (linter + sibling test) after the essay linter pair. |
| `tools/ci-local.sh` | Modify | Same pair in the pre-build block. |
| `assets/css/main.css` | Modify | `.toc-toggle` / `.toc-disclosure` styling + grid-rows animation + reduced-motion (after line 674). |
| `assets/js/nav.js` | Modify | Replace the TOC scrollspy block (lines 1–39): DOM transform + collapse drivers folded into `updateActive()`. |
| `CLAUDE.md` | Modify | Linter inventory (19→20), CI step counts (16→17 pairs, 34→36, 51→53), slice status. |

Order matters: the fixture (Task 1) must exist before the linter's real-repo run (Task 2/3), or `check_toc_depth.py` fails against the live tree (currently no essay has ≥3 levels).

---

### Task 1: Deep-TOC essay fixture

**Files:**
- Create: `content/essays/example-deep-toc-essay/index.md`

- [ ] **Step 1: Create the fixture**

Create `content/essays/example-deep-toc-essay/index.md` with exactly this content (full essay frontmatter contract per `tools/check_fixtures.py` `REQUIRED_FIELDS`; obviously-dummy body; h2›h3›h4 with ≥3 top-level sections, one nesting h3s, one h3 nesting h4s):

```markdown
---
title: "Example deep TOC essay"
date: 2026-05-18
lastmod: 2026-05-18
draft: false
summary: "Lorem ipsum example — exercises the collapsible-subsection TOC with a three-level heading tree."
tags: ["example-tag-a"]
series: ""
series_order: 0
tile_size: medium
toc: true
has_sidenotes: false
has_citations: false
has_footnotes: false
has_math: false
has_widgets: false
has_video_sync: false
---

Lorem ipsum dolor sit amet — example body exercising a deep table of contents.

## Section one — example heading

Lorem ipsum dolor sit amet, consectetur adipiscing elit.

### Subsection one·a — example heading

Lorem ipsum dolor sit amet.

#### Detail one·a·i — example heading

Lorem ipsum dolor sit amet, sed do eiusmod tempor.

#### Detail one·a·ii — example heading

Ut enim ad minim veniam, quis nostrud exercitation.

### Subsection one·b — example heading

Duis aute irure dolor in reprehenderit.

## Section two — example heading

Excepteur sint occaecat cupidatat non proident.

### Subsection two·a — example heading

Sunt in culpa qui officia deserunt mollit anim.

## Section three — example heading

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod.
```

- [ ] **Step 2: Verify it passes the essay fixture linter**

Run: `python3 tools/check_fixtures.py`
Expected: `All essay fixtures pass linter.` (exit 0). The new fixture has the full required-field set, so no new failure.

- [ ] **Step 3: Verify it builds and renders a 3-level TOC**

Run: `HUGO_ENVIRONMENT=production hugo --minify >/dev/null && grep -o 'TableOfContents' public/essays/example-deep-toc-essay/index.html | head -1`
Expected: prints `TableOfContents` (the page built with a TOC). Then:
Run: `grep -c '<ul>' public/essays/example-deep-toc-essay/index.html`
Expected: a count ≥ 4 (nested `<ul>`s prove multi-level nesting rendered). Then clean: `rm -rf public`.

- [ ] **Step 4: Commit**

```bash
git add content/essays/example-deep-toc-essay/index.md
git commit -m "fixture(essays): add example-deep-toc-essay (h2>h3>h4 tree)

Exercises the collapsible-subsection TOC. Obviously-dummy filler;
full frontmatter contract; all has_* false.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: `check_toc_depth.py` linter + unit tests (TDD)

**Files:**
- Create: `tools/test_check_toc_depth.py`
- Create: `tools/check_toc_depth.py`

- [ ] **Step 1: Write the failing test**

Create `tools/test_check_toc_depth.py` with exactly:

```python
"""Tests for check_toc_depth.py — run with: python3 -m unittest tools/test_check_toc_depth.py -v"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_toc_depth as lint  # noqa: E402  # pyright: ignore[reportMissingImports]


def essay(draft: bool, body: str) -> str:
    return (
        "---\n"
        'title: "X"\n'
        "draft: " + ("true" if draft else "false") + "\n"
        "---\n\n" + body
    )


DEEP = essay(False, "## H2 a\n\n### H3 a\n\n#### H4 a\n\nbody\n")
SHALLOW = essay(False, "## H2 a\n\n### H3 a\n\nbody\n")
DRAFT_DEEP = essay(True, "## H2 a\n\n### H3 a\n\n#### H4 a\n\nbody\n")
FENCED_FAKE_DEPTH = essay(
    False,
    "## H2 a\n\n```text\n### not a heading\n#### not a heading\n```\n\nbody\n",
)


class TempRepo:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        (self.root / "content" / "essays").mkdir(parents=True)

    def write_essay(self, slug: str, text: str) -> None:
        d = self.root / "content" / "essays" / slug
        d.mkdir(exist_ok=True)
        (d / "index.md").write_text(text)

    def cleanup(self) -> None:
        shutil.rmtree(self.root)


class CheckTocDepthTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    def test_one_deep_essay_passes(self) -> None:
        self.repo.write_essay("deep", DEEP)
        self.repo.write_essay("shallow", SHALLOW)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected failures: {errors}")
        self.assertEqual(errors, [])

    def test_all_shallow_fails(self) -> None:
        self.repo.write_essay("shallow-1", SHALLOW)
        self.repo.write_essay("shallow-2", SHALLOW)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("3 distinct heading levels" in e for e in errors))

    def test_draft_deep_does_not_count(self) -> None:
        self.repo.write_essay("draft-deep", DRAFT_DEEP)
        self.repo.write_essay("shallow", SHALLOW)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)

    def test_fenced_code_block_depth_ignored(self) -> None:
        self.repo.write_essay("fenced", FENCED_FAKE_DEPTH)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)

    def test_empty_essays_section_passes(self) -> None:
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tools/test_check_toc_depth.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'check_toc_depth'`.

- [ ] **Step 3: Write the linter**

Create `tools/check_toc_depth.py` with exactly:

```python
#!/usr/bin/env python3
"""Essay TOC-depth linter.

Guards the invariant that at least one non-draft essay fixture exercises a
deep (>=3 distinct heading levels) table of contents, so the collapsible-
subsection TOC behaviour stays exercised. If every essay flattens to <3
levels the collapse feature has nothing to act on and no test of it.

Counts ATX headings h2-h6 (Hugo markup.tableOfContents startLevel is 2, so
h1 / page title is irrelevant). Fenced code blocks are stripped first so a
`### ...` inside a ``` block is not miscounted.

Exits 0 on all-pass, 1 on violation. Stdlib only.
"""
from __future__ import annotations

import re
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
DRAFT_RE = re.compile(r"^draft:\s*(true|false)\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^\s*```")
HEADING_RE = re.compile(r"^(#{2,6})\s+\S")
MIN_DISTINCT_LEVELS = 3


def strip_frontmatter(text: str) -> tuple[bool, str]:
    """Return (is_draft, body). Missing draft key counts as not-draft."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return (False, text)
    fm = m.group(1)
    dm = DRAFT_RE.search(fm)
    is_draft = bool(dm and dm.group(1) == "true")
    return (is_draft, text[m.end():])


def distinct_heading_levels(body: str) -> set[int]:
    """Distinct ATX heading levels h2-h6, ignoring fenced code blocks."""
    levels: set[int] = set()
    in_fence = False
    for line in body.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        hm = HEADING_RE.match(line)
        if hm:
            levels.add(len(hm.group(1)))
    return levels


def run(repo_root: Path) -> tuple[int, list[str]]:
    essays_dir = repo_root / "content" / "essays"
    if not essays_dir.exists():
        return (0, [])

    non_draft_essays = 0
    deepest = 0
    for essay_dir in sorted(essays_dir.iterdir()):
        if not essay_dir.is_dir():
            continue
        md = essay_dir / "index.md"
        if not md.exists():
            continue
        is_draft, body = strip_frontmatter(md.read_text())
        if is_draft:
            continue
        non_draft_essays += 1
        deepest = max(deepest, len(distinct_heading_levels(body)))

    if non_draft_essays == 0:
        return (0, [])
    if deepest < MIN_DISTINCT_LEVELS:
        return (
            1,
            [
                "no non-draft essay reaches >=3 distinct heading levels "
                f"(deepest is {deepest}); the collapsible-subsection TOC "
                "needs a fixture with h2>h3>h4 to stay exercised"
            ],
        )
    return (0, [])


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        print("TOC-depth lint failures:")
        for e in errors:
            print(f"  {e}")
    else:
        print("TOC-depth linter passes (a deep-TOC essay fixture exists).")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the unit tests to verify they pass**

Run: `python3 -m unittest tools/test_check_toc_depth.py -v`
Expected: PASS — `Ran 5 tests` … `OK`.

- [ ] **Step 5: Run the linter against the real repo**

Run: `python3 tools/check_toc_depth.py`
Expected: `TOC-depth linter passes (a deep-TOC essay fixture exists).` (exit 0) — because Task 1's fixture exists. If Task 1 was skipped this prints the failure message and exits 1.

- [ ] **Step 6: Commit**

```bash
git add tools/check_toc_depth.py tools/test_check_toc_depth.py
git commit -m "lint(toc): add check_toc_depth linter pair

Asserts >=1 non-draft essay has >=3 distinct heading levels so the
collapsible-subsection TOC stays exercised. Strips fenced code blocks;
drafts don't count; empty essays section vacuously passes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Wire the linter pair into CI + ci-local.sh

**Files:**
- Modify: `.github/workflows/hugo.yaml` (after line 55)
- Modify: `tools/ci-local.sh` (after line 22)

- [ ] **Step 1: Add the two CI steps after the essay linter pair**

In `.github/workflows/hugo.yaml`, find:

```yaml
      - name: Run essay linter unit tests
        run: python3 -m unittest tools/test_check_fixtures.py -v
      - name: Verify garden fixtures
```

Replace with:

```yaml
      - name: Run essay linter unit tests
        run: python3 -m unittest tools/test_check_fixtures.py -v
      - name: Verify essay TOC depth
        run: python3 tools/check_toc_depth.py
      - name: Run TOC-depth linter unit tests
        run: python3 -m unittest tools/test_check_toc_depth.py -v
      - name: Verify garden fixtures
```

- [ ] **Step 2: Add the pair to ci-local.sh after the essay pair**

In `tools/ci-local.sh`, find:

```bash
python3 tools/check_fixtures.py
python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -3

python3 tools/check_garden_fixtures.py
```

Replace with:

```bash
python3 tools/check_fixtures.py
python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -3

python3 tools/check_toc_depth.py
python3 -m unittest tools/test_check_toc_depth.py -v 2>&1 | tail -3

python3 tools/check_garden_fixtures.py
```

- [ ] **Step 3: Verify the workflow YAML is still valid**

Run: `python3 -c "import sys; sys.exit(0)" && grep -n "check_toc_depth" .github/workflows/hugo.yaml tools/ci-local.sh`
Expected: prints 3 matching lines (1 linter + 1 test step in the workflow, the linter line in ci-local.sh — plus the test line; 4 lines total across both files). Confirm the workflow shows `Verify essay TOC depth` and `Run TOC-depth linter unit tests` adjacent to the essay pair.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/hugo.yaml tools/ci-local.sh
git commit -m "ci(toc): run check_toc_depth pair after the essay linter pair

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: CSS — toggle + animatable disclosure

**Files:**
- Modify: `assets/css/main.css` (insert after line 674: `.essay-toc #TableOfContents > ul > li > ul { padding-left: 1rem; }`)

- [ ] **Step 1: Add the CSS block**

In `assets/css/main.css`, find this exact line:

```css
.essay-toc #TableOfContents > ul > li > ul { padding-left: 1rem; }
```

Immediately after it (before the `@media (min-width: 1100px)` block that follows), insert:

```css

/* TOC collapsible subsections — spec
   docs/superpowers/specs/2026-05-14-toc-collapsible-subsections-design.md.
   assets/js/nav.js injects .toc-toggle buttons and wraps each section's
   child <ul> in .toc-disclosure. No-JS: none of this matches and the rule
   above shows the full indented tree (progressive-enhancement floor). */
.toc-toggle {
  appearance: none;
  background: none;
  border: 0;
  margin: 0;
  padding: 0 0.4rem 0 0;
  cursor: pointer;
  color: var(--color-ink-soft);
  font: inherit;
  line-height: 1;
}
.toc-toggle::before {
  content: "";
  display: inline-block;
  width: 0;
  height: 0;
  border-left: 0.32rem solid currentColor;
  border-top: 0.26rem solid transparent;
  border-bottom: 0.26rem solid transparent;
  transition: transform 180ms ease;
}
.toc-toggle[aria-expanded="true"]::before { transform: rotate(90deg); }
.toc-toggle:hover { color: var(--color-burgundy); }

.toc-disclosure {
  display: grid;
  grid-template-rows: 0fr;
  overflow: hidden;
  transition: grid-template-rows 180ms ease;
}
.toc-section.is-expanded > .toc-disclosure { grid-template-rows: 1fr; }
.toc-disclosure > ul {
  min-height: 0;        /* required so the 0fr row actually clips the <ul> */
  padding-left: 1rem;   /* preserves the indent the > li > ul rule gave pre-wrap */
}
.toc-disclosure.is-instant { transition: none; }

@media (prefers-reduced-motion: reduce) {
  .toc-disclosure,
  .toc-toggle::before { transition: none; }
}
```

- [ ] **Step 2: Verify no contrast regression and CSS still compiles via Hugo**

Run: `python3 tools/check-contrast.py`
Expected: passes (no `:root` token added — only existing `--color-ink-soft` / `--color-burgundy` / `currentColor` used).
Run: `HUGO_ENVIRONMENT=production hugo --minify >/dev/null && echo BUILD_OK && rm -rf public`
Expected: prints `BUILD_OK` (Hugo's CSS pipeline accepted the new rules; no template error).

- [ ] **Step 3: Commit**

```bash
git add assets/css/main.css
git commit -m "style(toc): collapsible-subsection chrome + grid-rows animation

.toc-toggle chevron (CSS border-triangle, no new asset) + .toc-disclosure
0fr<->1fr animatable container; .is-instant escape hatch for scrollspy-
driven changes; prefers-reduced-motion => instant.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: JS — DOM transform + collapse drivers in `nav.js`

**Files:**
- Modify: `assets/js/nav.js` (replace lines 1–39 — the entire TOC scrollspy `DOMContentLoaded` block, up to and including its closing `});` on line 39; leave the page-sidebar block lines 41–97 untouched)

- [ ] **Step 1: Replace the TOC scrollspy block**

Replace the block that currently starts at line 1 (`// TOC active-link highlighter …`) and ends at line 39 (`});` — immediately before the blank line and `// Page sidebar — scrollspy + click handler.` comment) with exactly:

```js
// TOC active-link highlighter + collapsible subsections.
//
// Active-link highlight: "last heading whose top has crossed the trigger
// line" (same algorithm as the page-sidebar scrollspy below).
//
// Collapse: each top-level #TableOfContents > ul > li (level-agnostic) with
// a child <ul> gets a .toc-toggle button; its child <ul> is wrapped in an
// animatable .toc-disclosure. Scrollspy keeps exactly the active section
// expanded (instant, no animation, clears manual "peek"). A manual chevron
// click is an additive animated peek the next scroll re-asserts away.
// No JS -> Hugo's full tree stays visible (true progressive enhancement).
window.addEventListener('DOMContentLoaded', () => {
  const tocRoot = document.getElementById('TableOfContents');
  if (!tocRoot) return;
  const tocLinks = tocRoot.querySelectorAll('a[href^="#"]');
  if (tocLinks.length === 0) return;

  const sections = Array.from(tocLinks)
    .map((link) => ({ link, target: document.querySelector(link.getAttribute('href')) }))
    .filter((s) => s.target);
  if (sections.length === 0) return;

  // --- Collapse: one-time DOM transform ---------------------------------
  let uid = 0;
  const metas = []; // { li, btn, disclosure, peeked }

  function setExpanded(meta, open, instant) {
    if (instant) meta.disclosure.classList.add('is-instant');
    meta.btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    meta.li.classList.toggle('is-expanded', open);
    meta.disclosure.inert = !open;
    if (instant) {
      // Force layout so the no-transition state is committed, then drop
      // .is-instant so a later manual toggle on this section animates.
      void meta.disclosure.offsetHeight;
      meta.disclosure.classList.remove('is-instant');
    }
  }

  Array.from(tocRoot.querySelectorAll(':scope > ul > li')).forEach((li) => {
    const subList = li.querySelector(':scope > ul');
    if (!subList) return;
    uid += 1;
    const id = `toc-sub-${uid}`;
    const disclosure = document.createElement('div');
    disclosure.className = 'toc-disclosure';
    disclosure.id = id;
    li.insertBefore(disclosure, subList);
    disclosure.appendChild(subList);

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'toc-toggle';
    btn.setAttribute('aria-controls', id);
    const label = (li.querySelector(':scope > a')?.textContent || 'section').trim();
    btn.setAttribute('aria-label', `Toggle ${label} subsections`);
    li.insertBefore(btn, li.firstChild);
    li.classList.add('toc-section');

    const meta = { li, btn, disclosure, peeked: false };
    metas.push(meta);
    setExpanded(meta, false, true); // start collapsed, no flash/animation

    btn.addEventListener('click', () => {
      const willOpen = btn.getAttribute('aria-expanded') !== 'true';
      setExpanded(meta, willOpen, false); // manual => animated
      meta.peeked = willOpen;
    });
  });

  function applyActive(activeLink) {
    if (metas.length === 0) return;
    const activeMeta = activeLink
      ? metas.find((m) => m.li.contains(activeLink))
      : null;
    metas.forEach((m) => {
      const shouldOpen = m === activeMeta;
      const isOpen = m.btn.getAttribute('aria-expanded') === 'true';
      if (shouldOpen !== isOpen) setExpanded(m, shouldOpen, true);
      m.peeked = false;
    });
  }

  // --- Scrollspy (drives both highlight and collapse) -------------------
  function updateActive() {
    const scrollY = window.scrollY;
    const viewHeight = window.innerHeight;
    const docHeight = document.documentElement.scrollHeight;
    const triggerY = scrollY + viewHeight * 0.1;
    const atBottom = scrollY + viewHeight >= docHeight - 2;

    let activeHref = sections[0].link.getAttribute('href');
    if (atBottom) {
      activeHref = sections[sections.length - 1].link.getAttribute('href');
    } else {
      for (const s of sections) {
        if (s.target.getBoundingClientRect().top + scrollY <= triggerY) {
          activeHref = s.link.getAttribute('href');
        }
      }
    }

    let activeLink = null;
    tocLinks.forEach((a) => {
      const on = a.getAttribute('href') === activeHref;
      a.classList.toggle('is-active', on);
      if (on) activeLink = a;
    });
    applyActive(activeLink);
  }

  window.addEventListener('scroll', updateActive, { passive: true });
  window.addEventListener('resize', updateActive, { passive: true });
  updateActive();
});
```

- [ ] **Step 2: Verify the bundle builds (esbuild via Hugo) and smoke passes**

Run: `HUGO_ENVIRONMENT=production hugo --minify >/dev/null && echo BUILD_OK`
Expected: `BUILD_OK` (esbuild accepted `nav.js`; no syntax error — a JS error here fails the Hugo build).
Run: `python3 tools/check_smoke.py && rm -rf public`
Expected: smoke passes (built pages well-formed; `core.<hash>.js` emitted and referenced).

- [ ] **Step 3: Manual spot-check on the dev server**

Run: `pkill -f 'hugo server' 2>/dev/null; hugo server --buildDrafts` then open `http://localhost:1313/essays/example-deep-toc-essay/` and verify (both at full width ≥1100px where the TOC is the fixed left rail, and at ~960px half-screen where it is the inline `<details>`):

1. On load only "Section one" is expanded (its h3/h4 visible); Sections two/three show their entry only.
2. Scrolling down expands the section you reach and collapses the previous — instantly, no animation churn.
3. Clicking a collapsed section's chevron animates it open without collapsing the active one (peek); the next scroll re-collapses the peeked one.
4. Clicking a section's text link smooth-scrolls there; on arrival it is expanded.
5. macOS/GNOME reduce-motion (or DevTools "Emulate prefers-reduced-motion: reduce"): manual toggle is instant.
6. Keyboard: Tab reaches the chevron; Space toggles it; `aria-expanded` flips in the a11y tree; Tab into an expanded subtree reaches the sub-links; collapsed subtree links are NOT in the tab order (`inert`).
7. Disable JS (DevTools): the full tree is visible, no chevrons, every link reachable.

Stop the server when done: `pkill -f 'hugo server'`.

- [ ] **Step 4: Commit**

```bash
git add assets/js/nav.js
git commit -m "feat(toc): collapsible subsections driven by the TOC scrollspy

Folds collapse into the existing nav.js TOC scrollspy: injects
.toc-toggle buttons, wraps child <ul>s in animatable .toc-disclosure,
keeps exactly the active section expanded (instant, clears peek), manual
chevron = additive animated peek scrollspy re-asserts. inert on collapsed
disclosures for a11y; no-JS shows the full tree.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Documentation wiring (CLAUDE.md + spec status)

**Files:**
- Modify: `CLAUDE.md` (lines 14, 151, 160, 179, 181, and the Project status block)

- [ ] **Step 1: Update the linter inventory (line 14)**

Find `- Nineteen linter pairs under` … `garden history, pagefind metadata, cite metadata, page weights.` and change `Nineteen` → `Twenty` and insert `essay TOC depth, ` into the enumerated list immediately after `essay fixtures, ` so it reads: `essay fixtures, essay TOC depth, garden fixtures, …`.

- [ ] **Step 2: Update CI step counts (line 151)**

In the Deployment paragraph change `contrast + 16 linter pairs + 1 sibling-less = 34 steps` → `contrast + 17 linter pairs + 1 sibling-less = 36 steps` and `Total: 51 named steps.` → `Total: 53 named steps.`

- [ ] **Step 3: Update the slice's reference-doc line (line 160)**

Replace:

```
- **TOC collapsible subsections stub**: `docs/superpowers/specs/2026-05-14-toc-collapsible-subsections-design.md`. Brainstorm pending — show only the active top-level section's subsections; collapse the rest. Needs a fixture with ≥3 heading levels.
```

with:

```
- **TOC collapsible subsections**: `docs/superpowers/specs/2026-05-14-toc-collapsible-subsections-design.md` (designed) + `docs/superpowers/plans/2026-05-18-toc-collapsible-subsections.md` (plan). Shipped — see memory `project_toc_collapsible_subsections_slice.md`.
```

- [ ] **Step 4: Remove the queued-table row + sequencing mention**

Delete the table row at line 179 (`| TOC collapsible subsections | Independent essay-polish slice | … Stub spec only. |`). At line 181 change the trailing sentence `TOC collapsible subsections is a polish slice with a stub spec only.` to `TOC collapsible subsections shipped 2026-05-18.`

- [ ] **Step 5: Update the Project status "Shipped" line**

In the `**Shipped**:` paragraph (line 164) append ` + TOC collapsible subsections` to the polish-slice list and update `Most recent:` to a one-line summary: `Most recent: TOC collapsible subsections merged 2026-05-18 — scrollspy-driven essay-TOC collapse (level-agnostic top-level, full-subtree expand, manual chevron peek scrollspy re-asserts), new example-deep-toc-essay fixture + check_toc_depth linter pair (20th).` (Replace the existing `Most recent: Persistent graph access …` sentence.)

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude.md): register toc-collapsible-subsections slice (shipped)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Full local CI gate + branch finish

**Files:** none (verification + integration)

- [ ] **Step 1: Run the full CI-equivalent locally**

Run: `tools/ci-local.sh`
Expected: ends with `── CI-EQUIVALENT GREEN — safe to push ──`. The new `check_toc_depth` linter + sibling test run in the pre-build block; LHCI desktop+mobile pass (per memory, expect 5–8 pt mobile-perf local variance vs CI — not a regression if within that band).

- [ ] **Step 2: Write the slice memory file**

Create `/home/a3madkour/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/project_toc_collapsible_subsections_slice.md` (frontmatter `type: project`) summarizing: scope, the four locked decisions, files touched, linter pair #20, merge commit + push status (filled at merge). Add the one-line pointer to `MEMORY.md`.

- [ ] **Step 3: Finish the development branch**

Invoke `superpowers:finishing-a-development-branch` to present merge / PR / cleanup options for `feature/toc-collapsible-subsections`. (Per project convention slices merge to `master` and push; the spot-check checklist from Task 5 Step 3 is the pre-merge eyeball gate already satisfied — re-offer it if the user wants a second pass.)

---

## Self-Review

**1. Spec coverage:**
- Resolved decision 1 (level-agnostic top-level) → Task 5 `:scope > ul > li`. ✓
- Decision 2 (full subtree) → Task 5 wraps the whole child `<ul>` (all descendants) in one disclosure; expanding shows the entire subtree. ✓
- Decision 3 (manual peek, scrollspy re-asserts) → Task 5 `btn.click` sets `peeked`; `applyActive` flips non-active open→closed and clears `peeked`. ✓
- Decision 4 (animate manual, instant scrollspy, reduced-motion) → Task 4 `.is-instant` + `@media reduce`; Task 5 passes `instant=true` from scrollspy, `false` from click. ✓
- Server unchanged / no-JS full tree → no `essay-toc.html` edit; Task 4 comment + the retained `> li > ul` rule. ✓
- a11y `inert` + `aria-expanded`/`aria-controls` + button → Task 5. ✓
- Fixture → Task 1. Linter pair → Task 2. CI/ci-local wiring → Task 3. Bundle placement (nav.js core) → Task 5 (no entry split). Scope (essay TOC only, page-sidebar untouched) → no page-sidebar edits; Task 5 explicitly leaves lines 41–97. Docs → Task 6. Verification → Task 5 Step 3 + Task 7. ✓ No spec gap.

**2. Placeholder scan:** No "TBD"/"TODO"/"similar to"/"handle edge cases". Every code step contains complete code. The only deferred-to-runtime detail (exact chevron glyph) is concretely resolved (CSS border-triangle in Task 4). ✓

**3. Type/name consistency:** `metas` array of `{ li, btn, disclosure, peeked }`; `setExpanded(meta, open, instant)`, `applyActive(activeLink)`, `updateActive()` consistent across Task 5. CSS classes `.toc-toggle` / `.toc-disclosure` / `.toc-section.is-expanded` / `.is-instant` and id pattern `toc-sub-<n>` match between Task 4 (CSS) and Task 5 (JS). Linter `run(repo_root) -> (rc, errors)` matches the test's `lint.run(self.repo.root)`. ✓
