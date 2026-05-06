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
    """Parse YAML frontmatter — narrow subset, no third-party deps."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    out: dict[str, object] = {}
    for raw in m.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = parse_scalar(value.strip())
    return out


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
