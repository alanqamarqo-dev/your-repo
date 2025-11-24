# -*- coding: utf-8 -*-
import json, subprocess, sys
from pathlib import Path

def run():
    outdir = Path("artifacts/reports"); outdir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "pytest", "-q", "tests/test_agi_advanced_eval.py", "-s", "-ra", "--maxfail=1"]
    print("Running:", " ".join(cmd))
    rc = subprocess.call(cmd)
    # جمع النتائج الجزئية
    parts = {}
    for name in ["agi_adv_case1.json","agi_adv_case2.json","agi_adv_case3.json"]:
        p = outdir / name
        if p.exists():
            parts[name[:-5]] = json.loads(p.read_text(encoding="utf-8"))
    summary = {
        "ok": rc==0,
        "rc": rc,
        "cases": parts,
        "hint": "الملفات التفصيلية موجودة في artifacts/reports/"
    }
    (outdir / "agi_advanced_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    sys.exit(rc)

if __name__ == "__main__":
    run()
