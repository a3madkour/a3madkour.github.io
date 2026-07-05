#!/usr/bin/env python3
"""Built-HTML link-integrity crawler (R6.3).

The `check_*_links.py` linters validate frontmatter-declared refs pre-build;
nothing crawled the RENDERED `public/` for broken `<a href>`s. This does: every
internal `<a href>` must resolve to a file in `public/`, and every fragment to a
real anchor in the target document. External links are out of scope.

Hugo's HTML minifier strips attribute quotes (`href=/essays/`), so parsing uses
stdlib `html.parser` (not regex). Runs AFTER the Hugo build, on `public/`.

Stdlib only. Exits 0 when every internal link + fragment resolves, 1 otherwise.
"""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

# baseURL — same-domain absolute hrefs are internal. Update if the site moves.
SITE_ORIGIN = "https://a3madkour.github.io"
SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:")


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = dict(attrs)
        if elem_id := d.get("id"):
            self.ids.add(elem_id)
        if tag == "a":
            if name := d.get("name"):
                self.ids.add(name)
            href = d.get("href")
            if href is not None:
                self.hrefs.append(href)


def parse_html(text: str) -> tuple[set[str], list[str]]:
    p = _LinkParser()
    p.feed(text)
    return p.ids, p.hrefs


def is_skip(href: str) -> bool:
    """True for links the crawler does not check (external / non-navigational)."""
    h = href.strip()
    if h == "":
        return True  # empty href = current page, no-op
    low = h.lower()
    if low.startswith(SITE_ORIGIN.lower()):
        return False  # same-domain absolute = internal
    if h.startswith("//"):
        return True  # protocol-relative external
    return low.startswith(SKIP_SCHEMES)


def resolve(href: str, source_url: str) -> tuple[str, str]:
    """Resolve `href` (found on the page at `source_url`) to (path, fragment).
    `path` is a URL path under the site root; `?query` is dropped."""
    h = href.strip()
    if h.lower().startswith(SITE_ORIGIN.lower()):
        h = h[len(SITE_ORIGIN):] or "/"
    sp = urlsplit(urljoin(source_url, h))
    return sp.path, sp.fragment


def resolve_file(path: str, public: Path) -> str | None:
    """Map a URL path to an existing file's posix relpath under `public`, or None."""
    p = unquote(path).lstrip("/")
    if p == "":
        cands = ["index.html"]
    elif p.endswith("/"):
        cands = [p + "index.html"]
    else:
        cands = [p + "/index.html", p, p + ".html"]
    for c in cands:
        if (public / c).is_file():
            return c
    return None


def url_path_for(relpath: str) -> str:
    """public relpath -> the URL path a browser would use for that document."""
    if relpath == "index.html":
        return "/"
    if relpath.endswith("/index.html"):
        return "/" + relpath[: -len("index.html")]
    return "/" + relpath


def run(public: Path) -> tuple[int, list[str]]:
    if not public.is_dir():
        return (1, [f"public/ not found at {public} — run `hugo --minify` first"])
    anchors: dict[str, set[str]] = {}
    links: dict[str, list[str]] = {}
    for f in sorted(public.rglob("*.html")):
        rel = f.relative_to(public).as_posix()
        ids, hrefs = parse_html(f.read_text(encoding="utf-8", errors="replace"))
        anchors[rel] = ids
        links[rel] = hrefs

    errors: list[str] = []
    for rel in sorted(links):
        source_url = url_path_for(rel)
        for href in links[rel]:
            if is_skip(href):
                continue
            path, frag = resolve(href, source_url)
            target = resolve_file(path, public)
            if target is None:
                errors.append(f'{rel}: <a href="{href}"> -> missing target ({path})')
                continue
            if frag and frag != "top" and target.endswith(".html"):
                if frag not in anchors.get(target, set()):
                    errors.append(
                        f'{rel}: <a href="{href}"> -> missing anchor #{frag} in {target}'
                    )
    return (1 if errors else 0, errors)


def main() -> int:
    public = Path("public")
    rc, errors = run(public)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} broken internal link(s).", file=sys.stderr)
        return rc
    print("OK — every internal <a href> + fragment resolves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
