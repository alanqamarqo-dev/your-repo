"""Compatibility shim for Knowledge_Graph.

Some callers import `Knowledge_Base.Knowledge_Graph`. The real adapter is
implemented in `Self_Improvement.Knowledge_Graph`. This file re-exports the
class and ensures the IntegrationRegistry factory remains available under the
expected module path.
"""
from typing import Any

try:
    # import the implementation from Self_Improvement
    from Self_Improvement.Knowledge_Graph import AssociativeGraph  # type: ignore
except Exception:
    # fallback stub
    class AssociativeGraph:  # type: ignore
        def __init__(self):
            self.enabled = False
        def add_edge(self, *a, **k):
            return
        def neighbors(self, *a, **k):
            return []
        def find_associates(self, *a, **k):
            return []

# Re-register factory if the original module registered under IntegrationRegistry
try:
    from AGL_legacy import IntegrationRegistry as _Reg
except Exception:
    _Reg = None

def _register_compat_factory():
    if _Reg and hasattr(_Reg, "register_factory"):
        try:
            # Register the same factory under the Knowledge_Base path as a convenience
            _Reg.register_factory("associative_graph", lambda **kw: AssociativeGraph())
        except Exception:
            pass

_register_compat_factory()
