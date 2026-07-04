---
name: reference-python-re-escape-hyphen
description: "Python 3.13's re.escape escapes hyphens (`\\-`); strip with .replace(r'\\-', '-') when building plain-text regex patterns from slug-like strings"
metadata: 
  node_type: memory
  type: reference
  originSessionId: fb6e003f-473b-4c49-b2c8-ba5e6fb3bc64
---

`re.escape('/essays/example-one/')` in **Python 3.13** returns `'/essays/example\\-one/'` — hyphens are escaped even though they're only special inside `[]` character classes. This changed between Python versions; older Pythons left bare `-` alone outside character classes.

**Bite:** building regex patterns from URL slugs / hyphenated identifiers (LHCI `matchingUrlPattern`, link checkers, fixture-name validators) ends up with `\\-` in the output. The pattern still *works* as a regex, but if you test the literal string (or pass it to a regex engine that's strict about unnecessary escapes), you'll see the surprise.

**Workaround** (Tier 7.1 `render_assert_matrix` shipped this):
```python
pattern = re.escape(url).replace(r"\-", "-") + "$"
```

Strips the escape since `-` outside `[]` is always literal.

**How to apply:** when writing any tool that builds regex from path-like or slug-like strings on Python 3.13+, either accept the `\-` (it's correct regex) or strip it for cleaner output. TDD will catch the mismatch on the first comparison test.

**Discovery:** Tier 7.1 LHCI sitemap-derived URLs slice, 2026-06-12. See `tools/gen_lhci_urls.py:render_assert_matrix`.
