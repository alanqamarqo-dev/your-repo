import json
import sys
import pathlib

baseline_p = pathlib.Path("artifacts/baselines/stability_baseline.json")
current_p = pathlib.Path("artifacts/stability_matrix.json")
THRESH_PCT = float(sys.argv[1]) if len(sys.argv) > 1 else float(__import__('os').environ.get('AGL_STABILITY_SLOWDOWN_PCT', '30'))

if not baseline_p.exists() or not current_p.exists():
    print("Baseline or current report missing — skipping compare.")
    sys.exit(0)

b = json.loads(baseline_p.read_text(encoding="utf-8"))
c = json.loads(current_p.read_text(encoding="utf-8"))

b_map = {r["engine"]: r for r in b["results"]}
regress = []
for r in c["results"]:
    name = r["engine"]
    if name in b_map and r["ok"] and b_map[name]["ok"]:
        old = b_map[name]["elapsed_s"]
        new = r["elapsed_s"]
        if old > 0 and (new - old) / old * 100 > THRESH_PCT:
            regress.append((name, old, new))

if regress:
    print("❌ Regression detected (slower engines):")
    for name, old, new in regress:
        print(f"- {name}: {old:.3f}s -> {new:.3f}s")
    sys.exit(1)

print("✅ No performance regression beyond threshold.")
