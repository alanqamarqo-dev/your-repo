"""Simple dedupe helper: read facts JSONL and report duplicates by (domain, text hash).
Usage: python tools/dedupe_check.py artifacts/external_info_cache/*.json
"""
import sys
# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_PREVIEW_20 = _to_int('AGL_PREVIEW_20', 20)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import json
import hashlib
from collections import Counter
def key_of(f):
    return (f.get('domain', ''), f.get('text', '').strip())
def main(paths):
    seen = Counter()
    total = 0
    for p in paths:
        try:
            with open(p, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                entries = data if isinstance(data, list) else [data]
                for e in entries:
                    total += 1
                    k = key_of(e)
                    seen[k] += 1
        except Exception as e:
            continue
    dupes = {k: v for k, v in seen.items() if v > 1}
    print(f'total_entries={total} unique={len(seen)} duplicates={len(dupes)}')
    for (dom, txt), cnt in sorted(dupes.items(), key=lambda kv: kv[1], reverse=True)[:_AGL_PREVIEW_20]:
        print(f'{cnt}x domain={dom} text_preview={txt[:80]!r}')
if __name__ == '__main__':
    main(sys.argv[1:])
