#!/usr/bin/env python3
"""Research fixture frontmatter linter.

Validates theme and question frontmatter contracts per spec §3.1
(2026-05-11 research surface slice). Imports parse_frontmatter from
check_fixtures so all linters share one YAML parser.

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


STATUSES = {"active", "dormant", "answered"}
OUTPUT_KINDS = {"paper", "talk", "code"}

THEME_REQUIRED = {"title", "status", "tags", "last_modified", "description", "weight"}
THEME_OPTIONAL = {"garden_topic_ref", "summary"}
THEME_FORBIDDEN = {"parent_question", "theme"}

QUESTION_REQUIRED = {"title", "theme", "status", "last_modified", "description"}
QUESTION_OPTIONAL = {
    "parent_question", "started", "tags",
    "supporting_notes", "related_essays", "outputs", "weight",
}


def lint_theme(theme_dir: Path) -> list[str]:
    """Return list of error strings for one theme dir."""
    errors: list[str] = []
    md = theme_dir / "index.md"
    if not md.exists():
        return [f"{theme_dir}: no index.md"]
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return [f"{md}: no frontmatter"]

    for field in sorted(THEME_REQUIRED - fm.keys()):
        errors.append(f"{md}: missing required field '{field}'")

    for field in sorted(THEME_FORBIDDEN & fm.keys()):
        errors.append(f"{md}: forbidden field '{field}' on theme")

    allowed = THEME_REQUIRED | THEME_OPTIONAL
    for field in sorted(fm.keys() - allowed):
        errors.append(f"{md}: unknown field '{field}'")

    status = fm.get("status")
    if status and status not in STATUSES:
        errors.append(f"{md}: status='{status}' not in {sorted(STATUSES)}")

    weight = fm.get("weight")
    if weight is not None and not isinstance(weight, int):
        errors.append(f"{md}: weight must be an integer, got {type(weight).__name__}")

    tags = fm.get("tags")
    if tags is not None and not isinstance(tags, list):
        errors.append(f"{md}: tags must be a list")
    elif isinstance(tags, list):
        for i, t in enumerate(tags):
            if not isinstance(t, str):
                errors.append(f"{md}: tags[{i}] must be a string")

    return errors


def lint_question(question_dir: Path) -> list[str]:
    """Return list of error strings for one question dir."""
    errors: list[str] = []
    md = question_dir / "index.md"
    if not md.exists():
        return [f"{question_dir}: no index.md"]
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return [f"{md}: no frontmatter"]

    for field in sorted(QUESTION_REQUIRED - fm.keys()):
        errors.append(f"{md}: missing required field '{field}'")

    allowed = QUESTION_REQUIRED | QUESTION_OPTIONAL
    for field in sorted(fm.keys() - allowed):
        errors.append(f"{md}: unknown field '{field}'")

    status = fm.get("status")
    if status and status not in STATUSES:
        errors.append(f"{md}: status='{status}' not in {sorted(STATUSES)}")

    outputs = fm.get("outputs")
    if outputs is not None:
        if not isinstance(outputs, list):
            errors.append(f"{md}: outputs must be a list")
        else:
            for i, o in enumerate(outputs):
                if not isinstance(o, dict):
                    errors.append(f"{md}: outputs[{i}] must be a mapping")
                    continue
                kind = o.get("kind")
                if kind not in OUTPUT_KINDS:
                    errors.append(
                        f"{md}: outputs[{i}].kind='{kind}' not in {sorted(OUTPUT_KINDS)}"
                    )
                year = o.get("year")
                if not isinstance(year, int) or not (1900 <= year <= 2100):
                    errors.append(
                        f"{md}: outputs[{i}].year must be a 4-digit int, got {year!r}"
                    )
                title = o.get("title")
                if not isinstance(title, str) or not title.strip():
                    errors.append(f"{md}: outputs[{i}].title must be non-empty string")
                url = o.get("url")
                if not isinstance(url, str) or not url.strip():
                    errors.append(f"{md}: outputs[{i}].url must be non-empty string")

    for list_field in ("tags", "supporting_notes", "related_essays"):
        val = fm.get(list_field)
        if val is not None and not isinstance(val, list):
            errors.append(f"{md}: {list_field} must be a list")

    weight = fm.get("weight")
    if weight is not None and not isinstance(weight, int):
        errors.append(f"{md}: weight must be an integer")

    return errors


def validate_unique_theme_weights(themes: list[dict]) -> list[str]:
    """Theme weights must be unique so themePaletteOrder is deterministic.

    Returns a list of error strings (empty if all weights are distinct or absent).
    """
    seen: dict = {}
    errors: list[str] = []
    for theme in themes:
        w = theme.get("weight")
        if w is None:
            continue
        if w in seen:
            errors.append(
                f"theme weight {w} duplicated: {seen[w]} and {theme['slug']}"
            )
        else:
            seen[w] = theme["slug"]
    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    themes_dir = repo_root / "content" / "research" / "themes"
    questions_dir = repo_root / "content" / "research" / "questions"

    if not themes_dir.is_dir() or not questions_dir.is_dir():
        print(
            f"error: missing {themes_dir} or {questions_dir}", file=sys.stderr
        )
        return 1

    errors: list[str] = []
    themes: list[dict] = []
    for d in sorted(themes_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        errors.extend(lint_theme(d))
        md = d / "index.md"
        if md.exists():
            fm = parse_frontmatter(md.read_text())
            if fm is not None:
                fm["slug"] = d.name
                themes.append(fm)
    errors.extend(validate_unique_theme_weights(themes))
    for d in sorted(questions_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        errors.extend(lint_question(d))

    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} problem(s).", file=sys.stderr)
        return 1

    print("All research fixtures pass linter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
