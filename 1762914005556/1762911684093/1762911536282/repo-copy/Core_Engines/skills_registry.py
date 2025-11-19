"""
Skills registry and tool runner.

Defines a SKILLS mapping (name -> input/output schema) and a ToolRunner that
validates and executes registered callables. The orchestrator can ask an LLM
to propose a tool call (JSON) and then use ToolRunner to run it and feed the
result back to the LLM for final phrasing.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, Iterable, List, Optional


SKILLS: Dict[str, Dict[str, Any]] = {
    "exp_algebra.solve": {"in": {"expr": "str"}, "out": {"value": "float", "steps": "str"}},
    "causal.infer": {"in": {"facts": "list[str]", "rules": "list[str]"}, "out": {"conclusion": "str", "explain": "str"}},
    "rag.search": {"in": {"query": "str", "k": "int"}, "out": {"chunks": "list[dict]"}},
    "safety.review": {"in": {"text": "str"}, "out": {"passed": "bool", "flags": "list[str]"}},
}


class ToolRunner:
    """Register and execute tools defined in SKILLS.

    Tools are simple callables that accept a dict of args and return a dict
    that at least contains keys from the declared output schema.
    """

    def __init__(self):
        self._registry: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}

    def register(self, name: str, fn: Callable[[Dict[str, Any]], Dict[str, Any]]):
        if name not in SKILLS:
            raise ValueError(f"Skill {name} not declared in SKILLS")
        self._registry[name] = fn

    def available(self) -> List[str]:
        return list(self._registry.keys())

    def _validate_args(self, name: str, args: Dict[str, Any]) -> Optional[str]:
        schema = SKILLS.get(name, {})
        req = schema.get("in", {})
        for k, t in req.items():
            if k not in args:
                return f"missing_arg:{k}"
        return None

    def run(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self._registry:
            return {"ok": False, "error": f"tool_not_registered:{name}"}
        err = self._validate_args(name, args)
        if err:
            return {"ok": False, "error": err}
        try:
            res = self._registry[name](args)
            # best-effort wrap
            if not isinstance(res, dict):
                return {"ok": False, "error": "tool_returned_non_dict"}
            res.setdefault("ok", True)
            return res
        except Exception as e:
            return {"ok": False, "error": str(e)}
