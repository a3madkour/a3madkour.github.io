"""Graph-chrome consistency gate.

Enforces the single-source-of-truth invariants from
docs/superpowers/specs/2026-05-14-graph-view-consistency-design.md:

  1. No pruned per-section graph-control selector survives in main.css.
  2. The 6 graph surfaces each include partials/graph-legend.html and do
     NOT hand-roll a legend or per-section toolbar/legend class.

Sibling-less (no paired unit test): the logic is substring scans +
file-presence checks, too thin to warrant pairing — same rationale as
tools/check_smoke.py (spec §3.1).
"""

import sys
from pathlib import Path

CSS = Path("assets/css/main.css")

# Selectors that must not reappear once the refactor lands.
FORBIDDEN_CSS = [
    ".works-umbrella-toolbar .graph-toggle",
    ".garden-graph-toolbar",
    ".research-graph-toolbar",
    ".graph-page-toolbar",
    ".graph-panel-toolbar",
    ".graph-panel-legend",
    ".garden-graph-legend",
    ".research-graph-legend",
    ".graph-page-legend",
    ".graph-panel-toolbtn",
]

# The 6 graph surfaces. Each must include the shared legend partial and
# must not hand-roll a legend / per-section toolbar class.
SURFACES = [
    Path("layouts/partials/garden/graph-panel.html"),
    Path("layouts/partials/research/graph-panel.html"),
    Path("layouts/partials/works/graph-panel.html"),
    Path("layouts/garden/graph.html"),
    Path("layouts/research/graph.html"),
    Path("layouts/works/graph.html"),
]
LEGEND_PARTIAL_CALL = 'partial "graph-legend.html"'
FORBIDDEN_MARKUP = [
    "graph-panel-legend",
    "graph-page-legend",
    "garden-graph-legend",
    "research-graph-legend",
    "graph-panel-toolbtn",
    "graph-panel-toolbar",
    "garden-graph-toolbar",
    "research-graph-toolbar",
    "graph-page-toolbar",
    'class="filter-chip',  # works graph used the global filter-chip class
    "legend-mark-solid",
    "legend-mark-dashed",
]


def main() -> int:
    errors = []

    if not CSS.is_file():
        print("check_graph_chrome: assets/css/main.css missing", file=sys.stderr)
        return 2
    css = CSS.read_text(encoding="utf-8")
    for sel in FORBIDDEN_CSS:
        if sel in css:
            errors.append(f"main.css still contains forbidden selector: {sel}")

    for surface in SURFACES:
        if not surface.is_file():
            errors.append(f"missing surface file: {surface}")
            continue
        text = surface.read_text(encoding="utf-8")
        if LEGEND_PARTIAL_CALL not in text:
            errors.append(f"{surface}: does not include {LEGEND_PARTIAL_CALL}")
        for bad in FORBIDDEN_MARKUP:
            if bad in text:
                errors.append(f"{surface}: still contains hand-rolled chrome: {bad!r}")

    if errors:
        print(f"check_graph_chrome: {len(errors)} issue(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"check_graph_chrome: OK ({len(SURFACES)} surfaces)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
