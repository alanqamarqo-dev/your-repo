"""Lightweight RAG fallback providing a simple answer structure.
Used when the real RAG module isn't available.
"""
from typing import List, Dict, Any


class RagFallback:
    def __init__(self):
        pass

    def answer(self, query: str, contexts: List[dict] = None) -> Dict[str, Any]:
        return {"answer": "", "sources": []}

    # some callers expect a module-level function; provide it too
def answer_with_rag(query: str, contexts: List[dict] = None) -> Dict[str, Any]:
    return RagFallback().answer(query, contexts)
