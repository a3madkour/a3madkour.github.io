#!/usr/bin/env python3
"""Anchor-link affordance linter.

Walks public/**/*.html. For each reading-flow target inside <main>
(except those marked data-no-anchor-link), asserts that the target
contains or is immediately followed by an <a class="anchor-link"> with
the matching href="#<id>".

Reading-flow targets per spec §1 are exactly:
  - Headings h1-h6 (Goldmark auto-IDed or :CUSTOM_ID: opted-in)
    The anchor-link is emitted as the LAST start-tag INSIDE the heading
    (render hook) or as the immediately-following sibling (chrome
    partials).
  - Elements whose class list contains a "block-" prefix token (D.1
    semantic blocks: block-theorem / block-soft / block-proof / etc.)
    The anchor-link is emitted as a direct child INSIDE the block div,
    after the block-header <h4>. The linter scans any start-tag at
    depth-1 inside the block container until it finds the anchor-link
    or exits the block.

Other id-bearing elements inside <main> (SVG <symbol>, graph-data
<script>, sidenote <aside>, footnote <sup>/<li>, TOC <nav>, etc.)
are infrastructure, not deep-link targets, and are silently ignored.

Exits 0 on all-pass, 1 on violation. Stdlib only.

Spec: docs/superpowers/specs/2026-06-07-anchor-affordance-design.md §4.1.
"""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

_HEADING_TAGS = {"h1", "h2", "h3"}
# H4-H6 are intentionally excluded — the heading render hook skips the
# §-glyph at those levels to avoid visual density on deeply-nested
# subsections (roadmap row 2.4; render-heading.html). Excluding them from
# this set lets Goldmark-emitted H4/H5/H6 carry their id without a
# matching anchor-link. AMS block-header H4s (block-* container children)
# remain checked via the BLOCK pending mode below.

# HTML void elements that produce a start-tag event but no end-tag event.
_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
    # SVG self-closers commonly found in blocks:
    "path", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "use",
}


def _is_reading_flow_target(tag: str, attr_map: dict[str, str | None]) -> bool:
    """Spec §1: headings + block-* class elements only."""
    if tag in _HEADING_TAGS:
        return True
    classes = (attr_map.get("class") or "").split()
    return any(c.startswith("block-") for c in classes)


def _is_block_container(tag: str, attr_map: dict[str, str | None]) -> bool:
    """True only for D.1 block-* container elements (non-heading targets)."""
    if tag in _HEADING_TAGS:
        return False
    classes = (attr_map.get("class") or "").split()
    return any(c.startswith("block-") for c in classes)


class _Linter(HTMLParser):
    """Tracks <main> scope and reading-flow targets.

    Two pending modes:

    HEADING pending (self._pending_id set, self._block_depth == -1):
      The next start-tag must be <a class="anchor-link" href="#id">.
      This covers both the render-hook form (anchor INSIDE <hN>) and
      the sibling form (anchor after </hN>).

    BLOCK pending (self._pending_id set, self._block_depth >= 0):
      We're inside a block-* container div. Any start-tag at the direct
      child level (self._block_depth == 0 before descent) is a candidate.
      The anchor-link may appear after the <h4 class="block-header">.
      We scan until we find the anchor-link or a non-permitted start-tag
      at depth-0 that is NOT the block-header <h4> or the anchor-link.
      When we exit the block div (_block_depth goes to -1), if the anchor
      was never found we record an error.
    """

    def __init__(self, file_path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.file_path = file_path
        self.errors: list[str] = []
        self._main_depth = 0
        self._pending_id: str | None = None
        self._pending_tag: str | None = None
        # For block-container pending: depth counter relative to the block
        # opening tag (incremented on start-tags, decremented on end-tags).
        # -1 means "not in block-pending mode".
        self._block_depth: int = -1
        # Whether we've already scanned past the block-header <h4>.
        self._block_header_seen: bool = False

    def _clear_pending(self) -> None:
        self._pending_id = None
        self._pending_tag = None
        self._block_depth = -1
        self._block_header_seen = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: v for k, v in attrs}

        if tag == "main":
            self._main_depth += 1
            return
        if self._main_depth <= 0:
            return

        # ── BLOCK-CONTAINER PENDING MODE ──────────────────────────────────
        if self._block_depth >= 0:
            is_void = tag in _VOID_TAGS
            if not is_void:
                self._block_depth += 1
            # Only check direct children (depth becomes 1 on entry).
            if self._block_depth == 1 or (is_void and self._block_depth == 0):
                cls = (attr_map.get("class") or "").split()
                href = attr_map.get("href") or ""
                if tag == "a" and "anchor-link" in cls and href == f"#{self._pending_id}":
                    # Found the anchor-link inside the block — success.
                    self._clear_pending()
                    return
                elif tag == "h4" and "block-header" in cls and not self._block_header_seen:
                    # The block-header <h4> is expected first — allow it.
                    self._block_header_seen = True
                    # Don't track this <h4> as a new pending; fall through.
                elif not is_void:
                    # Unexpected direct child before anchor-link was found.
                    self.errors.append(
                        f"{self.file_path}: id='{self._pending_id}' on "
                        f"<{self._pending_tag}> is missing its "
                        f"<a class='anchor-link' href='#{self._pending_id}'> "
                        f"(unexpected child <{tag}> found first)"
                    )
                    self._clear_pending()
            # Continue — don't return early; the tag might also start a new
            # reading-flow target (handled below after this block).
            # But if we're still in block-pending mode, don't process further.
            if self._block_depth >= 0:
                return

        # ── HEADING PENDING MODE ─────────────────────────────────────────
        if self._pending_id is not None:
            # (block_depth == -1 here, so this is heading-pending)
            cls = (attr_map.get("class") or "").split()
            href = attr_map.get("href") or ""
            if tag == "a" and "anchor-link" in cls and href == f"#{self._pending_id}":
                self._clear_pending()
                return
            else:
                self.errors.append(
                    f"{self.file_path}: id='{self._pending_id}' on "
                    f"<{self._pending_tag}> is not immediately followed by "
                    f"<a class='anchor-link' href='#{self._pending_id}'>; "
                    f"got <{tag}> instead"
                )
                self._clear_pending()
                # Fall through — this tag itself might be a new reading-flow target.

        # ── NEW READING-FLOW TARGET ──────────────────────────────────────
        el_id = attr_map.get("id")
        if el_id is None:
            return
        if "data-no-anchor-link" in attr_map:
            return
        # Skip the anchor-link itself.
        cls = (attr_map.get("class") or "").split()
        if tag == "a" and "anchor-link" in cls:
            return
        # Only track reading-flow targets per spec §1.
        if not _is_reading_flow_target(tag, attr_map):
            return

        self._pending_id = el_id
        self._pending_tag = tag

        if _is_block_container(tag, attr_map):
            # Block-container mode: start counting depth from 0.
            # The opening <div> itself doesn't count as a child, so depth=0.
            self._block_depth = 0
        # else: heading mode, _block_depth remains -1.

    def handle_endtag(self, tag: str) -> None:
        if tag == "main" and self._main_depth > 0:
            self._main_depth -= 1
            return

        if self._block_depth >= 0:
            if tag not in _VOID_TAGS:
                self._block_depth -= 1
            if self._block_depth < 0:
                # Exited the block container without finding the anchor-link.
                if self._pending_id is not None:
                    self.errors.append(
                        f"{self.file_path}: id='{self._pending_id}' on "
                        f"<{self._pending_tag}> has no "
                        f"<a class='anchor-link' href='#{self._pending_id}'> "
                        f"inside the block (anchor-link missing)"
                    )
                self._clear_pending()


def lint_file(path: Path) -> list[str]:
    html = path.read_text(encoding="utf-8", errors="replace")
    p = _Linter(path)
    try:
        p.feed(html)
    except Exception as e:
        return [f"{path}: HTML parse error: {e}"]
    # Any pending heading id at EOF means the anchor-link was never found.
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
    print("check_anchor_link: OK (every reading-flow [id] inside <main> has a matching <a class='anchor-link'>).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
