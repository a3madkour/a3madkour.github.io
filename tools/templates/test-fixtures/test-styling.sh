#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
INPUT=test-fixtures/styling-input.org
JSON=$(pandoc -f org -t json --lua-filter=d2-blocks.lua "$INPUT")

# Sanity: header for titled theorem contains "Theorem 1: Intermediate Value".
if ! echo "$JSON" | grep -q '"Intermediate Value"'; then
  echo "FAIL: titled theorem header missing title"; exit 1
fi
# Sanity: definition header reads "Definition 1." with no title.
if ! echo "$JSON" | python3 -c "
import json,sys
def text_of(o):
    if isinstance(o,dict):
        if o.get('t')=='Str': return o.get('c','')
        return ''.join(text_of(v) for v in o.values())
    if isinstance(o,list): return ' '.join(text_of(v) for v in o)
    return ''
data=json.load(sys.stdin)
flat=text_of(data)
assert 'Definition 1' in flat, flat
print(flat)
" > /dev/null; then
  echo "FAIL: Definition header"; exit 1
fi
# Proof: appended ∎ tombstone, header label "Proof." without number.
if ! echo "$JSON" | grep -q "∎"; then
  echo "FAIL: proof tombstone missing"; exit 1
fi
echo OK
