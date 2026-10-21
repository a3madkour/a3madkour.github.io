#!/usr/bin/env python3
"""Library fixture frontmatter linter.

Validates `data/{reading,listening,playing,watching}.yaml` shape per
docs/superpowers/specs/2026-05-12-library-section-design.md §3, each item
against its shelf's `library/<shelf>` entry in data/sections.json
(sections.check_fields; spec 2026-10-20 §5.1).

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_scalar  # noqa: E402
import sections  # noqa: E402


ITEM_START_RE = re.compile(r"^  - ([a-zA-Z_]+):\s*(.*)$")
ITEM_FIELD_RE = re.compile(r"^    ([a-zA-Z_]+):\s*(.*)$")
NESTED_FIELD_RE = re.compile(r"^      ([a-zA-Z_]+):\s*(.*)$")
# Only these item-level fields open a nested mapping when their value is empty.
# All other empty-value item fields parse to None.
NESTED_BLOCK_FIELDS = {"extras"}


def _scalar(value: str) -> object:
    """Extend parse_scalar with null → None handling."""
    if value == "null":
        return None
    return parse_scalar(value)


# NOTE (R5.4 item 3): this parses data/<medium>.yaml (a list-of-dicts data
# file), NOT `---` frontmatter — a genuinely different shape, so it stays
# separate from check_fixtures.parse_frontmatter.
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

        m_nested = NESTED_FIELD_RE.match(raw)
        if m_nested and nested is not None:
            field, value = m_nested.group(1), m_nested.group(2).strip()
            nested[field] = _scalar(value)
            continue

        m_field = ITEM_FIELD_RE.match(raw)
        if m_field and current is not None:
            field, value = m_field.group(1), m_field.group(2).strip()
            if value == "" and field in NESTED_BLOCK_FIELDS:
                # Open a nested mapping (e.g., extras: <newline> 6-space fields).
                if nested_key is not None and nested is not None:
                    current[nested_key] = nested
                nested_key = field
                nested = {}
            else:
                if nested_key is not None and nested is not None:
                    current[nested_key] = nested
                    nested_key = None
                    nested = None
                current[field] = _scalar(value) if value else None
            continue

    if current is not None:
        if nested_key is not None and nested is not None:
            current[nested_key] = nested
        items.append(current)

    return items


# --- contract ---
#
# Per-shelf field sets, media/status enums, types and the per-media_type
# `extras` sub-keys live in data/sections.json under library/<shelf>
# (store: "data"; spec 2026-10-20 §4). What stays here: the ISBN / slug / date
# / cover-key format rules, slug uniqueness, the finished-date and episode
# cross-field rules, the progress range, and the active-items warning.

ISBN_RE = re.compile(r"^\d{10}$|^\d{13}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ACTIVE_STATUSES = {"reading", "listening", "playing", "watching"}


def library_files(registry: dict | None = None) -> list[str]:
    """`<shelf>.yaml` for every library/<shelf> section in the registry."""
    return sorted(f"{name.split('/', 1)[1]}.yaml"
                  for name in sections.section_names(registry)
                  if name.startswith("library/"))


def _validate_extras_formats(extras: dict, errors: list, ctx: str) -> None:
    """Format rules for cover keys. Type and per-media allowance are the
    registry's; each rule here fires only on a value of the declared type."""
    for key, value in extras.items():
        if key == "isbn":
            if isinstance(value, str) and not ISBN_RE.match(value):
                errors.append(f"{ctx}: extras.isbn must be 10 or 13 digits, got {value!r}")
        elif key in {"igdb_id", "tmdb_id"}:
            if isinstance(value, int) and not isinstance(value, bool) and value <= 0:
                errors.append(f"{ctx}: extras.{key} must be a positive integer, got {value!r}")
        elif key == "musicbrainz_release_group":
            if isinstance(value, str) and not value:
                errors.append(f"{ctx}: extras.musicbrainz_release_group must be a non-empty string")
        elif key == "cover_url":
            if isinstance(value, str):
                parsed = urllib.parse.urlparse(value)
                if not parsed.scheme or not parsed.netloc:
                    errors.append(f"{ctx}: extras.cover_url must be an absolute URL, got {value!r}")
        elif key == "cover_file":
            if isinstance(value, str) and ("/" in value or ".." in value or not value):
                errors.append(f"{ctx}: extras.cover_file must be a relative filename without '/' or '..', got {value!r}")


def lint_yaml_file(file_name: str, text: str,
                   registry: dict | None = None) -> tuple[list[str], list[str]]:
    """Validate one library yaml file.

    Returns (errors, warnings). Errors fail CI; warnings print to stderr only.
    """
    errors: list[str] = []
    warnings: list[str] = []
    section = "library/" + file_name.removesuffix(".yaml")
    if file_name not in library_files(registry):
        return [f"{file_name}: unknown library file"], []

    items = parse_library_yaml(text)

    if not items:
        return [f"{file_name}: no items parsed"], []

    seen_slugs: set[str] = set()
    active_count = 0

    for idx, item in enumerate(items):
        prefix = f"{file_name}[{idx}]"

        errors.extend(sections.check_fields(item, section, prefix, registry=registry))

        slug = item.get("slug")
        if isinstance(slug, str):
            if not SLUG_RE.match(slug):
                errors.append(f"{prefix}: slug '{slug}' not kebab-case")
            if slug in seen_slugs:
                errors.append(f"{prefix}: duplicate slug '{slug}'")
            seen_slugs.add(slug)

        # The registry's `date` accepts any ISO-date-prefixed string (stream
        # datetimes). Library dates are bare dates, so the full match stays
        # here, firing only where the registry's prefix check passed.
        for date_field in ("started", "finished", "last_modified"):
            v = item.get(date_field)
            if isinstance(v, str) and sections.DATE_PREFIX_RE.match(v) and not DATE_RE.match(v):
                errors.append(f"{prefix}: {date_field} not YYYY-MM-DD ('{v}')")

        status = item.get("status")
        if status in ACTIVE_STATUSES:
            active_count += 1

        if status == "finished" and item.get("finished") in (None, ""):
            errors.append(f"{prefix}: finished date required when status='finished'")

        url = item.get("canonical_url")
        if isinstance(url, str) and not url.startswith("https://"):
            errors.append(f"{prefix}: canonical_url must be https:// or null")

        tags = item.get("tags")
        if isinstance(tags, list):
            for t in tags:
                if isinstance(t, str) and not SLUG_RE.match(t):
                    errors.append(f"{prefix}: tag '{t}' not slug-shaped")

        extras = item.get("extras")
        if isinstance(extras, dict):
            pct = extras.get("progress_pct")
            if isinstance(pct, int) and not isinstance(pct, bool) and not 0 <= pct <= 100:
                errors.append(f"{prefix}: progress_pct must be int 0..100, got {pct}")
            ce = extras.get("current_episode")
            ec = extras.get("episode_count")
            if isinstance(ce, int) and isinstance(ec, int) and ce > ec:
                errors.append(f"{prefix}: current_episode ({ce}) > episode_count ({ec})")
            _validate_extras_formats(extras, errors, prefix)

    if active_count > 3:
        warnings.append(f"{file_name}: {active_count} active items, expected ≤3 in currently-active highlight")

    return errors, warnings


def run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]:
    try:
        reg = registry if registry is not None else sections.default_registry()
    except sections.SectionsError as e:
        return 1, [str(e)]
    all_errs: list[str] = []
    all_warns: list[str] = []
    data_dir = repo_root / "data"
    for fname in library_files(reg):
        path = data_dir / fname
        if not path.exists():
            continue
        errs, warns = lint_yaml_file(fname, path.read_text(), reg)
        all_errs.extend(errs)
        all_warns.extend(warns)
    for w in all_warns:
        print(f"warning: {w}", file=sys.stderr)
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
