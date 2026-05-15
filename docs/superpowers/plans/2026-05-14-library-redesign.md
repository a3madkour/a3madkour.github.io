# Library Redesign + Icon Provenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign `/library/` umbrella from uniform 4-card grid into hero + themed cross-medium shelves + catalogue block, while replacing 11 AI-drafted SVG icons with Lucide (ISC) — closes the spec §1 hard-constraint violation surfaced mid-brainstorm.

**Architecture:** Two layers in one slice. Layer 2 (icon provenance) lands first as a mechanical content swap — closes the §1 violation early and is independent of Layer 1. Layer 1 (library redesign) builds on top with new data files, partials, CSS §44, and one new JS module for keyboard nav. TDD via linter-first per layer.

**Tech Stack:** Hugo extended 0.148.0 · stdlib Python 3 · esbuild via Hugo `js.Build` · hand-rolled CSS · no npm. Pre-existing patterns: per-slice linter pair (`tools/check_<slice>.py` + sibling `test_…`), CSS sections numbered §1–§44, multi-entry JS bundles via `partials/scripts.html`.

**Reference docs:** spec `docs/superpowers/specs/2026-05-14-library-redesign-design.md` (committed at `b27b331`); CLAUDE.md (project architecture).

**Real icon inventory** (spec §5.1 used approximate filenames — these are the actual paths):

| Current path | Lucide source | Action |
|---|---|---|
| `assets/images/icons/library/book.svg` | `book-open.svg` | Swap content |
| `assets/images/icons/library/clapper.svg` | `clapperboard.svg` | Swap content |
| `assets/images/icons/glyph-music.svg` | `music.svg` | Swap content |
| `assets/images/icons/glyph-game.svg` | `gamepad-2.svg` | Swap content |
| `assets/images/icons/glyph-poetry.svg` | `feather.svg` | Swap content |
| `assets/images/icons/output-code.svg` | `code.svg` | Swap content |
| `assets/images/icons/output-paper.svg` | `file-text.svg` | Swap content |
| `assets/images/icons/output-talk.svg` | `presentation.svg` | Swap content |
| `assets/images/icons/search.svg` | `search.svg` | Swap content |
| `assets/images/icons/rss.svg` | `rss.svg` | Swap content |
| `assets/images/icons/sun.svg` | `sun.svg` | Swap content |
| `assets/images/icons/monogram-am.svg` | — | Delete; replace with CSS |

**Strategy:** keep existing filenames (zero reference updates needed in templates); swap each file's content to Lucide path data + add the canonical attribution header. Total: **11 content swaps + 1 deletion = 12 file changes** under `assets/images/icons/`.

---

## Phase 0 — Setup

### Task 0.1: Cut feature branch

**Files:**
- Modify: (git only)

- [ ] **Step 1: Verify clean working tree**

Run:
```
git status
```
Expected: only `CLAUDE.md` modified (from the pre-brainstorm session — leave it).

- [ ] **Step 2: Create feature branch**

```
git checkout -b feature/library-redesign
```

- [ ] **Step 3: Confirm**

Run: `git branch --show-current`
Expected: `feature/library-redesign`

---

## Phase 1 — Layer 2 (Icon-provenance close-out)

### Task 1.1: Add Lucide license file

**Files:**
- Create: `LICENSES/lucide-ISC.txt`

- [ ] **Step 1: Create license file**

Fetch the upstream ISC license text:
```
mkdir -p LICENSES
curl -fsSL https://raw.githubusercontent.com/lucide-icons/lucide/main/LICENSE -o LICENSES/lucide-ISC.txt
```

- [ ] **Step 2: Verify**

Run: `head -3 LICENSES/lucide-ISC.txt`
Expected: ISC License header text including "Copyright (c) ... Lucide Contributors".

- [ ] **Step 3: Commit**

```
git add LICENSES/lucide-ISC.txt
git commit -m "icons: vendor Lucide ISC license"
```

---

### Task 1.2: Create THIRD_PARTY.md

**Files:**
- Create: `THIRD_PARTY.md`

- [ ] **Step 1: Write the file**

```markdown
# Third-party assets

This site bundles a small number of third-party assets. Each entry below lists the
upstream source, the license, and where the license text is mirrored in this repo.

## Icons

**Lucide** — https://lucide.dev — version 1.16.0 — ISC License
License text: [`LICENSES/lucide-ISC.txt`](LICENSES/lucide-ISC.txt)

Used files (under `assets/images/icons/`):

- `glyph-game.svg` — Lucide `gamepad-2`
- `glyph-music.svg` — Lucide `music`
- `glyph-poetry.svg` — Lucide `feather`
- `library/book.svg` — Lucide `book-open`
- `library/clapper.svg` — Lucide `clapperboard`
- `output-code.svg` — Lucide `code`
- `output-paper.svg` — Lucide `file-text`
- `output-talk.svg` — Lucide `presentation`
- `rss.svg` — Lucide `rss`
- `search.svg` — Lucide `search`
- `sun.svg` — Lucide `sun`

## Fonts

Google Fonts (Open Font License) — Petrona, Inter, JetBrains Mono. Loaded via CDN
in `layouts/partials/head.html`; no font files vendored in this repo.
```

- [ ] **Step 2: Commit**

```
git add THIRD_PARTY.md
git commit -m "third-party: document Lucide icons + Google Fonts provenance"
```

---

### Task 1.3: Linter pair #19 — scaffold RED

**Files:**
- Create: `tools/check_icon_attribution.py`
- Create: `tools/test_check_icon_attribution.py`
- Create: `tools/.icon-attribution-exceptions.yaml`

- [ ] **Step 1: Write the failing test file**

```python
# tools/test_check_icon_attribution.py
"""Tests for check_icon_attribution.py — run with:
   python3 -m unittest tools/test_check_icon_attribution.py -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_icon_attribution as lint  # noqa: E402


LUCIDE_HEADER = '<!-- Lucide v1.16.0 — book-open · ISC License · see /THIRD_PARTY.md -->\n'
GOOD_SVG = LUCIDE_HEADER + '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0"/></svg>\n'
NO_HEADER_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0"/></svg>\n'

THIRD_PARTY_GOOD = """# Third-party assets

## Icons

**Lucide** — https://lucide.dev — ISC License
"""

THIRD_PARTY_NO_LUCIDE = """# Third-party assets

## Icons

Hand-authored only.
"""

EXCEPTIONS_YAML = """exceptions:
  - file: custom-mark.svg
    provenance: "Hand-drawn by author 2026-05-14"
"""


def make_project(td: Path, *, third_party: str | None, icons: dict[str, str], exceptions: str | None) -> Path:
    """Build a synthetic project root inside td. Return the root path."""
    root = td / "project"
    (root / "assets" / "images" / "icons").mkdir(parents=True)
    (root / "tools").mkdir(parents=True)
    if third_party is not None:
        (root / "THIRD_PARTY.md").write_text(third_party)
    for name, body in icons.items():
        target = root / "assets" / "images" / "icons" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    if exceptions is not None:
        (root / "tools" / ".icon-attribution-exceptions.yaml").write_text(exceptions)
    return root


class IconAttributionTest(unittest.TestCase):

    def test_happy_path_all_have_headers(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(
                Path(td),
                third_party=THIRD_PARTY_GOOD,
                icons={"book-open.svg": GOOD_SVG, "music.svg": GOOD_SVG},
                exceptions=None,
            )
            errors = lint.lint_icon_attribution(root)
            self.assertEqual(errors, [])

    def test_missing_third_party_md(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), third_party=None, icons={"book-open.svg": GOOD_SVG}, exceptions=None)
            errors = lint.lint_icon_attribution(root)
            self.assertTrue(any("THIRD_PARTY.md" in e for e in errors))

    def test_third_party_lacks_lucide_mention(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), third_party=THIRD_PARTY_NO_LUCIDE, icons={"book-open.svg": GOOD_SVG}, exceptions=None)
            errors = lint.lint_icon_attribution(root)
            self.assertTrue(any("Lucide" in e for e in errors))

    def test_svg_without_header(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), third_party=THIRD_PARTY_GOOD, icons={"bad.svg": NO_HEADER_SVG}, exceptions=None)
            errors = lint.lint_icon_attribution(root)
            self.assertTrue(any("bad.svg" in e for e in errors))

    def test_svg_in_exceptions_passes(self):
        with tempfile.TemporaryDirectory() as td:
            exc = "exceptions:\n  - file: bad.svg\n    provenance: \"OK\"\n"
            root = make_project(Path(td), third_party=THIRD_PARTY_GOOD, icons={"bad.svg": NO_HEADER_SVG}, exceptions=exc)
            errors = lint.lint_icon_attribution(root)
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write the empty linter (so the test can import)**

```python
# tools/check_icon_attribution.py
"""Icon attribution linter. STUB — will be implemented in next task."""
from __future__ import annotations
from pathlib import Path


def lint_icon_attribution(project_root: Path) -> list[str]:
    return ["NOT IMPLEMENTED"]


if __name__ == "__main__":
    import sys
    errors = lint_icon_attribution(Path(__file__).resolve().parent.parent)
    for e in errors:
        print(e)
    sys.exit(1 if errors else 0)
```

- [ ] **Step 3: Write exceptions manifest stub**

```yaml
# tools/.icon-attribution-exceptions.yaml
# Icons that don't carry a Lucide attribution header — must list provenance.
exceptions: []
```

- [ ] **Step 4: Run tests, verify they FAIL**

Run: `python3 -m unittest tools/test_check_icon_attribution.py -v`
Expected: 5 tests RUN; 4 FAIL (test_happy_path_all_have_headers, test_missing_third_party_md, test_third_party_lacks_lucide_mention, test_svg_without_header, test_svg_in_exceptions_passes — all fail because lint returns `["NOT IMPLEMENTED"]`).

- [ ] **Step 5: Commit RED**

```
git add tools/check_icon_attribution.py tools/test_check_icon_attribution.py tools/.icon-attribution-exceptions.yaml
git commit -m "test(icons): scaffold linter pair #19 (RED)"
```

---

### Task 1.4: Linter pair #19 — implement GREEN

**Files:**
- Modify: `tools/check_icon_attribution.py`

- [ ] **Step 1: Replace the stub with the real implementation**

```python
# tools/check_icon_attribution.py
"""Icon attribution linter.

Asserts that every SVG under `assets/images/icons/` either carries the
canonical Lucide attribution header comment OR is listed in the exceptions
manifest. Also asserts THIRD_PARTY.md exists and mentions Lucide.

Exits 0 on success, 1 on any error. Stdlib only. Paired with
tools/test_check_icon_attribution.py.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HEADER_PATTERN = re.compile(
    r"<!--\s*Lucide\s+v[\d.]+\s+—\s+[\w-]+\s+·\s+ISC License\s+·\s+see\s+/THIRD_PARTY\.md\s*-->",
    re.IGNORECASE,
)


def _parse_exceptions(yaml_path: Path) -> set[str]:
    """Tiny YAML reader — we only need a flat list of `file:` keys."""
    if not yaml_path.exists():
        return set()
    files: set[str] = set()
    in_list = False
    for raw in yaml_path.read_text().splitlines():
        line = raw.rstrip()
        if line.strip().startswith("#") or not line.strip():
            continue
        if line.strip() == "exceptions:" or line.strip().startswith("exceptions:"):
            in_list = True
            continue
        if not in_list:
            continue
        m = re.match(r"\s*-\s*file:\s*(.+?)\s*$", line)
        if m:
            files.add(m.group(1).strip().strip('"').strip("'"))
    return files


def lint_icon_attribution(project_root: Path) -> list[str]:
    errors: list[str] = []

    # 1. THIRD_PARTY.md must exist and mention Lucide
    tp = project_root / "THIRD_PARTY.md"
    if not tp.exists():
        errors.append("THIRD_PARTY.md is missing at repo root")
    else:
        body = tp.read_text()
        if "lucide" not in body.lower():
            errors.append("THIRD_PARTY.md exists but does not mention Lucide")

    # 2. Every SVG under assets/images/icons/ must carry the header OR be in exceptions
    icons_dir = project_root / "assets" / "images" / "icons"
    if not icons_dir.exists():
        errors.append("assets/images/icons/ directory is missing")
        return errors

    exceptions = _parse_exceptions(project_root / "tools" / ".icon-attribution-exceptions.yaml")

    for svg in sorted(icons_dir.rglob("*.svg")):
        rel = svg.relative_to(icons_dir).as_posix()
        if rel in exceptions or svg.name in exceptions:
            continue
        head = svg.read_text()[:512]
        if not HEADER_PATTERN.search(head):
            errors.append(f"{svg.relative_to(project_root)}: missing Lucide attribution header (first 512 bytes)")

    return errors


if __name__ == "__main__":
    errors = lint_icon_attribution(Path(__file__).resolve().parent.parent)
    for e in errors:
        print(e)
    sys.exit(1 if errors else 0)
```

- [ ] **Step 2: Run unit tests, verify GREEN**

Run: `python3 -m unittest tools/test_check_icon_attribution.py -v`
Expected: 5 tests, all PASS.

- [ ] **Step 3: Run linter on real project, verify it FAILS** (Lucide attribution headers don't exist yet on real SVGs — by design)

Run: `python3 tools/check_icon_attribution.py`
Expected: non-zero exit; one error line per SVG file (11 errors); plus possibly the THIRD_PARTY.md was added but the icons are still AI-drafted with no headers.

- [ ] **Step 4: Commit**

```
git add tools/check_icon_attribution.py
git commit -m "feat(icons): implement icon-attribution linter (GREEN fixtures, RED project)"
```

---

### Task 1.5: Replace 11 SVG files with Lucide content + headers

**Files:**
- Modify (content only, same names): all 11 SVGs in the table at the top of this plan.

- [ ] **Step 1: Fetch Lucide SVGs to a temp dir**

Run:
```
mkdir -p /tmp/lucide-fetch
cd /tmp/lucide-fetch
for src in book-open music gamepad-2 clapperboard feather code file-text presentation rss search sun; do
  curl -fsSL "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/${src}.svg" -o "${src}.svg"
done
ls *.svg
```
Expected: 11 SVGs downloaded.

- [ ] **Step 2: Replace each existing icon file with Lucide content + header**

For each row in the inventory table, OVERWRITE the existing file. Template (using `library/book.svg` ← `book-open.svg`):

```bash
# Run from project root /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
{ echo '<!-- Lucide v1.16.0 — book-open · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/book-open.svg; } > assets/images/icons/library/book.svg
```

Repeat for all 11 mappings. Concrete commands (exact filenames, exact mappings):

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io

# library/ subdir
{ echo '<!-- Lucide v1.16.0 — book-open · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/book-open.svg; } > assets/images/icons/library/book.svg
{ echo '<!-- Lucide v1.16.0 — clapperboard · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/clapperboard.svg; } > assets/images/icons/library/clapper.svg

# glyph-* family
{ echo '<!-- Lucide v1.16.0 — music · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/music.svg; } > assets/images/icons/glyph-music.svg
{ echo '<!-- Lucide v1.16.0 — gamepad-2 · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/gamepad-2.svg; } > assets/images/icons/glyph-game.svg
{ echo '<!-- Lucide v1.16.0 — feather · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/feather.svg; } > assets/images/icons/glyph-poetry.svg

# output-* family
{ echo '<!-- Lucide v1.16.0 — code · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/code.svg; } > assets/images/icons/output-code.svg
{ echo '<!-- Lucide v1.16.0 — file-text · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/file-text.svg; } > assets/images/icons/output-paper.svg
{ echo '<!-- Lucide v1.16.0 — presentation · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/presentation.svg; } > assets/images/icons/output-talk.svg

# top-level chrome icons
{ echo '<!-- Lucide v1.16.0 — rss · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/rss.svg; } > assets/images/icons/rss.svg
{ echo '<!-- Lucide v1.16.0 — search · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/search.svg; } > assets/images/icons/search.svg
{ echo '<!-- Lucide v1.16.0 — sun · ISC License · see /THIRD_PARTY.md -->'; cat /tmp/lucide-fetch/sun.svg; } > assets/images/icons/sun.svg
```

- [ ] **Step 3: Verify every SVG now passes the linter**

Run: `python3 tools/check_icon_attribution.py`
Expected: exits 0 (no output). Only remaining concern: `monogram-am.svg` is NOT in the swap list — it's deleted in the next task. Until that task lands, the linter will still print one error for monogram-am. To unblock this commit:

Run: `python3 tools/check_icon_attribution.py 2>&1 | head -5`
Expected: 1 error line for `monogram-am.svg`.

- [ ] **Step 4: Build with `hugo --minify`, verify no broken icon references**

Run: `hugo --minify --cleanDestinationDir`
Expected: build succeeds. Open `public/index.html`, `public/about/index.html`, `public/library/index.html`, `public/works/index.html` in browser and check icons render. (Should look identical or very close — Lucide and the AI-drafted icons are similar styles.)

- [ ] **Step 5: Commit**

```
git add assets/images/icons/
git commit -m "feat(icons): swap 11 SVGs for Lucide content + attribution headers"
```

---

### Task 1.6: Replace monogram-am.svg with CSS "AM" disc

**Files:**
- Delete: `assets/images/icons/monogram-am.svg`
- Modify: `layouts/about/single.html` (line 14-16)
- Modify: `assets/css/main.css` (append in the about-page section, currently around §X — locate via grep)

- [ ] **Step 1: Update about template**

Read current `layouts/about/single.html` lines 13-17 to confirm context, then replace lines 14-16:

```html
    <div class="monogram about-monogram" aria-label="A.M. — Abdelrahman Madkour">AM</div>
```

(Drop the `aria-hidden="true"` since the disc IS the meaningful image now; the `aria-label` provides the SR text.)

- [ ] **Step 2: Locate the about-page CSS section + add monogram rules**

Find existing about-page CSS rules:
```
grep -n "\.monogram\|about-hero" assets/css/main.css | head
```

Append to the relevant section (or to the existing `.monogram` rule if present):

```css
.about-monogram {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: var(--color-ink);
  color: var(--color-stone);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 2.4rem;
  letter-spacing: -0.02em;
  line-height: 1;
}
```

If a previous `.monogram` rule was tuned for an SVG (width/height auto, etc.), strip those conflicting properties — `.about-monogram` is sized internally now.

- [ ] **Step 3: Delete the SVG file**

```
git rm assets/images/icons/monogram-am.svg
```

- [ ] **Step 4: Verify linter passes now**

```
python3 tools/check_icon_attribution.py
```
Expected: exits 0 with no output.

- [ ] **Step 5: Verify dev server renders the new monogram**

In a separate terminal, start `hugo server --buildDrafts`; open http://localhost:1313/about/. Confirm the disc displays "AM" in Petrona, white-on-ink, no broken-image icon.

- [ ] **Step 6: Verify contrast**

The disc is `--color-stone` on `--color-ink` (≥AAA in both modes per the contrast linter). Run:
```
python3 tools/check-contrast.py
```
Expected: exits 0.

- [ ] **Step 7: Commit**

```
git add layouts/about/single.html assets/css/main.css
git commit -m "feat(about): replace monogram SVG with CSS 'AM' disc"
```

---

### Task 1.7: Create /credits/ page

**Files:**
- Create: `content/credits/_index.md`
- Create: `layouts/credits/single.html` (Hugo will render a section's `_index.md` via `_default/single.html` if a section-specific layout doesn't exist — but we want to constrain weight and page-sidebar, so creating one is clearer)

- [ ] **Step 1: Write the content stub**

```markdown
---
title: "Credits"
description: "Third-party assets bundled in this site."
date: 2026-05-14
last_modified: 2026-05-14
draft: false
---

This site bundles a small number of third-party assets. Full source + license details are in [`THIRD_PARTY.md`](https://github.com/a3madkour/a3madkour.github.io/blob/master/THIRD_PARTY.md) at the repository root.

## Icons

[Lucide](https://lucide.dev) v1.16.0 — ISC License. Used for the 11 SVG icons across the site (medium glyphs, output-type indicators, header chrome).

## Fonts

[Google Fonts](https://fonts.google.com) under the Open Font License — Petrona (body), Inter (UI), JetBrains Mono (code).
```

- [ ] **Step 2: Write the layout**

```html
{{ define "main" }}
<main class="prose credits-page" data-pagefind-body>
  <header class="credits-header">
    <h1>{{ .Title }}</h1>
    {{ with .Params.description }}<p class="lede">{{ . }}</p>{{ end }}
  </header>
  <article class="credits-body">
    {{ .Content }}
  </article>

  {{/* Pagefind meta */}}
  <span data-pagefind-meta="section:credits" hidden></span>
  <span data-pagefind-filter="section:credits" hidden></span>
</main>
{{ end }}
```

- [ ] **Step 3: Verify build**

Run: `hugo --minify --cleanDestinationDir`
Expected: succeeds. `public/credits/index.html` exists.

- [ ] **Step 4: Verify dev server**

In dev server: visit http://localhost:1313/credits/. Confirm page renders with H1, lede, body content.

- [ ] **Step 5: Commit**

```
git add content/credits/ layouts/credits/
git commit -m "feat(credits): add /credits/ page for third-party attribution"
```

---

### Task 1.8: Add linter to workflow + ci-local.sh

**Files:**
- Modify: `.github/workflows/hugo.yaml`
- Modify: `tools/ci-local.sh`

- [ ] **Step 1: Find the right spot in the workflow**

Run: `grep -n 'check_library_covers\|check_pagefind_meta' .github/workflows/hugo.yaml`
Expected: two named steps. Insert the new linter pair AFTER `check_library_covers` and BEFORE `check_pagefind_meta`.

- [ ] **Step 2: Add two named steps to the workflow**

In `.github/workflows/hugo.yaml`, after the `check_library_covers` block and BEFORE `check_pagefind_meta`:

```yaml
      - name: Lint — icon attribution
        run: python3 tools/check_icon_attribution.py

      - name: Test — icon-attribution linter
        run: python3 -m unittest tools/test_check_icon_attribution.py -v
```

(Use `check_library_shelves` in Layer 1 — Task 2.2 — between these two new steps. The shelves linter doesn't exist yet so add ONLY the icon-attribution steps here.)

- [ ] **Step 3: Mirror in ci-local.sh**

In `tools/ci-local.sh`, after the existing `python3 tools/check_library_covers.py` + `python3 -m unittest tools/test_check_library_covers.py` block, add:

```bash
python3 tools/check_icon_attribution.py
python3 -m unittest tools/test_check_icon_attribution.py -v 2>&1 | tail -3
```

- [ ] **Step 4: Verify both pass locally**

Run: `tools/ci-local.sh`
Expected: succeeds through the new icon-attribution steps; will eventually fail on later steps for other reasons but should pass through the new steps.

- [ ] **Step 5: Commit**

```
git add .github/workflows/hugo.yaml tools/ci-local.sh
git commit -m "ci(icons): wire icon-attribution linter (47 named steps)"
```

---

### Task 1.9: Layer 2 verification + checkpoint commit

- [ ] **Step 1: Run full CI locally**

```
tools/ci-local.sh
```
Expected: passes start-to-finish. If anything else fails (page-weight changes, etc.), fix before continuing.

- [ ] **Step 2: Eyeball changed surfaces**

Start dev server: `hugo server --buildDrafts`. Visit and visually confirm each page renders correctly with the new Lucide icons:

- http://localhost:1313/ (homepage hero, search/RSS/theme icons in header)
- http://localhost:1313/about/ (monogram disc, no SVG broken icons)
- http://localhost:1313/works/ (game/music/poetry glyphs)
- http://localhost:1313/library/ (current 4-card umbrella with book/music/game/clapper glyphs — note: this gets rewritten in Phase 2)
- http://localhost:1313/research/ (output icons on output-items)
- http://localhost:1313/credits/ (new page)

- [ ] **Step 3: Stop dev server, run production build**

(Make sure the dev server is killed — running `hugo --minify` against a live dev server poisons the dev CSS per `reference_hugo_dev_server_gotcha`.)

```
pkill -f "hugo server" 2>/dev/null
sleep 1
rm -rf public
hugo --minify
```
Expected: succeeds.

- [ ] **Step 4: Sanity-check page weights**

Run: `python3 tools/check_page_weights.py`
Expected: passes. The icon swap is content-equivalent so weights should be unchanged.

- [ ] **Step 5: No commit needed — this is a verification gate**

Move on to Phase 2.

---

## Phase 2 — Layer 1 (Library umbrella redesign)

### Task 2.1: Linter pair #18 — scaffold RED

**Files:**
- Create: `tools/check_library_shelves.py`
- Create: `tools/test_check_library_shelves.py`

- [ ] **Step 1: Write the failing test file**

```python
# tools/test_check_library_shelves.py
"""Tests for check_library_shelves.py — run with:
   python3 -m unittest tools/test_check_library_shelves.py -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_library_shelves as lint  # noqa: E402


MEDIA_YAML_GOOD = """media:
  - key: reading
    label: "Reading"
    glyph: book-open
    cover_aspect: portrait
  - key: listening
    label: "Listening"
    glyph: music
    cover_aspect: square
"""

SHELVES_YAML_GOOD = """hero: invisible-cities

shelves:
  - title: "Recently finished"
    intro: "Things I closed the cover on."
    tag: finished
  - title: "Field of game design"
    intro: "Books and papers."
    items:
      - invisible-cities
      - lorem-ipsum-ii
"""

READING_YAML = """items:
  - slug: invisible-cities
    title: "Invisible Cities"
    creator: "Italo Calvino"
    year: 1972
    media_type: book
    status: reading
    last_modified: 2026-04-22
    tags: [fiction, finished]
  - slug: lorem-ipsum-ii
    title: "Lorem Ipsum II"
    creator: "Author II"
    year: 2024
    media_type: book
    status: finished
    last_modified: 2026-05-01
    tags: [non-fiction, finished]
"""

LISTENING_YAML = """items: []
"""


def make_project(td: Path, *, media: str | None, shelves: str | None,
                 reading: str | None, listening: str | None,
                 stubs: dict[str, str] | None = None) -> Path:
    root = td / "project"
    (root / "data").mkdir(parents=True)
    (root / "assets" / "images" / "icons").mkdir(parents=True)
    if media is not None:
        (root / "data" / "library-media.yaml").write_text(media)
    if shelves is not None:
        (root / "data" / "library-shelves.yaml").write_text(shelves)
    if reading is not None:
        (root / "data" / "reading.yaml").write_text(reading)
    if listening is not None:
        (root / "data" / "listening.yaml").write_text(listening)
    # Touch glyph files mentioned in media yaml
    for fname in ("book-open.svg", "music.svg"):
        (root / "assets" / "images" / "icons" / fname).write_text("<!-- stub -->")
    if stubs:
        for slug, body in stubs.items():
            path = root / "content" / "library" / "shelves" / slug / "_index.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
    return root


class LibraryShelvesTest(unittest.TestCase):

    def test_happy_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=SHELVES_YAML_GOOD,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            self.assertEqual(errors, [])

    def test_missing_media_yaml_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=None, shelves=SHELVES_YAML_GOOD,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            self.assertTrue(any("library-media" in e for e in errors))

    def test_missing_shelves_yaml_is_ok(self):
        """Shelves yaml is optional — soft fall-back is documented behaviour."""
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=None,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            self.assertEqual(errors, [])

    def test_shelf_with_both_tag_and_items_fails(self):
        bad = """hero: invisible-cities

shelves:
  - title: "Conflicted"
    intro: "Has both"
    tag: finished
    items:
      - invisible-cities
"""
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=bad,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            self.assertTrue(any("both tag and items" in e.lower() or "exactly one" in e.lower() for e in errors))

    def test_unresolved_hero_slug_warns(self):
        bad = """hero: nonexistent-slug

shelves:
  - title: "OK"
    intro: "Fine"
    tag: finished
"""
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=bad,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            # Per spec §3.5, unresolved hero is a warning not a hard error — but the linter
            # must report it. Implementation may classify as warning OR error.
            self.assertTrue(any("nonexistent-slug" in e or "hero" in e.lower() for e in errors))

    def test_slug_list_with_bad_slug_fails(self):
        bad = """shelves:
  - title: "Bad"
    intro: "Has unresolvable slug"
    items:
      - does-not-exist
"""
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=bad,
                                reading=READING_YAML, listening=LISTENING_YAML)
            errors = lint.lint_library_shelves(root)
            self.assertTrue(any("does-not-exist" in e for e in errors))

    def test_long_shelf_requires_stub(self):
        # 13-item slug list — stub required.
        slug_lines = "\n".join(f"      - lorem-ipsum-{n}" for n in range(13))
        bad = f"""shelves:
  - title: "Long shelf"
    intro: "Has 13 items"
    items:
{slug_lines}
"""
        # Provide a reading yaml that has those slugs so they resolve
        many_reading = "items:\n" + "\n".join(
            f"  - slug: lorem-ipsum-{n}\n    title: \"T{n}\"\n    creator: \"C\"\n    year: 2024\n    media_type: book\n    status: reading\n    last_modified: 2026-05-01\n    tags: [t]"
            for n in range(13)
        )
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=bad,
                                reading=many_reading, listening=LISTENING_YAML, stubs=None)
            errors = lint.lint_library_shelves(root)
            self.assertTrue(any("stub" in e.lower() and "long" in e.lower() or "_index.md" in e for e in errors))

    def test_orphan_stub_fails(self):
        # Stub exists for a shelf that doesn't appear in yaml
        stub = """---
title: "Orphan"
shelf: orphan
type: library-shelf
---
"""
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), media=MEDIA_YAML_GOOD, shelves=SHELVES_YAML_GOOD,
                                reading=READING_YAML, listening=LISTENING_YAML,
                                stubs={"orphan": stub})
            errors = lint.lint_library_shelves(root)
            self.assertTrue(any("orphan" in e.lower() for e in errors))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write the empty linter (so test can import)**

```python
# tools/check_library_shelves.py
"""Library shelves linter. STUB — implemented in next task."""
from __future__ import annotations
from pathlib import Path


def lint_library_shelves(project_root: Path) -> list[str]:
    return ["NOT IMPLEMENTED"]


if __name__ == "__main__":
    import sys
    errors = lint_library_shelves(Path(__file__).resolve().parent.parent)
    for e in errors:
        print(e)
    sys.exit(1 if errors else 0)
```

- [ ] **Step 3: Run tests, verify they FAIL**

Run: `python3 -m unittest tools/test_check_library_shelves.py -v`
Expected: 8 tests, all FAIL (linter returns `["NOT IMPLEMENTED"]`).

- [ ] **Step 4: Commit RED**

```
git add tools/check_library_shelves.py tools/test_check_library_shelves.py
git commit -m "test(library-shelves): scaffold linter pair #18 (RED)"
```

---

### Task 2.2: Linter pair #18 — implement GREEN

**Files:**
- Modify: `tools/check_library_shelves.py`

- [ ] **Step 1: Replace stub with full implementation**

```python
# tools/check_library_shelves.py
"""Library shelves linter.

Asserts:
  - data/library-media.yaml exists, parses, has media[] list with required keys.
  - For each media[].key: data/<key>.yaml exists AND assets/images/icons/<glyph>.svg exists.
  - data/library-shelves.yaml is optional; if present, every shelf has exactly
    one of tag: or items:, every slug in items: resolves to a real library item,
    and any shelf with items: count > 12 has a corresponding content stub.
  - hero: slug (if present) resolves to a real item.
  - No orphan stubs under content/library/shelves/.

Exits 0 on success, 1 on any error. Stdlib only. Paired with
tools/test_check_library_shelves.py.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_MEDIA_KEYS = {"key", "label", "glyph", "cover_aspect"}
MEDIUM_YAMLS = ("reading", "listening", "playing", "watching")
SHELF_ITEM_CAP = 12


def _parse_simple_yaml(text: str) -> dict:
    """A flat-stack YAML reader for the limited shapes we use.

    Handles: top-level keys (string scalars), list-of-maps (each map's keys are
    string scalars or list-of-scalars), nested 2-deep maps. Comments stripped.
    Does NOT handle arbitrary YAML — designed for our specific schemas.
    """
    out: dict = {}
    current_list_key: str | None = None
    current_item: dict | None = None
    current_sublist_key: str | None = None
    current_sublist: list | None = None

    for raw in text.splitlines():
        # Strip comments + trailing whitespace
        line = re.sub(r"\s+#.*$", "", raw).rstrip()
        if not line.strip():
            continue

        # Track indentation
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0 and ":" in stripped and not stripped.startswith("-"):
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            current_sublist_key = None
            current_sublist = None
            if val == "":
                # List or map following
                current_list_key = key
                out[key] = []
                current_item = None
            else:
                # Scalar
                out[key] = _scalar(val)
                current_list_key = None
                current_item = None
        elif current_list_key is not None and stripped.startswith("- "):
            # New list item
            current_item = {}
            out[current_list_key].append(current_item)
            current_sublist_key = None
            current_sublist = None
            rest = stripped[2:].strip()
            if ":" in rest:
                key, _, val = rest.partition(":")
                key = key.strip()
                val = val.strip()
                if val == "":
                    current_sublist_key = key
                    current_sublist = []
                    current_item[key] = current_sublist
                else:
                    current_item[key] = _scalar(val)
        elif current_item is not None and indent >= 2:
            if stripped.startswith("- "):
                # Sublist scalar
                if current_sublist is not None:
                    current_sublist.append(_scalar(stripped[2:].strip()))
                continue
            if ":" not in stripped:
                continue
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "":
                current_sublist_key = key
                current_sublist = []
                current_item[key] = current_sublist
            else:
                current_item[key] = _scalar(val)
                current_sublist_key = None
                current_sublist = None
    return out


def _scalar(s: str):
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_scalar(x.strip()) for x in inner.split(",")]
    if re.match(r"^-?\d+$", s):
        return int(s)
    if re.match(r"^-?\d+\.\d+$", s):
        return float(s)
    return s


def _collect_slugs(project_root: Path) -> set[str]:
    slugs: set[str] = set()
    for key in MEDIUM_YAMLS:
        path = project_root / "data" / f"{key}.yaml"
        if not path.exists():
            continue
        parsed = _parse_simple_yaml(path.read_text())
        for item in parsed.get("items", []) or []:
            slug = item.get("slug")
            if slug:
                slugs.add(slug)
    return slugs


def _slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def lint_library_shelves(project_root: Path) -> list[str]:
    errors: list[str] = []

    # 1. library-media.yaml required
    media_path = project_root / "data" / "library-media.yaml"
    if not media_path.exists():
        errors.append("data/library-media.yaml is missing (required)")
        return errors  # everything downstream depends on this

    media = _parse_simple_yaml(media_path.read_text())
    media_entries = media.get("media", []) or []
    if not media_entries:
        errors.append("data/library-media.yaml has no media entries")
        return errors

    for entry in media_entries:
        missing = REQUIRED_MEDIA_KEYS - set(entry.keys())
        if missing:
            errors.append(f"data/library-media.yaml: entry {entry.get('key', '?')} missing keys: {sorted(missing)}")
        key = entry.get("key")
        if key:
            data_file = project_root / "data" / f"{key}.yaml"
            if not data_file.exists():
                errors.append(f"data/library-media.yaml: media key '{key}' has no matching data/{key}.yaml")
        glyph = entry.get("glyph")
        if glyph:
            # Check both top-level and library/ subdir
            candidates = [
                project_root / "assets" / "images" / "icons" / f"{glyph}.svg",
                project_root / "assets" / "images" / "icons" / "library" / f"{glyph}.svg",
            ]
            if not any(c.exists() for c in candidates):
                errors.append(f"data/library-media.yaml: glyph '{glyph}' has no matching SVG under assets/images/icons/")

    # 2. library-shelves.yaml is optional
    shelves_path = project_root / "data" / "library-shelves.yaml"
    if not shelves_path.exists():
        return errors

    shelves_doc = _parse_simple_yaml(shelves_path.read_text())
    all_slugs = _collect_slugs(project_root)

    # 3. Hero slug (optional)
    hero = shelves_doc.get("hero")
    if hero and hero not in all_slugs:
        errors.append(f"data/library-shelves.yaml: hero slug '{hero}' does not resolve to any library item (warning)")

    # 4. Each shelf
    shelves_list = shelves_doc.get("shelves", []) or []
    shelves_dir = project_root / "content" / "library" / "shelves"
    shelf_slugs_in_yaml: set[str] = set()

    for idx, shelf in enumerate(shelves_list):
        title = shelf.get("title", f"<shelf #{idx}>")
        has_tag = "tag" in shelf and shelf.get("tag")
        has_items = "items" in shelf and shelf.get("items")

        if has_tag and has_items:
            errors.append(f"data/library-shelves.yaml: shelf '{title}' has both tag and items (exactly one allowed)")
            continue
        if not has_tag and not has_items:
            errors.append(f"data/library-shelves.yaml: shelf '{title}' has neither tag nor items (exactly one required)")
            continue
        if not shelf.get("intro"):
            errors.append(f"data/library-shelves.yaml: shelf '{title}' missing intro")

        if has_items:
            items = shelf["items"]
            for slug in items:
                if slug not in all_slugs:
                    errors.append(f"data/library-shelves.yaml: shelf '{title}' items[]: slug '{slug}' does not resolve")
            if len(items) > SHELF_ITEM_CAP:
                shelf_slug = _slugify(title)
                shelf_slugs_in_yaml.add(shelf_slug)
                stub = shelves_dir / shelf_slug / "_index.md"
                if not stub.exists():
                    errors.append(f"data/library-shelves.yaml: long shelf '{title}' ({len(items)} items) requires stub at content/library/shelves/{shelf_slug}/_index.md")

    # 5. Orphan stub check
    if shelves_dir.exists():
        for stub in shelves_dir.glob("*/_index.md"):
            slug = stub.parent.name
            if slug not in shelf_slugs_in_yaml:
                # Try frontmatter `shelf:` field too — accept if it matches any yaml shelf
                fm_match = re.search(r"^shelf:\s*(\S+)\s*$", stub.read_text(), re.MULTILINE)
                yaml_match = fm_match.group(1) if fm_match else None
                if yaml_match and yaml_match in shelf_slugs_in_yaml:
                    continue
                errors.append(f"content/library/shelves/{slug}/_index.md: orphan stub (no corresponding shelf in library-shelves.yaml)")

    return errors


if __name__ == "__main__":
    errors = lint_library_shelves(Path(__file__).resolve().parent.parent)
    for e in errors:
        print(e)
    sys.exit(1 if errors else 0)
```

- [ ] **Step 2: Run unit tests, verify GREEN**

Run: `python3 -m unittest tools/test_check_library_shelves.py -v`
Expected: 8 tests, all PASS. If any fail, fix and re-run before moving on.

- [ ] **Step 3: Run linter on real project, expect failure** (data files don't exist yet)

Run: `python3 tools/check_library_shelves.py`
Expected: exits 1 with `data/library-media.yaml is missing (required)`.

- [ ] **Step 4: Commit GREEN**

```
git add tools/check_library_shelves.py
git commit -m "feat(library-shelves): implement linter (GREEN fixtures, RED project)"
```

---

### Task 2.3: Create fixture data files

**Files:**
- Create: `data/library-media.yaml`
- Create: `data/library-shelves.yaml`
- Create: `content/library/shelves/long-example/_index.md`

- [ ] **Step 1: Write library-media.yaml**

```yaml
# Library medium registry. Adding a new medium = 1 row here + 1 new
# data/<key>.yaml file + 1 layout for the leaf page.
media:
  - key: reading
    label: "Reading"
    glyph: book        # resolves to assets/images/icons/library/book.svg (post-icon-swap)
    cover_aspect: portrait
  - key: listening
    label: "Listening"
    glyph: glyph-music
    cover_aspect: square
  - key: playing
    label: "Playing"
    glyph: glyph-game
    cover_aspect: portrait
  - key: watching
    label: "Watching"
    glyph: clapper
    cover_aspect: portrait
```

(Note: glyph names are the current SVG filenames without `.svg` extension. The linter checks both top-level and library/ subdir.)

- [ ] **Step 2: Write library-shelves.yaml — example shelves**

```yaml
# Library curation file. Each shelf is either tag-driven (tag: <name>) or
# hand-curated (items: [<slug>, …]). hero: optionally pins a featured item.
hero: invisible-cities

shelves:
  - title: "Recently finished"
    intro: "Things I closed the cover on this season."
    tag: finished

  - title: "Field of game design"
    intro: "Books and papers that shaped how I think about games."
    items:
      - lorem-ipsum-iii    # adjust to slugs that actually exist in your fixtures

  - title: "Long evenings"
    intro: "Soundtrack for late writing."
    tag: jazz

  # A 13-item shelf demonstrates the stub requirement (linter expects a stub for >12 items).
  - title: "Long example"
    intro: "Used to exercise the long-shelf detail-page pattern."
    items:
      - lorem-ipsum-ii
      - lorem-ipsum-iii
      - lorem-ipsum-iv
      - lorem-ipsum-v
      - lorem-ipsum-vi
      - lorem-ipsum-vii
      - lorem-ipsum-viii
      - lorem-ipsum-ix
      - lorem-ipsum-x
      - lorem-ipsum-xi
      - lorem-ipsum-xii
      - lorem-ipsum-xiii
      - lorem-ipsum-xiv
```

(Adjust slugs to match real items in your `data/{reading,listening,playing,watching}.yaml` fixtures. If you don't have 13+ real fixture slugs, either lower the cap test to a shelf with 13 fictional slugs OR add fixture items in the medium yamls to support it.)

- [ ] **Step 3: Write the long-example stub**

```markdown
---
title: "Long example"
shelf: long-example
type: library-shelf
summary: "Used to exercise the long-shelf detail-page pattern. Lorem ipsum fixture content."
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Items below.
```

- [ ] **Step 4: Verify linter passes**

Run: `python3 tools/check_library_shelves.py`
Expected: exits 0, no output. If any errors come back about unresolved slugs, either fix the yaml to use existing fixture slugs OR add fixture items to the medium yamls to cover the slugs.

- [ ] **Step 5: Commit**

```
git add data/library-media.yaml data/library-shelves.yaml content/library/shelves/
git commit -m "feat(library): seed library-media + library-shelves yaml fixtures"
```

---

### Task 2.4: Create medium-rail partial

**Files:**
- Create: `layouts/partials/library/medium-rail.html`

- [ ] **Step 1: Write the partial**

```html
{{/* Medium pill rail for the library umbrella. Reads site.Data.library-media. */}}
{{- $media := index site.Data "library-media" -}}
{{- $section := .Section | default "" -}}
<nav class="medium-rail" aria-label="Library mediums">
  <a class="medium-pill {{ if eq $section "library" }}is-active{{ end }}" href="/library/" data-key="all">All</a>
  {{- range $entry := $media.media }}
  <a class="medium-pill" href="/library/{{ $entry.key }}/" data-key="{{ $entry.key }}">{{ $entry.label }}</a>
  {{- end }}
</nav>
```

- [ ] **Step 2: Verify Hugo can resolve the partial reference**

Run: `hugo --quiet 2>&1 | head` (Hugo will warn but build until the partial is referenced from a layout).

- [ ] **Step 3: Commit**

```
git add layouts/partials/library/medium-rail.html
git commit -m "feat(library): add medium-rail partial"
```

---

### Task 2.5: Create umbrella-catalogue partial

**Files:**
- Create: `layouts/partials/library/umbrella-catalogue.html`

- [ ] **Step 1: Write the partial**

```html
{{/* Bottom 'Browse the catalogue' block. N cards = one per medium in the registry. */}}
{{- $media := index site.Data "library-media" -}}
<section class="library-catalogue" id="catalogue" aria-labelledby="catalogue-heading">
  <h2 id="catalogue-heading">Browse the catalogue</h2>
  <div class="library-cat-cards">
    {{- range $entry := $media.media }}
    {{- $key := $entry.key -}}
    {{- $items := index site.Data $key -}}
    {{- $count := len $items.items -}}
    <a class="library-cat-card" href="/library/{{ $key }}/" aria-label="{{ $entry.label }} — {{ $count }} items">
      <span class="library-cat-disc" aria-hidden="true">
        {{- with resources.Get (printf "images/icons/library/%s.svg" $entry.glyph) -}}
          {{ .Content | safeHTML }}
        {{- else -}}
          {{- with resources.Get (printf "images/icons/%s.svg" $entry.glyph) -}}
            {{ .Content | safeHTML }}
          {{- end -}}
        {{- end -}}
      </span>
      <span class="library-cat-name">{{ $entry.label }}</span>
      <span class="library-cat-count">{{ $count }}</span>
    </a>
    {{- end }}
  </div>
</section>
```

- [ ] **Step 2: Commit**

```
git add layouts/partials/library/umbrella-catalogue.html
git commit -m "feat(library): add umbrella-catalogue partial"
```

---

### Task 2.6: Create umbrella-tile partial

**Files:**
- Create: `layouts/partials/library/umbrella-tile.html`

- [ ] **Step 1: Write the partial**

```html
{{/* One library tile. Input dict: { item: <medium-item-map>, medium: <medium-entry-from-registry> } */}}
{{- $item := .item -}}
{{- $medium := .medium -}}
{{- $kind := default "item" $item.media_type -}}
{{- $aspect := default "portrait" $medium.cover_aspect -}}
<article class="library-tile" data-medium="{{ $medium.key }}">
  <a class="library-tile-link" href="/library/{{ $medium.key }}/#{{ $item.slug }}">
    <div class="library-cover-wrap library-cover-{{ $aspect }}">
      {{- $cover := default "" $item.extras.cover_file -}}
      {{- if $cover -}}
        <img class="library-cover" src="/library/covers/{{ $cover }}" alt="" loading="lazy" decoding="async" width="140" height="{{ if eq $aspect "square" }}140{{ else }}190{{ end }}">
      {{- else if $item.extras.cover_url -}}
        <img class="library-cover" src="{{ $item.extras.cover_url }}" alt="" loading="lazy" decoding="async" width="140" height="{{ if eq $aspect "square" }}140{{ else }}190{{ end }}">
      {{- else -}}
        <div class="library-glyph-block {{ $medium.key }}" aria-hidden="true">
          {{- with resources.Get (printf "images/icons/library/%s.svg" $medium.glyph) -}}{{ .Content | safeHTML }}{{- else -}}{{- with resources.Get (printf "images/icons/%s.svg" $medium.glyph) -}}{{ .Content | safeHTML }}{{- end -}}{{- end -}}
        </div>
      {{- end -}}
      <span class="library-badge" aria-hidden="true">
        {{- with resources.Get (printf "images/icons/library/%s.svg" $medium.glyph) -}}{{ .Content | safeHTML }}{{- else -}}{{- with resources.Get (printf "images/icons/%s.svg" $medium.glyph) -}}{{ .Content | safeHTML }}{{- end -}}{{- end -}}
      </span>
    </div>
    <h4 class="library-tile-title">{{ $item.title }}</h4>
    <p class="library-tile-meta">{{ $item.creator }}{{ with $item.year }} · {{ . }}{{ end }}</p>
  </a>
  <script class="cite-data" type="application/json">{{ partial "cite/data-blob" (dict "self_only" true "item" $item "kind" $kind) | safeJS }}</script>
  <div class="library-tile-actions">
    <button class="cite-cta" type="button" data-kind="{{ $kind }}">Cite this {{ $kind }}</button>
    {{- with $item.note_slug }}<a class="ref-cite-note" href="/garden/{{ . }}/">Note</a>{{- end }}
    {{- with $item.canonical_url }}<a class="ref-cite-source" href="{{ . }}" rel="external">Original</a>{{- end }}
  </div>
</article>
```

(Note: this assumes `partials/cite/data-blob.html` accepts a `self_only` flag — verify with the existing cite-export slice's data-blob signature. If it doesn't, write an inline JSON blob with just `{self: {…}, refs: []}` directly in this partial.)

- [ ] **Step 2: Verify cite/data-blob signature**

Run: `head -30 layouts/partials/cite/data-blob.html`
If the existing partial doesn't support a `self_only` flag, inline a minimal JSON blob:

```html
<script class="cite-data" type="application/json">{
  "self": {
    "citekey": "madkour-{{ $item.year }}-{{ $item.slug }}",
    "title": "{{ $item.title }}",
    "creator": "{{ $item.creator }}",
    "year": {{ $item.year }},
    "kind": "{{ $kind }}",
    "url": "{{ $item.canonical_url }}",
    "notes_ref": "{{ $item.note_slug }}",
    "formats": {}
  },
  "refs": []
}</script>
```

- [ ] **Step 3: Commit**

```
git add layouts/partials/library/umbrella-tile.html
git commit -m "feat(library): add umbrella-tile partial"
```

---

### Task 2.7: Create umbrella-shelf partial

**Files:**
- Create: `layouts/partials/library/umbrella-shelf.html`

- [ ] **Step 1: Write the partial**

```html
{{/* One library shelf. Input dict: { shelf: <shelf-map-from-yaml>, media_index: <slug -> medium-entry> } */}}
{{- $shelf := .shelf -}}
{{- $media_index := .media_index -}}
{{- $title := $shelf.title -}}
{{- $shelf_slug := urlize $title -}}
{{- $cap := 12 -}}

{{/* Resolve items: tag-driven or slug-list */}}
{{- $items := slice -}}
{{- if $shelf.items -}}
  {{- range $slug := $shelf.items -}}
    {{- $resolved := index $media_index $slug -}}
    {{- if $resolved -}}
      {{- $items = $items | append $resolved -}}
    {{- end -}}
  {{- end -}}
{{- else if $shelf.tag -}}
  {{- $tag := $shelf.tag -}}
  {{- range $slug, $entry := $media_index -}}
    {{- $item := $entry.item -}}
    {{- if in $item.tags $tag -}}
      {{- $items = $items | append $entry -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{- $cap_reached := gt (len $items) $cap -}}
{{- $see_all := "" -}}
{{- if $shelf.tag -}}
  {{- $see_all = printf "/tags/%s/" (urlize $shelf.tag) -}}
{{- else if $cap_reached -}}
  {{- $see_all = printf "/library/shelves/%s/" $shelf_slug -}}
{{- end -}}

{{/* Hide shelf entirely if it resolves to zero items */}}
{{- if not $items -}}{{/* no output */}}{{- else -}}
<section class="library-shelf" id="shelf-{{ $shelf_slug }}" aria-labelledby="shelf-{{ $shelf_slug }}-heading">
  <header class="library-shelf-head">
    <h2 id="shelf-{{ $shelf_slug }}-heading">{{ $title }}</h2>
    {{- with $shelf.intro }}<p class="library-shelf-intro">{{ . }}</p>{{ end -}}
    {{- with $see_all }}<a class="library-shelf-see-all" href="{{ . }}">See all</a>{{ end -}}
  </header>
  <div class="library-shelf-strip" role="list">
    {{- range $idx, $entry := first $cap $items -}}
      <div role="listitem">{{ partial "library/umbrella-tile.html" (dict "item" $entry.item "medium" $entry.medium) }}</div>
    {{- end -}}
  </div>
</section>
{{- end -}}
```

- [ ] **Step 2: Commit**

```
git add layouts/partials/library/umbrella-shelf.html
git commit -m "feat(library): add umbrella-shelf partial"
```

---

### Task 2.8: Create umbrella-hero partial

**Files:**
- Create: `layouts/partials/library/umbrella-hero.html`

- [ ] **Step 1: Write the partial**

```html
{{/* Library hero block. Input dict: { hero_slug: <slug | nil>, media_index: <slug -> medium-entry> } */}}
{{- $hero_slug := .hero_slug -}}
{{- $media_index := .media_index -}}

{{/* Resolve hero: explicit slug → max-last_modified fallback */}}
{{- $entry := "" -}}
{{- if $hero_slug -}}
  {{- $entry = index $media_index $hero_slug -}}
{{- end -}}
{{- if not $entry -}}
  {{/* Fall back: max last_modified across all */}}
  {{- $newest_date := "" -}}
  {{- range $slug, $candidate := $media_index -}}
    {{- $lm := default "1970-01-01" $candidate.item.last_modified -}}
    {{- if gt $lm $newest_date -}}
      {{- $newest_date = $lm -}}
      {{- $entry = $candidate -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{- if not $entry -}}{{/* Library is empty — no hero */}}{{- else -}}
  {{- $item := $entry.item -}}
  {{- $medium := $entry.medium -}}
  {{- $kind := default "item" $item.media_type -}}
  {{- $aspect := default "portrait" $medium.cover_aspect -}}
<article class="library-hero" id="hero" data-medium="{{ $medium.key }}">
  <div class="library-hero-cover-wrap library-cover-{{ $aspect }}">
    {{- if $item.extras.cover_file -}}
      <img class="library-hero-cover" src="/library/covers/{{ $item.extras.cover_file }}" alt="" loading="eager" fetchpriority="high" width="140" height="{{ if eq $aspect "square" }}140{{ else }}190{{ end }}">
    {{- else if $item.extras.cover_url -}}
      <img class="library-hero-cover" src="{{ $item.extras.cover_url }}" alt="" loading="eager" fetchpriority="high" width="140" height="{{ if eq $aspect "square" }}140{{ else }}190{{ end }}">
    {{- else -}}
      <div class="library-glyph-block library-hero-glyph {{ $medium.key }}" aria-hidden="true">
        {{- with resources.Get (printf "images/icons/library/%s.svg" $medium.glyph) -}}{{ .Content | safeHTML }}{{- else -}}{{- with resources.Get (printf "images/icons/%s.svg" $medium.glyph) -}}{{ .Content | safeHTML }}{{- end -}}{{- end -}}
      </div>
    {{- end -}}
  </div>
  <div class="library-hero-body">
    <p class="library-hero-eyebrow">★ Featured · {{ $medium.label }}</p>
    <h2 class="library-hero-title">{{ $item.title }}</h2>
    <p class="library-hero-meta">
      {{ $item.creator }}{{ with $item.year }} · {{ . }}{{ end }}{{ with $item.started }} · started {{ . }}{{ end }}{{ with $item.finished }} · finished {{ . }}{{ end }}
    </p>
    {{- with $item.preview }}<p class="library-hero-preview">{{ . }}</p>{{ end -}}
    <script class="cite-data" type="application/json">{
      "self": {
        "citekey": "madkour-{{ $item.year }}-{{ $item.slug }}",
        "title": "{{ $item.title }}",
        "creator": "{{ $item.creator }}",
        "year": {{ $item.year }},
        "kind": "{{ $kind }}",
        "url": "{{ $item.canonical_url }}",
        "notes_ref": "{{ $item.note_slug }}",
        "formats": {}
      },
      "refs": []
    }</script>
    <div class="library-hero-actions">
      <button class="cite-cta" type="button" data-kind="{{ $kind }}">Cite this {{ $kind }}</button>
      {{- with $item.note_slug }}<a class="ref-cite-note" href="/garden/{{ . }}/">Note</a>{{- end }}
      {{- with $item.canonical_url }}<a class="ref-cite-source" href="{{ . }}" rel="external">Original</a>{{- end }}
    </div>
  </div>
</article>
{{- end -}}
```

- [ ] **Step 2: Commit**

```
git add layouts/partials/library/umbrella-hero.html
git commit -m "feat(library): add umbrella-hero partial"
```

---

### Task 2.9: Rewrite layouts/library/list.html

**Files:**
- Modify: `layouts/library/list.html`
- Delete: `layouts/partials/library/umbrella-card.html`

- [ ] **Step 1: Read current list.html for context**

Run: `cat layouts/library/list.html`. Note the current structure (4 hardcoded umbrella-card partials).

- [ ] **Step 2: Replace with the new umbrella layout**

```html
{{ define "main" }}
{{- $media := index site.Data "library-media" -}}
{{- $shelves := index site.Data "library-shelves" -}}

{{/* Build a unified slug→{item, medium} index across all media yamls */}}
{{- $media_index := dict -}}
{{- range $entry := $media.media -}}
  {{- $key := $entry.key -}}
  {{- $bucket := index site.Data $key -}}
  {{- range $item := $bucket.items -}}
    {{- $media_index = merge $media_index (dict $item.slug (dict "item" $item "medium" $entry)) -}}
  {{- end -}}
{{- end -}}

<main class="library-umbrella prose" data-pagefind-body>
  <header class="library-umbrella-header">
    <h1>{{ .Title }}</h1>
    {{- with .Params.description }}<p class="lede">{{ . }}</p>{{ end -}}
  </header>
  {{ partial "library/medium-rail.html" . }}
  {{- if $shelves -}}
    {{ partial "library/umbrella-hero.html" (dict "hero_slug" $shelves.hero "media_index" $media_index) }}
    {{- range $shelf := $shelves.shelves -}}
      {{ partial "library/umbrella-shelf.html" (dict "shelf" $shelf "media_index" $media_index) }}
    {{- end -}}
  {{- else -}}
    {{/* Soft fall-back: no shelves yaml → hero from max-last_modified */}}
    {{ partial "library/umbrella-hero.html" (dict "hero_slug" "" "media_index" $media_index) }}
  {{- end -}}
  {{ partial "library/umbrella-catalogue.html" . }}

  {{/* Page sidebar */}}
  {{- $sections := slice -}}
  {{- $sections = $sections | append (dict "id" "hero" "label" "Hero") -}}
  {{- if $shelves -}}
    {{- range $shelf := $shelves.shelves -}}
      {{- $sections = $sections | append (dict "id" (printf "shelf-%s" (urlize $shelf.title)) "label" $shelf.title) -}}
    {{- end -}}
  {{- end -}}
  {{- $sections = $sections | append (dict "id" "catalogue" "label" "Browse") -}}
  {{ partial "page-sidebar.html" (dict "sections" $sections) }}

  {{/* Pagefind meta */}}
  <span data-pagefind-meta="section:library" hidden></span>
  <span data-pagefind-filter="section:library" hidden></span>
</main>
{{ end }}
```

- [ ] **Step 3: Delete the obsolete umbrella-card partial**

```
git rm layouts/partials/library/umbrella-card.html
```

- [ ] **Step 4: Verify Hugo build**

```
hugo --quiet --cleanDestinationDir
```
Expected: build succeeds. Open `public/library/index.html`, confirm hero + shelves + catalogue render.

- [ ] **Step 5: Eyeball in dev server**

Start dev server, visit http://localhost:1313/library/. Expect: H1, lede, medium rail, hero block with one item, one or more shelves with tiles, bottom catalogue cards.

- [ ] **Step 6: Commit**

```
git add layouts/library/list.html layouts/partials/library/
git commit -m "feat(library): rewrite umbrella list.html — hero + shelves + catalogue"
```

---

### Task 2.10: Create library-shelf layout for /library/shelves/<slug>/

**Files:**
- Create: `layouts/library-shelf/list.html`

- [ ] **Step 1: Write the section template**

```html
{{ define "main" }}
{{- $shelf_slug := .Params.shelf -}}
{{- $shelves := index site.Data "library-shelves" -}}
{{- $media := index site.Data "library-media" -}}

{{/* Find the shelf in yaml */}}
{{- $found := "" -}}
{{- range $s := $shelves.shelves -}}
  {{- if eq (urlize $s.title) $shelf_slug -}}{{- $found = $s -}}{{- end -}}
{{- end -}}

{{/* Build media index */}}
{{- $media_index := dict -}}
{{- range $entry := $media.media -}}
  {{- $bucket := index site.Data $entry.key -}}
  {{- range $item := $bucket.items -}}
    {{- $media_index = merge $media_index (dict $item.slug (dict "item" $item "medium" $entry)) -}}
  {{- end -}}
{{- end -}}

<main class="library-shelf-page prose" data-pagefind-body>
  <header class="library-shelf-page-header">
    <p class="eyebrow"><a href="/library/">← Library</a></p>
    <h1>{{ .Title }}</h1>
    {{- with .Params.summary }}<p class="lede">{{ . }}</p>{{ end -}}
  </header>
  {{- with .Content }}<article class="library-shelf-page-body">{{ . }}</article>{{ end -}}

  {{- if $found -}}
    <div class="library-shelf-page-grid">
      {{- range $slug := $found.items -}}
        {{- $entry := index $media_index $slug -}}
        {{- if $entry }}{{ partial "library/umbrella-tile.html" (dict "item" $entry.item "medium" $entry.medium) }}{{- end -}}
      {{- end -}}
    </div>
  {{- else -}}
    <p class="library-shelf-empty">Shelf "{{ $shelf_slug }}" not found in <code>data/library-shelves.yaml</code>.</p>
  {{- end -}}

  <span data-pagefind-meta="section:library" hidden></span>
  <span data-pagefind-filter="section:library" hidden></span>
</main>
{{ end }}
```

- [ ] **Step 2: Verify build**

```
hugo --quiet --cleanDestinationDir
```
Expected: build succeeds. `public/library/shelves/long-example/index.html` exists and renders the long shelf.

- [ ] **Step 3: Eyeball in dev server**

Visit http://localhost:1313/library/shelves/long-example/. Expect: H1, summary, grid of all items in the shelf.

- [ ] **Step 4: Commit**

```
git add layouts/library-shelf/
git commit -m "feat(library): add library-shelf section template for long-shelf pages"
```

---

### Task 2.11: CSS §44 — structure + rail

**Files:**
- Modify: `assets/css/main.css`

- [ ] **Step 1: Find the end of the existing CSS and the §43 marker**

Run: `grep -n '^/\* §' assets/css/main.css | tail -3`
Expected: last section heading is §43 (citation export). Add §44 after it.

- [ ] **Step 2: Update the top-of-file index**

Find the comment block at the top of main.css that lists §1–§43. Add `§44 Library umbrella redesign` to the list.

- [ ] **Step 3: Append §44 base layout + medium rail**

```css
/* ───────────────────────────────────────────────────── */
/* §44 Library umbrella redesign                          */
/* Hero + themed shelves + bottom catalogue. Driven by   */
/* data/library-shelves.yaml + data/library-media.yaml.  */
/* ───────────────────────────────────────────────────── */

.library-umbrella {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 1.5rem 4rem;
}

.library-umbrella-header h1 {
  margin-bottom: 0.4rem;
}

.library-umbrella-header .lede {
  color: var(--color-ink-soft);
  font-style: italic;
  margin: 0 0 1.5rem;
}

/* Medium pill rail */
.medium-rail {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0 0 2rem;
  font-family: var(--font-ui);
}

.medium-pill {
  display: inline-block;
  padding: 0.3rem 0.9rem;
  border-radius: 999px;
  border: 1px solid var(--color-ink-soft);
  color: var(--color-ink-soft);
  font-size: 0.8rem;
  text-decoration: none;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.medium-pill:hover,
.medium-pill:focus-visible {
  background: var(--color-ink);
  color: var(--color-stone);
  border-color: var(--color-ink);
  outline: none;
}

.medium-pill.is-active {
  background: var(--color-ink);
  color: var(--color-stone);
  border-color: var(--color-ink);
}
```

- [ ] **Step 4: Verify dev server**

In dev server, confirm the rail renders with proper pill styling.

- [ ] **Step 5: Run contrast linter**

```
python3 tools/check-contrast.py
```
Expected: passes.

- [ ] **Step 6: Commit**

```
git add assets/css/main.css
git commit -m "feat(library): CSS §44 base layout + medium rail"
```

---

### Task 2.12: CSS §44 — hero block

**Files:**
- Modify: `assets/css/main.css`

- [ ] **Step 1: Append hero block styles to §44**

```css
/* Hero block — single featured item */
.library-hero {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1.5rem;
  align-items: start;
  padding: 1.5rem;
  margin-bottom: 2.5rem;
  background: linear-gradient(120deg, color-mix(in srgb, var(--color-tile) 92%, var(--color-burgundy) 8%) 0%, var(--color-tile) 100%);
  border-radius: 8px;
}

.library-hero-cover-wrap {
  position: relative;
  width: 140px;
  flex-shrink: 0;
}

.library-cover-portrait { aspect-ratio: 140 / 190; }
.library-cover-square   { aspect-ratio: 1 / 1; }

.library-hero-cover {
  width: 100%;
  height: auto;
  border-radius: 4px;
  display: block;
}

.library-hero-body { min-width: 0; }

.library-hero-eyebrow {
  font-family: var(--font-ui);
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-burgundy);
  margin: 0 0 0.4rem;
}

.library-hero-title {
  font-family: var(--font-body);
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0 0 0.4rem;
  line-height: 1.2;
}

.library-hero-meta {
  font-family: var(--font-ui);
  font-size: 0.82rem;
  color: var(--color-ink-soft);
  margin: 0 0 0.8rem;
}

.library-hero-preview {
  font-style: italic;
  color: var(--color-ink);
  margin: 0 0 1rem;
}

.library-hero-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

@media (max-width: 720px) {
  .library-hero {
    grid-template-columns: 1fr;
  }
  .library-hero-cover-wrap {
    width: 120px;
  }
}
```

- [ ] **Step 2: Eyeball in dev server**

Confirm hero block displays correctly at 1220px / 960px / 720px viewports.

- [ ] **Step 3: Run contrast linter**

```
python3 tools/check-contrast.py
```
Expected: passes.

- [ ] **Step 4: Commit**

```
git add assets/css/main.css
git commit -m "feat(library): CSS §44 hero block"
```

---

### Task 2.13: CSS §44 — shelves + tiles

**Files:**
- Modify: `assets/css/main.css`

- [ ] **Step 1: Append shelf + tile styles to §44**

```css
/* Shelf block */
.library-shelf {
  margin-bottom: 2.5rem;
}

.library-shelf-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.6rem;
  gap: 1rem;
}

.library-shelf-head h2 {
  font-size: 1.1rem;
  margin: 0;
}

.library-shelf-intro {
  font-style: italic;
  color: var(--color-ink-soft);
  font-size: 0.85rem;
  flex: 1;
  margin: 0;
}

.library-shelf-see-all {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--color-burgundy);
  text-decoration: none;
  white-space: nowrap;
}

.library-shelf-see-all:hover,
.library-shelf-see-all:focus-visible { text-decoration: underline; }

.library-shelf-strip {
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}

/* Tile */
.library-tile {
  width: 140px;
  flex-shrink: 0;
  background: var(--color-tile);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
}

.library-tile-link {
  display: block;
  color: inherit;
  text-decoration: none;
}

.library-tile-link:focus-visible {
  outline: 2px solid var(--color-burgundy);
  outline-offset: 2px;
}

.library-cover-wrap {
  position: relative;
  width: 100%;
  border-radius: 4px;
  overflow: hidden;
}

.library-cover {
  width: 100%;
  height: auto;
  display: block;
}

.library-badge {
  position: absolute;
  bottom: 6px;
  right: 6px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-ink);
  color: var(--color-stone);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 1.5px color-mix(in srgb, var(--color-stone) 50%, transparent);
}

.library-badge svg {
  width: 12px;
  height: 12px;
}

.library-glyph-block {
  width: 100%;
  aspect-ratio: 140 / 190;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-stone);
}

.library-glyph-block.book      { background: var(--color-burgundy); }
.library-glyph-block.reading   { background: var(--color-burgundy); }
.library-glyph-block.music     { background: var(--color-steel); }
.library-glyph-block.listening { background: var(--color-steel); }
.library-glyph-block.game      { background: var(--color-green); }
.library-glyph-block.playing   { background: var(--color-green); }
.library-glyph-block.watching  { background: var(--color-violet); }

.library-glyph-block svg {
  width: 56px;
  height: 56px;
}

.library-tile-title {
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 0.95rem;
  margin: 0.5rem 0 0.2rem;
  line-height: 1.2;
}

.library-tile-meta {
  font-family: var(--font-ui);
  font-size: 0.72rem;
  color: var(--color-ink-soft);
  margin: 0 0 0.5rem;
}

.library-tile-actions {
  display: flex;
  gap: 0.3rem;
  flex-wrap: wrap;
  padding: 0 0 0.25rem;
}

.library-tile-actions .cite-cta,
.library-tile-actions .ref-cite-note,
.library-tile-actions .ref-cite-source {
  font-size: 0.65rem;
  padding: 2px 7px;
  border-radius: 999px;
  border: 1px solid;
  background: transparent;
  line-height: 1.2;
  text-decoration: none;
  font-family: var(--font-ui);
}

.library-tile-actions .cite-cta {
  color: var(--color-burgundy);
  border-color: var(--color-burgundy);
  cursor: pointer;
}

.library-tile-actions .ref-cite-note   { color: var(--color-green);    border-color: var(--color-green); }
.library-tile-actions .ref-cite-source { color: var(--color-steel);    border-color: var(--color-steel); }
```

- [ ] **Step 2: Eyeball**

Visit http://localhost:1313/library/ at 1220 / 960 / 720 widths. Confirm tile rows scroll horizontally; action pills wrap if needed; no overflow chaos.

- [ ] **Step 3: Contrast linter**

```
python3 tools/check-contrast.py
```
Expected: passes.

- [ ] **Step 4: Commit**

```
git add assets/css/main.css
git commit -m "feat(library): CSS §44 shelves + tiles + action row"
```

---

### Task 2.14: CSS §44 — catalogue block + responsive

**Files:**
- Modify: `assets/css/main.css`

- [ ] **Step 1: Append catalogue + responsive rules to §44**

```css
/* Bottom catalogue block */
.library-catalogue {
  padding: 2rem 1.5rem;
  margin-top: 2rem;
  background: color-mix(in srgb, var(--color-tile) 70%, var(--color-stone) 30%);
  border-radius: 8px;
}

.library-catalogue h2 {
  margin: 0 0 1rem;
  font-size: 1.05rem;
}

.library-cat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.8rem;
}

.library-cat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  padding: 1rem 0.5rem;
  background: var(--color-tile);
  border: 1px solid color-mix(in srgb, var(--color-ink) 12%, transparent);
  border-radius: 6px;
  text-decoration: none;
  color: inherit;
  font-family: var(--font-ui);
  transition: border-color 0.15s, transform 0.15s;
}

.library-cat-card:hover,
.library-cat-card:focus-visible {
  border-color: var(--color-burgundy);
  outline: none;
  transform: translateY(-2px);
}

.library-cat-disc {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-ink);
  color: var(--color-stone);
  display: flex;
  align-items: center;
  justify-content: center;
}

.library-cat-disc svg {
  width: 14px;
  height: 14px;
}

.library-cat-name {
  font-weight: 600;
  font-size: 0.85rem;
}

.library-cat-count {
  font-size: 0.7rem;
  color: var(--color-ink-soft);
}

/* Library shelf detail page (/library/shelves/<slug>/) */
.library-shelf-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 1.5rem 4rem;
}

.library-shelf-page-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 140px);
  gap: 1.2rem;
  justify-content: start;
  margin-top: 1.5rem;
}

/* Responsive */
@media (max-width: 960px) {
  .library-cat-cards { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 720px) {
  .library-cat-cards { grid-template-columns: 1fr; }
  .library-shelf-head { flex-wrap: wrap; }
}
```

- [ ] **Step 2: Eyeball at 360 / 414 / 720 / 960 / 1220 widths**

Confirm: catalogue cards reflow from 4-col → 2-col → 1-col; shelf header wraps cleanly on narrow viewports.

- [ ] **Step 3: Contrast linter**

```
python3 tools/check-contrast.py
```
Expected: passes.

- [ ] **Step 4: Commit**

```
git add assets/css/main.css
git commit -m "feat(library): CSS §44 catalogue + responsive breakpoints"
```

---

### Task 2.15: Create library-shelf-nav.js + wire into entry-library

**Files:**
- Create: `assets/js/library-shelf-nav.js`
- Modify: `assets/js/entry-library.js`

- [ ] **Step 1: Write the nav handler**

```javascript
// assets/js/library-shelf-nav.js
// Keyboard navigation within a shelf strip:
//   Tab lands on the first tile of each strip; ←/→ traverses tiles within
//   the strip; no wraparound; Tab exits to the next strip's first tile.
//
// Implementation: each strip is a .library-shelf-strip; tiles inside have
// `.library-tile-link`. On mount: first tile keeps tabindex=0, rest get
// tabindex=-1. Arrow keys call .focus() on the next sibling tile.

function mountShelf(strip) {
  const tiles = strip.querySelectorAll('.library-tile-link');
  if (tiles.length === 0) return;
  tiles.forEach((tile, i) => {
    tile.tabIndex = i === 0 ? 0 : -1;
  });
  strip.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const focused = document.activeElement;
    if (!focused || !focused.classList.contains('library-tile-link')) return;
    if (!strip.contains(focused)) return;
    e.preventDefault();
    const tilesNow = Array.from(strip.querySelectorAll('.library-tile-link'));
    const idx = tilesNow.indexOf(focused);
    let next;
    if (e.key === 'ArrowRight' && idx < tilesNow.length - 1) next = tilesNow[idx + 1];
    if (e.key === 'ArrowLeft'  && idx > 0)                   next = tilesNow[idx - 1];
    if (next) next.focus();
  });
}

export function initLibraryShelfNav() {
  document.querySelectorAll('.library-shelf-strip').forEach(mountShelf);
}
```

- [ ] **Step 2: Wire into entry-library.js**

Read current `assets/js/entry-library.js`. Add an import + a call:

```javascript
// At the top with other imports
import { initLibraryShelfNav } from './library-shelf-nav.js';

// Inside the DOMContentLoaded handler (or whatever entry point the file uses)
initLibraryShelfNav();
```

- [ ] **Step 3: Update scripts.html to load entry-library on /library/ umbrella too**

Read `layouts/partials/scripts.html`. Find the entry-library scoping block. Current shape (per CLAUDE.md):
```
.Section == "library" AND NOT /library/
```

Change to:
```
.Section == "library"
```

Concretely: locate the `if` condition for entry-library and remove the `AND NOT eq .RelPermalink "/library/"` clause.

- [ ] **Step 4: Verify Hugo build**

```
hugo --quiet --cleanDestinationDir
```
Expected: succeeds. Inspect `public/library/index.html` for `<script src=".../library.<hash>.js">`.

- [ ] **Step 5: Eyeball keyboard nav**

In dev server: visit `/library/`, focus first tile via `Tab`, press `→` repeatedly — focus should advance through the shelf strip. Press `Tab` again — focus should exit to the next shelf's first tile.

- [ ] **Step 6: Commit**

```
git add assets/js/library-shelf-nav.js assets/js/entry-library.js layouts/partials/scripts.html
git commit -m "feat(library): keyboard nav within shelf strips"
```

---

### Task 2.16: Update page-weight classifier + smoke test

**Files:**
- Modify: `tools/check_page_weights.py`
- Modify: `tools/check_smoke.py`

- [ ] **Step 1: Locate the classifier in check_page_weights.py**

Run: `grep -n 'library\|classifier' tools/check_page_weights.py | head`

- [ ] **Step 2: Add `/credits/` to the classifier**

Find the classifier dict (e.g. `URL_BUDGETS = {...}` or similar). Add:

```python
"/credits/": 100_000,
"/library/shelves/": 500_000,  # Same tier as /library/
```

(Keep `/library/` at 500_000.)

- [ ] **Step 3: Add `/credits/` to the smoke URL list**

Find the URL list in `tools/check_smoke.py` (typically `SMOKE_URLS = [...]`). Append:

```python
"/credits/",
```

Also confirm `/library/` and `/library/shelves/long-example/` are testable (smoke may already cover `/library/`).

- [ ] **Step 4: Run both linters**

```
hugo --minify --cleanDestinationDir
python3 tools/check_page_weights.py
python3 tools/check_smoke.py
```
Expected: both pass.

- [ ] **Step 5: Commit**

```
git add tools/check_page_weights.py tools/check_smoke.py
git commit -m "ci(library): add /credits/ + /library/shelves/ to weight + smoke gates"
```

---

### Task 2.17: Wire shelves linter into workflow + ci-local.sh

**Files:**
- Modify: `.github/workflows/hugo.yaml`
- Modify: `tools/ci-local.sh`

- [ ] **Step 1: Add workflow steps**

Insert AFTER the icon-attribution steps (from Task 1.8) and BEFORE `check_pagefind_meta`:

```yaml
      - name: Lint — library shelves
        run: python3 tools/check_library_shelves.py

      - name: Test — library-shelves linter
        run: python3 -m unittest tools/test_check_library_shelves.py -v
```

- [ ] **Step 2: Mirror in ci-local.sh**

After the icon-attribution block, add:

```bash
python3 tools/check_library_shelves.py
python3 -m unittest tools/test_check_library_shelves.py -v 2>&1 | tail -3
```

- [ ] **Step 3: Run full CI locally**

```
tools/ci-local.sh
```
Expected: passes start-to-finish.

- [ ] **Step 4: Verify named-step count is 48**

```
grep -c '^      - name:' .github/workflows/hugo.yaml
```
Expected: `48`.

- [ ] **Step 5: Commit**

```
git add .github/workflows/hugo.yaml tools/ci-local.sh
git commit -m "ci(library): wire shelves linter (48 named steps)"
```

---

### Task 2.18: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CSS section index**

Find the "CSS pipeline" section. Update the §-numbering note to include §44.

Find this line:
> consumed by `layouts/partials/head.html` via `resources.Get` + (production) `minify | fingerprint` with SRI integrity.

Look for any list of sections — update to mention §44.

- [ ] **Step 2: Update the linter count**

Find every reference to "seventeen linter pairs" / "17 linter pairs" / "13th linter pair" etc. Update to "nineteen linter pairs" (19 total: 17 from before + #18 + #19).

Find the workflow step count. Update from "46 named steps" to "48 named steps."

- [ ] **Step 3: Update the JS pipeline table**

Find the table that documents `js/entry-library.js`. Current row (per CLAUDE.md):

```
| `js/entry-library.js` | `library.<hash>.js` (~5 KB) | `.Section == "library"` AND NOT `/library/` | imports `filter-chips.js`; per-leaf pages only (no graph) |
```

Update to:

```
| `js/entry-library.js` | `library.<hash>.js` (~5 KB) | `.Section == "library"` | imports `filter-chips.js` + `library-shelf-nav.js`; per-leaf pages AND umbrella |
```

- [ ] **Step 4: Add a queued-section pointer**

Find the "queued-work" entries section. Remove the "Library redesign stub" entry — the spec is now full. Add nothing replacement; the slice is in progress.

- [ ] **Step 5: Commit**

```
git add CLAUDE.md
git commit -m "claude.md: register library redesign slice (CSS §44, linters 18+19, JS pipeline change)"
```

---

## Phase 3 — Integration verification

### Task 3.1: Full CI locally

- [ ] **Step 1: Clean working state**

```
pkill -f "hugo server" 2>/dev/null
rm -rf public
```

- [ ] **Step 2: Run ci-local.sh**

```
tools/ci-local.sh
```
Expected: passes end-to-end.

- [ ] **Step 3: If anything fails — fix and re-run**

No commit on this task; this is a gate.

---

### Task 3.2: Manual visual verification

- [ ] **Step 1: Start dev server**

```
hugo server --buildDrafts
```

- [ ] **Step 2: Inspect at three viewport widths**

For each width: 1220px, 960px (half-screen), 720px:

- http://localhost:1313/ — homepage still renders correctly
- http://localhost:1313/about/ — monogram disc displays "AM"
- http://localhost:1313/library/ — NEW umbrella: rail + hero + shelves + catalogue
- http://localhost:1313/library/shelves/long-example/ — long-shelf detail page
- http://localhost:1313/library/reading/ — leaf still works
- http://localhost:1313/works/ — works umbrella still renders correctly (icon swap shouldn't break it)
- http://localhost:1313/research/ — research output items still render with new icons
- http://localhost:1313/credits/ — new attribution page

Test keyboard nav on `/library/`: Tab through, use ← → arrow keys within shelves, confirm Tab exits to next shelf.

- [ ] **Step 3: Kill dev server**

```
pkill -f "hugo server"
```

- [ ] **Step 4: No commit — this is a manual gate**

---

### Task 3.3: Final verification + merge plan

- [ ] **Step 1: Confirm all commits land cleanly**

```
git log --oneline feature/library-redesign ^master
```
Expected: ~24 commits (one per task that ended in commit).

- [ ] **Step 2: Inform user**

> "Library redesign slice ready on `feature/library-redesign`. {N} commits.  CI passes locally. Suggested next step: push branch and merge to master, OR open a PR for additional review."

Wait for user direction before pushing or merging.

---

## Self-review

### Spec coverage check

- ✓ §2.1 Layer 1 scope — covered by Phase 2 (tasks 2.1–2.18).
- ✓ §2.1 Layer 2 scope — covered by Phase 1 (tasks 1.1–1.9).
- ✓ §3.1 Content + layouts — Task 2.9 (rewrite list.html), 2.10 (library-shelf), 2.3 (shelves stub).
- ✓ §3.2 Partials — Tasks 2.4–2.8 (one task per partial), 2.9 (delete umbrella-card).
- ✓ §3.3 Data contracts — Task 2.3.
- ✓ §3.4 Detail-page pattern — Tasks 2.3 (stub) + 2.10 (layout).
- ✓ §3.5 Empty-state matrix — implicit in partial code (Tasks 2.7, 2.8, 2.9 handle each branch).
- ✓ §3.6 Soft cap — implicit (hardcoded `$cap := 12` in Task 2.7).
- ✓ §4.1 Page shape — Task 2.9.
- ✓ §4.2 Tile — Task 2.6.
- ✓ §4.3 Medium badge — Tasks 2.6/2.8 (markup) + 2.13 (CSS).
- ✓ §4.4 No-cover fallback — Tasks 2.6/2.8 (markup) + 2.13 (`.library-glyph-block.<medium>` CSS).
- ✓ §4.5 Hero — Task 2.8.
- ✓ §4.6 Scroll-row plain — Task 2.13 (CSS).
- ✓ §4.7 Keyboard nav — Task 2.15.
- ✓ §4.8 CSS §44 — Tasks 2.11–2.14.
- ✓ §4.9 Page weight — Task 2.16.
- ✓ §5.1 Icon canon — Task 1.5.
- ✓ §5.2 Ship parameters — Task 1.5.
- ✓ §5.3 Per-SVG header — Task 1.5.
- ✓ §5.4 `/credits/` page — Task 1.7.
- ✓ §5.5 `THIRD_PARTY.md` — Task 1.2.
- ✓ §5.6 Monogram replacement — Task 1.6.
- ✓ §7.1 Library shelves linter — Tasks 2.1, 2.2.
- ✓ §7.2 Icon attribution linter — Tasks 1.3, 1.4.
- ✓ §8 JS — Task 2.15.
- ✓ §9 Test plan — covered piecemeal (fixtures in 2.3; CI sequence in 1.8 + 2.17; smoke in 2.16).
- ✓ §13 Done criteria — Phase 3 covers every line item.

### Placeholder scan

No `TBD`, `TODO`, `FIXME` in the plan body. Every code block contains actual code; every `- [ ]` step contains the command or test to run.

### Type consistency

- `lint_icon_attribution(project_root)` and `lint_library_shelves(project_root)` — both functions called the same way in their respective test files. ✓
- `initLibraryShelfNav()` — defined in Task 2.15, called in same task. ✓
- Partial dict signatures — `umbrella-shelf` takes `{shelf, media_index}`; `umbrella-tile` takes `{item, medium}`; `umbrella-hero` takes `{hero_slug, media_index}`. Consumers match definitions. ✓
- `cite-cta` button + `ref-cite-note` + `ref-cite-source` — class names match what `cite.js` listens for (from `assets/js/cite.js:140-149`).

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-14-library-redesign.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
