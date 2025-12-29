"""
Small discovery script for AGL knobization: search python files for small numeric limits and write JSON results.
Usage: run from repository root (or with full path to this script).
"""
import os
import re
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'reports', 'agl_discovery_results.json')
PATTERNS = [
    (r"\[:\s*\d+\]", 'slice_simple'),
    (r"\[:\s*-?\d+\s*:\s*-?\d*\]", 'slice_range'),
    (r"\btop[_-]?k\s*=\s*\d+\b", 'top_k'),
    (r"\blimit\s*=\s*\d+\b", 'limit'),
    (r"\bk\s*=\s*\d+\b", 'k_assign'),
    (r"\bmax_results\s*=\s*\d+\b", 'max_results'),
    (r"\bn_results\s*=\s*\d+\b", 'n_results'),
]
COMPILED = [(re.compile(p), name) for p, name in PATTERNS]

results = []
count = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip virtualenvs, .git, __pycache__, artifacts
    if any(skip in dirpath for skip in ('\.venv', 'venv', '__pycache__', '.git', 'artifacts')):
        continue
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        fp = os.path.join(dirpath, fn)
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            for cre, name in COMPILED:
                m = cre.search(line)
                if m:
                    results.append({
                        'path': os.path.relpath(fp, ROOT).replace('\\', '/'),
                        'lineno': i,
                        'line': line.rstrip('\n'),
                        'match': m.group(0),
                        'pattern': name,
                    })
                    count += 1

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as out:
    json.dump({'root': ROOT, 'matches': results, 'count': count}, out, ensure_ascii=False, indent=2)

print(f"WROTE {count} matches to {OUT}")
