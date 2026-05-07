#!/usr/bin/env python3
"""Garden note fixture frontmatter linter.

Walks `content/garden/<slug>/index.md` (skips `_index.md`), validates
flavor-specific frontmatter per spec §5.1, and verifies that every
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

# --- contract ---

ALWAYS_REQUIRED = {"title", "draft", "last_modified", "growth_stage"}

GROWTH_STAGES = {"seedling", "budding", "evergreen"}
STATUSES = {"reading", "finished", "abandoned", "queued"}
SPOILER_LEVELS = {"none", "light", "heavy"}

MEDIA_TYPES = {"book", "album", "track", "game", "film", "series"}
REFERENCE_TYPES = {"paper", "video", "article", "talk"}
ALL_MEDIA_TYPES = MEDIA_TYPES | REFERENCE_TYPES

# Fields permitted on each flavor (anything else is forbidden)
CONCEPT_FIELDS = ALWAYS_REQUIRED | {"tags", "summary", "topic_map", "roam_refs", "year"}
MEDIA_FIELDS = ALWAYS_REQUIRED | {
    "media_type", "status", "creator",
    "tags", "summary", "topic_map", "roam_refs", "year",
    "original_url", "started", "finished", "spoiler_level",
}
REFERENCE_FIELDS = ALWAYS_REQUIRED | {
    "media_type", "creator",
    "tags", "summary", "topic_map", "roam_refs", "year",
    "original_url",
}

MEDIA_REQUIRED_EXTRA = {"media_type", "status", "creator"}
REFERENCE_REQUIRED_EXTRA = {"media_type", "creator"}


def derive_flavor(fm: dict[str, object]) -> str:
    media_type = fm.get("media_type")
    if not media_type:
        return "concept"
    if media_type in MEDIA_TYPES:
        return "media"
    if media_type in REFERENCE_TYPES:
        return "reference"
    return "unknown"


def lint_note(note_dir: Path) -> tuple[list[str], dict[str, object] | None]:
    """Return (errors, parsed_frontmatter_or_None) for a single note dir."""
    errors: list[str] = []
    md = note_dir / "index.md"
    if not md.exists():
        return [f"{note_dir}: no index.md"], None
    text = md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md}: no frontmatter"], None

    # Always-required fields
    for field in sorted(ALWAYS_REQUIRED - fm.keys()):
        errors.append(f"{md}: missing required field '{field}'")

    # Enum: growth_stage
    stage = fm.get("growth_stage")
    if stage and stage not in GROWTH_STAGES:
        errors.append(
            f"{md}: growth_stage='{stage}' not in {sorted(GROWTH_STAGES)}"
        )

    # Date validation: last_modified, started, finished
    for date_field in ("last_modified", "started", "finished"):
        val = fm.get(date_field)
        if val is None or val == "":
            continue
        if not isinstance(val, Date):
            errors.append(
                f"{md}: {date_field}='{val}' is not a valid YYYY-MM-DD date"
            )
            continue
        if date_field == "last_modified" and val > Date.today():
            errors.append(f"{md}: last_modified {val} is in the future")

    # Flavor-specific
    flavor = derive_flavor(fm)
    if flavor == "unknown":
        errors.append(
            f"{md}: media_type='{fm.get('media_type')}' "
            f"not in {sorted(ALL_MEDIA_TYPES)}"
        )
        return errors, fm

    if flavor == "concept":
        allowed = CONCEPT_FIELDS
    elif flavor == "media":
        allowed = MEDIA_FIELDS
        for f in sorted(MEDIA_REQUIRED_EXTRA - fm.keys()):
            errors.append(f"{md}: '{f}' is required for media notes")
    else:  # reference
        allowed = REFERENCE_FIELDS
        for f in sorted(REFERENCE_REQUIRED_EXTRA - fm.keys()):
            errors.append(f"{md}: '{f}' is required for reference notes")

    for f in sorted(set(fm.keys()) - allowed):
        errors.append(f"{md}: '{f}' not permitted on {flavor} notes")

    # Enum checks for media-only fields
    if flavor == "media":
        status = fm.get("status")
        if status and status not in STATUSES:
            errors.append(
                f"{md}: status='{status}' not in {sorted(STATUSES)}"
            )
        spl = fm.get("spoiler_level")
        if spl and spl not in SPOILER_LEVELS:
            errors.append(
                f"{md}: spoiler_level='{spl}' not in {sorted(SPOILER_LEVELS)}"
            )

    # URL scheme check
    url = fm.get("original_url")
    if url and not (str(url).startswith("http://") or str(url).startswith("https://")):
        errors.append(f"{md}: original_url must be http(s)")

    return errors, fm


def run(repo_root: Path) -> tuple[int, list[str]]:
    garden_dir = repo_root / "content" / "garden"
    errors: list[str] = []

    if not garden_dir.exists():
        return 0, []

    # Pass 1: lint each note, build the slug → frontmatter index
    notes: dict[str, dict[str, object]] = {}
    for entry in sorted(garden_dir.iterdir()):
        if not entry.is_dir():
            continue
        slug = entry.name
        if slug.startswith("_"):
            continue
        note_errors, fm = lint_note(entry)
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
