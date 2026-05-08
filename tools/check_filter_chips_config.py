#!/usr/bin/env python3
"""Filter-chips config linter.

Validates `data/filter-chips.yaml`: every entry in each section's
`primary_tags` must resolve to a tag used by at least one non-draft note in
that section's `content/<section>/`. Optional `primary_top_k` must be a
positive integer.

Exits 0 on all-pass (or absent config file), 1 on any violation.
Stdlib only — imports the YAML-subset parser from check_fixtures.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter, parse_scalar  # noqa: E402

# YAML structure we accept (narrow subset, no third-party deps):
#
#   <section>:
#     primary_tags: ["a", "b"]
#     primary_top_k: 10
#
# - Top-level keys are section names (`garden`, `essays`, ...).
# - `primary_tags` is a flow-style list of strings (same shape as the
#   `tags:` field elsewhere) OR may be omitted/empty.
# - `primary_top_k` is an integer.

SECTION_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*$")
KV_RE = re.compile(r"^\s{2}([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def parse_config(text: str) -> dict[str, dict[str, object]]:
    """Parse the data/filter-chips.yaml subset we accept."""
    out: dict[str, dict[str, object]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = SECTION_RE.match(line)
        if m:
            current = m.group(1)
            out[current] = {}
            continue
        m = KV_RE.match(line)
        if m and current is not None:
            key, value = m.group(1), m.group(2).strip()
            out[current][key] = parse_scalar(value)
    return out


def collect_tags(section_dir: Path) -> set[str]:
    """Return the set of tags used by any non-draft note in section_dir."""
    tags: set[str] = set()
    if not section_dir.exists():
        return tags
    for entry in sorted(section_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        md = entry / "index.md"
        if not md.exists():
            continue
        fm = parse_frontmatter(md.read_text())
        if not fm:
            continue
        if fm.get("draft") is True:
            continue
        page_tags = fm.get("tags") or []
        if isinstance(page_tags, list):
            for t in page_tags:
                tags.add(str(t))
    return tags


def run(repo_root: Path) -> tuple[int, list[str]]:
    config_path = repo_root / "data" / "filter-chips.yaml"
    errors: list[str] = []

    if not config_path.exists():
        return 0, []

    config = parse_config(config_path.read_text())

    for section, section_cfg in config.items():
        # Validate primary_top_k if present
        top_k = section_cfg.get("primary_top_k")
        if top_k is not None:
            if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
                errors.append(
                    f"data/filter-chips.yaml:{section}.primary_top_k "
                    f"must be a positive integer, got {top_k!r}"
                )

        # Validate primary_tags entries
        primary = section_cfg.get("primary_tags")
        if not primary:
            continue
        if not isinstance(primary, list):
            errors.append(
                f"data/filter-chips.yaml:{section}.primary_tags "
                f"must be a list, got {type(primary).__name__}"
            )
            continue
        live = collect_tags(repo_root / "content" / section)
        for entry in primary:
            if str(entry) not in live:
                errors.append(
                    f"data/filter-chips.yaml:{section}.primary_tags: "
                    f'"{entry}" is not used by any non-draft note '
                    f"in /content/{section}/"
                )

    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        print("Filter-chips config lint failures:")
        for e in errors:
            print(f"  {e}")
    else:
        print("All filter-chips config entries pass linter.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
