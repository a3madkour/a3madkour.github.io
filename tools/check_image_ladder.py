#!/usr/bin/env python3
"""Recipe `image` branch-ladder lockstep linter (RF2.1 guard). Stdlib only.

`layouts/partials/recipes/schema-recipe.html` resolves a recipe's `image` down a
three-branch ladder — absolute `http(s)` passes through, root-relative `/x` goes
through `absURL`, anything else is prefixed with the page permalink — and
`tools/check_recipes_links.py` validates against the *same* three shapes.

The two are coupled by nothing but a pair of reciprocal comments. When they
drift, the linter certifies a value the template mangles: the emitted JSON-LD
URL is broken, no other check can see it (`image` is never rendered as an
`<img>`, so the built-HTML link crawler never visits it), and the only way to
notice is to build a fixture and read the JSON. That is not hypothetical — it
is exactly the defect that shipped and survived a first review during the
recipe remediation run, where the linter accepted absolute and root-relative
values the template turned into
`https://site/recipes/slug/https://cdn.example.com/a.png`.

This asserts the branch *keys* match. It cannot prove the two agree on every
input — only a build can — but drift in the ladder is how they come apart, and
that is cheap to pin here rather than expensive to discover later.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TEMPLATE = Path("layouts") / "partials" / "recipes" / "schema-recipe.html"
LINTER = Path("tools") / "check_recipes_links.py"

# {{- if or (hasPrefix $img "http://") (hasPrefix $img "https://") -}}
TPL_PREFIX_RE = re.compile(r'hasPrefix\s+\$img\s+"([^"]+)"')
# val.startswith(("http://", "https://"))  /  val.startswith("//")
LINT_TUPLE_RE = re.compile(r'\.startswith\(\(([^)]*)\)\)')
LINT_SINGLE_RE = re.compile(r'\.startswith\("([^"]+)"\)')
STR_RE = re.compile(r'"([^"]+)"')

# The linter deliberately rejects shapes the template does not declare, so its
# key set is a superset. These are the extras it is allowed to carry — each one
# narrows *within* a template branch rather than contradicting it.
LINTER_ONLY = {"//"}


def run(repo_root: Path) -> tuple[int, list[str]]:
    errs: list[str] = []
    tpl_path, lint_path = repo_root / TEMPLATE, repo_root / LINTER
    for p in (tpl_path, lint_path):
        if not p.exists():
            return 1, [f"{p}: not found"]

    tpl = tpl_path.read_text(encoding="utf-8")
    lint = lint_path.read_text(encoding="utf-8")

    tpl_keys = set(TPL_PREFIX_RE.findall(tpl))
    if 'hasPrefix $img "/"' in tpl or re.search(r'hasPrefix\s+\$img\s+"/"', tpl):
        tpl_keys.add("/")
    if not tpl_keys:
        return 1, [f"{TEMPLATE}: no hasPrefix branches found — has the ladder moved?"]

    lint_keys: set[str] = set()
    for group in LINT_TUPLE_RE.findall(lint):
        lint_keys.update(STR_RE.findall(group))
    lint_keys.update(LINT_SINGLE_RE.findall(lint))
    if not lint_keys:
        return 1, [f"{LINTER}: no startswith branches found — has the ladder moved?"]

    for key in sorted(tpl_keys - lint_keys):
        errs.append(
            f"image ladder drift: {TEMPLATE} branches on '{key}' but {LINTER} "
            f"does not — the linter would certify a value the template mangles"
        )
    for key in sorted(lint_keys - tpl_keys - LINTER_ONLY):
        errs.append(
            f"image ladder drift: {LINTER} branches on '{key}' but {TEMPLATE} "
            f"does not — the linter rejects a shape the template handles fine"
        )
    return (1 if errs else 0), errs


def main() -> int:
    rc, errs = run(Path(__file__).resolve().parent.parent)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_image_ladder: OK (template and linter branch on the same shapes)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
