#!/usr/bin/env python3
"""Research fixture frontmatter linter.

Validates theme and question frontmatter contracts per spec §3.1
(2026-05-11 research surface slice). Field sets, enums and types come from
data/sections.json via sections.check_fields (spec 2026-10-20 §5.1); the
structured `outputs` shape and theme-weight uniqueness stay here. Imports
parse_frontmatter from check_fixtures so all linters share one YAML parser.

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402
import sections  # noqa: E402


OUTPUT_KINDS = {"paper", "talk", "code"}


def _lint(entry_dir: Path, section: str, registry: dict | None) -> tuple[Path, dict | None, list[str]]:
    """Shared front half: locate, parse, and run the registry field checks."""
    md = entry_dir / "index.md"
    if not md.exists():
        return md, None, [f"{entry_dir}: no index.md"]
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return md, None, [f"{md}: no frontmatter"]
    return md, fm, sections.check_fields(fm, section, md, registry=registry)


def lint_theme(theme_dir: Path, registry: dict | None = None) -> list[str]:
    """Return list of error strings for one theme dir."""
    _md, _fm, errors = _lint(theme_dir, "research/themes", registry)
    return errors


def lint_question(question_dir: Path, registry: dict | None = None) -> list[str]:
    """Return list of error strings for one question dir."""
    md, fm, errors = _lint(question_dir, "research/questions", registry)
    if fm is None:
        return errors

    # `outputs` is a `structured` field: the registry checks presence only and
    # its inner shape stays here (spec §4).
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

    return errors


def validate_unique_theme_weights(themes: list[dict]) -> list[str]:
    """Theme weights must be unique so themePaletteOrder is deterministic.

    Returns a list of error strings (empty if all weights are distinct or absent).
    """
    seen: dict[int, str] = {}
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


def run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]:
    try:
        reg = registry if registry is not None else sections.default_registry()
    except sections.SectionsError as e:
        return 1, [str(e)]
    themes_dir = repo_root / "content" / "research" / "themes"
    questions_dir = repo_root / "content" / "research" / "questions"
    errors: list[str] = []
    themes: list[dict] = []
    for d in sorted(themes_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        errors.extend(lint_theme(d, reg))
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
        errors.extend(lint_question(d, reg))
    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    themes_dir = repo_root / "content" / "research" / "themes"
    questions_dir = repo_root / "content" / "research" / "questions"
    if not themes_dir.is_dir() or not questions_dir.is_dir():
        print(
            f"error: missing {themes_dir} or {questions_dir}", file=sys.stderr
        )
        return 1
    rc, errors = run(repo_root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} problem(s).", file=sys.stderr)
    if rc == 0:
        print("All research fixtures pass linter.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
