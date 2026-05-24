#!/usr/bin/env python3
"""Org-asset link linter (24th in CI).

Walks every `content/<section>/<slug>/index.md` bundle, extracts `<img src>`,
`<a href>`, and markdown `![alt](src)` references, and verifies:

  - References starting with `/notes-shared/` resolve to existing files in
    `static/notes-shared/`.
  - Relative references (no scheme, no leading `/`, no `#`) resolve inside
    the bundle dir.
  - No `../` path traversal in any reference.
  - Orphan check: every regular file in the bundle (except `index.md`,
    `_index.md`, `index.*.md`, dotfiles) must be referenced.

External links (`http://`, `https://`, `mailto:`, `tel:`), anchor-only refs
(`#section`), and internal Hugo routes (`/garden/<slug>/`, etc.) are skipped.

Cross-namespace validation is NOT performed here (elisp-side only — Python
has no view of the org source).

Exits 0 on success, 1 on any error.  Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


# Match <img src="..."> and <a href="..."> in the bundle's index.md body.
IMG_SRC_RE = re.compile(r'<img\b[^>]*\bsrc="([^"]*)"', re.IGNORECASE)
A_HREF_RE = re.compile(r'<a\b[^>]*\bhref="([^"]*)"', re.IGNORECASE)
# Markdown image syntax ![alt](src) — future-proofing for B's slices.
MD_IMG_RE = re.compile(r'!\[[^\]]*\]\(([^)\s]+)')
# Hugo shortcode syntax: {{< name attr="value" ... >}}
# Extracts src, figure, image, etc. attributes.
SHORTCODE_ATTR_RE = re.compile(r'{{\s*<\s*\w+\b[^>]*?\b(?:src|figure|image|href)="([^"]*)"', re.IGNORECASE)


# Internal Hugo routes we skip (not file references).
INTERNAL_ROUTE_PREFIXES = (
    "/about/", "/blog/", "/essays/", "/garden/", "/library/",
    "/research/", "/streams/", "/works/",
)
EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "tel:", "ftp://")
SKIP_BUNDLE_FILES = {"index.md", "_index.md"}
SKIP_BUNDLE_RE = re.compile(r"\Aindex\..+\.md\Z")  # index.<lang>.md


def _strip_frontmatter(text: str) -> tuple[str, str]:
    """Return (body, frontmatter_text) tuple."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if m:
        frontmatter = m.group(1)
        body = text[m.end():]
        return body, frontmatter
    return text, ""


def _extract_refs(body: str, frontmatter: str = "") -> list[str]:
    refs: list[str] = []
    refs.extend(IMG_SRC_RE.findall(body))
    refs.extend(A_HREF_RE.findall(body))
    refs.extend(MD_IMG_RE.findall(body))
    refs.extend(SHORTCODE_ATTR_RE.findall(body))
    # Extract asset-referencing frontmatter fields: hero, image, cover, etc.
    for field in ("hero", "image", "cover"):
        m = re.search(rf"^{field}:\s*['\"]?([^\s'\"]+)['\"]?\s*$", frontmatter, re.MULTILINE)
        if m:
            refs.append(m.group(1))
    return refs


def _classify(ref: str) -> str:
    """Return 'external' | 'anchor' | 'internal-route' | 'shared' | 'traversal'
    | 'local'."""
    if any(ref.startswith(s) for s in EXTERNAL_SCHEMES):
        return "external"
    if ref.startswith("#"):
        return "anchor"
    if ref.startswith("/notes-shared/"):
        return "shared"
    if any(ref.startswith(p) for p in INTERNAL_ROUTE_PREFIXES):
        return "internal-route"
    if ref.startswith("/"):
        # Other absolute /paths/ — treat as internal route (skip)
        return "internal-route"
    if "../" in ref:
        return "traversal"
    return "local"


def lint_bundle(bundle: Path, static_notes_shared: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    index = bundle / "index.md"
    if not index.exists():
        return errors, warnings
    text = index.read_text(encoding="utf-8")
    body, frontmatter = _strip_frontmatter(text)
    refs = _extract_refs(body, frontmatter)
    referenced_locals: set[str] = set()
    for ref in refs:
        kind = _classify(ref)
        if kind in ("external", "anchor", "internal-route"):
            continue
        if kind == "traversal":
            errors.append(f"{bundle}: path traversal in ref: {ref}")
            continue
        if kind == "shared":
            target = static_notes_shared / ref[len("/notes-shared/"):]
            if not target.exists():
                errors.append(f"{bundle}: shared ref does not resolve: {ref} (looked at {target})")
            continue
        # kind == "local"
        target = bundle / ref
        if not target.exists():
            errors.append(f"{bundle}: local ref does not resolve: {ref}")
        else:
            referenced_locals.add(ref)
    # Orphan check.
    for f in sorted(bundle.iterdir()):
        if not f.is_file():
            continue
        name = f.name
        if name.startswith("."):
            continue
        if name in SKIP_BUNDLE_FILES or SKIP_BUNDLE_RE.fullmatch(name):
            continue
        if name not in referenced_locals:
            errors.append(f"{bundle}: orphan file not referenced by index.md: {name}")
    return errors, warnings


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    content_dir = repo_root / "content"
    static_notes_shared = repo_root / "static" / "notes-shared"
    if not content_dir.is_dir():
        print(f"error: {content_dir} not found", file=sys.stderr)
        return 1
    errors: list[str] = []
    warnings: list[str] = []
    bundle_count = 0
    for section in sorted(content_dir.iterdir()):
        if not section.is_dir():
            continue
        for entry in sorted(section.iterdir()):
            if not entry.is_dir():
                continue
            if not (entry / "index.md").exists():
                continue
            bundle_count += 1
            e, w = lint_bundle(entry, static_notes_shared)
            errors.extend(e)
            warnings.extend(w)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} asset-ref issue(s) across {bundle_count} bundle(s).",
              file=sys.stderr)
        return 1
    print(f"OK — verified {bundle_count} bundle(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
