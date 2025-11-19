import os
from typing import List, Any, Optional

# conservative evidence limit for verifier work
try:
    _AGL_VERIFIER_EVIDENCE_LIMIT = int(
        os.environ.get("AGL_VERIFIER_EVIDENCE_LIMIT", "5")
    )
except Exception:
    _AGL_VERIFIER_EVIDENCE_LIMIT = 5
# controlled by AGL_VERIFIER_EVIDENCE_LIMIT (default 5)


class GKVerifier:
    """Minimal verifier engine that scores a small, configurable set
    of evidences and finds simple contradictions in a graph.
    """

    def __init__(self, **kwargs):
        self.name = "GK_verifier"

    def score_and_check(self, evidences: Optional[List[Any]]) -> List[Any]:
        """Score up to _AGL_VERIFIER_EVIDENCE_LIMIT evidences.

        Returns the list of evidences with a computed_score attribute attached
        for downstream consumers. This is intentionally conservative and
        deterministic to avoid behavioral surprises.
        """
        out: List[Any] = []
        try:
            for e in (evidences or [])[:_AGL_VERIFIER_EVIDENCE_LIMIT]:
                score = getattr(e, "score", 0.5)
                # boost score for locally-provided evidence
                src = getattr(e, "source", None)
                if src and getattr(src, "provider", "") == "local":
                    score = min(0.95, score + 0.2)
                try:
                    e.computed_score = float(score)
                except Exception:
                    e.computed_score = 0.5
                out.append(e)
        except Exception:
            # keep the verifier robust on unexpected evidence shapes
            pass
        return out

    def scan_graph(self, graph) -> List[Any]:
        """Find simple contradictions in a graph represented with
        an 'edges' iterable of (s, p, o, weight) tuples.
        """
        contradictions: List[Any] = []
        seen = {}
        for edge in getattr(graph, "edges", []):
            if not isinstance(edge, (list, tuple)) or len(edge) < 3:
                continue
            s, p, o = edge[0], edge[1], edge[2]
            key = (s, p)
            if key in seen and seen[key] != o:
                contradictions.append({"subject": s, "predicate": p, "values": [seen[key], o]})
            seen[key] = o
        return contradictions

    def process_task(self, payload: dict) -> dict:
        """Process simple tasks: 'score' or 'scan'.

        - score: expects payload['evidences'] -> returns {'scored': [...]}
        - scan: expects payload['graph'] -> returns {'contradictions': [...]}
        """
        try:
            action = payload.get("action")
            if action == "score":
                evidences = payload.get("evidences", [])
                return {"ok": True, "scored": self.score_and_check(evidences)}
            if action == "scan":
                return {"ok": True, "contradictions": self.scan_graph(payload.get("graph"))}
            return {"ok": True, "msg": "noop"}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def create_engine(config: Optional[dict] = None) -> GKVerifier:
    """Factory function used by other parts of the system to create a verifier.

    The function preserves the older create_engine() contract used elsewhere
    in the codebase while keeping the implementation simple and import-safe.
    """
    return GKVerifier()


__all__ = ["GKVerifier", "create_engine", "_AGL_VERIFIER_EVIDENCE_LIMIT"]
