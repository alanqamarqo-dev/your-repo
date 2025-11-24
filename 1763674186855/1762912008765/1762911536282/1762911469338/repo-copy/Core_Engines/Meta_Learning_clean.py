"""
Clean Meta_Learning implementation used as a safe replacement while the
original file is being repaired. Keeps a small, stable API (create_engine).
"""

from typing import Any, Dict, List, Optional
import os

# configurable cap for number of hypotheses to consider
try:
    _AGL_META_HYPS_LIMIT = int(os.environ.get('AGL_META_HYPS_LIMIT', '8'))
except Exception:
    _AGL_META_HYPS_LIMIT = 8
# controlled by AGL_META_HYPS_LIMIT (default 8)


class MetaLearningEngine:
    """Simple meta-learner: rank hypotheses using light heuristics."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = "Meta_Learning"
        self.config = config or {}

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        hyps: List[str] = (payload.get("hypotheses") or [])[:_AGL_META_HYPS_LIMIT]
        edges = payload.get("causal_edges") or []
        evid = payload.get("evidence") or []

        boost_words = ("سبب", "ينتج", "يسبب", "if", "because", "causal", "leads to")
        scored: List[Dict[str, Any]] = []
        for h in hyps:
            base = 0.4 + 0.05 * len(edges) + 0.03 * len(evid)
            if any(w in h for w in boost_words):
                base += 0.2
            score = max(0.0, min(1.0, base))
            scored.append({"hypothesis": h, "score": round(score, 3)})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return {
            "engine": self.name,
            "ok": True,
            "ranked_hypotheses": scored,
            "meta_summary": {
                "n_inputs": {"edges": len(edges), "hypotheses": len(hyps), "evidence": len(evid)},
                "hint": "تمت المفاضلة بحسب إشارات السببية والأدلة المتاحة."
            },
        }


def create_engine(config: Optional[Dict[str, Any]] = None) -> MetaLearningEngine:
    return MetaLearningEngine(config=config)
