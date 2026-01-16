from __future__ import annotations

import json
import os
import sys


def _configure_utf8_console() -> None:
    if os.name != "nt":
        return

    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass


HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from agl.bench.compare import BenchComparator
from agl.bench.tasks import (
    deterministic_holdout_tasks,
    causal_holdout_tasks,
    planning_holdout_tasks,
    planner_holdout_tasks,
    planner_strict_holdout_tasks,
    criteria_tasks_for_suite,
)


def main() -> int:
    _configure_utf8_console()
    repeats = int(os.getenv("AGL_BENCH_REPEATS", "3"))
    use_core = os.getenv("AGL_BENCH_USE_CORE", "0") in ("1", "true", "True")
    suite = (os.getenv("AGL_BENCH_SUITE", "deterministic_holdout") or "deterministic_holdout").strip().lower()

    if suite in ("causal_holdout", "holdout_causal"):
        tasks = causal_holdout_tasks()
    elif suite in ("planning_holdout", "holdout_planning"):
        tasks = planning_holdout_tasks()
    elif suite in ("planner_holdout", "holdout_planner"):
        tasks = planner_holdout_tasks()
    elif suite in ("planner_strict_holdout", "holdout_planner_strict"):
        tasks = planner_strict_holdout_tasks()
    elif suite.startswith("criteria") or suite in ("criteria", "all_criteria", "all"):
        picked = criteria_tasks_for_suite(suite)
        tasks = picked if picked else deterministic_holdout_tasks()
    else:
        tasks = deterministic_holdout_tasks()

    rep = BenchComparator(repeats=repeats, use_core_consciousness=use_core).run(tasks)
    print(json.dumps(rep["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
