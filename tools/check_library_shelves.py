#!/usr/bin/env python3
"""Library shelves linter.

Asserts:
  - data/library-media.yaml exists, parses, has media[] list with required keys.
  - For each media[].key: data/<key>.yaml exists AND assets/images/icons/<glyph>.svg exists.
  - data/library-shelves.yaml is optional; if present, every shelf has exactly
    one of tag: or items:, every slug in items: resolves to a real library item,
    and any shelf with items: count > 12 has a corresponding content stub.
  - hero: slug (if present) resolves to a real item.
  - No orphan stubs under content/library/shelves/.

Exits 0 on success, 1 on any error. Stdlib only. Paired with
tools/test_check_library_shelves.py.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_MEDIA_KEYS = {"key", "label", "glyph", "cover_aspect"}
MEDIUM_YAMLS = ("reading", "listening", "playing", "watching")
SHELF_ITEM_CAP = 12


def _parse_simple_yaml(text: str) -> dict:
    """A flat-stack YAML reader for the limited shapes we use.

    Handles: top-level keys (string scalars), list-of-maps (each map's keys are
    string scalars or list-of-scalars), nested 2-deep maps. Comments stripped.
    Does NOT handle arbitrary YAML — designed for our specific schemas.
    """
    out: dict = {}
    current_list_key: str | None = None
    current_item: dict | None = None
    current_sublist: list | None = None

    for raw in text.splitlines():
        # Strip comments + trailing whitespace
        line = re.sub(r"\s+#.*$", "", raw).rstrip()
        if not line.strip():
            continue

        # Track indentation
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0 and ":" in stripped and not stripped.startswith("-"):
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            current_sublist = None
            if val == "":
                # List or map following
                current_list_key = key
                out[key] = []
                current_item = None
            else:
                # Scalar
                out[key] = _scalar(val)
                current_list_key = None
                current_item = None
        elif current_list_key is not None and indent == 2 and stripped.startswith("- "):
            # New list item (top-level list, indent exactly 2)
            current_item = {}
            out[current_list_key].append(current_item)
            current_sublist = None
            rest = stripped[2:].strip()
            if ":" in rest:
                key, _, val = rest.partition(":")
                key = key.strip()
                val = val.strip()
                if val == "":
                    current_sublist = []
                    current_item[key] = current_sublist
                else:
                    current_item[key] = _scalar(val)
        elif current_item is not None and indent >= 2:
            if stripped.startswith("- "):
                # Sublist scalar
                if current_sublist is not None:
                    current_sublist.append(_scalar(stripped[2:].strip()))
                continue
            if ":" not in stripped:
                continue
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "":
                current_sublist = []
                current_item[key] = current_sublist
            else:
                current_item[key] = _scalar(val)
                current_sublist = None
    return out


def _scalar(s: str):
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_scalar(x.strip()) for x in inner.split(",")]
    if re.match(r"^-?\d+$", s):
        return int(s)
    if re.match(r"^-?\d+\.\d+$", s):
        return float(s)
    return s


def _collect_slugs(project_root: Path) -> set[str]:
    slugs: set[str] = set()
    for key in MEDIUM_YAMLS:
        path = project_root / "data" / f"{key}.yaml"
        if not path.exists():
            continue
        parsed = _parse_simple_yaml(path.read_text())
        for item in parsed.get("items", []) or []:
            slug = item.get("slug")
            if slug:
                slugs.add(slug)
    return slugs


def _slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def lint_library_shelves(project_root: Path) -> list[str]:
    errors: list[str] = []

    # 1. library-media.yaml required
    media_path = project_root / "data" / "library-media.yaml"
    if not media_path.exists():
        errors.append("data/library-media.yaml is missing (required)")
        return errors  # everything downstream depends on this

    media = _parse_simple_yaml(media_path.read_text())
    media_entries = media.get("media", []) or []
    if not media_entries:
        errors.append("data/library-media.yaml has no media entries")
        return errors

    for entry in media_entries:
        missing = REQUIRED_MEDIA_KEYS - set(entry.keys())
        if missing:
            errors.append(f"data/library-media.yaml: entry {entry.get('key', '?')} missing keys: {sorted(missing)}")
        key = entry.get("key")
        if key:
            data_file = project_root / "data" / f"{key}.yaml"
            if not data_file.exists():
                errors.append(f"data/library-media.yaml: media key '{key}' has no matching data/{key}.yaml")
        glyph = entry.get("glyph")
        if glyph:
            # Check both top-level and library/ subdir
            candidates = [
                project_root / "assets" / "images" / "icons" / f"{glyph}.svg",
                project_root / "assets" / "images" / "icons" / "library" / f"{glyph}.svg",
            ]
            if not any(c.exists() for c in candidates):
                errors.append(f"data/library-media.yaml: glyph '{glyph}' has no matching SVG under assets/images/icons/")

    # 2. library-shelves.yaml is optional
    shelves_path = project_root / "data" / "library-shelves.yaml"
    if not shelves_path.exists():
        return errors

    shelves_doc = _parse_simple_yaml(shelves_path.read_text())
    all_slugs = _collect_slugs(project_root)

    # 3. Hero slug (optional)
    hero = shelves_doc.get("hero")
    if hero and hero not in all_slugs:
        errors.append(f"data/library-shelves.yaml: hero slug '{hero}' does not resolve to any library item (warning)")

    # 4. Each shelf
    shelves_list = shelves_doc.get("shelves", []) or []
    shelves_dir = project_root / "content" / "library" / "shelves"
    shelf_slugs_in_yaml: set[str] = set()

    for idx, shelf in enumerate(shelves_list):
        title = shelf.get("title", f"<shelf #{idx}>")
        has_tag = "tag" in shelf and shelf.get("tag")
        has_items = "items" in shelf and shelf.get("items")

        if has_tag and has_items:
            errors.append(f"data/library-shelves.yaml: shelf '{title}' has both tag and items (exactly one allowed)")
            continue
        if not has_tag and not has_items:
            errors.append(f"data/library-shelves.yaml: shelf '{title}' has neither tag nor items (exactly one required)")
            continue
        if not shelf.get("intro"):
            errors.append(f"data/library-shelves.yaml: shelf '{title}' missing intro")

        if has_items:
            items = shelf["items"]
            for slug in items:
                if slug not in all_slugs:
                    errors.append(f"data/library-shelves.yaml: shelf '{title}' items[]: slug '{slug}' does not resolve")
            if len(items) > SHELF_ITEM_CAP:
                shelf_slug = _slugify(title)
                shelf_slugs_in_yaml.add(shelf_slug)
                stub = shelves_dir / shelf_slug / "_index.md"
                if not stub.exists():
                    errors.append(f"data/library-shelves.yaml: long shelf '{title}' ({len(items)} items) requires stub at content/library/shelves/{shelf_slug}/_index.md")

    # 5. Orphan stub check
    if shelves_dir.exists():
        for stub in shelves_dir.glob("*/_index.md"):
            slug = stub.parent.name
            if slug not in shelf_slugs_in_yaml:
                # Try frontmatter `shelf:` field too — accept if it matches any yaml shelf
                fm_match = re.search(r"^shelf:\s*(\S+)\s*$", stub.read_text(), re.MULTILINE)
                yaml_match = fm_match.group(1) if fm_match else None
                if yaml_match and yaml_match in shelf_slugs_in_yaml:
                    continue
                errors.append(f"content/library/shelves/{slug}/_index.md: orphan stub (no corresponding shelf in library-shelves.yaml)")

    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    errors = lint_library_shelves(repo_root)
    return (1 if errors else 0, errors)


def main() -> int:
    rc, errors = run(Path(__file__).resolve().parent.parent)
    for e in errors:
        print(e)
    return rc


if __name__ == "__main__":
    sys.exit(main())
