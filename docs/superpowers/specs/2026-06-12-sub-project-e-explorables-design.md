# Sub-project E — Explorable explainables

**Status:** designed 2026-06-12. No plan yet. Ships as a single slice.

**Parent context.** Phase 3 sub-project E per [`project_phase_3_decomposition`](../../../.claude/memory/project_phase_3_decomposition.md). Last open Phase 3 piece. Carries the forward-compat hook the multi-target export spec §7 sketched (PDF/Word skip widget blocks). Resolves parent spec [`2026-05-03-personal-site-design.md`](2026-05-03-personal-site-design.md) §15.3 ("Per-page bundle JS — exact convention for essays with interactive widgets").

**Driver.** Groundwork-first. No real essay in mind. Ships infrastructure + one fixture; real explorable essays land in follow-up slices.

---

## 1. Scope

### In-scope deliverables

1. Runtime `assets/js/explorables/runtime.js` — `registerWidget(id, mountFn)` + auto-mount on `DOMContentLoaded`.
2. Two library widget classes — `ReactiveValue` and `ReactiveChart`, importable from `assets/js/explorables/lib/`. Hand-rolled SVG; no d3.
3. Per-essay JS bundle convention — each essay with `has_widgets: true` gets a dynamic `js.Build` entry from `assets/js/explorables/<slug>/index.js`. Output `explorables-<slug>.<hash>.js`, page-narrow loading.
4. Shortcode upgrade — `{{< widget id="..." [label="..."] >}}` emits a server-rendered no-JS caption + a mount target div. Supersedes the existing 1-line stub in `layouts/shortcodes/widget.html`.
5. 28th linter pair — `tools/check_explorables.py` + `tools/test_check_explorables.py`. Coupling-only, source-side.
6. CSS §49 — `.explorable*` selectors + slider cross-browser chrome. No new color tokens.
7. One fixture — `content/essays/example-explorables/` exercising both library kinds + one bespoke widget.
8. Smoke-test addition — `tools/check_smoke.py` GETs `/essays/example-explorables/` and asserts the three `data-widget-id` attributes plus the page-narrow bundle `<script>` tag.

### Out of scope (queued — see §10 Follow-ups)

- Org-side authoring (`#+begin_explorable` block in ox-hugo handler).
- Third library kind (step-through animator).
- Multi-series ReactiveChart.
- Static-screenshot fallback for PDF/Word.
- ReactiveChart screen-reader text alternative (sampled-data prose).
- Runtime split into shared bundle entry.
- Cross-widget state coordination.
- Render-time browserless headless paint check.

### Out of scope (closed — no follow-up)

- Widget framework / React-style component model. Vanilla JS classes + imperative register stays forever unless a future spec re-opens.
- A widget gallery page (`/demos/explorables/`).
- A WYSIWYG widget builder.

### Constraints carried in (from parent spec §1)

- **No AI text or images in widget prose / data.** AI permitted for widget *code* per parent spec §1 (explicit exemption: "code for interactive explorables").
- **No npm.** Stays vanilla JS + Hugo's `js.Build` esbuild. Hand-rolled SVG charts; no charting library.
- **WCAG AA on widget chrome; AAA on widget text.** Native `<input type="range">` for keyboard a11y. ARIA live regions on reactive output. No new color tokens — uses existing site palette.

---

## 2. Architecture

### File layout

```
assets/js/explorables/
├── runtime.js                 # registerWidget(id, fn) + DOMContentLoaded sweep
├── lib/
│   ├── _base.js               # internal helpers (buildControls, clamp, scale)
│   ├── reactive-value.js      # ReactiveValue class
│   └── reactive-chart.js      # ReactiveChart class
└── <essay-slug>/
    └── index.js               # imports runtime + lib kinds; calls registerWidget(id, fn)
```

### Bundle pipeline

`layouts/partials/scripts.html` adds a 13th entry — a *dynamic loop* over essays. Modeled on the existing 12 fixed entries (see CLAUDE.md "JS pipeline — multi-entry bundling" table).

```go-html-template
{{ range where site.RegularPages "Section" "essays" }}
  {{ if .Params.has_widgets }}
    {{ $slug := .File.ContentBaseName }}
    {{ with resources.Get (printf "js/explorables/%s/index.js" $slug) }}
      {{ $opts := dict "minify" true "targetPath" (printf "explorables-%s.js" $slug) }}
      {{ $bundle := . | js.Build $opts | fingerprint | resources.PostProcess }}
      {{ if eq $.Permalink $.Page.Permalink }}
        <script src="{{ $bundle.RelPermalink }}" integrity="{{ $bundle.Data.Integrity }}" crossorigin="anonymous"></script>
      {{ end }}
    {{ end }}
  {{ end }}
{{ end }}
```

Implementation note: the page-narrow `<script>` emit condition above (`eq $.Permalink $.Page.Permalink`) is sketch-level — final implementation may compare `.File.ContentBaseName` against the current page directly. The plan resolves the exact comparison.

The `<script>` tag emits **only** when the currently-rendering page IS the essay whose bundle was just built. Matches existing per-section narrowing (see `entry-poetry.js` which page-narrows to `works/<poem>/`).

### Bundle contents

Each per-essay bundle inlines:

- `runtime.js`
- Any imported library kinds (esbuild tree-shakes unused ones)
- The per-essay `index.js`

No cross-bundle sharing in v1 (intentional). Duplication cost is sub-KB per essay; revisit when N>3 widget-bearing essays exist (queued as §10 follow-up 6).

### Runtime contract — `assets/js/explorables/runtime.js`

```js
const registry = new Map();

export function registerWidget(id, mountFn) {
  if (registry.has(id)) {
    console.warn(`[explorables] duplicate registerWidget for id="${id}"`);
  }
  registry.set(id, mountFn);
}

document.addEventListener('DOMContentLoaded', () => {
  for (const el of document.querySelectorAll('[data-widget-id]')) {
    const id = el.getAttribute('data-widget-id');
    const fn = registry.get(id);
    if (!fn) {
      console.warn(`[explorables] no widget registered for id="${id}"`);
      continue;
    }
    el.removeAttribute('data-widget-fallback');  // hides the static caption via CSS
    try {
      fn(el);
    } catch (err) {
      console.error(`[explorables] mount failed for "${id}":`, err);
    }
  }
});
```

**Dispose lifecycle:** not implemented in v1. Essays are static; full page unload disposes everything. Add only if a widget grows resource-hungry.

**Module side-effects are intentional.** Imports → `registerWidget` calls at top level → runtime sweeps after `DOMContentLoaded`. No "register all" wrapper, no React-style declarative tree.

### CLAUDE.md update

The "JS pipeline — multi-entry bundling" table gains a 13th row:

| Entry | Output | Loaded on | Notes |
|---|---|---|---|
| `js/explorables/<slug>/index.js` (dynamic loop) | `explorables-<slug>.<hash>.js` (~few KB) | `.Section == "essays"` AND `.Kind == "page"` AND `.Params.has_widgets` AND `.File.ContentBaseName == <slug>` | inlines runtime + library kinds; per-essay |

---

## 3. Authoring API

### Shortcode — `{{< widget id="..." [label="..."] >}}`

```go-html-template
{{- /* layouts/shortcodes/widget.html */ -}}
{{- $id := .Get "id" -}}
{{- $label := or (.Get "label") "Interactive figure" -}}
<div data-widget-id="{{ $id }}"
     data-widget-fallback
     role="figure"
     aria-label="{{ $label }}">
  <p class="widget-fallback">{{ $label }} — enable JavaScript to view.</p>
</div>
```

- `id` is required. Linter (§7) enforces non-empty + per-page uniqueness.
- `label` is optional but recommended — drives `aria-label` AND the no-JS caption text.
- The runtime removes `data-widget-fallback` on successful mount. CSS hides `.widget-fallback` when `[data-widget-id]:not([data-widget-fallback])`.

Supersedes the current `widget.html` stub. One existing fixture references the stub today: `content/essays/example-one/index.md:59` calls `{{< widget src="example-widget" >}}` (the old stub took `src=`; the current `.Get "id"` line silently ignored it). The plan must pick one of:

- **(a) Update example-one to the new contract.** Change the shortcode to `{{< widget id="example-widget" label="Example widget" >}}` and add `assets/js/explorables/example-one/index.js` with a matching `registerWidget('example-widget', ...)` call (any minimal mount fn — the existing fixture's only purpose is exercising frontmatter shape). Two fixtures end up carrying the contract; satisfies [[feedback-deferred-features-stay-visible]].
- **(b) Drop the widget from example-one.** Remove the shortcode call and flip `has_widgets: false` in its frontmatter. Smaller scope; `example-explorables` is the sole carrier. Loses one round-trip exerciser.

Recommendation: **(a)**, mirroring the deferred-stub-stays-visible principle. The added per-essay JS file is ~10 lines.

### Mount API — `assets/js/explorables/<slug>/index.js`

```js
import { registerWidget } from '../runtime.js';
import { ReactiveValue } from '../lib/reactive-value.js';
import { ReactiveChart } from '../lib/reactive-chart.js';

registerWidget('gaussian', (el) =>
  new ReactiveChart(el, {
    inputs: [
      { name: 'sigma', min: 0.1, max: 3, default: 1, step: 0.1 },
      { name: 'mu',    min: -3,  max: 3, default: 0, step: 0.1 },
    ],
    fn: (x, { sigma, mu }) =>
      Math.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) / (sigma * Math.sqrt(2 * Math.PI)),
    x: [-5, 5],
    y: [0, 0.8],
  })
);

registerWidget('k-square', (el) =>
  new ReactiveValue(el, {
    inputs: [{ name: 'k', min: 0, max: 10, default: 2, step: 0.1 }],
    render: ({ k }) => `f(k) = ${(k * k).toFixed(2)}`,
  })
);

registerWidget('spinner', (el) => {
  const canvas = document.createElement('canvas');
  canvas.width = 200; canvas.height = 200;
  el.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let t = 0;
  const tick = () => {
    ctx.clearRect(0, 0, 200, 200);
    ctx.beginPath();
    ctx.arc(100, 100, 60, t, t + Math.PI);
    ctx.stroke();
    t += 0.02;
    if (!reduced) requestAnimationFrame(tick);
  };
  tick();
});
```

**Contract:** `registerWidget(id, fn)` takes a string id (must match a `{{< widget id=... >}}` on the page) and a mount fn `(el: HTMLElement) => void`. The fn owns `el`'s contents post-mount.

---

## 4. Library widgets

Hand-rolled in `assets/js/explorables/lib/`. Internal helpers shared via `_base.js`.

### `ReactiveValue`

```ts
new ReactiveValue(el, {
  inputs: Array<{
    name: string;
    min: number;
    max: number;
    default: number;
    step?: number;        // default 1
  }>,
  render: (state: Record<string, number>) => string,
  format?: (state: Record<string, number>) => HTMLElement;   // optional rich output
})
```

**DOM produced** (illustrative):

```html
<div class="explorable explorable-value">
  <div class="explorable-controls">
    <label>
      <span class="explorable-label">sigma</span>
      <input type="range" min="0.1" max="3" step="0.1" value="1">
      <output aria-live="polite">1.0</output>
    </label>
    <!-- repeat per input -->
  </div>
  <p class="explorable-output" aria-live="polite">f(k) = 4.00</p>
</div>
```

- `<output aria-live="polite">` per slider — current numeric value, screen-reader-announced on change.
- Final `.explorable-output` — result of `render(state)`. Also `aria-live="polite"`.
- Wire-up: `input` event on each `<input type=range>` → recompute state → update both per-slider output and final output.

### `ReactiveChart`

```ts
new ReactiveChart(el, {
  inputs: Array<{...}>,                       // same shape as ReactiveValue
  fn: (x: number, state: Record<string, number>) => number,
  x: [min: number, max: number],
  y: [min: number, max: number],
  samples?: number;                           // default 100
  width?: number;                             // default 480
  height?: number;                            // default 200
  xLabel?: string;
  yLabel?: string;
})
```

**DOM produced**:

```html
<div class="explorable explorable-chart">
  <div class="explorable-controls"> <!-- same as above --> </div>
  <figure class="explorable-figure">
    <svg viewBox="0 0 480 200"
         preserveAspectRatio="xMidYMid meet"
         role="img"
         aria-label="<yLabel> as a function of <xLabel>">
      <g class="explorable-axes"> <!-- x/y axis lines + 4 tick labels --> </g>
      <path class="explorable-line" d="..." />
    </svg>
    <figcaption class="explorable-axes-caption">x: -5 to 5, y: 0 to 0.8</figcaption>
  </figure>
</div>
```

- One `<path>` per chart. Multi-series queued as §10 follow-up 3.
- Axis chrome: two static `<line>` + four `<text>` ticks (min / mid-low / mid-high / max). No grid lines.
- Re-render: on input change, recompute samples → rebuild `d`. No animation in v1; raw replace.
- Responsive via `viewBox` + `preserveAspectRatio`; scales to container at all breakpoints including 960px half-screen per [[feedback-test-at-half-screen-1080p]].

### Shared base — `assets/js/explorables/lib/_base.js`

Internal (no public export). Provides:

- `buildControls(inputs, onChange)` → returns `{ controlsEl: HTMLElement, getState: () => Record<string, number> }`. Used by both library kinds.
- `clamp(v, min, max)`, `scale(v, [inMin, inMax], [outMin, outMax])` — axis math helpers.

---

## 5. No-JS / accessibility / cross-format

### No-JS fallback

Static caption inside the mount div (server-rendered by the shortcode — §3). CSS hides the caption once the runtime removes `data-widget-fallback`.

```css
.widget-fallback {
  font-style: italic;
  color: var(--color-ink-soft);
  padding: var(--space-3);
  border: 1px dashed var(--color-steel);
  border-radius: var(--radius-sm);
  text-align: center;
}
[data-widget-id]:not([data-widget-fallback]) .widget-fallback {
  display: none;
}
```

Uses a class + attribute selector pair (not the `hidden` attribute) — avoids the `[hidden]` cascade gotcha from CLAUDE.md's filter-chips note.

### Accessibility

- **Mount target:** `role="figure"` + `aria-label`. Screen-reader announces the figure on entry.
- **Slider chrome:** native `<input type="range">`. Keyboard focus, arrow-key step, Home/End jump, screen-reader read-out work for free. Hand-rolled focus ring (CSS §49) overrides UA inconsistencies.
- **Per-slider `<output aria-live="polite">`:** screen-reader announces current numeric value on change.
- **Reactive value `.explorable-output`:** `aria-live="polite"`. Re-read on change; browser throttles automatically.
- **Reactive chart SVG:** `role="img"` + `aria-label`. AT users hear the figure name but not the live curve. Text-alt is queued (§10 follow-up 5).
- **Contrast:** all consumed tokens already in the 9-pairing set checked by `tools/check-contrast.py`. No new pairings.
- **Reduced motion:** library kinds don't animate (chart re-renders via path swap). Bespoke widgets that animate MUST honor `prefers-reduced-motion: reduce` — author responsibility; the fixture demonstrates.

### Cross-format

- **PDF / Word:** per multi-target export spec §7 — blocks tagged `:explorable:` (or doc-level `#+explorable: t`) drop from PDF/Word output via the org-side filter rule in `pdf.el` / `word.el`. Site-side spec only acknowledges. No site code change.
- **RSS:** essays feed uses `.Summary`. Widget shortcodes near the top of an essay may show their static caption in the summary. Accept; revisit if a real essay surfaces friction.
- **Print:** no print-specific CSS today. Widgets print as their interactive web rendering minus interaction (sliders frozen at last state). Don't add print rules until an author actually prints.

### Crash safety

Runtime's `try/catch` per `fn(el)` call → `console.error` with widget id; continues iteration. One broken widget never breaks others or the page.

---

## 6. CSS scoping (§49)

New section appended to `assets/css/main.css`. Site-wide cascade; no Shadow DOM. Class names follow site convention (semantic dashed names; no BEM).

**Selectors:**

```
.explorable
.explorable-controls
.explorable-controls label
.explorable-label
.explorable-controls input[type="range"]
.explorable-controls input[type="range"]:focus-visible
.explorable-controls output
.explorable-output
.explorable-figure
.explorable-line
.explorable-axes
.explorable-axes-caption
.widget-fallback
```

**Tokens consumed (no new tokens):** `--color-burgundy`, `--color-ink-soft`, `--color-stone`, `--color-steel`, `--space-3`, `--space-6`, `--radius-sm`, `--font-ui`, `--font-mono`.

**Slider chrome — cross-browser.** Native `<input type="range">` has the most fragmented styling surface on the web. Hand-roll both UA prefixes (webkit + moz):

```css
.explorable-controls input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
}
.explorable-controls input[type="range"]::-webkit-slider-runnable-track,
.explorable-controls input[type="range"]::-moz-range-track {
  height: 4px; background: var(--color-steel); border-radius: 2px;
}
.explorable-controls input[type="range"]::-webkit-slider-thumb,
.explorable-controls input[type="range"]::-moz-range-thumb {
  -webkit-appearance: none; appearance: none;
  width: 16px; height: 16px; background: var(--color-burgundy);
  border: none; border-radius: 50%; cursor: pointer;
}
.explorable-controls input[type="range"]:focus-visible::-webkit-slider-thumb,
.explorable-controls input[type="range"]:focus-visible::-moz-range-thumb {
  outline: 2px solid var(--color-burgundy);
  outline-offset: 2px;
}
```

**Layout.** `.explorable` is `display: block` with `margin: var(--space-6) 0` — same rhythm as `<figure>`. `.explorable-controls` is `display: flex; gap: var(--space-3); flex-wrap: wrap`. SVG scales via `viewBox`; no media queries needed sub-960px.

**Dark mode.** All consumed tokens already have dark-mode duplicates. No new dark-mode rules.

**Section index update.** Top-of-file index in `main.css` gets `§49 — explorables`.

---

## 7. Linter + `has_widgets` coupling

### 28th linter pair — `tools/check_explorables.py` + `tools/test_check_explorables.py`

Coupling-only, source-side (parses `content/essays/<slug>/index.md` + `assets/js/explorables/<slug>/index.js`). No rendered-HTML parsing. Six rules:

1. **`has_widgets` ↔ shortcode presence.** Every essay with `has_widgets: true` must contain at least one `{{< widget ... >}}` shortcode in its body; every essay containing a `widget` shortcode must declare `has_widgets: true`. (Mirrors `check_math.py`'s `has_math` coupling.)
2. **Widget id required.** Every `{{< widget ... >}}` must have a non-empty `id` parameter.
3. **Widget ids unique per page.** No two `widget` shortcodes in one essay share an `id`.
4. **Per-essay JS exists.** Any essay with `has_widgets: true` must have `assets/js/explorables/<slug>/index.js` on disk.
5. **Every widget id is registered.** Each `id` declared in a markdown shortcode must appear in a `registerWidget(<quote><id><quote>, ...)` call in that essay's `index.js` — quote-agnostic (single or double). Regex match; strips `// ...` and `/* ... */` first to avoid comment false-positives.
6. **No orphan `registerWidget`.** Every `registerWidget` call in `assets/js/explorables/<slug>/index.js` must correspond to a `{{< widget id="<id>" >}}` in the markdown.

**Runner contract:** `check_explorables.run(repo_root) -> (rc, errors)` — parity with sibling linters per the [[project-tier-4-complete]] follow-up pattern.

### CI integration

`.github/workflows/hugo.yaml` linter sequence gains `Check explorables coupling` + the sibling test step. Total step count: 67 → 69. No new deps (stdlib only).

### `tools/ci-local.sh`

Append the new linter + sibling-test invocations so [[feedback-always-run-ci-locally]] catches drift before push.

### `has_widgets` semantics — clarified

- **Reader (site, this slice):** `scripts.html` partial uses it to gate per-essay bundle emission. The `<script>` tag is only emitted when the current page is the essay whose bundle was just built.
- **Reader (future, multi-target):** future `pdf.el` / `word.el` use it as a *hint*. The authoritative per-block filter is the `:explorable:` tag (multi-target export spec §7 contract).
- **Writer (deferred to §10 follow-up 1):** the org-side publish handler will set `has_widgets: true` when the source org file contains a widget shortcode emission or a `#+begin_explorable` block. Until then, value is hand-authored in the markdown frontmatter (fixtures + any future hand-written essays).

### Out-of-scope linter checks (documented; not implemented)

- Render-time check that each registered widget's mount fn paints visibly. Requires headless browser; expensive. Manual QA only.
- Cross-essay widget id uniqueness — runtimes are page-narrow; not needed.
- Contrast check on widget JS that injects raw `style="color:..."` — covered by the deferred parent-spec §13 linter ("WCAG contrast on non-HTML sources").

---

## 8. Fixture — `content/essays/example-explorables/`

Layout:

```
content/essays/example-explorables/
└── index.md
assets/js/explorables/example-explorables/
└── index.js
```

**Frontmatter** (all 15 essay-fixture-required keys per `tools/check_fixtures.py`):

```yaml
title: "Example: explorables"
date: 2026-06-12
lastmod: 2026-06-12
draft: false
summary: "Filler essay exercising the explorables runtime — two library widgets and one bespoke widget."
tags: [example, explorables]
series: ""
series_order: 0
toc: true
has_sidenotes: false
has_citations: false
has_footnotes: false
has_math: false
has_widgets: true
has_video_sync: false
```

**Body** (filler-only per [[feedback-filler-text-only]]):

```markdown
## A reactive value

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
ut labore et dolore magna aliqua.

{{< widget id="k-square" label="Square of k" >}}

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
commodo consequat.

## A reactive chart

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat
nulla pariatur.

{{< widget id="gaussian" label="Gaussian curve" >}}

Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit
anim id est laborum.

## A bespoke widget

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque
laudantium.

{{< widget id="spinner" label="Rotating spinner" >}}

Totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae
vitae dicta sunt explicabo.
```

**`index.js`** is the verbatim file from §3.

### What this fixture proves end-to-end

- Shortcode emits mount target + no-JS caption.
- Page-narrow bundle emission (only this essay loads `explorables-example-explorables.<hash>.js`).
- Runtime sweeps + mounts on `DOMContentLoaded`.
- Both library kinds render with controls + reactive output.
- Bespoke widget (raw canvas) mounts via the same lifecycle.
- Linter passes (28th pair green on this fixture).
- Reduced-motion: the bespoke spinner respects it (the `if (!reduced) requestAnimationFrame(tick)` guard).

### Smoke-test addition

`tools/check_smoke.py` extends its essay assertions:

```python
# inside the smoke checks for /essays/example-explorables/
assert b'data-widget-id="k-square"' in body
assert b'data-widget-id="gaussian"' in body
assert b'data-widget-id="spinner"' in body
assert b'<script src="/explorables-example-explorables.' in body
```

---

## 9. Risks + open questions for the plan

These don't block the spec but should be resolved when the implementation plan is written:

1. **Hugo `js.Build` in a dynamic loop — verify it works.** The existing 12 entries are static-string `resources.Get`. The dynamic-iteration pattern should be straightforward (Hugo supports `range` over pages + `resources.Get` per iteration) but hasn't been used here before. Plan should validate against a minimal repro before writing the full partial.
2. **Page-narrow `<script>` emit predicate.** The §2 sketch uses `eq $.Permalink $.Page.Permalink`; final form likely compares `.File.ContentBaseName` against the current page's. Plan resolves.
3. **Esbuild's tree-shaking on side-effect-bearing `registerWidget` calls.** Top-level `registerWidget(...)` calls have side effects (mutate the runtime's registry). Esbuild treats top-level side-effects as roots; tree-shaking only drops *unreferenced* exports. The library kinds are imported + instantiated, so they're roots too. Verify no surprise drops in a minimal repro before declaring v1.
4. **`widget` shortcode already exists.** Current `layouts/shortcodes/widget.html` is `<div data-widget data-widget-id="{{ .Get "id" }}"></div>` (note: `data-widget` attribute, not `data-widget-id` selector — the existing stub is *almost* right but uses an extra deprecated attribute). Plan replaces the file outright; grep `content/` for any existing usage that depends on `data-widget` (likely none — parent spec §6.3 lists `widget` as a deferred-feature stub only present as fixture exercise).
5. **CSP / SRI parity.** Existing entries use `fingerprint` + `Data.Integrity` + `crossorigin="anonymous"`. Per-essay bundles must emit the same `integrity=` + `crossorigin=` attributes.

---

## 10. Follow-ups (queued; not in this slice)

1. **Org-side authoring path.** `#+begin_explorable` block → `{{< widget id=... >}}` emission via ox-hugo handler. Per-essay JS authoring colocation question: org-side colocated with essay subtree, OR site-side `assets/js/explorables/<slug>/`. **Trigger:** first real explorable essay needs export. Filed during section-1 review of this brainstorm at author's request.
2. **Third library kind: step-through animator.** Next/prev button walking labeled stages. **Trigger:** second bespoke widget that re-implements stepping.
3. **Multi-series `ReactiveChart`.** `series: [...]` field for stacking multiple `<path>` lines. **Trigger:** first real chart needing comparison data.
4. **Static-screenshot fallback for PDF/Word.** Author-supplied PNG per widget; ox-* handlers slot it in. **Trigger:** first real essay that needs widget representation in PDF/Word (not just exclusion).
5. **Screen-reader text alternative for `ReactiveChart`.** Sampled-data prose summary ("at x=0, y=0.4..."). **Trigger:** a11y review of first real chart-bearing essay.
6. **Runtime split into shared bundle entry.** Once N>3 widget-bearing essays exist, share the runtime + library kinds across them. **Trigger:** profiling shows duplication cost > 10 KB total.
7. **Cross-widget state coordination.** One slider driving multiple charts. **Trigger:** first essay that needs it. Pattern: export a shared state store from per-essay `index.js`.
8. **Render-time linter** (browserless headless paint check). **Trigger:** author hits a bug where mount fn silently no-ops in CI but works locally.

---

## 11. Pointers

- **Parent spec:** [`2026-05-03-personal-site-design.md`](2026-05-03-personal-site-design.md) §1, §3.2, §15.3.
- **Phase 3 decomposition:** [`project_phase_3_decomposition`](../../../.claude/memory/project_phase_3_decomposition.md).
- **Multi-target export spec §7 (forward-compat sketch):** [`2026-05-13-multi-target-export-design.md`](2026-05-13-multi-target-export-design.md).
- **CLAUDE.md "JS pipeline — multi-entry bundling"** table — pattern for the 13th dynamic entry.
- **Roadmap row:** [`2026-06-07-polish-and-bugfix-roadmap.md`](2026-06-07-polish-and-bugfix-roadmap.md) Tier 8.1.
