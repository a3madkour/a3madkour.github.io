"""Graph-chrome consistency gate.

Enforces the single-source-of-truth invariants from
docs/superpowers/specs/2026-05-14-graph-view-consistency-design.md:

  1. No pruned per-section graph-control selector survives in main.css.
  2. The 7 graph surfaces each include partials/graph-legend.html (directly
     or transitively via the shared graph-panel.html partial — which is itself
     a checked surface) and do NOT hand-roll a legend or per-section
     toolbar/legend class.

Sibling-less (no paired unit test): the logic is substring scans +
file-presence checks, too thin to warrant pairing — same rationale as
tools/check_smoke.py (spec §3.1).
"""

import sys
from pathlib import Path

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

# The 6 graph surfaces. Each must include the shared legend partial
# (directly or via the shared graph-panel.html wrapper) and must not
# hand-roll a legend / per-section toolbar class.
# After R5.3b: the three graph-panel.html files are thin wrappers that
# delegate to the shared layouts/partials/graph-panel.html, which itself
# always calls graph-legend.html — so they satisfy the invariant
# transitively via SHARED_PANEL_CALL rather than LEGEND_PARTIAL_CALL.
SURFACES = [
    # The shared panel partial the 3 wrappers delegate to. Guarded directly so
    # the transitive legend link (wrapper → SHARED_PANEL_CALL → this file →
    # LEGEND_PARTIAL_CALL) can't silently break: if this file ever drops its
    # graph-legend.html call, this entry fails instead of a false-green.
    Path("layouts/partials/graph-panel.html"),
    Path("layouts/partials/garden/graph-panel.html"),
    Path("layouts/partials/research/graph-panel.html"),
    Path("layouts/partials/works/graph-panel.html"),
    Path("layouts/garden/graph.html"),
    Path("layouts/research/graph.html"),
    Path("layouts/works/graph.html"),
]
LEGEND_PARTIAL_CALL = 'partial "graph-legend.html"'
# After R5.3b the three graph-panel.html wrappers call the shared partial
# instead of graph-legend.html directly; the shared partial always calls
# graph-legend.html so transitive inclusion counts.
SHARED_PANEL_CALL = 'partial "graph-panel.html"'
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

# Item-page surfaces added by the persistent-graph-access slice
# (2026-05-16 spec). Each must include the shared launcher bar AND its
# section's graph panel + graph-data script, so the launcher/panel/legend
# canon stays enforced as surfaces grow.
LAUNCHER_BAR_CALL = 'partial "graph-launcher-bar.html"'
ITEM_SURFACES = {
    Path("layouts/research-theme/single.html"): "research",
    Path("layouts/research-question/single.html"): "research",
    Path("layouts/works-games/single.html"): "works",
    Path("layouts/works-music/single.html"): "works",
    Path("layouts/works-poetry/single.html"): "works",
}


def run(repo_root: Path) -> tuple[int, list[str]]:
    errors: list[str] = []

    css_path = repo_root / "assets" / "css" / "main.css"
    if not css_path.is_file():
        print("check_graph_chrome: assets/css/main.css missing", file=sys.stderr)
        return 2, []
    css = css_path.read_text(encoding="utf-8")
    for sel in FORBIDDEN_CSS:
        if sel in css:
            errors.append(f"main.css still contains forbidden selector: {sel}")

    surfaces = [repo_root / p for p in SURFACES]
    for surface in surfaces:
        if not surface.is_file():
            errors.append(f"missing surface file: {surface.relative_to(repo_root)}")
            continue
        text = surface.read_text(encoding="utf-8")
        rel = surface.relative_to(repo_root)
        if LEGEND_PARTIAL_CALL not in text and SHARED_PANEL_CALL not in text:
            errors.append(
                f"{rel}: does not include {LEGEND_PARTIAL_CALL}"
                f" (or {SHARED_PANEL_CALL})"
            )
        for bad in FORBIDDEN_MARKUP:
            if bad in text:
                errors.append(f"{rel}: still contains hand-rolled chrome: {bad!r}")

    for surface_rel, section in ITEM_SURFACES.items():
        surface = repo_root / surface_rel
        if not surface.is_file():
            errors.append(f"missing item surface file: {surface.relative_to(repo_root)}")
            continue
        text = surface.read_text(encoding="utf-8")
        rel = surface.relative_to(repo_root)
        if LAUNCHER_BAR_CALL not in text:
            errors.append(f"{rel}: does not include {LAUNCHER_BAR_CALL}")
        panel_call = f'partial "{section}/graph-panel.html"'
        script_call = f'partial "{section}/graph-script.html"'
        if panel_call not in text:
            errors.append(f"{rel}: does not include {panel_call}")
        if script_call not in text:
            errors.append(f"{rel}: does not include {script_call}")

    return (1 if errors else 0, errors)


def main() -> int:
    rc, errors = run(Path(__file__).resolve().parent.parent)
    if rc == 2:
        return rc
    if errors:
        print(f"check_graph_chrome: {len(errors)} issue(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
    if rc == 0:
        print(
            f"check_graph_chrome: OK ({len(SURFACES)} graph surfaces, "
            f"{len(ITEM_SURFACES)} item surfaces)"
        )
    return rc


if __name__ == "__main__":
    sys.exit(main())
