from __future__ import annotations
import json, time
from pathlib import Path
from typing import Dict, Any

HIST = Path("artifacts/history/evolution.jsonl")
HIST.parent.mkdir(parents=True, exist_ok=True)


def snapshot(run_tag: str = "") -> None:
    def _read(p: str):
        fp = Path(p)
        return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
    theory = _read("artifacts/theory_bundle.json")
    reason = _read("artifacts/reasoning_eval.json")
    prog = _read("artifacts/harvest_progress.json")
    cfg = _read("artifacts/agl4_config.json")

    row: Dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tag": run_tag or time.strftime("run_%Y%m%d_%H%M%S"),
        "metrics": {
            "coherence": theory.get("metrics", {}).get("coherence", theory.get("coherence")),
            "coverage": theory.get("metrics", {}).get("coverage", theory.get("coverage")),
            "falsifiability": theory.get("metrics", {}).get("falsifiability", theory.get("falsifiability")),
            "hyp_acc": reason.get("hypotheses_accepted"),
            "hyp_gen": reason.get("hypotheses_generated"),
        },
        "config": cfg,
        "domains": list((prog or {}).get("Last facts per domain", {}).keys()) if prog else None
    }
    entry = json.dumps(row, ensure_ascii=False)
    if HIST.exists():
        HIST.write_text(HIST.read_text(encoding="utf-8") + entry + "\n", encoding="utf-8")
    else:
        HIST.write_text(entry + "\n", encoding="utf-8")
