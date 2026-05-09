# Garden Interactions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Phase 4 garden interactions — eager Matuschak-style stacked-column retrieval, path log with consent, outgoing/backlinks sections, and a force-directed graph view (side panel + separate page) — decoupled from the Phase 3 org-mode pipeline by synthesizing graph data from existing fixtures at Hugo build time.

**Architecture:** A single Hugo partial (`partials/garden/graph-data.html`, `partialCached`) walks all garden pages, extracts internal links via `findRE` on `.RawContent`, classifies edges by topic-map membership, and emits a JSON blob inlined on every garden page. Two browser modules — `garden-stack.js` (column app) and `garden-graph.js` (d3-force renderer) — read that JSON via a `<script type="application/json">` tag and coordinate via a `garden:stack-changed` custom DOM event. d3-force is vendored at `assets/js/vendor/d3-force.min.js` (no npm) and lazy-imported on first graph open.

**Tech Stack:** Hugo extended ≥ 0.148.0 · vanilla ES modules built by Hugo's `js.Build` (esbuild) · d3-force v3 (vendored) · Python 3 stdlib for the new linter · CSS hand-rolled in `assets/css/main.css` sections 24–28.

**Spec:** `docs/superpowers/specs/2026-05-08-garden-interactions-design.md`

**Predecessor working state:** master @ commit `6a76331` (spec landed). Tag-search slice already merged; 14 garden fixtures with 2 internal links between them.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `tools/check_garden_links.py` | NEW | Linter: validate every `/garden/<slug>/` reference resolves to a non-draft fixture |
| `tools/test_check_garden_links.py` | NEW | Unit tests for the linter |
| `layouts/partials/garden/graph-data.html` | NEW | Build-time graph data partial; called via `partialCached`; emits a JSON string |
| `layouts/partials/garden/path-log.html` | NEW | Sticky breadcrumb at top of stack container |
| `layouts/partials/garden/links-section.html` | NEW | Outgoing-links + backlinks rendered at column bottom |
| `layouts/partials/garden/graph-panel.html` | NEW | Side-panel scaffolding (closed-state HTML) |
| `layouts/garden/graph.html` | NEW | Standalone `/garden/graph/` route |
| `assets/js/garden-stack.js` | NEW | Column app: click intercept, fetch+append, URL sync, clear/Esc, consent banner |
| `assets/js/garden-graph.js` | NEW | Graph runtime: d3-force, panel toggle, filters, local mode, in-stack markers |
| `assets/js/vendor/d3-force.min.js` | NEW | Vendored d3-force v3 ESM bundle |
| `layouts/garden/single.html` | MODIFY | Wrap article in `.garden-stack`; add path log, links section, graph panel, JSON script |
| `layouts/garden/list.html` | MODIFY | Add `⊞ Graph` toggle to filter strip; mount graph panel + JSON script |
| `assets/js/index.js` | MODIFY | Import the two new modules |
| `assets/css/main.css` | MODIFY | Append §§24–28 (path log, columns, links section, graph panel, graph page) |
| `content/garden/<slug>/index.md` × 13 | MODIFY | Insert internal `/garden/` links into existing lorem-ipsum bodies |
| `content/garden/_index.md` | unchanged | — |
| `.github/workflows/hugo.yaml` | MODIFY | Insert two new linter steps between garden-fixtures and filter-chips checks |
| `CLAUDE.md` | MODIFY | New commands, new architecture sections, project-status update |

**Branch convention:** work on `phase-4-garden-interactions`. Commit per task; merge with `--no-ff` at end.

---

## Task 1: Linter — failing tests

**Files:**
- Create: `tools/test_check_garden_links.py`

- [ ] **Step 1.1: Create branch + write failing tests**

```bash
git checkout -b phase-4-garden-interactions
```

Create `tools/test_check_garden_links.py`:

```python
"""Tests for check_garden_links.py — run with:
   python3 -m unittest tools/test_check_garden_links.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_garden_links as lint  # noqa: E402


CONCEPT_NOTE_NO_LINKS = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Lorem ipsum dolor sit amet.
"""

CONCEPT_NOTE_TO_B = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Lorem ipsum [b](/garden/note-b/) dolor sit amet.
"""

CONCEPT_NOTE_TO_MISSING = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Lorem ipsum [missing](/garden/does-not-exist/).
"""

CONCEPT_NOTE_DRAFT = """\
---
title: "Note B"
draft: true
last_modified: 2026-04-22
growth_stage: seedling
---

Body.
"""

CONCEPT_NOTE_PUBLISHED_B = """\
---
title: "Note B"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Body.
"""

CONCEPT_NOTE_SELF_REF = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Self-link [a](/garden/note-a/).
"""

CONCEPT_NOTE_MULTIPLE_TARGETS = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

[b](/garden/note-b/) and [c](/garden/note-c/) and [b again](/garden/note-b/).
"""

CONCEPT_NOTE_NON_GARDEN_LINK = """\
---
title: "Note A"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
---

Outside the section: [essay](/essays/some-essay/).
"""


class GardenLinksLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.garden = self.tmp / "content" / "garden"
        self.garden.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, slug: str, body: str) -> None:
        d = self.garden / slug
        d.mkdir()
        (d / "index.md").write_text(body)

    def test_no_links_passes(self):
        self._write("note-a", CONCEPT_NOTE_NO_LINKS)
        errors, warnings = lint.lint_garden_links(self.garden)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_resolved_link_passes(self):
        self._write("note-a", CONCEPT_NOTE_TO_B)
        self._write("note-b", CONCEPT_NOTE_PUBLISHED_B)
        errors, warnings = lint.lint_garden_links(self.garden)
        self.assertEqual(errors, [])

    def test_missing_target_fails(self):
        self._write("note-a", CONCEPT_NOTE_TO_MISSING)
        errors, _ = lint.lint_garden_links(self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("does-not-exist", errors[0])
        self.assertIn("note-a", errors[0])

    def test_draft_target_fails(self):
        self._write("note-a", CONCEPT_NOTE_TO_B)
        self._write("note-b", CONCEPT_NOTE_DRAFT)
        errors, _ = lint.lint_garden_links(self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("draft", errors[0].lower())

    def test_self_reference_warns_does_not_fail(self):
        self._write("note-a", CONCEPT_NOTE_SELF_REF)
        errors, warnings = lint.lint_garden_links(self.garden)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("note-a", warnings[0])

    def test_multiple_targets_in_one_file(self):
        self._write("note-a", CONCEPT_NOTE_MULTIPLE_TARGETS)
        self._write("note-b", CONCEPT_NOTE_PUBLISHED_B)
        # note-c is missing → 1 error; note-b appears twice but should only error/pass once
        errors, _ = lint.lint_garden_links(self.garden)
        self.assertEqual(len(errors), 1)
        self.assertIn("note-c", errors[0])

    def test_non_garden_link_ignored(self):
        self._write("note-a", CONCEPT_NOTE_NON_GARDEN_LINK)
        errors, warnings = lint.lint_garden_links(self.garden)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 1.2: Run tests to verify they fail (linter doesn't exist yet)**

Run: `python3 -m unittest tools/test_check_garden_links.py -v`

Expected: ImportError ("No module named 'check_garden_links'") or fail at setUp.

---

## Task 2: Linter — implementation

**Files:**
- Create: `tools/check_garden_links.py`

- [ ] **Step 2.1: Implement the linter**

Create `tools/check_garden_links.py`:

```python
#!/usr/bin/env python3
"""Garden internal-link linter.

Walks `content/garden/<slug>/index.md` (skips `_index.md`), extracts every
`/garden/<target-slug>/` reference from the body, and verifies each target
exists and is non-draft.

Self-references are flagged as warnings (likely typos) but do not fail.

Exits 0 on success, 1 on any unresolved or draft target. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


GARDEN_LINK_RE = re.compile(r"/garden/([a-z0-9][a-z0-9-]*)/")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _is_draft(fm: dict[str, object] | None) -> bool:
    if fm is None:
        return False
    return bool(fm.get("draft", False))


def lint_garden_links(garden_dir: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings).

    Errors fail the build; warnings are advisory.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # First pass: which slugs exist + draft state
    slug_state: dict[str, bool] = {}  # slug -> is_draft
    for d in sorted(garden_dir.iterdir()):
        if not d.is_dir():
            continue
        index = d / "index.md"
        if not index.exists():
            continue
        text = _read(index)
        fm = parse_frontmatter(text)
        slug_state[d.name] = _is_draft(fm)

    # Second pass: validate every reference
    for slug, is_draft in sorted(slug_state.items()):
        index = garden_dir / slug / "index.md"
        text = _read(index)
        # Strip frontmatter so we only scan the body
        m = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
        body = text[m.end():] if m else text

        seen: set[str] = set()
        for match in GARDEN_LINK_RE.finditer(body):
            target = match.group(1)
            if target in seen:
                continue
            seen.add(target)

            if target == slug:
                warnings.append(
                    f"{slug}/index.md: self-reference to /garden/{target}/ (likely a typo)"
                )
                continue

            if target not in slug_state:
                errors.append(
                    f"{slug}/index.md: link to /garden/{target}/ does not resolve"
                )
                continue

            if slug_state[target]:
                errors.append(
                    f"{slug}/index.md: link to /garden/{target}/ resolves to a draft note"
                )

    return errors, warnings


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    garden_dir = repo_root / "content" / "garden"
    if not garden_dir.is_dir():
        print(f"error: {garden_dir} not found", file=sys.stderr)
        return 1

    errors, warnings = lint_garden_links(garden_dir)

    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)

    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} broken link(s).", file=sys.stderr)
        return 1

    print(f"OK — verified {len([1 for d in garden_dir.iterdir() if d.is_dir()])} note(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2.2: Run tests**

Run: `python3 -m unittest tools/test_check_garden_links.py -v`

Expected: 7/7 PASS.

- [ ] **Step 2.3: Run linter against current fixtures**

Run: `python3 tools/check_garden_links.py`

Expected: `OK — verified 14 note(s).` (procedural-narrative→salience and surprise-budget→salience both resolve; nguyen orphan is fine; no broken refs.)

- [ ] **Step 2.4: Commit**

```bash
git add tools/check_garden_links.py tools/test_check_garden_links.py
git commit -m "Add garden-links linter (verifies every /garden/ reference resolves)"
```

---

## Task 3: Fixture extension — insert ~27 internal links

**Files:**
- Modify: 13 of 14 `content/garden/<slug>/index.md` (all except `nguyen-2020-games-as-art`)

Filler-only insertion: every link appended into an existing lorem-ipsum sentence with a dash or comma break. No authored prose. Aim for 27 new edges (existing 2: `procedural-narrative→salience-and-memory`, `surprise-budget→salience-and-memory`).

- [ ] **Step 3.1: Edit `content/garden/emergence-vs-design/index.md`**

Replace the body section (after the `---` close) with:

```markdown
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Example sentence one about the line between emergent and authored systems — see [procedural narrative](/garden/procedural-narrative/) for the framing topic.

Example sentence two referencing [surprise budget](/garden/surprise-budget/). Example sentence three.
```

- [ ] **Step 3.2: Edit `content/garden/invisible-cities/index.md`**

Replace the body (keep frontmatter as-is):

```markdown
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Example sentence about Calvino's nested-list structure — compare with [story atoms](/garden/story-atoms/) and the [emergence vs design](/garden/emergence-vs-design/) lens.

{{< spoiler summary="chapter ending" level="light" >}}
Filler placeholder revealing how the framing device resolves at the end. (Hidden by default — click to expand.)
{{< /spoiler >}}

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium. Example sentence two.
```

- [ ] **Step 3.3: Edit `content/garden/koyaanisqatsi-soundtrack/index.md`**

Replace the body:

```markdown
Lorem ipsum dolor sit amet. Example sentence about minimalism and pacing — pairs with [emergence vs design](/garden/emergence-vs-design/) on system-driven aesthetics.

Example sentence two. Example sentence three.
```

- [ ] **Step 3.4: Edit `content/garden/memory-in-play/index.md`**

Replace the body (keep `topic_map` frontmatter):

```markdown
What survives a session, and what does the player rebuild from scratch. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Members include [recall vs replay](/garden/recall-vs-replay/) and [the save game](/garden/the-save-game/).

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua — see also [salience and memory](/garden/salience-and-memory/) for the cross-topic bridge.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
```

- [ ] **Step 3.5: Edit `content/garden/outer-wilds/index.md`**

Replace the body:

```markdown
Lorem ipsum dolor sit amet. Example sentence about queued status — connects to [salience and memory](/garden/salience-and-memory/) and [recall vs replay](/garden/recall-vs-replay/).

Example sentence two.
```

- [ ] **Step 3.6: Edit `content/garden/recall-vs-replay/index.md`**

Replace the body:

```markdown
Lorem ipsum dolor sit amet. Example sentence one about replay as recall — depends on [sleep and consolidation](/garden/sleep-and-consolidation/) and ties back to [salience and memory](/garden/salience-and-memory/).

Sed ut perspiciatis. Example sentence two referencing [the save game](/garden/the-save-game/).
```

- [ ] **Step 3.7: Edit `content/garden/salience-and-memory/index.md`**

Replace the body:

```markdown
Lorem ipsum dolor sit amet. Example sentence about salience as a narrative resource — leans on [emergence vs design](/garden/emergence-vs-design/), informs [surprise budget](/garden/surprise-budget/), bridges into [memory in play](/garden/memory-in-play/).

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium.
```

- [ ] **Step 3.8: Edit `content/garden/severance-s2/index.md`**

Replace the body (keep all spoiler shortcodes intact):

```markdown
Lorem ipsum dolor sit amet. Example sentence one about the show's premise — the structural interest sits near [memory in play](/garden/memory-in-play/) and [recall vs replay](/garden/recall-vs-replay/).

{{< spoiler summary="episode 1 ending" level="heavy" >}}
Filler placeholder for first heavy spoiler.
{{< /spoiler >}}

Example sentence two. Example sentence three.

{{< spoiler summary="midseason twist" level="heavy" >}}
Filler placeholder for second heavy spoiler.
{{< /spoiler >}}

Example sentence four.

{{< spoiler summary="finale" level="heavy" >}}
Filler placeholder for third heavy spoiler.
{{< /spoiler >}}

Example sentence five.
```

- [ ] **Step 3.9: Edit `content/garden/sleep-and-consolidation/index.md`**

Replace the body:

```markdown
Lorem ipsum dolor sit amet. Example sentence about consolidation during sleep — relates to [memory in play](/garden/memory-in-play/) and [recall vs replay](/garden/recall-vs-replay/).

Example sentence two.
```

- [ ] **Step 3.10: Edit `content/garden/story-atoms/index.md`**

Replace the body (keep figure shortcode):

```markdown
Lorem ipsum dolor sit amet. Example sentence one drawing on [emergence vs design](/garden/emergence-vs-design/), [salience and memory](/garden/salience-and-memory/), [koyaanisqatsi soundtrack](/garden/koyaanisqatsi-soundtrack/), and [invisible cities](/garden/invisible-cities/).

{{< figure src="figure-placeholder.svg" caption="Filler caption — story atoms diagram" >}}

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam.
```

- [ ] **Step 3.11: Edit `content/garden/surprise-budget/index.md`**

Replace the body (keep sidenote, keep existing salience-and-memory link):

```markdown
Lorem ipsum dolor sit amet, consectetur adipiscing elit. {{< sidenote >}}Example sentence with a sidenote.{{< /sidenote >}} Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

This note links to [salience and memory](/garden/salience-and-memory/) — the back-target. Also see [story atoms](/garden/story-atoms/) and [recall vs replay](/garden/recall-vs-replay/) for adjacent threads.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
```

- [ ] **Step 3.12: Edit `content/garden/the-save-game/index.md`**

Replace the body:

```markdown
Lorem ipsum dolor sit amet. Example sentence about the save game as a memory artifact — read alongside [recall vs replay](/garden/recall-vs-replay/).

Example sentence two.
```

- [ ] **Step 3.13: Leave `content/garden/nguyen-2020-games-as-art/index.md` untouched (deliberate orphan)**

Verify with: `grep -c '/garden/' content/garden/nguyen-2020-games-as-art/index.md`. Expected: `0`.

- [ ] **Step 3.14: Run linter — should pass**

Run: `python3 tools/check_garden_links.py`

Expected: `OK — verified 14 note(s).`

- [ ] **Step 3.15: Run garden-fixtures linter — should still pass (no frontmatter touched)**

Run: `python3 tools/check_garden_fixtures.py`

Expected: clean exit.

- [ ] **Step 3.16: Sanity-check edge count**

Run: `grep -ohE '/garden/[a-z0-9-]+/' content/garden/*/index.md | sort | uniq -c | sort -rn | head`

Expected: salience-and-memory referenced ~6–7 times (hub); other slugs distributed.

- [ ] **Step 3.17: Commit**

```bash
git add content/garden/
git commit -m "Extend garden fixtures with ~27 internal links for graph structure"
```

---

## Task 4: Build-time graph data partial

**Files:**
- Create: `layouts/partials/garden/graph-data.html`

This partial walks all garden pages once and emits a JSON string. Wrapped in `partialCached` at call sites so it computes once per build.

- [ ] **Step 4.1: Create `layouts/partials/garden/graph-data.html`**

```hugo
{{- /* Inputs:
       . — Hugo Site (passed from call site as `partialCached "garden/graph-data" .Site`)
   Output: a JSON string {nodes, edges, topics} encoding the garden graph.
   Tag colour, edge solid/dashed, node sizing all live in the consumer (garden-graph.js).
*/ -}}
{{- $pages := where .RegularPages "Section" "garden" -}}

{{- /* 1. Outgoing-link map: slug -> []targets (deduped, in document order) */ -}}
{{- $byOut := dict -}}
{{- range $pages -}}
  {{- $slug := path.Base .File.Dir -}}
  {{- $matches := findRE `\(/garden/[a-z0-9-]+/\)` .RawContent -}}
  {{- $targets := slice -}}
  {{- range $matches -}}
    {{- $t := strings.TrimPrefix "(/garden/" . -}}
    {{- $t = strings.TrimSuffix "/)" $t -}}
    {{- if not (in $targets $t) -}}
      {{- if ne $t $slug -}}
        {{- $targets = $targets | append $t -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
  {{- $byOut = merge $byOut (dict $slug $targets) -}}
{{- end -}}

{{- /* 2. Incoming-link map: slug -> []sources */ -}}
{{- $byIn := dict -}}
{{- range $src, $targets := $byOut -}}
  {{- range $targets -}}
    {{- $cur := index $byIn . | default slice -}}
    {{- $byIn = merge $byIn (dict . ($cur | append $src)) -}}
  {{- end -}}
{{- end -}}

{{- /* 3. Topic-membership map: topic-owner-slug -> []member-slugs (from topic_map frontmatter) */ -}}
{{- $byTopic := dict -}}
{{- range $pages -}}
  {{- $owner := path.Base .File.Dir -}}
  {{- with .Params.topic_map -}}
    {{- $byTopic = merge $byTopic (dict $owner .) -}}
  {{- end -}}
{{- end -}}

{{- /* 4. Edge list with crossTopic classification.
       Edge is solid (crossTopic=false) iff src and tgt share at least one topic-owner. */ -}}
{{- $edges := slice -}}
{{- range $src, $targets := $byOut -}}
  {{- range $targets -}}
    {{- $tgt := . -}}
    {{- $cross := true -}}
    {{- range $owner, $members := $byTopic -}}
      {{- if and (in $members $src) (in $members $tgt) -}}
        {{- $cross = false -}}
      {{- end -}}
    {{- end -}}
    {{- $edges = $edges | append (dict "source" $src "target" $tgt "crossTopic" $cross) -}}
  {{- end -}}
{{- end -}}

{{- /* 5. Node list with degree (in + out) */ -}}
{{- $nodes := slice -}}
{{- range $pages -}}
  {{- $slug := path.Base .File.Dir -}}
  {{- $tags := .Params.tags | default slice -}}
  {{- $tag := "" -}}
  {{- if gt (len $tags) 0 -}}{{- $tag = index $tags 0 -}}{{- end -}}
  {{- $stage := .Params.growth_stage | default "seedling" -}}
  {{- $mt := .Params.media_type -}}
  {{- $flavor := "concept" -}}
  {{- if $mt -}}
    {{- if in (slice "book" "album" "track" "game" "film" "series") $mt -}}
      {{- $flavor = "media" -}}
    {{- else -}}
      {{- $flavor = "reference" -}}
    {{- end -}}
  {{- end -}}
  {{- $out := index $byOut $slug | default slice -}}
  {{- $in := index $byIn $slug | default slice -}}
  {{- $degree := add (len $out) (len $in) -}}
  {{- $nodes = $nodes | append (dict
        "slug"   $slug
        "title"  .Title
        "tag"    $tag
        "stage"  $stage
        "flavor" $flavor
        "degree" $degree) -}}
{{- end -}}

{{- $data := dict "nodes" $nodes "edges" $edges "topics" $byTopic -}}
{{- $data | jsonify -}}
```

- [ ] **Step 4.2: Mount the JSON on the garden index temporarily**

Modify `layouts/garden/list.html`. After the closing `</section>` of the existing section (around the last line before `{{ end }}`), insert:

```hugo
<script type="application/json" id="garden-graph-data">{{ partialCached "garden/graph-data" .Site }}</script>
```

So the file's last few lines become:

```hugo
    <p class="garden-empty" hidden>No notes match these filters yet.</p>

  {{- end -}}
</section>
<script type="application/json" id="garden-graph-data">{{ partialCached "garden/graph-data" .Site }}</script>
{{ end }}
```

- [ ] **Step 4.3: Build and inspect**

Run: `hugo --minify --buildDrafts=false 2>&1 | tail -10`

Expected: build succeeds.

Run: `grep -A 1 "garden-graph-data" public/garden/index.html | head -5`

Expected: a single `<script type="application/json" id="garden-graph-data">{...}</script>` tag with valid JSON.

- [ ] **Step 4.4: Validate JSON shape**

Run:

```bash
python3 -c '
import json, re
html = open("public/garden/index.html").read()
m = re.search(r"<script type=\"application/json\" id=\"garden-graph-data\">(.*?)</script>", html, re.S)
data = json.loads(m.group(1))
print("nodes:", len(data["nodes"]))
print("edges:", len(data["edges"]))
print("topics:", list(data["topics"].keys()))
print("hub:", max(data["nodes"], key=lambda n: n["degree"])["slug"], "deg", max(n["degree"] for n in data["nodes"]))
print("orphan:", [n["slug"] for n in data["nodes"] if n["degree"] == 0])
'
```

Expected output (approximate):
```
nodes: 14
edges: 29  (or close)
topics: ['memory-in-play', 'procedural-narrative']
hub: salience-and-memory deg 7
orphan: ['nguyen-2020-games-as-art']
```

- [ ] **Step 4.5: Commit**

```bash
git add layouts/partials/garden/graph-data.html layouts/garden/list.html
git commit -m "Emit build-time garden graph data as inline JSON"
```

---

## Task 5: Links section partial (outgoing + backlinks)

**Files:**
- Create: `layouts/partials/garden/links-section.html`
- Modify: `layouts/garden/single.html`

- [ ] **Step 5.1: Create `layouts/partials/garden/links-section.html`**

```hugo
{{- /* Inputs:
       . — Hugo Page (the note being rendered)
   Output: <section class="garden-links"> with outgoing + backlinks lists, both
   limited to /garden/ targets. Reads the cached graph data so we don't
   re-walk pages.
*/ -}}
{{- $slug := path.Base .File.Dir -}}
{{- $dataJSON := partialCached "garden/graph-data" .Site -}}
{{- $data := $dataJSON | transform.Unmarshal -}}

{{- /* Build a slug -> title lookup once */ -}}
{{- $titleBySlug := dict -}}
{{- range $data.nodes -}}
  {{- $titleBySlug = merge $titleBySlug (dict .slug .title) -}}
{{- end -}}

{{- $outgoing := slice -}}
{{- $backlinks := slice -}}
{{- range $data.edges -}}
  {{- if eq .source $slug -}}{{- $outgoing = $outgoing | append .target -}}{{- end -}}
  {{- if eq .target $slug -}}{{- $backlinks = $backlinks | append .source -}}{{- end -}}
{{- end -}}

{{- if or $outgoing $backlinks -}}
<section class="garden-links" aria-label="Note links">
  {{- if $outgoing -}}
  <h2 class="garden-links-heading">Links from this note</h2>
  <ul class="garden-links-list">
    {{- range $outgoing -}}
    <li><a href="/garden/{{ . }}/">{{ index $titleBySlug . | default . }}</a></li>
    {{- end -}}
  </ul>
  {{- end -}}
  {{- if $backlinks -}}
  <h2 class="garden-links-heading">Backlinks ({{ len $backlinks }})</h2>
  <ul class="garden-links-list">
    {{- range $backlinks -}}
    <li><a href="/garden/{{ . }}/">{{ index $titleBySlug . | default . }}</a></li>
    {{- end -}}
  </ul>
  {{- end -}}
</section>
{{- end -}}
```

- [ ] **Step 5.2: Wire into `layouts/garden/single.html`**

Read the current file: `layouts/garden/single.html`. Replace the entire `define "main"` block with:

```hugo
{{ define "main" }}
<article class="reading-column garden-note">
  <p class="crumb"><a href="{{ "/garden/" | relURL }}">Garden</a> ›</p>

  {{ partial "garden/note-header.html" . }}

  <h1 class="garden-note-title">{{ .Title }}</h1>

  {{- $mediaType := .Params.media_type -}}
  {{- $isMedia := and $mediaType (in (slice "book" "album" "track" "game" "film" "series") $mediaType) -}}
  {{- $isReference := and $mediaType (in (slice "paper" "video" "article" "talk") $mediaType) -}}

  {{- if or $isMedia $isReference -}}
    {{- with .Params.creator -}}
    <p class="garden-creator">by {{ . }}{{ with $.Params.year }} · {{ . }}{{ end }}</p>
    {{- end -}}
    <div class="garden-media-meta">
      {{- with .Params.original_url -}}
      <a class="original-link" href="{{ . }}" rel="noopener noreferrer">→ original</a>
      {{- end -}}
      {{- with $mediaType -}}
      <span class="media-type-meta">{{ . }}</span>
      {{- end -}}
    </div>
  {{- end -}}

  <div class="garden-note-body essay-body">
    {{ .Content }}
  </div>

  {{- with .Params.topic_map -}}
  {{ partial "garden/topic-section.html" (dict
      "context" $
      "heading" "Notes in this topic"
      "framing" "Curated reading order, not chronological."
      "linkHeading" false
  ) }}
  {{- end -}}

  {{ partial "garden/links-section.html" . }}
</article>
<script type="application/json" id="garden-graph-data">{{ partialCached "garden/graph-data" .Site }}</script>
{{ end }}
```

- [ ] **Step 5.3: Build and verify a note with edges renders both lists**

Run: `hugo --minify`

Run: `grep -A 20 "garden-links" public/garden/salience-and-memory/index.html | head -30`

Expected: a `<section class="garden-links">` containing:
- "Links from this note" heading + list of 3 `<li><a href="/garden/.../">...</a></li>`
- "Backlinks (N)" heading + list with multiple entries

- [ ] **Step 5.4: Verify the orphan has no section**

Run: `grep -c "garden-links" public/garden/nguyen-2020-games-as-art/index.html`

Expected: `0`.

- [ ] **Step 5.5: Commit**

```bash
git add layouts/partials/garden/links-section.html layouts/garden/single.html
git commit -m "Render outgoing-links + backlinks sections at column bottom"
```

---

## Task 6: Path log partial + CSS §24

**Files:**
- Create: `layouts/partials/garden/path-log.html`
- Modify: `assets/css/main.css`
- Modify: `layouts/garden/single.html`

- [ ] **Step 6.1: Create `layouts/partials/garden/path-log.html`**

```hugo
{{- /* Inputs:
       . — Hugo Page (the note being rendered)
   Output: <nav class="garden-path-log"> with one crumb (the URL note).
   garden-stack.js extends the crumb list when ?stack= is present and on click.
*/ -}}
<nav class="garden-path-log" aria-label="Reading path">
  <span class="path-log-label">Path:</span>
  <a class="path-log-crumb" href="{{ "/garden/" | relURL }}">Garden</a>
  <span class="path-log-sep" aria-hidden="true">›</span>
  <a class="path-log-crumb is-active" aria-current="page" href="{{ .RelPermalink }}" data-slug="{{ path.Base .File.Dir }}">{{ .Title }}</a>
  <span class="path-log-actions">
    <span class="path-log-count" data-stack-count="1">1 in stack</span>
    <button type="button" class="path-log-clear" hidden>clear</button>
    <button type="button" class="garden-graph-toggle" aria-expanded="false" aria-controls="garden-graph-panel">⊞ Graph</button>
  </span>
</nav>
```

- [ ] **Step 6.2: Add CSS §24 to `assets/css/main.css`**

Append to the bottom of the file:

```css
/* ------------------------------------------------------------------
 * 24. Garden path log + consent banner
 * ------------------------------------------------------------------ */
.garden-path-log {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem var(--page-gutter);
  border-bottom: 1px solid var(--color-rule);
  background: var(--color-tile);
  position: sticky;
  top: 0;
  z-index: 5;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  flex-wrap: wrap;
}
.garden-path-log .path-log-label {
  color: var(--color-ink-soft);
  font-weight: 500;
}
.garden-path-log .path-log-crumb {
  color: var(--color-burgundy);
  text-decoration: none;
  border-bottom: 1px dotted var(--color-burgundy);
  padding-bottom: 1px;
}
.garden-path-log .path-log-crumb.is-active {
  font-weight: 600;
  border-bottom-style: solid;
}
.garden-path-log .path-log-sep {
  color: var(--color-ink-fade);
}
.garden-path-log .path-log-actions {
  margin-left: auto;
  display: flex;
  gap: 0.7rem;
  align-items: center;
}
.garden-path-log .path-log-count {
  color: var(--color-ink-soft);
}
.garden-path-log .path-log-clear,
.garden-path-log .garden-graph-toggle {
  background: transparent;
  border: 1px solid var(--color-rule);
  border-radius: 4px;
  padding: 0.15rem 0.55rem;
  font: inherit;
  color: var(--color-ink-soft);
  cursor: pointer;
}
.garden-path-log .path-log-clear:hover,
.garden-path-log .garden-graph-toggle:hover {
  background: var(--color-stone);
  color: var(--color-ink);
}
.garden-path-log .garden-graph-toggle[aria-expanded="true"] {
  background: var(--color-burgundy);
  color: var(--color-tile);
  border-color: var(--color-burgundy);
}

.garden-consent-banner {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.45rem var(--page-gutter);
  background: color-mix(in srgb, var(--color-warn) 15%, var(--color-tile));
  border-bottom: 1px solid var(--color-rule);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink);
  flex-wrap: wrap;
}
.garden-consent-banner .opts {
  margin-left: auto;
  display: flex;
  gap: 0.35rem;
}
.garden-consent-banner button {
  background: var(--color-tile);
  border: 1px solid var(--color-rule);
  border-radius: 4px;
  padding: 0.15rem 0.55rem;
  font: inherit;
  cursor: pointer;
}
.garden-consent-banner button:hover { background: var(--color-stone); }
```

- [ ] **Step 6.3: Mount path log in `single.html`**

Modify `layouts/garden/single.html` to insert the path log partial directly inside `define "main"`, before the article. Replace the opening of the main block:

```hugo
{{ define "main" }}
{{ partial "garden/path-log.html" . }}
<article class="reading-column garden-note">
```

(The article opening tag stays where it was.)

- [ ] **Step 6.4: Build and visually verify**

Run: `hugo server --buildDrafts` (in a background terminal). Visit `http://localhost:1313/garden/salience-and-memory/`.

Expected: a sticky breadcrumb row at the top showing `Path: Garden › Salience and memory`, right-side `1 in stack · clear (hidden) · ⊞ Graph`.

- [ ] **Step 6.5: Run contrast linter**

Run: `python3 tools/check-contrast.py`

Expected: clean exit (no token changes).

- [ ] **Step 6.6: Commit**

```bash
git add layouts/partials/garden/path-log.html layouts/garden/single.html assets/css/main.css
git commit -m "Add path-log partial + CSS §24 (sticky breadcrumb, consent banner)"
```

---

## Task 7: Stack-columns wrapping + CSS §25 + §26

**Files:**
- Modify: `layouts/garden/single.html`
- Modify: `assets/css/main.css`

The article needs to be wrapped in `.garden-stack > .garden-stack-columns > .garden-column` so the JS runtime has clean DOM hooks. CSS makes this look like a single column on every viewport at this stage; the multi-column behavior unlocks once garden-stack.js appends columns (Task 8).

- [ ] **Step 7.1: Restructure `layouts/garden/single.html`**

Replace the file with:

```hugo
{{ define "main" }}
{{ partial "garden/path-log.html" . }}
<div class="garden-stack" data-stack-root="true">
  <div class="garden-stack-columns">
    <article class="garden-column is-active reading-column garden-note" data-slug="{{ path.Base .File.Dir }}">
      <p class="crumb"><a href="{{ "/garden/" | relURL }}">Garden</a> ›</p>

      {{ partial "garden/note-header.html" . }}

      <h1 class="garden-note-title" tabindex="-1">{{ .Title }}</h1>

      {{- $mediaType := .Params.media_type -}}
      {{- $isMedia := and $mediaType (in (slice "book" "album" "track" "game" "film" "series") $mediaType) -}}
      {{- $isReference := and $mediaType (in (slice "paper" "video" "article" "talk") $mediaType) -}}

      {{- if or $isMedia $isReference -}}
        {{- with .Params.creator -}}
        <p class="garden-creator">by {{ . }}{{ with $.Params.year }} · {{ . }}{{ end }}</p>
        {{- end -}}
        <div class="garden-media-meta">
          {{- with .Params.original_url -}}
          <a class="original-link" href="{{ . }}" rel="noopener noreferrer">→ original</a>
          {{- end -}}
          {{- with $mediaType -}}
          <span class="media-type-meta">{{ . }}</span>
          {{- end -}}
        </div>
      {{- end -}}

      <div class="garden-note-body essay-body">
        {{ .Content }}
      </div>

      {{- with .Params.topic_map -}}
      {{ partial "garden/topic-section.html" (dict
          "context" $
          "heading" "Notes in this topic"
          "framing" "Curated reading order, not chronological."
          "linkHeading" false
      ) }}
      {{- end -}}

      {{ partial "garden/links-section.html" . }}
    </article>
  </div>
</div>
<script type="application/json" id="garden-graph-data">{{ partialCached "garden/graph-data" .Site }}</script>
{{ end }}
```

- [ ] **Step 7.2: Add CSS §25 + §26 to `assets/css/main.css`**

Append:

```css
/* ------------------------------------------------------------------
 * 25. Garden stacked-column container
 *     (default: single column = canonical reading layout;
 *      ≥ 2 columns appear once garden-stack.js appends.)
 * ------------------------------------------------------------------ */
.garden-stack {
  display: block;
}
.garden-stack-columns {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(0, 1fr);
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
}
.garden-stack-columns:has(.garden-column:nth-child(2)) {
  grid-auto-columns: 480px;
  overflow-x: auto;
  border-bottom: 1px solid var(--color-rule);
}
.garden-column {
  scroll-snap-align: start;
  border-right: 1px solid var(--color-rule);
  padding: 1.5rem var(--page-gutter) 2rem;
  overflow-y: auto;
  min-height: 0;
}
.garden-column:last-child { border-right: none; }
.garden-column.is-active {
  background: color-mix(in srgb, var(--color-tile) 70%, var(--color-stone));
}
.garden-stack-columns:not(:has(.garden-column:nth-child(2))) .garden-column {
  /* Single-column mode — restore canonical reading width */
  border-right: none;
  background: transparent;
  padding: 0;
  overflow: visible;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .garden-stack-columns { scroll-behavior: auto; }
}

/* Mobile — collapse stack to single column even when JS would have appended */
@media (max-width: 720px) {
  .garden-stack-columns {
    grid-auto-flow: row;
    grid-auto-columns: 1fr;
    overflow-x: visible !important;
  }
  .garden-column {
    border-right: none;
    border-bottom: 1px solid var(--color-rule);
  }
  .garden-column:last-child { border-bottom: none; }
}

/* ------------------------------------------------------------------
 * 26. Garden links section (outgoing + backlinks at column bottom)
 * ------------------------------------------------------------------ */
.garden-links {
  margin-top: 2rem;
  padding-top: 1.25rem;
  border-top: 1px dashed var(--color-rule);
}
.garden-links-heading {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-ink-soft);
  margin: 1rem 0 0.4rem;
  font-weight: 600;
}
.garden-links-heading:first-of-type { margin-top: 0; }
.garden-links-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.garden-links-list li { padding: 0.15rem 0; font-size: var(--text-sm); }
.garden-links-list a {
  color: var(--color-burgundy);
  text-decoration: underline;
  text-decoration-style: dotted;
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
}
.garden-links-list a:hover { text-decoration-style: solid; }
```

- [ ] **Step 7.3: Build and verify**

Run: `hugo server --buildDrafts`. Visit `/garden/salience-and-memory/`.

Expected: page renders identically to before this task (single column, canonical width). Inspect DOM: `<div class="garden-stack"><div class="garden-stack-columns"><article class="garden-column is-active …">` is the new wrapper structure.

- [ ] **Step 7.4: Commit**

```bash
git add layouts/garden/single.html assets/css/main.css
git commit -m "Wrap garden notes in stack-column container; add CSS §§25–26"
```

---

## Task 8: garden-stack.js — init from URL + click interception

**Files:**
- Create: `assets/js/garden-stack.js`
- Modify: `assets/js/index.js`

This task lands the column app in working state for navigation: direct entry, deep links restoring `?stack=`, click-to-append, click-to-refocus.

- [ ] **Step 8.1: Create `assets/js/garden-stack.js`**

```js
// Garden stacked-column runtime — eager Matuschak-style.
// Spec: docs/superpowers/specs/2026-05-08-garden-interactions-design.md §5.

const STACK_ROOT = '.garden-stack';
const COLUMNS = '.garden-stack-columns';
const COLUMN = '.garden-column';
const PATHLOG = '.garden-path-log';
const MOBILE_QUERY = '(max-width: 720px)';
const FETCH_OPTS = { credentials: 'same-origin' };

const state = {
  slugs: [],
  consent: 'unset', // 'unset' | 'yes' | 'session' | 'no'
};

function isMobile() {
  return window.matchMedia(MOBILE_QUERY).matches;
}

function motionPref() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
}

function urlStackParam() {
  const p = new URL(window.location.href).searchParams.get('stack');
  return p ? p.split(',').map(s => s.trim()).filter(Boolean) : [];
}

function rootSlug() {
  const root = document.querySelector(`${COLUMNS} ${COLUMN}`);
  return root ? root.getAttribute('data-slug') : null;
}

function rewriteURL() {
  const url = new URL(window.location.href);
  if (state.slugs.length <= 1) {
    url.searchParams.delete('stack');
  } else {
    url.searchParams.set('stack', state.slugs.join(','));
  }
  history.replaceState(null, '', url.toString());
}

function dispatchStackChanged() {
  window.dispatchEvent(new CustomEvent('garden:stack-changed', {
    detail: { slugs: state.slugs.slice() },
  }));
}

function updatePathLog() {
  const log = document.querySelector(PATHLOG);
  if (!log) return;

  // Remove all crumbs except the first (Garden anchor) — we'll rebuild from state.
  const label = log.querySelector('.path-log-label');
  const actions = log.querySelector('.path-log-actions');
  const gardenAnchor = log.querySelector('.path-log-crumb[href$="/garden/"]');

  // Clear everything between label and actions
  Array.from(log.children).forEach(child => {
    if (child !== label && child !== actions && child !== gardenAnchor) {
      log.removeChild(child);
    }
  });

  // Rebuild: › <crumb>...
  state.slugs.forEach((slug, i) => {
    const sep = document.createElement('span');
    sep.className = 'path-log-sep';
    sep.setAttribute('aria-hidden', 'true');
    sep.textContent = '›';
    log.insertBefore(sep, actions);

    const a = document.createElement('a');
    a.className = 'path-log-crumb';
    a.href = `/garden/${slug}/`;
    a.dataset.slug = slug;
    if (i === state.slugs.length - 1) {
      a.classList.add('is-active');
      a.setAttribute('aria-current', 'page');
    }
    // Title comes from the rendered column's <h1>
    const col = document.querySelector(`${COLUMN}[data-slug="${CSS.escape(slug)}"]`);
    a.textContent = col ? col.querySelector('.garden-note-title').textContent.trim() : slug;
    log.insertBefore(a, actions);
  });

  // Update count + clear visibility
  const count = actions.querySelector('.path-log-count');
  const clear = actions.querySelector('.path-log-clear');
  if (count) {
    count.textContent = `${state.slugs.length} in stack`;
    count.dataset.stackCount = String(state.slugs.length);
  }
  if (clear) clear.hidden = state.slugs.length < 2;
}

async function fetchColumn(slug) {
  const res = await fetch(`/garden/${slug}/`, FETCH_OPTS);
  if (!res.ok) return null;
  const text = await res.text();
  const doc = new DOMParser().parseFromString(text, 'text/html');
  const col = doc.querySelector(`${COLUMN}[data-slug="${CSS.escape(slug)}"]`);
  return col ? col.cloneNode(true) : null;
}

function focusColumn(slug) {
  const col = document.querySelector(`${COLUMN}[data-slug="${CSS.escape(slug)}"]`);
  if (!col) return;
  document.querySelectorAll(`${COLUMN}.is-active`).forEach(c => c.classList.remove('is-active'));
  col.classList.add('is-active');
  col.scrollIntoView({ behavior: motionPref(), inline: 'start', block: 'nearest' });
  const heading = col.querySelector('.garden-note-title');
  if (heading) heading.focus();
}

async function appendColumn(slug) {
  if (state.slugs.includes(slug)) {
    focusColumn(slug);
    return;
  }
  const cols = document.querySelector(COLUMNS);
  if (!cols) return;
  const col = await fetchColumn(slug);
  if (!col) return;
  cols.appendChild(col);
  state.slugs.push(slug);
  rewriteURL();
  focusColumn(slug);
  updatePathLog();
  dispatchStackChanged();
}

function clearStack() {
  if (state.slugs.length < 2) return;
  const cols = document.querySelector(COLUMNS);
  const root = state.slugs[0];
  Array.from(cols.querySelectorAll(COLUMN)).forEach(col => {
    if (col.getAttribute('data-slug') !== root) cols.removeChild(col);
  });
  state.slugs = [root];
  rewriteURL();
  focusColumn(root);
  updatePathLog();
  dispatchStackChanged();
}

function isInternalGardenLink(a) {
  if (!a || a.tagName !== 'A' || !a.href) return null;
  const u = new URL(a.href, window.location.href);
  if (u.origin !== window.location.origin) return null;
  const m = u.pathname.match(/^\/garden\/([a-z0-9][a-z0-9-]*)\/?$/);
  return m ? m[1] : null;
}

async function init() {
  const root = document.querySelector(STACK_ROOT);
  if (!root) return;

  const rs = rootSlug();
  if (!rs) return;

  // Mobile bypass: links navigate normally; no init.
  if (isMobile()) {
    state.slugs = [rs];
    return;
  }

  // Normalize: URL slug is column 0. ?stack= entries appended in order, deduped, URL slug skipped.
  const declared = urlStackParam();
  state.slugs = [rs];
  for (const s of declared) {
    if (s !== rs && !state.slugs.includes(s)) state.slugs.push(s);
  }

  // Fetch slugs 1..N in parallel; drop unresolved.
  const fetches = state.slugs.slice(1).map(s => fetchColumn(s).then(col => ({ slug: s, col })));
  const results = await Promise.all(fetches);
  const cols = document.querySelector(COLUMNS);
  const finalSlugs = [rs];
  for (const r of results) {
    if (r.col) {
      cols.appendChild(r.col);
      finalSlugs.push(r.slug);
    }
  }
  state.slugs = finalSlugs;

  rewriteURL();
  updatePathLog();
  if (state.slugs.length > 1) {
    focusColumn(state.slugs[state.slugs.length - 1]);
  }
  dispatchStackChanged();

  // Delegated click handler for internal /garden/ links
  root.addEventListener('click', (e) => {
    const a = e.target.closest('a');
    const slug = isInternalGardenLink(a);
    if (!slug) return;
    e.preventDefault();
    appendColumn(slug);
  });

  // Path-log clear button
  const clear = document.querySelector(`${PATHLOG} .path-log-clear`);
  if (clear) clear.addEventListener('click', clearStack);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
```

- [ ] **Step 8.2: Wire the module into `assets/js/index.js`**

Replace the contents:

```js
import './toggle-theme.js';
import './nav.js';
import './essay.js';
import './garden.js';
import './garden-stack.js';
```

- [ ] **Step 8.3: Build and verify**

Run: `hugo server --buildDrafts`. In a desktop browser:

- Visit `/garden/salience-and-memory/` — single column shows; path log "1 in stack"; clear button hidden
- Click an internal `/garden/...` link in the body (e.g., to "memory in play") → second column appends; URL changes to `?stack=memory-in-play`; path log shows "2 in stack"; clear button visible
- Click the same link again → no third column appended; first column re-focused
- Visit `/garden/salience-and-memory/?stack=memory-in-play,recall-vs-replay` directly → all three columns load
- Click clear → URL strips `?stack=`; only column 1 remains
- On mobile (DevTools narrow viewport): click on internal link → normal navigation, no append

- [ ] **Step 8.4: Commit**

```bash
git add assets/js/garden-stack.js assets/js/index.js
git commit -m "Add garden-stack.js: eager init, click intercept, URL sync, clear"
```

---

## Task 9: garden-stack.js — Esc handling + path-log click

**Files:**
- Modify: `assets/js/garden-stack.js`

The Esc key needs disambiguation: if the graph panel is open and focused → close panel (Task 12 wires this). If panel closed and stack ≥ 2 → clear. If neither → no-op. We add the stack-side keyboard handler now; the panel side wires later.

Also: clicking a path-log crumb should re-focus the existing column. Currently the delegated click handler runs on `STACK_ROOT` which doesn't include the path log. We add a separate handler.

- [ ] **Step 9.1: Add Esc handler in `garden-stack.js`**

Inside `init()`, after the path-log clear listener, add:

```js
  // Esc: clear stack if graph panel isn't focused
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (state.slugs.length < 2) return;
    const panel = document.getElementById('garden-graph-panel');
    if (panel && panel.contains(document.activeElement) && panel.getAttribute('aria-hidden') === 'false') {
      // Panel will handle Esc; do nothing.
      return;
    }
    clearStack();
  });

  // Path log: clicking a crumb refocuses
  const log = document.querySelector(PATHLOG);
  if (log) {
    log.addEventListener('click', (e) => {
      const a = e.target.closest('a.path-log-crumb');
      if (!a) return;
      const slug = a.dataset.slug;
      if (slug && state.slugs.includes(slug)) {
        e.preventDefault();
        focusColumn(slug);
      }
    });
  }
```

- [ ] **Step 9.2: Build and verify**

Run: `hugo server`. Navigate `/garden/salience-and-memory/`, click two internal links → 3 columns. Press Esc → stack collapses to column 1. Append two more, click on the leftmost path-log crumb → focuses column 1 (no change to URL or stack).

- [ ] **Step 9.3: Commit**

```bash
git add assets/js/garden-stack.js
git commit -m "Wire Esc + path-log crumb clicks into stack runtime"
```

---

## Task 10: Consent banner

**Files:**
- Modify: `assets/js/garden-stack.js`

The banner appears the FIRST time the stack would persist a visited slug, i.e., on the first 1→2 transition when `path-log-consent === null` in localStorage. After choice, banner is removed.

- [ ] **Step 10.1: Add consent state + helpers**

In `garden-stack.js`, near the top (after the `state` declaration), add:

```js
const CONSENT_KEY = 'path-log-consent';
const VISITED_KEY = 'garden-path-log';
const VISITED_CAP = 100;

function readConsent() {
  try {
    return localStorage.getItem(CONSENT_KEY) || 'unset';
  } catch { return 'unset'; }
}

function writeConsent(value) {
  try { localStorage.setItem(CONSENT_KEY, value); } catch {}
  state.consent = value;
}

function persistVisited(slug) {
  if (state.consent === 'unset' || state.consent === 'no') return;
  const store = state.consent === 'session' ? sessionStorage : localStorage;
  let list;
  try {
    list = JSON.parse(store.getItem(VISITED_KEY) || '[]');
  } catch { list = []; }
  list.push(slug);
  if (list.length > VISITED_CAP) list = list.slice(-VISITED_CAP);
  try { store.setItem(VISITED_KEY, JSON.stringify(list)); } catch {}
}
```

- [ ] **Step 10.2: Render the banner on first 1→2 transition**

Add a helper and wire it into `appendColumn`:

```js
function showConsentBanner() {
  if (state.consent !== 'unset') return;
  const log = document.querySelector(PATHLOG);
  if (!log) return;
  if (document.querySelector('.garden-consent-banner')) return;

  const banner = document.createElement('aside');
  banner.className = 'garden-consent-banner';
  banner.setAttribute('role', 'dialog');
  banner.setAttribute('aria-label', 'Track reading path');
  banner.innerHTML = `
    <span>Track your reading path across visits?</span>
    <span class="opts">
      <button type="button" data-choice="yes">Yes, persist</button>
      <button type="button" data-choice="session">Just this session</button>
      <button type="button" data-choice="no">No, never</button>
    </span>
  `;
  log.parentNode.insertBefore(banner, log);

  banner.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-choice]');
    if (!btn) return;
    const choice = btn.dataset.choice;
    writeConsent(choice);
    if (choice !== 'no') {
      // Persist current stack retroactively.
      state.slugs.forEach(persistVisited);
    }
    banner.parentNode.removeChild(banner);
  });
}
```

Replace the `appendColumn` function with:

```js
async function appendColumn(slug) {
  if (state.slugs.includes(slug)) {
    focusColumn(slug);
    return;
  }
  const cols = document.querySelector(COLUMNS);
  if (!cols) return;
  const col = await fetchColumn(slug);
  if (!col) return;
  const wasOne = state.slugs.length === 1;
  cols.appendChild(col);
  state.slugs.push(slug);
  rewriteURL();
  focusColumn(slug);
  updatePathLog();
  dispatchStackChanged();
  persistVisited(slug);
  if (wasOne) showConsentBanner();
}
```

Initialize `state.consent` in `init()` near the top:

```js
  state.consent = readConsent();
```

- [ ] **Step 10.3: Build and verify**

Run: `hugo server`. In a fresh browser profile (or with `localStorage.clear()` from devtools):

- Visit `/garden/salience-and-memory/` — no banner
- Click an internal link → second column appends AND consent banner appears above the path log
- Click "Yes, persist" → banner disappears; check `localStorage["path-log-consent"]` is `"yes"`; `localStorage["garden-path-log"]` contains both slugs
- Reload `/garden/salience-and-memory/` → no banner (consent already chosen)
- Reset storage and try "Just this session" → check `sessionStorage["garden-path-log"]`; `localStorage["garden-path-log"]` empty
- Reset storage and try "No, never" → no further writes after choice

- [ ] **Step 10.4: Commit**

```bash
git add assets/js/garden-stack.js
git commit -m "Add consent banner + persistent path-log storage"
```

---

## Task 11: Vendor d3-force

**Files:**
- Create: `assets/js/vendor/d3-force.min.js`

Hugo's `js.Build` (esbuild) cannot resolve `d3-force` from a bare specifier without `node_modules`. Vendoring keeps the project npm-free and allows a relative `import` from `garden-graph.js`.

- [ ] **Step 11.1: Download d3-force ESM bundle**

```bash
mkdir -p assets/js/vendor
curl -L 'https://cdn.jsdelivr.net/npm/d3-force@3/+esm' -o assets/js/vendor/d3-force.min.js
```

- [ ] **Step 11.2: Verify download is an ESM module**

```bash
head -c 200 assets/js/vendor/d3-force.min.js
```

Expected: starts with `import` statements (it pulls `d3-dispatch`, `d3-quadtree`, `d3-timer` from the CDN). Since these are CDN-relative imports, esbuild won't resolve them at build time. Use the **standalone bundle** instead:

```bash
curl -L 'https://cdn.jsdelivr.net/npm/d3-force@3/dist/d3-force.min.js' -o assets/js/vendor/d3-force.umd.js
```

This is UMD, not ESM. To get a proper standalone ESM bundle, fetch from `esm.sh`:

```bash
curl -L 'https://esm.sh/d3-force@3?bundle' -o assets/js/vendor/d3-force.min.js
```

`?bundle` inlines the dependencies into a single file with no remote imports.

Verify: `wc -c assets/js/vendor/d3-force.min.js` (expected ~25–35 KB).
Verify: `head -c 200 assets/js/vendor/d3-force.min.js` should NOT contain external `import` statements (only internal aliasing).

- [ ] **Step 11.3: Smoke-test the import resolves at build**

Create a temporary smoke file `assets/js/vendor/_smoke.js`:

```js
import { forceSimulation } from './d3-force.min.js';
console.log('d3-force loaded:', typeof forceSimulation);
```

Run: `hugo --renderToMemory 2>&1 | grep -i "error\|warn" | head -20`

Expected: no resolve errors mentioning `d3-force`.

Delete the smoke file:

```bash
rm assets/js/vendor/_smoke.js
```

- [ ] **Step 11.4: Commit**

```bash
git add assets/js/vendor/
git commit -m "Vendor d3-force v3 ESM bundle (no npm dependency)"
```

---

## Task 12: Graph panel partial + CSS §27

**Files:**
- Create: `layouts/partials/garden/graph-panel.html`
- Modify: `assets/css/main.css`
- Modify: `layouts/garden/single.html`
- Modify: `layouts/garden/list.html`

The panel is empty scaffolding at this stage; `garden-graph.js` (next task) renders into it.

- [ ] **Step 12.1: Create `layouts/partials/garden/graph-panel.html`**

```hugo
<aside class="garden-graph-panel"
       id="garden-graph-panel"
       role="region"
       aria-label="Garden graph"
       aria-hidden="true">
  <header class="garden-graph-panel-header">
    <span class="garden-graph-panel-title">Graph</span>
    <button type="button" class="garden-graph-panel-close" aria-label="Close graph panel">×</button>
  </header>
  <div class="garden-graph-panel-toolbar" aria-label="Graph filters">
    {{- /* Tag/stage chips populated by garden-graph.js once data is parsed */ -}}
  </div>
  <div class="garden-graph-panel-canvas"></div>
  <ul class="garden-graph-panel-legend" aria-hidden="true"></ul>
</aside>
```

- [ ] **Step 12.2: Add CSS §27 to `assets/css/main.css`**

Append:

```css
/* ------------------------------------------------------------------
 * 27. Garden graph panel (slide-in side panel, desktop only)
 * ------------------------------------------------------------------ */
.garden-graph-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 320px;
  background: var(--color-tile);
  border-left: 1px solid var(--color-rule);
  box-shadow: -8px 0 22px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  transform: translateX(100%);
  transition: transform 200ms ease-out;
  z-index: 20;
}
.garden-graph-panel[aria-hidden="false"] {
  transform: translateX(0);
}
.garden-graph-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.7rem 1rem;
  border-bottom: 1px solid var(--color-rule);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
}
.garden-graph-panel-close {
  background: transparent;
  border: 0;
  font-size: 1.2rem;
  line-height: 1;
  color: var(--color-ink-soft);
  cursor: pointer;
  padding: 0.1rem 0.4rem;
}
.garden-graph-panel-close:hover { color: var(--color-ink); }
.garden-graph-panel-toolbar {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--color-rule);
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
}
.garden-graph-panel-toolbar .label {
  color: var(--color-ink-soft);
  margin-right: 0.2rem;
}
.garden-graph-panel-toolbar .chip {
  background: transparent;
  border: 1px solid var(--color-rule);
  border-radius: 999px;
  padding: 0.1rem 0.55rem;
  font: inherit;
  cursor: pointer;
  color: var(--color-ink-soft);
}
.garden-graph-panel-toolbar .chip[aria-pressed="true"] {
  background: var(--color-burgundy);
  color: var(--color-tile);
  border-color: var(--color-burgundy);
}
.garden-graph-panel-canvas {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
}
.garden-graph-panel-canvas svg {
  width: 100%;
  height: 100%;
}
.garden-graph-panel-legend {
  list-style: none;
  margin: 0;
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--color-rule);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}
.garden-graph-panel-legend .swatch {
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-right: 0.25rem;
  vertical-align: middle;
}

/* Force-directed graph node + edge styling */
.garden-graph-node circle {
  cursor: pointer;
  stroke: transparent;
  stroke-width: 1;
}
.garden-graph-node.in-stack circle {
  stroke: var(--color-ink);
  stroke-width: 2.5;
}
.garden-graph-node text {
  font-family: var(--font-ui);
  font-size: 9px;
  fill: var(--color-ink);
  pointer-events: none;
  user-select: none;
}
.garden-graph-node:focus circle {
  outline: 2px solid var(--color-burgundy);
  outline-offset: 2px;
}
.garden-graph-edge {
  stroke: var(--color-ink-fade);
  stroke-width: 1;
}
.garden-graph-edge.cross-topic {
  stroke-dasharray: 4 3;
}

/* Reduced motion: no slide */
@media (prefers-reduced-motion: reduce) {
  .garden-graph-panel { transition: none; }
}

/* Mobile: panel hidden — toggle navigates to /garden/graph/ instead */
@media (max-width: 720px) {
  .garden-graph-panel { display: none; }
}
```

- [ ] **Step 12.3: Mount panel in `layouts/garden/single.html`**

Add directly after the closing `</div>` of `.garden-stack`, before the `<script type="application/json">` tag:

```hugo
{{ partial "garden/graph-panel.html" . }}
<script type="application/json" id="garden-graph-data">{{ partialCached "garden/graph-data" .Site }}</script>
{{ end }}
```

- [ ] **Step 12.4: Mount panel + toggle button in `layouts/garden/list.html`**

The list page doesn't have a path log. Add the toggle button to the filter strip and mount the panel.

In `layouts/garden/list.html`, find the closing of the filter chips partial call:

```hugo
    {{ partial "filter-chips.html" (dict "dimensions" $dims "section" "garden") }}
```

Right after that line, add:

```hugo
    <button type="button" class="garden-graph-toggle" aria-expanded="false" aria-controls="garden-graph-panel">⊞ Graph</button>
```

And right before the `</section>` close tag (the existing one after the empty-state paragraph), add the panel mount:

```hugo
    <p class="garden-empty" hidden>No notes match these filters yet.</p>

  {{- end -}}
</section>
{{ partial "garden/graph-panel.html" . }}
<script type="application/json" id="garden-graph-data">{{ partialCached "garden/graph-data" .Site }}</script>
{{ end }}
```

- [ ] **Step 12.5: Build and verify**

Run: `hugo server`. Visit `/garden/salience-and-memory/`. Inspect DOM:
- `<aside class="garden-graph-panel" id="garden-graph-panel" aria-hidden="true">` exists
- Panel is off-screen (transform: translateX(100%))

Visit `/garden/`:
- The "⊞ Graph" toggle button appears at the end of the filter strip
- Panel exists, hidden

Click the toggle → no behavior yet (JS not wired). That's expected; Task 13 wires it.

- [ ] **Step 12.6: Commit**

```bash
git add layouts/partials/garden/graph-panel.html layouts/garden/single.html layouts/garden/list.html assets/css/main.css
git commit -m "Add graph-panel partial + CSS §27 (closed-state scaffolding)"
```

---

## Task 13: garden-graph.js — d3-force render + panel toggle + filters + in-stack markers

**Files:**
- Create: `assets/js/garden-graph.js`
- Modify: `assets/js/index.js`

This is the largest single task. Splitting further would create coupling cycles (each piece needs a reference to the SVG and the data); we keep them together but the file stays under ~250 lines.

- [ ] **Step 13.1: Create `assets/js/garden-graph.js`**

```js
// Garden graph runtime. Uses d3-force for layout; renders to SVG.
// Spec: docs/superpowers/specs/2026-05-08-garden-interactions-design.md §6.

const PANEL_KEY = 'garden-graph-open';
const TAG_PALETTE = {
  // Map well-known tags to existing site tokens.
  // Anything else falls back to --color-ink-fade.
  'narrative': 'var(--color-burgundy)',
  'memory':    'var(--color-green)',
  'games':     'var(--color-steel)',
  'reading':   'var(--color-warn)',
  'calvino':   'var(--color-warn)',
  'play':      'var(--color-steel)',
  'aesthetics':'var(--color-ink-soft)',
};

const state = {
  data: null,
  panel: null,
  panelOpen: false,
  svg: null,
  simulation: null,
  filters: { tag: 'all', stage: 'all', local: 'all' /* all | 1-hop | 2-hop */ },
  inStack: new Set(),
  page: { isMobile: false, isNotePage: false, currentSlug: null },
};

function reducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function isMobile() {
  return window.matchMedia('(max-width: 720px)').matches;
}

function tagColor(tag) {
  return TAG_PALETTE[tag] || 'var(--color-ink-fade)';
}

function nodeRadius(degree) {
  return Math.min(16, Math.max(5, 5 + degree * 1.5));
}

function parseData() {
  const tag = document.getElementById('garden-graph-data');
  if (!tag) return null;
  try { return JSON.parse(tag.textContent); } catch { return null; }
}

function bfsNeighborhood(focus, hops, edges) {
  const adj = new Map();
  for (const e of edges) {
    if (!adj.has(e.source)) adj.set(e.source, new Set());
    if (!adj.has(e.target)) adj.set(e.target, new Set());
    adj.get(e.source).add(e.target);
    adj.get(e.target).add(e.source);
  }
  const visited = new Set([focus]);
  let frontier = new Set([focus]);
  for (let i = 0; i < hops; i++) {
    const next = new Set();
    frontier.forEach(s => {
      (adj.get(s) || new Set()).forEach(t => {
        if (!visited.has(t)) { next.add(t); visited.add(t); }
      });
    });
    frontier = next;
  }
  return visited;
}

function applyFilters() {
  if (!state.data) return { nodes: [], edges: [] };
  const f = state.filters;
  let nodes = state.data.nodes;
  if (f.tag !== 'all') nodes = nodes.filter(n => n.tag === f.tag);
  if (f.stage !== 'all') nodes = nodes.filter(n => n.stage === f.stage);
  if (state.page.isNotePage && f.local !== 'all') {
    const hops = f.local === '1-hop' ? 1 : 2;
    const allowed = bfsNeighborhood(state.page.currentSlug, hops, state.data.edges);
    nodes = nodes.filter(n => allowed.has(n.slug));
  }
  const allowed = new Set(nodes.map(n => n.slug));
  const edges = state.data.edges.filter(e => allowed.has(e.source) && allowed.has(e.target));
  return { nodes: nodes.map(n => ({ ...n })), edges: edges.map(e => ({ ...e })) };
}

async function buildSimulation(canvas) {
  const { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } =
    await import('./vendor/d3-force.min.js');

  const { nodes, edges } = applyFilters();
  const w = canvas.clientWidth || 320;
  const h = canvas.clientHeight || 360;

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', `Force-directed graph of ${nodes.length} note(s)`);
  const desc = document.createElementNS(SVG_NS, 'desc');
  desc.textContent = `Garden graph with ${nodes.length} nodes and ${edges.length} edges. Click a node to open it in a stack.`;
  svg.appendChild(desc);

  const edgeLayer = document.createElementNS(SVG_NS, 'g');
  edgeLayer.setAttribute('class', 'garden-graph-edges');
  svg.appendChild(edgeLayer);
  const nodeLayer = document.createElementNS(SVG_NS, 'g');
  nodeLayer.setAttribute('class', 'garden-graph-nodes');
  svg.appendChild(nodeLayer);

  // Build edge elements
  const edgeEls = edges.map(e => {
    const line = document.createElementNS(SVG_NS, 'line');
    line.setAttribute('class', 'garden-graph-edge' + (e.crossTopic ? ' cross-topic' : ''));
    edgeLayer.appendChild(line);
    return { e, line };
  });

  // Build node elements (each is a <g> with circle + text)
  const nodeEls = nodes.map(n => {
    const g = document.createElementNS(SVG_NS, 'g');
    g.setAttribute('class', 'garden-graph-node' + (state.inStack.has(n.slug) ? ' in-stack' : ''));
    g.setAttribute('tabindex', '0');
    g.setAttribute('role', 'link');
    g.setAttribute('aria-label', `Open ${n.title} in stack`);
    g.dataset.slug = n.slug;

    const c = document.createElementNS(SVG_NS, 'circle');
    c.setAttribute('r', String(nodeRadius(n.degree)));
    c.setAttribute('fill', tagColor(n.tag));
    g.appendChild(c);

    const t = document.createElementNS(SVG_NS, 'text');
    t.textContent = n.title;
    t.setAttribute('x', String(nodeRadius(n.degree) + 3));
    t.setAttribute('y', '3');
    g.appendChild(t);

    g.addEventListener('click', () => { window.location.assign(`/garden/${n.slug}/`); });
    g.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        window.location.assign(`/garden/${n.slug}/`);
      }
    });

    nodeLayer.appendChild(g);
    return { n, g };
  });

  canvas.replaceChildren(svg);

  const sim = forceSimulation(nodes)
    .force('link', forceLink(edges).id(d => d.slug).distance(60).strength(0.6))
    .force('charge', forceManyBody().strength(-180))
    .force('center', forceCenter(w / 2, h / 2))
    .force('collide', forceCollide().radius(d => nodeRadius(d.degree) + 4));

  function renderTick() {
    edgeEls.forEach(({ e, line }) => {
      line.setAttribute('x1', e.source.x);
      line.setAttribute('y1', e.source.y);
      line.setAttribute('x2', e.target.x);
      line.setAttribute('y2', e.target.y);
    });
    nodeEls.forEach(({ n, g }) => {
      g.setAttribute('transform', `translate(${n.x}, ${n.y})`);
    });
  }

  if (reducedMotion()) {
    sim.stop();
    for (let i = 0; i < 300; i++) sim.tick();
    renderTick();
  } else {
    sim.on('tick', renderTick);
  }

  return { svg, simulation: sim };
}

function rebuildGraph() {
  const canvas = state.panel
    ? state.panel.querySelector('.garden-graph-panel-canvas')
    : document.querySelector('.garden-graph-page .garden-graph-canvas');
  if (!canvas) return;
  if (state.simulation) state.simulation.stop();
  buildSimulation(canvas).then(({ svg, simulation }) => {
    state.svg = svg;
    state.simulation = simulation;
  });
}

function updateInStackMarkers() {
  if (!state.svg) return;
  state.svg.querySelectorAll('.garden-graph-node').forEach(g => {
    const slug = g.dataset.slug;
    g.classList.toggle('in-stack', state.inStack.has(slug));
  });
}

function buildToolbar(host) {
  if (!state.data) return;
  const tags = new Set();
  const stages = new Set();
  state.data.nodes.forEach(n => { if (n.tag) tags.add(n.tag); stages.add(n.stage); });

  const mkChip = (label, dim, value) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'chip';
    b.dataset.dim = dim;
    b.dataset.value = value;
    b.setAttribute('aria-pressed', state.filters[dim] === value ? 'true' : 'false');
    b.textContent = label;
    b.addEventListener('click', () => {
      state.filters[dim] = value;
      host.querySelectorAll(`button[data-dim="${dim}"]`).forEach(c => {
        c.setAttribute('aria-pressed', c.dataset.value === value ? 'true' : 'false');
      });
      rebuildGraph();
    });
    return b;
  };

  host.replaceChildren();

  // Tag dim
  const tagLabel = document.createElement('span'); tagLabel.className = 'label'; tagLabel.textContent = 'Tag:';
  host.append(tagLabel, mkChip('All', 'tag', 'all'));
  Array.from(tags).sort().forEach(t => host.appendChild(mkChip(t, 'tag', t)));

  // Stage dim
  const stageLabel = document.createElement('span'); stageLabel.className = 'label'; stageLabel.textContent = 'Stage:';
  host.append(stageLabel, mkChip('All', 'stage', 'all'));
  ['seedling', 'budding', 'evergreen'].filter(s => stages.has(s)).forEach(s => host.appendChild(mkChip(s, 'stage', s)));

  // Local dim — note pages only
  if (state.page.isNotePage) {
    const localLabel = document.createElement('span'); localLabel.className = 'label'; localLabel.textContent = 'Scope:';
    host.append(localLabel, mkChip('All', 'local', 'all'), mkChip('1-hop', 'local', '1-hop'), mkChip('2-hop', 'local', '2-hop'));
  }
}

function buildLegend(host) {
  host.replaceChildren();
  const tags = new Map();
  (state.data.nodes || []).forEach(n => { if (n.tag) tags.set(n.tag, true); });
  Array.from(tags.keys()).slice(0, 4).forEach(tag => {
    const li = document.createElement('li');
    li.innerHTML = `<span class="swatch" style="background:${tagColor(tag)}"></span>${tag}`;
    host.appendChild(li);
  });
  const note = document.createElement('li');
  note.textContent = 'size = link count · solid = same topic · dashed = cross-topic';
  host.appendChild(note);
}

function openPanel() {
  if (!state.panel) return;
  if (isMobile()) {
    window.location.assign('/garden/graph/');
    return;
  }
  state.panel.setAttribute('aria-hidden', 'false');
  state.panelOpen = true;
  try { sessionStorage.setItem(PANEL_KEY, '1'); } catch {}
  document.querySelectorAll('.garden-graph-toggle').forEach(b => b.setAttribute('aria-expanded', 'true'));

  const toolbar = state.panel.querySelector('.garden-graph-panel-toolbar');
  const legend = state.panel.querySelector('.garden-graph-panel-legend');
  if (toolbar && !toolbar.children.length) buildToolbar(toolbar);
  if (legend && !legend.children.length) buildLegend(legend);
  rebuildGraph();
}

function closePanel() {
  if (!state.panel) return;
  state.panel.setAttribute('aria-hidden', 'true');
  state.panelOpen = false;
  try { sessionStorage.removeItem(PANEL_KEY); } catch {}
  document.querySelectorAll('.garden-graph-toggle').forEach(b => b.setAttribute('aria-expanded', 'false'));
  const toggle = document.querySelector('.garden-graph-toggle');
  if (toggle) toggle.focus();
}

function init() {
  state.data = parseData();
  if (!state.data) return;
  state.panel = document.getElementById('garden-graph-panel');
  state.page.isMobile = isMobile();
  const stackRoot = document.querySelector('.garden-stack-columns .garden-column');
  state.page.isNotePage = !!stackRoot;
  state.page.currentSlug = stackRoot ? stackRoot.dataset.slug : null;

  // Initial in-stack set
  document.querySelectorAll('.garden-stack-columns .garden-column').forEach(c => {
    state.inStack.add(c.dataset.slug);
  });

  // Toggle button(s)
  document.querySelectorAll('.garden-graph-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      if (state.panelOpen) closePanel(); else openPanel();
    });
  });

  // Close button inside panel
  if (state.panel) {
    const close = state.panel.querySelector('.garden-graph-panel-close');
    if (close) close.addEventListener('click', closePanel);
  }

  // Esc when panel focused
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!state.panelOpen) return;
    if (state.panel && state.panel.contains(document.activeElement)) {
      e.stopPropagation();
      closePanel();
    }
  });

  // Listen for stack changes
  window.addEventListener('garden:stack-changed', (e) => {
    state.inStack = new Set(e.detail.slugs);
    updateInStackMarkers();
  });

  // Restore panel state
  let restore = false;
  try { restore = sessionStorage.getItem(PANEL_KEY) === '1'; } catch {}
  if (restore && !isMobile()) openPanel();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
```

- [ ] **Step 13.2: Wire into `assets/js/index.js`**

```js
import './toggle-theme.js';
import './nav.js';
import './essay.js';
import './garden.js';
import './garden-stack.js';
import './garden-graph.js';
```

- [ ] **Step 13.3: Build and verify**

Run: `hugo server`. Visit `/garden/salience-and-memory/`:
- Click `⊞ Graph` toggle → panel slides in from the right
- Filters render (Tag: All / narrative / memory / … · Stage: All / seedling / budding / evergreen · Scope: All / 1-hop / 2-hop)
- Force-directed graph renders inside the panel; salience-and-memory has bold-stroke (in stack)
- Click a tag chip → graph re-simulates filtered subset
- Click `1-hop` → only nodes 1 hop from salience-and-memory + connecting edges
- Click an internal link in the article (e.g., to memory-in-play) → second column appends; graph's bold-stroke set updates to include both
- Press Esc with focus inside panel → panel closes
- Toggle panel open, navigate to `/garden/sleep-and-consolidation/` → panel re-opens (sessionStorage persistence)
- Click toggle → panel closes; sessionStorage cleared

Visit `/garden/`:
- Toggle works
- "Scope" chips not shown (no current slug)

Mobile (DevTools narrow viewport):
- Click toggle → navigates to `/garden/graph/` (404 for now; that's task 14)

- [ ] **Step 13.4: Commit**

```bash
git add assets/js/garden-graph.js assets/js/index.js
git commit -m "Add garden-graph.js: d3-force render, panel toggle, filters, local mode"
```

---

## Task 14: Graph page at /garden/graph/

**Files:**
- Create: `layouts/garden/graph.html`
- Create: `content/garden/graph.md`
- Modify: `assets/css/main.css`

The standalone graph page is the mobile fallback. Same JSON, same JS module, different layout shell.

- [ ] **Step 14.1: Create `content/garden/graph.md` (so Hugo treats `/garden/graph/` as a real page)**

```markdown
---
title: "Graph"
draft: false
last_modified: 2026-05-08
growth_stage: evergreen
type: garden-graph
url: /garden/graph/
---

The garden as a network.
```

We use `type: garden-graph` so Hugo picks the special layout below instead of the default garden single template. The `growth_stage` is required by the garden-fixtures linter.

- [ ] **Step 14.2: Create `layouts/garden/graph.html`**

This layout uses the `garden-graph` type. Hugo resolves layouts in this order: `layouts/<section>/<type>.html` doesn't exist by default — we use Hugo's default lookup by setting `type` in frontmatter and creating the matching template. Place at `layouts/garden-graph/single.html`:

Actually simpler: use `layouts/garden/graph.html` and reference via Hugo's lookup with `layout: graph` in frontmatter:

Update `content/garden/graph.md`:

```markdown
---
title: "Graph"
draft: false
last_modified: 2026-05-08
growth_stage: evergreen
layout: graph
url: /garden/graph/
---

The garden as a network.
```

Now create `layouts/garden/graph.html`:

```hugo
{{ define "main" }}
<section class="reading-column garden-graph-page">
  <p class="crumb"><a href="{{ "/garden/" | relURL }}">Garden</a> ›</p>
  <h1>{{ .Title }}</h1>
  <p class="garden-graph-summary">Click a node to open it in a stack.</p>

  <nav class="garden-graph-toolbar" aria-label="Graph filters">
    {{- /* populated by garden-graph.js */ -}}
  </nav>

  <div class="garden-graph-canvas" role="img" aria-label="Force-directed graph of garden notes">
    {{- /* SVG mounted by garden-graph.js */ -}}
  </div>

  <ul class="garden-graph-legend"></ul>
</section>
<script type="application/json" id="garden-graph-data">{{ partialCached "garden/graph-data" .Site }}</script>
{{ end }}
```

The current `garden-graph.js` looks for `.garden-graph-panel` and falls back to `.garden-graph-page .garden-graph-canvas` in `rebuildGraph`. The init also checks for an open panel (none exists on this layout) and treats the page as the canvas.

- [ ] **Step 14.3: Update `garden-graph.js` for graph-page mode**

`init()` needs to handle the graph-page case where there's no panel and no path log.

Locate `init()` and modify the panel/toolbar logic. Replace `init()` with:

```js
function init() {
  state.data = parseData();
  if (!state.data) return;
  state.panel = document.getElementById('garden-graph-panel');
  state.page.isMobile = isMobile();
  const stackRoot = document.querySelector('.garden-stack-columns .garden-column');
  state.page.isNotePage = !!stackRoot;
  state.page.currentSlug = stackRoot ? stackRoot.dataset.slug : null;

  // Initial in-stack set
  document.querySelectorAll('.garden-stack-columns .garden-column').forEach(c => {
    state.inStack.add(c.dataset.slug);
  });

  const isGraphPage = !!document.querySelector('.garden-graph-page');

  if (isGraphPage) {
    // Standalone /garden/graph/ — render immediately; no panel.
    const toolbar = document.querySelector('.garden-graph-page .garden-graph-toolbar');
    const legend = document.querySelector('.garden-graph-page .garden-graph-legend');
    if (toolbar) buildToolbar(toolbar);
    if (legend) buildLegend(legend);
    rebuildGraph();
    return;
  }

  // Toggle button(s)
  document.querySelectorAll('.garden-graph-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      if (state.panelOpen) closePanel(); else openPanel();
    });
  });

  // Close button inside panel
  if (state.panel) {
    const close = state.panel.querySelector('.garden-graph-panel-close');
    if (close) close.addEventListener('click', closePanel);
  }

  // Esc when panel focused
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!state.panelOpen) return;
    if (state.panel && state.panel.contains(document.activeElement)) {
      e.stopPropagation();
      closePanel();
    }
  });

  // Listen for stack changes
  window.addEventListener('garden:stack-changed', (e) => {
    state.inStack = new Set(e.detail.slugs);
    updateInStackMarkers();
  });

  // Restore panel state
  let restore = false;
  try { restore = sessionStorage.getItem(PANEL_KEY) === '1'; } catch {}
  if (restore && !isMobile()) openPanel();
}
```

Also update `rebuildGraph()` to find the canvas correctly on the graph page:

```js
function rebuildGraph() {
  let canvas;
  const isGraphPage = !!document.querySelector('.garden-graph-page');
  if (isGraphPage) {
    canvas = document.querySelector('.garden-graph-page .garden-graph-canvas');
  } else if (state.panel) {
    canvas = state.panel.querySelector('.garden-graph-panel-canvas');
  }
  if (!canvas) return;
  if (state.simulation) state.simulation.stop();
  buildSimulation(canvas).then(({ svg, simulation }) => {
    state.svg = svg;
    state.simulation = simulation;
  });
}
```

- [ ] **Step 14.4: Add CSS §28 to `assets/css/main.css`**

Append:

```css
/* ------------------------------------------------------------------
 * 28. Garden graph standalone page (/garden/graph/)
 * ------------------------------------------------------------------ */
.garden-graph-page .garden-graph-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
  padding: 0.5rem 0;
  border-top: 1px solid var(--color-rule);
  border-bottom: 1px solid var(--color-rule);
  margin: 1rem 0;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
}
.garden-graph-page .garden-graph-toolbar .label {
  color: var(--color-ink-soft);
}
.garden-graph-page .garden-graph-toolbar .chip {
  background: transparent;
  border: 1px solid var(--color-rule);
  border-radius: 999px;
  padding: 0.1rem 0.65rem;
  font: inherit;
  cursor: pointer;
  color: var(--color-ink-soft);
}
.garden-graph-page .garden-graph-toolbar .chip[aria-pressed="true"] {
  background: var(--color-burgundy);
  color: var(--color-tile);
  border-color: var(--color-burgundy);
}
.garden-graph-page .garden-graph-canvas {
  min-height: 70vh;
  border: 1px solid var(--color-rule);
  border-radius: 6px;
  background: var(--color-tile);
}
.garden-graph-page .garden-graph-canvas svg {
  width: 100%;
  height: 70vh;
}
.garden-graph-page .garden-graph-legend {
  list-style: none;
  margin: 1rem 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
}
.garden-graph-page .garden-graph-legend .swatch {
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-right: 0.25rem;
  vertical-align: middle;
}
```

- [ ] **Step 14.5: Adjust the linter to skip the graph page**

The graph fixture has frontmatter that doesn't fit the regular concept-flavor schema (it has `layout` + `url` keys). Run `python3 tools/check_garden_fixtures.py` — it will flag `layout` and `url` as unrecognized fields.

Two options:
1. Add `layout` and `url` to the allowed concept fields.
2. Skip the graph page in the linter by filename.

Choose option 2 for clarity. Edit `tools/check_garden_fixtures.py`:

Find the main loop that walks fixtures and add a skip condition for `graph.md`. Locate:

```python
    for d in sorted(garden_dir.iterdir()):
        if not d.is_dir():
            continue
```

The graph page is `content/garden/graph.md` (a leaf bundle, not a directory). The current linter walks directories only — so it already skips the graph file. Verify by running:

Run: `python3 tools/check_garden_fixtures.py`

Expected: clean exit. If it skips graph.md naturally, no edit needed. If not, add the skip.

Run: `python3 tools/check_garden_links.py`

Expected: clean exit (the graph.md page has no /garden/ links in its body).

- [ ] **Step 14.6: Build and verify**

Run: `hugo server`. Visit `/garden/graph/`:
- Page renders with breadcrumb, title "Graph", toolbar (Tag / Stage chips, no Scope), full-viewport canvas with the force-directed graph, legend at bottom
- Click a node → navigates to that note's URL → lands in stacked-columns mode

On mobile (DevTools narrow): visit `/garden/<any-note>/`, click `⊞ Graph` toggle in path log → navigates to `/garden/graph/`. Graph renders.

- [ ] **Step 14.7: Commit**

```bash
git add content/garden/graph.md layouts/garden/graph.html assets/js/garden-graph.js assets/css/main.css
git commit -m "Add /garden/graph/ standalone page (mobile fallback + deep link)"
```

---

## Task 15: CI workflow + CLAUDE.md update

**Files:**
- Modify: `.github/workflows/hugo.yaml`
- Modify: `CLAUDE.md`

- [ ] **Step 15.1: Add the linter to the workflow**

Edit `.github/workflows/hugo.yaml`. Locate the existing garden-fixtures step pair:

```yaml
      - name: Verify garden fixtures
        run: python3 tools/check_garden_fixtures.py
      - name: Run garden linter unit tests
        run: python3 -m unittest tools/test_check_garden_fixtures.py -v
```

Insert directly after, before "Verify filter-chips config":

```yaml
      - name: Verify garden links
        run: python3 tools/check_garden_links.py
      - name: Run garden links linter unit tests
        run: python3 -m unittest tools/test_check_garden_links.py -v
```

- [ ] **Step 15.2: Update `CLAUDE.md` — Commands section**

Find the Commands section. After the line:

```
- `python3 -m unittest tools/test_check_garden_fixtures.py -v` — garden linter unit tests (CI gate)
```

Insert:

```
- `python3 tools/check_garden_links.py` — garden internal-link linter (CI gate)
- `python3 -m unittest tools/test_check_garden_links.py -v` — garden links linter unit tests (CI gate)
```

- [ ] **Step 15.3: Update `CLAUDE.md` — Architecture section**

In the "JS pipeline" subsection, replace:

```
`assets/js/index.js` is bundled by Hugo's `js.Build` (esbuild) into `js/bundle.<hash>.js`, minified, fingerprinted, and loaded with `defer`. Entry imports `toggle-theme.js`, `nav.js` (TOC scroll-spy via `IntersectionObserver`), `essay.js`, and `garden.js`. Both `essay.js` and `garden.js` import the shared `filter-chips.js` module (multi-dim AND filter behavior). Each page-level module guards on its own selector (`.essay-body || .essay-grid` / `.garden-grid || .garden-note`) and bails on irrelevant pages.
```

with:

```
`assets/js/index.js` is bundled by Hugo's `js.Build` (esbuild) into `js/bundle.<hash>.js`, minified, fingerprinted, and loaded with `defer`. Entry imports `toggle-theme.js`, `nav.js` (TOC scroll-spy via `IntersectionObserver`), `essay.js`, `garden.js`, `garden-stack.js`, and `garden-graph.js`. Both `essay.js` and `garden.js` import the shared `filter-chips.js` module (multi-dim AND filter behavior). `garden-stack.js` runs the eager-Matuschak stacked-column app (click intercept → fetch → DOMParser → append; URL synced to `?stack=`); `garden-graph.js` mounts the d3-force graph (panel slide-in on desktop, separate `/garden/graph/` page on mobile). The two coordinate via the `garden:stack-changed` custom event; neither imports the other. d3-force is vendored at `assets/js/vendor/d3-force.min.js` (no npm) and lazy-imported on first graph open. Each page-level module guards on its own selector and bails on irrelevant pages.
```

In the "Content & layouts" subsection, under Layouts, find the garden line:

```
- `layouts/garden/{list,single,rss.xml}.html` — garden index (topic-map sections + Other notes + multi-dim filter strip), single note page (single template, flavor-routed metadata strip), per-section RSS feed.
```

replace with:

```
- `layouts/garden/{list,single,graph,rss.xml}.html` — garden index (topic-map sections + Other notes + multi-dim filter strip + ⊞ Graph toggle), single note page (single template wrapped in `.garden-stack` for Matuschak-style retrieval), `/garden/graph/` standalone page (mobile fallback + deep link), per-section RSS feed.
```

Under Partials, after the existing garden partials, insert:

```
  - `garden/path-log.html` (sticky breadcrumb at top of stack container; "N in stack · clear · ⊞ Graph"; populated by JS as columns append)
  - `garden/links-section.html` (outgoing-links + backlinks at column bottom; computed from build-time graph data; titles only, no snippet preview)
  - `garden/graph-data.html` (build-time data partial — walks all garden pages, extracts internal links via `findRE`, classifies edges by `topic_map` membership, returns JSON; `partialCached`)
  - `garden/graph-panel.html` (side-panel scaffolding; empty until `garden-graph.js` mounts)
```

- [ ] **Step 15.4: Update `CLAUDE.md` — Project status section**

Locate the "Project status" section. Add a new "Phase 4 complete" subsection after the last completed phase:

```
**Phase 4 — garden interactions complete (2026-05-08).** Eager Matuschak-style stacked-column retrieval (`garden-stack.js`): every garden note page is column 1 from load, path log sticky at top, internal `/garden/` link clicks fetch + DOMParser-extract `<article>` and append a column with scroll-snap focus, URL synced as `?stack=a,b,c`, deep links restore stack on load, click-on-existing re-focuses, clear/Esc collapses to URL note. First-time consent banner on 1→2 expansion stores choice as `path-log-consent` (yes/session/no); visited slugs persist to localStorage or sessionStorage based on consent. Outgoing-links + backlinks at the bottom of every column (`partials/garden/links-section.html`) computed from the same shared graph data. Force-directed graph (`garden-graph.js` + vendored d3-force at `assets/js/vendor/d3-force.min.js`, no npm): side panel on desktop with slide-in transform, ~320px; toggle in path log + index filter strip; tag/stage filter chips inside; all/1-hop/2-hop local mode on note pages; bold-stroke "in stack" markers driven by `garden:stack-changed` event; reduced-motion runs simulation 300 ticks then freezes. Mobile (≤720px): stack collapses to single-column, links navigate normally, panel hidden, graph toggle navigates to `/garden/graph/` standalone page. New CI gate `tools/check_garden_links.py` validates every internal `/garden/<slug>/` reference resolves to a non-draft fixture. Fixture set extended with ~27 internal links across 13 of 14 notes (one deliberate orphan: `nguyen-2020-games-as-art`); insertion is filler-only (lorem-ipsum sentences with markdown links dropped in), no authored prose.
```

- [ ] **Step 15.5: Update Project status — remaining slices**

In the "remaining slices" list, remove the Phase 4 line. Update the list to reflect Phase 4 done.

- [ ] **Step 15.6: Build, run all linters**

Run:

```bash
python3 tools/check-contrast.py
python3 tools/check_fixtures.py
python3 -m unittest tools/test_check_fixtures.py -v
python3 tools/check_garden_fixtures.py
python3 -m unittest tools/test_check_garden_fixtures.py -v
python3 tools/check_garden_links.py
python3 -m unittest tools/test_check_garden_links.py -v
python3 tools/check_filter_chips_config.py
python3 -m unittest tools/test_check_filter_chips_config.py -v
hugo --minify
```

Expected: every command exits 0; final `hugo --minify` produces `public/`.

- [ ] **Step 15.7: Commit**

```bash
git add .github/workflows/hugo.yaml CLAUDE.md
git commit -m "Wire garden-links linter into CI; update CLAUDE.md for Phase 4"
```

---

## Task 16: Final acceptance walkthrough + merge

- [ ] **Step 16.1: Run the full QA checklist**

In a desktop browser at `hugo server --buildDrafts`:

1. Visit `/garden/` → graph toggle visible; topic-map sections render; filter chips work
2. Click `⊞ Graph` → panel slides in; graph renders; bold-stroke nothing (no stack on index)
3. Click a node in the graph → navigates to that note's URL
4. On the note page: panel still open (sessionStorage); bold-stroke marks the current note
5. Click an internal link in body → second column appends; consent banner shows; URL `?stack=`
6. Choose "Just this session" → banner disappears; sessionStorage `garden-path-log` populated
7. Click another internal link → 3 columns; bold-stroke now marks all 3
8. Click already-stacked note title in path log → re-focuses, no duplicate
9. Press Esc with focus inside panel → panel closes
10. Press Esc with focus outside panel and stack ≥ 2 → stack collapses to column 1
11. Click `clear` → stack collapses
12. Visit `/garden/<slug>/?stack=foo,bar` directly → 3 columns, deep link restored
13. Force a 404 by editing URL: `?stack=fake-slug` → fake slug silently dropped, URL rewritten
14. Visit `/garden/graph/` directly → graph renders full-viewport
15. Resize to mobile width: visit `/garden/<slug>/` → single column; toggle goes to `/garden/graph/`
16. Theme toggle: cycle light/dark/system — graph renders correctly in all
17. Reduced-motion (DevTools "Emulate prefers-reduced-motion: reduce"): graph renders statically; column scroll-snap is instant; panel transition disabled

- [ ] **Step 16.2: Final lint + build**

```bash
python3 tools/check-contrast.py
python3 tools/check_garden_links.py
python3 -m unittest discover tools -p 'test_*.py' -v
hugo --minify
```

Expected: all green.

- [ ] **Step 16.3: Merge to master**

```bash
git checkout master
git merge --no-ff phase-4-garden-interactions -m "Merge phase-4-garden-interactions: stacked columns, path log, backlinks, graph view"
```

- [ ] **Step 16.4: Push (only if user requests)**

Do not push without explicit user confirmation. Report PR-ready state.

---

## Self-review checklist

- [ ] **Spec coverage:** every section of the spec maps to a task above
  - §3 architecture → Tasks 4, 5, 6, 7, 11, 12, 13, 14
  - §4 linter → Tasks 1, 2, 15
  - §5 stack interaction → Tasks 7, 8, 9, 10
  - §6 graph view → Tasks 11, 12, 13, 14
  - §7 fixture extension → Task 3
  - §8 perf budget → addressed via vendoring (Task 11) + lazy import (Task 13)
  - §9 a11y → integrated throughout (focus management Task 8, path-log ARIA Task 6, graph SVG roles Task 13, reduced motion Task 13)
  - §10 implementation order → matches the task numbering with two consolidations: 15 covers steps 11+12; 13 covers steps 8+9
- [ ] **No placeholders:** every code block is complete; no "TBD", "TODO", "fill in"
- [ ] **Type consistency:** function names match across tasks (`appendColumn`, `clearStack`, `focusColumn`, `rebuildGraph`); module imports relative (`./vendor/d3-force.min.js`); CSS class names match (`.garden-stack`, `.garden-stack-columns`, `.garden-column`, `.garden-graph-panel`, `.garden-graph-page`); event name `garden:stack-changed` consistent in both modules
- [ ] **Open questions from spec §11:** flagged in the relevant task for in-flight decision; not deferred without rationale

---

*End of plan.*
