#!/usr/bin/env python3
"""Library fixture frontmatter linter.

Validates `data/{reading,listening,playing,watching}.yaml` shape per
docs/superpowers/specs/2026-05-12-library-section-design.md §3.

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from datetime import date as Date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_scalar  # noqa: E402


ITEM_START_RE = re.compile(r"^  - ([a-zA-Z_]+):\s*(.*)$")
ITEM_FIELD_RE = re.compile(r"^    ([a-zA-Z_]+):\s*(.*)$")
NESTED_HEADER_RE = re.compile(r"^    ([a-zA-Z_]+):\s*$")
NESTED_FIELD_RE = re.compile(r"^      ([a-zA-Z_]+):\s*(.*)$")


def _scalar(value: str) -> object:
    """Extend parse_scalar with null → None handling."""
    if value == "null":
        return None
    return parse_scalar(value)


def parse_library_yaml(text: str) -> list[dict[str, object]]:
    """Parse a library data yaml file into a list of item dicts.

    Format:
        items:
          - slug: foo
            title: Bar
            tags: [a, b]
            extras:
              progress_pct: 50

    `null`, ints, floats, bools, [a, b] inline arrays handled via parse_scalar.
    """
    items: list[dict[str, object]] = []
    in_items = False
    current: dict[str, object] | None = None
    nested_key: str | None = None
    nested: dict[str, object] | None = None

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw.startswith("items:"):
            in_items = True
            continue
        if not in_items:
            continue

        m = ITEM_START_RE.match(raw)
        if m:
            if current is not None:
                if nested_key is not None and nested is not None:
                    current[nested_key] = nested
                items.append(current)
            current = {}
            nested_key = None
            nested = None
            field, value = m.group(1), m.group(2).strip()
            current[field] = _scalar(value)
            continue

        m_nested_hdr = NESTED_HEADER_RE.match(raw)
        if m_nested_hdr and current is not None:
            if nested_key is not None and nested is not None:
                current[nested_key] = nested
            nested_key = m_nested_hdr.group(1)
            nested = {}
            continue

        m_nested = NESTED_FIELD_RE.match(raw)
        if m_nested and nested is not None:
            field, value = m_nested.group(1), m_nested.group(2).strip()
            nested[field] = _scalar(value)
            continue

        m_field = ITEM_FIELD_RE.match(raw)
        if m_field and current is not None:
            if nested_key is not None and nested is not None:
                current[nested_key] = nested
                nested_key = None
                nested = None
            field, value = m_field.group(1), m_field.group(2).strip()
            current[field] = _scalar(value)
            continue

    if current is not None:
        if nested_key is not None and nested is not None:
            current[nested_key] = nested
        items.append(current)

    return items


ALLOWED_MEDIA_TYPES = {
    "reading.yaml":   {"book"},
    "listening.yaml": {"album", "track"},
    "playing.yaml":   {"game"},
    "watching.yaml":  {"film", "series"},
}

ALLOWED_STATUSES = {
    "reading.yaml":   {"finished", "reading", "queued", "abandoned"},
    "listening.yaml": {"finished", "listening", "queued", "dropped"},
    "playing.yaml":   {"finished", "100pct", "playing", "queued", "dropped"},
    "watching.yaml":  {"finished", "watching", "queued", "dropped"},
}

ALLOWED_EXTRAS = {
    "book":   {"progress_pct", "progress_label"},
    "album":  set(),
    "track":  set(),
    "game":   {"hours_played", "platform"},
    "film":   {"runtime_min"},
    "series": {"episode_count", "current_episode", "current_season"},
}

REQUIRED_FIELDS = {"slug", "title", "creator", "year", "media_type", "status", "last_modified", "tags"}
ALLOWED_FIELDS = REQUIRED_FIELDS | {
    "started", "finished", "spoiler_level", "cite_key",
    "canonical_url", "note_slug", "preview", "extras",
}
SPOILER_LEVELS = {"none", "light", "heavy"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ACTIVE_STATUSES = {"reading", "listening", "playing", "watching"}


def _check_date(label: str, value: object) -> str | None:
    if value is None:
        return None
    # parse_scalar converts valid YYYY-MM-DD strings to datetime.date objects
    if isinstance(value, Date):
        return None
    if not isinstance(value, str) or not DATE_RE.match(value):
        return f"{label}: not YYYY-MM-DD ('{value}')"
    return None


def lint_yaml_file(file_name: str, text: str) -> list[str]:
    errors: list[str] = []
    if file_name not in ALLOWED_MEDIA_TYPES:
        return [f"{file_name}: unknown library file"]

    media_allow = ALLOWED_MEDIA_TYPES[file_name]
    status_allow = ALLOWED_STATUSES[file_name]
    items = parse_library_yaml(text)

    if not items:
        return [f"{file_name}: no items parsed"]

    seen_slugs: set[str] = set()
    active_count = 0

    for idx, item in enumerate(items):
        prefix = f"{file_name}[{idx}]"

        # Required fields
        missing = REQUIRED_FIELDS - set(item.keys())
        for f in sorted(missing):
            errors.append(f"{prefix}: missing required field '{f}'")

        # Unknown fields
        unknown = set(item.keys()) - ALLOWED_FIELDS
        for f in sorted(unknown):
            errors.append(f"{prefix}: unknown field '{f}'")

        slug = item.get("slug")
        if isinstance(slug, str):
            if not SLUG_RE.match(slug):
                errors.append(f"{prefix}: slug '{slug}' not kebab-case")
            if slug in seen_slugs:
                errors.append(f"{prefix}: duplicate slug '{slug}'")
            seen_slugs.add(slug)

        year = item.get("year")
        if year is not None and not isinstance(year, int):
            errors.append(f"{prefix}: year must be int, got {type(year).__name__}")

        mt = item.get("media_type")
        if mt is not None and mt not in media_allow:
            errors.append(f"{prefix}: media_type='{mt}' not allowed in {file_name} (allowed: {sorted(media_allow)})")

        status = item.get("status")
        if status is not None and status not in status_allow:
            errors.append(f"{prefix}: status='{status}' not allowed in {file_name} (allowed: {sorted(status_allow)})")
        if status in ACTIVE_STATUSES:
            active_count += 1

        for date_field in ("started", "finished", "last_modified"):
            err = _check_date(f"{prefix}: {date_field}", item.get(date_field))
            if err:
                errors.append(err.replace("not YYYY-MM-DD", f"{date_field} not YYYY-MM-DD"))

        if status == "finished" and item.get("finished") in (None, ""):
            errors.append(f"{prefix}: finished date required when status='finished'")

        sl = item.get("spoiler_level")
        if sl is not None and sl not in SPOILER_LEVELS:
            errors.append(f"{prefix}: spoiler_level='{sl}' not in {sorted(SPOILER_LEVELS)}")

        url = item.get("canonical_url")
        if url is not None and not (isinstance(url, str) and url.startswith("https://")):
            errors.append(f"{prefix}: canonical_url must be https:// or null")

        tags = item.get("tags")
        if tags is None or not isinstance(tags, list):
            errors.append(f"{prefix}: tags must be a list (may be empty)")
        else:
            for t in tags:
                if not isinstance(t, str) or not SLUG_RE.match(t):
                    errors.append(f"{prefix}: tag '{t}' not slug-shaped")

        extras = item.get("extras")
        if extras is not None:
            if not isinstance(extras, dict):
                errors.append(f"{prefix}: extras must be a mapping")
            elif isinstance(mt, str):
                allowed = ALLOWED_EXTRAS.get(mt, set())
                for k in extras:
                    if k not in allowed:
                        errors.append(f"{prefix}: extras.{k} not allowed for media_type '{mt}'")
                if "progress_pct" in extras:
                    pct = extras["progress_pct"]
                    if not isinstance(pct, int) or not 0 <= pct <= 100:
                        errors.append(f"{prefix}: progress_pct must be int 0..100, got {pct}")
                if "current_episode" in extras and "episode_count" in extras:
                    ce = extras.get("current_episode")
                    ec = extras.get("episode_count")
                    if isinstance(ce, int) and isinstance(ec, int) and ce > ec:
                        errors.append(f"{prefix}: current_episode ({ce}) > episode_count ({ec})")

    if active_count > 3:
        errors.append(f"{file_name}: warning — {active_count} active items, expected ≤3 in currently-active highlight")

    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    data_dir = repo_root / "data"
    for fname in sorted(ALLOWED_MEDIA_TYPES.keys()):
        path = data_dir / fname
        if not path.exists():
            continue
        all_errs.extend(lint_yaml_file(fname, path.read_text()))
    return (1 if all_errs else 0), all_errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_library_fixtures: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
