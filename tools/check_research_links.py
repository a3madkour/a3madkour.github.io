#!/usr/bin/env python3
"""Research cross-reference linter.

Validates that:
  - A theme's garden_topic_ref (if set) resolves to a non-draft garden note
    that has topic_map declared.
  - A question's theme resolves to an existing theme.
  - A question's parent_question (if set) resolves to an existing question
    in the same theme.
  - Every entry in a question's supporting_notes resolves to a non-draft
    garden note.
  - Every entry in a question's related_essays resolves to a non-draft
    essay page.

Exits 0 on success, 1 on any unresolved reference. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


def _load_slug_map(root: Path) -> dict[str, dict]:
    """slug -> frontmatter dict, for direct children of root that have index.md."""
    out: dict[str, dict] = {}
    if not root.is_dir():
        return out
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        md = d / "index.md"
        if not md.exists():
            continue
        fm = parse_frontmatter(md.read_text()) or {}
        out[d.name] = fm
    return out


def lint_research_links(
    themes_dir: Path,
    questions_dir: Path,
    garden_dir: Path,
    essays_dir: Path,
) -> list[str]:
    errors: list[str] = []

    themes = _load_slug_map(themes_dir)
    questions = _load_slug_map(questions_dir)
    garden = _load_slug_map(garden_dir)
    essays = _load_slug_map(essays_dir)

    # Themes: garden_topic_ref must resolve to a non-draft garden note with topic_map.
    for slug, fm in themes.items():
        ref = fm.get("garden_topic_ref")
        if not ref:
            continue
        if ref not in garden:
            errors.append(
                f"themes/{slug}: garden_topic_ref='{ref}' does not resolve to a garden note"
            )
            continue
        gfm = garden[ref]
        if gfm.get("draft"):
            errors.append(
                f"themes/{slug}: garden_topic_ref='{ref}' resolves to a draft note"
            )
        if not gfm.get("topic_map"):
            errors.append(
                f"themes/{slug}: garden_topic_ref='{ref}' resolves to a note without topic_map"
            )

    # Questions: theme + parent_question + supporting_notes + related_essays.
    for slug, fm in questions.items():
        theme_slug = fm.get("theme")
        if theme_slug and theme_slug not in themes:
            errors.append(
                f"questions/{slug}: theme='{theme_slug}' does not resolve to an existing theme"
            )

        parent = fm.get("parent_question")
        if parent:
            if parent not in questions:
                errors.append(
                    f"questions/{slug}: parent_question='{parent}' does not resolve"
                )
            else:
                parent_theme = questions[parent].get("theme")
                if parent_theme != theme_slug:
                    errors.append(
                        f"questions/{slug}: parent_question='{parent}' is in theme "
                        f"'{parent_theme}', not '{theme_slug}'"
                    )

        for target in fm.get("supporting_notes") or []:
            if target not in garden:
                errors.append(
                    f"questions/{slug}: supporting_notes entry '{target}' "
                    f"does not resolve to a garden note"
                )
            elif garden[target].get("draft"):
                errors.append(
                    f"questions/{slug}: supporting_notes entry '{target}' resolves to a draft"
                )

        for target in fm.get("related_essays") or []:
            if target not in essays:
                errors.append(
                    f"questions/{slug}: related_essays entry '{target}' "
                    f"does not resolve to an essay"
                )
            elif essays[target].get("draft"):
                errors.append(
                    f"questions/{slug}: related_essays entry '{target}' resolves to a draft"
                )

    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    themes_dir = repo_root / "content" / "research" / "themes"
    questions_dir = repo_root / "content" / "research" / "questions"
    garden_dir = repo_root / "content" / "garden"
    essays_dir = repo_root / "content" / "essays"
    errors = lint_research_links(themes_dir, questions_dir, garden_dir, essays_dir)
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
        print(f"\n{len(errors)} broken reference(s).", file=sys.stderr)
    if rc == 0:
        n_themes = len([d for d in themes_dir.iterdir() if d.is_dir() and not d.name.startswith("_")])
        n_questions = len(
            [d for d in questions_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
        )
        print(f"OK — verified {n_themes} theme(s), {n_questions} question(s).")
    return rc


if __name__ == "__main__":
    sys.exit(main())
