#!/usr/bin/env python3
"""Clean harvested facts: remove mock-provider entries, dedupe exact duplicates,
and write back a compacted file.

Writes to artifacts/harvested_facts.jsonl.tmp then atomically replaces the original.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'artifacts' / 'harvested_facts.jsonl'
TMP = ART.with_suffix('.jsonl.tmp')

if not ART.exists():
    print('No harvested_facts.jsonl found; nothing to do.')
    raise SystemExit(0)

seen = set()
out_lines = []
count_in = 0
count_skipped = 0
count_written = 0

with ART.open('r', encoding='utf-8') as fh:
    for line in fh:
        count_in += 1
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            # keep malformed lines out
            count_skipped += 1
            continue
        # filter mock-provider
        if obj.get('source') == 'mock-provider':
            count_skipped += 1
            continue
        # dedupe by domain+text
        key = (obj.get('domain'), obj.get('text'))
        if key in seen:
            count_skipped += 1
            continue
        seen.add(key)
        out_lines.append(json.dumps(obj, ensure_ascii=False))
        count_written += 1

# atomic replace
os.replace(str(TMP), str(ART)) if False else None
with TMP.open('w', encoding='utf-8') as fh:
    fh.write('\n'.join(out_lines) + '\n')

# move tmp -> actual
os.replace(str(TMP), str(ART))
print(f'Cleaned harvested facts: in={count_in} written={count_written} skipped={count_skipped}')
