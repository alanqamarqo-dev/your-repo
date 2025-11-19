"""A tiny in-process priority message bus used by the DKN (blackboard).

This is deliberately simple and synchronous (blocking pop with timeout).
It is not an asyncio implementation to keep integration with existing tests
and the repo simple; it uses a heapq priority queue keyed by -score.
"""
import heapq
import time
from typing import Optional


class PriorityBus:
    def __init__(self):
        # heap elements: (-score, ts, seq, message)
        self._q = []
        self._seq = 0

    def publish(self, signal):
        # signal: should have .score and .ts
        score = float(getattr(signal, 'score', 0.0) or 0.0)
        ts = float(getattr(signal, 'ts', time.time()))
        self._seq += 1
        heapq.heappush(self._q, (-score, ts, self._seq, signal))

    def pop(self, timeout: float = 0.0):
        start = time.time()
        while True:
            if self._q:
                return heapq.heappop(self._q)[3]
            if timeout <= 0:
                return None
            if time.time() - start >= timeout:
                return None
            time.sleep(min(0.01, timeout))
