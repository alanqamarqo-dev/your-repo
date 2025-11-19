# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_PREVIEW_20 = _to_int('AGL_PREVIEW_20', 20)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
from typing import List, Any
from .GK_types import GKAnswer, GKFact
import os
_GK_EVIDENCE_LIMIT = int(os.environ.get('AGL_EVIDENCE_LIMIT', os.environ.get('AGL_GK_EVIDENCE_LIMIT', '3')))
class GKReasoner:
    def __init__(self, graph, verifier):
        self.graph = graph
        self.verifier = verifier
    def infer(self, query: Any, evidences: List[Any]) -> GKAnswer:
        best = evidences[:_GK_EVIDENCE_LIMIT]
        supporting = []
        for e in best:
            subj = getattr(e, 'text', 'source')[:_AGL_PREVIEW_20]
            supporting.append(GKFact(subject=subj, predicate='supports', obj=getattr(e, 'text', ''), confidence=getattr(e, 'computed_score', getattr(e, 'score', 0.5)), provenance=[e]))
        contradictions = self.verifier.scan_graph(self.graph)
        text = self._compose_text(query, supporting, contradictions)
        conf = min(0.99, 0.6 + 0.1 * len(best) - 0.1 * len(contradictions))
        return GKAnswer(text, conf, supporting, contradictions)
    def _compose_text(self, query: Any, facts: List[GKFact], contradictions: List[Any]) -> str:
        if contradictions:
            return 'تم العثور على معلومات متضاربة؛ أعرض أقوى رواية مدعّمة بالمصادر.'
        return 'الخلاصة المدعومة بالأدلة: ' + (facts[0].obj if facts else 'لا توجد أدلة كافية.')
def create_engine(config: dict | None=None):
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
            self.name = 'GK_reasoner'
        def process_task(self, task: Any):
            q = None
            evidences = []
            if isinstance(task, dict):
                q = task.get('query') or task.get('text')
                evidences = task.get('evidences') or []
            elif isinstance(task, str):
                q = task
            class _Q:
                def __init__(self, text):
                    self.text = text
            if q is None:
                return {'ok': True, 'answer': ''}
            ans = core.infer(_Q(q), evidences)
            return {'ok': True, 'answer': getattr(ans, 'text', str(ans)), 'confidence': getattr(ans, 'confidence', None)}
    return _EngineWrapper(core)
