"""Compatibility shim: re-export Integration_Layer.Domain_Router

This file exists in Core_Engines for historical reasons. The canonical
implementation lives in `Integration_Layer.Domain_Router`. To avoid breaking
imports that still reference `Core_Engines.domain_router`, we import the
integration-layer module and re-export its public names.
"""
try:
    import importlib

    _mod = importlib.import_module("Integration_Layer.Domain_Router")
    for _name in dir(_mod):
        if not _name.startswith("_"):
            globals()[_name] = getattr(_mod, _name)
    __all__ = [n for n in dir() if not n.startswith("_")]
except Exception:
    # If import fails, export an empty surface to avoid hard crashes during import
    __all__ = []

# Simple task-to-engines routing map used by the integration layer.
from typing import List, Dict

# نوع مهمة بسيط → قائمة محركات مقترحة
TASK_TO_ENGINES: Dict[str, List[str]] = {
    "math":        ["Mathematical_Brain", "Units_Validator", "Consistency_Checker"],
    "code":        ["Code_Generator", "Protocol_Designer"],
    "plan":        ["Reasoning_Planner", "Strategic_Thinking", "Meta_Learning"],
    "nlp":         ["NLP_Advanced", "Hosted_LLM"],
    "vision":      ["Visual_Spatial"],
    "knowledge":   ["GK_retriever", "GK_reasoner", "GK_verifier"],
    "causal":      ["Causal_Graph", "AdvancedMetaReasoner"],
    "law":         ["Law_Parser", "Law_Matcher", "GK_verifier"],
    "creative":    ["Creative_Innovation", "Strategic_Thinking"],
    "social":      ["Social_Interaction"],
}


def route(task_type: str) -> List[str]:
    """Return a list of engine names suitable for the given task type.

    Default: fall back to Hosted_LLM for unknown task types.
    """
    return TASK_TO_ENGINES.get(task_type, ["Hosted_LLM"])
