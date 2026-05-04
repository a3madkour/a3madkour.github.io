# Foundation Cleanup + Visual Identity Implementation Plan

> **Status (2026-05-04): COMPLETE.** All 14 tasks executed and merged to `master` via the `rebuild/foundation-and-identity` branch (subagent-driven execution, with per-task spec + code review). Phase 2 (Essays grid, Garden tiles + graph, Research themes, Works pages, Library, Pagefind search, plus the per-section content widgets) is the next chunk — see `docs/superpowers/specs/2026-05-03-personal-site-design.md` §14 for the phase breakdown.
>
> Carried-forward items to revisit when starting Phase 2:
> - `actions/checkout@v6` and `actions/configure-pages@v6` in `.github/workflows/hugo.yaml` may not resolve (latest tags are v4 / v5); intentionally left for the user to confirm.
> - Petrona italic only loaded at weight 400 — Phase 2 may want italic 600/700 for emphasized headings (extend the Google Fonts URL in `layouts/partials/head.html`).
> - `::selection` is 4.68:1 in dark mode (acceptable per spec accent rules; flagged for future thought).
> - RSS orange `#ee7e2c` is 2.36:1 on light stone (universal-recognition exception per spec).
> - Bluesky URL in the footer is the placeholder `https://bsky.app/` — replace with a real handle when the user is ready.
>
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current Tailwind v4 CSS pipeline with hand-rolled CSS implementing the locked visual identity (Petrona/Inter/JetBrains Mono on cool stone with burgundy/steel accents), update the top navigation to match the new content architecture, and add a contrast-checker tool — without breaking the existing Hugo build or content. After this plan, the site renders with the new look on the `rebuild/foundation-and-identity` branch, ready for section work in Phase 2.

**Architecture:** Single hand-rolled `assets/css/main.css` consumed by Hugo's `resources.Get` + `minify` + `fingerprint` (no PostCSS, no Node). Theme toggle migrates from a `.dark` class to a `data-theme` attribute with three-state cycle (light → dark → system). `tools/check-contrast.py` parses the CSS and asserts WCAG 2.1 ratios per spec §2's accessibility policy. Layouts use semantic class names (`.site-header`, `.reading-column`, etc.) styled by `main.css` rather than utility classes.

**Tech Stack:** Hugo extended ≥0.148, vanilla CSS, vanilla JS bundled by `js.Build`, Python 3 stdlib (contrast checker only), Google Fonts.

**Reference docs:**
- Spec: `docs/superpowers/specs/2026-05-03-personal-site-design.md` (especially §2 visual identity, §3 nav, §5.9 theme toggle, §11 CI gates)
- WCAG 2.1 contrast formula: https://www.w3.org/TR/WCAG21/#dfn-relative-luminance

**Branch / worktree:** `rebuild/foundation-and-identity` at `~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity`.

**Out of scope (later plans):**
- Per-section layouts: Essays grid, Garden tiles, Research themes (Phase 2 onward)
- Org-mode pipeline integration (Phase 3)
- Pagefind search, full Lighthouse CI (Phase 8)
- Full v3 homepage and About content (Phase 7 / Phase 2 respectively — this plan ships placeholders)

**Branch policy:** Do NOT push to `master`, do NOT open a PR. The user will merge by hand after review. All commits land on `rebuild/foundation-and-identity` only.

---

## File map

### Delete
- `package.json`
- `package-lock.json`
- `assets/css/compiled.css` (Tailwind build artifact; only present if previously built locally)

### Modify
- `.gitignore` — drop Node + Tailwind entries
- `.github/workflows/hugo.yaml` — remove `npm ci`, remove Tailwind build step, add Python contrast-check step
- `assets/css/main.css` — full rewrite (hand-rolled tokens + typography + components)
- `assets/js/toggle-theme.js` — migrate to `data-theme` attribute, three-state cycle, key `theme-pref`
- `assets/js/nav.js` — replace Tailwind class names in TOC active highlighting
- `layouts/_default/baseof.html` — drop Tailwind classes, semantic structure
- `layouts/_default/single.html` — semantic markup
- `layouts/_default/list.html` — semantic markup
- `layouts/404.html` — drop Tailwind classes
- `layouts/partials/head.html` — load `main.css` directly, Google Fonts for three families
- `layouts/partials/header.html` — new top nav, RSS button, theme toggle
- `layouts/partials/footer.html` — colophon line + "Words are mine; not generated" + social links
- `layouts/blog/list.html` — strip Tailwind classes (full essay grid in Phase 2)
- `layouts/blog/single.html` — strip Tailwind classes
- `content/_index.html` — placeholder hero (full v3 in Phase 7)
- `content/about/index.md` — placeholder body with role line (full About in Phase 2)

### Create
- `assets/images/icons/sun.svg` — theme toggle icon
- `assets/images/icons/rss.svg` — RSS button icon
- `tools/check-contrast.py` — WCAG contrast verifier

---

## Phase 0: Cleanup

### Task 1: Establish baseline build

**Files:** none modified — verification only.

- [ ] **Step 1: Confirm worktree is clean and on rebuild branch**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git status
git rev-parse --abbrev-ref HEAD
```

Expected:
- `git status` reports `nothing to commit, working tree clean` (the in-progress plan file may show as untracked — that's fine, it gets committed separately at the end of the plan).
- `git rev-parse` prints `rebuild/foundation-and-identity`.

- [ ] **Step 2: Run a one-time build with the current Tailwind pipeline**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
npm install && npm run hugo:build
```

Expected: `npm install` populates `node_modules/`, `npm run build:css` produces `assets/css/compiled.css`, `hugo --minify` writes to `public/`. No errors. This confirms the worktree starts from a working state. After this task, npm and Tailwind disappear.

- [ ] **Step 3: Open the homepage in a browser briefly (optional sanity check)**

```bash
hugo server --disableFastRender
```
Visit `http://localhost:1313/`, confirm the site renders with the existing pink-accent Tailwind look. `Ctrl+C` to stop.

- [ ] **Step 4: No commit — this is verification**

Continue to Task 2.

---

### Task 2: Remove npm + Tailwind files; clean .gitignore

**Files:**
- Delete: `package.json`, `package-lock.json`, `assets/css/compiled.css`
- Delete (working dir only): `node_modules/`
- Modify: `.gitignore`

- [ ] **Step 1: Delete the project files**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
rm -f package.json package-lock.json assets/css/compiled.css
rm -rf node_modules/
```

- [ ] **Step 2: Replace `.gitignore` contents**

Open `.gitignore` and replace its contents with:

```gitignore
# Hugo
public/
resources/_gen/
.hugo_build.lock

# Superpowers brainstorm artifacts
.superpowers/

# Environment variables
.env
.env.local
.env.*.local

# Operating System Files
# macOS
.DS_Store
.AppleDouble
.LSOverride
._*
.Spotlight-V100
.Trashes

# Windows
Thumbs.db
Thumbs.db:encryptable
ehthumbs.db
ehthumbs_vista.db
Desktop.ini
$RECYCLE.BIN/

# Linux
*~
.directory

# Editor directories and files
# VSCode
.vscode/
*.code-workspace

# JetBrains IDEs (IntelliJ, WebStorm, etc.)
.idea/
*.iml
*.ipr
*.iws

# Sublime Text
*.sublime-project
*.sublime-workspace

# Vim
[._]*.s[a-v][a-z]
[._]*.sw[a-p]
[._]s[a-rt-v][a-z]
[._]ss[a-gi-z]
[._]sw[a-p]
*.swp
*.swo

# Emacs
\#*\#
/.emacs.desktop
/.emacs.desktop.lock
*.elc

# Temporary files
*.tmp
*.temp
*.log
*.cache

# Misc
.sass-cache/
*.css.map
*.js.map
```

(This drops the Node/npm block, the Tailwind compiled-output block, the unused `static/css/output.css` build-outputs block, and the `coverage/` testing block. Keeps Hugo, OS, editor, and misc entries.)

- [ ] **Step 3: Verify git sees the deletions**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git status
```

Expected: `package.json`, `package-lock.json` shown as deleted; `.gitignore` shown as modified. `assets/css/compiled.css` was previously gitignored so it does not show. `node_modules/` was previously gitignored so it does not show.

- [ ] **Step 4: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add -A
git commit -m "$(cat <<'EOF'
Phase 0: Drop Tailwind/Node from project

Removes package.json, package-lock.json, and the Tailwind-built
compiled.css along with their .gitignore entries. Hugo template
references to compiled.css will be replaced in subsequent commits;
the build still completes (Hugo's `with resources.Get` skips silently
when the resource is absent, and the site is unstyled in this
intermediate state).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Remove npm + Tailwind steps from CI workflow

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Open the workflow file and remove the npm + Tailwind steps**

Open `.github/workflows/hugo.yaml`. Find the block (currently lines 49–52):

```yaml
      - name: Install Node.js dependencies
        run: "[[ -f package-lock.json || -f npm-shrinkwrap.json ]] && npm ci || true"
      - name: Build CSS (Tailwind)
        run: npm run build:css
```

Delete those four lines entirely. The next step in the workflow (`Build with Hugo`) follows directly after `Setup Pages`.

- [ ] **Step 2: Verify the rest of the workflow is intact**

Read the modified file. Confirm:
- `Install Hugo CLI` step present
- `Checkout` step present (with `submodules: recursive`, `fetch-depth: 0`)
- `Setup Pages` step present
- `Build with Hugo` step present (env `HUGO_ENVIRONMENT: production`, `--gc --minify --baseURL`)
- `Upload artifact` step uploads `./public`
- `deploy` job uses `actions/deploy-pages@v4`

- [ ] **Step 3: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add .github/workflows/hugo.yaml
git commit -m "$(cat <<'EOF'
Phase 0: Drop npm + Tailwind steps from Pages workflow

Hugo no longer needs Node — CSS is hand-rolled in Phase 1. The
contrast-check CI gate is added in Task 13.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Phase 1: Visual identity

### Task 4: Write contrast checker tool

**Files:**
- Create: `tools/check-contrast.py`

The contrast checker parses CSS custom properties from `assets/css/main.css` (light mode at `:root`, dark mode at `:root[data-theme="dark"]`), computes WCAG 2.1 relative luminance + contrast ratios for the documented pairings, and exits non-zero on violations. Python stdlib only.

This task is the failing test: it runs against the still-Tailwind-driven `main.css` and exits non-zero. Task 5 makes it pass.

- [ ] **Step 1: Create the directory and write the script**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
mkdir -p tools
```

Create `tools/check-contrast.py` with exactly this content:

```python
#!/usr/bin/env python3
"""WCAG 2.1 contrast verifier for the site palette.

Parses CSS custom properties from `assets/css/main.css` and asserts the
documented pairings (spec §2) hit their thresholds.

Exits 0 on all-pass, 1 on any violation. No third-party deps.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = REPO_ROOT / "assets" / "css" / "main.css"

# (foreground_token, background_token, min_ratio, role)
# WCAG 2.1: AAA body text = 7.0; AA body / AAA large = 4.5.
PAIRINGS = [
    ("color-ink",      "color-stone", 7.0, "body text on background"),
    ("color-ink-soft", "color-stone", 4.5, "secondary text on background"),
    ("color-burgundy", "color-stone", 4.5, "accent on background"),
    ("color-steel",    "color-stone", 4.5, "accent on background"),
]


def parse_palette(css: str) -> tuple[dict[str, str], dict[str, str]]:
    """Return (light_tokens, dark_tokens) as name -> '#rrggbb'."""
    light_match = re.search(r":root\s*\{([^}]*)\}", css, re.DOTALL)
    dark_match = re.search(
        r':root\[data-theme="dark"\]\s*\{([^}]*)\}', css, re.DOTALL
    )
    if not light_match:
        sys.exit("ERROR: could not find ':root { ... }' block in main.css")
    if not dark_match:
        sys.exit(
            'ERROR: could not find \':root[data-theme="dark"] { ... }\' block in main.css'
        )

    def extract(block: str) -> dict[str, str]:
        return {
            name: value.lower()
            for name, value in re.findall(
                r"--([a-z0-9\-]+)\s*:\s*(#[0-9a-fA-F]{3,8})\s*;", block
            )
        }

    return extract(light_match.group(1)), extract(dark_match.group(1))


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    s = value.lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        sys.exit(f"ERROR: unsupported hex color '{value}'")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    l1 = relative_luminance(hex_to_rgb(fg))
    l2 = relative_luminance(hex_to_rgb(bg))
    light, dark = max(l1, l2), min(l1, l2)
    return (light + 0.05) / (dark + 0.05)


def check(palette_name: str, palette: dict[str, str]) -> list[str]:
    failures: list[str] = []
    print(f"\n{palette_name}:")
    for fg_name, bg_name, min_ratio, role in PAIRINGS:
        fg = palette.get(fg_name)
        bg = palette.get(bg_name)
        if fg is None or bg is None:
            failures.append(
                f"  MISSING tokens for {fg_name} or {bg_name} in {palette_name}"
            )
            print(f"  MISSING {fg_name} / {bg_name}")
            continue
        ratio = contrast_ratio(fg, bg)
        status = "PASS" if ratio >= min_ratio else "FAIL"
        if status == "FAIL":
            failures.append(
                f"  FAIL {fg_name} ({fg}) on {bg_name} ({bg}): "
                f"{ratio:.2f}:1 < {min_ratio:.1f}:1 ({role})"
            )
        print(
            f"  {status} {fg_name:16s} on {bg_name:14s} "
            f"{ratio:5.2f}:1  (min {min_ratio}, {role})"
        )
    return failures


def main() -> int:
    if not CSS_PATH.exists():
        sys.exit(f"ERROR: {CSS_PATH} not found")
    css = CSS_PATH.read_text()
    light, dark = parse_palette(css)
    failures = check("Light mode (:root)", light)
    failures += check('Dark mode (:root[data-theme="dark"])', dark)
    if failures:
        print("\nFAILURES:")
        for line in failures:
            print(line)
        return 1
    print("\nAll contrast pairings pass WCAG thresholds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Make it executable**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
chmod +x tools/check-contrast.py
```

- [ ] **Step 3: Run it — expect failure**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
python3 tools/check-contrast.py; echo "exit=$?"
```

Expected: `ERROR: could not find ':root { ... }' block in main.css` and `exit=1`. The current `main.css` is Tailwind imports + `@theme {}` blocks, not `:root` custom properties. The test fails because the implementation hasn't landed. This confirms the checker is wired correctly.

- [ ] **Step 4: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add tools/check-contrast.py
git commit -m "$(cat <<'EOF'
Add WCAG contrast checker tool

`python3 tools/check-contrast.py` parses :root and :root[data-theme="dark"]
blocks in assets/css/main.css and verifies the four documented palette
pairings hit their WCAG 2.1 thresholds (AAA body = 7.0, AA body / AAA
large = 4.5).

Currently fails (no `:root` block in the Tailwind-driven main.css).
The next task replaces main.css with the hand-rolled palette and the
checker passes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Replace main.css with hand-rolled CSS

**Files:**
- Modify: `assets/css/main.css` (full replacement)

The new `main.css` defines:
1. Minimal CSS reset
2. CSS custom properties (light at `:root`, dark via `:root[data-theme="dark"]` and `@media (prefers-color-scheme: dark) :root:not([data-theme])`)
3. Typography (body, headings, links, code)
4. Layout primitives (`.page`, `.reading-column`)
5. Site components (`.site-header`, `.site-nav`, `.icon-button`, `.rss-link`, `.site-footer`, `.colophon`)
6. Focus states + `prefers-reduced-motion` overrides

- [ ] **Step 1: Replace `assets/css/main.css` contents**

Open `assets/css/main.css` and replace the full file with exactly this:

```css
/* a3madkour.github.io — visual identity
 * Tokens, typography, base layout, and site components.
 * See docs/superpowers/specs/2026-05-03-personal-site-design.md §2.
 */

/* ------------------------------------------------------------------
 * 1. Reset
 * ------------------------------------------------------------------ */
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { min-height: 100dvh; }
img, svg { display: block; max-width: 100%; }

/* ------------------------------------------------------------------
 * 2. Tokens — light mode (:root, default)
 * ------------------------------------------------------------------ */
:root {
  --color-stone:    #eeeeea;
  --color-ink:      #1c1a17;
  --color-ink-soft: #5a564f;
  --color-ink-fade: #9a958e;
  --color-rule:     #d4d3cd;
  --color-tile:     #fdfcf8;
  --color-burgundy: #6b1f2c;
  --color-steel:    #1e4060;

  --font-body: "Petrona", Georgia, serif;
  --font-ui:   "Inter", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;

  --reading-column: 720px;
  --page-gutter:    1.25rem;

  --text-xs:   0.8125rem;
  --text-sm:   0.9375rem;
  --text-base: 1.0625rem;
  --text-md:   1.25rem;
  --text-lg:   1.625rem;
  --text-xl:   2rem;
  --text-2xl:  2.75rem;
  --text-3xl:  3.5rem;
}

/* Dark mode — explicit override via attribute */
:root[data-theme="dark"] {
  --color-stone:    #181818;
  --color-ink:      #e2e2dd;
  --color-ink-soft: #b0aca0;
  --color-ink-fade: #7a7770;
  --color-rule:     #333333;
  --color-tile:     #2a2a2a;
  --color-burgundy: #d65a6a;
  --color-steel:    #7eafd0;
}

/* Dark mode — system preference, only when no explicit override */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    --color-stone:    #181818;
    --color-ink:      #e2e2dd;
    --color-ink-soft: #b0aca0;
    --color-ink-fade: #7a7770;
    --color-rule:     #333333;
    --color-tile:     #2a2a2a;
    --color-burgundy: #d65a6a;
    --color-steel:    #7eafd0;
  }
}

/* ------------------------------------------------------------------
 * 3. Typography
 * ------------------------------------------------------------------ */
body {
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: 1.6;
  color: var(--color-ink);
  background: var(--color-stone);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-body);
  font-weight: 700;
  line-height: 1.2;
  margin: 1.5em 0 0.5em;
  color: var(--color-ink);
}

h1 { font-size: var(--text-2xl); }
h2 { font-size: var(--text-xl); }
h3 { font-size: var(--text-lg); }
h4 { font-size: var(--text-md); }

p { margin: 0 0 1em; }

a {
  color: var(--color-burgundy);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
}
a:hover { text-decoration-thickness: 2px; }

code, pre, kbd, samp {
  font-family: var(--font-mono);
  font-size: 0.95em;
}
pre {
  background: var(--color-tile);
  border: 1px solid var(--color-rule);
  border-radius: 8px;
  padding: 1rem;
  overflow-x: auto;
}

hr {
  border: 0;
  border-top: 1px solid var(--color-rule);
  margin: 2.5rem 0;
}

::selection {
  background: var(--color-burgundy);
  color: var(--color-stone);
}

:focus-visible {
  outline: 2px solid var(--color-burgundy);
  outline-offset: 2px;
}

/* ------------------------------------------------------------------
 * 4. Layout primitives
 * ------------------------------------------------------------------ */
.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 var(--page-gutter);
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
}

.reading-column {
  max-width: var(--reading-column);
  margin: 0 auto;
}

main { flex-grow: 1; }

/* ------------------------------------------------------------------
 * 5. Site header
 * ------------------------------------------------------------------ */
.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2rem 0;
  font-family: var(--font-ui);
  flex-wrap: wrap;
  gap: 1rem;
}

.site-brand {
  font-family: var(--font-body);
  font-weight: 700;
  font-size: var(--text-md);
  color: var(--color-ink);
  text-decoration: none;
}
.site-brand:hover { color: var(--color-burgundy); }

.site-nav {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  font-size: var(--text-sm);
}

.site-nav a {
  color: var(--color-ink);
  text-decoration: none;
}
.site-nav a:hover { color: var(--color-burgundy); text-decoration: underline; }
.site-nav a[aria-current="page"] { color: var(--color-burgundy); }

.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  background: transparent;
  border: 0;
  padding: 0;
  cursor: pointer;
  color: var(--color-ink);
  text-decoration: none;
}
.icon-button:hover { color: var(--color-burgundy); }
.icon-button svg { width: 1.25rem; height: 1.25rem; }

.rss-link { color: #ee7e2c; }
.rss-link:hover { color: #ee7e2c; filter: brightness(1.1); }

/* ------------------------------------------------------------------
 * 6. Site footer
 * ------------------------------------------------------------------ */
.site-footer {
  margin-top: 4rem;
  padding: 2rem 0;
  border-top: 1px solid var(--color-rule);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
}

.colophon { margin: 0 0 0.75rem; }
.colophon strong { color: var(--color-ink); font-weight: 600; }

.site-footer .social {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}
.site-footer .social a {
  color: var(--color-ink-soft);
  text-decoration: none;
}
.site-footer .social a:hover {
  color: var(--color-burgundy);
  text-decoration: underline;
}

/* ------------------------------------------------------------------
 * 7. Hero / role line (homepage placeholder)
 * ------------------------------------------------------------------ */
.role {
  font-family: var(--font-ui);
  color: var(--color-ink-soft);
  max-width: 640px;
  font-size: var(--text-md);
  margin: 0.25rem 0 1.5rem;
}

/* ------------------------------------------------------------------
 * 8. Reduced motion
 * ------------------------------------------------------------------ */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- [ ] **Step 2: Run the contrast checker — expect pass**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
python3 tools/check-contrast.py; echo "exit=$?"
```

Expected output:

```
Light mode (:root):
  PASS color-ink         on color-stone   14.92:1  (min 7.0, body text on background)
  PASS color-ink-soft    on color-stone    6.27:1  (min 4.5, secondary text on background)
  PASS color-burgundy    on color-stone    9.71:1  (min 4.5, accent on background)
  PASS color-steel       on color-stone    9.21:1  (min 4.5, accent on background)

Dark mode (:root[data-theme="dark"]):
  PASS color-ink         on color-stone   13.65:1  (min 7.0, body text on background)
  PASS color-ink-soft    on color-stone    7.83:1  (min 4.5, secondary text on background)
  PASS color-burgundy    on color-stone    4.68:1  (min 4.5, accent on background)
  PASS color-steel       on color-stone    7.55:1  (min 4.5, accent on background)

All contrast pairings pass WCAG thresholds.
exit=0
```

(Ratios are within ±0.02 of the spec's stated values, depending on float rounding. All eight pairings must be PASS. If any pairing FAILs, **stop and surface the finding to the user** — do not silently lower thresholds.)

- [ ] **Step 3: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add assets/css/main.css
git commit -m "$(cat <<'EOF'
Replace Tailwind import with hand-rolled visual identity

Implements the locked palette + typography from spec §2:
- Petrona / Inter / JetBrains Mono token families
- Cool stone background, burgundy + steel accents
- Light at :root; dark at :root[data-theme="dark"] AND
  @media (prefers-color-scheme: dark) :root:not([data-theme])
- Reading column 720px, focus states, prefers-reduced-motion fallback
- Site header / nav / footer / colophon component classes

All eight contrast pairings pass WCAG 2.1 thresholds (AAA body, AA accents)
per tools/check-contrast.py.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Update head.html — load main.css directly + Google Fonts

**Files:**
- Modify: `layouts/partials/head.html`

- [ ] **Step 1: Replace `layouts/partials/head.html` contents**

Open `layouts/partials/head.html` and replace the full file with exactly this:

```html
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="author" content="Abdelrahman Madkour">
  {{ $description := or .Description .Summary site.Params.description }}
  {{ with $description }}<meta name="description" content="{{ . }}">{{ end }}
  <title>{{ if .IsHome }}{{ site.Title }}{{ else }}{{ .Title }} | {{ site.Title }}{{ end }}</title>
  <link rel="canonical" href="{{ .Permalink }}">

  {{/* Open Graph / Twitter */}}
  <meta property="og:title" content="{{ if .IsHome }}{{ site.Title }}{{ else }}{{ .Title }}{{ end }}">
  <meta property="og:type" content="{{ if .IsPage }}article{{ else }}website{{ end }}">
  <meta property="og:url" content="{{ .Permalink }}">
  {{ with $description }}<meta property="og:description" content="{{ . }}">{{ end }}
  <meta name="twitter:card" content="summary">

  {{/* RSS */}}
  {{ range .AlternativeOutputFormats }}
    <link rel="{{ .Rel }}" type="{{ .MediaType.Type }}" href="{{ .Permalink }}" title="{{ site.Title }}">
  {{ end }}

  {{/* Fonts: Petrona (body) + Inter (UI) + JetBrains Mono (code) */}}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono&family=Petrona:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">

  {{/* Site CSS — hand-rolled, processed by Hugo */}}
  {{ with resources.Get "css/main.css" }}
    {{ $styles := . }}
    {{ if hugo.IsProduction }}
      {{ $styles = $styles | minify | fingerprint }}
    {{ end }}
    <link href="{{ $styles.RelPermalink }}" rel="stylesheet"
      {{ with $styles.Data.Integrity }} integrity="{{ . }}" crossorigin="anonymous"{{ end }}>
  {{ end }}
</head>
```

Changes vs the previous file:
- Replaced single Righteous Google Fonts link with three families (Petrona italic+upright with multiple weights, Inter 400/500/600, JetBrains Mono regular)
- Replaced `resources.Get "css/compiled.css"` with `resources.Get "css/main.css"`
- Kept the production minify+fingerprint pipeline and SRI integrity

- [ ] **Step 2: Run the build**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
hugo --minify
```

Expected: build succeeds, `public/css/main.<hash>.css` is generated. (Layouts still reference Tailwind classes at this point — pages will render with our typography but the `bg-white`, `flex`, etc. classes are no-ops. That's fine until Task 11.)

- [ ] **Step 3: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add layouts/partials/head.html
git commit -m "$(cat <<'EOF'
Load hand-rolled main.css and three font families in head.html

- Drops the compiled.css reference (Tailwind output, no longer built)
- Adds Petrona (body, italic + upright), Inter (UI), and JetBrains Mono
  via a single Google Fonts link with display=swap

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Migrate theme toggle JS to data-theme attribute

**Files:**
- Modify: `assets/js/toggle-theme.js` (full rewrite)

Per spec §5.9: theme cycles light → dark → system; persisted in `localStorage` key `theme-pref`; absence of the key falls back to `prefers-color-scheme`. Implementation toggles `data-theme="light"` / `"dark"` / removes the attribute on `<html>`.

The button label updates to indicate the current state for screen readers (`aria-label="Theme: light"` etc.).

- [ ] **Step 1: Replace `assets/js/toggle-theme.js` contents**

Open `assets/js/toggle-theme.js` and replace the full file with exactly this:

```javascript
// Theme toggle — cycles light → dark → system.
// Stores override in localStorage key "theme-pref".
// On load: if "theme-pref" is set, applies it; otherwise CSS handles
// system preference via @media (prefers-color-scheme: dark) :root:not([data-theme]).

(function () {
  const STORAGE_KEY = 'theme-pref';
  const ORDER = ['system', 'light', 'dark'];

  const root = document.documentElement;

  function apply(pref) {
    if (pref === 'light' || pref === 'dark') {
      root.setAttribute('data-theme', pref);
    } else {
      root.removeAttribute('data-theme');
    }
  }

  function read() {
    const stored = localStorage.getItem(STORAGE_KEY);
    return ORDER.includes(stored) ? stored : 'system';
  }

  function next(current) {
    const i = ORDER.indexOf(current);
    return ORDER[(i + 1) % ORDER.length];
  }

  // Initialize on load
  apply(read());

  function updateButtonLabel(button, pref) {
    const labels = {
      system: 'Theme: system (click to switch to light)',
      light:  'Theme: light (click to switch to dark)',
      dark:   'Theme: dark (click to switch to system)',
    };
    button.setAttribute('aria-label', labels[pref]);
    button.setAttribute('title', labels[pref]);
    button.dataset.themePref = pref;
  }

  document.addEventListener('DOMContentLoaded', () => {
    const button = document.querySelector('[data-theme-toggle]');
    if (!button) return;

    updateButtonLabel(button, read());

    button.addEventListener('click', () => {
      const newPref = next(read());
      if (newPref === 'system') {
        localStorage.removeItem(STORAGE_KEY);
      } else {
        localStorage.setItem(STORAGE_KEY, newPref);
      }
      apply(newPref);
      updateButtonLabel(button, newPref);
    });
  });
})();
```

Key changes vs the previous file:
- Storage key `theme` → `theme-pref` (matches spec §5.9)
- `.dark` class → `data-theme="dark"` attribute
- Two-state toggle (light/dark) → three-state cycle (system → light → dark → system)
- Button label updates to expose current state to screen readers
- No more `matchMedia` event listener — CSS `@media (prefers-color-scheme: dark) :root:not([data-theme])` handles system mode automatically

- [ ] **Step 2: Build and verify the JS bundle**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
hugo --minify
ls -lh public/js/
```

Expected: `bundle.<hash>.min.js` exists. No build errors.

- [ ] **Step 3: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add assets/js/toggle-theme.js
git commit -m "$(cat <<'EOF'
Migrate theme toggle to data-theme attribute, three-state cycle

Per spec §5.9:
- Storage key: "theme-pref" (was "theme")
- Cycle: system → light → dark → system
- `data-theme` attribute on <html> instead of `.dark` class
- Removing the attribute restores system-preference behavior, which
  the CSS handles via @media (prefers-color-scheme: dark) :root:not([data-theme])
- Button aria-label/title reflect current state for screen readers

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Create theme toggle and RSS SVG icons

**Files:**
- Create: `assets/images/icons/sun.svg`
- Create: `assets/images/icons/rss.svg`

Per spec §2 illustration approach: thin strokes (~1.5px), monochromatic via `currentColor`, ~16–24px display. These two are the first members of the icon set; later phases add growth-stage icons + game/music/poem glyphs.

- [ ] **Step 1: Create the directories**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
mkdir -p assets/images/icons
```

- [ ] **Step 2: Create `sun.svg`**

Create `assets/images/icons/sun.svg` with:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
     stroke-linejoin="round" aria-hidden="true">
  <circle cx="12" cy="12" r="4"/>
  <path d="M12 3v2"/>
  <path d="M12 19v2"/>
  <path d="M3 12h2"/>
  <path d="M19 12h2"/>
  <path d="M5.6 5.6l1.4 1.4"/>
  <path d="M17 17l1.4 1.4"/>
  <path d="M5.6 18.4l1.4-1.4"/>
  <path d="M17 7l1.4-1.4"/>
</svg>
```

- [ ] **Step 3: Create `rss.svg`**

Create `assets/images/icons/rss.svg` with:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
     stroke-linejoin="round" aria-hidden="true">
  <path d="M4 11a9 9 0 0 1 9 9"/>
  <path d="M4 4a16 16 0 0 1 16 16"/>
  <circle cx="5" cy="19" r="1.5" fill="currentColor"/>
</svg>
```

- [ ] **Step 4: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add assets/images/icons/
git commit -m "$(cat <<'EOF'
Add sun (theme toggle) and RSS header icons

Stroked SVGs (1.5px) using currentColor. First members of the icon
set described in spec §2; growth-stage and creative-output glyphs
land in later phases.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Update header.html — new top nav, RSS button, theme toggle

**Files:**
- Modify: `layouts/partials/header.html`

Per spec §3: top nav is `Essays | Garden | Research | Works | About` plus RSS and theme-toggle icon buttons. Brand on the left links home.

The Garden / Research / Works sections don't have content yet — links go to `/garden/`, `/research/`, `/works/` which Hugo resolves to placeholder list pages (or 404 if no content). For now this is acceptable; later phases create the section content.

- [ ] **Step 1: Replace `layouts/partials/header.html` contents**

Open `layouts/partials/header.html` and replace the full file with exactly this:

```html
<header class="site-header">
  <a class="site-brand" href="{{ "/" | relURL }}">a3madkour</a>
  <nav class="site-nav" aria-label="Primary">
    {{ $current := .RelPermalink }}
    {{ range slice
        (dict "url" "/essays/"  "label" "Essays")
        (dict "url" "/garden/"  "label" "Garden")
        (dict "url" "/research/" "label" "Research")
        (dict "url" "/works/"   "label" "Works")
        (dict "url" "/about/"   "label" "About")
    }}
      <a href="{{ .url | relURL }}"
         {{ if hasPrefix $current .url }}aria-current="page"{{ end }}>{{ .label }}</a>
    {{ end }}
    <a class="icon-button rss-link"
       href="{{ "/index.xml" | relURL }}"
       aria-label="RSS feed"
       title="RSS feed">
      {{ with resources.Get "images/icons/rss.svg" }}{{ .Content | safeHTML }}{{ end }}
    </a>
    <button class="icon-button"
            type="button"
            data-theme-toggle
            aria-label="Theme: system (click to switch to light)">
      {{ with resources.Get "images/icons/sun.svg" }}{{ .Content | safeHTML }}{{ end }}
    </button>
  </nav>
</header>
```

Key changes:
- Brand text: `A3Madkour` → `a3madkour` (lowercase per spec §3 nav line)
- Nav: `Blog | Tools | About` → `Essays | Garden | Research | Works | About`
- Adds RSS button with the `rss.svg` icon
- Theme toggle button now uses the `sun.svg` icon, no Tailwind classes
- All Tailwind utility classes removed; uses semantic class names (`.site-header`, `.site-nav`, `.icon-button`, `.rss-link`)

- [ ] **Step 2: Build and verify**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
hugo --minify
```

Expected: clean build, no errors.

- [ ] **Step 3: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add layouts/partials/header.html
git commit -m "$(cat <<'EOF'
Rewrite site header with new nav, RSS, and theme toggle

Per spec §3: top nav is Essays / Garden / Research / Works / About,
plus an orange-tinted RSS link to /index.xml and the data-theme toggle.
Drops all Tailwind utility classes for semantic class names styled by
main.css. Inline SVG icons via resources.Get + safeHTML.

Some sections (Garden / Research / Works) don't have content yet —
their nav links resolve to empty list pages until later phases.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 10: Update footer.html — colophon line + social links

**Files:**
- Modify: `layouts/partials/footer.html`

Per spec §4.1 / §4.2: footer has a colophon line "Built with Hugo / set in Petrona & Inter / **Words are mine; not generated**" and social links (GitHub / Bluesky / Email).

- [ ] **Step 1: Replace `layouts/partials/footer.html` contents**

Open `layouts/partials/footer.html` and replace the full file with exactly this:

```html
<footer class="site-footer">
  <p class="colophon">
    Built with <a href="https://gohugo.io/">Hugo</a>.
    Set in Petrona &amp; Inter.
    <strong>Words are mine; not generated.</strong>
  </p>
  <p class="copyright">
    &copy; {{ now.Year }} Abdelrahman Madkour.
  </p>
  <div class="social">
    <a href="https://github.com/a3madkour" rel="me">GitHub</a>
    <a href="https://bsky.app/" rel="me">Bluesky</a>
    <a href="mailto:a3madkour@gmail.com">Email</a>
    <a href="{{ "/index.xml" | relURL }}">RSS</a>
  </div>
</footer>
```

Notes:
- Bluesky URL is a placeholder — the user will edit this to their actual handle. Leaving as `https://bsky.app/` for now is intentional; replacing it with a real handle is a content change, not a layout change.
- Social link list is minimal: GitHub, Bluesky, Email, RSS. The full list per spec §4.2 (Mastodon, itch.io, etc.) belongs on the About page in Phase 2.

- [ ] **Step 2: Build and verify**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
hugo --minify
```

Expected: clean build.

- [ ] **Step 3: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add layouts/partials/footer.html
git commit -m "$(cat <<'EOF'
Add colophon and social links to site footer

Per spec §4.1 / §4.2:
- "Built with Hugo / Set in Petrona & Inter / Words are mine; not generated"
- Compact social row (GitHub, Bluesky, Email, RSS) — full social list
  belongs on the About page in Phase 2

Bluesky URL is a placeholder; the user will personalize.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 11: Update baseof.html — drop Tailwind, semantic structure

**Files:**
- Modify: `layouts/_default/baseof.html`

- [ ] **Step 1: Replace `layouts/_default/baseof.html` contents**

Open `layouts/_default/baseof.html` and replace the full file with exactly this:

```html
<!DOCTYPE html>
<html lang="{{ .Site.Language.Lang }}">
  {{ partial "head.html" . }}
  <body>
    <div class="page">
      {{ partial "header.html" . }}
      <main>
        {{- block "main" . -}}{{- end -}}
      </main>
      {{ partial "footer.html" . }}
    </div>
    {{ partial "scripts.html" . }}
  </body>
</html>
```

Key changes:
- Drops all Tailwind classes from `<body>` and the wrapping `<section>`
- Replaces `<section class="xl:max-w-5xl ...">` with `<div class="page">`
- Removes the right-side TOC `<aside>` block — TOC layout returns in Phase 2 when essay pages need it
- Body styles (background, color) come from main.css `body { ... }` rule

- [ ] **Step 2: Build and verify**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
hugo --minify
```

Expected: clean build. The TOC condition (`{{ if .Params.showTOC }}`) is dropped — pages with `showTOC: true` in front matter no longer render a sidebar. That's expected; the spec defers TOC to per-essay layouts in Phase 2.

- [ ] **Step 3: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add layouts/_default/baseof.html
git commit -m "$(cat <<'EOF'
Simplify baseof to a semantic .page wrapper

Drops Tailwind utility classes. Removes the right-side TOC <aside> —
TOC layout returns in Phase 2 with the essay-specific template.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 12: Update remaining layouts, JS, and content placeholders

**Files:**
- Modify: `layouts/_default/single.html`
- Modify: `layouts/_default/list.html`
- Modify: `layouts/404.html`
- Modify: `layouts/blog/list.html`
- Modify: `layouts/blog/single.html`
- Modify: `assets/js/nav.js`
- Modify: `content/_index.html`
- Modify: `content/about/index.md`

Goal: every layout and content file builds cleanly with the new identity, no Tailwind classes left behind. Phase 2 will redo blog/essays with the proper grid; for now, blog list and posts just render readably with the new typography.

- [ ] **Step 1: Update `layouts/_default/single.html`**

Replace contents with:

```html
{{ define "main" }}
<article class="reading-column">
  <h1>{{ .Title }}</h1>
  {{- .Content -}}
</article>
{{ end }}
```

(Date metadata stays out of the default template — Hugo populates `.Date` from file mtime even when front matter doesn't set one, which would print a misleading date on the About page. The blog single template adds its own date in Step 5.)

- [ ] **Step 2: Update `layouts/_default/list.html`**

Replace contents with:

```html
{{ define "main" }}
<section class="reading-column">
  <h1>{{ .Title }}</h1>
  {{ .Content }}
  <ul class="page-list">
    {{ range .Pages }}
      <li>
        <a href="{{ .RelPermalink }}">{{ .LinkTitle }}</a>
        {{ with .Description }}<span class="page-list-desc"> — {{ . }}</span>{{ end }}
      </li>
    {{ end }}
  </ul>
</section>
{{ end }}
```

- [ ] **Step 3: Update `layouts/404.html`**

Replace contents with:

```html
{{ define "main" }}
<section class="reading-column" style="text-align: center; padding: 4rem 0;">
  <h1>404</h1>
  <p>page not found</p>
  <p><a href="{{ "/" | relURL }}">&larr; Back home</a></p>
</section>
{{ end }}
```

- [ ] **Step 4: Update `layouts/blog/list.html`**

The Tailwind-styled card grid will be replaced by the variable-tile essay grid in Phase 2. For now, render a clean reading-column list:

```html
{{ define "main" }}
<section class="reading-column">
  <h1>{{ .Title | default "Blog" }}</h1>
  {{ .Content }}
  <ul class="page-list">
    {{ range .Pages.ByDate.Reverse }}
      <li>
        <a href="{{ .RelPermalink }}">{{ .LinkTitle }}</a>
        {{ with .Date }}<span class="meta"> — {{ time.Format "Jan 2, 2006" . }}</span>{{ end }}
        {{ with .Description }}<p class="page-list-desc">{{ . }}</p>{{ end }}
      </li>
    {{ end }}
  </ul>
</section>
{{ end }}
```

- [ ] **Step 5: Update `layouts/blog/single.html`**

Replace contents with:

```html
{{ define "main" }}
<article class="reading-column">
  {{ if .Params.image }}
    {{ with .Resources.Get .Params.image }}
      <p class="post-hero"><img src="{{ .RelPermalink }}" alt=""></p>
    {{ end }}
  {{ end }}
  <header>
    <h1>{{ .Title }}</h1>
    <p class="meta">{{ time.Format "January 02, 2006" .Date }}</p>
  </header>
  {{ .Content }}
</article>
{{ end }}
```

- [ ] **Step 6: Update `assets/js/nav.js`**

The current file adds Tailwind classes (`text-accent-500`, `font-medium`) to the active TOC link. Since the TOC is removed from `baseof.html` in Task 11, this script targets nothing — but keep the logic intact so when the TOC returns in Phase 2 it works with the new class. Replace with:

```javascript
// TOC active-link highlighter — observes headings with `id` and adds
// `is-active` to the corresponding anchor inside the TOC container.
// Used by per-essay layouts when a TOC is present (Phase 2 onward).

window.addEventListener('DOMContentLoaded', () => {
  const tocLinks = document.querySelectorAll('#TableOfContents a');
  if (tocLinks.length === 0) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      const id = entry.target.getAttribute('id');
      if (!id) return;
      if (entry.intersectionRatio > 0) {
        tocLinks.forEach((a) => a.classList.remove('is-active'));
        document.querySelector(`#TableOfContents a[href="#${id}"]`)?.classList.add('is-active');
      }
    });
  });

  document.querySelectorAll('h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]')
    .forEach((heading) => observer.observe(heading));
});
```

- [ ] **Step 7: Update `content/_index.html`**

Replace contents with:

```html
---
title: 'Abdelrahman Madkour'
description: "Games researcher, writer, occasional maker of music and poems."
layout: 'single'
---
<p class="role">Games researcher, writer, occasional maker of music and poems.</p>
```

The `<h1>` comes from the layout (`_default/single.html` renders `<h1>{{ .Title }}</h1>` from front matter), so this content body is body-only — no inner h1 (one-h1-per-page rule).

This is a placeholder for the homepage. The full v3 homepage (Currently widget, Essays grid, Research cards, Garden + Studio columns) lands in Phase 7.

- [ ] **Step 8: Update `content/about/index.md`**

Replace contents with:

```markdown
---
title: 'About'
description: 'About Abdelrahman Madkour.'
type: 'about'
---

Games researcher, writer, occasional maker of music and poems.

## Bio

(Placeholder. Phase 2 fills in the long-form bio, Now widget, affiliations, connect block, and colophon.)
```

- [ ] **Step 9: Add small list-styling and meta CSS to main.css**

Open `assets/css/main.css` and append (at the end, before the `@media (prefers-reduced-motion)` block — or append after it; placement doesn't matter for cascade here):

```css
/* ------------------------------------------------------------------
 * 9. Page lists, meta, post hero
 * ------------------------------------------------------------------ */
.page-list {
  list-style: none;
  padding: 0;
  margin: 2rem 0;
}
.page-list > li { margin: 0 0 1.25rem; }
.page-list-desc {
  color: var(--color-ink-soft);
  font-size: var(--text-sm);
  margin: 0.25rem 0 0;
}
.meta {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
  margin: 0;
}
.post-hero {
  margin: 2rem 0;
  text-align: center;
}
```

(If you appended it after the reduced-motion block, that's fine — these declarations have no animation/transition to override.)

- [ ] **Step 10: Build and rerun the contrast checker**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
hugo --minify
python3 tools/check-contrast.py
```

Expected: build succeeds, all eight contrast pairings pass.

- [ ] **Step 11: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add -A
git commit -m "$(cat <<'EOF'
Strip Tailwind from default/blog/404 layouts and content

- _default/single.html: reading-column article wrapper, h1 + date
- _default/list.html: section + page-list pattern
- 404.html: minimal centered fallback
- blog/list.html, blog/single.html: clean list + reading-column
  (full essay grid arrives in Phase 2)
- assets/js/nav.js: TOC observer uses `is-active` class instead of
  Tailwind utilities; safely no-ops when no TOC is present
- content/_index.html: hero placeholder with role line
- content/about/index.md: placeholder (Phase 2 fills in)
- main.css: page-list, meta, post-hero rules

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 13: Add contrast-check to CI workflow

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Insert the contrast-check step**

Open `.github/workflows/hugo.yaml`. Find the `Setup Pages` step (it has `id: pages` and `uses: actions/configure-pages@v6`). Immediately AFTER that step and BEFORE the `Build with Hugo` step, insert this new step:

```yaml
      - name: Verify CSS contrast (WCAG)
        run: python3 tools/check-contrast.py
```

(The `ubuntu-latest` runner has Python 3 preinstalled, so no setup step is needed.)

- [ ] **Step 2: Verify the workflow file**

Read the full workflow. The `build` job's steps should now be in this order:
1. Install Hugo CLI
2. Checkout
3. Setup Pages
4. Verify CSS contrast (WCAG) ← new
5. Build with Hugo
6. Upload artifact

- [ ] **Step 3: Commit**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add .github/workflows/hugo.yaml
git commit -m "$(cat <<'EOF'
Add WCAG contrast-check as required CI gate

Per spec §11. The step runs `python3 tools/check-contrast.py` after
Setup Pages and before the Hugo build. Uses the runner's preinstalled
Python 3 — no extra setup. Failure blocks deploy.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 14: Final verification

**Files:** none modified — verification only.

- [ ] **Step 1: Build cleanly**

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
rm -rf public/ resources/_gen/
hugo --minify
```

Expected: build completes, no errors, no warnings about missing resources.

- [ ] **Step 2: Run the contrast checker**

```bash
python3 tools/check-contrast.py; echo "exit=$?"
```

Expected: all eight pairings PASS, `exit=0`.

- [ ] **Step 3: Open key URLs in the browser**

```bash
hugo server --disableFastRender --port 1313
```

Visit each URL and verify:

| URL | Expectation |
|---|---|
| `http://localhost:1313/` | Hero with name (Petrona, large), role line below in Inter, cool-stone background. Header shows brand left + nav (Essays/Garden/Research/Works/About) + RSS icon + sun icon, all in burgundy on hover. Footer at bottom with colophon line "Words are mine; not generated" in stronger weight. |
| `http://localhost:1313/about/` | Reading-column body, "About" h1, placeholder body text. |
| `http://localhost:1313/blog/` | Reading-column list of blog posts ("lorem-ipsum"), no Tailwind grid. |
| `http://localhost:1313/blog/lorem-ipsum/` | Reading-column post layout, h1 in Petrona, date metadata in Inter, body text in Petrona. |
| `http://localhost:1313/garden/` (and `/essays/`, `/research/`, `/works/`) | Hugo renders an empty `_default/list.html` ("Garden" / etc. heading, empty `.page-list`). Acceptable until Phase 2. |
| `http://localhost:1313/asdf-not-real` | 404 page renders centered with "404" + "page not found" + "Back home" link. |

- [ ] **Step 4: Test theme toggle**

In the browser:
1. Click the sun icon. The page should switch to dark mode (`#181818` background, `#e2e2dd` text). Check `<html data-theme="dark">` in DevTools Elements panel.
2. Click again. The page should switch to light (`<html data-theme="light">`).
3. Click again. The page should fall back to system preference (`<html>` has no `data-theme` attribute). Background reflects your OS theme.
4. Reload the page. State persists (or returns to system) per the previous click.
5. Open DevTools → Application → Local Storage. Confirm `theme-pref` key holds `light`, `dark`, or is absent (system).

- [ ] **Step 5: Test with prefers-reduced-motion**

In Chrome DevTools: Rendering panel → "Emulate CSS media feature prefers-reduced-motion" → "reduce". Reload. Site renders normally; no animations would kick in (we have none yet, but the override is wired).

- [ ] **Step 6: Test focus states**

Press Tab repeatedly from the address bar onto the page. Each focusable element (brand link, nav links, RSS, theme toggle, footer links, body links) should show a visible 2px burgundy outline with 2px offset.

- [ ] **Step 7: Stop the server**

`Ctrl+C` to stop `hugo server`.

- [ ] **Step 8: Commit the plan itself**

The plan file `docs/superpowers/plans/2026-05-04-foundation-and-visual-identity.md` should still be present in the worktree (it was written during planning, before any tasks ran). Commit it now so the branch's history records it.

```bash
cd ~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity
git add docs/superpowers/plans/2026-05-04-foundation-and-visual-identity.md
git commit -m "$(cat <<'EOF'
Add Phase 0+1 implementation plan

Captures the full task list executed on this branch — drop Tailwind,
hand-roll main.css with the locked palette, migrate the theme toggle,
new top nav, contrast-check CI gate. Saved on-branch so future Claude
sessions can find it from any commit in this branch's history.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 9: Stop. Hand off to user.**

Do NOT push. Do NOT open a PR. Do NOT merge to master.

Report to the user:
- Branch: `rebuild/foundation-and-identity` at `~/.config/superpowers/worktrees/a3madkour.github.io/rebuild-foundation-identity`
- Total commits on this branch (count via `git log master..HEAD --oneline | wc -l`)
- Contrast checker status (PASS/FAIL summary)
- One-line summary of what was delivered: "Phase 0+1 done — Tailwind removed, hand-rolled visual identity in place, theme toggle migrated, contrast CI gate added. Site renders on all key URLs."
- Suggested next step: user reviews the branch, merges to master manually, then we plan Phase 2 (Essays + About + Garden notes).

---

## Summary

Total: 14 tasks across 2 phases.

- **Phase 0 (Tasks 1–3):** Drop Node.js, Tailwind, and the npm step from CI.
- **Phase 1 (Tasks 4–14):** Hand-rolled CSS with the locked palette, new theme toggle, new top nav, contrast-check CI gate, placeholder homepage and About.

After execution, the branch is ready for the user to review and merge by hand. Phase 2 (Essays + Garden notes + About content) gets its own plan once master has this work.
