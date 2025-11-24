"""Orchestrator: knowledge -> (synthesis) -> creative -> strategic -> language

Single, minimal and robust implementation: synthesizes the user's question using
the knowledge engine, calls the creative engine to generate structured ideas,
asks the strategic engine for a plan for the top idea, and uses the NLP engine
to produce a public-friendly explanation. Tolerant of missing engines.
"""
import os
from Integration_Layer.Domain_Router import get_engine
import json
from typing import Any, Dict, Optional

# router/result limits configurable via env
_AGL_ROUTER_RESULT_LIMIT = int(os.environ.get('AGL_ROUTER_RESULT_LIMIT', '8'))


def synthesize_understanding(problem: str, gk_engine: Any, seed: int = 42) -> Dict:
    out = {"summary": "", "relevant_disciplines": [], "key_concepts": [], "assumptions": []}
    if not gk_engine:
        return out

    try:
        if hasattr(gk_engine, "ask"):
            resp = gk_engine.ask(f"اقرأ السؤال التالي وقل ملخصاً موجزاً للمفاهيم الأساسية: {problem}")
            if isinstance(resp, dict) and resp.get("text"):
                out["summary"] = resp.get("text")
    except Exception:
        pass

    try:
        resp = gk_engine.ask(f"ما هي التخصصات العلمية والعملية الأكثر صلة بهذا السؤال: {problem}")
        if isinstance(resp, dict) and resp.get("text"):
            parts = [p.strip() for p in resp.get("text").replace('\n', ',').split(',') if p.strip()] # type: ignore
            out["relevant_disciplines"] = parts[:_AGL_ROUTER_RESULT_LIMIT]
    except Exception:
        pass

    try:
        resp = gk_engine.ask(f"حدد 3 إلى 6 مفاهيم أو افتراضات أساسية في هذا السؤال: {problem}")
        if isinstance(resp, dict) and resp.get("text"):
            parts = [p.strip() for p in resp.get("text").replace('\n', ',').split(',') if p.strip()] # type: ignore
            out["key_concepts"] = parts[:_AGL_ROUTER_RESULT_LIMIT]
    except Exception:
        pass

    return out


def orchestrate_environment_solution(problem: str, constraints: Optional[dict] = None, seed: int = 42) -> Dict:
    constraints = dict(constraints or {})

    # 1) Knowledge
    try:
        gk = get_engine("knowledge")
        gk_out = gk.ask(problem, context=None) if hasattr(gk, "ask") else {"ok": False, "text": ""}
    except Exception as e:
        gk_out = {"ok": False, "error": str(e), "text": ""}

    # 2) Synthesis
    try:
        understanding = synthesize_understanding(problem, gk if 'gk' in locals() else None, seed=seed) # type: ignore
    except Exception:
        understanding = {"summary": "", "relevant_disciplines": [], "key_concepts": [], "assumptions": []}

    constraints.setdefault("_understanding", understanding)

    # 3) Creative
    try:
        ci = get_engine("creative")
        if hasattr(ci, "design_solutions_for_hard_problems"):
            ideas = ci.design_solutions_for_hard_problems(problem, attempts=3, decomposition_depth=3, constraints=constraints)
        else:
            ideas = ci.generate_ideas(problem, n=5)
    except Exception as e:
        ideas = [{"error": str(e)}]

    top = ideas[0] if isinstance(ideas, list) and ideas else (ideas if isinstance(ideas, dict) else {"idea": "no idea"})

    # 4) Strategic
    try:
        st = get_engine("strategic")
        if hasattr(st, "plan"):
            objective = top.get("solution") if isinstance(top, dict) and top.get("solution") else str(top)
            try:
                plan = st.plan(objective, n=3, context={"understanding": understanding})
            except TypeError:
                plan = st.plan(objective, n=3)
        else:
            plan = {"note": "strategic engine missing plan/roadmap"}
    except Exception as e:
        plan = {"error": str(e)}

    # 5) Language
    try:
        nlp = get_engine("nlp")
        facts_for_nlp = []
        if understanding.get("summary"):
            facts_for_nlp.append({"object": understanding.get("summary"), "source": "synthesis", "confidence": 0.95})
        if isinstance(gk_out, dict) and gk_out.get("ok") and gk_out.get("text"):
            facts_for_nlp.append({"object": gk_out.get("text"), "source": gk_out.get("engine"), "confidence": 0.9})
        cand_text = (
            top.get("solution")
            if isinstance(top, dict) and top.get("solution")
            else top.get("idea") if isinstance(top, dict) else str(top)
        )
        if cand_text:
            facts_for_nlp.append({"object": cand_text, "source": "creative", "confidence": 0.8})

        if hasattr(nlp, "naturalize_answer"):
            explanation = nlp.naturalize_answer(facts_for_nlp, problem, provider_answer=None)
            if isinstance(explanation, dict) and explanation.get("text"):
                explanation = explanation.get("text")
        else:
            resp = nlp.respond(f"اشرح بلغة مبسطة الحل لهذه المشكلة: {cand_text}")
            explanation = resp.get("text") if isinstance(resp, dict) else str(resp)
    except Exception as e:
        explanation = f"(language engine error) {e}"

    envelope = {
        "problem": problem,
        "understanding": understanding,
        "knowledge": gk_out,
        "creative_candidates": ideas,
        "selected_candidate": top,
        "strategic_plan": plan,
        "public_explanation": explanation,
    }

    return envelope


if __name__ == '__main__':
    import sys
    default_q = (
        "صمم حلًا مبتكرًا لمشكلة ازدحام المرور في مدينة كبرى، مع شرح التأثيرات الاجتماعية "
        "والاقتصادية والبيئية، مستخدمًا أمثلة من أنظمة طبيعية للإلهام."
    )
    q = default_q if len(sys.argv) < 2 else " ".join(sys.argv[1:])
    out = orchestrate_environment_solution(q, constraints={"budget": 2_000_000, "timeline_days": 365}, seed=7)
    print(json.dumps(out, ensure_ascii=False, indent=2))
