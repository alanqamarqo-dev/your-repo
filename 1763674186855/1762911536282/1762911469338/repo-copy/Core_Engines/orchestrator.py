"""Lightweight orchestrator for coordinating Core_Engines.

Responsibilities:
- route tasks to an ordered set of engines using Core_Engines.domain_router
- fan-out to multiple engines and aggregate responses
- expose a simple live priority adjustment hook for meta-cognition feedback

This module provides a minimal synchronous Orchestrator suitable for unit
tests and as a stepping stone for adding async/streaming behavior later.
"""
from typing import Dict, Any, List, Optional, Tuple
import os
from . import domain_router

# Orchestrator result limit knob
try:
    _AGL_ORCHESTRATOR_LIMIT = int(os.environ.get('AGL_ORCHESTRATOR_LIMIT', os.getenv('AGL_MAX_ACTIVE_ENGINES', '20')))
except Exception:
    _AGL_ORCHESTRATOR_LIMIT = 20


class Orchestrator:
    """Coordinate multiple engines as a single decision-making unit.

    Engine objects must expose a .process_task(payload: dict) -> dict API.
    """

    def __init__(self, engines: Optional[Dict[str, Any]] = None):
        self.engines: Dict[str, Any] = engines or {}
        self.weights: Dict[str, float] = {n: 1.0 for n in self.engines}

    def register_engine(self, name: str, engine_obj: Any) -> None:
        self.engines[name] = engine_obj
        self.weights.setdefault(name, 1.0)

    def route(self, task_type: str, limit: Optional[int] = None) -> List[str]:
        candidates = []
        try:
            candidates = domain_router.route(task_type)
        except Exception:
            # fallback: use all known engines
            candidates = list(self.engines.keys())
        filtered: List[Tuple[str, float]] = [(n, self.weights.get(n, 0.0)) for n in candidates if n in self.engines]
        filtered.sort(key=lambda x: x[1], reverse=True)
        # determine effective limit from env or module-level knob if not provided
        if limit is None:
            try:
                limit = int(_AGL_ORCHESTRATOR_LIMIT)
            except Exception:
                try:
                    limit = int(os.getenv('AGL_MAX_ACTIVE_ENGINES', '20'))
                except Exception:
                    limit = 20
        try:
            lim = int(limit)
        except Exception:
            lim = 20
        if lim <= 0:
            return [n for n, _ in filtered]
        return [n for n, _ in filtered][:lim]

    def run_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        routed = self.route(task_type)
        responses: List[Dict[str, Any]] = []
        for name in routed:
            eng = self.engines.get(name)
            if eng is None:
                responses.append({"engine": name, "error": "missing_engine", "score": 0.0})
                continue
            try:
                resp = eng.process_task(payload)
            except Exception as e:
                responses.append({"engine": name, "error": str(e), "score": 0.0})
                continue
            if not isinstance(resp, dict):
                resp = {"result": resp}
            resp.setdefault("engine", name)
            try:
                resp_score = float(resp.get("score", 0.0))
            except Exception:
                resp_score = 0.0
            resp["score"] = resp_score
            responses.append(resp)

        best = None
        if responses:
            responses.sort(key=lambda r: (r.get("score", 0.0), self.weights.get(r.get("engine", ""), 0.0)), reverse=True)
            best = responses[0]
        return {"task_type": task_type, "answers": responses, "best": best}

    def update_priorities(self, feedback: Dict[str, float]) -> None:
        for name, delta in feedback.items():
            if name not in self.weights:
                self.weights[name] = 0.0
            try:
                self.weights[name] = max(0.0, min(100.0, self.weights[name] + float(delta)))
            except Exception:
                continue


__all__ = ["Orchestrator"]


def run_meta_self_improve(registry: Any, text: str, evidence=None) -> Dict[str, Any]:
    """
    Pipeline:
      1) Causal_Graph(text) -> edges
      2) Hypothesis_Generator(text, context=edges) -> hypotheses
      3) Meta_Learning(hypotheses, edges, evidence) -> ranked
      4) AdvancedMetaReasoner(ranked) -> plan & calibrations
    """
    evidence = evidence or []
    r: Dict[str, Any] = {}

    # support multiple registry shapes
    def _get(key):
        try:
            return registry.get(key)
        except Exception:
            try:
                return registry[key]
            except Exception:
                return None

    causal = _get("CAUSAL_GRAPH") or _get("Causal_Graph")
    hyp = _get("HYPOTHESIS_GENERATOR") or _get("Hypothesis_Generator")
    meta = _get("Meta_Learning")
    amr = _get("AdvancedMetaReasoner")

    if not (causal and hyp and meta and amr):
        return {"ok": False, "error": "missing engines", "have": list(registry.keys()) if hasattr(registry, "keys") else None}

    c_out = causal.process_task({"text": text})
    edges = c_out.get("edges", [])

    h_out = hyp.process_task({"text": text, "context_edges": edges})
    hyps = h_out.get("hypotheses", [])

    m_out = meta.process_task({"text": text, "causal_edges": edges, "hypotheses": hyps, "evidence": evidence})
    ranked = m_out.get("ranked_hypotheses", [])

    a_out = amr.process_task({"ranked_hypotheses": ranked, "context_info": {"pipeline": "meta_self_improve"}})

    r["ok"] = True
    r["causal"] = c_out
    r["hypotheses"] = hyps
    r["meta"] = m_out
    r["amr"] = a_out
    return r
