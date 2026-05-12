# Research surface (Slice 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `/research/` index + `/research/themes/<slug>/` + `/research/questions/<slug>/` as a working surface with 3-theme + 6-question fixture set, two new CI linters (frontmatter + cross-refs), 3 hand-authored output icons, new CSS §30, and CLAUDE.md updates. Graph deferred to Slice 2.

**Architecture:** Layouts use Hugo's cascade-based type discrimination (`type: research-theme` / `type: research-question` set on section `_index.md` files; bare section URLs hidden with `_build: render: false`). Theme pages reuse the existing `partials/garden/topic-section.html` to embed a referenced garden topic. Backlinks are computed at build time via a `partialCached` data partial that walks all pages' `.RawContent` with `findRE`. Two new Python stdlib linters validate frontmatter contracts + cross-reference resolution, both wired into the GitHub Actions workflow (gate count 9 → 11).

**Tech Stack:** Hugo extended ≥ 0.148, hand-authored CSS, hand-authored SVG, Python 3 stdlib (no deps).

**Slice spec:** `docs/superpowers/specs/2026-05-11-research-surface-design.md` (commit `b8c68f8`).

---

## File structure

**New Python tools** (stdlib only, share `parse_frontmatter` from `check_fixtures.py`):
- `tools/check_research_fixtures.py` — validates theme + question frontmatter contracts.
- `tools/test_check_research_fixtures.py` — unit tests via tempdir fixtures.
- `tools/check_research_links.py` — validates cross-reference resolution (theme/parent_question/supporting_notes/related_essays/garden_topic_ref).
- `tools/test_check_research_links.py` — unit tests via tempdir fixtures.

**New content** (fixtures):
- `content/research/_index.md` — section index (replaces the "Coming soon" stub).
- `content/research/themes/_index.md` — `cascade: { type: research-theme }` + `_build: render: false`.
- `content/research/questions/_index.md` — `cascade: { type: research-question }` + `_build: render: false`.
- `content/research/themes/{memory-and-play,procedural-narrative,save-game-as-form}/index.md` — 3 theme fixtures.
- `content/research/questions/{6 question slugs}/index.md` — 6 question fixtures.

**New SVG icons** (hand-authored, ~24×24 viewBox, `currentColor` stroke, stage-glyph style):
- `assets/images/icons/output-paper.svg`
- `assets/images/icons/output-talk.svg`
- `assets/images/icons/output-code.svg`

**New layouts:**
- `layouts/research/list.html` — `/research/` index (theme cards grid + filter chips).
- `layouts/research-theme/single.html` — theme page (research framing + optional garden embed).
- `layouts/research-question/single.html` — question hub (full sections per spec §3.3).

**New partials:**
- `layouts/partials/research/status-pill.html` — small badge component (active/dormant/answered).
- `layouts/partials/research/output-item.html` — single output entry (icon + title + url + year).
- `layouts/partials/research/theme-card.html` — single theme card (used by the index grid).
- `layouts/partials/research/backlinks-data.html` — build-time JSON map of question slug → backlinking pages. `partialCached`.

**Modified:**
- `assets/css/main.css` — append §30 "Research" (~200 lines).
- `.github/workflows/hugo.yaml` — add 4 new linter steps (becomes 11 Python checks).
- `CLAUDE.md` — layouts list, partials list, fixtures/contract notes, status update.

**Not touched:**
- `hugo.yaml` (cascade handles type lookup).
- `data/` (research is content-driven, no data files).
- `assets/js/` (no JS in Slice 1; graph runtime = Slice 2).
- Existing garden / essays / about layouts.
- Existing 5 linters or `tools/check_fixtures.py` (imported only).

---

## Task 0: Create feature branch

**Files:** none

- [ ] **Step 1: Confirm clean tree on master**

Run: `git status && git rev-parse --abbrev-ref HEAD`
Expected: `nothing to commit, working tree clean` and `master`.

- [ ] **Step 2: Create + check out the branch**

Run: `git checkout -b research-surface`
Expected: `Switched to a new branch 'research-surface'`

---

## Task 1: Implement `check_research_fixtures.py`

**Files:**
- Create: `tools/check_research_fixtures.py`

- [ ] **Step 1: Write the linter**

Create `tools/check_research_fixtures.py` with this content:

```python
#!/usr/bin/env python3
"""Research fixture frontmatter linter.

Validates theme and question frontmatter contracts per spec §3.1
(2026-05-11 research surface slice). Imports parse_frontmatter from
check_fixtures so all linters share one YAML parser.

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


STATUSES = {"active", "dormant", "answered"}
OUTPUT_KINDS = {"paper", "talk", "code"}

THEME_REQUIRED = {"title", "status", "tags", "last_modified", "description", "weight"}
THEME_OPTIONAL = {"garden_topic_ref", "summary"}
THEME_FORBIDDEN = {"parent_question", "theme"}

QUESTION_REQUIRED = {"title", "theme", "status", "last_modified", "description"}
QUESTION_OPTIONAL = {
    "parent_question", "started", "tags",
    "supporting_notes", "related_essays", "outputs", "weight",
}


def lint_theme(theme_dir: Path) -> list[str]:
    """Return list of error strings for one theme dir."""
    errors: list[str] = []
    md = theme_dir / "index.md"
    if not md.exists():
        return [f"{theme_dir}: no index.md"]
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return [f"{md}: no frontmatter"]

    for field in sorted(THEME_REQUIRED - fm.keys()):
        errors.append(f"{md}: missing required field '{field}'")

    for field in sorted(THEME_FORBIDDEN & fm.keys()):
        errors.append(f"{md}: forbidden field '{field}' on theme")

    allowed = THEME_REQUIRED | THEME_OPTIONAL
    for field in sorted(fm.keys() - allowed):
        errors.append(f"{md}: unknown field '{field}'")

    status = fm.get("status")
    if status and status not in STATUSES:
        errors.append(f"{md}: status='{status}' not in {sorted(STATUSES)}")

    weight = fm.get("weight")
    if weight is not None and not isinstance(weight, int):
        errors.append(f"{md}: weight must be an integer, got {type(weight).__name__}")

    tags = fm.get("tags")
    if tags is not None and not isinstance(tags, list):
        errors.append(f"{md}: tags must be a list")
    elif isinstance(tags, list):
        for i, t in enumerate(tags):
            if not isinstance(t, str):
                errors.append(f"{md}: tags[{i}] must be a string")

    return errors


def lint_question(question_dir: Path) -> list[str]:
    """Return list of error strings for one question dir."""
    errors: list[str] = []
    md = question_dir / "index.md"
    if not md.exists():
        return [f"{question_dir}: no index.md"]
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return [f"{md}: no frontmatter"]

    for field in sorted(QUESTION_REQUIRED - fm.keys()):
        errors.append(f"{md}: missing required field '{field}'")

    allowed = QUESTION_REQUIRED | QUESTION_OPTIONAL
    for field in sorted(fm.keys() - allowed):
        errors.append(f"{md}: unknown field '{field}'")

    status = fm.get("status")
    if status and status not in STATUSES:
        errors.append(f"{md}: status='{status}' not in {sorted(STATUSES)}")

    outputs = fm.get("outputs")
    if outputs is not None:
        if not isinstance(outputs, list):
            errors.append(f"{md}: outputs must be a list")
        else:
            for i, o in enumerate(outputs):
                if not isinstance(o, dict):
                    errors.append(f"{md}: outputs[{i}] must be a mapping")
                    continue
                kind = o.get("kind")
                if kind not in OUTPUT_KINDS:
                    errors.append(
                        f"{md}: outputs[{i}].kind='{kind}' not in {sorted(OUTPUT_KINDS)}"
                    )
                year = o.get("year")
                if not isinstance(year, int) or not (1900 <= year <= 2100):
                    errors.append(
                        f"{md}: outputs[{i}].year must be a 4-digit int, got {year!r}"
                    )
                title = o.get("title")
                if not isinstance(title, str) or not title.strip():
                    errors.append(f"{md}: outputs[{i}].title must be non-empty string")
                url = o.get("url")
                if not isinstance(url, str) or not url.strip():
                    errors.append(f"{md}: outputs[{i}].url must be non-empty string")

    for list_field in ("tags", "supporting_notes", "related_essays"):
        val = fm.get(list_field)
        if val is not None and not isinstance(val, list):
            errors.append(f"{md}: {list_field} must be a list")

    weight = fm.get("weight")
    if weight is not None and not isinstance(weight, int):
        errors.append(f"{md}: weight must be an integer")

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    themes_dir = repo_root / "content" / "research" / "themes"
    questions_dir = repo_root / "content" / "research" / "questions"

    if not themes_dir.is_dir() or not questions_dir.is_dir():
        print(
            f"error: missing {themes_dir} or {questions_dir}", file=sys.stderr
        )
        return 1

    errors: list[str] = []
    for d in sorted(themes_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        errors.extend(lint_theme(d))
    for d in sorted(questions_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        errors.extend(lint_question(d))

    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} problem(s).", file=sys.stderr)
        return 1

    print("All research fixtures pass linter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x tools/check_research_fixtures.py`

- [ ] **Step 3: Smoke-run (no fixtures yet — the directories don't exist)**

Run: `python3 tools/check_research_fixtures.py 2>&1 | head -3`
Expected: `error: missing .../content/research/themes or .../content/research/questions` and exit code 1. That's the desired behavior when content dirs don't exist; later tasks create them and the smoke run passes.

- [ ] **Step 4: Commit**

```bash
git add tools/check_research_fixtures.py
git commit -m "Research linter: validate theme + question frontmatter

Stdlib-only. Shares parse_frontmatter with the other linters via
import. Validates required/optional/forbidden fields, status enum,
output kind enum, year range, tag/list types. Fails if fixtures
dir is missing (caught on first CI run after merge — fixtures
arrive in a later task)."
```

---

## Task 2: Unit tests for `check_research_fixtures.py`

**Files:**
- Create: `tools/test_check_research_fixtures.py`

- [ ] **Step 1: Write the test file**

Create `tools/test_check_research_fixtures.py`:

```python
"""Tests for check_research_fixtures.py — run with:
   python3 -m unittest tools/test_check_research_fixtures.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_research_fixtures as lint  # noqa: E402


THEME_OK = """\
---
title: "Memory and play"
status: active
tags: [memory, play]
last_modified: 2026-05-11
description: "Theme framing."
weight: 10
---

Body.
"""

THEME_MISSING_REQUIRED = """\
---
title: "Memory and play"
last_modified: 2026-05-11
description: "Theme framing."
weight: 10
---
"""

THEME_BAD_STATUS = """\
---
title: "Memory and play"
status: pondering
tags: [memory]
last_modified: 2026-05-11
description: "Theme framing."
weight: 10
---
"""

THEME_FORBIDDEN_PARENT_QUESTION = """\
---
title: "Memory and play"
status: active
tags: [memory]
last_modified: 2026-05-11
description: "Theme framing."
weight: 10
parent_question: some-question
---
"""

THEME_BAD_WEIGHT = """\
---
title: "Memory and play"
status: active
tags: [memory]
last_modified: 2026-05-11
description: "Theme framing."
weight: high
---
"""


QUESTION_OK = """\
---
title: "How do readers form narrative?"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "Question framing."
supporting_notes: [story-atoms]
outputs:
  - { kind: paper, title: "Paper", url: "https://x", year: 2025 }
---

Body.
"""

QUESTION_MISSING_THEME = """\
---
title: "Q"
status: active
last_modified: 2026-05-11
description: "..."
---
"""

QUESTION_BAD_OUTPUT_KIND = """\
---
title: "Q"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
outputs:
  - { kind: poster, title: "X", url: "https://x", year: 2025 }
---
"""

QUESTION_BAD_OUTPUT_YEAR = """\
---
title: "Q"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
outputs:
  - { kind: paper, title: "X", url: "https://x", year: "2025" }
---
"""

QUESTION_UNKNOWN_FIELD = """\
---
title: "Q"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
nonsense: yes
---
"""


def _write(parent: Path, name: str, body: str) -> None:
    d = parent / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.md").write_text(body)


class LintThemeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_valid_theme_no_errors(self):
        _write(self.tmp, "memory-and-play", THEME_OK)
        self.assertEqual([], lint.lint_theme(self.tmp / "memory-and-play"))

    def test_missing_required_fields(self):
        _write(self.tmp, "memory-and-play", THEME_MISSING_REQUIRED)
        errs = lint.lint_theme(self.tmp / "memory-and-play")
        joined = "\n".join(errs)
        self.assertIn("missing required field 'status'", joined)
        self.assertIn("missing required field 'tags'", joined)

    def test_bad_status_enum(self):
        _write(self.tmp, "memory-and-play", THEME_BAD_STATUS)
        errs = lint.lint_theme(self.tmp / "memory-and-play")
        self.assertTrue(any("status='pondering'" in e for e in errs))

    def test_forbidden_field_parent_question(self):
        _write(self.tmp, "memory-and-play", THEME_FORBIDDEN_PARENT_QUESTION)
        errs = lint.lint_theme(self.tmp / "memory-and-play")
        self.assertTrue(any("forbidden field 'parent_question'" in e for e in errs))

    def test_bad_weight_type(self):
        _write(self.tmp, "memory-and-play", THEME_BAD_WEIGHT)
        errs = lint.lint_theme(self.tmp / "memory-and-play")
        self.assertTrue(any("weight must be an integer" in e for e in errs))


class LintQuestionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_valid_question_no_errors(self):
        _write(self.tmp, "q-slug", QUESTION_OK)
        self.assertEqual([], lint.lint_question(self.tmp / "q-slug"))

    def test_missing_theme(self):
        _write(self.tmp, "q-slug", QUESTION_MISSING_THEME)
        errs = lint.lint_question(self.tmp / "q-slug")
        self.assertTrue(any("missing required field 'theme'" in e for e in errs))

    def test_bad_output_kind(self):
        _write(self.tmp, "q-slug", QUESTION_BAD_OUTPUT_KIND)
        errs = lint.lint_question(self.tmp / "q-slug")
        self.assertTrue(any("outputs[0].kind='poster'" in e for e in errs))

    def test_bad_output_year_type(self):
        _write(self.tmp, "q-slug", QUESTION_BAD_OUTPUT_YEAR)
        errs = lint.lint_question(self.tmp / "q-slug")
        self.assertTrue(any("outputs[0].year must be a 4-digit int" in e for e in errs))

    def test_unknown_field(self):
        _write(self.tmp, "q-slug", QUESTION_UNKNOWN_FIELD)
        errs = lint.lint_question(self.tmp / "q-slug")
        self.assertTrue(any("unknown field 'nonsense'" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests**

Run: `python3 -m unittest tools/test_check_research_fixtures.py -v 2>&1 | tail -10`
Expected: `Ran 10 tests in <X>s` and `OK`.

- [ ] **Step 3: Commit**

```bash
git add tools/test_check_research_fixtures.py
git commit -m "Research fixture linter: unit tests

10 tests across LintThemeTests + LintQuestionTests covering valid
cases, missing required fields, bad status enum, forbidden fields,
bad output kind/year, unknown fields. Uses tempdir fixtures."
```

---

## Task 3: Implement `check_research_links.py`

**Files:**
- Create: `tools/check_research_links.py`

- [ ] **Step 1: Write the cross-reference linter**

Create `tools/check_research_links.py`:

```python
#!/usr/bin/env python3
"""Research cross-reference linter.

Validates that:
  - A theme's garden_topic_ref (if set) resolves to a non-draft garden note
    that has topic_map declared.
  - A question's theme resolves to an existing theme.
  - A question's parent_question (if set) resolves to an existing question
    in the same theme.
  - Every entry in a question's supporting_notes resolves to a non-draft
    garden note.
  - Every entry in a question's related_essays resolves to a non-draft
    essay page.

Exits 0 on success, 1 on any unresolved reference. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


def _load_slug_map(root: Path) -> dict[str, dict]:
    """slug -> frontmatter dict, for direct children of root that have index.md."""
    out: dict[str, dict] = {}
    if not root.is_dir():
        return out
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        md = d / "index.md"
        if not md.exists():
            continue
        fm = parse_frontmatter(md.read_text()) or {}
        out[d.name] = fm
    return out


def lint_research_links(
    themes_dir: Path,
    questions_dir: Path,
    garden_dir: Path,
    essays_dir: Path,
) -> list[str]:
    errors: list[str] = []

    themes = _load_slug_map(themes_dir)
    questions = _load_slug_map(questions_dir)
    garden = _load_slug_map(garden_dir)
    essays = _load_slug_map(essays_dir)

    # Themes: garden_topic_ref must resolve to a non-draft garden note with topic_map.
    for slug, fm in themes.items():
        ref = fm.get("garden_topic_ref")
        if not ref:
            continue
        if ref not in garden:
            errors.append(
                f"themes/{slug}: garden_topic_ref='{ref}' does not resolve to a garden note"
            )
            continue
        gfm = garden[ref]
        if gfm.get("draft"):
            errors.append(
                f"themes/{slug}: garden_topic_ref='{ref}' resolves to a draft note"
            )
        if not gfm.get("topic_map"):
            errors.append(
                f"themes/{slug}: garden_topic_ref='{ref}' resolves to a note without topic_map"
            )

    # Questions: theme + parent_question + supporting_notes + related_essays.
    for slug, fm in questions.items():
        theme_slug = fm.get("theme")
        if theme_slug and theme_slug not in themes:
            errors.append(
                f"questions/{slug}: theme='{theme_slug}' does not resolve to an existing theme"
            )

        parent = fm.get("parent_question")
        if parent:
            if parent not in questions:
                errors.append(
                    f"questions/{slug}: parent_question='{parent}' does not resolve"
                )
            else:
                parent_theme = questions[parent].get("theme")
                if parent_theme != theme_slug:
                    errors.append(
                        f"questions/{slug}: parent_question='{parent}' is in theme "
                        f"'{parent_theme}', not '{theme_slug}'"
                    )

        for target in fm.get("supporting_notes") or []:
            if target not in garden:
                errors.append(
                    f"questions/{slug}: supporting_notes entry '{target}' "
                    f"does not resolve to a garden note"
                )
            elif garden[target].get("draft"):
                errors.append(
                    f"questions/{slug}: supporting_notes entry '{target}' resolves to a draft"
                )

        for target in fm.get("related_essays") or []:
            if target not in essays:
                errors.append(
                    f"questions/{slug}: related_essays entry '{target}' "
                    f"does not resolve to an essay"
                )
            elif essays[target].get("draft"):
                errors.append(
                    f"questions/{slug}: related_essays entry '{target}' resolves to a draft"
                )

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    themes_dir = repo_root / "content" / "research" / "themes"
    questions_dir = repo_root / "content" / "research" / "questions"
    garden_dir = repo_root / "content" / "garden"
    essays_dir = repo_root / "content" / "essays"

    if not themes_dir.is_dir() or not questions_dir.is_dir():
        print(
            f"error: missing {themes_dir} or {questions_dir}", file=sys.stderr
        )
        return 1

    errors = lint_research_links(themes_dir, questions_dir, garden_dir, essays_dir)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} broken reference(s).", file=sys.stderr)
        return 1

    n_themes = len([d for d in themes_dir.iterdir() if d.is_dir() and not d.name.startswith("_")])
    n_questions = len(
        [d for d in questions_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
    )
    print(f"OK — verified {n_themes} theme(s), {n_questions} question(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x tools/check_research_links.py`

- [ ] **Step 3: Smoke-run (still no fixtures yet)**

Run: `python3 tools/check_research_links.py 2>&1 | head -3`
Expected: `error: missing .../themes or .../questions` (same shape as Task 1's smoke).

- [ ] **Step 4: Commit**

```bash
git add tools/check_research_links.py
git commit -m "Research links linter: validate cross-references

Stdlib-only. Resolves garden_topic_ref → garden topic-map note,
theme → theme, parent_question → same-theme question,
supporting_notes → garden, related_essays → essays. Imports
parse_frontmatter from check_fixtures."
```

---

## Task 4: Unit tests for `check_research_links.py`

**Files:**
- Create: `tools/test_check_research_links.py`

- [ ] **Step 1: Write the test file**

Create `tools/test_check_research_links.py`:

```python
"""Tests for check_research_links.py — run with:
   python3 -m unittest tools/test_check_research_links.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_research_links as lint  # noqa: E402


THEME_OK = """\
---
title: "Memory and play"
status: active
tags: [memory]
last_modified: 2026-05-11
description: "..."
weight: 10
garden_topic_ref: memory-in-play
---
"""

THEME_NO_REF = """\
---
title: "Save-game as form"
status: answered
tags: [aesthetics]
last_modified: 2026-05-11
description: "..."
weight: 30
---
"""

GARDEN_TOPIC_MAP_NOTE = """\
---
title: "Memory in play"
draft: false
last_modified: 2026-05-11
growth_stage: evergreen
topic_map: [story-atoms]
---
"""

GARDEN_PLAIN_NOTE = """\
---
title: "Story atoms"
draft: false
last_modified: 2026-05-11
growth_stage: budding
---
"""

GARDEN_DRAFT_NOTE = """\
---
title: "Draft"
draft: true
last_modified: 2026-05-11
growth_stage: seedling
---
"""

QUESTION_OK = """\
---
title: "How do readers form narrative?"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
supporting_notes: [story-atoms]
---
"""

QUESTION_BAD_THEME = """\
---
title: "Q"
theme: nonexistent-theme
status: active
last_modified: 2026-05-11
description: "..."
---
"""

QUESTION_BAD_SUPPORTING = """\
---
title: "Q"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
supporting_notes: [does-not-exist]
---
"""

QUESTION_PARENT_WRONG_THEME = """\
---
title: "Q"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "..."
parent_question: stranger-q
---
"""

QUESTION_STRANGER = """\
---
title: "Stranger"
theme: save-game-as-form
status: active
last_modified: 2026-05-11
description: "..."
---
"""


ESSAY_OK = """\
---
title: "Example"
date: 2026-05-11
lastmod: 2026-05-11
draft: false
summary: "..."
tags: []
series: ""
series_order: 0
toc: false
has_sidenotes: false
has_citations: false
has_footnotes: false
has_math: false
has_widgets: false
has_video_sync: false
---
"""


def _write(parent: Path, name: str, body: str) -> None:
    d = parent / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.md").write_text(body)


class CrossRefTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.themes = self.tmp / "themes"
        self.questions = self.tmp / "questions"
        self.garden = self.tmp / "garden"
        self.essays = self.tmp / "essays"
        for d in (self.themes, self.questions, self.garden, self.essays):
            d.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_valid_setup_no_errors(self):
        _write(self.themes, "memory-and-play", THEME_OK)
        _write(self.questions, "q-slug", QUESTION_OK)
        _write(self.garden, "memory-in-play", GARDEN_TOPIC_MAP_NOTE)
        _write(self.garden, "story-atoms", GARDEN_PLAIN_NOTE)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertEqual([], errs)

    def test_dangling_garden_topic_ref(self):
        _write(self.themes, "memory-and-play", THEME_OK)
        # no memory-in-play garden note created
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("garden_topic_ref='memory-in-play' does not resolve" in e for e in errs))

    def test_garden_topic_ref_without_topic_map(self):
        _write(self.themes, "memory-and-play", THEME_OK)
        # memory-in-play exists but has no topic_map declared
        _write(self.garden, "memory-in-play", GARDEN_PLAIN_NOTE)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("without topic_map" in e for e in errs))

    def test_garden_topic_ref_to_draft(self):
        _write(self.themes, "memory-and-play", THEME_OK)
        _write(self.garden, "memory-in-play", GARDEN_DRAFT_NOTE)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("resolves to a draft" in e for e in errs))

    def test_theme_no_ref_is_fine(self):
        _write(self.themes, "save-game-as-form", THEME_NO_REF)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertEqual([], errs)

    def test_question_bad_theme(self):
        _write(self.themes, "memory-and-play", THEME_NO_REF)
        _write(self.questions, "q-slug", QUESTION_BAD_THEME)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("theme='nonexistent-theme'" in e for e in errs))

    def test_question_bad_supporting_note(self):
        _write(self.themes, "memory-and-play", THEME_NO_REF)
        _write(self.questions, "q-slug", QUESTION_BAD_SUPPORTING)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("supporting_notes entry 'does-not-exist'" in e for e in errs))

    def test_parent_question_wrong_theme(self):
        _write(self.themes, "memory-and-play", THEME_NO_REF)
        _write(self.themes, "save-game-as-form", THEME_NO_REF)
        _write(self.questions, "q-slug", QUESTION_PARENT_WRONG_THEME)
        _write(self.questions, "stranger-q", QUESTION_STRANGER)
        errs = lint.lint_research_links(
            self.themes, self.questions, self.garden, self.essays
        )
        self.assertTrue(any("is in theme 'save-game-as-form', not 'memory-and-play'" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests**

Run: `python3 -m unittest tools/test_check_research_links.py -v 2>&1 | tail -10`
Expected: `Ran 8 tests in <X>s` and `OK`.

- [ ] **Step 3: Commit**

```bash
git add tools/test_check_research_links.py
git commit -m "Research links linter: unit tests

8 cross-reference scenarios: valid setup, dangling garden_topic_ref,
garden_topic_ref without topic_map, draft target, theme-with-no-ref,
bad theme on question, bad supporting_notes entry, parent_question
pointing to different theme. Tempdir-based fixtures."
```

---

## Task 5: Section scaffolding (research/_index.md + cascade indices)

**Files:**
- Modify: `content/research/_index.md`
- Create: `content/research/themes/_index.md`
- Create: `content/research/questions/_index.md`

- [ ] **Step 1: Replace `content/research/_index.md`**

Write to `content/research/_index.md`:

```markdown
---
title: 'Research'
description: 'Active research questions and themes.'
---

Threads I am pulling on. Each theme links a clutch of questions; each question links the garden notes, essays, and outputs that support it.
```

- [ ] **Step 2: Create `content/research/themes/_index.md`**

```markdown
---
title: 'Research themes'
cascade:
  type: research-theme
_build:
  render: false
  list: never
---
```

- [ ] **Step 3: Create `content/research/questions/_index.md`**

```markdown
---
title: 'Research questions'
cascade:
  type: research-question
_build:
  render: false
  list: never
---
```

- [ ] **Step 4: Verify Hugo still builds (no layouts yet — falls back to defaults)**

Run: `hugo --quiet 2>&1 | head -5`
Expected: builds without errors. `/research/themes/` and `/research/questions/` won't be in the output (`_build: render: false`).

Run: `ls public/research/themes/ 2>&1`
Expected: `ls: cannot access ...: No such file or directory` (the directory doesn't exist because the section pages aren't rendered).

- [ ] **Step 5: Commit**

```bash
git add content/research/_index.md content/research/themes/_index.md content/research/questions/_index.md
git commit -m "Research section scaffolding: _index files + cascade

content/research/_index.md replaces the 'Coming soon' stub.
themes/_index.md and questions/_index.md set type via cascade and
hide the bare section URLs with _build: render: false."
```

---

## Task 6: Theme fixtures (3 themes)

**Files:**
- Create: `content/research/themes/memory-and-play/index.md`
- Create: `content/research/themes/procedural-narrative/index.md`
- Create: `content/research/themes/save-game-as-form/index.md`

- [ ] **Step 1: Write `memory-and-play/index.md`**

Create `content/research/themes/memory-and-play/index.md`:

```markdown
---
title: "Memory and play"
status: active
tags: [memory, play]
last_modified: 2026-05-11
description: "How readers and players assemble fragments into story; what 'remembering a game' means."
weight: 10
garden_topic_ref: memory-in-play
summary: "An umbrella thread for several questions about recall, narrative assembly, and what counts as having played something."
---

Example 1. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
```

- [ ] **Step 2: Write `procedural-narrative/index.md`**

Create `content/research/themes/procedural-narrative/index.md`:

```markdown
---
title: "Procedural narrative"
status: dormant
tags: [narrative, procedural]
last_modified: 2026-05-11
description: "When generated text can carry a throughline, and what breaks when it can't."
weight: 20
garden_topic_ref: procedural-narrative
---

Example 2. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
```

- [ ] **Step 3: Write `save-game-as-form/index.md`**

Create `content/research/themes/save-game-as-form/index.md`:

```markdown
---
title: "Save-game as form"
status: answered
tags: [aesthetics, games]
last_modified: 2026-05-11
description: "What it means aesthetically when the act of saving a game is itself part of the work."
weight: 30
---

Example 3. Lorem ipsum dolor sit amet.
```

(Note: no `garden_topic_ref` — exercises the "without garden topic" variant.)

- [ ] **Step 4: Run the fixture linter**

Run: `python3 tools/check_research_fixtures.py`
Expected: ⚠️ may print "missing .../questions" — that's fine until Task 7 adds question fixtures. If it prints any theme-related error, fix and re-run.

To verify themes specifically:
Run: `python3 -c "
import sys; sys.path.insert(0, 'tools')
from pathlib import Path
from check_research_fixtures import lint_theme
for d in sorted(Path('content/research/themes').iterdir()):
    if d.is_dir() and not d.name.startswith('_'):
        errs = lint_theme(d)
        print(d.name, '→', 'OK' if not errs else errs)
"`
Expected: three lines, each `<slug> → OK`.

- [ ] **Step 5: Commit**

```bash
git add content/research/themes
git commit -m "Research theme fixtures: 3 themes covering all variants

memory-and-play (active, with garden_topic_ref + summary);
procedural-narrative (dormant, with garden_topic_ref, no summary);
save-game-as-form (answered, no garden_topic_ref). Filler bodies."
```

---

## Task 7: Question fixtures (6 questions)

**Files:**
- Create: 6 × `content/research/questions/<slug>/index.md`

- [ ] **Step 1: Write `how-do-readers-form-narrative-from-shuffle/index.md`**

```markdown
---
title: "How do readers form narrative from shuffle?"
theme: memory-and-play
status: active
last_modified: 2026-05-11
started: 2025-09-01
description: "Top-level question for the memory-and-play theme."
tags: [memory, narrative]
supporting_notes: [story-atoms, salience-and-memory]
related_essays: [example-essay-one]
outputs:
  - { kind: paper, title: "Example Paper Title", url: "https://example.com/paper", year: 2025 }
  - { kind: talk,  title: "Example Talk Title",  url: "https://example.com/talk",  year: 2024 }
weight: 10
---

Example 1. Lorem ipsum dolor sit amet. The current thinking on this question is consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
```

- [ ] **Step 2: Write `what-counts-as-story-recall/index.md`**

```markdown
---
title: "What counts as story recall?"
theme: memory-and-play
status: active
last_modified: 2026-05-11
description: "Sub-question of how-do-readers-form-narrative-from-shuffle."
tags: [memory, narrative]
parent_question: how-do-readers-form-narrative-from-shuffle
supporting_notes: [recall-vs-replay]
weight: 20
---

Example 2. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
```

- [ ] **Step 3: Write `when-does-replay-feel-like-cheating/index.md`**

```markdown
---
title: "When does replay feel like cheating?"
theme: memory-and-play
status: dormant
last_modified: 2026-05-11
description: "Empty-state exemplar: no supporting notes, no related essays, no outputs."
tags: [play]
weight: 30
---

Example 3. Lorem ipsum dolor sit amet.
```

- [ ] **Step 4: Write `can-procedural-text-have-a-throughline/index.md`**

```markdown
---
title: "Can procedural text have a throughline?"
theme: procedural-narrative
status: dormant
last_modified: 2026-05-11
description: "Dormant question in the procedural-narrative theme."
tags: [narrative, procedural]
supporting_notes: [procedural-narrative]
weight: 10
---

Example 4. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
```

- [ ] **Step 5: Write `what-is-a-narrative-atom/index.md`**

```markdown
---
title: "What is a narrative atom?"
theme: procedural-narrative
status: active
last_modified: 2026-05-11
description: "Active question with supporting notes and a related essay; no outputs yet."
tags: [narrative]
supporting_notes: [story-atoms]
related_essays: [example-essay-two]
weight: 20
---

Example 5. Lorem ipsum dolor sit amet.
```

- [ ] **Step 6: Write `when-is-a-save-an-edit/index.md`**

```markdown
---
title: "When is a save an edit?"
theme: save-game-as-form
status: answered
last_modified: 2026-05-11
started: 2024-01-15
description: "Answered question with a paper output and a code output."
tags: [aesthetics, games]
supporting_notes: [the-save-game]
related_essays: [example-essay-three]
outputs:
  - { kind: paper, title: "Save States as Edit States", url: "https://example.com/save-paper", year: 2024 }
  - { kind: code,  title: "save-replay-tool",            url: "https://github.com/example/save-replay-tool", year: 2024 }
weight: 10
---

Example 6. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
```

- [ ] **Step 7: Run both research linters**

Run: `python3 tools/check_research_fixtures.py && python3 tools/check_research_links.py`
Expected: both print success lines and exit 0.

- [ ] **Step 8: Run all linters + unit tests as a full sweep**

Run: `python3 tools/check-contrast.py > /dev/null && python3 tools/check_fixtures.py && python3 tools/check_garden_fixtures.py && python3 tools/check_garden_links.py && python3 tools/check_filter_chips_config.py && python3 tools/check_research_fixtures.py && python3 tools/check_research_links.py && python3 -m unittest tools/test_check_fixtures.py tools/test_check_garden_fixtures.py tools/test_check_garden_links.py tools/test_check_filter_chips_config.py tools/test_check_research_fixtures.py tools/test_check_research_links.py 2>&1 | tail -3`
Expected: all linters pass; unit tests show `Ran 71 tests` (53 existing + 10 + 8 new) `OK`.

- [ ] **Step 9: Commit**

```bash
git add content/research/questions
git commit -m "Research question fixtures: 6 questions covering all variants

Distribution: 3 in memory-and-play (incl. one with parent_question),
2 in procedural-narrative, 1 in save-game-as-form. Variants exercised:
all 3 statuses; top-level vs sub-question; with/without
supporting_notes; with/without related_essays; with/without outputs
(2 papers, 1 talk, 1 code). Filler bodies."
```

---

## Task 8: Hand-author output icons

**Files:**
- Create: `assets/images/icons/output-paper.svg`
- Create: `assets/images/icons/output-talk.svg`
- Create: `assets/images/icons/output-code.svg`

- [ ] **Step 1: Write `output-paper.svg`**

```svg
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 24 24"
     role="img"
     aria-label="paper"
     fill="none"
     stroke="currentColor"
     stroke-width="1.6"
     stroke-linecap="round"
     stroke-linejoin="round">
  <path d="M6 3 H15 L18 6 V21 H6 Z"/>
  <path d="M15 3 V6 H18"/>
  <path d="M9 11 H15"/>
  <path d="M9 14 H15"/>
  <path d="M9 17 H13"/>
</svg>
```

- [ ] **Step 2: Write `output-talk.svg`**

```svg
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 24 24"
     role="img"
     aria-label="talk"
     fill="none"
     stroke="currentColor"
     stroke-width="1.6"
     stroke-linecap="round"
     stroke-linejoin="round">
  <path d="M5 14 V8 C5 7 6 6 7 6 H17 C18 6 19 7 19 8 V14 C19 15 18 16 17 16 H13 L9 19 V16 H7 C6 16 5 15 5 14 Z"/>
  <path d="M9 10 H15"/>
  <path d="M9 12.5 H13"/>
</svg>
```

- [ ] **Step 3: Write `output-code.svg`**

```svg
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 24 24"
     role="img"
     aria-label="code"
     fill="none"
     stroke="currentColor"
     stroke-width="1.8"
     stroke-linecap="round"
     stroke-linejoin="round">
  <path d="M9 8 L4 12 L9 16"/>
  <path d="M15 8 L20 12 L15 16"/>
</svg>
```

- [ ] **Step 4: Verify all three parse as valid XML**

Run: `for f in assets/images/icons/output-*.svg; do python3 -c "import xml.etree.ElementTree as ET; ET.parse('$f'); print('$f parses')"; done`
Expected: three "parses" lines.

- [ ] **Step 5: Commit**

```bash
git add assets/images/icons/output-paper.svg assets/images/icons/output-talk.svg assets/images/icons/output-code.svg
git commit -m "Output icons: paper / talk / code hand-authored SVGs

24x24 viewBox, currentColor stroke (theme-aware), stroke-width 1.6-1.8,
rounded caps. Matches stage-glyph conventions. Inlined into question
hubs via the output-item.html partial in a later task."
```

---

## Task 9: Status pill + output item partials

**Files:**
- Create: `layouts/partials/research/status-pill.html`
- Create: `layouts/partials/research/output-item.html`

- [ ] **Step 1: Write `layouts/partials/research/status-pill.html`**

```html
{{- /* Inputs: . — a status string ("active" | "dormant" | "answered") */ -}}
<span class="status-pill status-{{ . }}">{{ . }}</span>
```

- [ ] **Step 2: Write `layouts/partials/research/output-item.html`**

```html
{{- /* Inputs:
       .kind  — "paper" | "talk" | "code"
       .title — string
       .url   — string
       .year  — int
*/ -}}
<li class="output-item output-item-{{ .kind }}">
  <span class="output-icon" aria-hidden="true">
    {{ with resources.Get (printf "images/icons/output-%s.svg" .kind) }}{{ .Content | safeHTML }}{{ end }}
  </span>
  <a href="{{ .url }}" class="output-title">{{ .title }}</a>
  <span class="output-year">{{ .year }}</span>
</li>
```

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/research/status-pill.html layouts/partials/research/output-item.html
git commit -m "Research partials: status pill + output item

status-pill.html — single-input span with status-{value} class.
output-item.html — li with inlined SVG (resources.Get) + linked title
+ year, dispatched by kind."
```

---

## Task 10: Theme card partial

**Files:**
- Create: `layouts/partials/research/theme-card.html`

- [ ] **Step 1: Write the theme card partial**

```html
{{- /* Inputs:
       .theme       — the theme Page
       .questions   — slice of question Pages for this theme (already filtered)
*/ -}}
{{- $theme := .theme -}}
{{- $questions := .questions -}}
{{- $active := where $questions "Params.status" "active" -}}
{{- $dormant := where $questions "Params.status" "dormant" -}}
{{- $answered := where $questions "Params.status" "answered" -}}
{{- $supportingSet := dict -}}
{{- range $questions -}}
  {{- range .Params.supporting_notes -}}
    {{- $supportingSet = merge $supportingSet (dict . true) -}}
  {{- end -}}
{{- end -}}

<article class="research-card" data-theme-slug="{{ path.Base $theme.File.Dir }}">
  {{ partial "research/status-pill.html" $theme.Params.status }}
  <h2 class="research-card-title">
    <a href="{{ $theme.RelPermalink }}">{{ $theme.Title }}</a>
  </h2>
  {{ if $theme.Params.garden_topic_ref }}
    <span class="research-card-badge">↗ also a Garden topic</span>
  {{ end }}
  <p class="research-card-description">{{ $theme.Params.description }}</p>
  {{ with $theme.Params.tags }}
    <ul class="research-card-tags">
      {{ range . }}<li>{{ . }}</li>{{ end }}
    </ul>
  {{ end }}
  <div class="research-card-counts">
    {{ len $active }}/{{ len $dormant }}/{{ len $answered }} questions
    · {{ len $supportingSet }} supporting notes
  </div>
</article>
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/research/theme-card.html
git commit -m "Research partial: theme card

Renders a single card for the /research/ index grid. Takes the theme
page + a pre-filtered slice of its questions; counts active/dormant/
answered + unique supporting_notes. Surfaces the 'also a Garden
topic' badge when garden_topic_ref is set."
```

---

## Task 11: Backlinks data partial

**Files:**
- Create: `layouts/partials/research/backlinks-data.html`

- [ ] **Step 1: Write the backlinks data partial**

```html
{{- /* Builds a JSON map { question-slug: [{ title, url, kind }, ...] }
       at build time by scanning every page's .RawContent for internal
       /research/questions/<slug>/ references. partialCached — runs once.

       Usage from a question hub template:
         {{ $data := partialCached "research/backlinks-data.html" . }}
         {{ $thisSlug := path.Base .File.Dir }}
         {{ $thisBacklinks := index $data $thisSlug }}
*/ -}}
{{- $linkRE := `/research/questions/([a-z0-9][a-z0-9-]*)/` -}}
{{- $byQuestion := dict -}}
{{- range site.RegularPages -}}
  {{- $thisPage := . -}}
  {{- $kind := "page" -}}
  {{- if eq .Section "essays" -}}{{- $kind = "essay" -}}{{- end -}}
  {{- if eq .Section "garden" -}}{{- $kind = "garden" -}}{{- end -}}
  {{- if eq .Type "research-question" -}}{{- $kind = "question" -}}{{- end -}}
  {{- $seen := dict -}}
  {{- range findRE $linkRE .RawContent -}}
    {{- $slug := replaceRE `^/research/questions/(.*)/$` "$1" . -}}
    {{- /* Skip self-references and dedupe per-page hits */ -}}
    {{- $thisSlug := "" -}}
    {{- if eq $thisPage.Type "research-question" -}}
      {{- $thisSlug = path.Base $thisPage.File.Dir -}}
    {{- end -}}
    {{- if and (ne $slug $thisSlug) (not (index $seen $slug)) -}}
      {{- $seen = merge $seen (dict $slug true) -}}
      {{- $existing := index $byQuestion $slug | default slice -}}
      {{- $entry := dict
            "title" $thisPage.Title
            "url" $thisPage.RelPermalink
            "kind" $kind -}}
      {{- $byQuestion = merge $byQuestion (dict $slug (append $entry $existing)) -}}
    {{- end -}}
  {{- end -}}
{{- end -}}
{{- return $byQuestion -}}
```

- [ ] **Step 2: Commit**

```bash
git add layouts/partials/research/backlinks-data.html
git commit -m "Research partial: build-time backlinks data

Walks site.RegularPages once (partialCached), extracts /research/
questions/<slug>/ refs via findRE on .RawContent, returns a map
{ slug: [{title, url, kind}] } that question hubs index by their
own slug. Same pattern as garden/graph-data.html. Self-references
are skipped; per-page duplicates are deduped."
```

---

## Task 12: Layout — `/research/` index

**Files:**
- Create: `layouts/research/list.html`

- [ ] **Step 1: Write the index layout**

Create `layouts/research/list.html`:

```html
{{ define "main" }}
<main class="reading-column research-page">

  <header class="research-hero">
    <h1>{{ .Title }}</h1>
    {{ with .Content }}<div class="research-framing">{{ . }}</div>{{ end }}
  </header>

  {{- /* All theme + question pages */ -}}
  {{- $themes := where site.RegularPages "Type" "research-theme" -}}
  {{- $questions := where site.RegularPages "Type" "research-question" -}}

  {{- /* Filter chips: tag dim only for v1 */ -}}
  {{- $tags := slice -}}
  {{- range $themes -}}
    {{- range .Params.tags -}}
      {{- if not (in $tags .) -}}{{- $tags = $tags | append . -}}{{- end -}}
    {{- end -}}
  {{- end -}}
  {{- $dims := slice -}}
  {{- if ge (len $tags) 2 -}}
    {{- $dims = $dims | append (dict "key" "tag" "label" "Tag" "values" (sort $tags)) -}}
  {{- end -}}
  {{ partial "filter-chips.html" (dict "dimensions" $dims "section" "research") }}

  <div class="research-grid">
    {{- range $themes.ByWeight -}}
      {{- $thisTheme := . -}}
      {{- $thisSlug := path.Base $thisTheme.File.Dir -}}
      {{- $themeQs := where $questions "Params.theme" $thisSlug -}}
      {{ partial "research/theme-card.html" (dict "theme" $thisTheme "questions" $themeQs) }}
    {{- end -}}
  </div>

</main>
{{ end }}
```

- [ ] **Step 2: Verify Hugo build**

Run: `rm -rf public resources && hugo --minify 2>&1 | tail -3`
Expected: build succeeds. (The theme pages won't render yet — Hugo falls back to `_default/single.html`; that's fine until Task 13.)

- [ ] **Step 3: Visit `/research/` in the dev server**

Open: `http://localhost:1313/research/`
Expected: hero with H1 "Research" + framing paragraph. Filter chips strip with the unique tags from the 3 themes (memory, play, narrative, procedural, aesthetics, games — 6 tags). Three theme cards in a grid; each shows status pill, title (linked), description, tag list, "↗ also a Garden topic" badge on memory-and-play + procedural-narrative (not save-game-as-form), and counts ("2/1/0 questions · 3 supporting notes" for memory-and-play, similar for the others).

- [ ] **Step 4: Commit**

```bash
git add layouts/research/list.html
git commit -m "Research layout: /research/ index page

Hero + filter chips (tag dim) + 2-col theme cards grid. Iterates
themes by weight, hands each card the theme + its pre-filtered
question slice. No 'Open graph' button (Slice 2 adds it)."
```

---

## Task 13: Layout — `/research/themes/<slug>/`

**Files:**
- Create: `layouts/research-theme/single.html`

- [ ] **Step 1: Write the theme page layout**

Create `layouts/research-theme/single.html`:

```html
{{ define "main" }}
{{- $thisSlug := path.Base .File.Dir -}}
{{- $questions := where site.RegularPages "Type" "research-question" -}}
{{- $themeQs := where $questions "Params.theme" $thisSlug -}}
{{- $active := where $themeQs "Params.status" "active" -}}
{{- $dormant := where $themeQs "Params.status" "dormant" -}}
{{- $answered := where $themeQs "Params.status" "answered" -}}

{{- /* Aggregated outputs across this theme's questions */ -}}
{{- $allOutputs := slice -}}
{{- range $themeQs -}}
  {{- range .Params.outputs -}}
    {{- $allOutputs = $allOutputs | append . -}}
  {{- end -}}
{{- end -}}

<main class="reading-column research-theme-page">

  <nav class="research-breadcrumb" aria-label="Breadcrumb">
    <a href="/research/">Research</a> ›
    <span aria-current="page">{{ .Title }}</span>
  </nav>

  <header class="research-theme-hero">
    <h1>{{ .Title }}</h1>
    {{ partial "research/status-pill.html" .Params.status }}
    <p class="research-theme-description">{{ .Params.description }}</p>
    {{ with .Params.summary }}<p class="research-theme-summary">{{ . }}</p>{{ end }}
    {{ if .Params.garden_topic_ref }}
      <p class="research-theme-cross-link">
        ↗ also at
        <a href="/garden/{{ .Params.garden_topic_ref }}/">/garden/{{ .Params.garden_topic_ref }}/</a>
      </p>
    {{ end }}
  </header>

  <section class="three-col-questions">
    {{ if $active }}
    <div class="col-active">
      <h3>Active</h3>
      <ul>
        {{ range $active.ByWeight }}
          <li>
            <a href="{{ .RelPermalink }}">{{ .Title }}</a>
            <span class="q-desc">{{ .Params.description }}</span>
          </li>
        {{ end }}
      </ul>
    </div>
    {{ end }}
    {{ if $dormant }}
    <div class="col-dormant">
      <h3>Dormant</h3>
      <ul>
        {{ range $dormant.ByWeight }}
          <li>
            <a href="{{ .RelPermalink }}">{{ .Title }}</a>
            <span class="q-desc">{{ .Params.description }}</span>
          </li>
        {{ end }}
      </ul>
    </div>
    {{ end }}
    {{ if $answered }}
    <div class="col-answered">
      <h3>Answered</h3>
      <ul>
        {{ range $answered.ByWeight }}
          <li>
            <a href="{{ .RelPermalink }}">{{ .Title }}</a>
            <span class="q-desc">{{ .Params.description }}</span>
          </li>
        {{ end }}
      </ul>
    </div>
    {{ end }}
  </section>

  {{ if $allOutputs }}
  <section class="research-outputs">
    <h2>Outputs</h2>
    <ul class="outputs-list">
      {{ range sort $allOutputs "year" "desc" }}
        {{ partial "research/output-item.html" . }}
      {{ end }}
    </ul>
  </section>
  {{ end }}

  {{ if .Params.garden_topic_ref }}
    {{- $gardenPage := index site.RegularPages.ByPath (printf "garden/%s/index.md" .Params.garden_topic_ref) -}}
    {{- if not $gardenPage -}}
      {{- /* Fallback lookup if ByPath shape differs */ -}}
      {{- range where site.RegularPages "Section" "garden" -}}
        {{- if eq (path.Base .File.Dir) $.Params.garden_topic_ref -}}
          {{- $gardenPage = . -}}
        {{- end -}}
      {{- end -}}
    {{- end -}}
    {{ if $gardenPage }}
    <section class="research-garden-embed">
      <h2>From the Garden</h2>
      {{ partial "garden/topic-section.html" (dict "context" $gardenPage) }}
    </section>
    {{ end }}
  {{ end }}

  {{ if .Content }}
  <section class="research-theme-body">
    {{ .Content }}
  </section>
  {{ end }}

</main>
{{ end }}
```

- [ ] **Step 2: Verify Hugo build**

Run: `rm -rf public resources && hugo --minify 2>&1 | tail -3`
Expected: builds successfully.

- [ ] **Step 3: Visit theme pages**

Open: `http://localhost:1313/research/themes/memory-and-play/`
Expected: breadcrumb (Research › Memory and play), hero with title + active pill + description + summary + "↗ also at /garden/memory-in-play/", three-column block showing 2 Active questions + 1 Dormant question + no Answered column, an outputs section showing 1 paper + 1 talk (from `how-do-readers-form-narrative-from-shuffle`), a "From the Garden" section with the memory-in-play topic_map tile grid.

Open: `http://localhost:1313/research/themes/save-game-as-form/`
Expected: similar but with answered status, no cross-link, no "From the Garden" section, 1 Answered question, outputs section showing 1 paper + 1 code.

- [ ] **Step 4: Commit**

```bash
git add layouts/research-theme/single.html
git commit -m "Research layout: /research/themes/<slug>/ theme page

Breadcrumb + hero + three-col questions block (only renders columns
that have entries) + aggregated outputs (only when any exist) +
optional 'From the Garden' embed using partials/garden/topic-section.html.
Reuses the garden tile renderer end-to-end."
```

---

## Task 14: Layout — `/research/questions/<slug>/`

**Files:**
- Create: `layouts/research-question/single.html`

- [ ] **Step 1: Write the question hub layout**

Create `layouts/research-question/single.html`:

```html
{{ define "main" }}
{{- $thisSlug := path.Base .File.Dir -}}
{{- $themeSlug := .Params.theme -}}
{{- /* Look up the parent theme page */ -}}
{{- $themePages := where site.RegularPages "Type" "research-theme" -}}
{{- $themePage := "" -}}
{{- range $themePages -}}
  {{- if eq (path.Base .File.Dir) $themeSlug -}}
    {{- $themePage = . -}}
  {{- end -}}
{{- end -}}

{{- /* Same-theme questions */ -}}
{{- $allQs := where site.RegularPages "Type" "research-question" -}}
{{- $themeQs := where $allQs "Params.theme" $themeSlug -}}

{{- /* Sub-questions: questions whose parent_question == this slug */ -}}
{{- $subQs := where $themeQs "Params.parent_question" $thisSlug -}}

{{- /* Siblings: same-theme, not this, not parent, not children */ -}}
{{- $parentSlug := .Params.parent_question | default "" -}}
{{- $siblings := slice -}}
{{- range $themeQs -}}
  {{- $candidateSlug := path.Base .File.Dir -}}
  {{- $isThis := eq $candidateSlug $thisSlug -}}
  {{- $isParent := and (ne $parentSlug "") (eq $candidateSlug $parentSlug) -}}
  {{- $isChild := eq (.Params.parent_question | default "") $thisSlug -}}
  {{- if and (not $isThis) (not $isParent) (not $isChild) -}}
    {{- $siblings = $siblings | append . -}}
  {{- end -}}
{{- end -}}

{{- /* Backlinks lookup */ -}}
{{- $backlinksData := partialCached "research/backlinks-data.html" . -}}
{{- $myBacklinks := index $backlinksData $thisSlug | default slice -}}

<main class="reading-column research-question-hub">

  <nav class="research-breadcrumb" aria-label="Breadcrumb">
    <a href="/research/">Research</a> ›
    {{ if $themePage }}
      <a href="{{ $themePage.RelPermalink }}">{{ $themePage.Title }}</a> ›
    {{ else }}
      <span>{{ $themeSlug }}</span> ›
    {{ end }}
    <span aria-current="page">{{ .Title }}</span>
  </nav>

  <header class="research-question-status-strip">
    {{ partial "research/status-pill.html" .Params.status }}
    <span class="last-tended">Last tended: <time>{{ .Params.last_modified }}</time></span>
    {{ with .Params.started }}<span class="started">Started: <time>{{ . }}</time></span>{{ end }}
    {{ with .Params.tags }}
      <ul class="question-tags">{{ range . }}<li>{{ . }}</li>{{ end }}</ul>
    {{ end }}
  </header>

  <h1 class="question-statement">{{ .Title }}</h1>

  <section class="research-current-thinking">
    <h2>Current thinking</h2>
    {{ .Content }}
  </section>

  {{ if $subQs }}
  <section class="research-sub-questions">
    <h2>Sub-questions</h2>
    <ul>
      {{ range $subQs.ByWeight }}
        <li>
          <a href="{{ .RelPermalink }}">{{ .Title }}</a>
          <span class="q-desc">{{ .Params.description }}</span>
        </li>
      {{ end }}
    </ul>
  </section>
  {{ end }}

  {{ if $siblings }}
  <section class="research-siblings">
    <h2>Sibling questions</h2>
    <ul>
      {{ range sort $siblings "Params.weight" "asc" }}
        <li>
          {{ partial "research/status-pill.html" .Params.status }}
          <a href="{{ .RelPermalink }}">{{ .Title }}</a>
        </li>
      {{ end }}
    </ul>
  </section>
  {{ end }}

  {{ with .Params.supporting_notes }}
  <section class="research-supporting-notes">
    <h2>Supporting notes</h2>
    <div class="garden-tiles">
      {{ range . }}
        {{- $slug := . -}}
        {{- $note := "" -}}
        {{- range where site.RegularPages "Section" "garden" -}}
          {{- if eq (path.Base .File.Dir) $slug -}}{{- $note = . -}}{{- end -}}
        {{- end -}}
        {{ with $note }}{{ partial "garden/note-tile.html" (dict "page" .) }}{{ end }}
      {{ end }}
    </div>
  </section>
  {{ end }}

  {{ with .Params.related_essays }}
  <section class="research-related-essays">
    <h2>Related essays</h2>
    <ul>
      {{ range . }}
        {{- $slug := . -}}
        {{- $essay := "" -}}
        {{- range where site.RegularPages "Section" "essays" -}}
          {{- if eq (path.Base .File.Dir) $slug -}}{{- $essay = . -}}{{- end -}}
        {{- end -}}
        {{ with $essay }}
          <li>
            <a href="{{ .RelPermalink }}">{{ .Title }}</a>
            {{ partial "essay-meta.html" . }}
          </li>
        {{ end }}
      {{ end }}
    </ul>
  </section>
  {{ end }}

  {{ with .Params.outputs }}
  <section class="research-outputs">
    <h2>Outputs</h2>
    <ul class="outputs-list">
      {{ range sort . "year" "desc" }}
        {{ partial "research/output-item.html" . }}
      {{ end }}
    </ul>
  </section>
  {{ end }}

  <section class="research-backlinks">
    <h2>Backlinks</h2>
    {{ if $myBacklinks }}
      <ul>
        {{ range $myBacklinks }}
          <li>
            <span class="backlink-kind">{{ .kind }}</span>
            <a href="{{ .url }}">{{ .title }}</a>
          </li>
        {{ end }}
      </ul>
    {{ else }}
      <p class="research-backlinks-empty">No backlinks yet.</p>
    {{ end }}
  </section>

</main>
{{ end }}
```

- [ ] **Step 2: Verify Hugo build**

Run: `rm -rf public resources && hugo --minify 2>&1 | tail -3`
Expected: builds successfully.

- [ ] **Step 3: Visit question hubs**

Open: `http://localhost:1313/research/questions/how-do-readers-form-narrative-from-shuffle/`
Expected: breadcrumb (Research › Memory and play › ...), status strip with active pill + dates + tags, large question statement, "Current thinking" filler paragraphs, "Sub-questions" with what-counts-as-story-recall, "Sibling questions" with when-does-replay-feel-like-cheating only (parent has no other siblings besides itself), "Supporting notes" tile grid with story-atoms + salience-and-memory, "Related essays" list with example-essay-one, "Outputs" with 1 paper + 1 talk (icons render), "Backlinks" section ("No backlinks yet").

Open: `http://localhost:1313/research/questions/when-does-replay-feel-like-cheating/`
Expected: hub with empty supporting/related/outputs sections (headings omitted entirely), siblings list shows the two other memory-and-play questions, "Backlinks" section ("No backlinks yet").

- [ ] **Step 4: Commit**

```bash
git add layouts/research-question/single.html
git commit -m "Research layout: /research/questions/<slug>/ question hub

Full sections per spec §3.3: breadcrumb, status strip, question
statement, current thinking, sub-questions, siblings, supporting
notes (reuses garden note-tile), related essays (with essay-meta),
outputs, backlinks. Optional sections omit their heading entirely
when empty; backlinks always renders (with 'No backlinks yet' on
empty)."
```

---

## Task 15: CSS §30 — Research section

**Files:**
- Modify: `assets/css/main.css`

- [ ] **Step 1: Find the end of the file**

Run: `tail -3 assets/css/main.css`
Expected: shows the closing `}` of the last `.placeholder`-adjacent rule from §29.

- [ ] **Step 2: Append §30**

Append to `assets/css/main.css`:

```css

/* ------------------------------------------------------------------
 * 30. Research surface
 *
 * Slice 1 ships /research/, /research/themes/<slug>/, and
 * /research/questions/<slug>/. Graph runtime + "Open graph"
 * toggle come in Slice 2. Status pills (active/dormant/answered)
 * use existing palette tokens — no new contrast pair introduced.
 * ------------------------------------------------------------------ */

/* Shared status pill (used on theme cards, theme hero, question status strip, sibling list) */
.status-pill {
  display: inline-block;
  padding: 0.05rem 0.5rem;
  border-radius: 999px;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: lowercase;
  letter-spacing: 0.02em;
  border: 1px solid currentColor;
  background: transparent;
}
.status-pill.status-active   { color: var(--color-burgundy); }
.status-pill.status-dormant  { color: var(--color-warn); }
.status-pill.status-answered { color: var(--color-green); }

/* Index page */
.research-page { padding-top: 2rem; padding-bottom: 4rem; }
.research-hero h1 { margin: 0 0 0.5rem; }
.research-framing { color: var(--color-ink-soft); margin-bottom: 1.5rem; }

.research-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}
@media (max-width: 720px) {
  .research-grid { grid-template-columns: 1fr; }
}

.research-card {
  position: relative;
  padding: 1rem 1.1rem;
  border: 1px solid var(--color-rule);
  border-radius: 6px;
  background: var(--color-tile);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.research-card .status-pill { align-self: flex-start; }
.research-card-title {
  margin: 0;
  font-size: var(--text-xl);
}
.research-card-title a {
  color: var(--color-ink);
  text-decoration: none;
}
.research-card-title a:hover { text-decoration: underline; }
.research-card-badge {
  align-self: flex-start;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  padding: 0.05rem 0.45rem;
  border: 1px dotted var(--color-rule);
  border-radius: 4px;
}
.research-card-description {
  margin: 0;
  color: var(--color-ink);
}
.research-card-tags {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
}
.research-card-tags li {
  padding: 0.02rem 0.45rem;
  border: 1px solid var(--color-rule);
  border-radius: 4px;
  color: var(--color-ink-soft);
}
.research-card-counts {
  margin-top: auto;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
}

/* Breadcrumb (used on theme page + question hub) */
.research-breadcrumb {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  margin: 1.5rem 0 0.5rem;
}
.research-breadcrumb a { color: var(--color-ink-soft); }
.research-breadcrumb [aria-current="page"] { color: var(--color-ink); }

/* Theme page */
.research-theme-page { padding-top: 1rem; padding-bottom: 4rem; }
.research-theme-hero { margin-bottom: 2rem; }
.research-theme-hero h1 { margin: 0 0 0.5rem; display: inline-block; margin-right: 0.7rem; }
.research-theme-description { margin: 0.4rem 0 0; }
.research-theme-summary { margin: 0.6rem 0 0; color: var(--color-ink-soft); font-style: italic; }
.research-theme-cross-link {
  margin: 0.6rem 0 0;
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
}

.three-col-questions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.5rem;
  margin: 1.5rem 0;
}
@media (max-width: 720px) {
  .three-col-questions { grid-template-columns: 1fr; }
}
.three-col-questions h3 {
  margin: 0 0 0.5rem;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.three-col-questions ul { list-style: none; margin: 0; padding: 0; }
.three-col-questions li { margin: 0.4rem 0; }
.three-col-questions li a {
  display: block;
  font-weight: 600;
  color: var(--color-ink);
  text-decoration: none;
}
.three-col-questions li a:hover { text-decoration: underline; }
.three-col-questions .q-desc {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  margin-top: 0.15rem;
}

.research-garden-embed { margin-top: 2.5rem; }
.research-garden-embed h2 { margin-bottom: 0.6rem; }

/* Question hub */
.research-question-hub { padding-top: 1rem; padding-bottom: 4rem; }
.research-question-status-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.8rem;
  margin-top: 0.5rem;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
}
.research-question-status-strip .last-tended,
.research-question-status-strip .started { white-space: nowrap; }
.research-question-status-strip .question-tags {
  list-style: none; margin: 0; padding: 0;
  display: flex; gap: 0.4rem; flex-wrap: wrap;
}
.research-question-status-strip .question-tags li {
  padding: 0.02rem 0.45rem;
  border: 1px solid var(--color-rule);
  border-radius: 4px;
}

.question-statement {
  font-family: var(--font-body);
  font-style: italic;
  font-weight: 400;
  font-size: var(--text-2xl);
  margin: 1.5rem 0 2rem;
  line-height: 1.25;
}

.research-current-thinking { margin-bottom: 2rem; }
.research-current-thinking h2 { margin-bottom: 0.6rem; }
.research-current-thinking p { margin: 0.6rem 0; }

.research-sub-questions, .research-siblings {
  margin: 1.5rem 0;
}
.research-sub-questions h2, .research-siblings h2 {
  margin: 0 0 0.6rem;
  font-size: var(--text-xl);
}
.research-sub-questions ul, .research-siblings ul {
  list-style: none; margin: 0; padding: 0;
}
.research-sub-questions li, .research-siblings li { margin: 0.5rem 0; }
.research-sub-questions a, .research-siblings a {
  font-weight: 600;
  color: var(--color-ink);
  text-decoration: none;
}
.research-sub-questions a:hover, .research-siblings a:hover { text-decoration: underline; }
.research-sub-questions .q-desc {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  margin-top: 0.15rem;
}
.research-siblings li { display: flex; gap: 0.7rem; align-items: center; }

.research-supporting-notes { margin: 1.8rem 0; }
.research-supporting-notes h2 { margin-bottom: 0.6rem; }

.research-related-essays { margin: 1.8rem 0; }
.research-related-essays h2 { margin-bottom: 0.6rem; }
.research-related-essays ul { list-style: none; margin: 0; padding: 0; }
.research-related-essays li { margin: 0.5rem 0; }
.research-related-essays li a {
  font-weight: 600;
  color: var(--color-ink);
  text-decoration: none;
}
.research-related-essays li a:hover { text-decoration: underline; }

/* Outputs (used on theme page + question hub) */
.research-outputs { margin: 1.8rem 0; }
.research-outputs h2 { margin-bottom: 0.6rem; }
.outputs-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.output-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.35rem 0;
  border-bottom: 1px solid var(--color-rule);
}
.output-item:last-child { border-bottom: none; }
.output-icon {
  display: inline-flex;
  width: 18px; height: 18px;
  color: var(--color-ink-soft);
  flex-shrink: 0;
}
.output-icon svg { width: 100%; height: 100%; }
.output-title { flex: 1; color: var(--color-ink); text-decoration: none; }
.output-title:hover { text-decoration: underline; }
.output-year {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
}

/* Backlinks */
.research-backlinks { margin: 2rem 0 1rem; }
.research-backlinks h2 { margin-bottom: 0.6rem; }
.research-backlinks ul { list-style: none; margin: 0; padding: 0; }
.research-backlinks li {
  display: flex; gap: 0.6rem; align-items: baseline;
  padding: 0.25rem 0;
  font-size: var(--text-sm);
}
.research-backlinks .backlink-kind {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  text-transform: lowercase;
  width: 5rem;
  flex-shrink: 0;
}
.research-backlinks-empty {
  font-style: italic;
  color: var(--color-ink-soft);
}
```

- [ ] **Step 3: Re-run contrast verifier**

Run: `python3 tools/check-contrast.py`
Expected: still PASS in both modes. No new contrast pair was introduced (status pills use existing tokens `--color-burgundy`, `--color-warn`, `--color-green` which are already on `--color-stone` per the verifier's checked set or otherwise informally OK as decorative accents).

- [ ] **Step 4: Visit the pages again and verify styling lands**

Open: `http://localhost:1313/research/`
Expected: theme cards in a 2-column grid, each with the status pill rendered as a colored outlined chip. Card hover shows underline on title.

Open: `http://localhost:1313/research/themes/memory-and-play/`
Expected: hero with title + status pill side by side; three columns Active / Dormant / Answered (one missing); outputs section with paper + talk rows; "From the Garden" section showing the topic_map tile grid styled the same as `/garden/`.

Open: `http://localhost:1313/research/questions/how-do-readers-form-narrative-from-shuffle/`
Expected: status strip horizontal; large italic question statement; sections styled distinctly; sibling list shows status pill inline before the title; outputs list with icons.

Toggle dark mode: monogram and pills tint correctly; cards keep visible borders.

- [ ] **Step 5: Commit**

```bash
git add assets/css/main.css
git commit -m "CSS §30: Research surface

~200 lines covering: index grid + theme card; theme page (hero,
three-col questions, outputs, garden embed wrapper); question hub
(status strip, question statement Petrona italic, sub-questions,
siblings, supporting notes wrapper, related essays list, backlinks);
shared status pill (active=burgundy, dormant=warn, answered=green);
shared outputs list + output-item with icon. Contrast verifier
still green."
```

---

## Task 16: Wire new CI gates into the GitHub Actions workflow

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Locate the existing linter step block**

Run: `grep -n "filter-chips" .github/workflows/hugo.yaml`
Expected: shows two lines (the verify step and the unit-test step), the last linters before the Hugo build.

- [ ] **Step 2: Append the 4 new steps after the filter-chips block**

Edit `.github/workflows/hugo.yaml` — after the `- name: Run filter-chips linter unit tests` step and before the `- name: Build with Hugo` step, insert:

```yaml
      - name: Verify research fixtures
        run: python3 tools/check_research_fixtures.py
      - name: Run research fixture linter unit tests
        run: python3 -m unittest tools/test_check_research_fixtures.py -v
      - name: Verify research links
        run: python3 tools/check_research_links.py
      - name: Run research links linter unit tests
        run: python3 -m unittest tools/test_check_research_links.py -v
```

- [ ] **Step 3: Verify the YAML still parses**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/hugo.yaml'))" 2>&1 || echo "(yaml package missing; sanity-checking with a stdlib parser)" && python3 -c "
import re
text = open('.github/workflows/hugo.yaml').read()
# Look for the expected 11 verify/test linter steps
verify_count = len(re.findall(r'- name: Verify ', text))
test_count = len(re.findall(r'- name: Run .* linter unit tests', text))
print(f'verify steps: {verify_count}, unit-test steps: {test_count}')
"`
Expected: `verify steps: 5, unit-test steps: 4` — wait, that's the count of `Verify` headers. Actually the existing workflow has: contrast, essay fixtures, garden fixtures, garden links, filter-chips config = 5 verify; plus the new research-fixtures and research-links = 7 verify total. Unit tests: essay + garden fixtures + garden links + filter-chips + research-fixtures + research-links = 6. So expect: `verify steps: 7, unit-test steps: 6`.

Run the actual count:
```bash
grep -c "^      - name: Verify " .github/workflows/hugo.yaml
grep -c "^      - name: Run .* linter unit tests" .github/workflows/hugo.yaml
```
Expected: `7` and `6` respectively (13 total Python checks across the two patterns; matches the spec's "9 → 11" framing for *Python check pairings*).

- [ ] **Step 4: Run the new steps locally as a final pre-merge gate**

Run: `python3 tools/check_research_fixtures.py && python3 tools/check_research_links.py && python3 -m unittest tools/test_check_research_fixtures.py tools/test_check_research_links.py 2>&1 | tail -3`
Expected: `All research fixtures pass linter.`, `OK — verified 3 theme(s), 6 question(s).`, `Ran 18 tests`, `OK`.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "CI: add research fixtures + links linter gates

Four new steps added between filter-chips and the Hugo build:
verify research fixtures, run their unit tests, verify research
links, run their unit tests. Same pattern as the existing four
linter pairs."
```

---

## Task 17: CLAUDE.md update

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add the new linter commands**

In the **Commands** section of `CLAUDE.md`, find the existing `python3 tools/check_filter_chips_config.py` block and add 4 new bullets after it:

```markdown
- `python3 tools/check_research_fixtures.py` — research theme + question fixture frontmatter linter (CI gate)
- `python3 -m unittest tools/test_check_research_fixtures.py -v` — research fixture linter unit tests (CI gate)
- `python3 tools/check_research_links.py` — research cross-reference linter (CI gate)
- `python3 -m unittest tools/test_check_research_links.py -v` — research links linter unit tests (CI gate)
```

Also update the line that mentions the linter count from "nine Python checks" to "thirteen Python checks" (or the actual count after Task 16 — verify with `grep -c "python3 tools/" .github/workflows/hugo.yaml`).

- [ ] **Step 2: Update the layouts list**

In **Architecture → Content & layouts → Layouts**, after `layouts/about/single.html`, add:

```markdown
  - `layouts/research/list.html` — `/research/` index (theme cards grid + tag filter chips; "Open graph" toggle deferred to Slice 2).
  - `layouts/research-theme/single.html` — `/research/themes/<slug>/` (hero + three-column questions block + aggregated outputs + optional embedded garden topic via `partials/garden/topic-section.html` when `garden_topic_ref` is set).
  - `layouts/research-question/single.html` — `/research/questions/<slug>/` (status strip, question statement, current thinking, sub-questions, siblings, supporting notes, related essays, outputs, backlinks).
```

- [ ] **Step 3: Update the partials list**

In **Architecture → Content & layouts → Partials**, add:

```markdown
  - `research/status-pill.html` (active/dormant/answered colored badge — `--color-burgundy`/`--color-warn`/`--color-green`)
  - `research/output-item.html` (single output entry: hand-authored SVG icon + linked title + year; takes `{kind, title, url, year}` dict)
  - `research/theme-card.html` (single theme card for the index grid; computes counts from the question slice)
  - `research/backlinks-data.html` (build-time `partialCached`: walks `site.RegularPages`, extracts `/research/questions/<slug>/` references via `findRE`, returns a slug → list-of-pages map consumed by question hubs)
```

- [ ] **Step 4: Add Phase 5 status entry**

In **Project status** section, before the existing "Phase 2 — remaining slices" entry, add:

```markdown
**Phase 5 — research surface (Slice 1) complete (2026-05-11).** Three new layouts (`/research/`, `/research/themes/<slug>/`, `/research/questions/<slug>/`), three hand-authored output icons, four new partials (`status-pill`, `output-item`, `theme-card`, `backlinks-data`), new CSS §30, 3-theme + 6-question fixture set exercising every variant, two new CI gates (`check_research_fixtures.py` + `check_research_links.py`) with unit tests. Theme pages with `garden_topic_ref` embed the referenced garden topic-map via the existing `partials/garden/topic-section.html` — full visual re-use. Backlinks computed at build time via `partialCached` data partial scanning `.RawContent`. "Open graph" toggle + force-directed research graph deferred to Slice 2.
```

- [ ] **Step 5: Final CI sweep + production build**

Run: `python3 tools/check-contrast.py > /dev/null && python3 tools/check_fixtures.py && python3 tools/check_garden_fixtures.py && python3 tools/check_garden_links.py && python3 tools/check_filter_chips_config.py && python3 tools/check_research_fixtures.py && python3 tools/check_research_links.py && python3 -m unittest tools/test_check_fixtures.py tools/test_check_garden_fixtures.py tools/test_check_garden_links.py tools/test_check_filter_chips_config.py tools/test_check_research_fixtures.py tools/test_check_research_links.py 2>&1 | tail -3 && rm -rf public resources && hugo --minify 2>&1 | tail -5`
Expected: all linters pass; unit tests show ~71 tests OK (53 existing + 18 new); Hugo build clean.

Run: `grep -oE 'src=[^ >]+\.js' public/research/index.html`
Expected: only `src=/js/core.<hash>.js` (no essay or garden bundle on the research index).

Run: `grep -oE 'src=[^ >]+\.js' public/research/questions/how-do-readers-form-narrative-from-shuffle/index.html`
Expected: only `src=/js/core.<hash>.js` (same; no graph runtime).

Run: `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:1313/research/themes/`
Expected: `404` — the bare section page is `_build: render: false`.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md: document research surface (Slice 1) shipment

Commands list gets four new linter entries; layouts list gets three
new layouts; partials list gets four new research/* partials;
project status gets a Phase 5 Slice 1 entry noting the graph + Open
graph toggle deferred to Slice 2."
```

---

## Self-review checklist

- [ ] **Spec coverage:** every section of the spec maps to a task
  - §1.1 frontmatter contracts → Tasks 1, 2 (linter + tests)
  - §1.2 layouts → Tasks 12, 13, 14
  - §1.3 partials → Tasks 9, 10, 11
  - §1.4 SVG icons → Task 8
  - §1.5 CSS §30 → Task 15
  - §1.6 fixtures → Tasks 5, 6, 7
  - §1.7 section infrastructure → Task 5
  - §1.8 two new CI gates → Tasks 1–4
  - §1.9 GitHub Actions workflow update → Task 16
  - §1.10 CLAUDE.md update → Task 17
  - §3.1 frontmatter contracts → Task 1 (linter mirrors the contract)
  - §3.2 fixture set → Tasks 6, 7 (every row of the table is a sub-step)
  - §3.3 page structures → Tasks 12, 13, 14 (each layout matches the spec block)
  - §3.4 component partials → Tasks 9, 10
  - §3.5 CSS additions → Task 15
  - §3.6 Hugo lookup → Task 5 (cascade + render:false)
  - §4 anticipated org-mode contract → not implemented this slice; contract is locked in §3.1 / Task 1
  - §6 acceptance criteria → Task 17 step 5 + per-task visual checks (criteria 1–6, 10–14); contrast (12) covered in Task 15 step 3
- [ ] **No placeholders:** every step contains the actual code, command, or expected output. The filler bodies in fixture files (`Example N. Lorem ipsum ...`) are intentional product content per the parent spec's "fixtures must be obviously dummy" rule, not plan placeholders.
- [ ] **Type consistency:**
  - `research-theme` and `research-question` (the cascade `type:` values) are used identically in Tasks 5 (cascade declaration), 12 (where filter), 13 (single template lookup), 14 (single template lookup), and 17 (CLAUDE.md docs).
  - Frontmatter keys (`garden_topic_ref`, `parent_question`, `supporting_notes`, `related_essays`, `outputs`) appear with the same shape in the spec §3.1, the linter (Task 1), the fixtures (Tasks 6/7), and the layouts (Tasks 13/14).
  - Status enum values (`active`/`dormant`/`answered`) and output kind enum (`paper`/`talk`/`code`) are identical across the linter (Task 1), fixtures (Tasks 6/7), CSS classes (Task 15), and partials (Task 9: `status-{value}`, output-item kind dispatch).
  - The partial input contracts (`partial "research/status-pill.html" .status`, `partial "research/output-item.html" .dict`, `partial "research/theme-card.html" (dict "theme" t "questions" qs)`) match between the partial definitions (Tasks 9, 10) and the layout call sites (Tasks 12, 13, 14).
- [ ] **Acceptance criteria coverage from spec §6:**
  - 1, 2 (index page renders) — Task 12 step 3
  - 3 (memory-and-play theme page) — Task 13 step 3
  - 4 (save-game-as-form theme page) — Task 13 step 3
  - 5, 6 (question hubs) — Task 14 step 3
  - 7, 8 (linters print success) — Task 7 step 7 + Task 17 step 5
  - 9 (unit tests) — Tasks 2 + 4 (cover the enumerated cases) + Task 17 step 5
  - 10 (11 CI gates pass) — Task 17 step 5
  - 11 (hugo --minify clean) — Task 17 step 5
  - 12 (contrast verifier) — Task 15 step 3
  - 13 (only core.js on research pages) — Task 17 step 5 (grep -oE 'src=...')
  - 14 (bare section URLs 404) — Task 17 step 5 (curl)

---

*End of plan.*
