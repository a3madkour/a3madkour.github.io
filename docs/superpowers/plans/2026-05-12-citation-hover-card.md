# Citation hover-card runtime — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the interactive citation hover-card runtime — a singleton popover/sheet anchored to inline `<cite>` elements that clones content from the already-rendered references list, plus a CI linter that closes the only un-linted data file in the repo.

**Architecture:** New ESM module `assets/js/citation-card.js` imported by `essay.js` (rides in the existing essay bundle, page-scoped to `/essays/`). Content cloned at runtime from `<li id="ref-KEY">` in the server-rendered references list — no JSON blob. New stdlib-only Python linter `tools/check_citations.py` validates `data/citations.yaml` shape and resolves `notes_ref` against the garden tree, wired as CI gate.

**Tech Stack:** Hugo extended (≥ 0.148.0), vanilla JS (ESM), hand-rolled CSS (single `main.css`, numbered sections), Python 3 stdlib (linter + tests).

**Spec:** `docs/superpowers/specs/2026-05-12-citation-hover-card-design.md` (commit `46491b9`).

---

## Task 1: Linter test scaffold — fixtures and helpers

**Why first:** TDD for the linter. Write all tests against a not-yet-existent `check_citations.py`; they'll all fail with `ModuleNotFoundError`. That's the "red" step.

**Files:**
- Create: `tools/test_check_citations.py`

- [ ] **Step 1: Create the test file with imports, base class, and a write_yaml helper**

```python
"""Tests for check_citations.py — run with:
   python3 -m unittest tools/test_check_citations.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_citations as lint  # noqa: E402


GARDEN_NOTE_PUBLISHED = """\
---
title: "Story atoms"
draft: false
last_modified: 2026-04-22
growth_stage: budding
---

Body.
"""

GARDEN_NOTE_DRAFT = """\
---
title: "Draft note"
draft: true
last_modified: 2026-04-22
growth_stage: seedling
---

Body.
"""


class CitationLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.garden = self.tmp / "content" / "garden"
        self.garden.mkdir(parents=True)
        self.data = self.tmp / "data"
        self.data.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write_garden(self, slug: str, body: str = GARDEN_NOTE_PUBLISHED) -> None:
        d = self.garden / slug
        d.mkdir()
        (d / "index.md").write_text(body)

    def _write_citations(self, yaml_text: str) -> Path:
        p = self.data / "citations.yaml"
        p.write_text(yaml_text)
        return p


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test file to confirm import-time failure**

Run: `python3 -m unittest tools/test_check_citations.py -v`
Expected: `ModuleNotFoundError: No module named 'check_citations'`

- [ ] **Step 3: Commit the scaffold**

```bash
git add tools/test_check_citations.py
git commit -m "$(cat <<'EOF'
test: scaffold check_citations test harness

Helpers + base class. Fails at import time until check_citations.py lands.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Linter test cases — full coverage

**Files:**
- Modify: `tools/test_check_citations.py`

- [ ] **Step 1: Add the happy-path test inside `CitationLinterTests`**

Append to the class body (before the `if __name__` block):

```python
    def test_happy_path_passes(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["Lastname, F."]
    year: 2020
    title: "Lorem ipsum"
    venue: "Journal of Examples"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(errors, [])
```

- [ ] **Step 2: Add required-field tests (one per missing field)**

```python
    def test_missing_authors_fails(self):
        self._write_citations("""\
citations:
  source-1:
    year: 2020
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("authors", errors[0])

    def test_missing_year_fails(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("year", errors[0])

    def test_missing_title_fails(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("title", errors[0])

    def test_missing_venue_fails(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("venue", errors[0])
```

- [ ] **Step 3: Add value-validation tests**

```python
    def test_empty_authors_list_rejected(self):
        self._write_citations("""\
citations:
  source-1:
    authors: []
    year: 2020
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("authors", errors[0])

    def test_year_as_string_rejected(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: "2020"
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("year", errors[0])

    def test_year_too_low_rejected(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 1499
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("year", errors[0])

    def test_year_too_high_rejected(self):
        # current_year + 3 should fail; +2 should pass.
        from datetime import date
        too_high = date.today().year + 3
        self._write_citations(f"""\
citations:
  source-1:
    authors: ["A"]
    year: {too_high}
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("year", errors[0])

    def test_non_http_url_rejected(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    url: "ftp://example.invalid/x"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("url", errors[0])

    def test_unknown_field_rejected(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    year_published: 2020
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("year_published", errors[0])

    def test_bad_key_format_rejected(self):
        self._write_citations("""\
citations:
  Bad_Key:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("Bad_Key", errors[0])
```

- [ ] **Step 4: Add notes_ref resolution tests**

```python
    def test_notes_ref_resolved_passes(self):
        self._write_garden("story-atoms")
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    notes_ref: story-atoms
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(errors, [])

    def test_notes_ref_to_missing_slug_fails(self):
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    notes_ref: does-not-exist
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("does-not-exist", errors[0])

    def test_notes_ref_to_draft_fails(self):
        self._write_garden("drafty", GARDEN_NOTE_DRAFT)
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    notes_ref: drafty
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("drafty", errors[0])
        self.assertIn("draft", errors[0].lower())

    def test_empty_notes_ref_ignored(self):
        # notes_ref: "" was the old fixture state; should not trip the linter.
        self._write_citations("""\
citations:
  source-1:
    authors: ["A"]
    year: 2020
    title: "T"
    venue: "V"
    notes_ref: ""
""")
        errors = lint.lint_citations(self.data / "citations.yaml", self.garden)
        self.assertEqual(errors, [])
```

- [ ] **Step 5: Run the suite to confirm everything fails on the missing module**

Run: `python3 -m unittest tools/test_check_citations.py -v`
Expected: all tests error out with `ModuleNotFoundError: No module named 'check_citations'`. (`ERRORS`, not `FAILURES`.)

- [ ] **Step 6: Commit**

```bash
git add tools/test_check_citations.py
git commit -m "$(cat <<'EOF'
test: citation linter spec — 16 cases

Covers required-field detection, value validation (year type + range,
authors non-empty, url scheme, unknown-field/key-format rejection), and
notes_ref resolution (happy path, missing slug, draft slug, empty
string). All currently error with ModuleNotFoundError — implementation
in next commit.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Linter implementation

**Files:**
- Create: `tools/check_citations.py`

- [ ] **Step 1: Create the linter module with the parser**

```python
#!/usr/bin/env python3
"""Citation fixture linter.

Validates `data/citations.yaml` shape and cross-references. Stdlib only.
- Required entry fields: authors (non-empty list of strings), year (int
  in [1500, current_year + 2]), title (non-empty), venue (non-empty).
- Optional: url (must be http/https), notes_ref (must resolve to a
  non-draft `content/garden/<slug>/index.md`).
- Citation keys must be lowercase kebab-case (`^[a-z0-9-]+$`).
- Unknown fields on any entry are errors.

Exits 0 on all-pass, 1 on any violation.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_scalar  # noqa: E402
from check_fixtures import parse_frontmatter  # noqa: E402


ALLOWED_FIELDS = {"authors", "year", "title", "venue", "url", "notes_ref"}
REQUIRED_FIELDS = {"authors", "year", "title", "venue"}
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ENTRY_HEADER_RE = re.compile(r"^  ([^:\s]+):\s*$")
FIELD_RE = re.compile(r"^    ([a-zA-Z_]+):\s*(.*)$")


def parse_citations_yaml(text: str) -> dict[str, dict[str, object]]:
    """Two-level parser for data/citations.yaml.

    Format:
        citations:
          <key>:
            <field>: <scalar-or-inline-array>
            ...
          <key>:
            ...

    Returns the parsed mapping. Lines that don't match expected indent
    or shape are skipped — the validator below catches shape violations.
    """
    entries: dict[str, dict[str, object]] = {}
    in_citations = False
    current_key: str | None = None
    for raw in text.splitlines():
        if raw.startswith("#") or raw.strip() == "":
            continue
        if raw.startswith("citations:"):
            in_citations = True
            continue
        if not in_citations:
            continue
        m = ENTRY_HEADER_RE.match(raw)
        if m:
            current_key = m.group(1)
            entries[current_key] = {}
            continue
        m = FIELD_RE.match(raw)
        if m and current_key is not None:
            field, value = m.group(1), m.group(2).strip()
            entries[current_key][field] = parse_scalar(value)
            continue
        # Anything else (e.g., top-level non-comment outside citations) ends the block.
        if not raw.startswith(" "):
            in_citations = False
            current_key = None
    return entries


def _is_draft(fm: dict[str, object] | None) -> bool:
    if fm is None:
        return False
    return bool(fm.get("draft", False))


def _garden_slug_state(garden_dir: Path) -> dict[str, bool]:
    """Map slug -> is_draft for every garden subdirectory with an index.md."""
    state: dict[str, bool] = {}
    if not garden_dir.is_dir():
        return state
    for d in sorted(garden_dir.iterdir()):
        if not d.is_dir():
            continue
        index = d / "index.md"
        if not index.exists():
            continue
        fm = parse_frontmatter(index.read_text(encoding="utf-8"))
        state[d.name] = _is_draft(fm)
    return state


def lint_citations(citations_yaml: Path, garden_dir: Path) -> list[str]:
    """Return list of error strings. Empty list = all good."""
    errors: list[str] = []
    if not citations_yaml.exists():
        return [f"{citations_yaml}: file not found"]

    entries = parse_citations_yaml(citations_yaml.read_text(encoding="utf-8"))
    slug_state = _garden_slug_state(garden_dir)
    current_year = date.today().year

    for key, entry in entries.items():
        prefix = f"citations.{key}"

        if not KEY_RE.match(key):
            errors.append(f"{prefix}: key must match ^[a-z0-9][a-z0-9-]*$ (got {key!r})")
            # continue validating fields anyway — surface as many errors as possible

        unknown = set(entry.keys()) - ALLOWED_FIELDS
        for u in sorted(unknown):
            errors.append(f"{prefix}: unknown field {u!r}")

        for required in sorted(REQUIRED_FIELDS):
            if required not in entry:
                errors.append(f"{prefix}: missing required field {required!r}")

        authors = entry.get("authors")
        if authors is not None:
            if not isinstance(authors, list) or len(authors) == 0:
                errors.append(f"{prefix}: authors must be a non-empty list of strings")
            else:
                for a in authors:
                    if not isinstance(a, str) or a.strip() == "":
                        errors.append(f"{prefix}: authors contains empty/non-string entry")
                        break

        year = entry.get("year")
        if year is not None:
            if not isinstance(year, int) or isinstance(year, bool):
                errors.append(f"{prefix}: year must be an integer (got {year!r})")
            elif year < 1500 or year > current_year + 2:
                errors.append(
                    f"{prefix}: year {year} out of allowed range [1500, {current_year + 2}]"
                )

        for str_field in ("title", "venue"):
            v = entry.get(str_field)
            if v is not None and (not isinstance(v, str) or v.strip() == ""):
                errors.append(f"{prefix}: {str_field} must be a non-empty string")

        url = entry.get("url")
        if url:
            if not isinstance(url, str) or not (
                url.startswith("http://") or url.startswith("https://")
            ):
                errors.append(f"{prefix}: url must start with http:// or https:// (got {url!r})")

        notes_ref = entry.get("notes_ref")
        if isinstance(notes_ref, str) and notes_ref.strip() != "":
            if notes_ref not in slug_state:
                errors.append(
                    f"{prefix}: notes_ref {notes_ref!r} does not resolve to a garden note"
                )
            elif slug_state[notes_ref]:
                errors.append(
                    f"{prefix}: notes_ref {notes_ref!r} resolves to a draft garden note"
                )

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    citations_yaml = repo_root / "data" / "citations.yaml"
    garden_dir = repo_root / "content" / "garden"

    errors = lint_citations(citations_yaml, garden_dir)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} citation issue(s).", file=sys.stderr)
        return 1
    print("OK — citations.yaml validates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Make the file executable (matches other linters)**

Run: `chmod +x tools/check_citations.py`
Expected: no output.

- [ ] **Step 3: Run unit tests — all should pass**

Run: `python3 -m unittest tools/test_check_citations.py -v`
Expected: `Ran 16 tests in <time>s` then `OK`.

- [ ] **Step 4: Run linter against the real repo — should currently FAIL on the existing fixture**

Run: `python3 tools/check_citations.py`
Expected: exit code 1 with `error: citations.example-source-2: notes_ref 'example-note-slug' does not resolve to a garden note`.

This proves the linter catches the existing broken `notes_ref`. The fix is Task 4.

- [ ] **Step 5: Commit the linter (do NOT commit the fixture fix yet — keep it atomic)**

```bash
git add tools/check_citations.py
git commit -m "$(cat <<'EOF'
tools: add check_citations linter

Stdlib-only Python linter for data/citations.yaml. Validates required
fields, year type/range, url scheme, citation-key format, and resolves
notes_ref against the garden tree (must be non-draft). Reuses
parse_scalar + parse_frontmatter from check_fixtures.py so the
two-level YAML parser stays narrow.

Fails today on the dangling example-note-slug notes_ref in the
fixtures — fixture fix lands in the next commit.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Fixture fix — update `example-source-2.notes_ref`

**Files:**
- Modify: `data/citations.yaml:17`

- [ ] **Step 1: Update the fixture**

Edit `data/citations.yaml`, change line 17 from:

```yaml
    notes_ref: "example-note-slug"
```

to:

```yaml
    notes_ref: "story-atoms"
```

- [ ] **Step 2: Re-run the linter — should now PASS**

Run: `python3 tools/check_citations.py`
Expected: `OK — citations.yaml validates.` and exit 0.

- [ ] **Step 3: Confirm the existing essay linter still passes (uses parse_citations_yaml as a key-set extractor — should be unaffected)**

Run: `python3 tools/check_fixtures.py`
Expected: exit 0.

- [ ] **Step 4: Commit**

```bash
git add data/citations.yaml
git commit -m "$(cat <<'EOF'
fixtures: point example-source-2.notes_ref at story-atoms

Was 'example-note-slug' (dangling — no such garden note). Pointing at
an existing well-connected concept note unblocks the new
check_citations linter and exercises the upcoming → related note link
in the references partial.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: CI workflow — add the two new gates

**Files:**
- Modify: `.github/workflows/hugo.yaml:74` (after the existing research-links unit-test step)

- [ ] **Step 1: Add the two new steps**

In `.github/workflows/hugo.yaml`, immediately after this block:

```yaml
      - name: Run research links linter unit tests
        run: python3 -m unittest tools/test_check_research_links.py -v
```

Insert these two new steps (preserving the same indentation):

```yaml
      - name: Verify citations
        run: python3 tools/check_citations.py
      - name: Run citation linter unit tests
        run: python3 -m unittest tools/test_check_citations.py -v
```

- [ ] **Step 2: Verify the YAML is still valid (Python's `yaml.safe_load` is not stdlib; use a syntax-only check)**

Run: `python3 -c 'import re; t = open(".github/workflows/hugo.yaml").read(); assert "Verify citations" in t and "Run citation linter unit tests" in t; print("OK")'`
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "$(cat <<'EOF'
ci: gate on check_citations + its unit tests

Slots after the research-links checks and before the Hugo build step,
mirroring the placement pattern of every other Python gate. Brings the
total to fifteen Python checks before deploy.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: References partial — add `→ related note` link

**Files:**
- Modify: `layouts/partials/essay-references.html`

- [ ] **Step 1: Update the partial**

Replace the entire file with:

```html
{{/* References list rendered at the end of the post.
     Reads keys collected by the cite shortcode via scratch. */}}
{{- $used := .Scratch.Get "cite-keys" | default slice -}}
{{- if $used -}}
  {{- $citations := site.Data.citations.citations -}}
  <section class="essay-references" aria-labelledby="references-heading">
    <h2 id="references-heading">References</h2>
    <ol>
      {{- range $used -}}
        {{- $entry := index $citations . -}}
        <li id="ref-{{ . }}">
          {{ delimit $entry.authors ", " }} ({{ $entry.year }}).
          <em>{{ $entry.title }}</em>.
          {{ $entry.venue }}.
          {{ with $entry.url }}<a href="{{ . }}" rel="noopener">→ source</a>{{ end }}
          {{ with $entry.notes_ref }}<a href="/garden/{{ . }}/" class="ref-note">→ related note</a>{{ end }}
        </li>
      {{- end -}}
    </ol>
  </section>
{{- end -}}
```

The only change is the new `{{ with $entry.notes_ref }}…{{ end }}` line. Hugo's `with` evaluates the empty string as falsy, so entries without `notes_ref` (or with `notes_ref: ""`) don't emit the extra link.

- [ ] **Step 2: Start the dev server and visit a citing essay**

Run: `hugo server --buildDrafts`

Then in a browser open `http://localhost:1313/essays/example-essay-one/` and scroll to the references list. Verify:
- Two entries (source-1 and source-2) are listed.
- `source-2` shows `→ source` followed by `→ related note` linking to `/garden/story-atoms/`.
- `source-1` shows only `→ source` (no `→ related note`).

Stop the server (Ctrl-C) before continuing.

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/essay-references.html
git commit -m "$(cat <<'EOF'
essay-references: surface notes_ref as → related note link

Hugo \`with\` makes the link conditional on a non-empty notes_ref.
Closes the only un-used field on the citation entry shape. The hover
card runtime that lands next inherits this link for free via DOM-clone.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: CSS §13 — card styles

**Files:**
- Modify: `assets/css/main.css` (append to §13, before §14 starts on line 485)

- [ ] **Step 1: Insert the card styles**

In `assets/css/main.css`, find the line `.essay-references li:target { background: rgba(107, 31, 44, 0.08); padding: 0.25rem 0.5rem; border-radius: 4px; }` (the last line of §13) and insert **after** it the following block, before the `/* ------` separator that introduces §14:

```css

/* Citation hover-card (singleton popover on desktop, bottom sheet on mobile).
 * Content is cloned at runtime from #ref-<key> by citation-card.js. */
.citation-card {
  position: absolute;
  z-index: 50;
  max-width: 320px;
  padding: 1rem 1.25rem;
  background: var(--color-stone);
  border: 1px solid var(--color-rule);
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  color: var(--color-ink);
  font-size: var(--text-sm);
  line-height: 1.5;
  transition: opacity 120ms ease-out;
}
.citation-card[hidden] { display: none; }
.citation-card em { font-style: italic; }
.citation-card a { color: var(--color-burgundy); }
.citation-card a:hover { text-decoration: underline; }
.citation-card-close {
  display: none;
}

@media (max-width: 720px) {
  .citation-card {
    position: fixed;
    left: 8px;
    right: 8px;
    bottom: 8px;
    top: auto;
    max-width: none;
    padding: 1.25rem 1.25rem 1rem;
    box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.16);
    border-radius: 8px;
  }
  .citation-card-close {
    display: block;
    position: absolute;
    top: 0.5rem;
    right: 0.75rem;
    background: none;
    border: none;
    font-size: 1.5rem;
    line-height: 1;
    color: var(--color-ink-soft);
    cursor: pointer;
    padding: 0.5rem 0.75rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .citation-card { transition: none; }
}
```

- [ ] **Step 2: Verify contrast linter still passes**

Run: `python3 tools/check-contrast.py`
Expected: exit 0 — no new pairings (only existing AAA-verified tokens used).

- [ ] **Step 3: Commit**

```bash
git add assets/css/main.css
git commit -m "$(cat <<'EOF'
css §13: citation hover-card styles

Singleton popover on desktop (max-width 320, anchored absolute,
border + shadow), bottom sheet on mobile (≤720px, fixed to viewport
bottom with close button). Uses existing tokens — no new contrast
pairings. Reduced-motion drops the fade.

The runtime that mounts and positions the card lands in the next
commit.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: JS module — `citation-card.js`

**Files:**
- Create: `assets/js/citation-card.js`
- Modify: `assets/js/essay.js`

- [ ] **Step 1: Create the runtime module**

Write `assets/js/citation-card.js`:

```javascript
// Citation hover-card runtime. Singleton card cloned from #ref-<key>;
// hover/focus on desktop, two-tap on mobile (first = card, second = jump).
//
// Guards on .essay-body + at least one .citation; bails otherwise.

const MOBILE_BREAKPOINT = 720;
const HOVER_OPEN_DELAY_MS = 150;
const HOVER_CLOSE_DELAY_MS = 200;
const VIEWPORT_PAD = 8;

let card = null;
let cardBody = null;
let closeBtn = null;
let currentCitation = null;
let lastActivatedKey = null;
let openTimer = null;
let closeTimer = null;

function reducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function isMobile() {
  return window.innerWidth <= MOBILE_BREAKPOINT;
}

function ensureCard() {
  if (card) return;
  card = document.createElement('aside');
  card.id = 'citation-card';
  card.className = 'citation-card';
  card.setAttribute('role', 'region');
  card.setAttribute('aria-label', 'Citation details');
  card.hidden = true;

  cardBody = document.createElement('div');
  cardBody.className = 'citation-card-body';

  closeBtn = document.createElement('button');
  closeBtn.type = 'button';
  closeBtn.className = 'citation-card-close';
  closeBtn.setAttribute('aria-label', 'Close citation');
  closeBtn.textContent = '×';

  card.append(cardBody, closeBtn);
  document.body.appendChild(card);

  card.addEventListener('mouseenter', () => clearTimeout(closeTimer));
  card.addEventListener('mouseleave', () => scheduleClose());
  closeBtn.addEventListener('click', hideCard);
}

function getKey(citation) {
  return citation.getAttribute('data-cite-key');
}

function populate(citation) {
  const key = getKey(citation);
  if (!key) return false;
  const refLi = document.getElementById('ref-' + key);
  if (!refLi) return false;
  cardBody.innerHTML = refLi.innerHTML;
  citation.setAttribute('aria-describedby', 'citation-card');
  currentCitation = citation;
  return true;
}

function positionDesktop(citation) {
  card.style.opacity = '0';
  card.hidden = false;
  const rect = citation.getBoundingClientRect();
  const cardRect = card.getBoundingClientRect();
  const scrollY = window.scrollY;
  const scrollX = window.scrollX;

  // Default: above the citation
  let top = rect.top + scrollY - cardRect.height - VIEWPORT_PAD;
  if (top < scrollY + VIEWPORT_PAD) {
    // Flip below
    top = rect.bottom + scrollY + VIEWPORT_PAD;
  }

  // Horizontal: center on citation, clamp to viewport
  let left = rect.left + scrollX + rect.width / 2 - cardRect.width / 2;
  const minLeft = scrollX + VIEWPORT_PAD;
  const maxLeft = scrollX + window.innerWidth - cardRect.width - VIEWPORT_PAD;
  left = Math.max(minLeft, Math.min(left, maxLeft));

  card.style.top = top + 'px';
  card.style.left = left + 'px';

  // Force layout flush, then fade in (skip transition under reduced-motion)
  if (reducedMotion()) {
    card.style.opacity = '1';
  } else {
    requestAnimationFrame(() => { card.style.opacity = '1'; });
  }
}

function positionMobile() {
  // CSS handles positioning (position: fixed, left/right/bottom). Just clear inline.
  card.style.top = '';
  card.style.left = '';
  card.style.opacity = '1';
  card.hidden = false;
}

function showCard(citation) {
  ensureCard();
  if (!populate(citation)) return;
  if (isMobile()) {
    positionMobile();
  } else {
    positionDesktop(citation);
  }
}

function hideCard() {
  if (!card) return;
  card.hidden = true;
  card.style.opacity = '';
  if (currentCitation) {
    currentCitation.removeAttribute('aria-describedby');
    currentCitation = null;
  }
  lastActivatedKey = null;
  clearTimeout(openTimer);
  clearTimeout(closeTimer);
  openTimer = closeTimer = null;
}

function scheduleClose() {
  clearTimeout(closeTimer);
  closeTimer = setTimeout(hideCard, HOVER_CLOSE_DELAY_MS);
}

function scheduleOpen(citation) {
  clearTimeout(openTimer);
  clearTimeout(closeTimer);
  openTimer = setTimeout(() => showCard(citation), HOVER_OPEN_DELAY_MS);
}

function onPointerEnter(e) {
  if (isMobile()) return;
  const citation = e.target.closest('.citation');
  if (!citation) return;
  scheduleOpen(citation);
}

function onPointerLeave(e) {
  if (isMobile()) return;
  const citation = e.target.closest('.citation');
  if (!citation) return;
  clearTimeout(openTimer);
  scheduleClose();
}

function onFocusIn(e) {
  const a = e.target;
  const citation = a.closest && a.closest('.citation');
  if (!citation) return;
  clearTimeout(closeTimer);
  showCard(citation);
}

function onFocusOut(e) {
  const citation = e.target.closest && e.target.closest('.citation');
  if (!citation) return;
  // If focus moves into the card, keep open.
  if (card && card.contains(e.relatedTarget)) return;
  hideCard();
}

function onClick(e) {
  const citation = e.target.closest('.citation');
  if (!citation) return;
  const key = getKey(citation);
  if (!key) return;

  if (isMobile()) {
    if (lastActivatedKey === key) {
      // Second tap on same citation — let click pass through to jump.
      hideCard();
      return;
    }
    e.preventDefault();
    lastActivatedKey = key;
    showCard(citation);
    return;
  }
  // Desktop: click is the user opting for the jump. Hide card and pass through.
  hideCard();
}

function onDocumentClick(e) {
  if (!card || card.hidden) return;
  if (e.target.closest('.citation') || card.contains(e.target)) return;
  hideCard();
}

function onKeydown(e) {
  if (e.key !== 'Escape') return;
  if (!card || card.hidden) return;
  const toFocus = currentCitation && currentCitation.querySelector('a');
  hideCard();
  if (toFocus) toFocus.focus();
}

function onResize() {
  if (card && !card.hidden) hideCard();
}

export function setupCitationCards() {
  const body = document.querySelector('.essay-body');
  if (!body) return;
  const citations = body.querySelectorAll('.citation');
  if (citations.length === 0) return;

  body.addEventListener('mouseover', onPointerEnter);
  body.addEventListener('mouseout', onPointerLeave);
  body.addEventListener('focusin', onFocusIn);
  body.addEventListener('focusout', onFocusOut);
  body.addEventListener('click', onClick);
  document.addEventListener('click', onDocumentClick);
  document.addEventListener('keydown', onKeydown);
  window.addEventListener('resize', onResize, { passive: true });
}
```

- [ ] **Step 2: Wire the new module into `essay.js`**

In `assets/js/essay.js`:

- Add a new import alongside the existing `filter-chips` import:

  ```javascript
  import { setupFilterChips } from './filter-chips.js';
  import { setupCitationCards } from './citation-card.js';
  ```

- Delete the entire `setupCitationHook` function (lines 70–76).
- Replace the call `setupCitationHook();` inside `init()` with `setupCitationCards();`.

After edits, the relevant region of `essay.js` should look like:

```javascript
function init() {
  if (!document.querySelector('.essay-body') && !document.querySelector('.essay-grid')) return;
  setupSidenotePopups();
  setupTocSmoothScroll();
  setupCitationCards();
  setupFilterChips({
    containerSelector: '.filter-chips',
    cardSelector: '.essay-card',
  });
}
```

- [ ] **Step 3: Start the dev server**

Run: `hugo server --buildDrafts`

(Leave it running for the spot checks in Step 4.)

- [ ] **Step 4: Spot-check on `http://localhost:1313/essays/example-essay-one/`**

The essay has two inline citations (`[Lastname & Othername 2020]` and `[Author 2024]`). Verify each of the following:

- **Desktop hover**: cursor onto a citation → after ~150ms a card appears above the citation containing the same text as the references-list entry. For `[Author 2024]`, the card includes both `→ source` and `→ related note`.
- **Move cursor into the card** → card stays.
- **Move cursor off card** → after ~200ms the card disappears.
- **Tab into the page**, keep tabbing until a citation anchor is focused (visible focus ring) → card appears with no delay.
- **Esc** while card is open → card closes, focus returns to the citation anchor.
- **Click a citation** → page jumps to the references entry at the bottom; entry is highlighted by the existing `:target` style; card is gone.
- **Resize the browser narrow (≤720px)** (Chrome devtools device mode helps), reload, **tap a citation** → card appears as a bottom sheet with a close (`×`) button visible in its top-right corner.
- **Tap the same citation again** → card disappears and the page jumps to the references entry.
- **Tap a different citation while a card is open** → card content swaps to the new entry; no flicker.
- **Tap the close button** → card hides; tapping the same citation again opens a fresh card (not "second tap").
- **Tap outside both** → card hides.

If any check fails, stop, investigate, and fix before committing. Do not commit a partial implementation.

- [ ] **Step 5: Stop the dev server**

Press Ctrl-C in the server terminal.

- [ ] **Step 6: Commit**

```bash
git add assets/js/citation-card.js assets/js/essay.js
git commit -m "$(cat <<'EOF'
js: citation hover-card runtime

Singleton card popped on hover/focus (desktop) or first tap (mobile).
Content cloned from the rendered references-list <li>, so the data
path is server-side YAML → references partial → DOM clone. Click on
desktop still jumps to references (browser default); second tap on
mobile passes through for the jump. Esc closes + restores focus.

Removes the obsolete setupCitationHook stub from essay.js. Rides the
existing essay bundle (~2 KB added; page-scoped to /essays/).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: CLAUDE.md updates

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the Commands section (add the two new lines)**

In `CLAUDE.md`, insert these two lines into the commands list immediately after the existing `tools/test_check_research_links.py` line (around line 25):

```markdown
- `python3 tools/check_citations.py` — citations data linter (CI gate)
- `python3 -m unittest tools/test_check_citations.py -v` — citation linter unit tests (CI gate)
```

- [ ] **Step 2: Update the CSS §13 description in the Architecture / CSS pipeline section**

Find the long sentence beginning `\`assets/css/main.css\` is a single hand-rolled stylesheet, organized into numbered sections (1 reset → 2 tokens → 3 typography → …)`. In the `13 citations + references` entry, replace it with: `13 citations + references (including hover-card + bottom-sheet)`.

- [ ] **Step 3: Update the deployment workflow description (line 169)**

Find the paragraph beginning `\`.github/workflows/hugo.yaml\` builds with Hugo extended...`. Update it to insert the two new checks into the chain (after `Run research links linter unit tests`) and bump the count from "thirteen" to "fifteen":

```
… → **Run research links linter unit tests** → **Verify citations** → **Run citation linter unit tests** → Build with Hugo → Upload artifact → Deploy. All fifteen Python checks must pass before the Hugo build.
```

- [ ] **Step 4: Update the deferred-features table (around line 227)**

Find the row:

```markdown
| Citation hover-card runtime | Phase 3 | `data-cite-key` hooks present in all essay citation fixtures + garden `roam_refs` field on media/reference notes |
```

Delete that row from the deferred-features table (the feature is no longer deferred).

- [ ] **Step 5: Add a Phase 3 status paragraph**

Find the `## Project status (2026-05-08)` heading near the start of the status section, and immediately before the `### Deferred features still in plan` heading (or wherever the status entries end), insert a new paragraph:

```markdown
**Phase 3 — citation hover-card runtime complete (2026-05-12).** New singleton card runtime (`assets/js/citation-card.js`, ~2 KB added to the existing essay bundle, page-scoped to `/essays/`) shows the full citation content on hover/focus (desktop) or first tap (mobile bottom sheet). Content is cloned at runtime from the server-rendered references-list `<li>` — no JSON blob, single source of truth. Mobile behavior: first tap opens the card, second tap on the same citation passes through to the references jump (preserving the existing `:target` highlight). `essay-references.html` partial now emits a `→ related note` link when `notes_ref` is set on a citation entry; `data/citations.yaml` fixture `example-source-2.notes_ref` updated from the dangling `example-note-slug` to `story-atoms`. New CI gate `tools/check_citations.py` (~140 LOC stdlib-only) validates `data/citations.yaml` shape (required fields, year type + range [1500, current_year + 2], url scheme, citation-key kebab-case format, unknown-field rejection) and resolves `notes_ref` against the garden tree; 16-test unit suite mirrors the existing linter test pattern. No template / fixture / CSS-token changes beyond the §13 card subsection. The remaining Phase 3 piece (Now widget) is still blocked on the elisp pipeline.
```

- [ ] **Step 6: Run every linter and the contrast checker to confirm nothing regressed**

Run:

```bash
python3 tools/check-contrast.py && \
python3 tools/check_fixtures.py && python3 -m unittest tools/test_check_fixtures.py -v && \
python3 tools/check_garden_fixtures.py && python3 -m unittest tools/test_check_garden_fixtures.py -v && \
python3 tools/check_garden_links.py && python3 -m unittest tools/test_check_garden_links.py -v && \
python3 tools/check_filter_chips_config.py && python3 -m unittest tools/test_check_filter_chips_config.py -v && \
python3 tools/check_research_fixtures.py && python3 -m unittest tools/test_check_research_fixtures.py -v && \
python3 tools/check_research_links.py && python3 -m unittest tools/test_check_research_links.py -v && \
python3 tools/check_citations.py && python3 -m unittest tools/test_check_citations.py -v
```

Expected: all OK, no failures, exit 0.

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
CLAUDE.md: document citation hover-card runtime slice

Adds the two new linter commands, the §13 card description, the new
Phase 3 status paragraph, the workflow gate-count bump (13→15), and
drops the deferred-features row that was previously labeled Phase 3.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Final verification + merge handoff

**Files:**
- (none — verification only)

- [ ] **Step 1: Confirm git is clean and all commits are stacked**

Run: `git status && git log --oneline master..HEAD`
Expected: working tree clean; commits listed in order: linter test scaffold → linter spec → linter implementation → fixture fix → CI gate → references partial → CSS §13 → JS runtime → CLAUDE.md.

If the work was done directly on master (no feature branch), the second command will print nothing — adjust to `git log --oneline -10`.

- [ ] **Step 2: Production-style build to catch anything dev-server forgave**

Run: `hugo --minify --gc`
Expected: builds cleanly to `public/`, no errors, no warnings.

- [ ] **Step 3: Dev-server final golden-path walk**

Run: `hugo server --buildDrafts`

Open `http://localhost:1313/essays/example-essay-one/`. Walk through one more time:

- Hover citation → card.
- Tab to citation, Esc → card closes, focus returned.
- Click citation → jump + highlight, no card.
- Narrow viewport → first tap opens sheet, second tap on same citation jumps + dismisses sheet.
- Tap close button on sheet → sheet hides.

Also visit `http://localhost:1313/essays/example-series-part-1/` (single citation) — hover works, card content correct.

Stop the server (Ctrl-C).

- [ ] **Step 4: Push and present merge options**

Per the user's standing preference: offer dev-server spot-check confirmation + a "what to eyeball" checklist before authorizing merge + push. The check above is that confirmation — proceed only if every box in step 3 ticked.

If this work was done on a feature branch, push it:

```bash
git push -u origin <branch-name>
```

If on master:

```bash
git push origin master
```

Then summarize: "Slice landed. New JS module + references partial enhancement + linter + CI gate + fixture fix + CLAUDE.md. Total ~10 commits. Want a memory-system entry written for the slice?"

---

## Verification matrix

| Verifier | Command | Owner step |
|---|---|---|
| Linter unit tests | `python3 -m unittest tools/test_check_citations.py -v` | Task 3, Step 3 |
| Linter on real fixtures | `python3 tools/check_citations.py` | Task 4, Step 2 |
| Existing linters not regressed | bundled command in Task 9, Step 6 | Task 9, Step 6 |
| Contrast checker | `python3 tools/check-contrast.py` | Task 7, Step 2 / Task 9, Step 6 |
| Hugo build | `hugo --minify --gc` | Task 10, Step 2 |
| References partial — `→ related note` | dev-server browse `/essays/example-essay-one/` | Task 6, Step 2 |
| JS runtime end-to-end | full checklist in Task 8 Step 4 + Task 10 Step 3 | Task 8 / Task 10 |

## File map

| File | Action | Purpose |
|---|---|---|
| `tools/test_check_citations.py` | create | 16 unit tests covering linter spec |
| `tools/check_citations.py` | create | Linter — validates `data/citations.yaml` |
| `data/citations.yaml` | modify | Fix dangling `notes_ref` |
| `.github/workflows/hugo.yaml` | modify | Add the two CI gates |
| `layouts/partials/essay-references.html` | modify | Emit `→ related note` when `notes_ref` set |
| `assets/css/main.css` | modify | §13 additions for card + bottom sheet |
| `assets/js/citation-card.js` | create | Singleton card runtime |
| `assets/js/essay.js` | modify | Wire `setupCitationCards`; drop legacy stub |
| `CLAUDE.md` | modify | Commands + workflow + Phase 3 status + remove deferred row |
