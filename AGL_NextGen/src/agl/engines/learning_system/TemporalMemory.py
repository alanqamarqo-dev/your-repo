from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Dict
from datetime import datetime, timezone


@dataclass
class TMRecord:
    ts: datetime
    data: Dict[str, Any]


class TemporalMemory:
    """
    مخزن أحداث بسيط بوسم زمني + استعلامات بالنطاق الزمني.
    """
    def __init__(self) -> None:
        self._store: List[TMRecord] = []

    def append(self, data: Dict[str, Any], ts: datetime | None = None) -> None:
        ts = ts or datetime.now(timezone.utc)
        self._store.append(TMRecord(ts=ts, data=dict(data)))

    def range_query(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        return [r.data for r in self._store if start <= r.ts <= end]

    def latest(self, n: int = 1) -> List[Dict[str, Any]]:
        return [r.data for r in sorted(self._store, key=lambda r: r.ts, reverse=True)[:n]]
