#!/usr/bin/env python3
"""Citation fixture linter.

Validates `data/citations.yaml` shape and cross-references. Stdlib only.
- Required entry fields: authors (non-empty list of strings), year (int
  in [1500, current_year + 2]), title (non-empty), venue (non-empty).
- Optional: url (must be http/https), notes_ref (must resolve to a
  non-draft `content/garden/<slug>/index.md`).
- Citation keys must be lowercase kebab-case (`^[a-z0-9-]+$`).
- Unknown fields on any entry are errors.

Exits 0 on all-pass, 1 on any violation.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_scalar  # noqa: E402
from check_fixtures import parse_frontmatter  # noqa: E402


ALLOWED_FIELDS = {"authors", "year", "title", "venue", "url", "notes_ref"}
REQUIRED_FIELDS = {"authors", "year", "title", "venue"}
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ENTRY_HEADER_RE = re.compile(r"^  ([^:\s]+):\s*$")
FIELD_RE = re.compile(r"^    ([a-zA-Z_]+):\s*(.*)$")


def parse_citations_yaml(text: str) -> dict[str, dict[str, object]]:
    """Two-level parser for data/citations.yaml.

    Format:
        citations:
          <key>:
            <field>: <scalar-or-inline-array>
            ...
          <key>:
            ...

    Returns the parsed mapping. Lines that don't match expected indent
    or shape are skipped — the validator below catches shape violations.
    """
    entries: dict[str, dict[str, object]] = {}
    in_citations = False
    current_key: str | None = None
    for raw in text.splitlines():
        if raw.startswith("#") or raw.strip() == "":
            continue
        if raw.startswith("citations:"):
            in_citations = True
            continue
        if not in_citations:
            continue
        m = ENTRY_HEADER_RE.match(raw)
        if m:
            key = m.group(1)
            current_key = key
            entries[key] = {}
            continue
        m = FIELD_RE.match(raw)
        if m and current_key is not None:
            field, value = m.group(1), m.group(2).strip()
            entries[current_key][field] = parse_scalar(value)
            continue
        # Anything else (e.g., top-level non-comment outside citations) ends the block.
        if not raw.startswith(" "):
            in_citations = False
            current_key = None
    return entries


def _is_draft(fm: dict[str, object] | None) -> bool:
    if fm is None:
        return False
    return bool(fm.get("draft", False))


def _garden_slug_state(garden_dir: Path) -> dict[str, bool]:
    """Map slug -> is_draft for every garden subdirectory with an index.md."""
    state: dict[str, bool] = {}
    if not garden_dir.is_dir():
        return state
    for d in sorted(garden_dir.iterdir()):
        if not d.is_dir():
            continue
        index = d / "index.md"
        if not index.exists():
            continue
        fm = parse_frontmatter(index.read_text(encoding="utf-8"))
        state[d.name] = _is_draft(fm)
    return state


def lint_citations(citations_yaml: Path, garden_dir: Path) -> list[str]:
    """Return list of error strings. Empty list = all good."""
    errors: list[str] = []
    if not citations_yaml.exists():
        return [f"{citations_yaml}: file not found"]

    entries = parse_citations_yaml(citations_yaml.read_text(encoding="utf-8"))
    slug_state = _garden_slug_state(garden_dir)
    current_year = date.today().year

    for key, entry in entries.items():
        prefix = f"citations.{key}"

        if not KEY_RE.match(key):
            errors.append(f"{prefix}: key must match ^[a-z0-9][a-z0-9-]*$ (got {key!r})")
            # continue validating fields anyway — surface as many errors as possible

        unknown = set(entry.keys()) - ALLOWED_FIELDS
        for u in sorted(unknown):
            errors.append(f"{prefix}: unknown field {u!r}")

        for required in sorted(REQUIRED_FIELDS):
            if required not in entry:
                errors.append(f"{prefix}: missing required field {required!r}")

        authors = entry.get("authors")
        if authors is not None:
            if not isinstance(authors, list) or len(authors) == 0:
                errors.append(f"{prefix}: authors must be a non-empty list of strings")
            else:
                for a in authors:
                    if not isinstance(a, str) or a.strip() == "":
                        errors.append(f"{prefix}: authors contains empty/non-string entry")
                        break

        year = entry.get("year")
        if year is not None:
            if not isinstance(year, int) or isinstance(year, bool):
                errors.append(f"{prefix}: year must be an integer (got {year!r})")
            elif year < 1500 or year > current_year + 2:
                errors.append(
                    f"{prefix}: year {year} out of allowed range [1500, {current_year + 2}]"
                )

        for str_field in ("title", "venue"):
            v = entry.get(str_field)
            if v is not None and (not isinstance(v, str) or v.strip() == ""):
                errors.append(f"{prefix}: {str_field} must be a non-empty string")

        url = entry.get("url")
        if url:
            if not isinstance(url, str) or not (
                url.startswith("http://") or url.startswith("https://")
            ):
                errors.append(f"{prefix}: url must start with http:// or https:// (got {url!r})")

        notes_ref = entry.get("notes_ref")
        if isinstance(notes_ref, str) and notes_ref.strip() != "":
            if notes_ref not in slug_state:
                errors.append(
                    f"{prefix}: notes_ref {notes_ref!r} does not resolve to a garden note"
                )
            elif slug_state[notes_ref]:
                errors.append(
                    f"{prefix}: notes_ref {notes_ref!r} resolves to a draft garden note"
                )

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    citations_yaml = repo_root / "data" / "citations.yaml"
    garden_dir = repo_root / "content" / "garden"

    errors = lint_citations(citations_yaml, garden_dir)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} citation issue(s).", file=sys.stderr)
        return 1
    print("OK — citations.yaml validates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
