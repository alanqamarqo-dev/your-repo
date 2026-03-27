from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .runner import BenchRunner
from .tasks import (
    causal_tasks,
    deterministic_tasks,
    planner_tasks,
    planning_tasks,
    planner_strict_holdout_tasks,
    criteria_tasks_for_suite,
)

try:
    from .gate import GateConfig, run_gate_once
except Exception:  # pragma: no cover
    GateConfig = None  # type: ignore
    run_gate_once = None  # type: ignore

try:
    # Optional integration with the existing self-improvement engine (if present).
    from agl.engines.self_improvement.Self_Improvement_Engine import SelfLearningManager  # type: ignore
except Exception:  # pragma: no cover
    SelfLearningManager = None  # type: ignore


@dataclass(frozen=True)
class SelfImproveConfig:
    suites: List[str]
    repeats: int = 3
    use_core_consciousness: bool = False
    target_accuracy: float = 1.0
    max_iters: int = 5
    artifacts_path: Optional[str] = None


@dataclass(frozen=True)
class SelfImproveIteration:
    iter_index: int
    suite: str
    timestamp: float
    summary: Dict[str, Any]
    notes: List[str]


def _project_root_from_here() -> str:
    here = os.path.abspath(__file__)  # .../src/agl/bench/self_improve.py
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here))))


def _default_artifacts_path() -> str:
    return os.path.join(_project_root_from_here(), "artifacts", "self_improve_runs.jsonl")


def _jsonl_append(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _tasks_for_suite(suite: str):
    s = (suite or "").strip().lower()
    if s.startswith("criteria") or s in ("c1", "c2", "c3", "c4", "c5", "autonomy", "superiority", "self_learning", "subgoals"):
        picked = criteria_tasks_for_suite(s)
        if picked:
            return picked
    if s == "causal":
        return causal_tasks()
    if s in ("planning", "plan"):
        return planning_tasks()
    if s in ("planner", "subgoals"):
        return planner_tasks()
    if s in ("planner_strict_holdout", "holdout_planner_strict"):
        return planner_strict_holdout_tasks()
    return deterministic_tasks()


def _diagnose(report: Dict[str, Any]) -> List[str]:
    notes: List[str] = []
    summary = report.get("summary") or {}
    acc = float(summary.get("accuracy") or 0.0)

    if acc >= 1.0:
        notes.append("All tasks passed at 1.0 accuracy.")
        return notes

    # Light heuristics: common failure modes in this repo.
    for r in report.get("results") or []:
        if r.get("ok") is True:
            continue
        texts = r.get("texts") or []
        joined = "\n".join(str(t) for t in texts)
        low = joined.lower()
        if "ollama" in low or "pull model" in low or "manifest" in low:
            notes.append("Detected LLM backend error (ollama). Prefer offline engines: set AGL_BENCH_USE_CORE=0.")
            break

    if not notes:
        notes.append("Some tasks failed; inspect artifacts/bench_runs.jsonl for details.")

    return notes


def run_self_improve(config: SelfImproveConfig) -> List[SelfImproveIteration]:
    artifacts_path = config.artifacts_path or _default_artifacts_path()
    iters: List[SelfImproveIteration] = []

    suites = config.suites or ["deterministic", "causal", "planning", "planner"]

    # Reuse one runner instance to avoid repeated heavyweight bootstraps.
    runner = BenchRunner(repeats=config.repeats, use_core_consciousness=config.use_core_consciousness)

    learner = None
    if SelfLearningManager is not None:
        try:
            learner = SelfLearningManager()
        except Exception:
            learner = None

    # Optional: run a sandboxed self-modification gate before the normal loops.
    # This is controlled by env vars to keep default behavior unchanged.
    if os.getenv("AGL_SELF_IMPROVE_GATE", "0").strip() == "1" and run_gate_once is not None:
        gate_suite = (os.getenv("AGL_SELF_IMPROVE_GATE_SUITE", "planner_strict_holdout") or "planner_strict_holdout").strip()
        reg = (os.getenv("AGL_SELF_IMPROVE_REGRESSION_SUITES", "planner,deterministic") or "planner,deterministic").strip()
        reg_suites = [s.strip() for s in reg.split(",") if s.strip()]

        gate_cfg = GateConfig(
            suite=gate_suite,
            regression_suites=reg_suites,
            repeats=config.repeats,
            use_core_consciousness=config.use_core_consciousness,
        )
        try:
            gate_res = run_gate_once(gate_cfg)
            _jsonl_append(
                artifacts_path,
                {
                    "iter": -1,
                    "suite": "gate",
                    "timestamp": time.time(),
                    "summary": {"accepted": bool(gate_res.get("accepted")), "suite": gate_suite},
                    "notes": [str(gate_res.get("reason") or "")],
                },
            )
        except Exception as e:
            _jsonl_append(
                artifacts_path,
                {
                    "iter": -1,
                    "suite": "gate",
                    "timestamp": time.time(),
                    "summary": {"accepted": False, "error": str(e)},
                    "notes": ["gate_failed"],
                },
            )

    for iter_index in range(int(config.max_iters)):
        for suite in suites:
            report = runner.run(tasks=_tasks_for_suite(suite))
            summary = report.get("summary") or {}
            notes = _diagnose(report)

            # Feed measured signals into the existing self-learning logger (best-effort).
            if learner is not None:
                try:
                    acc = float(summary.get("accuracy") or 0.0)
                    avg_lat = float(summary.get("avg_latency_ms") or 0.0)
                    learner.record(f"bench:{suite}", acc, note=f"avg_latency_ms={avg_lat:.6f}")
                    learner.improve(
                        {
                            "suite": str(suite),
                            "accuracy": acc,
                            "avg_score": float(summary.get("avg_score") or 0.0),
                            "avg_latency_ms": avg_lat,
                        }
                    )
                except Exception:
                    pass

            iteration = SelfImproveIteration(
                iter_index=iter_index,
                suite=str(suite),
                timestamp=time.time(),
                summary=dict(summary),
                notes=notes,
            )
            iters.append(iteration)

            _jsonl_append(
                artifacts_path,
                {
                    "iter": iteration.iter_index,
                    "suite": iteration.suite,
                    "timestamp": iteration.timestamp,
                    "summary": iteration.summary,
                    "notes": iteration.notes,
                },
            )

            if float(summary.get("accuracy") or 0.0) >= float(config.target_accuracy):
                # Target achieved for this suite; continue to next suite.
                continue

        # If we did a full pass and everything hit the target, stop.
        last_pass = iters[-len(suites) :]
        if last_pass and all(float(i.summary.get("accuracy") or 0.0) >= float(config.target_accuracy) for i in last_pass):
            break

    return iters
