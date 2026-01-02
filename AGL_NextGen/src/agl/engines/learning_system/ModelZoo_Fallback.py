"""Lightweight fallback ModelZoo used when the real ModelZoo isn't available.

This provides a minimal API expected by consumers: list_models() and get(name).
"""
from typing import List, Optional


class ModelZooFallback:
    def __init__(self):
        # a tiny in-memory registry of placeholder models
        self._models = {"baseline": None}

    def list_models(self) -> List[str]:
        return list(self._models.keys())

    def get(self, name: str = "baseline") -> Optional[object]:
        # Return None meaning no real model available; callers should handle this.
        return self._models.get(name)
