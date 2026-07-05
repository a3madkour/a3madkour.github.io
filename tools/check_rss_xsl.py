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
        # Find PI substring and first <rss occurrence. Match `xml-stylesheet`
        # and `feed/feed.xsl` on the same line; the Hugo template directive
        # between them (resources.Get, RelPermalink, etc.) is `[^\n]*` slop.
        pi_match = re.search(r"xml-stylesheet[^\n]*feed/feed\.xsl", essays_text)
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


def run(repo_root: Path) -> tuple[int, list[str]]:
    errors = lint_rss_xsl(
        xsl_path=repo_root / "assets" / "feed" / "feed.xsl",
        essays_rss_path=repo_root / "layouts" / "essays" / "rss.xml",
        garden_rss_path=repo_root / "layouts" / "garden" / "rss.xml",
    )
    return (1 if errors else 0, errors)


def main() -> int:
    rc, errors = run(Path(__file__).resolve().parent.parent)
    if errors:
        print(f"check_rss_xsl: {len(errors)} issue(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
    if rc == 0:
        print("check_rss_xsl: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
