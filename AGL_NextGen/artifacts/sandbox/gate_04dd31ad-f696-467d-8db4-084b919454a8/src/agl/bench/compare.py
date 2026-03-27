from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from .baselines import baseline_ask
from .runner import BenchRunner
from .tasks import BenchTask


def _project_root() -> str:
    here = os.path.abspath(__file__)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here))))


def _artifacts_dir() -> str:
    p = os.path.join(_project_root(), "artifacts")
    os.makedirs(p, exist_ok=True)
    return p


def _jsonl_append(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


class BenchComparator:
    def __init__(self, *, repeats: int = 3, use_core_consciousness: bool = False) -> None:
        self.repeats = max(1, int(repeats))
        self.system_runner = BenchRunner(repeats=repeats, use_core_consciousness=use_core_consciousness)

    def run(self, tasks: List[BenchTask]) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        ts = time.time()

        rows: List[Dict[str, Any]] = []
        sys_ok = []
        base_ok = []
        sys_lat = []
        base_lat = []

        for task in tasks:
            sys_rep_ok: List[bool] = []
            base_rep_ok: List[bool] = []
            sys_rep_lat: List[float] = []
            base_rep_lat: List[float] = []

            for _ in range(self.repeats):
                sys_got = self.system_runner._ask(task)
                base_got = baseline_ask(task.prompt)

                sys_eval_in = sys_got["text"]
                base_eval_in = base_got["text"]

                if "structured" in (task.tags or []):
                    sys_eval_in = json.dumps(sys_got.get("result") or {}, ensure_ascii=False)
                    base_eval_in = json.dumps(base_got.get("result") or {}, ensure_ascii=False)

                sys_ev = task.evaluator(sys_eval_in)
                base_ev = task.evaluator(base_eval_in)

                sys_rep_ok.append(bool(sys_ev.ok))
                base_rep_ok.append(bool(base_ev.ok))

                sys_rep_lat.append(float(sys_got.get("latency_ms") or 0.0))
                base_rep_lat.append(float(base_got.get("latency_ms") or 0.0))

            sys_task_ok = all(sys_rep_ok)
            base_task_ok = all(base_rep_ok)

            rows.append(
                {
                    "task": {"id": task.id, "prompt": task.prompt, "tags": task.tags},
                    "repeats": self.repeats,
                    "system": {
                        "ok": sys_task_ok,
                        "avg_latency_ms": sum(sys_rep_lat) / len(sys_rep_lat),
                    },
                    "baseline": {
                        "ok": base_task_ok,
                        "avg_latency_ms": sum(base_rep_lat) / len(base_rep_lat),
                    },
                }
            )

            sys_ok.append(1 if sys_task_ok else 0)
            base_ok.append(1 if base_task_ok else 0)
            sys_lat.append(sum(sys_rep_lat) / len(sys_rep_lat))
            base_lat.append(sum(base_rep_lat) / len(base_rep_lat))

        sys_acc = sum(sys_ok) / max(1, len(sys_ok))
        base_acc = sum(base_ok) / max(1, len(base_ok))
        win = 0
        tie = 0
        lose = 0
        for so, bo in zip(sys_ok, base_ok):
            if so > bo:
                win += 1
            elif so < bo:
                lose += 1
            else:
                tie += 1

        summary = {
            "run_id": run_id,
            "timestamp": ts,
            "repeats": self.repeats,
            "tasks": len(tasks),
            "system_accuracy": sys_acc,
            "baseline_accuracy": base_acc,
            "win": win,
            "tie": tie,
            "lose": lose,
            "avg_system_latency_ms": sum(sys_lat) / max(1, len(sys_lat)),
            "avg_baseline_latency_ms": sum(base_lat) / max(1, len(base_lat)),
        }

        report = {"summary": summary, "results": rows}
        out_path = os.path.join(_artifacts_dir(), "bench_compare.jsonl")
        _jsonl_append(out_path, report)
        return report
