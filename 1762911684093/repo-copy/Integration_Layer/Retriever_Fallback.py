"""Lightweight retriever fallback that returns an empty list of contexts.
Used when a real retriever is not available.
"""
from typing import List


class RetrieverFallback:
    def __init__(self):
        pass

    def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        """Return an empty list indicating no retrieved contexts."""
        return []
