from typing import Dict, Any
import logging

logger = logging.getLogger("AGL.Orchestrator")

def run_causal_and_hypothesis(registry, text: str) -> Dict[str, Any]:
    """
    يستدعي Causal_Graph ثم Hypothesis_Generator ويدمج النتائج.
    """
    out: Dict[str, Any] = {"ok": True, "bundle": {}, "errors": []}

    # 1) causal
    try:
        causal = registry.get("CAUSAL_GRAPH") if hasattr(registry, "get") else registry.get("CAUSAL_GRAPH")
        causal_res = causal.process_task({"text": text}) if causal else {"edges": []}
        out["bundle"]["causal"] = causal_res
    except Exception as e:
        out["ok"] = False
        out["errors"].append(f"causal_error:{e}")
        out["bundle"]["causal"] = {"edges": []}

    # 2) hypotheses (مرّر ملخص السببية كمحتوى سياقي)
    try:
        hypo = registry.get("HYPOTHESIS_GENERATOR") if hasattr(registry, "get") else registry.get("HYPOTHESIS_GENERATOR")
        causal_summary = ""
        edges = out["bundle"].get("causal", {}).get("edges", [])
        if edges:
            first = edges[0]
            causal_summary = f"سبب: {first.get('cause','…')} -> أثر: {first.get('effect','…')}"
        hyp_res = hypo.process_task({
            "topic": "تحليل سببي للنص",
            "context": text + "\n" + causal_summary
        }) if hypo else {"hypotheses": []}
        out["bundle"]["hypotheses"] = hyp_res
    except Exception as e:
        out["ok"] = False
        out["errors"].append(f"hypothesis_error:{e}")
        out["bundle"]["hypotheses"] = {"hypotheses": []}

    return out
