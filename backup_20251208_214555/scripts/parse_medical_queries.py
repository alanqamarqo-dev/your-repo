import json
from pathlib import Path
p = Path('artifacts/medical_queries.jsonl')
if not p.exists():
    print('no file')
    raise SystemExit(1)

records = []
with p.open('r', encoding='utf-8') as f:
    for ln in f:
        try:
            records.append(json.loads(ln))
        except Exception:
            continue

if not records:
    print('no records')
    raise SystemExit(1)

# sort by latency_s if available, otherwise 0
def _compute_effective_latency(rec):
    # Prefer explicit latency_s
    try:
        if rec.get('latency_s') is not None:
            return float(rec.get('latency_s') or 0.0)
    except Exception:
        pass
    # Fallback: if provenance.events present and contain numeric ts values, compute delta
    prov = rec.get('provenance') or {}
    ev = prov.get('events') or rec.get('events') or []
    try:
        if ev and isinstance(ev, list) and isinstance(ev[0], dict) and 'ts' in ev[0]:
            ts_vals = [float(e.get('ts')) for e in ev if e.get('ts') is not None]
            if len(ts_vals) >= 2:
                return max(ts_vals) - min(ts_vals)
    except Exception:
        pass
    return 0.0

for r in records:
    r['_lat'] = _compute_effective_latency(r)
records.sort(key=lambda x: x['_lat'], reverse=True)

# print summary lines for top 1
top = records[0]
print('TOP_TS:', top.get('ts'))
print('TOTAL_TIME_S:', top.get('latency_s'))
prov = top.get('provenance') or {}
steps = prov.get('events') or top.get('steps') or []
# steps may be list of events (dict) or list of numbers; convert to durations if events present
step_times = []
if steps and isinstance(steps, list) and all(isinstance(s, dict) and 'ts' in s for s in steps):
    # compute differences between consecutive ts if they are numeric timestamps
    try:
        ts_list = [float(s.get('ts')) for s in steps]
        if len(ts_list) >= 2:
            for i in range(1, len(ts_list)):
                step_times.append(round(ts_list[i] - ts_list[i-1], 3))
        else:
            step_times = [round(float(top.get('latency_s') or 0.0), 3)]
    except Exception:
        step_times = [round(float(top.get('latency_s') or 0.0), 3)]
else:
    # assume numeric list or single numeric
    try:
        step_times = [float(x) for x in steps]
    except Exception:
        step_times = [round(float(top.get('latency_s') or 0.0), 3)]

print('NUM_STEPS:', len(step_times))
print('STEP_TIMES:', step_times)
# also print a raw events count if present
ev = (top.get('provenance') or {}).get('events') or top.get('events')
if ev:
    print('RAW_EVENTS_COUNT:', len(ev))
    # print first/last event timestamps if numeric
    try:
        t0 = ev[0].get('ts')
        t1 = ev[-1].get('ts')
        print('EVENT_TS_RANGE:', t0, t1)
    except Exception:
        pass

# print the top 3 latencies
print('\nTOP 3 latencies (s):')
for r in records[:3]:
    print(r.get('ts'), r.get('latency_s'))
