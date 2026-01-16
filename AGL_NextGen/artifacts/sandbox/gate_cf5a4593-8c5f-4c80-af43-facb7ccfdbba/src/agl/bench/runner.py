from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from agl.lib.core_memory.bridge_singleton import get_bridge

try:
    from .baselines import BaselineEngine
except Exception:  # pragma: no cover
    BaselineEngine = None  # type: ignore

from .tasks import BenchTask, default_tasks


def _project_root() -> str:
    # AGL_NextGen/src/agl/bench -> AGL_NextGen
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


class BenchRunner:
    def __init__(self, repeats: int = 3, use_core_consciousness: bool = True) -> None:
        self.repeats = max(1, int(repeats))
        self.use_core_consciousness = bool(use_core_consciousness)
        self.bridge = get_bridge()
        self.no_system = os.getenv("AGL_BENCH_NO_SYSTEM", "0").strip() == "1"
        self.system = None
        self._offline = None

        if self.no_system:
            if BaselineEngine is not None:
                try:
                    self._offline = BaselineEngine()
                except Exception:
                    self._offline = None
            return

        # Import lazily to avoid expensive module initialization when not needed.
        from agl.core.super_intelligence import AGL_Super_Intelligence

        self.system = AGL_Super_Intelligence()

    def _call_engine(self, engine: Any, prompt: str, *, prefer_dict_payload: bool = False) -> Dict[str, Any]:
        start = time.time()
        text: str = ""
        out: Dict[str, Any] = {}

        def _normalize(res: Any) -> Dict[str, Any]:
            nonlocal text
            if isinstance(res, dict):
                out0 = dict(res)
                text = str(res.get("text") or res.get("content") or res.get("answer") or res)
                return out0
            text = str(res)
            return {"ok": True, "engine": getattr(engine, "name", engine.__class__.__name__), "text": text}

        if not hasattr(engine, "process_task"):
            out = {"ok": False, "engine": "unknown", "text": "", "error": "engine has no process_task"}
        else:
            payloads: List[Any]
            dict_payload = {"query": prompt, "text": prompt}
            if prefer_dict_payload:
                payloads = [dict_payload, prompt]
            else:
                payloads = [prompt, dict_payload]

            last_error: Optional[str] = None
            for payload in payloads:
                try:
                    res = engine.process_task(payload)
                    out = _normalize(res)
                    last_error = str(out.get("error")) if isinstance(out, dict) and out.get("error") else None
                    if last_error:
                        continue
                    break
                except TypeError as e:
                    last_error = str(e)
                    continue
                except Exception as e:
                    last_error = str(e)
                    continue

            if last_error and (not isinstance(out, dict) or not out.get("error")):
                out = {"ok": False, "engine": getattr(engine, "name", engine.__class__.__name__), "text": "", "error": last_error}

        latency_ms = (time.time() - start) * 1000.0
        try:
            out.setdefault("metrics", {})
            out["metrics"]["latency_ms"] = latency_ms
        except Exception:
            pass
        return {"result": out, "latency_ms": latency_ms, "text": str(text)}

    def _looks_like_llm_error(self, text: str) -> bool:
        t = (text or "").lower()
        return "ollama exit" in t or "pull model" in t or "manifest" in t

    def _ask(self, task: BenchTask) -> Dict[str, Any]:
        reg = getattr(self.system, "engine_registry", {}) or {} if self.system is not None else {}
        prompt = task.prompt

        # Criteria suites are meant to measure the strongest end-to-end reasoning.
        # Prefer task-appropriate engines first for criteria suites; the unified system
        # can be a last resort (some paths return echoed/metadata-only strings).
        if ("criteria" in (task.tags or [])) and (self.system is not None):
            # Planning criteria: must return structured plan output
            if "planner" in (task.tags or []):
                mp = None
                try:
                    from agl.engines.micro_planner import MicroPlanner

                    mp = MicroPlanner()
                except Exception:
                    mp = None
                if mp is not None:
                    return self._call_engine(mp, prompt, prefer_dict_payload=True)

            # Hypothesis/prediction criteria: use hypothesis engine when available
            if ("autonomy" in (task.tags or [])) or ("hypothesis" in (task.id or "")):
                hyp = reg.get("HYPOTHESIS_GENERATOR")
                if hyp is not None:
                    return self._call_engine(hyp, prompt, prefer_dict_payload=True)

            # Causal criteria: try causal graph engine if it can answer in text; otherwise fall back
            if "causal" in (task.tags or []):
                causal_eng = reg.get("Causal_Graph")
                if causal_eng is not None:
                    got = self._call_engine(causal_eng, prompt, prefer_dict_payload=True)
                    if got.get("text"):
                        return got

            # Otherwise try core consciousness if enabled
            core = reg.get("Core_Consciousness_Module")
            if self.use_core_consciousness and core is not None:
                got = self._call_engine(core, prompt, prefer_dict_payload=True)
                if not self._looks_like_llm_error(got.get("text", "")):
                    return got

            # Last resort: unified system string
            start = time.time()
            try:
                text = self.system.process_query(prompt)
                out = {"ok": True, "engine": "UnifiedAGISystem", "text": str(text)}
            except Exception as e:
                out = {"ok": False, "engine": "UnifiedAGISystem", "text": "", "error": str(e)}
            latency_ms = (time.time() - start) * 1000.0
            out.setdefault("metrics", {})
            out["metrics"]["latency_ms"] = latency_ms
            return {"result": out, "latency_ms": latency_ms, "text": str(out.get("text") or "")}

        # Prefer specialized engines for deterministic scoring (works even if LLM is down)
        if any(t in (task.tags or []) for t in ("math", "logic", "text", "plan")):
            math_eng = reg.get("Mathematical_Brain")
            if math_eng is not None:
                return self._call_engine(math_eng, prompt, prefer_dict_payload=False)

        if "causal" in (task.tags or []):
            causal_eng = reg.get("Causal_Graph") or reg.get("CAUSAL_GRAPH")
            if causal_eng is not None:
                return self._call_engine(causal_eng, prompt, prefer_dict_payload=True)

        if "planner" in (task.tags or []):
            mp = reg.get("Plan-and-Execute_MicroPlanner")
            if mp is None:
                try:
                    from agl.engines.micro_planner import MicroPlanner

                    mp = MicroPlanner()
                except Exception:
                    mp = None
            if mp is not None:
                return self._call_engine(mp, prompt, prefer_dict_payload=True)

        # If we're in no-system mode, use a lightweight offline engine for non-planner tasks.
        if self.system is None:
            if self._offline is not None:
                return self._call_engine(self._offline, prompt, prefer_dict_payload=True)
            return {"result": {"ok": False, "engine": "offline", "text": "", "error": "AGL_BENCH_NO_SYSTEM and no offline engine"}, "latency_ms": 0.0, "text": ""}

        # Otherwise try core consciousness if enabled
        core = reg.get("Core_Consciousness_Module")
        if self.use_core_consciousness and core is not None:
            got = self._call_engine(core, prompt, prefer_dict_payload=True)
            if not self._looks_like_llm_error(got.get("text", "")):
                return got

        # Last resort: unified system string
        start = time.time()
        try:
            text = self.system.process_query(prompt)
            out = {"ok": True, "engine": "UnifiedAGISystem", "text": str(text)}
        except Exception as e:
            out = {"ok": False, "engine": "UnifiedAGISystem", "text": "", "error": str(e)}
        latency_ms = (time.time() - start) * 1000.0
        out.setdefault("metrics", {})
        out["metrics"]["latency_ms"] = latency_ms
        return {"result": out, "latency_ms": latency_ms, "text": str(out.get("text") or "")}

    def run(self, tasks: Optional[List[BenchTask]] = None) -> Dict[str, Any]:
        tasks = tasks or default_tasks()
        run_id = str(uuid.uuid4())
        ts = time.time()

        results: List[Dict[str, Any]] = []
        scores: List[float] = []
        oks: List[int] = []
        latencies: List[float] = []

        for task in tasks:
            rep_texts: List[str] = []
            rep_scores: List[float] = []
            rep_ok: List[bool] = []
            rep_lat: List[float] = []
            rep_engine_results: List[Any] = []

            for _ in range(self.repeats):
                got = self._ask(task)
                text = got["text"]
                rep_texts.append(text)
                rep_engine_results.append(got.get("result"))
                lat = float(got.get("latency_ms") or 0.0)
                rep_lat.append(lat)

                eval_in = text
                if "structured" in (task.tags or []):
                    try:
                        eval_in = json.dumps(got.get("result") or {}, ensure_ascii=False)
                    except Exception:
                        eval_in = str(got.get("result") or "")

                ev = task.evaluator(eval_in)
                rep_scores.append(float(ev.score))
                rep_ok.append(bool(ev.ok))

            # stability: how often outputs agree (simple exact normalized match)
            norm = [" ".join((t or "").strip().lower().split()) for t in rep_texts]
            stability = 1.0 if len(set(norm)) == 1 else (max(norm.count(x) for x in set(norm)) / len(norm))

            task_score = sum(rep_scores) / len(rep_scores)
            task_ok = all(rep_ok)
            task_latency = sum(rep_lat) / len(rep_lat)

            results.append(
                {
                    "task": {"id": task.id, "prompt": task.prompt, "tags": task.tags},
                    "repeats": self.repeats,
                    "texts": rep_texts,
                    **({"engine_results": rep_engine_results} if "structured" in (task.tags or []) else {}),
                    "score": task_score,
                    "ok": task_ok,
                    "stability": stability,
                    "latency_ms": task_latency,
                }
            )

            scores.append(task_score)
            oks.append(1 if task_ok else 0)
            latencies.append(task_latency)

            # record to bridge (best-effort)
            try:
                if self.bridge is not None and hasattr(self.bridge, "put"):
                    self.bridge.put(
                        "metric",
                        {
                            "metric": "bench_task",
                            "task_id": task.id,
                            "score": task_score,
                            "ok": task_ok,
                            "stability": stability,
                            "latency_ms": task_latency,
                            "tags": task.tags,
                        },
                        to="stm",
                        trace_id=run_id,
                    )
            except Exception:
                pass

        # Per-criterion breakdown (when tasks are tagged with criteria1..criteria5)
        crit_keys = ["criteria1", "criteria2", "criteria3", "criteria4", "criteria5"]
        crit_stats: Dict[str, Dict[str, Any]] = {}
        for ck in crit_keys:
            crit_task_oks = [1 if r.get("ok") else 0 for r in results if ck in ((r.get("task") or {}).get("tags") or [])]
            crit_stats[ck] = {
                "tasks": len(crit_task_oks),
                "accuracy": (sum(crit_task_oks) / max(1, len(crit_task_oks))) if crit_task_oks else None,
            }

        summary = {
            "run_id": run_id,
            "timestamp": ts,
            "repeats": self.repeats,
            "tasks": len(tasks),
            "accuracy": (sum(oks) / max(1, len(oks))),
            "avg_score": (sum(scores) / max(1, len(scores))),
            "avg_latency_ms": (sum(latencies) / max(1, len(latencies))),
            "criteria": crit_stats,
        }

        report = {"summary": summary, "results": results}
        out_path = os.path.join(_artifacts_dir(), "bench_runs.jsonl")
        _jsonl_append(out_path, report)

        return report
