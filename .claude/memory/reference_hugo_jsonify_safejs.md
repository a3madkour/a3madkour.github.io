---
name: reference-hugo-jsonify-safejs
description: "Inline JSON blobs in <script> tags need `jsonify | safeJS` — without safeJS, Hugo HTML-escapes the result and the runtime parses a string instead of a dict"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6cf4b615-49d6-4ba4-93a9-5aac82ce1434
---

When emitting a `<script type="application/json">` blob inline via Hugo, pipe `jsonify | safeJS` — not just `jsonify`.

```hugo
<script type="application/json" class="cite-data">
{{- dict "self" $self "refs" $refs | jsonify | safeJS -}}
</script>
```

**Why this matters:** Hugo's html/template auto-escapes content in HTML context. `{{ ... | jsonify }}` produces a JSON string; if it's emitted into HTML without `safeJS` (or `safeHTML`), Hugo wraps it as a JSON-encoded string, so the consumer sees `"{\"self\":{...}}"` instead of `{"self":{...}}`. The runtime then does `JSON.parse(text)` and gets a string, not the dict it expected.

I hit this during the 2026-05-14 citation export slice in `layouts/partials/cite/data-blob.html`. The linter's HTML parser saw two-level encoding and the `inspect_html` function threw `'str' object has no attribute 'get'` on `blob.get('self')`. The fix was adding `| safeJS` to the pipe.

CLAUDE.md already documents the inverse trap for the graph-data partials (don't `jsonify` inside the `graph-data.html` partial — let the caller do it at the embed point with `| safeJS`). Same root cause: HTML auto-escape vs `<script>` raw-text context.

When to apply:
- Any `<script type="application/json" id|class="…">` blob populated by a Hugo expression.
- Any inline `<script>` that needs to embed a Hugo-rendered structure.

Sentinel for the fix: if a JSON blob in dev tools shows leading-and-trailing quotes around the whole object (`"{\"key\":\"value\"}"`), it's double-encoded — add `safeJS`.

Related: [[reference_hugo_dev_server_gotcha]] · [[reference_filter_chips_data_tags_space_delimited]] · [[project_citation_export_slice]].
