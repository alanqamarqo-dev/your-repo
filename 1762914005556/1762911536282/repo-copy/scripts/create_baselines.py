import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "rc_step": ROOT / "artifacts" / "models" / "rc_D" / "results.json",
    "projectile": ROOT / "artifacts" / "models" / "proj_D" / "results.json",
    "poly2_iv": ROOT / "artifacts" / "models" / "poly2_D" / "results.json",
}

BASELINE_DIR = ROOT / "artifacts" / "models" / "baselines" / "D"
KB_PATH = ROOT / "Knowledge_Base" / "Learned_Patterns.json"

patterns = []
for key, src in SOURCES.items():
    print(f"Processing source {key}: {src}")
    if not src.exists():
        print(f"  WARNING: source not found: {src}")
        continue
    data = json.loads(src.read_text(encoding="utf-8"))
    # Two supported artifact shapes currently:
    #  - legacy: has data['results'] = [ {candidate, fit: {a,b,rmse,confidence,n}} ... ]
    #  - ensemble output: has data['ensemble']['result'] = {winner, params, rmse, confidence, n}
    results = data.get("results", [])
    pattern = None
    if results:
        best = sorted(results, key=lambda it: float(it.get("fit", {}).get("rmse", 1e9)))[0]
        cand = best.get("candidate")
        fit = best.get("fit", {})
        params = {k: v for k, v in fit.items() if isinstance(v, (int, float)) and k not in ("rmse", "n", "confidence")}
        pattern = {
            "tag": f"D/{data.get('base','') }@{cand}",
            "base": data.get("base"),
            "candidate": cand,
            "params": params,
            "rmse": float(fit.get("rmse", 0.0)),
            "confidence": float(fit.get("confidence", 0.0)),
            "n": int(fit.get("n", 0)),
            "ts": int(time.time()),
        }
    else:
        # try ensemble-shaped artifact
        ens = data.get("ensemble") or {}
        if isinstance(ens, dict) and ens.get("success") and isinstance(ens.get("result"), dict):
            r = ens["result"]
            # winner may contain "poly2 (blended)" — strip extra suffix
            winner = str(r.get("winner", "")).split(" (")[0]
            params = r.get("params", {}) or {}
            pattern = {
                "tag": f"D/{data.get('base','') }@{winner}",
                "base": data.get("base"),
                "candidate": winner,
                "params": {k: v for k, v in params.items() if isinstance(v, (int, float))},
                "rmse": float(r.get("rmse", 0.0)),
                "confidence": float(r.get("confidence", 0.0)),
                "n": int(r.get("n", 0)) if r.get("n") is not None else 0,
                "ts": int(time.time()),
            }
        else:
            print(f"  WARNING: no results or ensemble result in {src}")
            continue
    patterns.append((key, src, data, pattern))

# write baselines
for key, src, data, pattern in patterns:
    base_name = data.get("base") or key
    dst_dir = BASELINE_DIR / base_name
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_path = dst_dir / "results.json"
    print(f"Writing baseline: {dst_path}")
    dst_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# merge into Knowledge_Base/Learned_Patterns.json
kb_dir = KB_PATH.parent
kb_dir.mkdir(parents=True, exist_ok=True)
if KB_PATH.exists():
    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))
    if not isinstance(kb, dict):
        kb = {"patterns": []}
    if "patterns" not in kb or not isinstance(kb["patterns"], list):
        kb["patterns"] = []
else:
    kb = {"patterns": []}

existing_tags = {p.get("tag") for p in kb.get("patterns", [])}
new_count = 0
for _, _, _, pattern in patterns:
    if pattern["tag"] in existing_tags:
        print(f"Knowledge base already has {pattern['tag']}, skipping")
        continue
    kb["patterns"].append(pattern)
    new_count += 1

KB_PATH.write_text(json.dumps(kb, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Added {new_count} new patterns to {KB_PATH}")
print("Done.")
