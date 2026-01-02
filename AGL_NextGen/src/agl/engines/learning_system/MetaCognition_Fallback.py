"""Simple meta-cognition fallback that evaluates a plan and returns a score and notes."""

from typing import Dict, Any


class MetaCognitionFallback:
    def __init__(self):
        pass

    def evaluate(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 0.5, "notes": "fallback meta-cognition evaluation"}
