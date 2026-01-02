"""Simple training path wrapper used by the CLI and UI.

This keeps the CLI thin and delegates to SelfLearning for the actual logic.
"""
from .Self_Learning import SelfLearning
from typing import Optional, List, Dict


def train_hooke_from_csv(path: str) -> Dict:
    # read CSV into samples expected by SelfLearning.run (list of dicts with y,x)
    import csv, os
    if not os.path.exists(path):
        return {"ok": False, "error": "dataset_not_found"}

    samples = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                samples.append({k: float(v) for k, v in row.items()})
            except Exception:
                continue

    sl = SelfLearning()
    res = sl.run('hooke', samples, max_candidates=2)
    # return a lightweight summary
    return {"ok": True, "results": res}

