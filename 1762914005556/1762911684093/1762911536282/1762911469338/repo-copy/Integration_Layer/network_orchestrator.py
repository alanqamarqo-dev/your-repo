"""Integration_Layer.network_orchestrator

Small, self-contained dynamic knowledge-network orchestrator.

Provides a lightweight graph of named "nodes" (callable services) and a
simple routing/message-passing API. This file is intentionally conservative
— it implements a minimal surface compatible with code that expects a
`pipeline_orchestrator` module (i.e. an object with `execute_pipeline`), and
also exposes a `NetworkOrchestrator` class for more advanced usage.

The goal: allow switching the system from a sequential pipeline to a
dynamic network of knowledge nodes with minimal changes elsewhere.
"""
from typing import Any, Callable, Dict, List, Optional, Tuple
import os
import threading
import time
import queue
import logging

logger = logging.getLogger(__name__)


class NetworkNode:
    def __init__(self, name: str, handler: Callable[[dict], dict]):
        self.name = name
        self.handler = handler

    def handle(self, message: dict) -> dict:
        try:
            return self.handler(message)
        except Exception as e:
            logger.exception("Node %s handler failed", self.name)
            return {"error": str(e)}


class NetworkOrchestrator:
    """Simple in-process network orchestrator.

    - nodes: mapping name -> NetworkNode
    - edges: adjacency mapping name -> list of (target, weight)
    - route: a simple breadth-first routing that prefers higher weight edges
    - execute_pipeline: compatibility shim that accepts a pipeline spec and
      routes messages through the network (returns aggregated outputs)
    """

    def __init__(self):
        self._nodes: Dict[str, NetworkNode] = {}
        self._edges: Dict[str, List[Tuple[str, float]]] = {}
        self._lock = threading.RLock()

    def register_node(self, name: str, handler: Callable[[dict], dict]) -> None:
        with self._lock:
            self._nodes[name] = NetworkNode(name, handler)
            self._edges.setdefault(name, [])

    def unregister_node(self, name: str) -> None:
        with self._lock:
            self._nodes.pop(name, None)
            self._edges.pop(name, None)
            # remove incoming edges
            for src, outs in list(self._edges.items()):
                self._edges[src] = [t for t in outs if t[0] != name]

    def link(self, src: str, dst: str, weight: float = 1.0) -> None:
        with self._lock:
            if src not in self._edges:
                self._edges[src] = []
            # replace existing weight for dst if present
            outs = [t for t in self._edges[src] if t[0] != dst]
            outs.append((dst, float(weight)))
            self._edges[src] = sorted(outs, key=lambda x: -x[1])

    def route(self, start: str, message: dict, max_hops: Optional[int] = None) -> Dict[str, Any]:
        """Route a message from `start` through the network and aggregate
        node responses. Returns mapping node_name -> node_response."""
        seen = set()
        out = {}
        q = queue.Queue()
        q.put((start, 0, message))

        # determine effective max_hops from env if not provided
        if max_hops is None:
            try:
                max_hops = int(os.getenv('AGL_NETWORK_MAX_HOPS', '10'))
            except Exception:
                max_hops = 10

        while not q.empty():
            node_name, depth, msg = q.get()
            if depth > max_hops:
                continue
            if node_name in seen:
                continue
            seen.add(node_name)
            node = self._nodes.get(node_name)
            if not node:
                continue
            try:
                resp = node.handle(msg)
            except Exception as e:
                resp = {"error": str(e)}
            out[node_name] = resp
            # enqueue neighbors ordered by weight
            for (nbr, w) in self._edges.get(node_name, []):
                q.put((nbr, depth + 1, resp if isinstance(resp, dict) else {"result": resp}))

        return out

    # Compatibility surface -------------------------------------------------
    def execute_pipeline(self, pipeline_spec: Any, context: Optional[dict] = None) -> dict:
        """Compatibility shim: run a simple pipeline spec against the network.

        pipeline_spec may be a list of node names or a dict {
          'start': <start_node>, 'steps': [<node>, ...]
        }

        Returns an aggregated envelope similar to Pipeline_Orchestrator.execute.
        """
        if context is None:
            context = {}
        # normalize pipeline spec
        start = None
        steps = []
        if isinstance(pipeline_spec, dict):
            start = pipeline_spec.get('start') or (pipeline_spec.get('steps') or [None])[0]
            steps = pipeline_spec.get('steps') or []
        elif isinstance(pipeline_spec, (list, tuple)):
            steps = list(pipeline_spec)
            start = steps[0] if steps else None
        elif isinstance(pipeline_spec, str):
            start = pipeline_spec
            steps = [pipeline_spec]

        if not start and steps:
            start = steps[0]

        if not start:
            return {'ok': False, 'error': 'empty_pipeline', 'result': {}}

        routed = self.route(start, {'context': context, 'spec': pipeline_spec}, max_hops=len(steps) + 2)
        # produce a simple merged result and details list
        merged = {}
        details = []
        for n, r in routed.items():
            merged[n] = r
            details.append({'node': n, 'out': r})

        # confidence heuristic: proportion of nodes that returned non-error
        ok_count = sum(1 for r in routed.values() if not (isinstance(r, dict) and 'error' in r))
        total = max(1, len(routed))
        confidence = ok_count / total
        return {'ok': True, 'result': merged, 'details': details, 'confidence': float(confidence)}


# Module-level singleton for convenience when imported as a module (like pipeline_orchestrator)
_default = NetworkOrchestrator()


def register_node(name: str, handler: Callable[[dict], dict]):
    _default.register_node(name, handler)


def execute_pipeline(pipeline_spec: Any, context: Optional[dict] = None) -> dict:
    return _default.execute_pipeline(pipeline_spec, context=context)


def route(start: str, message: dict, max_hops: Optional[int] = None) -> dict:
    return _default.route(start, message, max_hops=max_hops)


# --- AGL deliberation protocol (publish/subscribe + deliberate) ---
import os, time
from collections import defaultdict
from typing import Callable, Dict, List, Any

class DeliberationProtocol:
    """
    Very small event bus + synchronous deliberation.
    No external deps; disabled unless AGL_DELIBERATION_ENABLE=1.
    """
    def __init__(self):
        self.enabled = os.getenv("AGL_DELIBERATION_ENABLE", "0") == "1"
        self._subs: Dict[str, List[Callable[[Any], Any]]] = defaultdict(list)

    def publish(self, topic: str, payload: Any) -> None:
        if not self.enabled:
            return
        for fn in list(self._subs.get(topic, [])):
            try:
                fn(payload)
            except Exception:
                continue

    def subscribe(self, topic: str, fn: Callable[[Any], Any]) -> None:
        if not self.enabled:
            return
        self._subs[topic].append(fn)

    def deliberate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ask all subscribers of 'deliberation' for proposals; pick highest score.
        Each subscriber returns {'proposal':obj,'score':float}.
        """
        if not self.enabled:
            return {"ok": True, "decision": None, "reason": "disabled"}
        best, best_score = None, float("-inf")
        for fn in self._subs.get("deliberation", []):
            try:
                out = fn(context) or {}
                sc = float(out.get("score", 0.0))
                if sc > best_score:
                    best, best_score = out.get("proposal"), sc
            except Exception:
                continue
        return {"ok": True, "decision": best, "score": best_score, "ts": time.time()}

# ---- registry glue ----
try:
    from AGL_legacy import IntegrationRegistry as _Reg
except Exception:
    _Reg = None

def _register_deliberation_factory():
    if _Reg and hasattr(_Reg, "register_factory"):
        try:
            _Reg.register_factory("deliberation_protocol", lambda **_: DeliberationProtocol())
        except Exception:
            pass

_register_deliberation_factory()
"""Integration_Layer.network_orchestrator

Small, self-contained dynamic knowledge-network orchestrator.

Provides a lightweight graph of named "nodes" (callable services) and a
simple routing/message-passing API. This file is intentionally conservative
— it implements a minimal surface compatible with code that expects a
`pipeline_orchestrator` module (i.e. an object with `execute_pipeline`), and
also exposes a `NetworkOrchestrator` class for more advanced usage.

The goal: allow switching the system from a sequential pipeline to a
dynamic network of knowledge nodes with minimal changes elsewhere.
"""
from typing import Any, Callable, Dict, List, Optional, Tuple
import os
import threading
import time
import queue
import logging

logger = logging.getLogger(__name__)


class NetworkNode:
    def __init__(self, name: str, handler: Callable[[dict], dict]):
        self.name = name
        self.handler = handler

    def handle(self, message: dict) -> dict:
        try:
            return self.handler(message)
        except Exception as e:
            logger.exception("Node %s handler failed", self.name)
            return {"error": str(e)}


class NetworkOrchestrator:
    """Simple in-process network orchestrator.

    - nodes: mapping name -> NetworkNode
    - edges: adjacency mapping name -> list of (target, weight)
    - route: a simple breadth-first routing that prefers higher weight edges
    - execute_pipeline: compatibility shim that accepts a pipeline spec and
      routes messages through the network (returns aggregated outputs)
    """

    def __init__(self):
        self._nodes: Dict[str, NetworkNode] = {}
        self._edges: Dict[str, List[Tuple[str, float]]] = {}
        self._lock = threading.RLock()

    def register_node(self, name: str, handler: Callable[[dict], dict]) -> None:
        with self._lock:
            self._nodes[name] = NetworkNode(name, handler)
            self._edges.setdefault(name, [])

    def unregister_node(self, name: str) -> None:
        with self._lock:
            self._nodes.pop(name, None)
            self._edges.pop(name, None)
            # remove incoming edges
            for src, outs in list(self._edges.items()):
                self._edges[src] = [t for t in outs if t[0] != name]

    def link(self, src: str, dst: str, weight: float = 1.0) -> None:
        with self._lock:
            if src not in self._edges:
                self._edges[src] = []
            # replace existing weight for dst if present
            outs = [t for t in self._edges[src] if t[0] != dst]
            outs.append((dst, float(weight)))
            self._edges[src] = sorted(outs, key=lambda x: -x[1])

    def route(self, start: str, message: dict, max_hops: Optional[int] = None) -> Dict[str, Any]:
        """Route a message from `start` through the network and aggregate
        node responses. Returns mapping node_name -> node_response."""
        seen = set()
        out = {}
        q = queue.Queue()
        q.put((start, 0, message))

        # determine effective max_hops from env if not provided
        if max_hops is None:
            try:
                max_hops = int(os.getenv('AGL_NETWORK_MAX_HOPS', '10'))
            except Exception:
                max_hops = 10

        while not q.empty():
            node_name, depth, msg = q.get()
            if depth > max_hops:
                continue
            if node_name in seen:
                continue
            seen.add(node_name)
            node = self._nodes.get(node_name)
            if not node:
                continue
            try:
                resp = node.handle(msg)
            except Exception as e:
                resp = {"error": str(e)}
            out[node_name] = resp
            # enqueue neighbors ordered by weight
            for (nbr, w) in self._edges.get(node_name, []):
                q.put((nbr, depth + 1, resp if isinstance(resp, dict) else {"result": resp}))

        return out

    # Compatibility surface -------------------------------------------------
    def execute_pipeline(self, pipeline_spec: Any, context: Optional[dict] = None) -> dict:
        """Compatibility shim: run a simple pipeline spec against the network.

        pipeline_spec may be a list of node names or a dict {
          'start': <start_node>, 'steps': [<node>, ...]
        }

        Returns an aggregated envelope similar to Pipeline_Orchestrator.execute.
        """
        if context is None:
            context = {}
        # normalize pipeline spec
        start = None
        steps = []
        if isinstance(pipeline_spec, dict):
            start = pipeline_spec.get('start') or (pipeline_spec.get('steps') or [None])[0]
            steps = pipeline_spec.get('steps') or []
        elif isinstance(pipeline_spec, (list, tuple)):
            steps = list(pipeline_spec)
            start = steps[0] if steps else None
        elif isinstance(pipeline_spec, str):
            start = pipeline_spec
            steps = [pipeline_spec]

        if not start and steps:
            start = steps[0]

        if not start:
            return {'ok': False, 'error': 'empty_pipeline', 'result': {}}

        routed = self.route(start, {'context': context, 'spec': pipeline_spec}, max_hops=len(steps) + 2)
        # produce a simple merged result and details list
        merged = {}
        details = []
        for n, r in routed.items():
            merged[n] = r
            details.append({'node': n, 'out': r})

        # confidence heuristic: proportion of nodes that returned non-error
        ok_count = sum(1 for r in routed.values() if not (isinstance(r, dict) and 'error' in r))
        total = max(1, len(routed))
        confidence = ok_count / total
        return {'ok': True, 'result': merged, 'details': details, 'confidence': float(confidence)}


# Module-level singleton for convenience when imported as a module (like pipeline_orchestrator)
_default = NetworkOrchestrator()


def register_node(name: str, handler: Callable[[dict], dict]):
    _default.register_node(name, handler)


def execute_pipeline(pipeline_spec: Any, context: Optional[dict] = None) -> dict:
    return _default.execute_pipeline(pipeline_spec, context=context)


def route(start: str, message: dict, max_hops: Optional[int] = None) -> dict:
    return _default.route(start, message, max_hops=max_hops)
