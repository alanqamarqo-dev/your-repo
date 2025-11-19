import json, os, subprocess, sys, time, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PY = (ROOT / ".venv_embed" / "Scripts" / "python.exe")
if not PY.exists():
    PY = sys.executable

GRID = [0.50, 0.60, 0.65, 0.75]
OUT = ROOT / "data" / "alpha_grid_report.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

import re

def run_q(alpha):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["AGL_EMBEDDINGS_ENABLE"] = "1"
    env["AGL_RETRIEVER_BLEND_ALPHA"] = str(alpha)
    # clean reindex for each trial
    subprocess.check_call([str(PY), str(ROOT/"scripts"/"run_clean_reindex.py")], env=env)
    p = subprocess.run([str(PY), str(ROOT/"scripts"/"test_search_quality.py")], env=env, capture_output=True, text=True)
    stdout = p.stdout or ""
    # find improvement score in output
    score = None
    for line in stdout.splitlines():
        if "متوسط درجة التحسن" in line or "improvement" in line.lower():
            m = re.search(r"([0-9]+\.[0-9]+)", line)
            if m:
                score = float(m.group(1))
    return {"alpha": alpha, "score": score, "stdout_tail": "\n".join(stdout.splitlines()[-40:])}

results = []
for a in GRID:
    print(f"[alpha={a}] measuring ...", flush=True)
    t0 = time.time()
    res = run_q(a)
    res["seconds"] = round(time.time() - t0, 2)
    results.append(res)
    print(f"[alpha={a}] done → score={res['score']} ({res['seconds']}s)")

best_candidates = [r for r in results if r["score"] is not None]
best = max(best_candidates, key=lambda x: x["score"]) if best_candidates else None
report = {"grid": GRID, "results": results, "best": best}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nSaved: {OUT}\nBest alpha: {best['alpha']} (score={best['score']})" if best else f"\nSaved: {OUT} (no valid scores)")
