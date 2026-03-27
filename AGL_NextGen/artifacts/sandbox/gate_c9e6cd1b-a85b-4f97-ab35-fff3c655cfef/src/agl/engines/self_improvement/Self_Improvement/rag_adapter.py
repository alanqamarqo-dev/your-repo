import os
from typing import Any, Dict

FAST_MODE = os.getenv("AGL_FAST_MODE", "0") == "1"

try:
    from agl.engines.self_improvement.Self_Improvement.rag_index import retrieve_context
except Exception:
    def retrieve_context(q, k=5):
        return ""


class RAGAdapter:
    """Simple adapter exposing RAG retrieval as an engine named 'rag'.

    Methods:
      - infer(problem): returns a proposal dict compatible with CIE.
    """

    def __init__(self):
        self.name = "rag"
        self.domains = ["knowledge", "retrieval"]

    def infer(self, problem: Dict[str, Any], context=None, timeout_s: float = 3.0) -> Dict[str, Any]:
        q = ""
        try:
            if isinstance(problem, dict):
                q = problem.get("question") or problem.get("title") or ""
            else:
                q = str(problem)
        except Exception:
            q = str(problem or "")

        try:
            ctx = retrieve_context(q, k=5) if callable(retrieve_context) else ""
        except Exception:
            ctx = ""

        score = 0.5
        novelty = 0.1
        if ctx:
            score = 0.92 if FAST_MODE else 0.86
            novelty = 0.25

        return {
            "engine": "rag",
            "content": {"answer": ctx},
            "score": float(score),
            "novelty": float(novelty),
            "meta": {"source": "rag_adapter", "k": 5},
            "domains": list(self.domains),
        }

    # compatibility shim for HostedLLM usage
    def process_task(self, task: Any):
        return self.infer(task)

