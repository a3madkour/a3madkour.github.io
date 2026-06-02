#!/usr/bin/env bash
# Verify d2-blocks.lua's numbering pass against the org fixture.
# Run from the templates dir: ./test-fixtures/test-numbering.sh
set -euo pipefail
cd "$(dirname "$0")/.."
INPUT=test-fixtures/numbering-input.org
JSON=$(pandoc -f org -t json --lua-filter=d2-blocks.lua "$INPUT")

expect_num() {
  local kind="$1" want="$2"
  # Extract the d2-num attribute for the Nth Div of class $kind.
  if ! echo "$JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
def walk(o, kind):
    if isinstance(o, dict):
        if o.get('t') == 'Div':
            attrs = o.get('c', [None,None])[0]
            classes = attrs[1] if attrs else []
            kv = dict(attrs[2]) if attrs else {}
            if kind in classes:
                yield kv.get('d2-num','')
        for v in o.values(): yield from walk(v, kind)
    elif isinstance(o, list):
        for v in o: yield from walk(v, kind)
nums = list(walk(data, '$kind'))
print(','.join(nums))
" | grep -q "^$want\$"; then
    echo "FAIL: kind=$kind want=$want got=$(echo "$JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
def walk(o, kind):
    if isinstance(o, dict):
        if o.get('t') == 'Div':
            attrs = o.get('c', [None,None])[0]
            classes = attrs[1] if attrs else []
            kv = dict(attrs[2]) if attrs else {}
            if kind in classes:
                yield kv.get('d2-num','')
        for v in o.values(): yield from walk(v, kind)
    elif isinstance(o, list):
        for v in o: yield from walk(v, kind)
print(','.join(walk(data, '$kind')))
")"
    exit 1
  fi
}

# Theorem family shares counter: theorem=1, lemma=2, theorem=3.
expect_num theorem "1,3"
expect_num lemma "2"
# Definition has its own counter.
expect_num definition "1,2"
# Proof is unnumbered (empty d2-num).
expect_num proof ""

echo OK
