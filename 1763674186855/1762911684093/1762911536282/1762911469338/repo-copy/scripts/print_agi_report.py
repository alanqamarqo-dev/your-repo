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
_AGL_PREVIEW_1000 = _to_int('AGL_PREVIEW_1000', 1000)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import json, textwrap, sys
from pathlib import Path
p = Path('d:/AGL/artifacts/agi_test_results.json')
if not p.exists():
    print('agi_test_results.json not found at', p)
    sys.exit(2)
j = json.loads(p.read_text(encoding='utf-8'))
print('\nFULL JSON OUTPUT:\n' + '=' * 80)
print(json.dumps(j, ensure_ascii=False, indent=2))
print('\n\nDETAILED AGI TEST REPORT\n' + '=' * 80)
for k, v in j.items():
    print(f'PART: {k}')
    engine = v.get('raw', {}).get('engine')
    print('  Engine:       ', engine)
    print('  OK:           ', v.get('ok'))
    print('  Keyword score:', v.get('keyword_score'))
    note = v.get('raw', {}).get('note')
    if note:
        print('  Note:         ', note)
    resp = v.get('response') or ''
    print('  Response (truncated to 1000 chars):')
    print(textwrap.fill(resp[:_AGL_PREVIEW_1000], width=120))
    print('-' * 80)
THRESHOLD = 0.6
total = len(j)
correct = sum((1 for v in j.values() if v.get('ok') and v.get('keyword_score', 0) >= THRESHOLD))
pct = correct / total * 100 if total else 0.0
print(f'\nSimple correctness threshold: keyword_score >= {THRESHOLD} -> {correct}/{total} = {pct:.1f}%')
print('\nReport saved in: d:/AGL/artifacts/agi_test_results.json')
