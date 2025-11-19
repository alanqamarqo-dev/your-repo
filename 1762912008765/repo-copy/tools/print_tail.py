#!/usr/bin/env python3
import sys, io, json, os

def print_tail(path, n=2):
    if not os.path.exists(path):
        print(f"MISSING: {path}")
        return
    with io.open(path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    tail = lines[-n:] if lines else []
    print('--- tail:', path)
    for L in tail:
        try:
            obj = json.loads(L)
            print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False))
        except Exception:
            # fallback: show raw line
            print(L)

if __name__ == '__main__':
    p = sys.argv[1] if len(sys.argv) > 1 else 'artifacts/harvested_facts.jsonl'
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    print_tail(p, n)
