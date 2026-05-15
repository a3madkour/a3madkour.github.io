"""Library shelves linter. STUB — implemented in next task."""
from __future__ import annotations
from pathlib import Path


def lint_library_shelves(project_root: Path) -> list[str]:
    return ["NOT IMPLEMENTED"]


if __name__ == "__main__":
    import sys
    errors = lint_library_shelves(Path(__file__).resolve().parent.parent)
    for e in errors:
        print(e)
    sys.exit(1 if errors else 0)
