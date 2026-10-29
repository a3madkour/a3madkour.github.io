#!/usr/bin/env python3
"""Garden note fixture frontmatter linter.

Walks `content/garden/<slug>/index.md` (skips `_index.md`), validates
flavor-specific frontmatter per spec §5.1 against the `garden` entry of
data/sections.json (sections.check_fields), and verifies that every
`topic_map:` entry resolves to an existing non-draft note.

Exits 0 on all-pass, 1 on any violation. Stdlib only — imports the YAML
parser from check_fixtures so both linters share one parser.
"""
from __future__ import annotations

import sys
from datetime import date as Date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402
import sections  # noqa: E402

# --- contract ---
#
# Field sets, enums, types and the concept/media/reference flavors (variants
# on `media_type`) live in data/sections.json (spec 2026-10-20). What stays
# here: the future-date and URL-scheme rules and topic_map resolution.


def derive_flavor(fm: dict[str, object], registry: dict | None = None) -> str:
    """'concept' | 'media' | 'reference', or 'unknown' for an unlisted media_type."""
    case = sections.case_of(fm, "garden", registry)
    if case is None:
        return "unknown"
    # The media cases are one per library shelf (media-book, media-listening, …).
    return "media" if case.startswith("media-") else case


def lint_note(note_dir: Path, registry: dict | None = None) -> tuple[list[str], dict[str, object] | None]:
    """Return (errors, parsed_frontmatter_or_None) for a single note dir."""
    md = note_dir / "index.md"
    if not md.exists():
        return [f"{note_dir}: no index.md"], None
    text = md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md}: no frontmatter"], None

    errors = sections.check_fields(fm, "garden", md, registry=registry)

    # The registry's `date` accepts any ISO-date-prefixed string (stream
    # datetimes). Garden dates must be bare dates, which parse_scalar turns
    # into date objects; flag the prefixed strings the registry let through.
    for date_field in ("last_modified", "started", "finished"):
        val = fm.get(date_field)
        if isinstance(val, str) and sections.DATE_PREFIX_RE.match(val):
            errors.append(f"{md}: {date_field}='{val}' is not a valid YYYY-MM-DD date")

    last_modified = fm.get("last_modified")
    if isinstance(last_modified, Date) and last_modified > Date.today():
        errors.append(f"{md}: last_modified {last_modified} is in the future")

    # An unlisted media_type leaves the flavor — and so the legal field set —
    # unknown; the registry has already reported it. Stop, as before.
    if derive_flavor(fm, registry) == "unknown":
        return errors, fm

    # URL scheme check
    url = fm.get("original_url")
    if url and not (str(url).startswith("http://") or str(url).startswith("https://")):
        errors.append(f"{md}: original_url must be http(s)")

    return errors, fm


def run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]:
    garden_dir = repo_root / "content" / "garden"
    errors: list[str] = []

    if not garden_dir.exists():
        return 0, []
    try:
        reg = registry if registry is not None else sections.default_registry()
    except sections.SectionsError as e:
        return 1, [str(e)]

    # Pass 1: lint each note, build the slug → frontmatter index
    notes: dict[str, dict[str, object]] = {}
    for entry in sorted(garden_dir.iterdir()):
        if not entry.is_dir():
            continue
        slug = entry.name
        if slug.startswith("_"):
            continue
        # Skip section directories (have _index.md but no index.md) — e.g.,
        # /history/ is a Hugo section, not a note. The note linter expects
        # a per-slug index.md and would false-fail on these.
        if (entry / "_index.md").is_file() and not (entry / "index.md").is_file():
            continue
        note_errors, fm = lint_note(entry, reg)
        errors.extend(note_errors)
        if fm is not None:
            notes[slug] = fm

    # Pass 2: validate every topic_map entry resolves to an existing
    # non-draft note in the index
    for slug, fm in notes.items():
        topic_map = fm.get("topic_map")
        if not isinstance(topic_map, list):
            continue
        for i, entry_slug in enumerate(topic_map):
            target = notes.get(str(entry_slug))
            owner_md = garden_dir / slug / "index.md"
            if target is None:
                errors.append(
                    f"{owner_md}: topic_map[{i}]='{entry_slug}' "
                    f"does not resolve to an existing note"
                )
                continue
            if target.get("draft") is True:
                errors.append(
                    f"{owner_md}: topic_map[{i}]='{entry_slug}' "
                    f"is a draft; drafts cannot be in published topic maps"
                )

    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        print("Garden fixture lint failures:")
        for e in errors:
            print(f"  {e}")
    else:
        print("All garden fixtures pass linter.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
