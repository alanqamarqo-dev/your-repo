import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
GEN_DIR = ROOT / "artifacts" / "generalized"
RC_GEN = GEN_DIR / "rc_D_tau.json"
RC_D = ROOT / "artifacts" / "models" / "rc_D" / "results.json"
KB_PATH = ROOT / "Knowledge_Base" / "Learned_Patterns.json"

entry = None

# Try reading generalized output first
if RC_GEN.exists():
    data = json.loads(RC_GEN.read_text(encoding="utf-8-sig"))
    derived = data.get("derived", {})
    params = data.get("inputs", {}).get("params", {})
    a = params.get("a") if params else derived.get("a")
    V0 = params.get("b") if params else derived.get("V_approx")
    tau = derived.get("tau")
    entry = {
        "type": "rc_step",
        "tau": round(float(tau), 4) if tau is not None else None,
        "a": round(float(a), 10) if a is not None else None,
        "V0": round(float(V0), 4) if V0 is not None else None,
        "source": str(RC_D).replace('\\', '/')
    }
else:
    # fallback: try to compute from D-stage results
    if RC_D.exists():
        d = json.loads(RC_D.read_text(encoding='utf-8-sig'))
        # try to get ensemble result
        ens = d.get('ensemble') or {}
        if isinstance(ens, dict) and ens.get('success') and isinstance(ens.get('result'), dict):
            r = ens['result']
            params = r.get('params', {})
            a = params.get('a')
            V0 = params.get('b')
            tau = -1.0 / a if a else None
            entry = {
                "type": "rc_step",
                "tau": round(float(tau), 4) if tau is not None else None,
                "a": round(float(a), 10) if a is not None else None,
                "V0": round(float(V0), 4) if V0 is not None else None,
                "source": str(RC_D).replace('\\', '/')
            }

if entry is None:
    print("No RC data found (neither generalized nor D-stage results). Nothing written.")
    raise SystemExit(1)

# Ensure KB exists and has patterns list
KB_PATH.parent.mkdir(parents=True, exist_ok=True)
if KB_PATH.exists():
    kb = json.loads(KB_PATH.read_text(encoding='utf-8-sig'))
    if not isinstance(kb, dict):
        kb = {"patterns": []}
    if 'patterns' not in kb or not isinstance(kb['patterns'], list):
        kb['patterns'] = []
else:
    kb = {"patterns": []}

# Avoid duplicates by source
existing = [p for p in kb['patterns'] if p.get('source') == entry['source'] and p.get('type') == entry['type']]
if existing:
    print(f"Entry for source {entry['source']} already exists in KB. Skipping append.")
else:
    kb['patterns'].append(entry)
    KB_PATH.write_text(json.dumps(kb, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Appended entry to {KB_PATH}:")
    print(json.dumps(entry, ensure_ascii=False, indent=2))
