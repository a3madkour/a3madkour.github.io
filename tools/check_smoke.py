"""Smoke test for the post-build site.

Asserts that the seven top-level URLs listed in spec §11 each resolve to a
non-empty, parseable HTML file in public/. Runs in CI after `hugo --minify`.

No paired unit-test sibling: the logic is too thin (it's mostly stdlib
HTMLParser + file-exists checks). Documented in spec §3.1.
"""

import sys
from html.parser import HTMLParser
from pathlib import Path


# Spec §11 list.
URLS = [
    "/",
    "/essays/",
    "/garden/",
    "/research/",
    "/works/",
    "/about/",
    "/library/",
    "/credits/",
]


class _Parser(HTMLParser):
    """Tracks whether at least one <html> and <body> tag was seen."""

    def __init__(self) -> None:
        super().__init__()
        self.saw_html = False
        self.saw_body = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "html":
            self.saw_html = True
        elif tag == "body":
            self.saw_body = True


def file_for_url(public: Path, url: str) -> Path:
    rel = url.strip("/")
    if not rel:
        return public / "index.html"
    return public / rel / "index.html"


def check_url(public: Path, url: str) -> list:
    f = file_for_url(public, url)
    errors = []
    if not f.is_file():
        errors.append(f"{url}: file missing at {f.relative_to(public)}")
        return errors
    if f.stat().st_size == 0:
        errors.append(f"{url}: empty file at {f.relative_to(public)}")
        return errors
    html = f.read_text(encoding="utf-8", errors="replace")
    parser = _Parser()
    try:
        parser.feed(html)
    except Exception as e:
        errors.append(f"{url}: HTML parse error: {e}")
        return errors
    if not parser.saw_html:
        errors.append(f"{url}: no <html> tag")
    if not parser.saw_body:
        errors.append(f"{url}: no <body> tag")
    return errors


def main() -> int:
    public = Path("public")
    if not public.is_dir():
        print(
            "check_smoke: public/ not found. Run `hugo --minify` first.",
            file=sys.stderr,
        )
        return 2

    all_errors = []
    for url in URLS:
        all_errors.extend(check_url(public, url))

    if all_errors:
        print(f"check_smoke: {len(all_errors)} issue(s):", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"check_smoke: OK ({len(URLS)} URLs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
