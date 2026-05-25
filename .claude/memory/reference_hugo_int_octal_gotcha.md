---
name: reference-hugo-int-octal-gotcha
description: "Hugo `int` casts strings via base-0 strconv → zero-padded \"08\"/\"09\" parsed as octal, errors 'invalid syntax'"
metadata: 
  node_type: memory
  type: reference
  originSessionId: f5bcea34-8124-4ba8-a918-fcf90b93b5af
---

Hugo's `int` template function casts a string with base-0 `strconv.ParseInt`, so a **zero-padded** numeric string like `"08"` or `"09"` is interpreted as **octal** — digits 8 and 9 are invalid octal → build fails with `error calling int: ... parsing "08": invalid syntax`. `"01".."07"` and any value ≥ 10 (no leading zero) happen to work, which masks the bug until an `08`/`09`-shaped value appears.

**Fix:** cast through `float` first — `int (float $s)` — because `float` uses decimal `strconv.ParseFloat` (never octal). Applies to any Hugo template parsing zero-padded fields (timecodes `mm:ss`, dates, IDs).

Surfaced 2026-05-19 in the time-synced-poetry slice: `layouts/partials/works/synced-marker-seconds.html` did `int $rest` on a marker's seconds; the spec/plan shipped it verbatim and no fixture had `[00:08]`/`[00:09]` until a strictly-in-order fixture was added, so all reviews missed it (fix `ff35ee1`). The fixture intentionally keeps `[00:08]`/`[00:09]` as a CI regression guard. Related: [[project-time-synced-poetry-slice]], [[reference-hugo-jsonify-safejs]], [[reference-hugo-css-var-zgotmplz]].
