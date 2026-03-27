from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Dict, List, Optional


@dataclass
class AdaptiveMemoryItem:
    content: str
    timestamp: float
    importance: float = 0.5
    tags: List[str] | None = None
    context: Dict[str, Any] | None = None


class AdaptiveMemory:
    """Lightweight adaptive memory.

    Purpose:
      - Provide a real object for `engine_registry['AdaptiveMemory']`.
      - Keep it dependency-light and compatible with `ConsciousBridge` if available.

    This is intentionally minimal: UnifiedMemorySystem currently doesn't call into it,
    but other components may.
    """

    name = "AdaptiveMemory"

    def __init__(self, bridge: Any | None = None, max_items: int = 200) -> None:
        self.bridge = bridge
        self.max_items = max_items
        self._buffer: List[AdaptiveMemoryItem] = []

    def store(
        self,
        content: str,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        item = AdaptiveMemoryItem(
            content=content,
            timestamp=time.time(),
            importance=float(importance or 0.5),
            tags=list(tags) if tags else [],
            context=dict(context) if context else {},
        )
        self._buffer.append(item)
        if len(self._buffer) > self.max_items:
            self._buffer = self._buffer[-self.max_items :]

        # Best-effort bridge write
        try:
            if self.bridge is not None and hasattr(self.bridge, "put"):
                self.bridge.put(
                    "adaptive_memory",
                    {
                        "content": item.content,
                        "importance": item.importance,
                        "tags": item.tags,
                        "context": item.context,
                        "timestamp": item.timestamp,
                    },
                    to="stm",
                )
        except Exception:
            pass

        return {
            "ok": True,
            "engine": "AdaptiveMemory",
            "timestamp": item.timestamp,
        }

    def recall(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        q = (query or "").lower().strip()
        if not q:
            return []

        scored: List[tuple[float, AdaptiveMemoryItem]] = []
        for item in self._buffer:
            text = item.content.lower()
            score = 0.0
            if q in text:
                score += 1.0
            # simple token overlap
            for w in q.split():
                if w and w in text:
                    score += 0.2
            score *= (0.5 + float(item.importance))
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "content": it.content,
                "timestamp": it.timestamp,
                "importance": it.importance,
                "tags": it.tags or [],
                "context": it.context or {},
            }
            for _, it in scored[: max(1, int(top_k or 5))]
        ]
