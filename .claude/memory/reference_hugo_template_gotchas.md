---
name: reference-hugo-template-gotchas
description: "Two Hugo template-syntax gotchas that pass review-by-eye but break the build: hasKey/isset and substr pipe-arg-order"
metadata: 
  node_type: memory
  type: reference
  originSessionId: fab84d67-9908-43ee-a27e-dcf7540dea4f
---

Two Hugo template idioms that **look right** when reviewed visually but break the build immediately on `hugo`. Both shipped through TDD + spec-review + code-quality-review in the streams slice and were only caught when the controller ran `hugo` for the dev-server spot-check. The pattern: Hugo's template lib is Go-stdlib `text/template` + Hugo extensions, NOT Pongo2/Django/Jinja — many "obvious" function names + pipe semantics differ.

**1. `hasKey` doesn't exist in Hugo.** Use **`isset`** for dict-key-presence:
```hugo
{{- /* WRONG — parse error: function "hasKey" not defined */ -}}
{{- if hasKey $args "heading" -}}...{{- end -}}

{{- /* RIGHT */ -}}
{{- if isset $args "heading" -}}...{{- end -}}
```
`isset` returns true when the key exists regardless of value (so `""` is still "set"). That's the semantic you want when distinguishing "caller omitted the key (apply default)" from "caller explicitly passed empty string (suppress)".

**2. `substr` is `STRING START LENGTH` — pipe form REVERSES the argument:**
```hugo
{{- /* WRONG — "length argument must be an integer" */ -}}
{{- $head := (printf "%v" $d) | substr 0 10 -}}

{{- /* RIGHT — positional, no pipe */ -}}
{{- $head := substr (printf "%v" $d) 0 10 -}}
```
Why: Go template pipes insert the piped value as the **LAST** positional arg. So `STRING | substr 0 10` calls `substr(0, 10, STRING)` — substr sees `0` where it expects the string, `10` where it expects start, and `STRING` where it expects length → "length argument must be an integer". Hugo's `substr` signature is `substr STRING START [LENGTH]`; only safe to pipe a function whose value-arg is its LAST positional.

**Why this slipped through review:**
- The plan author (Claude writing the plan) used Pongo2/Django mental model and didn't run `hugo`.
- The implementer pasted verbatim per plan.
- Both spec + code-quality reviewers verified plan-fidelity + structure, did not run `hugo`.
- The CI workflow runs `hugo --minify` post-linters — would have caught it, but CI runs ONLY on push to master.
- Memory `feedback_verify_before_merge` is the only mitigation that catches this class — user runs the dev server, sees the parse error, controller fixes it pre-merge. **Don't rely on review alone for Hugo template syntax; run `hugo --minify` locally as part of pre-merge verification.**

Sibling gotchas already documented: [[reference-hugo-int-octal-gotcha]] (int "08"/"09" parsed as octal), [[reference-hugo-css-var-zgotmplz]] (CSS custom property interpolation sanitized), [[reference-hugo-jsonify-safejs]] (inline JSON blob escaping).
