from __future__ import annotations
from typing import Any


class LawMatcher:
    """Match an input expression string against a law store using LawParser."""

    def __init__(self, store: Any, parser: Any):
        self.store = store
        self.parser = parser
        # simple aliases: map alternative variable names to canonical names
        # extend this dict as needed or accept from outside in future
        self.aliases = {"U": "V"}

    def _apply_aliases(self, s: str) -> str:
        if not s:
            return s
        out = s
        for a, b in (self.aliases or {}).items():
            # replace standalone variable occurrences (simple heuristic)
            out = out.replace(f" {a} ", f" {b} ")
            out = out.replace(f"({a})", f"({b})")
            out = out.replace(f"{a}*", f"{b}*")
            out = out.replace(f"*{a}", f"*{b}")
            out = out.replace(f"{a}", f"{b}")
        return out

    def match(self, input_expr_str: str) -> dict:
        processed = self._apply_aliases(input_expr_str)
        query = self.parser.normalize(processed)
        for law in self.store.all():
            base = self.parser.normalize(law.equation_str)
            if self.parser.equivalent(query, base):
                return {"match": law, "similarity": 1.0}
        return {"match": None, "similarity": 0.0}

    # compatibility entrypoint expected by bootstrap/tests
    def process_task(self, payload: dict) -> dict:
        try:
            action = payload.get('action')
            if action == 'match':
                q = payload.get('expr') or payload.get('query') or ''
                return {'ok': True, 'engine': 'Law_Matcher', 'match': self.match(str(q))}
            return {'ok': True, 'engine': 'Law_Matcher', 'note': 'noop'}
        except Exception as e:
            return {'ok': False, 'error': str(e)}


def create_engine(config: dict | None = None):
    """Factory used by bootstrap: returns a LawMatcher instance.

    If environment AGL_LAW_MOCK is set, returns a mock store/parser to keep tests deterministic.
    """
    import os

    class _MockStore:
        def all(self):
            return []

    class _MockParser:
        def normalize(self, s: str) -> str:
            return (s or "").strip()

        def equivalent(self, a: str, b: str) -> bool:
            return a == b

    try:
        if os.getenv("AGL_LAW_MOCK"):
            return LawMatcher(_MockStore(), _MockParser())
    except Exception:
        pass

    # fallback: try to create a LawMatcher using provided config
    store = None
    parser = None
    if config:
        store = config.get("store")
        parser = config.get("parser")
    # safe defaults
    if store is None:
        store = _MockStore()
    if parser is None:
        parser = _MockParser()
    return LawMatcher(store, parser)
