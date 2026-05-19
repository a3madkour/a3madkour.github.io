#!/usr/bin/env python3
"""Synced-poetry marker linter.

For every content/works/poetry/<slug>/index.md whose body contains at least
one (non-escaped) [mm:ss] marker, validate the synced-poetry contract
(spec docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md §8):

  1. Marker shape  — \\[\\d{1,2}:\\d{2}(?:\\.\\d{1,2})?\\]; minutes 0-99,
                      seconds 00-59 (2 digits), fractional 1-2 digits.
  2. Placement     — every marker at line start (after optional leading
                      whitespace) OR immediately preceded by whitespace.
  3. Audio URL     — when audio_url set: relative → file exists in the page
                      bundle; absolute → ^https?://[^\\s]+$.
  4. Escape        — backslash-escaped \\[mm:ss] is literal text; excluded
                      from the marker counter and from shape checks.
  5. Monotonic     — non-decreasing marker order. WARNING only (rc stays 0).
  6. Non-empty     — at least one content (non-blank, non-marker-only) line.

Exits 0 on all-pass (warnings do not fail), 1 on any error. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)

# Escaped marker first (consumed → never a real marker).
ESCAPED_RE = re.compile(r"\\\[\d{1,2}:\d{2}(?:\.\d{1,2})?\]")
# Loose marker token: anything bracket-wrapped that looks marker-ish, so we
# can shape-check it precisely and report the offending text.
LOOSE_RE = re.compile(r"\[\d{1,2}:\d{1,3}(?:\.\d{1,3})?\]")
STRICT_RE = re.compile(r"^\[(\d{1,2}):(\d{2})(?:\.(\d{1,2}))?\]$")
ABS_URL_RE = re.compile(r"^https?://[^\s]+$")

_ESC_SENTINEL = "\x00ESC\x00"


def _split_body(text: str) -> str:
    m = FRONTMATTER_RE.match(text)
    return text[m.end():] if m else text


def _mask_escaped(body: str) -> str:
    """Replace every \\[mm:ss] with a bracket-free sentinel run so it is
    neither counted nor shape-checked."""
    return ESCAPED_RE.sub(_ESC_SENTINEL, body)


def _marker_seconds(mm: str, ss: str, frac: str | None) -> float:
    total = int(mm) * 60 + int(ss)
    if frac:
        total += int(frac) / (10 ** len(frac))
    return float(total)


def lint_file(md: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for one poetry index.md.

    A poem with no real markers returns ([], []) — not a synced poem.
    """
    errors: list[str] = []
    warnings: list[str] = []

    text = md.read_text()
    fm = parse_frontmatter(text) or {}
    body = _split_body(text)
    masked = _mask_escaped(body)

    loose = LOOSE_RE.findall(masked)
    if not loose:
        return [], []  # not a synced poem

    # (1) marker shape
    seconds: list[float] = []
    for tok in loose:
        m = STRICT_RE.match(tok)
        if not m:
            errors.append(
                f"{md}: malformed marker {tok} "
                f"(want [mm:ss] or [mm:ss.f]; mm 0-99, ss 2-digit)"
            )
            continue
        mm, ss, frac = m.group(1), m.group(2), m.group(3)
        if int(ss) > 59:
            errors.append(f"{md}: marker {tok} seconds out of range (00-59)")
            continue
        seconds.append(_marker_seconds(mm, ss, frac))

    # (2) placement — non-space immediately before a marker bracket
    for mobj in LOOSE_RE.finditer(masked):
        start = mobj.start()
        if start > 0 and not masked[start - 1].isspace():
            errors.append(
                f"{md}: marker {mobj.group(0)} placement — must be at line "
                f"start or preceded by whitespace (no embedded text[mm:ss])"
            )

    # (3) audio_url validity
    audio_url = fm.get("audio_url")
    if isinstance(audio_url, str) and audio_url.strip():
        au = audio_url.strip()
        if au.startswith(("http://", "https://")):
            if not ABS_URL_RE.match(au):
                errors.append(f"{md}: audio_url '{au}' is not a valid http(s) URL")
        elif "://" in au:
            errors.append(
                f"{md}: audio_url '{au}' — only http(s) absolute URLs or "
                f"bundle-relative paths are allowed"
            )
        else:
            if not (md.parent / au).is_file():
                errors.append(
                    f"{md}: audio_url '{au}' — relative file not found in "
                    f"page bundle ({md.parent / au})"
                )

    # (6) non-empty: at least one line with text after marker stripping
    has_content = False
    for line in masked.splitlines():
        stripped = LOOSE_RE.sub("", line).strip()
        if stripped:
            has_content = True
            break
    if not has_content:
        errors.append(f"{md}: synced poem has no content (markers only / empty)")

    # (5) monotonic — warning only
    for a, b in zip(seconds, seconds[1:]):
        if b < a:
            warnings.append(
                f"{md}: non-monotonic markers ({a:g}s then {b:g}s) — runtime "
                f"plays in marker order; visual jumps possible"
            )
            break

    # spec §3 edge-case warnings (informational; rc stays 0) ---------------
    untimed = 0
    first_untimed = ""
    eol_marker = 0
    first_eol = ""
    for line in masked.splitlines():
        content = LOOSE_RE.sub("", line).strip()
        matches = list(LOOSE_RE.finditer(line))
        if content:
            if not LOOSE_RE.match(line.lstrip()):
                untimed += 1
                if not first_untimed:
                    first_untimed = content[:40]
        if matches:
            last = matches[-1]
            if line[last.end():].strip() == "":
                eol_marker += 1
                if not first_eol:
                    first_eol = last.group(0)
    if untimed:
        warnings.append(
            f"{md}: {untimed} untimed line(s) in a synced poem (each "
            f"inherits prev_t + 0.5s); first: '{first_untimed}'"
        )
    if eol_marker:
        warnings.append(
            f"{md}: {eol_marker} marker(s) at end of line with no following "
            f"word (ignored at runtime); first: {first_eol}"
        )

    return errors, warnings


def run(repo_root: Path) -> tuple[int, list[str]]:
    poetry = repo_root / "content" / "works" / "poetry"
    if not poetry.exists():
        return 0, []
    all_errors: list[str] = []
    all_warnings: list[str] = []
    for child in sorted(poetry.iterdir()):
        if not child.is_dir():
            continue
        md = child / "index.md"
        if not md.exists():
            continue
        errs, warns = lint_file(md)
        all_errors.extend(errs)
        all_warnings.extend(warns)
    for w in all_warnings:
        print(f"WARN {w}", file=sys.stderr)
    return (1 if all_errors else 0), all_errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    for e in errors:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_poetry_synced: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
