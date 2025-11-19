from typing import List, Any
from .GK_types import GKAnswer, GKFact
import os

# Environment-configurable evidence limit for GK reasoner components.
# Falls back to previous behaviour (3) when not set.
_GK_EVIDENCE_LIMIT = int(os.environ.get('AGL_EVIDENCE_LIMIT', os.environ.get('AGL_GK_EVIDENCE_LIMIT', '3')))

try:
    _AGL_GK_SUBJECT_PREVIEW_CHARS = int(os.environ.get('AGL_GK_SUBJECT_PREVIEW_CHARS', '20'))
except Exception:
    _AGL_GK_SUBJECT_PREVIEW_CHARS = 20


class GKReasoner:
    def __init__(self, graph, verifier):
        self.graph = graph
        self.verifier = verifier

    def infer(self, query: Any, evidences: List[Any]) -> GKAnswer:
        best = evidences[:_GK_EVIDENCE_LIMIT]
        supporting = []
        for e in best:
            # create a minimal GKFact per evidence
            subj = getattr(e, "text", "source")[:_AGL_GK_SUBJECT_PREVIEW_CHARS]
            supporting.append(
                GKFact(
                    subject=subj,
                    predicate="supports",
                    obj=getattr(e, "text", ""),
                    confidence=getattr(e, "computed_score", getattr(e, "score", 0.5)),
                    provenance=[e],
                )
            )
        contradictions = self.verifier.scan_graph(self.graph)
        text = self._compose_text(query, supporting, contradictions)
        conf = min(0.99, 0.6 + 0.1 * len(best) - 0.1 * len(contradictions))
        return GKAnswer(text, conf, supporting, contradictions)

    def _compose_text(self, query: Any, facts: List[GKFact], contradictions: List[Any]) -> str:
        if contradictions:
            return "تم العثور على معلومات متضاربة؛ أعرض أقوى رواية مدعّمة بالمصادر."
        return "الخلاصة المدعومة بالأدلة: " + (facts[0].obj if facts else "لا توجد أدلة كافية.")


def create_engine(config: dict | None = None):
    """Provide a lightweight GKReasoner instance suitable for bootstrap.

    Uses simple in-process stubs for the graph and verifier to avoid heavy
    dependencies during CI or local integration runs.
    """
    class _SimpleGraph:
        def __init__(self):
            self._nodes = []

        from typing import List, Any
        from .GK_types import GKAnswer, GKFact


        class GKReasoner:
            def __init__(self, graph, verifier):
                self.graph = graph
                self.verifier = verifier

            def infer(self, query: Any, evidences: List[Any]) -> GKAnswer:
                best = evidences[:_GK_EVIDENCE_LIMIT]
                supporting = []
                for e in best:
                    # create a minimal GKFact per evidence
                    subj = getattr(e, "text", "source")[:_AGL_GK_SUBJECT_PREVIEW_CHARS]
                    supporting.append(
                        GKFact(
                            subject=subj,
                            predicate="supports",
                            obj=getattr(e, "text", ""),
                            confidence=getattr(e, "computed_score", getattr(e, "score", 0.5)),
                            provenance=[e],
                        )
                    )
                contradictions = self.verifier.scan_graph(self.graph)
                text = self._compose_text(query, supporting, contradictions)
                conf = min(0.99, 0.6 + 0.1 * len(best) - 0.1 * len(contradictions))
                return GKAnswer(text, conf, supporting, contradictions)

            def _compose_text(self, query: Any, facts: List[GKFact], contradictions: List[Any]) -> str:
                if contradictions:
                    return "تم العثور على معلومات متضاربة؛ أعرض أقوى رواية مدعّمة بالمصادر."
                return "الخلاصة المدعومة بالأدلة: " + (facts[0].obj if facts else "لا توجد أدلة كافية.")


        def create_engine(config: dict | None = None):
            """Provide a lightweight GKReasoner-like engine for bootstrap.

            Returns an object exposing `process_task` and `name` so the bootstrap
            mechanism registers it as an engine. The implementation uses simple
            in-process stubs to avoid heavy deps during CI/local runs.
            """
            class _SimpleGraph:
                def __init__(self):
                    self._nodes = []

                def upsert(self, node):
                    self._nodes.append(node)

            class _SimpleVerifier:
                def scan_graph(self, graph):
                    return []

            core = GKReasoner(_SimpleGraph(), _SimpleVerifier())

            class _EngineWrapper:
                def __init__(self, core):
                    self.core = core
                    self.name = "GK_reasoner"

                def process_task(self, task: Any):
                    # task should be a dict: {'query': str, 'evidences': [...]}
                    q = None
                    evidences = []
                    if isinstance(task, dict):
                        q = task.get("query") or task.get("text")
                        evidences = task.get("evidences") or []
                    elif isinstance(task, str):
                        q = task

                    class _Q:
                        def __init__(self, text):
                            self.text = text

                    if q is None:
                        return {"ok": True, "answer": ""}

                    ans = core.infer(_Q(q), evidences)
                    # GKAnswer is a simple tuple-like; convert to a dict if needed
                    try:
                        return {"ok": True, "answer": ans.text, "confidence": getattr(ans, "confidence", None)}
                    except Exception:
                        return {"ok": True, "answer": str(ans)}

            return _EngineWrapper(core)
