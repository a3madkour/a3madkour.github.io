# Time-synced Poetry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Poetry pages whose body contains `[mm:ss]` markers switch into a synced-reveal mode with a Play/Pause/Reset/Scrub player + a "Show all" accessibility toggle; audio-driven when `audio_url` is set, animation-driven otherwise.

**Architecture:** Hugo detects markers in `.RawContent` and routes through a new parser partial that emits structured DOM with `data-t` attributes (no client-side parsing, no FOUC, plain-text no-JS fallback). A narrowly-loaded JS bundle reads `data-t`, drives reveal via `audio.timeupdate` or `requestAnimationFrame`, and builds the player in JS so no-JS readers see nothing broken. A new stdlib linter pair guards marker grammar, placement, audio-URL validity, escape round-trip, monotonicity (warn), and non-empty poems.

**Tech Stack:** Hugo extended 0.148 (Go templates, `findRE`/`replaceRE`/`RenderString`), vanilla ES module bundled via `js.Build` (esbuild) with SRI, hand-rolled CSS §45, Python 3 stdlib linter.

**Spec:** `docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md` (implement in full, including §9 cite-note integration — citation export already shipped).

**Worktree:** `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry` on branch `feature/time-synced-poetry` @ `2bb9220`.

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `tools/check_works_fixtures.py` | Accept optional `audio_url` on poetry frontmatter | Modify (`POEM_OPTIONAL`) |
| `tools/test_check_works_fixtures.py` | New cases: poem with `audio_url` | Modify |
| `tools/check_poetry_synced.py` | Marker grammar / placement / audio-URL / escape / monotonic / non-empty linter | Create |
| `tools/test_check_poetry_synced.py` | Unit tests for the above | Create |
| `content/works/poetry/example-poem-synced/index.md` | Fixture exercising synced markup end-to-end | Create |
| `layouts/partials/works/synced-marker-seconds.html` | Return-partial: marker string → float seconds | Create (helper) |
| `layouts/partials/works/synced-text-parser.html` | Return-partial: raw body + page → parsed DOM string | Create (shared w/ future lyrics slice) |
| `layouts/partials/works/poem-synced.html` | Entry partial: wrapper div + calls parser | Create |
| `layouts/works-poetry/single.html` | Route to `poem-synced.html` when real markers present | Modify (1 block) |
| `assets/js/poem-synced.js` | Runtime: mode select, player DOM, reveal, seek, show-all | Create |
| `assets/js/entry-poetry.js` | Bundle entry | Create |
| `layouts/partials/scripts.html` | Wire `poetry.<hash>.js` narrowly | Modify (1 block) |
| `assets/css/main.css` | Append §45 | Modify (append) |
| `layouts/partials/cite/normalize-page.html` | §9: append "With audio reading." to BibTeX note | Modify (1 block) |
| `.github/workflows/hugo.yaml` | 2 new linter steps | Modify |
| `tools/ci-local.sh` | 2 new linter lines | Modify |
| `CLAUDE.md` | §45, JS entry table, linter count, project status | Modify |

> **Helper-partial note (spec deviation, intentional):** spec §4 names only `poem-synced.html` + `synced-text-parser.html`. This plan adds a third tiny return-partial `synced-marker-seconds.html` (marker → seconds) because Hugo's `findRE` returns whole matches, not capture groups, so the seconds conversion is non-trivial and is reused per-marker many times and again by the future lyrics slice. This is an implementation decomposition, not a scope change.

> **Fixture/audio decision (documented deferral):** the new fixture sets `audio_url: "https://example.com/example-reading.mp3"` (an obviously-dummy absolute URL). This passes the linter (absolute-URL branch, no binary asset shipped), makes the §9 cite-note fire on a real built page (grep-verifiable), and at runtime the audio load fails → the runtime's documented `audio.onerror` → animation-mode fallback path is exercised live and is fully QA-able as animation. Successful **audio-driven playback** QA stays deferred until the author records a real reading (no AI-generated audio — hard constraint). This matches spec §3's "audio_url set but file 404s → animation mode" edge case and the project's "deferred features stay fixture-seeded" convention.

---

## Task 1: Accept `audio_url` on poetry frontmatter

**Files:**
- Modify: `tools/check_works_fixtures.py:43`
- Test: `tools/test_check_works_fixtures.py`

- [ ] **Step 1: Write the failing tests**

Add these two methods to class `WorksFixturesLinterTests` in `tools/test_check_works_fixtures.py` (after `test_poem_with_optionals`, before `# --- umbrella (Bento grid) fields ---`):

```python
    def test_poem_accepts_audio_url(self):
        body = POEM_VALID.replace(
            "lines: 14\n",
            'lines: 14\naudio_url: "https://example.com/reading.mp3"\n',
        )
        p = self._write("poetry", "with-audio", body)
        self.assertEqual(lint.lint_file(p), [])

    def test_poem_audio_url_relative_accepted_by_fixture_linter(self):
        # check_works_fixtures only validates *shape* (unknown-field gate);
        # path/URL validity is the synced-poetry linter's job (Task 2).
        body = POEM_VALID.replace(
            "lines: 14\n",
            'lines: 14\naudio_url: reading.mp3\n',
        )
        p = self._write("poetry", "with-audio-rel", body)
        self.assertEqual(lint.lint_file(p), [])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && python3 -m unittest tools.test_check_works_fixtures.WorksFixturesLinterTests.test_poem_accepts_audio_url tools.test_check_works_fixtures.WorksFixturesLinterTests.test_poem_audio_url_relative_accepted_by_fixture_linter -v`
Expected: FAIL — `lint_file` reports `unknown field 'audio_url'`.

- [ ] **Step 3: Add `audio_url` to the poem optional set**

In `tools/check_works_fixtures.py`, change line 43 from:

```python
POEM_OPTIONAL = {"tags", "collection", "set_to_music", "summary"} | UMBRELLA_OPTIONAL
```

to:

```python
POEM_OPTIONAL = {"tags", "collection", "set_to_music", "summary", "audio_url"} | UMBRELLA_OPTIONAL
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && python3 -m unittest tools/test_check_works_fixtures.py -v 2>&1 | tail -3`
Expected: `OK` (all existing + 2 new pass).

- [ ] **Step 5: Run the linter against the live tree (no regressions)**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && python3 tools/check_works_fixtures.py`
Expected: `check_works_fixtures: OK`

- [ ] **Step 6: Commit**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
git add tools/check_works_fixtures.py tools/test_check_works_fixtures.py
git commit -m "feat(works): accept optional audio_url on poetry frontmatter"
```

---

## Task 2: Synced-poetry linter pair

**Files:**
- Create: `tools/check_poetry_synced.py`
- Test: `tools/test_check_poetry_synced.py`

Implements spec §8: (1) marker shape, (2) placement, (3) audio-URL validity, (4) escape round-trip, (5) monotonic ordering (warning), (6) non-empty poem.

- [ ] **Step 1: Write the test file (failing — module does not exist yet)**

Create `tools/test_check_poetry_synced.py`:

```python
"""Tests for check_poetry_synced.py — run with:
   python3 -m unittest tools/test_check_poetry_synced.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_poetry_synced as lint  # noqa: E402  # pyright: ignore[reportMissingImports]


def poem(body: str, *, audio_url: str | None = None, draft: bool = False) -> str:
    fm = [
        "---",
        'title: "Synced"',
        "date: 2026-05-18",
        "lastmod: 2026-05-18",
        f"draft: {'true' if draft else 'false'}",
        "lines: 4",
    ]
    if audio_url is not None:
        fm.append(f'audio_url: "{audio_url}"')
    fm.append("---")
    return "\n".join(fm) + "\n\n" + body


HAPPY = poem("[00:01]Lorem ipsum dolor\n[00:04]sit amet consectetur\n")
MIDLINE = poem("[00:01]Sed do [00:02]eiusmod [00:03]tempor\nincididunt ut labore\n")


class TempRepo:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())

    def write(self, slug: str, text: str, *, asset: str | None = None) -> Path:
        d = self.root / "content" / "works" / "poetry" / slug
        d.mkdir(parents=True)
        p = d / "index.md"
        p.write_text(text)
        if asset is not None:
            (d / asset).write_bytes(b"\x00")
        return p

    def cleanup(self) -> None:
        shutil.rmtree(self.root)


class CheckPoetrySyncedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    # --- happy path ---

    def test_happy_path_passes(self) -> None:
        p = self.repo.write("happy", HAPPY)
        errs, warns = lint.lint_file(p)
        self.assertEqual(errs, [])
        self.assertEqual(warns, [])

    def test_midline_markers_pass(self) -> None:
        p = self.repo.write("midline", MIDLINE)
        errs, warns = lint.lint_file(p)
        self.assertEqual(errs, [])

    def test_poem_without_markers_is_skipped(self) -> None:
        p = self.repo.write("plain", poem("Lorem ipsum\ndolor sit amet\n"))
        errs, warns = lint.lint_file(p)
        self.assertEqual(errs, [])
        self.assertEqual(warns, [])

    # --- (1) marker shape ---

    def test_seconds_over_59_fails(self) -> None:
        p = self.repo.write("badsec", poem("[00:60]Lorem ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("[00:60]" in e and "seconds" in e for e in errs), errs)

    def test_seconds_must_be_two_digits(self) -> None:
        p = self.repo.write("shortsec", poem("[03:5]Lorem ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("[03:5]" in e for e in errs), errs)

    def test_fractional_max_two_digits(self) -> None:
        p = self.repo.write("longfrac", poem("[00:03.123]Lorem ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("[00:03.123]" in e for e in errs), errs)

    def test_fractional_one_or_two_digits_ok(self) -> None:
        p = self.repo.write("frac", poem("[00:03.5]Lorem\n[00:04.50]ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertEqual(errs, [])

    # --- (2) placement ---

    def test_embedded_marker_without_separator_fails(self) -> None:
        p = self.repo.write("embedded", poem("Lorem[00:03]ipsum dolor\n"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("placement" in e.lower() or "whitespace" in e.lower() for e in errs), errs)

    def test_leading_whitespace_marker_ok(self) -> None:
        p = self.repo.write("indent", poem("   [00:03]Lorem ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertEqual(errs, [])

    # --- (3) audio-url validity ---

    def test_absolute_audio_url_ok(self) -> None:
        p = self.repo.write("abs", poem("[00:01]Lorem\n", audio_url="https://example.com/r.mp3"))
        errs, _ = lint.lint_file(p)
        self.assertEqual(errs, [])

    def test_absolute_audio_url_malformed_fails(self) -> None:
        p = self.repo.write("badabs", poem("[00:01]Lorem\n", audio_url="ftp://example.com/r.mp3"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("audio_url" in e for e in errs), errs)

    def test_relative_audio_url_missing_file_fails(self) -> None:
        p = self.repo.write("relmiss", poem("[00:01]Lorem\n", audio_url="reading.mp3"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("audio_url" in e and "reading.mp3" in e for e in errs), errs)

    def test_relative_audio_url_present_file_ok(self) -> None:
        p = self.repo.write("relok", poem("[00:01]Lorem\n", audio_url="reading.mp3"), asset="reading.mp3")
        errs, _ = lint.lint_file(p)
        self.assertEqual(errs, [])

    # --- (4) escape round-trip ---

    def test_escaped_marker_not_counted_and_not_shape_checked(self) -> None:
        # \[00:99] is escaped → literal text, must NOT trip shape (seconds>59)
        # and must NOT alone make the poem "synced".
        p = self.repo.write("esc", poem("Lorem ipsum \\[00:99] dolor sit amet\n"))
        errs, warns = lint.lint_file(p)
        self.assertEqual(errs, [])
        self.assertEqual(warns, [])

    def test_escaped_marker_alongside_real_marker(self) -> None:
        p = self.repo.write("escmix", poem("[00:01]Lorem \\[00:99] ipsum\n"))
        errs, _ = lint.lint_file(p)
        self.assertEqual(errs, [])

    # --- (5) monotonic ordering (warning only) ---

    def test_non_monotonic_warns_but_passes(self) -> None:
        p = self.repo.write("nonmono", poem("[00:10]Lorem ipsum\n[00:04]dolor sit\n"))
        errs, warns = lint.lint_file(p)
        self.assertEqual(errs, [])
        self.assertTrue(any("monoton" in w.lower() for w in warns), warns)

    # --- (6) non-empty poem ---

    def test_empty_poem_fails(self) -> None:
        p = self.repo.write("empty", poem("[00:01]\n"))
        errs, _ = lint.lint_file(p)
        self.assertTrue(any("no content" in e.lower() or "empty" in e.lower() for e in errs), errs)

    # --- runner ---

    def test_run_aggregates_and_returns_rc(self) -> None:
        self.repo.write("ok", HAPPY)
        self.repo.write("bad", poem("[00:60]Lorem ipsum\n"))
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(errors)

    def test_run_passes_clean_tree(self) -> None:
        self.repo.write("ok", HAPPY)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0)
        self.assertEqual(errors, [])

    def test_run_empty_section_passes(self) -> None:
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0)
        self.assertEqual(errors, [])

    def test_draft_poem_still_linted(self) -> None:
        # synced markup must be valid even in drafts (they ship in dev server).
        p = self.repo.write("draftbad", poem("[00:60]Lorem ipsum\n", draft=True))
        errs, _ = lint.lint_file(p)
        self.assertTrue(errs)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails (no module)**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && python3 -m unittest tools/test_check_poetry_synced.py -v 2>&1 | tail -5`
Expected: FAIL — `ModuleNotFoundError: No module named 'check_poetry_synced'`.

- [ ] **Step 3: Create the linter**

Create `tools/check_poetry_synced.py`:

```python
#!/usr/bin/env python3
"""Synced-poetry marker linter.

For every content/works/poetry/<slug>/index.md whose body contains at least
one (non-escaped) [mm:ss] marker, validate the synced-poetry contract
(spec docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md §8):

  1. Marker shape  — \\[\\d{1,2}:\\d{2}(?:\\.\\d{1,2})?\\]; minutes 0-99,
                      seconds 00-59 (2 digits), fractional 1-2 digits.
  2. Placement     — every marker at line start (after optional leading
                      whitespace) OR immediately preceded by whitespace.
  3. Audio URL     — when audio_url set: relative → file exists in the page
                      bundle; absolute → ^https?://[^\\s]+$.
  4. Escape        — backslash-escaped \\[mm:ss] is literal text; excluded
                      from the marker counter and from shape checks.
  5. Monotonic     — non-decreasing marker order. WARNING only (rc stays 0).
  6. Non-empty     — at least one content (non-blank, non-marker-only) line.

Exits 0 on all-pass (warnings do not fail), 1 on any error. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)

# Escaped marker first (consumed → never a real marker).
ESCAPED_RE = re.compile(r"\\\[\d{1,2}:\d{2}(?:\.\d{1,2})?\]")
# Loose marker token: anything bracket-wrapped that looks marker-ish, so we
# can shape-check it precisely and report the offending text.
LOOSE_RE = re.compile(r"\[\d{1,2}:\d{1,3}(?:\.\d{1,3})?\]")
STRICT_RE = re.compile(r"^\[(\d{1,2}):(\d{2})(?:\.(\d{1,2}))?\]$")
ABS_URL_RE = re.compile(r"^https?://[^\s]+$")

_ESC_SENTINEL = "\x00ESC\x00"


def _split_body(text: str) -> str:
    m = FRONTMATTER_RE.match(text)
    return text[m.end():] if m else text


def _mask_escaped(body: str) -> str:
    """Replace every \\[mm:ss] with a bracket-free sentinel run so it is
    neither counted nor shape-checked."""
    return ESCAPED_RE.sub(lambda m: _ESC_SENTINEL, body)


def _marker_seconds(mm: str, ss: str, frac: str | None) -> float:
    total = int(mm) * 60 + int(ss)
    if frac:
        total += int(frac) / (10 ** len(frac))
    return float(total)


def lint_file(md: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for one poetry index.md.

    A poem with no real markers returns ([], []) — not a synced poem.
    """
    errors: list[str] = []
    warnings: list[str] = []

    text = md.read_text()
    fm = parse_frontmatter(text) or {}
    body = _split_body(text)
    masked = _mask_escaped(body)

    loose = LOOSE_RE.findall(masked)
    if not loose:
        return [], []  # not a synced poem

    # (1) marker shape
    seconds: list[float] = []
    for tok in loose:
        m = STRICT_RE.match(tok)
        if not m:
            errors.append(
                f"{md}: malformed marker {tok} "
                f"(want [mm:ss] or [mm:ss.f]; mm 0-99, ss 2-digit)"
            )
            continue
        mm, ss, frac = m.group(1), m.group(2), m.group(3)
        if int(ss) > 59:
            errors.append(f"{md}: marker {tok} seconds out of range (00-59)")
            continue
        seconds.append(_marker_seconds(mm, ss, frac))

    # (2) placement — non-space immediately before a marker bracket
    for mobj in LOOSE_RE.finditer(masked):
        start = mobj.start()
        if start > 0 and not masked[start - 1].isspace():
            errors.append(
                f"{md}: marker {mobj.group(0)} placement — must be at line "
                f"start or preceded by whitespace (no embedded text[mm:ss])"
            )

    # (3) audio_url validity
    audio_url = fm.get("audio_url")
    if isinstance(audio_url, str) and audio_url.strip():
        au = audio_url.strip()
        if au.startswith(("http://", "https://")):
            if not ABS_URL_RE.match(au):
                errors.append(f"{md}: audio_url '{au}' is not a valid http(s) URL")
        elif "://" in au:
            errors.append(
                f"{md}: audio_url '{au}' — only http(s) absolute URLs or "
                f"bundle-relative paths are allowed"
            )
        else:
            if not (md.parent / au).is_file():
                errors.append(
                    f"{md}: audio_url '{au}' — relative file not found in "
                    f"page bundle ({md.parent / au})"
                )

    # (6) non-empty: at least one line with text after marker stripping
    has_content = False
    for line in masked.splitlines():
        stripped = LOOSE_RE.sub("", line).strip()
        if stripped:
            has_content = True
            break
    if not has_content:
        errors.append(f"{md}: synced poem has no content (markers only / empty)")

    # (5) monotonic — warning only
    for a, b in zip(seconds, seconds[1:]):
        if b < a:
            warnings.append(
                f"{md}: non-monotonic markers ({a:g}s then {b:g}s) — runtime "
                f"plays in marker order; visual jumps possible"
            )
            break

    return errors, warnings


def run(repo_root: Path) -> tuple[int, list[str]]:
    poetry = repo_root / "content" / "works" / "poetry"
    if not poetry.exists():
        return 0, []
    all_errors: list[str] = []
    all_warnings: list[str] = []
    for child in sorted(poetry.iterdir()):
        if not child.is_dir():
            continue
        md = child / "index.md"
        if not md.exists():
            continue
        errs, warns = lint_file(md)
        all_errors.extend(errs)
        all_warnings.extend(warns)
    for w in all_warnings:
        print(f"WARN {w}", file=sys.stderr)
    return (1 if all_errors else 0), all_errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    for e in errors:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_poetry_synced: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && python3 -m unittest tools/test_check_poetry_synced.py -v 2>&1 | tail -5`
Expected: `OK` (all ~22 tests pass).

- [ ] **Step 5: Run the linter against the live tree**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && python3 tools/check_poetry_synced.py`
Expected: `check_poetry_synced: OK` (no poetry fixture has markers yet → all skipped).

- [ ] **Step 6: Commit**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
git add tools/check_poetry_synced.py tools/test_check_poetry_synced.py
git commit -m "feat(tools): synced-poetry marker linter (21st linter pair)"
```

> **Amendment (applied during execution, code-review-driven):** spec §3's
> edge-case table additionally mandates two **warning-only** linter checks
> beyond the six in §8 — "Untimed line within a synced poem" and "Marker at
> end-of-line with no following word". These were added to `lint_file` as
> warnings (appended to `warnings`, never `errors`; `run()` rc stays 0) plus
> regression tests, in follow-up commits. The untimed-line check fires only
> when a content line has **no marker anywhere** (`LOOSE_RE.search`), so a
> partially-timed mid-line-marker line is not flagged. Net: the linter pair
> shipped is 24 tests, fully spec §3+§8 compliant.

---

## Task 3: Synced-poetry fixture

**Files:**
- Create: `content/works/poetry/example-poem-synced/index.md`

> Generate via shell heredoc (memory `reference_content_filter_bulk_filler.md`: the API content filter blocks bulk lorem-ipsum through Write/subagents).

- [ ] **Step 1: Create the fixture**

Run:

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
mkdir -p content/works/poetry/example-poem-synced
cat > content/works/poetry/example-poem-synced/index.md <<'EOF'
---
title: "Example Poem Synced"
date: 2026-05-18
lastmod: 2026-05-18
draft: false
lines: 8
collection: greenhouse-demos
tags: [example, synced]
summary: "Example synced poem — dummy filler exercising the timed-reveal runtime."
audio_url: "https://example.com/example-reading.mp3"
---

[00:01]Lorem ipsum dolor sit amet,
consectetur adipiscing elit.

[00:05]Sed do [00:06]eiusmod [00:07]tempor
incididunt ut labore et dolore.

[00:12]Ut enim ad minim
veniam quis nostrud.

[00:16]Duis aute *irure* dolor
in \[00:99] reprehenderit voluptate.
EOF
```

This exercises: leading line markers, mid-line word markers, an untimed line (inherits prev + 0.5s), an inline-markdown line (`*irure*` → markdownify path, no word spans), an escaped `\[00:99]` (literal text; not a marker; would be invalid seconds if unescaped → proves the escape bypass), four stanzas, max marker = 16s → `data-duration="16"`, monotonic order (no warning).

- [ ] **Step 2: Run both linters against the live tree**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && python3 tools/check_works_fixtures.py && python3 tools/check_poetry_synced.py`
Expected:
```
check_works_fixtures: OK
check_poetry_synced: OK
```
**Expected stderr:** exactly one informational line —
`WARN .../example-poem-synced/index.md: 4 untimed line(s) in a synced poem
(each inherits prev_t + 0.5s); first: '...'`. This is **expected and
correct**: the fixture deliberately exercises spec §3's untimed-line
inheritance (only the first line of each stanza is timed). Warnings do not
fail the linter — `check_poetry_synced` still exits 0 / prints `OK`, so CI
stays green. There must be **no** `ERROR`/non-zero exit, no monotonic
warning, and no trailing-marker warning.

- [ ] **Step 3: Commit**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
git add content/works/poetry/example-poem-synced/index.md
git commit -m "fixture(poetry): example-poem-synced exercising synced markup"
```

---

## Task 4: Hugo parser partials + routing

**Files:**
- Create: `layouts/partials/works/synced-marker-seconds.html`
- Create: `layouts/partials/works/synced-text-parser.html`
- Create: `layouts/partials/works/poem-synced.html`
- Modify: `layouts/works-poetry/single.html:29-31`
- Modify: `layouts/partials/head.html:9` (strip `[mm:ss]` from the description fallback — spec §4 "markers never appear in the rendered HTML"; `<meta name="description">` + `og:description` derive from `.Summary`, which is the raw body for summary-less poems)

- [ ] **Step 1: Create the seconds helper (return partial)**

Create `layouts/partials/works/synced-marker-seconds.html`:

```go-html-template
{{- /* Input: a marker string like "[12:34]" or "[00:03.5]".
       Output: float seconds. Hugo findRE has no capture groups, so we
       strip brackets and split manually. Shared by synced-text-parser and
       the future lyrics slice. */ -}}
{{- $inner := substr . 1 (sub (len .) 2) -}}
{{- $parts := split $inner ":" -}}
{{- $mm := int (index $parts 0) -}}
{{- $rest := index $parts 1 -}}
{{- $sec := 0.0 -}}
{{- if in $rest "." -}}
  {{- $sp := split $rest "." -}}
  {{- $ss := int (index $sp 0) -}}
  {{- $fracStr := index $sp 1 -}}
  {{- $divisor := cond (eq (len $fracStr) 1) 10.0 100.0 -}}
  {{- $frac := div (float (int $fracStr)) $divisor -}}
  {{- $sec = add (float (add (mul $mm 60) $ss)) $frac -}}
{{- else -}}
  {{- $ss := int $rest -}}
  {{- $sec = float (add (mul $mm 60) $ss) -}}
{{- end -}}
{{- return $sec -}}
```

- [ ] **Step 2: Create the parser (return partial)**

Create `layouts/partials/works/synced-text-parser.html`:

```go-html-template
{{- /* Input dict: { "raw": <markdown body, frontmatter-free>,
                      "page": <Page, for inline RenderString> }
       Output: HTML string (stanzas/lines/words with data-t + the wrapper's
       data-duration computed). Caller pipes through safeHTML.

       Marker grammar: \[\d{1,2}:\d{2}(?:\.\d{1,2})?\]  (spec §3).
       Escaped \[mm:ss] → literal [mm:ss] text (sentinel round-trip).      */ -}}

{{- $raw := .raw -}}
{{- $page := .page -}}
{{- $markerRE := `\[\d{1,2}:\d{2}(?:\.\d{1,2})?\]` -}}

{{- /* Protect escaped markers: \[02:03] → ⟦ESC:02:03⟧ (bracket-free). */ -}}
{{- $raw = replaceRE `\\\[(\d{1,2}:\d{2}(?:\.\d{1,2})?)\]` "⟦ESC:$1⟧" $raw -}}

{{- $lines := split $raw "\n" -}}
{{- $maxT := 0.0 -}}
{{- $prevT := -0.5 -}}      {{- /* first untimed line → 0.0 */ -}}
{{- $stanzas := slice -}}
{{- $cur := slice -}}       {{- /* rendered <span class=poem-line> for open stanza */ -}}

{{- range $lines -}}
  {{- $line := trim . " \t\r" -}}
  {{- if eq $line "" -}}
    {{- if gt (len $cur) 0 -}}
      {{- $stanzas = $stanzas | append (printf "<p class=\"poem-stanza\">%s</p>" (delimit $cur "<br>\n")) -}}
      {{- $cur = slice -}}
    {{- end -}}
  {{- else -}}
    {{- /* leading marker → line data-t; else inherit prevT + 0.5 */ -}}
    {{- $leadRE := `^\[\d{1,2}:\d{2}(?:\.\d{1,2})?\]` -}}
    {{- $lead := findRE $leadRE $line 1 -}}
    {{- $lineT := 0.0 -}}
    {{- if gt (len $lead) 0 -}}
      {{- $lineT = partial "works/synced-marker-seconds.html" (index $lead 0) -}}
      {{- $line = trim (replaceRE $leadRE "" $line 1) " \t" -}}
    {{- else -}}
      {{- $lineT = add $prevT 0.5 -}}
    {{- end -}}
    {{- $prevT = $lineT -}}
    {{- if gt $lineT $maxT -}}{{- $maxT = $lineT -}}{{- end -}}

    {{- $midMarkers := findRE $markerRE $line -}}
    {{- $hasMd := findRE "[*_`]|\\]\\(" $line 1 -}}
    {{- $lineHTML := "" -}}

    {{- if gt (len $midMarkers) 0 -}}
      {{- /* per-word: whitespace tokens; a token may carry a LEADING
             marker glued to its word (e.g. "[00:06]eiusmod" — spec §3:
             the marker immediately precedes the word it times) which both
             advances the clock and times that word. A token that is only
             a marker (source "word [00:06] word") just advances the clock.
             Embedded mid-token markers can't occur: the linter's placement
             rule forbids non-space before a marker, and whitespace-split
             means any marker in a token is at its start. */ -}}
      {{- $curT := $lineT -}}
      {{- $words := slice -}}
      {{- $tokMarkerRE := printf "^%s" $markerRE -}}
      {{- range (split $line " ") -}}
        {{- $tok := trim . " \t" -}}
        {{- if ne $tok "" -}}
          {{- $tm := findRE $tokMarkerRE $tok 1 -}}
          {{- if gt (len $tm) 0 -}}
            {{- $curT = partial "works/synced-marker-seconds.html" (index $tm 0) -}}
            {{- if gt $curT $maxT -}}{{- $maxT = $curT -}}{{- end -}}
            {{- $rest := trim (replaceRE $tokMarkerRE "" $tok 1) " \t" -}}
            {{- if ne $rest "" -}}
              {{- $words = $words | append (printf "<span class=\"poem-word\" data-t=\"%g\">%s </span>" $curT (htmlEscape $rest)) -}}
            {{- end -}}
          {{- else -}}
            {{- $words = $words | append (printf "<span class=\"poem-word\" data-t=\"%g\">%s </span>" $curT (htmlEscape $tok)) -}}
          {{- end -}}
        {{- end -}}
      {{- end -}}
      {{- $lineHTML = printf "<span class=\"poem-line\" data-t=\"%g\">%s</span>" $lineT (delimit $words "") -}}
    {{- else if gt (len $hasMd) 0 -}}
      {{- /* inline markdown, no mid-line markers → single line span */ -}}
      {{- $rendered := chomp ($page.RenderString (dict "display" "inline") $line) -}}
      {{- $lineHTML = printf "<span class=\"poem-line\" data-t=\"%g\">%s</span>" $lineT $rendered -}}
    {{- else -}}
      {{- /* plain text, no markdown, no mid-line markers → uniform words */ -}}
      {{- $words := slice -}}
      {{- range (split $line " ") -}}
        {{- $tok := . -}}
        {{- if ne (trim $tok " \t") "" -}}
          {{- $words = $words | append (printf "<span class=\"poem-word\" data-t=\"%g\">%s </span>" $lineT (htmlEscape $tok)) -}}
        {{- end -}}
      {{- end -}}
      {{- $lineHTML = printf "<span class=\"poem-line\" data-t=\"%g\">%s</span>" $lineT (delimit $words "") -}}
    {{- end -}}

    {{- $cur = $cur | append $lineHTML -}}
  {{- end -}}
{{- end -}}

{{- /* flush trailing stanza */ -}}
{{- if gt (len $cur) 0 -}}
  {{- $stanzas = $stanzas | append (printf "<p class=\"poem-stanza\">%s</p>" (delimit $cur "<br>\n")) -}}
{{- end -}}

{{- $body := delimit $stanzas "\n" -}}
{{- /* restore escaped markers as literal text */ -}}
{{- $body = replaceRE `⟦ESC:(\d{1,2}:\d{2}(?:\.\d{1,2})?)⟧` "[$1]" $body -}}
{{- return (printf "<div class=\"poem-synced\" data-duration=\"%g\">%s</div>" $maxT $body) -}}
```

> **Note on `data-audio-src`:** the wrapper div in this string deliberately omits `data-audio-src`; the entry partial (`poem-synced.html`) wraps this with the audio attribute so the parser stays audio-agnostic and reusable by the lyrics slice. The JS reads `data-audio-src` from the outer element.

- [ ] **Step 3: Create the entry partial**

Create `layouts/partials/works/poem-synced.html`:

```go-html-template
{{- /* Entry partial for synced poetry. Hugo's .RawContent is already
       frontmatter-free. Wrap the parser output so data-audio-src lives on
       the synced wrapper without the parser needing the audio URL. */ -}}
{{- $parsed := partial "works/synced-text-parser.html" (dict "raw" .RawContent "page" .) -}}
{{- with .Params.audio_url -}}
  {{- $parsed = replaceRE `^<div class="poem-synced"` (printf `<div class="poem-synced" data-audio-src="%s"` (htmlEscape .)) $parsed 1 -}}
{{- end -}}
{{ $parsed | safeHTML }}
```

- [ ] **Step 4: Wire routing into the poetry single layout**

In `layouts/works-poetry/single.html`, replace lines 29–31:

```go-html-template
  <section class="works-poem-body">
    {{ .Content }}
  </section>
```

with:

```go-html-template
  <section class="works-poem-body">
    {{- $all := findRE `\[\d{1,2}:\d{2}(?:\.\d{1,2})?\]` .RawContent -}}
    {{- $esc := findRE `\\\[\d{1,2}:\d{2}(?:\.\d{1,2})?\]` .RawContent -}}
    {{- if gt (len $all) (len $esc) -}}
      {{ partial "works/poem-synced.html" . }}
    {{- else -}}
      {{ .Content }}
    {{- end -}}
  </section>
```

> Routing counts **real** markers as `total − escaped` so a poem containing only `\[mm:ss]` literals stays on the plain `.Content` path (RE2 has no lookbehind; subtraction is the robust equivalent — mirrors the linter's `_mask_escaped`).

- [ ] **Step 4b: Keep markers out of the `<meta>` description fallback**

Spec §4: *"Markers are consumed during parse and never appear in the rendered HTML."* `layouts/partials/head.html` derives `<meta name="description">` **and** `og:description` from `.Summary` when no explicit `description`/`summary` is set. For a summary-less synced poem, Hugo's auto-`.Summary` is the raw body — so the literal `[mm:ss]` markers leak into page metadata (SEO / social cards). The fixture now carries an explicit `summary:` (Task 3) which fixes the demonstrated case; this step adds a defensive strip so **any** synced poem (incl. future real ones lacking a summary) is covered.

In `layouts/partials/head.html`, replace line 9:

```go-html-template
  {{ $description := or .Description .Summary site.Params.description }}
```

with:

```go-html-template
  {{ $description := replaceRE `\[\d{1,2}:\d{2}(?:\.\d{1,2})?\]` "" (or .Description .Summary site.Params.description "") }}
```

Lines 10 and 23 (the `<meta name="description">` and `og:description` emissions) are unchanged — they already consume `$description`. The trailing `""` default keeps `replaceRE`'s input a string when no description source is set (result is `""` → the existing `{{ with $description }}` guards still suppress empty tags). This is a strict no-op for every page whose description contains no `[mm:ss]` substring.

- [ ] **Step 5: Build and assert the emitted DOM**

Run:

> **`data-duration` semantics (intentional refinement of spec §4):** spec
> §4 says `data-duration = max [mm:ss] value`. Taken literally, a trailing
> untimed line (inherits `prev + 0.5`, spec §3) would sit *past* duration
> and never reveal in animation mode (the rAF loop ends at `now >=
> duration`), stranding authored content. So `$maxT` is the max **effective
> span time** (markers AND inherited untimed-line times) — identical to
> max-marker whenever there are no trailing untimed lines (the common
> case), only larger by the `+0.5` tail otherwise, guaranteeing full
> reveal. For this fixture: max marker = 16; the final line
> (`in [00:99] reprehenderit voluptate.`, untimed) inherits `16 + 0.5` ⇒
> **`data-duration="16.5"`**.

Run (a **non-minified** production build — the production HTML minifier
unquotes simple attribute values, which would cause false-negative greps;
minification is orthogonal to whether the parser emits correct DOM, so we
assert on stable non-minified output then separately confirm the minified
build also succeeds):

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
pkill -f 'hugo server' 2>/dev/null || true
rm -rf public && HUGO_ENVIRONMENT=production hugo 2>&1 | tail -3
F=public/works/poetry/example-poem-synced/index.html
echo "--- wrapper (expect class+data-audio-src+data-duration) ---"; grep -o 'class="poem-synced"[^>]*' "$F"
echo "--- duration 16.5 ---"; grep -o 'data-duration="16.5"' "$F"
echo "--- audio-src ---"; grep -o 'data-audio-src="https://example.com/example-reading.mp3"' "$F"
echo "--- word-span count (nonzero) ---"; grep -oc 'class="poem-word"' "$F"
echo "--- mid-line markers consumed + timed (eiusmod@6, tempor@7) ---"; grep -o 'data-t="6"' "$F" | head -1; grep -o 'data-t="7"' "$F" | head -1
echo "--- real markers NOT leaked as literal text ---"; grep -q '\[00:05\]' "$F" && echo LEAK_0005 || echo no-0005-leak; grep -q '\[00:06\]' "$F" && echo LEAK_0006 || echo no-0006-leak
echo "--- escaped marker survives as literal ---"; grep -o '\[00:99\]' "$F" | head -1
echo "--- untimed inheritance (veniam line: 12 + 0.5) ---"; grep -o 'data-t="12.5"' "$F" | head -1
echo "--- markdown preserved ---"; grep -o '<em>irure</em>' "$F"
echo "--- markerless poem unchanged ---"; grep -q 'class="poem-synced"' public/works/poetry/example-poem-minimal/index.html && echo MINIMAL_BROKEN || echo PLAIN_POEM_UNCHANGED
echo "--- minified production build also succeeds ---"; rm -rf public && HUGO_ENVIRONMENT=production hugo --minify 2>&1 | tail -1; test -f public/works/poetry/example-poem-synced/index.html && echo MINIFY_BUILD_OK
```

Expected: the `hugo` runs print **no `ERROR`** / no `execute of template failed`; wrapper line shows `class="poem-synced" data-audio-src="https://example.com/example-reading.mp3" data-duration="16.5"`; `data-duration="16.5"`; the audio-src match; a non-zero `poem-word` count; `data-t="6"` and `data-t="7"` both present (mid-line markers consumed + timed correctly); `no-0005-leak` and `no-0006-leak` (real markers consumed, not rendered as text); a literal `[00:99]` (escaped marker preserved); `data-t="12.5"`; `<em>irure</em>`; `PLAIN_POEM_UNCHANGED`; and `MINIFY_BUILD_OK`.

> Diagnose, don't mask: the `LEAK_*` greps scan the **whole HTML file**, so they also catch `[mm:ss]` in the `<head>` `<meta>`/`og:description` (Hugo auto-`.Summary`) — that is what Step 4b + the fixture `summary:` resolve, not the parser. If `data-t="6"`/`"7"` is absent, the per-token leading-marker logic in Step 2's mid-line branch is wrong — fix the parser. If `LEAK_*` persists after Step 4b, confirm `head.html` line 9 was replaced exactly and the fixture has its `summary:`. If `data-t="12.5"` is absent, inspect untimed-line inheritance (`$prevT + 0.5` and that `$maxT`/`$prevT` are not updated for untimed lines incorrectly). If `<em>irure</em>` is absent, check the inline-markdown branch (`RenderString` with `(dict "display" "inline")`). If a Hugo `ERROR`/template-execute failure mentions the new partials, the template syntax is wrong. Fix the parser, rebuild, re-assert — never weaken the asserts or the fixture to make them pass.

- [ ] **Step 6: Run the full pre-build linter sweep (no Hugo-side regressions)**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && python3 tools/check_pagefind_meta.py && python3 tools/check_cite_meta.py && python3 tools/check_smoke.py`
Expected: each prints OK (the new page carries the same poetry meta/cite scaffolding as siblings).

- [ ] **Step 7: Commit**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
git add layouts/partials/works/synced-marker-seconds.html layouts/partials/works/synced-text-parser.html layouts/partials/works/poem-synced.html layouts/works-poetry/single.html layouts/partials/head.html
git commit -m "feat(poetry): Hugo-side [mm:ss] parser + synced DOM emission"
```

---

## Task 5: JS runtime + bundle wiring

**Files:**
- Create: `assets/js/poem-synced.js`
- Create: `assets/js/entry-poetry.js`
- Modify: `layouts/partials/scripts.html` (append one block)

- [ ] **Step 1: Create the runtime module**

Create `assets/js/poem-synced.js`:

```js
// Synced-poetry runtime. Spec: docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md §6.
// DOM-first: Hugo emits .poem-synced with data-t spans + data-duration; this
// module builds the player (so no-JS readers see nothing broken), drives the
// reveal from audio.timeupdate (audio mode) or requestAnimationFrame
// (animation mode), and supports seek + reset + show-all.

const FLOURISH_MS = 600;

function fmt(t) {
  t = Math.max(0, Math.floor(t));
  const m = Math.floor(t / 60);
  const s = t % 60;
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}

function setupOne(wrap) {
  const wordSel = wrap.querySelectorAll('.poem-word[data-t]');
  const spans = Array.from(
    wordSel.length ? wordSel : wrap.querySelectorAll('.poem-line[data-t]')
  ).map((el) => ({ el, t: parseFloat(el.getAttribute('data-t')) || 0 }))
   .sort((a, b) => a.t - b.t);

  let duration = parseFloat(wrap.getAttribute('data-duration')) || 0;
  const src = wrap.getAttribute('data-audio-src');

  // --- player DOM (built in JS so no-JS readers never see broken controls) ---
  const player = document.createElement('div');
  player.className = 'poem-player';
  player.innerHTML =
    '<button type="button" class="poem-player-btn poem-player-btn--primary" ' +
    'data-act="play" aria-label="Play">▶</button>' +
    '<button type="button" class="poem-player-btn" data-act="reset" ' +
    'aria-label="Reset">↻</button>' +
    '<div class="poem-player-progress" role="slider" aria-label="Seek" ' +
    'tabindex="0" aria-valuemin="0">' +
    '<div class="poem-player-progress-fill"></div>' +
    '<div class="poem-player-progress-thumb"></div></div>' +
    '<span class="poem-player-time">0:00 / 0:00</span>' +
    '<button type="button" class="poem-player-show-all" data-act="showall" ' +
    'aria-pressed="false">👁 Show all</button>';
  wrap.parentNode.insertBefore(player, wrap);

  const playBtn = player.querySelector('[data-act="play"]');
  const resetBtn = player.querySelector('[data-act="reset"]');
  const showAllBtn = player.querySelector('[data-act="showall"]');
  const bar = player.querySelector('.poem-player-progress');
  const fill = player.querySelector('.poem-player-progress-fill');
  const thumb = player.querySelector('.poem-player-progress-thumb');
  const timeEl = player.querySelector('.poem-player-time');

  let mode = src ? 'audio' : 'anim';
  let audio = null;
  let playing = false;
  let elapsed = 0;       // anim-mode seconds
  let startedAt = 0;     // performance.now() at last play
  let rafId = 0;

  if (mode === 'audio') {
    audio = new Audio(src);
    audio.preload = 'none';
    audio.addEventListener('loadedmetadata', () => {
      if (isFinite(audio.duration) && audio.duration > 0) duration = audio.duration;
      render(currentTime());
    });
    audio.addEventListener('timeupdate', () => render(currentTime()));
    audio.addEventListener('ended', () => { playing = false; syncPlayBtn(); });
    audio.addEventListener('error', () => {
      console.warn('[poem-synced] audio failed to load; falling back to animation mode', src);
      mode = 'anim';
      audio = null;
      duration = parseFloat(wrap.getAttribute('data-duration')) || duration;
      stop();
      render(0);
    });
  }

  function currentTime() {
    if (mode === 'audio' && audio) return audio.currentTime || 0;
    if (playing) return elapsed + (performance.now() - startedAt) / 1000;
    return elapsed;
  }

  function syncPlayBtn() {
    playBtn.textContent = playing ? '⏸' : '▶';
    playBtn.setAttribute('aria-label', playing ? 'Pause' : 'Play');
  }

  function render(now) {
    for (const s of spans) {
      if (s.t <= now) {
        if (!s.el.classList.contains('is-visible') &&
            !s.el.classList.contains('is-current')) {
          s.el.classList.add('is-current');
          setTimeout(() => {
            s.el.classList.remove('is-current');
            s.el.classList.add('is-visible');
          }, FLOURISH_MS);
        }
      } else {
        s.el.classList.remove('is-current', 'is-visible');
      }
    }
    const pct = duration > 0 ? Math.min(1, now / duration) * 100 : 0;
    fill.style.width = pct + '%';
    thumb.style.left = pct + '%';
    timeEl.textContent = `${fmt(now)} / ${fmt(duration)}`;
    bar.setAttribute('aria-valuemax', String(Math.floor(duration)));
    bar.setAttribute('aria-valuenow', String(Math.floor(now)));
  }

  function tick() {
    if (!playing) return;
    const now = currentTime();
    render(now);
    if (now >= duration) { playing = false; syncPlayBtn(); return; }
    rafId = requestAnimationFrame(tick);
  }

  function play() {
    if (playing) return;
    playing = true;
    syncPlayBtn();
    if (mode === 'audio' && audio) {
      audio.play().catch(() => {});
    } else {
      startedAt = performance.now();
      rafId = requestAnimationFrame(tick);
    }
  }

  function pause() {
    if (!playing) return;
    if (mode === 'audio' && audio) {
      audio.pause();
    } else {
      elapsed = currentTime();
      cancelAnimationFrame(rafId);
    }
    playing = false;
    syncPlayBtn();
  }

  function stop() {
    cancelAnimationFrame(rafId);
    playing = false;
    syncPlayBtn();
  }

  function reset() {
    stop();
    if (mode === 'audio' && audio) { audio.pause(); audio.currentTime = 0; }
    elapsed = 0;
    render(0);
  }

  function seek(clientX) {
    const r = bar.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (clientX - r.left) / r.width));
    const target = ratio * duration;
    if (mode === 'audio' && audio) {
      audio.currentTime = target;
    } else {
      elapsed = target;
      if (playing) startedAt = performance.now();
    }
    render(target);
  }

  playBtn.addEventListener('click', () => (playing ? pause() : play()));
  resetBtn.addEventListener('click', reset);
  showAllBtn.addEventListener('click', () => {
    const on = wrap.classList.toggle('is-show-all');
    showAllBtn.classList.toggle('is-active', on);
    showAllBtn.setAttribute('aria-pressed', String(on));
  });

  let dragging = false;
  bar.addEventListener('pointerdown', (e) => {
    dragging = true;
    bar.setPointerCapture(e.pointerId);
    seek(e.clientX);
  });
  bar.addEventListener('pointermove', (e) => { if (dragging) seek(e.clientX); });
  bar.addEventListener('pointerup', () => { dragging = false; });
  bar.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault();
      const step = e.key === 'ArrowRight' ? 5 : -5;
      const t = Math.max(0, Math.min(duration, currentTime() + step));
      if (mode === 'audio' && audio) audio.currentTime = t;
      else { elapsed = t; if (playing) startedAt = performance.now(); }
      render(t);
    }
  });

  render(0);
}

export function initPoemSynced() {
  const wraps = document.querySelectorAll('.poem-synced');
  if (!wraps.length) return;
  wraps.forEach(setupOne);
}
```

- [ ] **Step 2: Create the bundle entry**

Create `assets/js/entry-poetry.js`:

```js
// Poetry-section entry — loaded only on /works/poetry/<slug>/ single pages.
// poem-synced.js owns its own .poem-synced guard, so non-synced poems no-op.
import { initPoemSynced } from './poem-synced.js';
initPoemSynced();
```

- [ ] **Step 3: Wire the bundle into scripts.html**

In `layouts/partials/scripts.html`, append this block at the end of the file (after the cite block, before EOF):

```go-html-template
{{- /* Synced-poetry runtime: only on poetry single pages. games/music
       single pages do not load this; entry-works-umbrella.js (filter chips
       + works graph) continues to load on all works single pages
       independently. */ -}}
{{- if and (eq .Section "works") (eq .Kind "page") (eq .Type "works-poetry") }}
{{- $poetryOpts := dict "targetPath" "js/poetry.js" "minify" true -}}
{{- $poetry := resources.Get "js/entry-poetry.js" | js.Build $poetryOpts | fingerprint }}
<script src="{{ $poetry.RelPermalink }}" integrity="{{ $poetry.Data.Integrity }}" defer></script>
{{- end }}
```

- [ ] **Step 4: Build and assert bundle scoping**

Run:

Run (non-minified build for stable attribute quoting — the production HTML
minifier can unquote `src=`; bundle wiring is orthogonal to minification, so
assert on non-minified then separately confirm the minified build succeeds):

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
pkill -f 'hugo server' 2>/dev/null || true
rm -rf public && HUGO_ENVIRONMENT=production hugo 2>&1 | tail -3
echo "--- poetry bundle on the synced poem page ---"; grep -oE '/js/poetry\.[0-9a-f]+\.js' public/works/poetry/example-poem-synced/index.html | head -1
echo "--- SRI integrity present on the poetry script tag ---"; grep -oE '<script src="/js/poetry\.[0-9a-f]+\.js" integrity="sha[0-9]+-[^"]+" defer>' public/works/poetry/example-poem-synced/index.html | head -1
echo "--- NOT on games single pages ---"; grep -lE '/js/poetry\.[0-9a-f]+\.js' public/works/games/*/index.html 2>/dev/null && echo LEAKED_TO_GAMES || echo NOT_ON_GAMES
echo "--- NOT on music single pages ---"; grep -lE '/js/poetry\.[0-9a-f]+\.js' public/works/music/*/index.html 2>/dev/null && echo LEAKED_TO_MUSIC || echo NOT_ON_MUSIC
echo "--- bundle artifact + size ---"; ls -la public/js/poetry.*.js
echo "--- minified production build also succeeds ---"; rm -rf public && HUGO_ENVIRONMENT=production hugo --minify 2>&1 | tail -1; test -f public/works/poetry/example-poem-synced/index.html && echo MINIFY_BUILD_OK
```

Expected: no Hugo `ERROR`; a `/js/poetry.<hash>.js` path on the poetry page; the SRI grep matches (the script tag carries `integrity="sha…"` + `defer`); `NOT_ON_GAMES`; `NOT_ON_MUSIC` (games/music single pages load `works-umbrella.<hash>.js`, not poetry); the built `public/js/poetry.<hash>.js` exists (~6–8 KB minified by `js.Build`'s own `minify:true`, independent of HTML minification); and `MINIFY_BUILD_OK`. (The poetry page legitimately *also* carries `works-umbrella.<hash>.js` — that's the pre-existing persistent-graph bundle, not a conflict.)

- [ ] **Step 5: Commit**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
git add assets/js/poem-synced.js assets/js/entry-poetry.js layouts/partials/scripts.html
git commit -m "feat(poetry): synced-reveal JS runtime + page-narrow bundle"
```

> **Amendment (applied during execution, code-review-driven):** a follow-up
> commit hardens `poem-synced.js`:
> - **Stale flourish timer:** track each span's 600 ms `setTimeout` in a
>   `Map`; `clearTimeout` + delete it in `render`'s hide branch so a
>   reset / backward-seek within 600 ms of a reveal can't let a stale timer
>   re-add `.is-visible`.
> - **`pointercancel`:** `bar.addEventListener('pointercancel', () => {
>   dragging = false; })` — matches the repo's other drag surfaces
>   (garden/research/works-graph) so an interrupted touch doesn't stick the
>   scrub bar in drag mode.
> - **a11y:** `aria-valuetext` ("`m:ss of m:ss`") on the slider each render;
>   show-all button gets `aria-label="Show all verses"` with the emoji
>   wrapped `<span aria-hidden="true">👁</span>`.
> - **Consciously NOT changed** (reviewer Minors, with rationale):
>   `aria-valuemax` stays in `render()` — single source of truth, robust to
>   duration changes on `loadedmetadata` / audio-error fallback, per-tick
>   idempotent write is negligible; the ▶ ⏸ ↻ 👁 control glyphs stay Unicode
>   — spec §1-mandated control characters (not illustrations), changing them
>   would deviate from "exactly as spec'd".

---

## Task 6: CSS §45

**Files:**
- Modify: `assets/css/main.css` (append after line 4843)

- [ ] **Step 1: Append §45**

Append to the end of `assets/css/main.css` (after the final `}` at line 4843), matching the §44 header style (`/* ===== §N Title ... ===== */`):

```css

/* ============================================================================
   §45 Synced poetry runtime
   Spec: docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md §7.
   Reveal opacity + flourish; JS-built player chrome. Reuses existing tokens.
   ========================================================================== */

.poem-synced { margin: 1.4rem 0 2rem; }

.poem-stanza {
  margin: 0 0 1em 0;
  line-height: 1.85;
  font-size: 1.05rem;
  font-family: var(--font-body);
}

.poem-word,
.poem-line[data-t] {
  opacity: 0.06;
  transition: opacity 600ms ease-out;
}
.poem-word.is-visible,
.poem-line.is-visible { opacity: 1; }

.poem-word.is-current {
  animation: poem-current-flourish 600ms ease-out forwards;
}
@keyframes poem-current-flourish {
  0%   { font-style: italic; opacity: 0.5; }
  60%  { font-style: italic; opacity: 1; }
  100% { font-style: normal; opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
  .poem-word, .poem-line[data-t] { transition: none; }
  .poem-word.is-current { animation: none; font-style: normal; opacity: 1; }
}

.poem-synced.is-show-all .poem-word,
.poem-synced.is-show-all .poem-line[data-t] {
  opacity: 1 !important;
  transition: none;
}

.poem-player {
  display: flex; align-items: center; gap: 0.7rem;
  padding: 0.5rem 0.85rem;
  background: var(--color-paper);
  border: 1px solid var(--color-ink-soft);
  border-radius: 4px;
  margin: 0.5rem 0 1.2rem;
  font-family: var(--font-ui);
  font-size: 0.8rem;
}

.poem-player-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px;
  background: transparent;
  border: 1px solid var(--color-ink-soft);
  color: var(--color-burgundy);
  border-radius: 50%;
  cursor: pointer;
}
.poem-player-btn--primary {
  background: var(--color-burgundy); color: white;
  border-color: var(--color-burgundy);
  width: 34px; height: 34px;
}

.poem-player-progress {
  flex: 1; height: 4px;
  background: rgba(138,58,58,0.12);
  border-radius: 2px;
  cursor: pointer;
  position: relative;
}
.poem-player-progress-fill {
  position: absolute; top: 0; left: 0; height: 100%;
  background: var(--color-burgundy);
  border-radius: 2px;
}
.poem-player-progress-thumb {
  position: absolute; top: 50%;
  width: 11px; height: 11px;
  background: var(--color-burgundy);
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

.poem-player-time {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--color-ink-soft);
  min-width: 70px; text-align: right;
}

.poem-player-show-all {
  display: inline-flex; align-items: center; gap: 0.3rem;
  padding: 4px 9px;
  background: transparent;
  border: 1px solid var(--color-ink-soft);
  color: var(--color-ink-soft);
  border-radius: 99px;
  cursor: pointer;
  font-size: 0.7rem;
}
.poem-player-show-all.is-active {
  background: var(--color-burgundy); color: white;
  border-color: var(--color-burgundy);
}

/* Reserved: the OPTIONAL in-audio-mode pill (spec §6.4 marks it "Optional").
   poem-synced.js does not build a .poem-audio-pill element yet — the
   audio-mode pill + its pulse animation are a documented deferral (see
   CLAUDE.md deferred-features: "Audio-pill pulse animation"); the style
   lives here so it round-trips when that JS lands. Distinct from
   .works-audio-pill (the set_to_music cross-link from audio-pill.html). */
.poem-audio-pill {
  display: inline-flex; align-items: center; gap: 0.4rem;
  margin-top: 0.4rem;
  padding: 0.4rem 0.7rem;
  background: rgba(138,58,58,0.06);
  border-left: 2px solid var(--color-ink-soft);
  border-radius: 0 3px 3px 0;
  font-size: 0.7rem;
  color: var(--color-ink-soft);
  font-family: var(--font-mono);
}

@media (max-width: 480px) {
  .poem-player { flex-wrap: wrap; }
  .poem-player-progress { order: 99; width: 100%; }
}
```

- [ ] **Step 2: Run the contrast linter (no regression)**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && python3 tools/check-contrast.py`
Expected: pass (§45 introduces no new tokens; the four checked pairings are untouched).

- [ ] **Step 3: Build (CSS pipeline still fingerprints cleanly)**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && pkill -f 'hugo server' 2>/dev/null || true; rm -rf public && HUGO_ENVIRONMENT=production hugo --minify >/dev/null 2>&1 && echo BUILD_OK && ls public/css/main.*.css`
Expected: `BUILD_OK` and a fingerprinted `public/css/main.<hash>.css`.

- [ ] **Step 4: Commit**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
git add assets/css/main.css
git commit -m "feat(css): §45 synced-poetry runtime styles"
```

---

## Task 7: §9 citation-note integration

**Files:**
- Modify: `layouts/partials/cite/normalize-page.html` (after line 51, before line 53)

- [ ] **Step 1: Add the note clause**

In `layouts/partials/cite/normalize-page.html`, immediately after the garden-note block (the `{{- end -}}` closing the `{{- if eq .Section "garden" -}}` at line 51) and before the dates comment at line 53, insert:

```go-html-template
{{- /* Synced poetry with a recorded reading — flag the audio performance. */ -}}
{{- if and (eq .Section "works") (eq .Type "works-poetry") .Params.audio_url -}}
  {{- $note = "With audio reading." -}}
{{- end -}}
```

> `$note` is declared with `:=` at line 44 and this is a `=` reassignment after that declaration — correct ordering.

- [ ] **Step 2: Build and assert the note reaches the cite data blob**

Run:

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
pkill -f 'hugo server' 2>/dev/null || true
rm -rf public && HUGO_ENVIRONMENT=production hugo --minify >/dev/null 2>&1 && echo BUILD_OK
grep -o 'With audio reading\.' public/works/poetry/example-poem-synced/index.html | head -1
! grep -q 'With audio reading' public/works/poetry/example-poem-minimal/index.html && echo "ONLY_ON_AUDIO_POEM"
```

Expected: `BUILD_OK`; `With audio reading.` present on the synced poem; `ONLY_ON_AUDIO_POEM` (the markerless/no-audio poem does not get the note).

- [ ] **Step 3: Run the cite-meta linter (no regression)**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && python3 tools/check_cite_meta.py`
Expected: pass (poetry already validates; the note only populates an existing field).

- [ ] **Step 4: Commit**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
git add layouts/partials/cite/normalize-page.html
git commit -m "feat(cite): note recorded reading on synced poetry (spec §9)"
```

---

## Task 8: CI wiring

**Files:**
- Modify: `.github/workflows/hugo.yaml` (after line 91)
- Modify: `tools/ci-local.sh` (after the works-links block)

- [ ] **Step 1: Add the workflow steps**

In `.github/workflows/hugo.yaml`, after line 91 (`run: python3 -m unittest tools/test_check_works_links.py -v`) and before line 92 (`- name: Verify library fixtures`), insert:

```yaml
      - name: Verify synced-poetry markers
        run: python3 tools/check_poetry_synced.py
      - name: Run synced-poetry linter unit tests
        run: python3 -m unittest tools/test_check_poetry_synced.py -v
```

- [ ] **Step 2: Add the ci-local.sh lines**

In `tools/ci-local.sh`, after the works-links block:

```bash
python3 tools/check_works_links.py
python3 -m unittest tools/test_check_works_links.py -v 2>&1 | tail -3
```

insert immediately after (before `python3 tools/check_library_fixtures.py`):

```bash
python3 tools/check_poetry_synced.py
python3 -m unittest tools/test_check_poetry_synced.py -v 2>&1 | tail -3
```

- [ ] **Step 3: Sanity-check the new linter lines run in isolation**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && python3 tools/check_poetry_synced.py && python3 -m unittest tools/test_check_poetry_synced.py -v 2>&1 | tail -3`
Expected: `check_poetry_synced: OK` then `OK`.

- [ ] **Step 4: Commit**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
git add .github/workflows/hugo.yaml tools/ci-local.sh
git commit -m "ci: wire synced-poetry linter pair (workflow + ci-local)"
```

---

## Task 9: CLAUDE.md updates

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the linter-pair count + enumeration**

In the `## Commands` section, change `Twenty linter pairs under tools/check_*.py ...` to `Twenty-one linter pairs ...` and insert `synced poetry, ` into the enumerated list immediately after `works links, ` (so the works grouping reads `… works fixtures, works links, synced poetry, library fixtures, …`).

- [ ] **Step 1b: Reconcile the Deployment step counts (verified, not guessed)**

In the `### Deployment` section, the pre-build parenthetical is pre-existing-stale (`17 linter pairs` while Commands already said twenty) AND this slice adds the 21st pair (+2 named workflow steps). The correct figures were verified against the actual workflow (`grep -c '^      - name:' .github/workflows/hugo.yaml` → 55; 21 paired linters; `check_graph_chrome.py` is the one pre-build sibling-less step; pre-build = contrast 1 + 21·2 + 1 = 44). Make these three exact replacements on the Deployment line:
- `contrast + 17 linter pairs + 1 sibling-less = 36 steps` → `contrast + 21 linter pairs + 1 sibling-less = 44 steps`
- `Total: 53 named steps` → `Total: 55 named steps`

(These are now exactly accurate against the workflow; this also closes the long-standing Commands-vs-Deployment count drift.)

- [ ] **Step 2: Update the JS pipeline entry table**

In `### JS pipeline — multi-entry bundling`, change "runs Hugo's `js.Build` (esbuild) nine times" to "ten times" and add a table row:

```
| `js/entry-poetry.js` | `poetry.<hash>.js` (~6–8 KB) | `.Section == "works"` AND `.Kind == "page"` AND `.Type == "works-poetry"` | `poem-synced.js` — synced-reveal runtime; player built in JS |
```

- [ ] **Step 3: Add §45 to the CSS pipeline section**

In `### CSS pipeline`, extend the parenthetical section list: after `§44 covers the library umbrella redesign ...` add `; §45 covers the synced-poetry runtime (reveal opacity/flourish + JS-built player chrome)`.

- [ ] **Step 4: Update project status**

In `## Project status`, move Time-synced poetry out of the "Designed but not yet implemented" table and add it to the **Shipped** line; update the recommended sequencing line so the next slice is "Phase 3 Slice 1 (garden publish)". Add a `### Deferred features` row note: `Audio-driven playback QA (real recording) | Synced poetry shipped; author records reading | example-poem-synced fixture uses dummy absolute audio_url → animation-fallback path exercised live`.

- [ ] **Step 5: Update the partials inventory + reference docs**

In `### Content & layouts`, add to the `works/` subfolder partial list: `synced-marker-seconds`, `synced-text-parser`, `poem-synced`. In `## Reference docs`, mark the Time-synced poetry line: append `+ `docs/superpowers/plans/2026-05-18-time-synced-poetry.md` (plan). Shipped.`

- [ ] **Step 6: Commit**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry
git add CLAUDE.md
git commit -m "docs(claude.md): register synced-poetry slice (shipped)"
```

---

## Task 10: Full CI-local + dev-server spot-check + branch finish

> **Step 0 — Critical fix from the final holistic review (C1 + C2).** The
> per-task reviews verified spec-fidelity but no task loaded a built page and
> watched a reveal; the whole-branch review found the reveal is **inert** on
> the primary path:
> - **C1:** the parser wraps word/uniform lines as
>   `<span class="poem-line" data-t> <span class="poem-word" data-t>…</span></span>`;
>   §45 dims **both** `.poem-word` *and* `.poem-line[data-t]` to `opacity:.06`;
>   JS adds `.is-visible` only to `.poem-word`. CSS opacity composites
>   multiplicatively → a revealed word renders at `1 × .06`. Word-mode reveal
>   (the fixture's path) never visibly happens.
> - **C2:** JS `wordSel.length ? wordSel : lineSel` is all-or-nothing; a poem
>   mixing word lines + a markdown line-mode line (the fixture's `*irure*`
>   line, spec §4 ¶172–174) never tracks the markdown line → it never reveals.
>
> **Root cause:** spec §4's DOM puts `data-t` on the word-wrapper line while
> spec §7's CSS dims `.poem-line[data-t]` — mutually inconsistent. The
> word-wrapper line's `data-t` is redundant (timing is per-word there).
>
> **Coherent fix (parser + JS; CSS §45 unchanged):**
> 1. `synced-text-parser.html`: the mid-marker word branch (line 82) and the
>    plain uniform-words branch (line 96) emit the wrapper as
>    `<span class="poem-line">%s</span>` — **drop `data-t` and the `$lineT`
>    printf arg**. The inline-markdown branch (line 86) is **unchanged**
>    (`<span class="poem-line" data-t="%g">` — line-mode IS line-timed).
>    Net contract: *`data-t` on an element ⇒ that element is individually
>    timed & dimmed*; word-wrapper lines are pure structure (opacity 1).
> 2. `poem-synced.js` `setupOne`: replace the all-or-nothing ternary with the
>    **union** of `.poem-word[data-t]` ∪ `.poem-line[data-t]` (now
>    non-overlapping, since word-wrapper lines lost `data-t`). Markdown
>    line-mode lines + words are all tracked → mixed poems reveal fully.
> 3. `assets/css/main.css` §45: **no change** — `.poem-line[data-t]` now
>    matches only markdown line-mode lines (correctly dimmed/revealed as a
>    unit); word-wrapper `.poem-line` (no `data-t`) is undimmed so its
>    revealed `.poem-word` children composite at full opacity.
>
> Spec deviation (necessary, documented): the spec §4 DOM example shows
> `data-t` on the word-wrapper line — dropped here because §4-DOM + §7-CSS
> taken literally yield a non-functional reveal. Task 4 Step 5's
> `grep -o 'data-t="12.5"'` still passes (the uniform branch puts `$lineT`
> on the *word* spans, line 93). Verify post-fix that built word spans reach
> effective opacity 1 on reveal (DOM-structure + logic trace) and the
> `*irure*` markdown line still carries `data-t="16"`.

- [ ] **Step 1: Run the full CI-equivalent locally**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && tools/ci-local.sh 2>&1 | tail -40`
Expected: ends with `CI-EQUIVALENT GREEN — safe to push`.

> Per memory `feedback_always_run_ci_locally.md` this is mandatory before any push. Per `reference_ci_local_lhci_deps.md`, LHCI needs `npx` + chromium on PATH; mobile-perf scores are CPU-sensitive locally (expect 5–8pt variance vs CI) — a `/garden/` mobile-LHCI dip is a documented pre-existing local-variance, not a regression from this slice (memory `project_toc_collapsible_subsections_slice.md`). If only that gate dips locally, note it and proceed.

- [ ] **Step 2: Dev-server spot-check (visual verification)**

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.worktrees/time-synced-poetry && pkill -f 'hugo server' 2>/dev/null || true; (hugo server --buildDrafts >/tmp/hugo-poetry.log 2>&1 &) ; sleep 4 && grep -o 'http://localhost:[0-9]*' /tmp/hugo-poetry.log | head -1`

Then present this **"what to eyeball"** checklist to the user (memory `feedback_verify_before_merge.md`, `feedback_test_at_half_screen_1080p.md`) at `/works/poetry/example-poem-synced/`:

1. Page initially shows the poem at ~6% opacity with a player bar above it.
2. ▶ Play → words fade in on the timeline with a brief italic flourish; time display counts up; progress fill advances. (Audio fails on the dummy URL → console warns, runtime auto-falls-back to **animation mode** — this is expected and is the live test of that path.)
3. ⏸ pauses; ↻ resets to hidden + 0:00.
4. Click/drag the progress bar seeks; words before the point are shown, after are hidden.
5. 👁 Show all → entire poem snaps visible (button turns burgundy); toggling off returns to timeline state.
6. The `*irure*` line renders as italic *irure* (markdown survived).
7. No literal `[mm:ss]` brackets anywhere except the escaped `[00:99]`, which appears as plain text.
8. Markerless poems (`/works/poetry/example-poem-minimal/`) render normally with **no** player.
9. Check at ~960px (half-screen 1080p) and ≤480px: at ≤480px the progress bar wraps to its own full-width row below the buttons.
10. Toggle the OS reduced-motion setting: reveal becomes instant (no fade/flourish), Show-all still works.

Stop the dev server after: `pkill -f 'hugo server'`.

- [ ] **Step 3: Finish the development branch**

Invoke `superpowers:finishing-a-development-branch` to present merge / PR / cleanup options. Per memory `feedback_verify_before_merge.md`, obtain explicit user authorization (after the spot-check) before merge + push to `master`.

- [ ] **Step 4: Post-merge — write the shipped-slice memory**

After merge + push: add `project_time_synced_poetry_slice.md` to memory (merge hash, what shipped, the audio-QA deferral, the helper-partial deviation), add the one-line pointer to `MEMORY.md`, and delete/refresh `project_next_slice_time_synced_poetry.md` (it is now stale — the slice shipped). Update `project_next_slice_*` to point at the new next slice (Phase 3 Slice 1 — garden publish), or replace it with a fresh "next slice" memory.

---

## Self-Review

**1. Spec coverage:**
- §1 scope / two modes / player UI / fade-in flourish → Tasks 4–6 (parser, JS, CSS).
- §2 Hugo-side parse, DOM-first, mode by `data-audio-src` → Tasks 4, 5.
- §3 marker grammar incl. all edge cases (untimed +0.5, escape, non-monotonic, audio fail) → parser Task 4 + JS Task 5 + linter Task 2. **§3's two "Linter warns" rows (untimed-line, trailing-marker) were added to Task 2's linter during execution (see the Task 2 amendment note) — initially missed in this plan; fixed.**
- §4 auto-detection routing, partial signatures, per-line/per-word logic, build-time stripping → Task 4 (router counts real = total − escaped; `.RawContent` is already frontmatter-free, improving on the spec's "strip frontmatter" wording; per-token leading-marker handling so glued `[mm:ss]word` times the word per spec §3; `data-duration` = max **effective** span time — refinement of §4's literal "max [mm:ss]" so trailing untimed lines aren't stranded past duration, documented inline in Task 4 Step 5). §4's "markers never appear in the rendered HTML" is honored for the body (parser strips/round-trips) **and** for `<meta>`/`og:description` (Task 4 Step 4b strips `[mm:ss]` from the `head.html` description fallback + the fixture carries an explicit `summary:`) — gap surfaced by the Task 4 implementer's leak diagnosis, fixed in-slice.
- §5 `audio_url` frontmatter (relative/absolute/absent) → Task 1 (fixture-linter accepts), Task 2 (validity), Task 5 (runtime resolves).
- §6 JS runtime responsibilities 1–10 → Task 5 (`poem-synced.js` covers init, mode, JS-built player, play/pause, reveal+flourish, reset, seek drag, show-all, audio-error fallback).
- §7 CSS §45 verbatim → Task 6.
- §8 linter pair (all 6 checks) + §8 fixture-linter `audio_url` extension → Tasks 1, 2.
- §9 cite-note integration → Task 7 (citation export already shipped, so in scope).
- §10 out-of-scope items — none implemented (correctly excluded).
- §11 touched-files list → matches the File Structure table (plus the documented `synced-marker-seconds.html` helper).

**2. Placeholder scan:** No TBD/TODO/"handle edge cases"/"similar to". Every code step contains complete content; every command has expected output.

**3. Type/name consistency:** `.poem-synced` / `.poem-stanza` / `.poem-line` / `.poem-word` / `data-t` / `data-duration` / `data-audio-src` / `is-visible` / `is-current` / `is-show-all` / `poem-player*` are identical across parser (Task 4), JS (Task 5), and CSS (Task 6). `lint_file → (errors, warnings)` and `run → (rc, errors)` signatures are consistent between `check_poetry_synced.py` and its test (Task 2). `audio_url` key spelled identically in fixture (Task 3), fixture-linter (Task 1), synced linter (Task 2), parser/entry partial (Task 4), and cite note (Task 7).
