"""Shared test scaffolding for the tools/ linter unit tests (R5.4).
Test-only — never imported by a linter. Replaces the per-file TempRepo that
~21 test_check_*.py files each re-rolled."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


class TempRepo:
    """A throwaway repo root under a tempdir. Domain writers live in each test
    file as a thin subclass calling `self.write(...)`."""

    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())

    def write(self, rel: str, text: str) -> Path:
        """Write `text` to <root>/<rel>, creating parent dirs. Returns the path."""
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
