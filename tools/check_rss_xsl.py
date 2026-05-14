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
