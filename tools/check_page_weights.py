"""Validate per-page payload size against spec §8 budgets.

Walks public/ post-`hugo --minify`. For each rendered index.html, parses
<link rel="stylesheet">, <script src=>, and <img src=> references that point
to local assets under public/. Sums HTML bytes + linked asset bytes.
Compares against a per-URL budget from the prefix classifier.

External resources (Google Fonts URLs, CDN scripts) are excluded — they're
not on our deploy and not bound by §8.

This linter runs in CI after `hugo --minify` and after the Pagefind index
build. Paired with tools/test_check_page_weights.py.
"""

from __future__ import annotations
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


# Ordered budget table (prefix → bytes). First match wins, EXCEPT "/" is
# treated as an exact-match — handled in budget_for() below.
BUDGETS_PREFIX = [
    ("/garden/graph/",   600_000),
    ("/research/graph/", 600_000),
    ("/works/graph/",    600_000),
    ("/works/music/",    500_000),   # music index + per-music-slug pages
    ("/works/",          600_000),   # works umbrella + per-game/poetry pages
    ("/garden/",         600_000),   # garden index + per-note pages
    ("/research/",       600_000),   # research index inlines the graph JS bundle
    ("/library/",        500_000),   # library leaves carry cover-image payloads
]

BUDGET_HOMEPAGE = 500_000   # exact match `/`
BUDGET_DEFAULT = 100_000


# URLs we don't audit (taxonomy pages, RSS feeds, sitemap, 404).
SKIP_PREFIXES = ("/tags/", "/series/", "/categories/")
SKIP_FILES = ("/index.xml", "/sitemap.xml", "/404.html")


@dataclass
class PageAudit:
    url: str
    file: Path
    budget: int
    html_bytes: int
    css_bytes: int
    js_bytes: int
    img_bytes: int

    @property
    def total(self) -> int:
        return self.html_bytes + self.css_bytes + self.js_bytes + self.img_bytes

    @property
    def over_budget(self) -> bool:
        return self.total > self.budget


def budget_for(url: str) -> int:
    if url == "/":
        return BUDGET_HOMEPAGE
    for prefix, budget in BUDGETS_PREFIX:
        if url.startswith(prefix):
            return budget
    return BUDGET_DEFAULT


class _RefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.css: list[str] = []
        self.js: list[str] = []
        self.img: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        a = dict(attrs)
        if tag == "link" and a.get("rel") == "stylesheet" and a.get("href"):
            self.css.append(a["href"])
        elif tag == "script" and a.get("src"):
            self.js.append(a["src"])
        elif tag == "img" and a.get("src"):
            self.img.append(a["src"])


def _is_local(ref: str) -> bool:
    if ref.startswith("//"):
        return False
    if re.match(r"^[a-zA-Z]+://", ref):
        return False
    return ref.startswith("/")


def extract_refs(html: str) -> tuple[list[str], list[str], list[str]]:
    p = _RefParser()
    p.feed(html)
    return (
        [r for r in p.css if _is_local(r)],
        [r for r in p.js if _is_local(r)],
        [r for r in p.img if _is_local(r)],
    )


def sum_asset_bytes(public: Path, refs: list[str]) -> int:
    total = 0
    for ref in refs:
        rel = ref.lstrip("/")
        f = public / rel
        if f.is_file():
            total += f.stat().st_size
    return total


def url_from_file(file: Path, public: Path) -> str:
    rel = file.relative_to(public)
    parts = rel.parts
    if parts == ("index.html",):
        return "/"
    if parts[-1] == "index.html":
        return "/" + "/".join(parts[:-1]) + "/"
    return "/" + "/".join(parts)


def should_skip(url: str) -> bool:
    return url.startswith(SKIP_PREFIXES) or url in SKIP_FILES


def audit_page(file: Path, public: Path) -> PageAudit:
    url = url_from_file(file, public)
    html_bytes = file.stat().st_size
    html = file.read_text(encoding="utf-8", errors="replace")
    css_refs, js_refs, img_refs = extract_refs(html)
    css = sum_asset_bytes(public, css_refs)
    js = sum_asset_bytes(public, js_refs)
    img = sum_asset_bytes(public, img_refs)
    return PageAudit(
        url=url,
        file=file,
        budget=budget_for(url),
        html_bytes=html_bytes,
        css_bytes=css,
        js_bytes=js,
        img_bytes=img,
    )


def main() -> int:
    public = Path("public")
    if not public.is_dir():
        print(
            "check_page_weights: public/ not found. Run `hugo --minify` first.",
            file=sys.stderr,
        )
        return 2

    failures: list[PageAudit] = []
    audited = 0
    for f in sorted(public.rglob("index.html")):
        url = url_from_file(f, public)
        if should_skip(url):
            continue
        audited += 1
        result = audit_page(f, public)
        if result.over_budget:
            failures.append(result)

    if failures:
        print(f"check_page_weights: {len(failures)} page(s) over budget:", file=sys.stderr)
        header = f"{'PAGE':<48} {'BUDGET':>10} {'ACTUAL':>10} {'HTML':>8} {'CSS':>8} {'JS':>8} {'IMG':>8}"
        print(header, file=sys.stderr)
        for r in failures:
            print(
                f"{r.url:<48} {r.budget:>10,} {r.total:>10,} "
                f"{r.html_bytes:>8,} {r.css_bytes:>8,} {r.js_bytes:>8,} {r.img_bytes:>8,}",
                file=sys.stderr,
            )
        return 1

    print(f"check_page_weights: OK ({audited} pages audited)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
