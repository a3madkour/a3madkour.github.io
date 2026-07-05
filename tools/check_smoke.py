"""Smoke test for the post-build site.

Asserts that the eight top-level URLs listed in spec §11 each resolve to a
non-empty, parseable HTML file in public/. Runs in CI after `hugo --minify`.
Also asserts that the D.1 kitchen-sink essay (/essays/example-five/) contains
at least one anchor-link element — catches catastrophic regressions of the
Tier 2.1 anchor-affordance pipeline before the full linter runs.
Also asserts that the explorables fixture (/essays/example-explorables/)
contains all three widget placeholders and its fingerprinted JS bundle tag.

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

# Tier 2.1 anchor-affordance smoke target.
ANCHOR_LINK_REQUIRED_URLS = ["/essays/example-five/"]

# Explorables runtime smoke target: widget placeholders + fingerprinted bundle.
EXPLORABLES_URL = "/essays/example-explorables/"
EXPLORABLES_REQUIRED_SUBSTRINGS = [
    "data-widget-id=k-square",
    "data-widget-id=gaussian",
    "data-widget-id=spinner",
    "src=/js/explorables-example-explorables.",
]


class _Parser(HTMLParser):
    """Tracks whether <html> + <body> were seen and counts .anchor-link tags."""

    def __init__(self) -> None:
        super().__init__()
        self.saw_html = False
        self.saw_body = False
        self.anchor_link_count = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "html":
            self.saw_html = True
        elif tag == "body":
            self.saw_body = True
        elif tag == "a":
            for k, v in attrs:
                if k == "class" and v and "anchor-link" in v.split():
                    self.anchor_link_count += 1
                    break


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
    if url in ANCHOR_LINK_REQUIRED_URLS and parser.anchor_link_count == 0:
        errors.append(
            f"{url}: no <a class='anchor-link'> elements found — "
            "Tier 2.1 anchor-affordance pipeline broken"
        )
    if url == EXPLORABLES_URL:
        for substr in EXPLORABLES_REQUIRED_SUBSTRINGS:
            if substr not in html:
                errors.append(
                    f"{url}: expected substring not found in rendered HTML: {substr!r}"
                )
    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    public = repo_root / "public"
    all_errors: list[str] = []
    for url in URLS + ANCHOR_LINK_REQUIRED_URLS + [EXPLORABLES_URL]:
        all_errors.extend(check_url(public, url))
    return (1 if all_errors else 0, all_errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    public = repo_root / "public"
    if not public.is_dir():
        print(
            "check_smoke: public/ not found. Run `hugo --minify` first.",
            file=sys.stderr,
        )
        return 2
    rc, errors = run(repo_root)
    if errors:
        print(f"check_smoke: {len(errors)} issue(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
    if rc == 0:
        print(f"check_smoke: OK ({len(URLS) + len(ANCHOR_LINK_REQUIRED_URLS) + 1} URLs)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
