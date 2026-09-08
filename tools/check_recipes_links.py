#!/usr/bin/env python3
"""Recipe source-URL + video-id well-formedness linter. Stdlib only."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

URL_RE = re.compile(r"^https?://\S+$")
VIDEO_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
# Any URI scheme; used to reject the ones the template cannot resolve
# (uppercase HTTPS://, data:, ftp:) with a message that names the cause.
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")


def lint_file(md: Path) -> list[str]:
    errs: list[str] = []
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return []
    sources = fm.get("sources")
    if isinstance(sources, list):
        for i, s in enumerate(sources):
            if isinstance(s, dict) and s.get("url"):
                if not URL_RE.match(str(s["url"])):
                    errs.append(f"{md}: sources[{i}] url is not a well-formed http(s) URL")
    vid = fm.get("video")
    if vid:
        if not VIDEO_RE.match(str(vid)):
            errs.append(f"{md}: video '{vid}' is not an 11-char YouTube id")
    # `image` reaches only the JSON-LD blob, never a rendered <img>, so a broken
    # path is invisible to every other check (the built-HTML link crawler included).
    # The branch keys below mirror layouts/partials/recipes/schema-recipe.html
    # exactly — http(s) prefix, then "/" prefix, then bundle-relative. Keep the two
    # in lockstep: a shape the template resolves but this rejects is safe (a loud
    # CI failure); the reverse ships a silently broken URL into the JSON-LD.
    img = fm.get("image")
    if img:  # "" / null / [] are falsy here and in the template's `with`.
        if not isinstance(img, str):
            # schema-recipe.html renders one value (`hasPrefix` on a slice breaks
            # the build), so a list is rejected outright rather than checked
            # element-wise. The value is deliberately not interpolated: a Python
            # repr in the error text is not something an author can act on.
            errs.append(f"{md}: image must be a single string path or URL, "
                        f"not a {type(img).__name__}")
        elif img.strip() not in ("", "null"):
            val = img.strip()
            # A query string or fragment is a legitimate cache-buster that the
            # template resolves fine; strip it before touching the filesystem.
            path = val.split("#", 1)[0].split("?", 1)[0]
            if val.startswith(("http://", "https://")):
                if not URL_RE.match(val):
                    errs.append(f"{md}: image is not a well-formed http(s) URL")
            elif val.startswith("//"):
                errs.append(f"{md}: image '{val}' is protocol-relative; "
                            f"use an absolute https:// URL")
            elif SCHEME_RE.match(val):
                errs.append(f"{md}: image '{val}' uses an unsupported URI scheme; "
                            f"use an absolute http(s) URL, a root-relative /path, "
                            f"or a file in the page bundle")
            elif not path.strip("/"):
                errs.append(f"{md}: image '{val}' has no path to resolve")
            elif val.startswith("/"):
                # md is <repo>/content/recipes/<slug>/index.md, so four parents up
                # is the repo root. This depth is coupled to run() walking ONLY the
                # direct children of content/recipes/ — if nested bundles are ever
                # allowed, this arithmetic breaks silently and every root-relative
                # image starts resolving against the wrong tree. Fix both together.
                target = md.parent.parent.parent.parent / "static" / path.lstrip("/")
                if not target.exists():
                    errs.append(f"{md}: image '{val}' not found under static/")
            else:
                if not (md.parent / path).exists():
                    errs.append(f"{md}: image '{val}' not found in the page bundle")
    return errs


def run(repo_root: Path) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    root = repo_root / "content" / "recipes"
    if root.exists():
        for child in sorted(root.iterdir()):
            md = child / "index.md"
            if child.is_dir() and md.exists():
                all_errs.extend(lint_file(md))
    return (1 if all_errs else 0), all_errs


def main() -> int:
    rc, errs = run(Path(__file__).resolve().parent.parent)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_recipes_links: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
