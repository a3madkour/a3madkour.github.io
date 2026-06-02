# Phase 3 C — math validator implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship pre-publish math-syntax validation by integrating the existing `org-math-lint` tool (under `~/org/notes/tools/org-math-lint/`) into the publish pipeline, plus a tiny site-side `has_math` frontmatter coupling check, two refinements to B.4's existing scanner (env detection + code-fence exclusion), retirement of the `{{< math >}}` placeholder shortcode, and a fixture conversion that exercises the whole chain.

**Architecture:** No new validator on the site side — `org-math-lint` is the source-of-truth (1.2k-LoC Python package; 10-rule registry; vendored KaTeX via py-mini-racer). C wires it in: `a3-pub.sh` calls it pre-Emacs (default on; `--skip-math-check` opts out); B.4's existing buffer scanner gains env detection + code-fence exclusion so emitted `has_math` reflects reality including environment-based math; a small `tools/check_math.py` validates `has_math` ↔ body coupling in essays at CI time. The `{{< math >}}` placeholder shortcode is retired (KaTeX parses raw `\(...\)` directly); example-one gets real LaTeX so the chain has an end-to-end fixture.

**Tech Stack:** Python 3 stdlib (`tools/check_math.py` + sibling unittest), Emacs Lisp (B.4 essays handler edits + 2 new ert tests), Bash (a3-pub.sh subprocess hook). No new dependencies in either repo. `org-math-lint` is consumed via its installed venv at `~/org/notes/tools/org-math-lint/.venv/`.

**Spec:** `docs/superpowers/specs/2026-06-01-phase-3-c-math-validator-design.md`

**Working directories:**
- Site: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/`
- Dotfiles: `/Users/a3madkour/dotfiles/`
- `org-math-lint`: `/Users/a3madkour/org/notes/tools/org-math-lint/`

**Test commands (used throughout):**
- Site linter sibling: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools/test_check_math.py -v 2>&1 | tail -15`
- Site linter `__main__`: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_math.py`
- Dotfiles ert: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -20`
- org-math-lint smoke: `/Users/a3madkour/org/notes/tools/org-math-lint/.venv/bin/python -m org_math_lint.cli check --root /Users/a3madkour/org/essays`

**Baseline counts before C:** 478 ert (post-F per [[f-complete]]) + 23 `check_citations` tests + 24 linter pairs + 1 sibling-less linter. Total CI step count: 61.
**Targets after C:** 480 ert (+2) + 6 new `check_math` tests + 25 linter pairs + 1 sibling-less linter. Total CI step count: 63.

---

## Task 1 — Site-side `tools/check_math.py` + sibling tests

**Files:**
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/check_math.py`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_check_math.py`

- [ ] **Step 1: Write the failing sibling test file**

Create `tools/test_check_math.py` with the full 6-test suite:

```python
"""Tests for check_math.py — run with:
   python3 -m unittest tools/test_check_math.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_math as lint  # noqa: E402


ESSAY_WITH_MATH = """\
---
title: "Example One"
date: 2026-04-12
draft: false
has_math: true
---

Lorem ipsum \\(\\alpha + \\beta\\) dolor.
"""

ESSAY_NO_MATH = """\
---
title: "Example Two"
date: 2026-04-13
draft: false
has_math: false
---

Lorem ipsum dolor sit amet.
"""

ESSAY_HAS_MATH_TRUE_BUT_NO_MARKERS = """\
---
title: "Example Three"
date: 2026-04-14
draft: false
has_math: true
---

Lorem ipsum dolor sit amet.
"""

ESSAY_HAS_MATH_FALSE_BUT_MARKERS_PRESENT = """\
---
title: "Example Four"
date: 2026-04-15
draft: false
has_math: false
---

Try \\(x = 1\\) here.
"""

ESSAY_NO_HAS_MATH_FIELD_BUT_MARKERS = """\
---
title: "Example Five"
date: 2026-04-16
draft: false
---

Try \\[E = mc^2\\] here.
"""

ESSAY_MATH_INSIDE_CODE_FENCE = """\
---
title: "Example Six"
date: 2026-04-17
draft: false
has_math: false
---

Lorem ipsum.

```python
# Example LaTeX in a code block — should NOT count:
# \\(x = 1\\)
```

Plain prose continues.
"""

ESSAY_DOLLAR_IN_PROSE = """\
---
title: "Example Seven"
date: 2026-04-18
draft: false
has_math: false
---

Costs $5 per month, $10/year. Discount of $100 for early signup.
"""


class MathCouplingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.essays = self.tmp / "content" / "essays"
        self.essays.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write_essay(self, slug: str, body: str) -> None:
        d = self.essays / slug
        d.mkdir()
        (d / "index.md").write_text(body)

    def test_has_math_true_with_markers_passes(self):
        self._write_essay("one", ESSAY_WITH_MATH)
        errors = lint.lint_math(self.essays)
        self.assertEqual(errors, [])

    def test_has_math_false_no_markers_passes(self):
        self._write_essay("two", ESSAY_NO_MATH)
        errors = lint.lint_math(self.essays)
        self.assertEqual(errors, [])

    def test_has_math_true_without_markers_fails(self):
        self._write_essay("three", ESSAY_HAS_MATH_TRUE_BUT_NO_MARKERS)
        errors = lint.lint_math(self.essays)
        self.assertEqual(len(errors), 1)
        self.assertIn("no math markers", errors[0])

    def test_has_math_false_with_markers_fails(self):
        self._write_essay("four", ESSAY_HAS_MATH_FALSE_BUT_MARKERS_PRESENT)
        errors = lint.lint_math(self.essays)
        self.assertEqual(len(errors), 1)
        self.assertIn("math markers found", errors[0])

    def test_has_math_missing_with_markers_fails(self):
        self._write_essay("five", ESSAY_NO_HAS_MATH_FIELD_BUT_MARKERS)
        errors = lint.lint_math(self.essays)
        self.assertEqual(len(errors), 1)
        self.assertIn("math markers found", errors[0])

    def test_math_in_code_fence_ignored(self):
        self._write_essay("six", ESSAY_MATH_INSIDE_CODE_FENCE)
        errors = lint.lint_math(self.essays)
        self.assertEqual(errors, [])

    def test_dollar_signs_in_prose_dont_trip_inline_dollar(self):
        self._write_essay("seven", ESSAY_DOLLAR_IN_PROSE)
        errors = lint.lint_math(self.essays)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test file to verify it fails (because `check_math` doesn't exist yet)**

Run:
```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools/test_check_math.py -v 2>&1 | tail -10
```

Expected: `ImportError: No module named 'check_math'` (or `ModuleNotFoundError`).

- [ ] **Step 3: Create `tools/check_math.py` with the implementation**

```python
#!/usr/bin/env python3
"""Math frontmatter coupling linter.

Validates that every essay's `has_math` frontmatter value matches whether
the rendered markdown body actually contains math markers. Source-side
syntactic validation is handled by `org-math-lint` (run pre-publish via
a3-pub.sh); this site-side check catches deploy-time regressions where
the frontmatter and the body fall out of sync (e.g., B.4's has_math
auto-derive having a bug).

Stdlib only.
Exits 0 on all-pass, 1 on any violation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


# Math markers recognized:
#   \(   inline LaTeX
#   \[   display LaTeX
#   \begin{...}  environment-based math
#   $$   display dollar (defense-in-depth; org-math-lint canonicalizes away)
# Inline single-$ recognition is handled by a separate dollar-pair test to
# avoid false-positives on prose with money amounts ($5, $10/mo, $100).
MARKER_PATTERNS = [
    re.compile(r"\\\("),
    re.compile(r"\\\["),
    re.compile(r"\\begin\{[a-zA-Z]+\*?\}"),
    re.compile(r"\$\$"),
]

# Inline dollar: a $-delimited token where the inner content looks like math
# (one or more non-space chars without an intervening digit-only prose hit).
# Conservative: require non-space immediately after the opening $, and a
# closing $ on the same line. Skips bare "$5" / "$10/mo" because the regex
# requires a closing $ before end-of-line/whitespace.
INLINE_DOLLAR = re.compile(r"\$[^\s\d$][^$\n]*\$")

CODE_FENCE = re.compile(r"^```", re.MULTILINE)


def _strip_code_fences(body: str) -> str:
    """Remove ```-fenced code blocks. Split on lines starting with ``` and keep
    only segments at even indices (text segments) — odd indices are inside fences."""
    segments = CODE_FENCE.split(body)
    return "\n".join(segments[::2])


def _body_has_math(body: str) -> bool:
    stripped = _strip_code_fences(body)
    for pat in MARKER_PATTERNS:
        if pat.search(stripped):
            return True
    if INLINE_DOLLAR.search(stripped):
        return True
    return False


def lint_math(essays_dir: Path) -> list[str]:
    """Return list of error strings. Empty list = all good."""
    errors: list[str] = []
    if not essays_dir.is_dir():
        return errors  # nothing to lint
    for d in sorted(essays_dir.iterdir()):
        if not d.is_dir():
            continue
        index = d / "index.md"
        if not index.exists():
            continue
        text = index.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm is None:
            continue  # no frontmatter to check against
        has_math = bool(fm.get("has_math", False))
        body = text.split("---", 2)[-1] if text.startswith("---") else text
        body_has = _body_has_math(body)
        rel = f"content/essays/{d.name}/index.md"
        if has_math and not body_has:
            errors.append(f"{rel}: has_math is true but no math markers found in body")
        elif not has_math and body_has:
            errors.append(f"{rel}: math markers found in body but has_math is false (or missing)")
    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    essays_dir = repo_root / "content" / "essays"
    errors = lint_math(essays_dir)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} math coupling issue(s).", file=sys.stderr)
        return 1
    print("OK — math frontmatter coupling validates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test file to verify all 6 tests pass**

Run:
```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools/test_check_math.py -v 2>&1 | tail -10
```

Expected: `Ran 7 tests in 0.0XXs` ending with `OK`. (Why 7 and not 6? The dollar-prose test is the 7th — keep counting; spec said "~6" loosely.)

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/check_math.py tools/test_check_math.py
git commit -m "$(cat <<'EOF'
feat(c): tools/check_math.py — has_math frontmatter coupling linter

25th linter pair. Validates that every essay's has_math frontmatter
value matches whether the rendered markdown body actually contains
math markers (\( / \[ / \begin{...} / $$ / inline $...$). Code-fenced
blocks are excluded from the scan; money amounts ($5, $10/mo, $100)
don't trip the inline-dollar detection.

Stdlib only; ~75 LoC linter + 7 sibling tests.

Source-side validation remains org-math-lint's job; this catches
deploy-time regressions where frontmatter and body fall out of sync
(e.g., a B.4 auto-derive bug).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2 — Retire `{{< math >}}` shortcode + convert example-one to real LaTeX

**Files:**
- Delete: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/layouts/shortcodes/math.html`
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-one/index.md`

- [ ] **Step 1: Delete the shortcode file**

Run:
```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git rm layouts/shortcodes/math.html
```

Expected: `rm 'layouts/shortcodes/math.html'`.

- [ ] **Step 2: Replace the `{{< math >}}` block in example-one with real LaTeX**

Open `content/essays/example-one/index.md`. Find the line with:

```
{{< math >}}&alpha; + &beta; = &gamma;{{< /math >}}
```

Replace with two math constructs (one inline, one display):

```
\(\alpha + \beta = \gamma\)

\[\sum_{i=1}^{n} x_i = \bar{x}\,n\]
```

Keep `has_math: true` in the frontmatter (no change there).

- [ ] **Step 3: Run check_math.py against current content to verify**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_math.py
```

Expected: `OK — math frontmatter coupling validates.` (Currently fails before example-one conversion because the old `{{< math >}}` content has no `\(` / `\[` markers but has_math is true; after conversion the markers are present.)

- [ ] **Step 4: Run the unittest sibling to verify nothing regressed**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools/test_check_math.py -v 2>&1 | tail -5
```

Expected: `Ran 7 tests in 0.0XXs` ending `OK`.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add layouts/shortcodes/math.html content/essays/example-one/index.md
git commit -m "$(cat <<'EOF'
chore(c): retire {{< math >}} shortcode + convert example-one to real LaTeX

The {{< math >}} shortcode wrapped content in <code data-math> — a pure
placeholder that wasn't the planned KaTeX rendering path. KaTeX parses
raw \(...\) / \[...\] directly from the HTML, so the shortcode added no
value.

example-one's math block becomes:
  \(\alpha + \beta = \gamma\)
  \[\sum_{i=1}^{n} x_i = \bar{x}\,n\]

has_math: true is unchanged; tools/check_math.py (25th linter pair)
now sees the markers and validates the coupling.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3 — Flip example-three `has_math: true` + add inline math marker

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-three/index.md`

- [ ] **Step 1: Change `has_math: false` → `has_math: true`**

Open `content/essays/example-three/index.md`. Frontmatter currently includes:

```
has_math: false
```

Change to:

```
has_math: true
```

- [ ] **Step 2: Add an inline math marker to the body**

The body is currently just `Lorem ipsum dolor sit amet, consectetur adipiscing elit.`. Append an inline math example so the coupling check has a second positive fixture beyond example-one:

```
Lorem ipsum dolor sit amet, consectetur adipiscing elit. The mass-energy equivalence is \(E = mc^2\).
```

- [ ] **Step 3: Run `check_math.py` to verify both essays pass**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_math.py
```

Expected: `OK — math frontmatter coupling validates.`

- [ ] **Step 4: Run the sibling tests (sanity)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools/test_check_math.py -v 2>&1 | tail -3
```

Expected: `Ran 7 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add content/essays/example-three/index.md
git commit -m "$(cat <<'EOF'
chore(c): example-three carries \(E = mc^2\); has_math: true

Gives the math coupling linter a second positive fixture beyond
example-one and asserts it scans all essays rather than only the
first match.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4 — Wire `check_math` into hugo.yaml + ci-local.sh (25th linter pair)

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/.github/workflows/hugo.yaml`
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/ci-local.sh`

- [ ] **Step 1: Add the linter-pair steps to hugo.yaml**

Open `.github/workflows/hugo.yaml`. Locate the citation pair (around line 80-83):

```yaml
      - name: Verify citations
        run: python3 tools/check_citations.py
      - name: Run citation linter unit tests
        run: python3 -m unittest tools/test_check_citations.py -v
```

Immediately after these two steps, insert:

```yaml
      - name: Verify math frontmatter coupling
        run: python3 tools/check_math.py
      - name: Run math linter unit tests
        run: python3 -m unittest tools/test_check_math.py -v
```

- [ ] **Step 2: Add the same to ci-local.sh**

Open `tools/ci-local.sh`. Locate the citations block (around line 42-43):

```bash
python3 tools/check_citations.py
python3 -m unittest tools/test_check_citations.py -v 2>&1 | tail -3
```

Add immediately after (preserving the surrounding blank-line style):

```bash

python3 tools/check_math.py
python3 -m unittest tools/test_check_math.py -v 2>&1 | tail -3
```

- [ ] **Step 3: Run the local CI to verify both steps integrate cleanly**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && bash tools/ci-local.sh 2>&1 | grep -E "check_math|math frontmatter|math linter" | head
```

Expected output includes:
```
OK — math frontmatter coupling validates.
```
plus the unittest tail (`Ran 7 tests` … `OK`).

If `ci-local.sh` exits early because of an LHCI dep (per `feedback_always_run_ci_locally`), bail out at the math step manually:

```bash
python3 tools/check_math.py && python3 -m unittest tools/test_check_math.py -v 2>&1 | tail -3
```

Same expected output as above.

- [ ] **Step 4: Verify no other linter pair was disturbed**

```bash
grep -c "Verify " .github/workflows/hugo.yaml
```

Expected: count goes from previous baseline to baseline+1.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add .github/workflows/hugo.yaml tools/ci-local.sh
git commit -m "$(cat <<'EOF'
ci(c): hugo.yaml + ci-local.sh — wire 25th linter pair (math)

Two new CI steps after the citations pair: verify check_math.py
against content/, then run the sibling unit tests. CI step count
goes 61 → 63 (per CLAUDE.md Architecture/Deployment count).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5 — CLAUDE.md "Math pipeline" architecture subsection + counts

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/CLAUDE.md`

- [ ] **Step 1: Update the linter-pair count + list in the Commands section**

Open `CLAUDE.md`. Find line ~14:

```
- Twenty-four linter pairs under `tools/check_*.py` + `tools/test_check_*.py` (CI runs each linter then its unit-test sibling): essay fixtures, essay TOC depth, garden fixtures, garden links, filter-chips config, research fixtures, research links, citations, works fixtures, works links, synced poetry, library fixtures, library links, library covers, library shelves, icon attribution, RSS XSL, garden history, streams fixtures, streams links, pagefind metadata, cite metadata, page weights, org-asset references. `tools/check_smoke.py` and `tools/check_graph_chrome.py` are sibling-less linters (no paired test file — spec §3.1: logic is too thin to warrant pairing).
```

Change `Twenty-four` → `Twenty-five` and add `math frontmatter coupling` to the comma-separated list (insert after `citations,` to group it with related concerns):

```
- Twenty-five linter pairs under `tools/check_*.py` + `tools/test_check_*.py` (CI runs each linter then its unit-test sibling): essay fixtures, essay TOC depth, garden fixtures, garden links, filter-chips config, research fixtures, research links, citations, math frontmatter coupling, works fixtures, works links, synced poetry, library fixtures, library links, library covers, library shelves, icon attribution, RSS XSL, garden history, streams fixtures, streams links, pagefind metadata, cite metadata, page weights, org-asset references. `tools/check_smoke.py` and `tools/check_graph_chrome.py` are sibling-less linters (no paired test file — spec §3.1: logic is too thin to warrant pairing).
```

- [ ] **Step 2: Update CI step count in the Deployment section**

Find line ~159:

```
... Total: 61 named steps.
```

Change `61` → `63`. The same paragraph mentions `24 linter pairs + 1 sibling-less = 50 steps`; update to `25 linter pairs + 1 sibling-less = 52 steps`.

- [ ] **Step 3: Insert the Math pipeline subsection**

Locate the existing "### Theme toggle" / "### Search modal" sibling subsections under `## Architecture`. Add a new subsection after the existing ones (before "### Content & layouts") — the exact paragraph to paste verbatim:

```markdown
### Math pipeline

Math content is authored in org-mode and validated **before publish**, not after.

1. **`org-math-lint` (pre-publish, dotfiles)** — runs against org source files; tokenizes, applies a 10-rule registry (delimiters, fragmented math, unicode → LaTeX, unknown commands), verifies each fragment by parsing it with vendored KaTeX in V8 via `py-mini-racer`. Source: `~/org/notes/tools/org-math-lint/` (not in this repo). Invoked by `a3-pub.sh` (default on; opt out via `--skip-math-check`).
2. **B.4 essays handler `has_math` scanner (dotfiles)** — buffer scan for math markers (`{{< math >}}` stub, `\(`, `\[`, `\begin{…}`) excluding fenced code blocks; sets emitted `has_math` frontmatter. `#+HUGO_HAS_MATH:` keyword acts as manual override when present.
3. **`tools/check_math.py` (site CI, 25th linter pair)** — coupling-only: every essay's `has_math` value must match whether the body actually contains math markers. Catches publish bugs the source-side validator can't see.
4. **KaTeX runtime — deferred.** No math engine ships on the site yet. When it lands, it will parse the canonical `\(...\)` / `\[...\]` forms `org-math-lint` produces.
```

- [ ] **Step 4: Verify the edits don't break the page-weight or smoke linters**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && grep -c "linter pair" CLAUDE.md
```

Expected: at least one match (the updated paragraph). The CLAUDE.md is not consumed by any linter directly — it's narrative — but sanity-check it parses:

```bash
head -20 CLAUDE.md | grep "Twenty-five"
```

Expected: line shown contains `Twenty-five linter pairs`.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(c): CLAUDE.md — Math pipeline architecture subsection + counts

- Linter-pair count: 24 → 25 (math frontmatter coupling added).
- CI step count: 61 → 63 (two new linter-pair steps in hugo.yaml).
- New "Math pipeline" Architecture subsection naming the chain:
  org source → org-math-lint → ox-hugo → has_math auto-derive (B.4)
  → site coupling check → KaTeX runtime (deferred).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6 — B.4 essays scanner: add environment-based math detection

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays.el:41-43`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays-test.el`

- [ ] **Step 1: Write the failing ert test**

Open `a3madkour-publish-essays-test.el`. Right after `scan-math-display-delim` (around line 56), insert:

```elisp
(ert-deftest a3madkour-pub-essays-test/scan-math-environment ()
  "Body contains \\begin{equation}...\\end{equation} → :has_math is t."
  (should (eq t (plist-get
                 (a3madkour-pub-essays--scan-has-flags
                  "see \\begin{equation}E = mc^2\\end{equation} here")
                 :has_math))))
```

- [ ] **Step 2: Run ert to verify the new test fails**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "scan-math-environment|Ran" | tail -5
```

Expected: the new test reports `FAILED` (because `\\begin{...}` isn't yet in the scanner disjunction).

- [ ] **Step 3: Add env detection to `--scan-has-flags`**

Open `a3madkour-publish-essays.el`. Locate lines 41-43:

```elisp
        :has_math       (and (or (string-match-p "{{< math "    body)
                                 (string-match-p "\\\\("        body)
                                 (string-match-p "\\\\\\["      body)) t)
```

Add a fourth disjunction for `\begin{<name>}` with optional `*` (KaTeX starred envs):

```elisp
        :has_math       (and (or (string-match-p "{{< math "    body)
                                 (string-match-p "\\\\("        body)
                                 (string-match-p "\\\\\\["      body)
                                 (string-match-p "\\\\begin{[a-zA-Z]+\\*?}" body)) t)
```

Also update the docstring at line 32:

```elisp
  :has_math       <- `{{< math ' OR raw KaTeX delim `\\(' OR `\\[' OR `\\begin{<env>}'
```

- [ ] **Step 4: Run ert to verify the new test passes; existing 6 math tests still pass**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "scan-math|Ran" | tail -10
```

Expected: all five `scan-math-*` tests `passed`. Overall: `Ran 479 tests` (478 + 1 new) ending `OK`.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-essays.el emacs-configs/custom/lisp/a3madkour-publish-essays-test.el
git commit -m "$(cat <<'EOF'
feat(c): B.4 essays scanner — detect \begin{<env>} math

Adds a 4th disjunction to the has_math detection in
a3madkour-pub-essays--scan-has-flags. Authors who write display math
as \begin{equation}…\end{equation} now get has_math: true emitted
without needing the manual #+HUGO_HAS_MATH: override.

KaTeX starred environments (e.g. equation*, align*) also match.

+1 ert test: scan-math-environment. 478 → 479 ert.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7 — B.4 essays scanner: exclude fenced code blocks before scanning

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays.el` (add new helper + call in `--scan-has-flags` body preparation)
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays-test.el`

- [ ] **Step 1: Write the failing ert test**

Open `a3madkour-publish-essays-test.el`. After `scan-math-environment`, insert:

```elisp
(ert-deftest a3madkour-pub-essays-test/scan-math-inside-code-fence-ignored ()
  "Body's only math marker is inside a ```-fenced code block → :has_math is nil."
  (let ((body (concat "Prose line.\n"
                      "```python\n"
                      "# illustrative LaTeX: \\(x = 1\\)\n"
                      "```\n"
                      "More prose.\n")))
    (should-not (plist-get
                 (a3madkour-pub-essays--scan-has-flags body)
                 :has_math))))
```

- [ ] **Step 2: Run ert to verify the new test fails**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "code-fence|Ran" | tail -5
```

Expected: `scan-math-inside-code-fence-ignored` reports `FAILED` (current scanner doesn't strip fences; the `\(` inside the code block triggers `has_math: t`).

- [ ] **Step 3: Add a code-fence stripper + invoke it before the has_math scan**

In `a3madkour-publish-essays.el`, immediately above `a3madkour-pub-essays--scan-has-flags` (line 24), add a new helper:

```elisp
(defun a3madkour-pub-essays--strip-code-fences (body)
  "Return BODY with `\\=```'-fenced code blocks and org `#+begin_src/example'
blocks removed.  Inline backtick spans and org `~…~' / `=…=' spans are NOT
stripped (single-line, math-rare, stripping would over-complicate the helper).

Used before the has_math marker scan so that code examples teaching LaTeX
syntax don't false-positive on \\(, \\[, or \\begin{…}."
  (let ((s body))
    ;; ```-fenced (Hugo markdown style; post-export form)
    (setq s (replace-regexp-in-string
             "```[a-zA-Z0-9_+-]*\n\\(.\\|\n\\)*?\n```" "" s t t))
    ;; #+begin_src / #+end_src (org-mode form; pre-export form)
    (setq s (replace-regexp-in-string
             "#\\+begin_src\\(.\\|\n\\)*?#\\+end_src" "" s t))
    ;; #+begin_example / #+end_example (org-mode form)
    (setq s (replace-regexp-in-string
             "#\\+begin_example\\(.\\|\n\\)*?#\\+end_example" "" s t))
    s))
```

Then modify `--scan-has-flags` to apply the stripper to BODY before the `:has_math` disjunction. Replace lines 38-45:

```elisp
(defun a3madkour-pub-essays--scan-has-flags (body)
  "Return a plist of 6 has_* booleans derived from substring scan of BODY
\(post-export markdown).

Patterns (all case-sensitive; shortcodes match the trailing space):
  :has_sidenotes  <- `{{< sidenote '
  :has_citations  <- `{{< cite '
  :has_footnotes  <- `[^N]' markdown footnote reference
  :has_math       <- `{{< math ' OR raw KaTeX delim `\\(' OR `\\[' OR `\\begin{<env>}'
                     (fenced code blocks are stripped before this scan to avoid
                     false-positives on code teaching LaTeX syntax)
  :has_widgets    <- `{{< widget '
  :has_video_sync <- `{{< video-sync '

Each value is `t' on a positive match or `nil' on no match.  Callers
merge with per-keyword `#+HUGO_HAS_<X>:' overrides (see Task 5)."
  (let ((math-body (a3madkour-pub-essays--strip-code-fences body)))
    (list :has_sidenotes  (and (string-match-p "{{< sidenote "   body) t)
          :has_citations  (and (string-match-p "{{< cite "        body) t)
          :has_footnotes  (and (string-match-p "\\[\\^[^]]+\\]"  body) t)
          :has_math       (and (or (string-match-p "{{< math "    math-body)
                                   (string-match-p "\\\\("        math-body)
                                   (string-match-p "\\\\\\["      math-body)
                                   (string-match-p "\\\\begin{[a-zA-Z]+\\*?}" math-body)) t)
          :has_widgets    (and (string-match-p "{{< widget "      body) t)
          :has_video_sync (and (string-match-p "{{< video-sync "  body) t))))
```

Note: only `:has_math` scans the stripped body. The other has_* keys keep using the unstripped body because their patterns (`{{< sidenote >}}`, footnote refs, etc.) shouldn't typically appear inside code blocks; if they did, the author has reason to inflate the has_* flag.

- [ ] **Step 4: Run ert to verify the new test passes; existing 7 math tests + 6 merge tests still pass**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "scan-math|merge|Ran" | tail -15
```

Expected: 5 `scan-math-*` tests pass (4 existing + env) plus the new code-fence test passes. Total: `Ran 480 tests` ending `OK`.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-essays.el emacs-configs/custom/lisp/a3madkour-publish-essays-test.el
git commit -m "$(cat <<'EOF'
feat(c): B.4 essays scanner — strip code fences before has_math scan

Adds a3madkour-pub-essays--strip-code-fences (handles ```-fenced Hugo
markdown blocks plus org #+begin_src / #+begin_example regions) and
applies it to the body before the has_math marker disjunction. Code
samples teaching LaTeX syntax (e.g., an essay about KaTeX) no longer
false-positive has_math: true.

Only :has_math uses the stripped body; other has_* keys keep
scanning the unstripped body (their markers are unlikely to appear
in code).

+1 ert test: scan-math-inside-code-fence-ignored. 479 → 480 ert.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8 — a3-pub.sh: math-check helper + `--skip-math-check` flag parsing

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh`

- [ ] **Step 1: Add the helper function after `a3_pub_resolve_site_data_dir`**

Open `a3-pub.sh`. Find the closing `}` of `a3_pub_resolve_site_data_dir` (around line 46). Insert a new helper function plus a per-run flag init immediately after:

```bash
# C: --skip-math-check flag init.  Default is on (run the check); the flag
# (parsed below before any intercept) flips this to skip the check.
A3_PUB_SKIP_MATH_CHECK="${A3_PUB_SKIP_MATH_CHECK:-0}"

# C: invoke `org-math-lint check --root <dir>' against the org source
# directory.  Default-on; honored unless A3_PUB_SKIP_MATH_CHECK=1.  Exits
# non-zero on validator failure or missing install (distinct exit codes
# so callers can tell them apart):
#   0  validation passed (or skipped via flag/env)
#   1  validator reported issues (stderr already detailed)
#   2  org-math-lint not installed at expected venv path
a3_pub_check_math() {
  local source_dir="$1"
  if [ "$A3_PUB_SKIP_MATH_CHECK" = "1" ]; then
    return 0
  fi
  local ml_venv="$HOME/org/notes/tools/org-math-lint/.venv/bin/python"
  if [ ! -x "$ml_venv" ]; then
    echo "a3-pub.sh: org-math-lint not installed at $ml_venv" >&2
    echo "  Install: cd ~/org/notes/tools/org-math-lint && python3 -m venv .venv && .venv/bin/pip install -e ." >&2
    echo "  Or rerun with --skip-math-check (sets A3_PUB_SKIP_MATH_CHECK=1)." >&2
    return 2
  fi
  if ! "$ml_venv" -m org_math_lint.cli check --root "$source_dir"; then
    echo "a3-pub.sh: math validation failed; publish aborted." >&2
    echo "  Fix the issues above, or rerun with --skip-math-check." >&2
    return 1
  fi
  return 0
}
```

- [ ] **Step 2: Add `--skip-math-check` flag parsing before the existing intercept blocks**

Still in `a3-pub.sh`, find the first intercept block: `if [ "${1:-}" = "--check-orphans" ]; then` (around line 50). Immediately before it, add the flag-parse loop:

```bash
# C: parse --skip-math-check anywhere in the arg list.  Done as a
# pre-pass so the rest of the intercept logic (positional <path>
# arguments, --eval pass-throughs) is unaffected.
parsed_args=()
for a in "$@"; do
  case "$a" in
    --skip-math-check) A3_PUB_SKIP_MATH_CHECK=1 ;;
    *) parsed_args+=("$a") ;;
  esac
done
set -- "${parsed_args[@]}"
```

- [ ] **Step 3: Sanity-check the flag parse doesn't break existing usage**

Run the help-ish invocation:

```bash
A3_PUB_SKIP_MATH_CHECK=1 /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --eval '(message "%s" a3madkour-pub/version)' 2>&1 | tail -3
```

Expected: still prints `[a3-pub] ready (v<...>)` and the version. The flag has no effect on `--eval` invocations because they hit the default-tail block, but the flag-parse loop must not eat the `--eval` argument.

Then try with the new flag:

```bash
/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --skip-math-check --eval '(message "skip-math test")' 2>&1 | tail -3
```

Expected: same `[a3-pub] ready` line; the flag is consumed before `--eval` reaches emacs.

- [ ] **Step 4: Confirm a3-pub.sh `bash -n` still parses**

```bash
bash -n /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh && echo "syntax OK"
```

Expected: `syntax OK`.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3-pub.sh
git commit -m "$(cat <<'EOF'
feat(c): a3-pub.sh — math-check helper + --skip-math-check flag

New a3_pub_check_math() helper invokes org-math-lint check against
the source directory using its installed venv at
~/org/notes/tools/org-math-lint/.venv/. Three distinct exit codes:
0 pass / 1 validator failure / 2 missing install.

New flag --skip-math-check (also via A3_PUB_SKIP_MATH_CHECK=1) opts
out. Flag is parsed via a pre-pass so positional <path> args and
--eval pass-throughs are unaffected.

Task 9 wires the helper into the 3 publish intercepts.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9 — a3-pub.sh: wire `a3_pub_check_math` into 3 publish intercepts

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh`

- [ ] **Step 1: Wire into `--publish-living` intercept**

Find the `--publish-living` block (around line 90). After `SITE_DATA_DIR="$(a3_pub_resolve_site_data_dir)" || exit 1` (~line 96), add:

```bash
  # C: source-side math validation before invoking emacs.
  a3_pub_check_math "$HOME/org/notes" || exit $?
```

Rationale: `--publish-living` walks org-roam-published notes under `~/org/notes/`, so that's the validation root.

- [ ] **Step 2: Wire into `--publish-deliberate <FILE>` intercept**

Find the `--publish-deliberate` block (around line 134). After `target_path="$1"` is captured but before the Emacs exec, add:

```bash
  # C: source-side math validation on the file's parent dir.
  a3_pub_check_math "$(dirname "$target_path")" || exit $?
```

Rationale: deliberate publishes operate on a single file; scoping to the parent directory (e.g., `~/org/essays/`) gives `org-math-lint` enough context (it auto-detects all `.org` files under root) without over-scoping.

- [ ] **Step 3: Wire into `--sync-citations` intercept**

Find the `--sync-citations` block (around line 182). After `SITE_DATA_DIR="$(a3_pub_resolve_site_data_dir)" || exit 1` (~line 188), add:

```bash
  # C: source-side math validation across all org dirs (sync walks the whole corpus).
  a3_pub_check_math "$HOME/org" || exit $?
```

Rationale: `--sync-citations` re-resolves every cite-key in the published corpus; the math validator runs over the same scope (`~/org/` is the umbrella).

- [ ] **Step 4: Manual smoke test — verify the wires don't break anything**

The full publish path needs Emacs + org-roam-db, which is heavy. Just smoke-test that the math-check is invoked and that `--skip-math-check` bypasses it without breaking the wire:

```bash
# With --skip-math-check: should print "[a3-pub] ready" without running validator.
/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-deliberate /Users/a3madkour/org/essays/example-one.org --skip-math-check 2>&1 | head -5
```

Expected: `[a3-pub] ready` line eventually appears (the actual publish runs in batch Emacs, may take time; you can Ctrl-C after the ready line if you don't want the full publish).

```bash
# Without --skip-math-check: validator runs. If org-math-lint catches an issue, prints it; if not, proceeds to Emacs.
/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-deliberate /Users/a3madkour/org/essays/example-one.org 2>&1 | head -5
```

Expected outcome A (org-math-lint clean): no validator stderr, proceeds to Emacs publish.
Expected outcome B (issues): org-math-lint's report on stderr, then `a3-pub.sh: math validation failed; publish aborted.`, exit 1.

If outcome B happens but you want to publish anyway, rerun with `--skip-math-check`.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3-pub.sh
git commit -m "$(cat <<'EOF'
feat(c): a3-pub.sh — wire math check into 3 publish intercepts

Each of --publish-living / --publish-deliberate <FILE> /
--sync-citations now invokes a3_pub_check_math with the appropriate
source-directory scope before launching Emacs:

  --publish-living:    ~/org/notes
  --publish-deliberate: $(dirname "$target_path")
  --sync-citations:    ~/org

Default-on; skip via --skip-math-check or A3_PUB_SKIP_MATH_CHECK=1.

Interactive M-x a3-publish-* paths remain uncovered V1 (see spec
§10 follow-up #1); if interactive publishing becomes the norm, a
parallel hook in begin-publish (elisp) is the planned follow-up.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10 — End-to-end spot-check on real corpus

**Files:**
- No code edits in this task. Output: a memory note documenting findings.

This is the equivalent of F's Task 18: drive the whole chain with real content and surface any in-slice fix-ups.

- [ ] **Step 1: Pre-flight — verify `org-math-lint` venv is healthy**

```bash
/Users/a3madkour/org/notes/tools/org-math-lint/.venv/bin/python -m org_math_lint.cli check --root /Users/a3madkour/org/essays 2>&1 | tail -10
```

Expected: either `0` exit (no issues) or a list of issues with file:line + rule ID. If the venv path doesn't exist, install per the error message and re-run.

- [ ] **Step 2: Drive a full publish-deliberate of example-one through a3-pub.sh**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-deliberate /Users/a3madkour/org/essays/example-one.org 2>&1 | tail -30
```

Expected sequence in output:
1. `org-math-lint` clean (no issues stderr).
2. Emacs publish executes; `[a3-pub] ready` line.
3. Existing F citation pipeline runs (resolves `meiRWoMRetrievalaugmentedWorld2026` cite).
4. `data/citations.yaml`, `content/essays/example-one/index.md` updated.

- [ ] **Step 3: Inspect the emitted `has_math` value**

```bash
grep -m1 "^has_math" /Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-one/index.md
```

Expected: `has_math: true` (the auto-derive should detect both the inline `\(...\)` and display `\[...\]` markers from Task 2's fixture conversion; no manual override needed).

If the emitted value is `false`, the scanner is missing one of the markers. Surface as a follow-up commit (the existing tests should have caught this; verify with `cd dotfiles/.../lisp && ./run-tests.sh 2>&1 | grep math`).

- [ ] **Step 4: Run the site-side coupling check against the freshly published essay**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_math.py
```

Expected: `OK — math frontmatter coupling validates.`

- [ ] **Step 5: Negative-path verification (one of these two; do at least one)**

Path A — inject a broken macro and verify a3-pub.sh aborts:

1. Edit `/Users/a3madkour/org/essays/example-one.org`; add `\(\textcolor{red}{x}\)` somewhere in the body (LaTeX macro not in KaTeX support table).
2. Re-run the same `a3-pub.sh --publish-deliberate ...` command.
3. Expected: `org-math-lint` reports `unknown macro \textcolor` (or similar rule output); `a3-pub.sh` prints `math validation failed; publish aborted.` and exits 1; `content/essays/example-one/index.md` and `data/citations.yaml` are NOT updated.
4. Revert the org-source edit.

Path B — flip example-three's `has_math` to `false` (revert Task 3) without removing the inline math; run `tools/check_math.py`; verify it reports the coupling error; revert the edit.

- [ ] **Step 6: Commit a memory note + any in-slice fix-ups**

If Steps 1-5 surface bugs, ship the fixes as additional commits (in either repo as appropriate), then write the memory entry. If clean, just write the memory entry.

Create `/Users/a3madkour/.claude/projects/-Users-a3madkour-Sync-Workspace-a3madkour-github-io/memory/project_c_complete.md`:

```markdown
---
name: c-complete
description: "C math validator — shipped 2026-06-XX (TBD when this lands). Integration slice; no new validator on site side. Pre-publish gate via a3-pub.sh subprocess-calling org-math-lint; B.4 scanner gained env detection + code-fence exclusion; site tools/check_math.py validates has_math ↔ body coupling on essays. 25th linter pair. CI step count 61 → 63. ert 478 → 480."
metadata:
  node_type: memory
  type: project
---

**Shipped (code-complete 2026-06-XX):** C — math validator per `docs/superpowers/specs/2026-06-01-phase-3-c-math-validator-design.md` + `docs/superpowers/plans/2026-06-01-phase-3-c-math-validator.md`. 10 tasks across 2 repos (3 dotfiles + 6 site commits + 1 spot-check).

## What ships in C

### Dotfiles
- `a3-pub.sh` — new `a3_pub_check_math()` helper + `--skip-math-check` flag; wired into `--publish-living` / `--publish-deliberate` / `--sync-citations` intercepts.
- `a3madkour-publish-essays.el` — `--scan-has-flags` extended with env detection (`\begin{<name>}` 4th disjunction) + new `--strip-code-fences` helper applied to BODY before the has_math scan.
- 2 new ert tests: `scan-math-environment`, `scan-math-inside-code-fence-ignored`.
- ert: 478 → 480.

### Site
- `tools/check_math.py` + `tools/test_check_math.py` (25th linter pair; ~75 LoC + 7 tests).
- `layouts/shortcodes/math.html` deleted.
- `content/essays/example-one/index.md` — `{{< math >}}` replaced with real `\(\alpha + \beta = \gamma\)` + `\[\sum...\]`.
- `content/essays/example-three/index.md` — `has_math: true`; inline `\(E = mc^2\)` added to body.
- `.github/workflows/hugo.yaml` — 2 new linter-pair steps (after citations). CI step count 61 → 63.
- `tools/ci-local.sh` — mirror of the same steps.
- `CLAUDE.md` — new "Math pipeline" Architecture subsection; linter-pair count 24 → 25; total step count 61 → 63.

## In-slice fix-ups

[List any commits beyond the 9 plan tasks. Examples of what to surface:
 - "Spot-check found X; shipped Y commit"
 - "Manual integration revealed Z; fixed in commit ABC"]

## Why this slice mattered

Closes the math-syntax validation gap left open since Phase 0. The site had `has_math: true` on example-one for a year but no validator to catch typos. C plugs in the validator the author already wrote (`org-math-lint`, 1.2k LoC), retires a placeholder stub, and tightens the deploy-time coupling so a future has_math regression in B.4's scanner fails CI rather than silently shipping.

## Known follow-ups (C.x)

- **Interactive `M-x a3-publish-*` paths uncovered.** Math check only runs through a3-pub.sh today.
- **`org-math-lint` venv portability.** Manual install on each dev machine; error message instructs how. If it bites repeatedly, ship a `tools/setup-org-math-lint.sh` helper.
- **Garden / research / library math.** Not validated (those sections don't carry `has_math`). Trigger to extend: a real math fixture appears in one of them.
- **KaTeX runtime itself.** Still deferred. Independent slice.
```

Also update `/Users/a3madkour/.claude/projects/-Users-a3madkour-Sync-Workspace-a3madkour-github-io/memory/MEMORY.md` — append:

```
- [C math validator — shipped](project_c_complete.md) — integration slice; org-math-lint as source-of-truth; B.4 env detection + code-fence exclusion; site coupling check (25th linter pair); CI 61→63; ert 478→480
```

And update `project_next_slice.md` — flip the pointer from C → D.

Commit:

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add .claude/memory/project_c_complete.md .claude/memory/MEMORY.md .claude/memory/project_next_slice.md
git commit -m "$(cat <<'EOF'
docs(memory): C math validator shipped — next slice D

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review checklist (for plan author / reviewer)

- [ ] Each task has 5 micro-steps ending in a commit.
- [ ] Every code block compiles / runs as-is (no `TBD` / `TODO` / `...`).
- [ ] All file paths are absolute (per F plan convention).
- [ ] Test commands include expected output.
- [ ] Type/function/variable names are consistent across tasks (e.g., `a3_pub_check_math`, `lint_math`).
- [ ] No task implements something a later task should implement.
- [ ] Spec coverage:
  - §3 (pre-publish gate) → Tasks 8 + 9.
  - §4 (scanner refinements) → Tasks 6 + 7.
  - §5 (site coupling check) → Tasks 1 + 4.
  - §6 (stub retirement + fixture conversion) → Tasks 2 + 3.
  - §7 (CLAUDE.md docs) → Task 5.
  - §8 (test plan) → distributed across Tasks 1, 6, 7, 10.
  - §10 (follow-ups) → memory note in Task 10.
  - §11 (commit shape) → 9 commits + 1 memory note across 10 tasks.

---

## Out-of-band notes for the executor

- **Task ordering matters.** Task 1 builds the linter; Task 2 makes the fixture pass it; Task 3 adds a second positive fixture; Task 4 wires CI. Running `tools/check_math.py` against `content/essays/` BETWEEN Tasks 1 and 2 will fail (correctly: example-one had `has_math: true` but no markers in the pre-T2 state). Don't be alarmed.
- **Dotfiles repo discipline.** Per [[next-slice]] and [[site-repo-staged-mess]] memos: the 5 pre-existing dirty tracked files in `~/dotfiles/` (`.gitignore`, `.zshrc`, `bookmarks`, `early-init.el`, `init.el`) are author's in-progress work — never commit them. Use `git add <specific files>` not `git add -A` / `git add .`.
- **org-math-lint may be missing on a CI-equivalent host.** The plan assumes the author's local venv. CI itself doesn't run `org-math-lint` — only the site-side coupling check. Don't try to wire `org-math-lint` into GitHub Actions.
- **No interactive Emacs needed.** All ert tests run under `cd ~/dotfiles/.../lisp && ./run-tests.sh` (the existing script). No fixtures need to be loaded interactively.
- **Push discipline.** Per F's session policy, hold push until the end of the slice (Task 10) unless the author requests otherwise. The 9 site + 3 dotfile commits stay local until then.
