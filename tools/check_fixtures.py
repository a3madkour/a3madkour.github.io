#!/usr/bin/env python3
"""Essay fixture frontmatter linter.

Walks `content/essays/*/index.md`, validates frontmatter, and checks every
`{{< cite "key" >}}` reference resolves against `data/citations.yaml`.

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
from datetime import date as Date
from pathlib import Path

REQUIRED_FIELDS = {
    "title", "date", "lastmod", "draft", "summary",
    "tags", "series", "series_order",
    "toc", "has_sidenotes", "has_citations", "has_footnotes",
    "has_math", "has_widgets", "has_video_sync",
}
ALLOWED_TILE_SIZE = {"large", "medium", "small"}

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
CITE_RE = re.compile(r'\{\{<\s*cite\s+"([^"]+)"\s*>\}\}')


def parse_frontmatter(text: str) -> dict[str, object] | None:
    """Parse YAML frontmatter — narrow subset, no third-party deps.

    Supports:
      - Top-level key: value pairs (scalars, inline arrays, quoted strings).
      - Empty-value top-level keys followed by indented block-sequence items
        (each item is either a scalar or a flow-style mapping `{k: v, ...}`).

    Does NOT support: block-style nested mappings, multi-document streams,
    anchors/aliases, or any other YAML feature beyond what the existing
    essay/garden/research fixtures need.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    out: dict[str, object] = {}
    lines = m.group(1).splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        # Indented lines without a preceding empty-value key are ignored
        # (the look-ahead block below consumes them when appropriate).
        if raw.startswith((" ", "\t")) or ":" not in stripped:
            i += 1
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if value != "":
            out[key] = parse_scalar(value)
            i += 1
            continue
        # Empty value — look for an indented block sequence on the next lines.
        items: list[object] = []
        j = i + 1
        while j < len(lines):
            nxt = lines[j]
            nxt_stripped = nxt.strip()
            if not nxt_stripped:
                j += 1
                continue
            if nxt.startswith((" ", "\t")) and nxt_stripped.startswith("-"):
                item_text = nxt_stripped[1:].strip()
                items.append(_parse_block_item(item_text))
                j += 1
                continue
            break
        if items:
            out[key] = items
            i = j
        else:
            out[key] = ""
            i += 1
    return out


def _parse_block_item(s: str) -> object:
    """Parse a single block-sequence item value (text after '- ')."""
    if s.startswith("{") and s.endswith("}"):
        return _parse_flow_mapping(s[1:-1])
    return parse_scalar(s)


def _parse_flow_mapping(inner: str) -> dict[str, object]:
    """Parse the inside of a flow-style mapping `{a: 1, b: "two"}`."""
    out: dict[str, object] = {}
    for piece in _split_top_commas(inner):
        if ":" not in piece:
            continue
        key, _, value = piece.partition(":")
        out[key.strip()] = parse_scalar(value.strip())
    return out


def _split_top_commas(s: str) -> list[str]:
    """Split a flow-mapping body on commas not inside quotes or braces."""
    parts: list[str] = []
    buf: list[str] = []
    quote = None
    depth = 0
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ('"', "'"):
            quote = ch
            buf.append(ch)
            continue
        if ch == "{":
            depth += 1
            buf.append(ch)
            continue
        if ch == "}":
            depth -= 1
            buf.append(ch)
            continue
        if ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return parts


def parse_scalar(s: str) -> object:
    if s == "":
        return ""
    if s in ("true", "false"):
        return s == "true"
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        items = [it.strip() for it in inner.split(",")]
        return [it.strip('"').strip("'") for it in items]
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1]
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        y, m, d = (int(x) for x in s.split("-"))
        return Date(y, m, d)
    return s


def parse_citations_yaml(path: Path) -> set[str]:
    """Pull cite keys from data/citations.yaml — looks for two-space-indented
    keys directly under `citations:`."""
    if not path.exists():
        return set()
    keys: set[str] = set()
    in_citations = False
    for raw in path.read_text().splitlines():
        if raw.startswith("citations:"):
            in_citations = True
            continue
        if not in_citations:
            continue
        if raw and not raw.startswith(" "):
            in_citations = False
            continue
        m = re.match(r"^  ([a-zA-Z0-9_\-]+):\s*$", raw)
        if m:
            keys.add(m.group(1))
    return keys


def lint_essay(essay_dir: Path, valid_cite_keys: set[str]) -> list[str]:
    errors: list[str] = []
    md_path = essay_dir / "index.md"
    if not md_path.exists():
        return [f"{essay_dir}: no index.md"]
    text = md_path.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md_path}: no frontmatter"]

    missing = REQUIRED_FIELDS - fm.keys()
    for field in sorted(missing):
        errors.append(f"{md_path}: missing required field '{field}'")

    if "tile_size" in fm and fm["tile_size"] not in ALLOWED_TILE_SIZE:
        errors.append(
            f"{md_path}: tile_size '{fm['tile_size']}' not in {ALLOWED_TILE_SIZE}"
        )

    series = fm.get("series", "")
    series_order = fm.get("series_order", 0)
    if series and series_order == 0:
        errors.append(
            f"{md_path}: series '{series}' set but series_order is 0"
        )

    hero = fm.get("hero", "")
    if hero:
        if not (essay_dir / str(hero)).exists():
            errors.append(f"{md_path}: hero file '{hero}' not found in page bundle")

    date = fm.get("date")
    lastmod = fm.get("lastmod")
    if isinstance(date, Date) and isinstance(lastmod, Date) and lastmod < date:
        errors.append(f"{md_path}: lastmod {lastmod} is before date {date}")

    fm_match = FRONTMATTER_RE.match(text)
    body = text[fm_match.end():] if fm_match else ""
    for cite_key in CITE_RE.findall(body):
        if cite_key not in valid_cite_keys:
            errors.append(
                f"{md_path}: cite key '{cite_key}' not found in data/citations.yaml"
            )
    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    essays_dir = repo_root / "content" / "essays"
    citations_path = repo_root / "data" / "citations.yaml"
    valid_keys = parse_citations_yaml(citations_path)

    errors: list[str] = []
    if essays_dir.exists():
        for essay_dir in sorted(essays_dir.iterdir()):
            if not essay_dir.is_dir():
                continue
            errors.extend(lint_essay(essay_dir, valid_keys))

    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        print("Fixture lint failures:")
        for e in errors:
            print(f"  {e}")
    else:
        print("All essay fixtures pass linter.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
