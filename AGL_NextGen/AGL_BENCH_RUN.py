from __future__ import annotations

import os
import sys
import json


def _configure_utf8_console() -> None:
    if os.name != "nt":
        return

    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # Best-effort: align Windows console code page to UTF-8 for proper Arabic output.
    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass

# allow running from repo root
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from agl.bench.runner import BenchRunner
from agl.bench.tasks import (
    deterministic_tasks,
    causal_tasks,
    planning_tasks,
    planner_tasks,
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
    suite = (os.getenv("AGL_BENCH_SUITE", "deterministic") or "deterministic").strip().lower()

    if suite in ("causal",):
        tasks = causal_tasks()
    elif suite in ("planning", "plan"):
        tasks = planning_tasks()
    elif suite in ("planner",):
        tasks = planner_tasks()
    elif suite in ("deterministic_holdout", "holdout_deterministic"):
        tasks = deterministic_holdout_tasks()
    elif suite in ("causal_holdout", "holdout_causal"):
        tasks = causal_holdout_tasks()
    elif suite in ("planning_holdout", "holdout_planning"):
        tasks = planning_holdout_tasks()
    elif suite in ("planner_holdout", "holdout_planner"):
        tasks = planner_holdout_tasks()
    elif suite in ("planner_strict_holdout", "holdout_planner_strict"):
        tasks = planner_strict_holdout_tasks()
    elif suite in ("nextgen_smoke", "smoke", "nextgen"):
        picked = criteria_tasks_for_suite(suite)
        tasks = picked if picked else deterministic_tasks()
    elif suite.startswith("criteria") or suite in ("c1", "c2", "c3", "c4", "c5", "autonomy", "superiority", "self_learning", "subgoals", "causal"):
        # Note: 'causal' also matches the main causal suite above.
        picked = criteria_tasks_for_suite(suite)
        tasks = picked if picked else deterministic_tasks()
    else:
        tasks = deterministic_tasks()

    rep = BenchRunner(repeats=repeats, use_core_consciousness=use_core).run(tasks=tasks)
    print(json.dumps(rep["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
