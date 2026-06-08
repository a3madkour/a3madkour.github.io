#!/usr/bin/env python3
"""Anchor-link affordance linter.

Walks public/**/*.html. For each [id]-bearing element inside <main>
(except those marked data-no-anchor-link), asserts that the immediately-
following sibling element is an <a class="anchor-link"> with the
matching href="#<id>".

Exits 0 on all-pass, 1 on violation. Stdlib only.

Spec: docs/superpowers/specs/2026-06-07-anchor-affordance-design.md §4.1.
"""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path


class _Linter(HTMLParser):
    """Tracks <main> scope and the most-recent [id]-bearing element.

    On every start-tag while inside <main>:
      - If the element has an id (and no data-no-anchor-link) and is NOT
        the anchor-link itself, remember the id as 'pending'. The next
        non-text, non-self-closing start-tag should be the matching
        <a class="anchor-link"> sibling.
      - If we have a 'pending' id and the next start-tag matches an
        anchor-link with the right href, clear the pending; otherwise
        record an error and clear pending (single chance per id).

    We treat the anchor-link as a sibling of the id-bearing element, not
    a child — Hugo's render hook emits it after the heading text but
    INSIDE the <hN>. To handle both cases (sibling and inside-heading),
    the matcher checks the NEXT start-tag regardless of nesting depth.
    """

    def __init__(self, file_path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.file_path = file_path
        self.errors: list[str] = []
        self._main_depth = 0
        self._pending_id: str | None = None
        self._pending_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: v for k, v in attrs}
        if tag == "main":
            self._main_depth += 1
            return
        if self._main_depth <= 0:
            return

        # If we just saw an id and this is its potential follower:
        if self._pending_id is not None:
            cls = (attr_map.get("class") or "").split()
            href = attr_map.get("href") or ""
            if tag == "a" and "anchor-link" in cls and href == f"#{self._pending_id}":
                # Match — clear pending.
                self._pending_id = None
                self._pending_tag = None
            else:
                # First following element is NOT the matching anchor-link.
                self.errors.append(
                    f"{self.file_path}: id='{self._pending_id}' on <{self._pending_tag}> "
                    f"is not immediately followed by <a class='anchor-link' "
                    f"href='#{self._pending_id}'>; got <{tag}> instead"
                )
                self._pending_id = None
                self._pending_tag = None
                # Fall through — this tag itself might have a new id to track.

        # Record a new pending id if this element has one and isn't opted out.
        # Skip the anchor-link itself (its href looks like an id-bearing
        # element if we don't filter it out).
        el_id = attr_map.get("id")
        if el_id is None:
            return
        if "data-no-anchor-link" in attr_map:
            return
        cls = (attr_map.get("class") or "").split()
        if tag == "a" and "anchor-link" in cls:
            return
        self._pending_id = el_id
        self._pending_tag = tag

    def handle_endtag(self, tag: str) -> None:
        if tag == "main" and self._main_depth > 0:
            self._main_depth -= 1


def lint_file(path: Path) -> list[str]:
    html = path.read_text(encoding="utf-8", errors="replace")
    p = _Linter(path)
    try:
        p.feed(html)
    except Exception as e:
        return [f"{path}: HTML parse error: {e}"]
    # Any pending id at EOF means the id-bearing element had no follower at all.
    if p._pending_id is not None:
        p.errors.append(
            f"{path}: id='{p._pending_id}' on <{p._pending_tag}> "
            f"has no following element (anchor-link missing)"
        )
    return p.errors


def run(public: Path) -> tuple[int, list[str]]:
    if not public.is_dir():
        return (0, [])
    all_errors: list[str] = []
    for f in sorted(public.rglob("*.html")):
        all_errors.extend(lint_file(f))
    return (1 if all_errors else 0, all_errors)


def main() -> int:
    public = Path("public")
    if not public.is_dir():
        print(
            "check_anchor_link: public/ not found. Run `hugo --minify` first.",
            file=sys.stderr,
        )
        return 2
    rc, errors = run(public)
    if errors:
        print(f"check_anchor_link: {len(errors)} violation(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("check_anchor_link: OK (every [id] inside <main> has a matching <a class='anchor-link'>).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
