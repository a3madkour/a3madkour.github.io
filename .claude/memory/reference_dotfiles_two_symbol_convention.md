---
name: reference-dotfiles-two-symbol-convention
description: Dotfiles publisher uses TWO section-symbol forms — slash for dispatch/enum/keyword, hyphen for normalize. Don't bulk-rename one direction.
metadata:
  type: reference
---

# Two parallel section-symbol forms in the dotfiles publisher

`a3madkour-pub/sections` enum + `#+HUGO_SECTION:` keyword + the **dispatch alist** in `a3madkour-publish-deliberate.el` use **slash form** for nested sections:

```elisp
'("works/games" "works/music" "works/poetry"
  "research/themes" "research/questions"
  "library/reading" "library/listening" "library/playing" "library/watching")
```

`a3madkour-pub-frontmatter--known-sections` + the **normalize dispatch arms** in `a3madkour-publish-frontmatter.el` use **hyphen form**:

```elisp
'(works-games works-music works-poetry
  research-themes research-questions
  library-reading library-listening library-playing library-watching)
```

So a single logical section has two representations. The poetry handler navigates this:

```elisp
;; Dispatch alist key (slash):
(works/poetry . a3madkour-pub-poetry/publish-poetry-file)

;; Inside the handler — normalize call (hyphen):
(a3madkour-pub-frontmatter/normalize 'works-poetry raw-fm file)
```

`note-section` returns the raw string from `#+HUGO_SECTION:` (slash form). The deliberate dispatcher does `(intern section)` to get the symbol — also slash form. The handler then has to know to translate to hyphen form before calling normalize.

**How to apply:**
- When adding a new section, register in BOTH the slash-form enum AND the hyphen-form known-sections list.
- Dispatch alist + `#+HUGO_SECTION:` value = slash. Normalize arm + symbol used in `normalize` call = hyphen.
- When debugging a "handler not found" error, check the dispatch alist key (must be slash).
- When debugging a "unknown section %S" error from normalize, check the symbol you passed (must be hyphen).
- **Never bulk-rename one form to the other** — they're independent. Caught painfully during the Tier 8.2 brainstorm: tried bulk slash→hyphen across the plan and broke the dispatch.

Source: caught during [[project-tier-8-2-complete]] Task 2 implementer cycle. Plan at `docs/superpowers/plans/2026-06-12-org-synced-poetry-export.md` documents it inline.
