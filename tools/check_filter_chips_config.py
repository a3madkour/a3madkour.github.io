#!/usr/bin/env python3
"""Filter-chips config linter.

Validates `data/filter-chips.yaml`: every entry in each section's
`primary_tags` must resolve to a tag used by at least one non-draft note in
that section's `content/<section>/`. Optional `primary_top_k` must be a
positive integer.

Exits 0 on all-pass (or absent config file), 1 on any violation.
Stdlib only — imports the YAML-subset parser from check_fixtures.

Unsupported YAML features (not handled by the narrow subset parser):
- Block-style lists (`- item` form); only flow-style (`["a", "b"]`) is parsed.
- Inline `#` comments on value lines (the `#` and everything after it is
  treated as part of the value).
- Multi-line / folded / literal-block strings.
- Anchors and aliases (`&anchor`, `*alias`).
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


def parse_config(text: str) -> tuple[dict[str, dict[str, object]], list[str]]:
    """Parse the data/filter-chips.yaml subset we accept.

    Returns (config_dict, parse_errors).  Any non-blank, non-comment line
    inside a section block that doesn't match the 2-space KV pattern is
    recorded as a parse error rather than silently dropped.
    """
    out: dict[str, dict[str, object]] = {}
    parse_errors: list[str] = []
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = SECTION_RE.match(line)
        if m:
            section = m.group(1)
            if section is None:
                continue
            current = section
            out[section] = {}
            continue
        m = KV_RE.match(line)
        if m and current is not None:
            key = m.group(1)
            value = m.group(2)
            if key is None or value is None:
                continue
            out[current][key] = parse_scalar(value.strip())
        elif current is not None:
            parse_errors.append(
                f"data/filter-chips.yaml: unrecognized line in section "
                f"'{current}' (expected 2-space indent): {line!r}"
            )
    return out, parse_errors


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


# Sections whose content lives at a path other than `content/<section>/`.
# Keys must match the top-level YAML key; values are relative to repo_root.
SECTION_PATH_OVERRIDES: dict[str, str] = {
    "games": "content/works/games",
    "music": "content/works/music",
    "poetry": "content/works/poetry",
}


def _section_content_path(repo_root: Path, section: str) -> Path:
    """Return the content directory for a section key."""
    override = SECTION_PATH_OVERRIDES.get(section)
    if override:
        return repo_root / override
    return repo_root / "content" / section


def run(repo_root: Path) -> tuple[int, list[str]]:
    config_path = repo_root / "data" / "filter-chips.yaml"
    errors: list[str] = []

    if not config_path.exists():
        return 0, []

    config, parse_errors = parse_config(config_path.read_text())
    errors.extend(parse_errors)

    ALLOWED_KEYS = {"primary_tags", "primary_top_k"}

    for section, section_cfg in config.items():
        # Flag unrecognized keys before per-key validation
        for unknown in sorted(set(section_cfg.keys()) - ALLOWED_KEYS):
            errors.append(
                f"data/filter-chips.yaml:{section}.{unknown} is not a recognized key"
            )

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
        content_path = _section_content_path(repo_root, section)
        display_path = str(content_path.relative_to(repo_root))
        live = collect_tags(content_path)
        for entry in primary:
            if str(entry) not in live:
                errors.append(
                    f"data/filter-chips.yaml:{section}.primary_tags: "
                    f'"{entry}" is not used by any non-draft note '
                    f"in /{display_path}/"
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
