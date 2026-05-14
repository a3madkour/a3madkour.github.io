# RSS XSL Pretty-Render Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pretty-render the essays RSS feed (`/essays/index.xml`) as a styled HTML page in browsers via an XSL stylesheet, while keeping the feed valid for RSS readers.

**Architecture:** Add `assets/feed/feed.xsl` (hand-authored XSL with inline CSS), reference it from `layouts/essays/rss.xml` via a `<?xml-stylesheet ?>` processing instruction emitted by Hugo's resource pipeline. Garden + site-wide feeds are untouched. A new linter pair (`tools/check_rss_xsl.py` + sibling test) gates regressions. Two new CI steps in `.github/workflows/hugo.yaml`.

**Tech Stack:** XSL 1.0, inline CSS, Hugo resource pipeline (`resources.Get`), Python 3 stdlib (linter), `unittest` (sibling test), GitHub Actions (CI wiring).

**Spec:** `docs/superpowers/specs/2026-05-13-rss-xsl-pretty-render-design.md`.

---

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `assets/feed/feed.xsl` | **create** | XSL 1.0 stylesheet — transforms RSS 2.0 → styled HTML5 with inline CSS. |
| `layouts/essays/rss.xml` | **modify** (1-line prepend) | Hugo template — adds the `<?xml-stylesheet ?>` PI ahead of `<rss>`. |
| `tools/check_rss_xsl.py` | **create** | CI linter — asserts XSL existence/shape + essays PI + garden-no-PI scope guard. |
| `tools/test_check_rss_xsl.py` | **create** | Sibling unit test — exercises the linter against 5 fixture configurations. |
| `.github/workflows/hugo.yaml` | **modify** | Add 2 named steps: "Verify RSS XSL" + "Run RSS XSL linter unit tests" in the pre-build linter block. |

The garden feed (`layouts/garden/rss.xml`) and home feed (Hugo default `/index.xml`) stay untouched — scope guard enforced by the linter.

---

## Task 1: Scaffold linter pair (failing tests for missing XSL + PI)

**Files:**
- Create: `tools/check_rss_xsl.py`
- Create: `tools/test_check_rss_xsl.py`

The plan is TDD: write the test fixtures first, drive the linter from them. We use the project's established convention (see `tools/check_garden_links.py` + `tools/test_check_garden_links.py`): the linter exposes a `lint_*` function parameterized over paths so the test can pass a `tempfile.TemporaryDirectory()` mirror.

- [ ] **Step 1: Create `tools/check_rss_xsl.py` with a stub `lint_rss_xsl()` returning an empty list.**

```python
#!/usr/bin/env python3
"""RSS XSL pretty-render linter.

Asserts:
  1. `assets/feed/feed.xsl` exists.
  2. It parses as XML (XSL is XML).
  3. Root element is xsl:stylesheet (namespace http://www.w3.org/1999/XSL/Transform).
  4. At least one <xsl:template match="/"> child exists.
  5. The output template contains an HTML <style> element (sentinel against
     accidental removal of the inline-CSS block).
  6. `layouts/essays/rss.xml` contains an `<?xml-stylesheet ... feed/feed.xsl ?>`
     processing instruction that appears BEFORE any literal `<rss` substring.
  7. `layouts/garden/rss.xml` does NOT contain `<?xml-stylesheet` (scope guard).

Exits 0 on success, 1 on any error. Stdlib only. Paired with
tools/test_check_rss_xsl.py.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


XSL_NS = "http://www.w3.org/1999/XSL/Transform"


def lint_rss_xsl(
    xsl_path: Path,
    essays_rss_path: Path,
    garden_rss_path: Path,
) -> list[str]:
    """Return a list of error strings. Empty list = clean."""
    errors: list[str] = []
    return errors


def main() -> int:
    project = Path(__file__).resolve().parent.parent
    errors = lint_rss_xsl(
        xsl_path=project / "assets" / "feed" / "feed.xsl",
        essays_rss_path=project / "layouts" / "essays" / "rss.xml",
        garden_rss_path=project / "layouts" / "garden" / "rss.xml",
    )
    if errors:
        print(f"check_rss_xsl: {len(errors)} issue(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("check_rss_xsl: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Create `tools/test_check_rss_xsl.py` with the 5 fixture tests, all currently failing.**

```python
"""Tests for check_rss_xsl.py — run with:
   python3 -m unittest tools/test_check_rss_xsl.py -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_rss_xsl as lint  # noqa: E402


# Minimal valid XSL: stylesheet root, template match="/", emits <style>.
VALID_XSL = """\
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="utf-8"/>
  <xsl:template match="/">
    <html lang="en">
      <head>
        <title><xsl:value-of select="/rss/channel/title"/></title>
        <style>body { font-family: serif; }</style>
      </head>
      <body><xsl:value-of select="/rss/channel/title"/></body>
    </html>
  </xsl:template>
</xsl:stylesheet>
"""

# Essays RSS template WITH the PI on the line before <rss>.
ESSAYS_RSS_WITH_PI = """\
{{- $pages := where site.RegularPages "Section" "essays" -}}
{{- printf "<?xml-stylesheet type=\\"text/xsl\\" href=\\"%s\\"?>" ((resources.Get "feed/feed.xsl").RelPermalink) | safeHTML }}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel><title>x</title></channel>
</rss>
"""

# Essays RSS template WITHOUT the PI.
ESSAYS_RSS_NO_PI = """\
{{- $pages := where site.RegularPages "Section" "essays" -}}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel><title>x</title></channel>
</rss>
"""

# Essays RSS template with PI AFTER <rss> (invalid placement).
ESSAYS_RSS_PI_AFTER_RSS = """\
{{- $pages := where site.RegularPages "Section" "essays" -}}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <?xml-stylesheet type="text/xsl" href="/feed/feed.xsl"?>
  <channel><title>x</title></channel>
</rss>
"""

# Garden RSS template — clean, no PI.
GARDEN_RSS_NO_PI = """\
<rss version="2.0">
  <channel><title>garden</title></channel>
</rss>
"""

# Garden RSS template — accidentally has the PI (scope guard violation).
GARDEN_RSS_WITH_PI = """\
{{- printf "<?xml-stylesheet type=\\"text/xsl\\" href=\\"%s\\"?>" ((resources.Get "feed/feed.xsl").RelPermalink) | safeHTML }}
<rss version="2.0">
  <channel><title>garden</title></channel>
</rss>
"""


def _write_fixture(tmpdir: Path, xsl: str | None, essays_rss: str, garden_rss: str) -> tuple[Path, Path, Path]:
    """Lay out a minimal tree under tmpdir mirroring the project layout."""
    xsl_path = tmpdir / "assets" / "feed" / "feed.xsl"
    essays_path = tmpdir / "layouts" / "essays" / "rss.xml"
    garden_path = tmpdir / "layouts" / "garden" / "rss.xml"
    if xsl is not None:
        xsl_path.parent.mkdir(parents=True, exist_ok=True)
        xsl_path.write_text(xsl)
    essays_path.parent.mkdir(parents=True, exist_ok=True)
    essays_path.write_text(essays_rss)
    garden_path.parent.mkdir(parents=True, exist_ok=True)
    garden_path.write_text(garden_rss)
    return xsl_path, essays_path, garden_path


class TestRssXslLinter(unittest.TestCase):
    def test_happy_path(self):
        # Fixture 1: well-formed XSL + essays PI present + garden PI absent.
        with tempfile.TemporaryDirectory() as td:
            xsl, essays, garden = _write_fixture(
                Path(td), VALID_XSL, ESSAYS_RSS_WITH_PI, GARDEN_RSS_NO_PI
            )
            errors = lint.lint_rss_xsl(xsl, essays, garden)
            self.assertEqual(errors, [], f"expected clean, got: {errors}")

    def test_missing_xsl(self):
        # Fixture 2: XSL file does not exist.
        with tempfile.TemporaryDirectory() as td:
            xsl, essays, garden = _write_fixture(
                Path(td), None, ESSAYS_RSS_WITH_PI, GARDEN_RSS_NO_PI
            )
            errors = lint.lint_rss_xsl(xsl, essays, garden)
            self.assertTrue(
                any("feed.xsl" in e and "missing" in e.lower() for e in errors),
                f"expected 'missing feed.xsl' error, got: {errors}",
            )

    def test_missing_essays_pi(self):
        # Fixture 3: XSL present but essays template has no PI.
        with tempfile.TemporaryDirectory() as td:
            xsl, essays, garden = _write_fixture(
                Path(td), VALID_XSL, ESSAYS_RSS_NO_PI, GARDEN_RSS_NO_PI
            )
            errors = lint.lint_rss_xsl(xsl, essays, garden)
            self.assertTrue(
                any("essays/rss.xml" in e and "xml-stylesheet" in e for e in errors),
                f"expected 'essays/rss.xml missing xml-stylesheet' error, got: {errors}",
            )

    def test_essays_pi_after_rss(self):
        # Fixture 4: PI appears after <rss> (invalid placement).
        with tempfile.TemporaryDirectory() as td:
            xsl, essays, garden = _write_fixture(
                Path(td), VALID_XSL, ESSAYS_RSS_PI_AFTER_RSS, GARDEN_RSS_NO_PI
            )
            errors = lint.lint_rss_xsl(xsl, essays, garden)
            self.assertTrue(
                any("essays/rss.xml" in e and "before" in e.lower() for e in errors),
                f"expected 'PI must precede <rss>' error, got: {errors}",
            )

    def test_garden_has_pi(self):
        # Fixture 5: scope guard — garden template has the PI.
        with tempfile.TemporaryDirectory() as td:
            xsl, essays, garden = _write_fixture(
                Path(td), VALID_XSL, ESSAYS_RSS_WITH_PI, GARDEN_RSS_WITH_PI
            )
            errors = lint.lint_rss_xsl(xsl, essays, garden)
            self.assertTrue(
                any("garden/rss.xml" in e and "xml-stylesheet" in e for e in errors),
                f"expected 'garden scope guard' error, got: {errors}",
            )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test suite to confirm all 5 tests fail (RED).**

```bash
python3 -m unittest tools/test_check_rss_xsl.py -v
```

Expected: `Ran 5 tests` — `test_happy_path` passes (lint returns [] which matches empty-errors expectation), the 4 negative-case tests FAIL because the stub returns []. We want the negative tests to fail right now — that's the TDD red signal.

- [ ] **Step 4: Commit the scaffolding.**

```bash
git add tools/check_rss_xsl.py tools/test_check_rss_xsl.py
git commit -m "test(rss-xsl): scaffold linter pair (RED)"
```

---

## Task 2: Implement linter — all 7 assertions

**Files:**
- Modify: `tools/check_rss_xsl.py` (replace the stub `lint_rss_xsl`)

- [ ] **Step 1: Replace the stub with the full implementation.**

```python
def lint_rss_xsl(
    xsl_path: Path,
    essays_rss_path: Path,
    garden_rss_path: Path,
) -> list[str]:
    """Return a list of error strings. Empty list = clean."""
    errors: list[str] = []

    # --- XSL file checks --------------------------------------------------
    if not xsl_path.is_file():
        errors.append(f"{xsl_path}: missing feed.xsl file")
        # Nothing more to check on the XSL side; continue to PI checks.
    else:
        try:
            tree = ET.parse(xsl_path)
        except ET.ParseError as exc:
            errors.append(f"{xsl_path}: XSL is not well-formed XML ({exc})")
            tree = None

        if tree is not None:
            root = tree.getroot()
            expected_root = f"{{{XSL_NS}}}stylesheet"
            if root.tag != expected_root:
                errors.append(
                    f"{xsl_path}: root element is {root.tag!r}, "
                    f"expected '{{xsl}}stylesheet'"
                )
            # At least one <xsl:template match="/">.
            template_match = f"{{{XSL_NS}}}template"
            roots = [t for t in root.findall(template_match) if t.get("match") == "/"]
            if not roots:
                errors.append(
                    f"{xsl_path}: missing <xsl:template match=\"/\"> "
                    "(stylesheet must transform the document root)"
                )
            # Sentinel: <style> element somewhere in the output. We don't care
            # about namespace — the output is HTML, and ElementTree treats
            # unprefixed elements inside XSL as namespace-less.
            has_style = any(
                el.tag == "style" or el.tag.endswith("}style")
                for el in root.iter()
            )
            if not has_style:
                errors.append(
                    f"{xsl_path}: no <style> element in output template "
                    "(inline-CSS sentinel missing — was it removed?)"
                )

    # --- Essays PI placement ---------------------------------------------
    if not essays_rss_path.is_file():
        errors.append(f"{essays_rss_path}: file missing")
    else:
        essays_text = essays_rss_path.read_text(encoding="utf-8")
        # Find PI substring and first <rss occurrence.
        pi_match = re.search(r"xml-stylesheet[^?]*feed/feed\.xsl", essays_text)
        rss_open = essays_text.find("<rss")
        if pi_match is None:
            errors.append(
                f"{essays_rss_path}: missing xml-stylesheet PI referencing "
                "feed/feed.xsl (browsers won't pretty-render the feed)"
            )
        elif rss_open == -1:
            # No <rss in the file — template malformed, but not our scope.
            pass
        elif pi_match.start() > rss_open:
            errors.append(
                f"{essays_rss_path}: xml-stylesheet PI must appear BEFORE the "
                "<rss> opening tag (browsers ignore PIs inside the root element)"
            )

    # --- Garden scope guard ----------------------------------------------
    if garden_rss_path.is_file():
        garden_text = garden_rss_path.read_text(encoding="utf-8")
        if "xml-stylesheet" in garden_text:
            errors.append(
                f"{garden_rss_path}: contains xml-stylesheet PI — garden feed "
                "is out of scope for the pretty-render slice (remove the PI)"
            )

    return errors
```

- [ ] **Step 2: Run the test suite — all 5 tests should pass (GREEN).**

```bash
python3 -m unittest tools/test_check_rss_xsl.py -v
```

Expected: `Ran 5 tests in ... OK`. If any test still fails, fix the linter (NOT the tests) until all pass.

- [ ] **Step 3: Run the linter against the real project — it should FAIL (no XSL exists yet, no PI in essays/rss.xml yet).**

```bash
python3 tools/check_rss_xsl.py
```

Expected: stderr lists 2 errors — `missing feed.xsl file` and `missing xml-stylesheet PI`. Exit code 1. This is correct — the project is currently in the pre-implementation state.

- [ ] **Step 4: Commit the linter implementation.**

```bash
git add tools/check_rss_xsl.py
git commit -m "feat(rss-xsl): implement linter (GREEN against fixtures, RED against project)"
```

---

## Task 3: Author the XSL stylesheet

**Files:**
- Create: `assets/feed/feed.xsl`

- [ ] **Step 1: Create the directory and write the XSL.**

```bash
mkdir -p assets/feed
```

Write `assets/feed/feed.xsl`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:atom="http://www.w3.org/2005/Atom">
  <xsl:output method="html" encoding="utf-8" indent="yes"
              doctype-system="about:legacy-compat"/>

  <xsl:template match="/">
    <html lang="en">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title><xsl:value-of select="/rss/channel/title"/></title>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Petrona:ital,wght@0,400;0,600;0,700;1,400&amp;display=swap"/>
        <style>
          :root {
            --color-stone:    #eeeeea;
            --color-ink:      #1c1a17;
            --color-ink-soft: #5a564f;
            --color-burgundy: #6b1f2c;
          }
          @media (prefers-color-scheme: dark) {
            :root {
              --color-stone:    #181818;
              --color-ink:      #e2e2dd;
              --color-ink-soft: #b0aca0;
              --color-burgundy: #d65a6a;
            }
          }
          *, *::before, *::after { box-sizing: border-box; }
          html, body { margin: 0; padding: 0; }
          body {
            background: var(--color-stone);
            color: var(--color-ink);
            font-family: "Petrona", Georgia, serif;
            font-size: 1.0625rem;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
          }
          .feed {
            width: min(680px, 92vw);
            margin: 0 auto;
            padding: 4rem 0;
          }
          .feed-header { margin-bottom: 3rem; }
          .feed-header h1 {
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0 0 0.5rem;
            line-height: 1.2;
          }
          .feed-hint {
            color: var(--color-ink-soft);
            font-size: 0.9375rem;
            font-style: italic;
            margin: 0;
          }
          .feed-items {
            list-style: none;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            gap: 2rem;
          }
          .feed-item article > * { margin: 0; }
          .feed-item h2 {
            font-size: 1.25rem;
            font-weight: 600;
            line-height: 1.3;
            margin-bottom: 0.25rem;
          }
          .feed-item h2 a {
            color: var(--color-ink);
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: color 0.15s, border-color 0.15s;
          }
          .feed-item h2 a:hover,
          .feed-item h2 a:focus-visible {
            color: var(--color-burgundy);
            border-bottom-color: var(--color-burgundy);
          }
          .feed-item time {
            display: block;
            color: var(--color-ink-soft);
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
          }
          .feed-item p {
            color: var(--color-ink);
          }
          @media (max-width: 600px) {
            .feed { padding: 2rem 0; }
            .feed-header h1 { font-size: 1.5rem; }
          }
        </style>
      </head>
      <body>
        <main class="feed">
          <header class="feed-header">
            <h1><xsl:value-of select="/rss/channel/title"/></h1>
            <p class="feed-hint">Subscribe in any RSS reader — copy this page's URL.</p>
          </header>
          <ul class="feed-items">
            <xsl:for-each select="/rss/channel/item">
              <li class="feed-item">
                <article>
                  <h2>
                    <a>
                      <xsl:attribute name="href"><xsl:value-of select="link"/></xsl:attribute>
                      <xsl:value-of select="title"/>
                    </a>
                  </h2>
                  <time>
                    <xsl:attribute name="datetime"><xsl:call-template name="pubdate-iso"><xsl:with-param name="rfc822" select="pubDate"/></xsl:call-template></xsl:attribute>
                    <xsl:call-template name="pubdate-display"><xsl:with-param name="rfc822" select="pubDate"/></xsl:call-template>
                  </time>
                  <p><xsl:value-of select="description" disable-output-escaping="yes"/></p>
                </article>
              </li>
            </xsl:for-each>
          </ul>
        </main>
      </body>
    </html>
  </xsl:template>

  <!-- Helper: extract ISO-8601 date from RFC-822 string.
       Input format (fixed by layouts/essays/rss.xml): "Mon, 02 Jan 2006 15:04:05 -0700"
       Positional slicing is safe because the Hugo template emits this exact form.
       Output: "2026-01-02"
  -->
  <xsl:template name="pubdate-iso">
    <xsl:param name="rfc822"/>
    <xsl:variable name="day"   select="substring($rfc822, 6, 2)"/>
    <xsl:variable name="mon3"  select="substring($rfc822, 9, 3)"/>
    <xsl:variable name="year"  select="substring($rfc822, 13, 4)"/>
    <xsl:variable name="month">
      <xsl:choose>
        <xsl:when test="$mon3 = 'Jan'">01</xsl:when>
        <xsl:when test="$mon3 = 'Feb'">02</xsl:when>
        <xsl:when test="$mon3 = 'Mar'">03</xsl:when>
        <xsl:when test="$mon3 = 'Apr'">04</xsl:when>
        <xsl:when test="$mon3 = 'May'">05</xsl:when>
        <xsl:when test="$mon3 = 'Jun'">06</xsl:when>
        <xsl:when test="$mon3 = 'Jul'">07</xsl:when>
        <xsl:when test="$mon3 = 'Aug'">08</xsl:when>
        <xsl:when test="$mon3 = 'Sep'">09</xsl:when>
        <xsl:when test="$mon3 = 'Oct'">10</xsl:when>
        <xsl:when test="$mon3 = 'Nov'">11</xsl:when>
        <xsl:when test="$mon3 = 'Dec'">12</xsl:when>
        <xsl:otherwise>01</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:value-of select="concat($year, '-', $month, '-', $day)"/>
  </xsl:template>

  <!-- Helper: human-readable date. Reuses the ISO slicing then formats. -->
  <xsl:template name="pubdate-display">
    <xsl:param name="rfc822"/>
    <xsl:variable name="day"   select="substring($rfc822, 6, 2)"/>
    <xsl:variable name="mon3"  select="substring($rfc822, 9, 3)"/>
    <xsl:variable name="year"  select="substring($rfc822, 13, 4)"/>
    <xsl:value-of select="concat($day, ' ', $mon3, ' ', $year)"/>
  </xsl:template>

</xsl:stylesheet>
```

- [ ] **Step 2: Verify the XSL parses as XML.**

```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('assets/feed/feed.xsl'); print('OK')"
```

Expected: `OK`. If you get a `ParseError`, fix the XSL until it parses.

- [ ] **Step 3: Run the linter — should still RED (no PI in essays/rss.xml yet, but XSL is fine).**

```bash
python3 tools/check_rss_xsl.py
```

Expected: one remaining error — `missing xml-stylesheet PI`. Exit 1.

- [ ] **Step 4: Commit the XSL.**

```bash
git add assets/feed/feed.xsl
git commit -m "feat(rss-xsl): add feed.xsl stylesheet with inline CSS"
```

---

## Task 4: Wire the PI into `layouts/essays/rss.xml`

**Files:**
- Modify: `layouts/essays/rss.xml`

- [ ] **Step 1: Read the current file to confirm its shape.**

```bash
cat layouts/essays/rss.xml
```

Expected contents (1-line `$pages` lookup → channel + items):

```
{{- $pages := where site.RegularPages "Section" "essays" -}}
{{- $title := printf "%s — Essays" site.Title -}}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  ...
</rss>
```

- [ ] **Step 2: Insert the PI line immediately before `<rss version="2.0" ...>`. Use the Edit tool / your editor to add this single line.**

The line to add:

```
{{- printf "<?xml-stylesheet type=\"text/xsl\" href=\"%s\"?>" ((resources.Get "feed/feed.xsl").RelPermalink) | safeHTML }}
```

Final shape of the top of the file:

```
{{- $pages := where site.RegularPages "Section" "essays" -}}
{{- $title := printf "%s — Essays" site.Title -}}
{{- printf "<?xml-stylesheet type=\"text/xsl\" href=\"%s\"?>" ((resources.Get "feed/feed.xsl").RelPermalink) | safeHTML }}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  ...
```

- [ ] **Step 3: Run the linter — should now pass (GREEN).**

```bash
python3 tools/check_rss_xsl.py
```

Expected: `check_rss_xsl: OK`. Exit 0.

- [ ] **Step 4: Run the linter unit tests again to confirm the fixture-driven tests still pass.**

```bash
python3 -m unittest tools/test_check_rss_xsl.py -v
```

Expected: `Ran 5 tests in ... OK`.

- [ ] **Step 5: Commit the rss.xml change.**

```bash
git add layouts/essays/rss.xml
git commit -m "feat(rss-xsl): wire <?xml-stylesheet ?> PI into essays feed"
```

---

## Task 5: Local Hugo build + browser verification

**Files:** (none changed — verification only)

- [ ] **Step 1: Kill any running dev server, then build production with Hugo.** (The CLAUDE.md warns: do NOT run `hugo --minify` with `hugo server` alive — it poisons dev-server CSS via a MIME mismatch.)

```bash
pkill -f 'hugo server' || true
hugo --minify
```

Expected: clean build, `public/` populated. No errors about `feed/feed.xsl`.

- [ ] **Step 2: Verify the XSL file lands in `public/feed/`.**

```bash
ls -la public/feed/
```

Expected: `feed.xsl` present.

- [ ] **Step 3: Verify the essays feed XML starts with the PI on line 1.**

```bash
head -2 public/essays/index.xml
```

Expected first line: `<?xml-stylesheet type="text/xsl" href="/feed/feed.xsl"?>` (the `href` value may differ slightly if `baseURL` is non-default — what matters is the PI is present, references `feed/feed.xsl`, and precedes `<rss`).

- [ ] **Step 4: Verify the garden feed does NOT contain the PI (scope guard).**

```bash
grep -c "xml-stylesheet" public/garden/index.xml || true
```

Expected: `0` (and exit non-zero from grep, which is fine).

- [ ] **Step 5: Start the dev server and open the rendered feed in a browser.**

```bash
hugo server --buildDrafts &
```

In Firefox AND Chromium, navigate to `http://localhost:1313/essays/index.xml`. Expected: a styled HTML page with the feed title, the "Subscribe in any RSS reader…" hint, and a vertical list of items (title link + date + summary). NOT the browser's default tree-view XML.

- [ ] **Step 6: Toggle the OS dark-mode setting (or use Firefox/Chromium devtools "Emulate CSS prefers-color-scheme") and reload the feed page.**

Expected: background flips dark, text flips light, the burgundy link color shifts to the lighter dark-mode variant. Contrast remains readable.

- [ ] **Step 7: Confirm the garden feed is still raw XML.**

Navigate to `http://localhost:1313/garden/index.xml`. Expected: the browser's default raw-XML tree-view. No styling applied.

- [ ] **Step 8: Confirm the feed remains valid RSS by passing it through an RSS validator.**

```bash
curl -s http://localhost:1313/essays/index.xml | head -5
```

Expected: line 1 PI, line 2 `<rss>`, then `<channel>`. Optionally paste into https://validator.w3.org/feed/ to double-check; expected: valid RSS 2.0 with at most a "stylesheet PI may not be recognized by all readers" advisory (not an error).

- [ ] **Step 9: Kill the dev server.**

```bash
pkill -f 'hugo server'
```

- [ ] **Step 10: If any visual issue surfaced (mis-aligned spacing, typo, color too dim), fix `assets/feed/feed.xsl` inline, rerun Step 5–8, and commit any follow-up tweaks as a separate commit.**

```bash
# Only if there were tweaks:
git add assets/feed/feed.xsl
git commit -m "fix(rss-xsl): adjust <style> per manual verification"
```

---

## Task 6: Wire CI

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Insert the 2 new steps after the existing `library_covers` linter pair (last pre-build linter) and before `Build with Hugo`.**

In `.github/workflows/hugo.yaml`, locate this block (around line 96-99):

```yaml
      - name: Verify library cover schema + cache + audit
        run: python3 tools/check_library_covers.py
      - name: Run library cover linter unit tests
        run: python3 -m unittest tools/test_check_library_covers.py -v
      - name: Build with Hugo
```

Insert two new steps directly above `Build with Hugo`:

```yaml
      - name: Verify RSS XSL
        run: python3 tools/check_rss_xsl.py
      - name: Run RSS XSL linter unit tests
        run: python3 -m unittest tools/test_check_rss_xsl.py -v
      - name: Build with Hugo
```

- [ ] **Step 2: Validate the YAML is still well-formed.**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/hugo.yaml')); print('YAML OK')"
```

Expected: `YAML OK`. If you get an error, fix the indentation (workflow YAML uses 6-space indent inside `steps:`).

- [ ] **Step 3: Confirm step count went from 40 to 42.**

```bash
grep -c "^      - name:" .github/workflows/hugo.yaml
```

Expected: `42`.

- [ ] **Step 4: Commit the CI wiring.**

```bash
git add .github/workflows/hugo.yaml
git commit -m "ci(rss-xsl): add linter pair to workflow (40 → 42 steps)"
```

---

## Task 7: CLAUDE.md update

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the "Shipped" section to mention the RSS XSL slice, and remove RSS pretty-render from the "Deferred features" table.**

In `CLAUDE.md`, locate the bulleted list under "Shipped — Phases 0–6 plus targeted polish" (specifically the "**Final QA — partial pass** (Phase 8 Slice 3)" entry where RSS deferral is mentioned), and the **Deferred features** table at the bottom. Make two changes:

1. Add a new bullet at the end of the "Shipped" list (in chronological order — last entry is the a11y close-out) describing the RSS XSL slice. Use the same prose style as the surrounding entries.

   Suggested text (adapt as needed once you know the merge commit hash):

   > **RSS XSL pretty-render** (post-Phase-8 polish, 2026-05-13): essays feed (`/essays/index.xml`) now opens in browsers as a styled HTML page via `assets/feed/feed.xsl` referenced by an `<?xml-stylesheet ?>` PI on `layouts/essays/rss.xml`. Inline `<style>` clones the four `:root` tokens from `main.css` (stone / ink / ink-soft / burgundy) and respects `prefers-color-scheme`. Garden + site-wide feeds stay raw (scope guard enforced by linter). 15th/16th linter pair (`tools/check_rss_xsl.py` + sibling) brings the workflow to 42 named steps.

2. In the "Final QA — partial pass (Phase 8 Slice 3)" entry, update the line about "RSS link UX" — strike-through or remove the "deferred" framing and link to the shipped slice. Suggested edit: drop the parenthetical `(no spec opened yet)` since the spec was opened and the work shipped.

3. In the section "Phase 8 follow-up: interactive QA walkthrough" near the bottom of "Not started, in phase order", update the line "RSS link UX (XSL pretty-render)" — remove it from the "still waiting" list.

- [ ] **Step 2: Commit the CLAUDE.md update.**

```bash
git add CLAUDE.md
git commit -m "claude.md: log RSS XSL pretty-render shipped"
```

---

## Task 8: Final verification + push

**Files:** (none changed — verification + push only)

- [ ] **Step 1: Run all linter pairs locally to confirm nothing else regressed.** (This catches issues like accidentally indenting another step inconsistently.)

```bash
python3 tools/check-contrast.py
python3 tools/check_fixtures.py && python3 -m unittest tools/test_check_fixtures.py -v
python3 tools/check_garden_fixtures.py && python3 -m unittest tools/test_check_garden_fixtures.py -v
python3 tools/check_garden_links.py && python3 -m unittest tools/test_check_garden_links.py -v
python3 tools/check_filter_chips_config.py && python3 -m unittest tools/test_check_filter_chips_config.py -v
python3 tools/check_research_fixtures.py && python3 -m unittest tools/test_check_research_fixtures.py -v
python3 tools/check_research_links.py && python3 -m unittest tools/test_check_research_links.py -v
python3 tools/check_citations.py && python3 -m unittest tools/test_check_citations.py -v
python3 tools/check_works_fixtures.py && python3 -m unittest tools/test_check_works_fixtures.py -v
python3 tools/check_works_links.py && python3 -m unittest tools/test_check_works_links.py -v
python3 tools/check_library_fixtures.py && python3 -m unittest tools/test_check_library_fixtures.py -v
python3 tools/check_library_links.py && python3 -m unittest tools/test_check_library_links.py -v
python3 tools/check_library_covers.py && python3 -m unittest tools/test_check_library_covers.py -v
python3 tools/check_rss_xsl.py && python3 -m unittest tools/test_check_rss_xsl.py -v
python3 tools/check_smoke.py
```

Expected: all pass. If anything else fails, it's an unrelated regression — investigate before pushing.

- [ ] **Step 2: Confirm clean working tree.**

```bash
git status
```

Expected: `nothing to commit, working tree clean`.

- [ ] **Step 3: Review the commits this slice produced.**

```bash
git log --oneline -10
```

Expected commit list (in order, oldest last):
- `claude.md: log RSS XSL pretty-render shipped`
- `ci(rss-xsl): add linter pair to workflow (40 → 42 steps)`
- `feat(rss-xsl): wire <?xml-stylesheet ?> PI into essays feed`
- `feat(rss-xsl): add feed.xsl stylesheet with inline CSS`
- `feat(rss-xsl): implement linter (GREEN against fixtures, RED against project)`
- `test(rss-xsl): scaffold linter pair (RED)`
- `spec(rss-xsl): fix placeholder token values to match main.css`
- `spec: RSS XSL pretty-render (Phase 8 deferral)`

Plus any additional `fix(rss-xsl):` commits from Task 5 Step 10.

- [ ] **Step 4: Offer the user dev-server spot-check + push.** Per the user's standing preference ("Always offer dev-server spot-check before merging"), confirm with them which screens to eyeball before pushing.

Suggested spot-check checklist for the user:
- `/essays/index.xml` in Firefox + Chromium, light mode → styled list visible.
- Same URLs in dark mode (OS-toggle or devtools `prefers-color-scheme: dark`).
- Click an item title link → essay page loads.
- `/garden/index.xml` in any browser → raw XML (unchanged).
- Subscribe the essays feed in any RSS reader (Feedly / NewsBlur / NetNewsWire / a desktop CLI like `rss2email`) → items parse correctly.

- [ ] **Step 5: Once the user confirms, push to origin/master.**

```bash
git push origin master
```

Expected: CI runs green; deploy step publishes the new XSL to GitHub Pages.

- [ ] **Step 6: Verify the live site after deploy.**

Visit `https://a3madkour.github.io/essays/index.xml` in a browser — expected: styled HTML page. CI workflow time should be within +5s of the prior baseline.

---

## Self-Review

Verifying spec coverage:

- §2 goal 1 (essays feed renders styled in browser) → Task 3 (XSL) + Task 4 (PI wiring) + Task 5 Step 5-6 (verification).
- §2 goal 2 (feed continues to parse for RSS readers) → Task 5 Step 8 (validator) + Task 8 Step 4 (real RSS reader subscribe).
- §2 goal 3 (self-contained, no JS) → Task 3 (no `<script>` in XSL).
- §2 goal 4 (linter pair gates regressions) → Tasks 1+2 + Task 6 (CI wiring).
- §3 non-goals: garden + home feed scope guard → Task 2 linter check + Task 5 Step 4 + Task 5 Step 7.
- §4 files list → covered task-by-task above.
- §5.1 document structure → Task 3 inline XSL matches the shape in §5.1.
- §5.2 date handling → Task 3 `pubdate-iso` + `pubdate-display` templates.
- §5.3 inline CSS tokens → Task 3 `<style>` block.
- §5.4 layout → Task 3 CSS.
- §6 Hugo wiring → Task 4.
- §7 linter — 7 assertions + 5 fixture cases → Task 2 implementation + Task 1 tests.
- §8 a11y → Task 3 (semantic HTML) + Task 5 Step 6 (manual dark-mode contrast).
- §9 risks → Task 5 Step 5-8 (manual verification covers browser support, font fallback, validator).
- §10 out-of-scope → enforced by §2 guard + Task 5 Step 4/7.
- §11 effort estimate → matches the 6 implementation tasks + 1 CLAUDE.md task + 1 push task above.

No `TBD`, `TODO`, `…handle edge cases…`, or "see Task N" placeholders found.

Type/name consistency check:
- `lint_rss_xsl(xsl_path, essays_rss_path, garden_rss_path)` signature — used identically in Tasks 1, 2, 8.
- XSL element names (`feed-header`, `feed-items`, `feed-item`, `feed-hint`, `pubdate-iso`, `pubdate-display`) — consistent across Tasks 3 and 5.
- Linter step names in CI ("Verify RSS XSL" / "Run RSS XSL linter unit tests") — match the project's existing "Verify X" / "Run X linter unit tests" pattern.

Plan looks complete.

---

*End of plan. Execute via `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans`.*
