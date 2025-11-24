"""Demo script for the domain router using mock engines.

Run from project root:
  $env:PYTHONPATH='D:\AGL'; py -3 tools\domain_router_demo.py
"""
import json
from Core_Engines.turn_contract import make_turn
from Core_Engines.domain_router import route_turn, orchestrate_turn


def _mock_algebra(turn):
    q = turn.get("query", {}).get("text", "")
    # pretend we solved it
    return {"ok": True, "text": f"حل جبري (مبسّط) لـ: {q}", "sources": ["algebra_engine"]}


def _mock_rag(turn):
    q = turn.get("query", {}).get("text", "")
    return {"ok": True, "text": f"مقتطفات مستخرجة عن: {q}", "sources": ["local_repo", "docs.pdf"]}


def _mock_llm(turn_or_payload):
    # payload may be the turn or a simple dict with text
    if isinstance(turn_or_payload, dict) and turn_or_payload.get("text"):
        prompt = turn_or_payload.get("text")
    else:
        prompt = (turn_or_payload or {}).get("query", {}).get("text", "")
    return {"ok": True, "text": f"LLM صياغة نهائية: {prompt}", "sources": []}


def _mock_causal(turn):
    return {"ok": True, "text": "سلسلة سببية مبسطة...", "sources": ["causal_db"]}


def _mock_planner(turn):
    return {"ok": True, "text": "Planner: أجريت جدولاً للمهام المطلوبة.", "sources": []}


ENGINES = {
    "algebra": _mock_algebra,
    "units": lambda t: {"ok": True, "text": "units checked", "sources": []},
    "numeric_checker": lambda t: {"ok": True, "text": "numeric ok", "sources": []},
    "llm": _mock_llm,
    "rag": _mock_rag,
    "causal_engine": _mock_causal,
    "consistency_checker": lambda p: {"ok": True, "text": "consistent", "sources": []},
    "planner": _mock_planner,
}


def demo_queries():
    queries = [
        "حل المعادلة x^2 - 3x + 2 = 0",
        "لماذا يحدث الاحتراق عندما نوفر أوكسجين؟",
        "ما هو تعريف التحفيز؟ أرجو ذكر المصادر",
        "مرحبا، كيف حالك؟",
        "شغّل المهمة المجدولة لتحديث التقارير"
    ]

    for q in queries:
        turn = make_turn(q)
        routed = route_turn(turn)
        final = orchestrate_turn(routed, ENGINES)
        print('\n--- QUERY ---')
        print(q)
        print('\n--- ROUTING ---')
        print(json.dumps(routed.get('routing', {}), ensure_ascii=False, indent=2))
        print('\n--- FINAL TURN ---')
        print(json.dumps(final, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    demo_queries()
