#!/usr/bin/env python3
"""CSS class referential-integrity linter (R2.3).

No gate catches CSS selectors orphaned when a template redesign changes class
names, so `assets/css/main.css` accumulates dead rules. This linter extracts
every class used in a selector and flags any that is referenced NOWHERE across
`layouts/`, `assets/js/` (excluding vendored d3), and `content/`.

Conservative by design: class names can be built dynamically (string
concatenation in JS, Hugo `printf`), which this static scan cannot see. Such
classes — and intentionally-deferred round-trip classes — live in
`tools/css-refs-allowlist.txt` (one bare class name per line, `#` comments ok).

Stdlib only. Exits 0 when every class resolves or is allowlisted, 1 otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
SELECTOR_RE = re.compile(r"([^{}]*)\{")
CLASS_IN_SELECTOR_RE = re.compile(r"\.([A-Za-z_][\w-]*)")

REFERENCE_ROOTS = ("layouts", "content")
JS_ROOT = ("assets", "js")
JS_VENDOR_MARKER = f"{Path('assets') / 'js' / 'vendor'}"


def extract_class_selectors(css: str) -> set[str]:
    """Return the set of class names that appear in a selector position."""
    css = COMMENT_RE.sub("", css)
    classes: set[str] = set()
    for selector in SELECTOR_RE.findall(css):
        # Skip at-rule prelude lines (`@media (...)`, `@supports ...`); they
        # carry no class selectors but harmlessly yield none anyway.
        classes.update(CLASS_IN_SELECTOR_RE.findall(selector))
    return classes


def is_referenced(cls: str, text: str) -> bool:
    """True if `cls` appears in `text` bounded by non-class chars (so `.btn`
    is not matched inside `btn-primary`)."""
    return re.search(r"(?<![\w-])" + re.escape(cls) + r"(?![\w-])", text) is not None


# Interpolation openers that construct a class name from a prefix at render
# time: Hugo `{{ ... }}`, JS template literal `${...}`, printf `%s`/`%v`/`%d`.
_INTERP = r"(?:\{\{|\$\{|%[svd])"


def is_dynamically_constructed(cls: str, text: str) -> bool:
    """True if a hyphen-delimited PREFIX of `cls` appears immediately followed by
    an interpolation opener — e.g. `stage-budding` is constructed by
    `class="stage-{{ .growth_stage }}"`. Only prefixes ending at a `-` boundary
    are considered, so a dynamic `stage-` site can't rescue an unrelated class."""
    for i, ch in enumerate(cls):
        if ch != "-":
            continue
        prefix = cls[: i + 1]
        if re.search(re.escape(prefix) + _INTERP, text):
            return True
    return False


def _load_allowlist(repo_root: Path) -> set[str]:
    path = repo_root / "tools" / "css-refs-allowlist.txt"
    if not path.exists():
        return set()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.add(line)
    return out


def _gather_reference_text(repo_root: Path) -> str:
    chunks: list[str] = []
    for root in REFERENCE_ROOTS:
        base = repo_root / root
        if base.is_dir():
            for p in base.rglob("*"):
                if p.is_file() and p.suffix in (".html", ".md"):
                    chunks.append(p.read_text(encoding="utf-8", errors="ignore"))
    js_base = repo_root / Path(*JS_ROOT)
    if js_base.is_dir():
        for p in js_base.rglob("*.js"):
            if "vendor" in p.parts:
                continue
            chunks.append(p.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def run(repo_root: Path) -> tuple[int, list[str]]:
    css_path = repo_root / "assets" / "css" / "main.css"
    if not css_path.exists():
        return (1, [f"main.css not found at {css_path}"])
    classes = extract_class_selectors(css_path.read_text(encoding="utf-8"))
    allow = _load_allowlist(repo_root)
    refs = _gather_reference_text(repo_root)

    errors: list[str] = []
    for cls in sorted(classes):
        if cls in allow:
            continue
        if not is_referenced(cls, refs) and not is_dynamically_constructed(cls, refs):
            errors.append(
                f".{cls}: no reference in layouts/ assets/js/ content/ "
                f"(delete the rule or add to tools/css-refs-allowlist.txt)"
            )
    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} orphaned CSS class(es).", file=sys.stderr)
        return rc
    print("OK — every CSS class resolves to a reference (or is allowlisted).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
