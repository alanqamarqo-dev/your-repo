#!/usr/bin/env python3
"""Compute harvest progress: counts per domain and last N facts per domain.
Usage: py tools/harvest_progress.py [--last N]
"""
import sys, os, io, json, argparse

def load_jsonl(p):
    if not os.path.exists(p):
        return []
    with io.open(p, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    out = []
    for L in lines:
        try:
            out.append(json.loads(L))
        except Exception:
            # ignore malformed lines
            pass
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--last', type=int, default=5, help='last N facts per domain')
    args = ap.parse_args()
    p = 'artifacts/harvested_facts.jsonl'
    rows = load_jsonl(p)
    counts = {}
    per = {}
    for r in rows:
        d = (r.get('domain') or 'unknown').strip()
        counts[d] = counts.get(d, 0) + 1
        per.setdefault(d, []).append(r)
    # print summary
    print('Harvest progress:')
    for d, c in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {d}: {c}")
    print('\nLast facts per domain:')
    for d, items in per.items():
        print('---', d)
        for item in items[-args.last:]:
            t = item.get('text','')
            s = item.get('source','')
            ts = item.get('ts','')
            print(f"  - [{ts}] ({s}) {t[:200].replace('\n',' ')}")

    # also write a compact JSON summary for external plotting
    summary = {'counts': counts, 'last': {d: items[-args.last:] for d, items in per.items()}}
    os.makedirs('artifacts', exist_ok=True)
    with io.open('artifacts/harvest_progress.json','w',encoding='utf-8') as f:
        f.write(json.dumps(summary, ensure_ascii=False, indent=2))
    print('\nWROTE artifacts/harvest_progress.json')

if __name__ == '__main__':
    main()
