"""Validate that every rendered HTML page in public/ carries the Pagefind
metadata the search modal depends on.

Checks per page:
  1. <main data-pagefind-body> is present.
  2. Some element inside <main> carries data-pagefind-meta with a 'section' key.
  3. The 'section' value matches what the URL prefix implies.

This linter runs in CI after `hugo --minify` builds public/. It is paired
with tools/test_check_pagefind_meta.py (unit-tested logic on synthetic HTML).
"""

import re
import sys
from pathlib import Path


# URL-prefix → section mapping. Order matters: longer prefixes win.
SECTION_BY_PREFIX = [
    ("/essays/",   "essays"),
    ("/garden/",   "garden"),
    ("/research/", "research"),
    ("/works/",    "works"),
    ("/library/",  "library"),
    ("/about/",    "about"),
    ("/blog/",     "blog"),
    ("/",          "home"),
]

# Pages we skip — taxonomy pages, RSS, /tags/, /series/, /404.html, etc.
# Pagefind ignores them too (no data-pagefind-body), so the linter mustn't
# fail on their absence.
SKIP_PREFIXES = [
    "/tags/",
    "/series/",
    "/categories/",
]
SKIP_FILES = [
    "/index.xml",   # RSS feed (XML, not indexed)
    "/sitemap.xml",
    "/404.html",
]


def parse_meta(html: str) -> dict:
    """Extract data-pagefind-meta="..." kv pairs from the first occurrence.

    Handles both quoted values (unminified) and unquoted values (minified by
    Hugo --minify, which drops quotes from simple attribute values).
    """
    # Try quoted first, then unquoted (minified HTML).
    m = re.search(r'data-pagefind-meta\s*=\s*"([^"]*)"', html)
    if not m:
        m = re.search(r"data-pagefind-meta\s*=\s*([^\s\"'`=<>]+)", html)
    if not m:
        return {}
    out = {}
    for pair in m.group(1).split(","):
        if ":" not in pair:
            continue
        k, v = pair.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def section_from_path(url_path: str) -> str:
    for prefix, section in SECTION_BY_PREFIX:
        if url_path.startswith(prefix):
            return section
    return ""


def url_from_file(file: Path, public: Path) -> str:
    rel = file.relative_to(public)
    parts = rel.parts
    if parts == ("index.html",):
        return "/"
    # .../foo/index.html → /foo/
    if parts[-1] == "index.html":
        return "/" + "/".join(parts[:-1]) + "/"
    return "/" + "/".join(parts)


def should_skip(url_path: str) -> bool:
    for prefix in SKIP_PREFIXES:
        if url_path.startswith(prefix):
            return True
    for f in SKIP_FILES:
        if url_path == f:
            return True
    return False


def validate_page(file: Path, public: Path) -> list:
    url = url_from_file(file, public)
    if should_skip(url):
        return []
    html = file.read_text(encoding="utf-8", errors="replace")

    errors = []
    if not re.search(r'<main[^>]*\sdata-pagefind-body(?=[\s>=])', html):
        errors.append(f"{url}: missing data-pagefind-body on <main>")

    meta = parse_meta(html)
    if "section" not in meta:
        errors.append(f"{url}: missing data-pagefind-meta with 'section' key")
        return errors

    expected = section_from_path(url)
    if expected and meta["section"] != expected:
        errors.append(
            f"{url}: section mismatch — meta says '{meta['section']}', "
            f"URL implies '{expected}'"
        )
    return errors


def main() -> int:
    public = Path("public")
    if not public.is_dir():
        print(
            "check_pagefind_meta: public/ not found. Run `hugo --minify` first.",
            file=sys.stderr,
        )
        return 2

    all_errors = []
    for html_file in public.rglob("index.html"):
        all_errors.extend(validate_page(html_file, public))

    if all_errors:
        print(f"check_pagefind_meta: {len(all_errors)} issue(s):", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("check_pagefind_meta: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
