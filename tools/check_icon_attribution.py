"""Icon attribution linter. STUB — will be implemented in next task."""
from __future__ import annotations
from pathlib import Path


def lint_icon_attribution(project_root: Path) -> list[str]:
    return ["NOT IMPLEMENTED"]


if __name__ == "__main__":
    import sys
    errors = lint_icon_attribution(Path(__file__).resolve().parent.parent)
    for e in errors:
        print(e)
    sys.exit(1 if errors else 0)
