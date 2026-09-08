#!/usr/bin/env python3
"""Search section-vocabulary linter (RF1.1 guard). Stdlib only.

`assets/js/search.js` groups Pagefind hits by their `section` meta value and
renders only the sections listed in `SECTION_ORDER`. A section the built site
emits but the array omits is *silently dropped* from the results pane — the
defect this linter exists to prevent, and one that shipped twice: once for
`recipes` (RC2.1) and once for `tags` / `series` / `credits` / `blog` (RF1.1),
50+ pages in the latter case.

Nothing else can catch it. The chip strip in `search-modal.html` is a subset of
the vocabulary (taxonomy pages have no chip), Pagefind indexes whatever the
templates emit, and the pane looks correct because the missing hits simply are
not there to notice.

So: every `section:<value>` the *built* site emits must appear in both
SECTION_ORDER and SECTION_LABEL. Runs post-build, like check_html_links.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Minified output drops attribute quotes, so match both forms.
EMITTED_RE = re.compile(r'data-pagefind-(?:meta|filter)="?section:([a-z][a-z0-9-]*)"?')
ORDER_RE = re.compile(r"const SECTION_ORDER\s*=\s*\[(.*?)\]", re.DOTALL)
LABEL_RE = re.compile(r"const SECTION_LABEL\s*=\s*\{(.*?)\n\};", re.DOTALL)
QUOTED_RE = re.compile(r"'([a-z][a-z0-9-]*)'")
KEY_RE = re.compile(r"^\s*([a-z][a-z0-9-]*)\s*:", re.MULTILINE)

# `other` is search.js's fallback bucket for a hit with no section meta. It is
# never emitted into HTML, so it is expected in the arrays but not in the build.
RUNTIME_ONLY = {"other"}


def parse_search_js(text: str) -> tuple[set[str], set[str], list[str]]:
    errs: list[str] = []
    order_m = ORDER_RE.search(text)
    label_m = LABEL_RE.search(text)
    if not order_m:
        errs.append("assets/js/search.js: could not find SECTION_ORDER")
    if not label_m:
        errs.append("assets/js/search.js: could not find SECTION_LABEL")
    order = set(QUOTED_RE.findall(order_m.group(1))) if order_m else set()
    labels = set(KEY_RE.findall(label_m.group(1))) if label_m else set()
    return order, labels, errs


def run(repo_root: Path, public: Path | None = None) -> tuple[int, list[str]]:
    errs: list[str] = []
    js = repo_root / "assets" / "js" / "search.js"
    if not js.exists():
        return 1, [f"{js}: not found"]
    order, labels, errs = parse_search_js(js.read_text(encoding="utf-8"))
    if errs:
        return 1, errs

    pub = public or (repo_root / "public")
    if not pub.exists():
        print("check_search_sections: public/ not found. Run `hugo --minify` first.")
        return 0, []

    emitted: set[str] = set()
    for html in pub.rglob("*.html"):
        emitted.update(EMITTED_RE.findall(html.read_text(encoding="utf-8", errors="replace")))

    for value in sorted(emitted - order):
        errs.append(
            f"section '{value}' is emitted by the built site but missing from "
            f"SECTION_ORDER in assets/js/search.js — its hits are counted and "
            f"then silently dropped from the results pane"
        )
    for value in sorted(emitted - labels):
        errs.append(
            f"section '{value}' is emitted by the built site but missing from "
            f"SECTION_LABEL — its group would render as <h3>undefined</h3>"
        )
    for value in sorted(order - emitted - RUNTIME_ONLY):
        errs.append(
            f"section '{value}' is listed in SECTION_ORDER but no built page "
            f"emits it — stale entry, or a template stopped emitting its meta"
        )
    for value in sorted(order - labels):
        errs.append(f"section '{value}' is in SECTION_ORDER but has no SECTION_LABEL entry")

    return (1 if errs else 0), errs


def main() -> int:
    rc, errs = run(Path(__file__).resolve().parent.parent)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_search_sections: OK (search.js renders every emitted section)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
