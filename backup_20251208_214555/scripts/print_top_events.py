import json
from pathlib import Path
p = Path('artifacts/medical_queries.jsonl')
if not p.exists():
    print('no file'); raise SystemExit(1)
recs = [json.loads(ln) for ln in p.open('r', encoding='utf-8')]
# compute effective latency
def eff(r):
    if r.get('latency_s') is not None:
        return float(r.get('latency_s') or 0.0)
    prov = r.get('provenance') or {}
    ev = prov.get('events') or r.get('events') or []
    try:
        ts = [float(e.get('ts')) for e in ev if e.get('ts') is not None]
        if len(ts) >= 2:
            return max(ts)-min(ts)
    except Exception:
        pass
    return 0.0
recs.sort(key=lambda x: eff(x), reverse=True)
top = recs[0]
prov = top.get('provenance') or {}
ev = prov.get('events') or []
print('TOP TS:', top.get('ts'))
for i, e in enumerate(ev):
    print(i+1, e.get('ts'), e.get('t'), e.get('note')[:120])
# print deltas
print('\nDELTAS:')
for i in range(1, len(ev)):
    try:
        print(i, round(float(ev[i].get('ts')) - float(ev[i-1].get('ts')), 3))
    except Exception:
        print(i, 'err')
