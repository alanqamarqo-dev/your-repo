"""Fixed orchestrator (temporary): knowledge -> synthesis -> creative -> strategic -> language

This file is a clean, single-copy orchestrator used to run the requested
Arabic test prompt while the original file is being repaired.
"""
from Integration_Layer.Domain_Router import get_engine
import json
from typing import Any, Dict, Optional
import math


def synthesize_understanding(problem: str, gk_engine: Any, seed: int = 42, live_provider: Optional[str] = None, test_type: Optional[str] = None) -> Dict:
    out = {"summary": "", "relevant_disciplines": [], "key_concepts": [], "assumptions": []}
    if not gk_engine:
        return out

    # prepare small context hints for provider use
    ctx = []
    try:
        if hasattr(gk_engine, "ask"):
            # pass provider/test hints to the knowledge engine via context so any
            # external provider can use them when fetching facts
            if live_provider:
                ctx.append(f"provider:{live_provider}")
            if test_type:
                ctx.append(f"test_type:{test_type}")
            resp = gk_engine.ask(f"اقرأ السؤال التالي وقل ملخصاً موجزاً للمفاهيم الأساسية: {problem}", context=ctx if ctx else None)
            if isinstance(resp, dict) and resp.get("text"):
                out["summary"] = resp.get("text")
    except Exception:
        pass

    try:
        resp = gk_engine.ask(f"ما هي التخصصات العلمية والعملية الأكثر صلة بهذا السؤال: {problem}", context=ctx if ctx else None)
        if isinstance(resp, dict) and resp.get("text"):
            parts = [p.strip() for p in resp.get("text").replace('\n', ',').split(',') if p.strip()] # type: ignore
            out["relevant_disciplines"] = parts[:6]
    except Exception:
        pass

    try:
        resp = gk_engine.ask(f"حدد 3 إلى 6 مفاهيم أو افتراضات أساسية في هذا السؤال: {problem}", context=ctx if ctx else None)
        if isinstance(resp, dict) and resp.get("text"):
            parts = [p.strip() for p in resp.get("text").replace('\n', ',').split(',') if p.strip()] # type: ignore
            out["key_concepts"] = parts[:8]
    except Exception:
        pass

    return out


def validate_relevance(understanding: Dict, artifact_text: str) -> Dict:
    """Lightweight relevance check between synthesized understanding and an artifact's text.

    Returns a dict: {score: 0-1, matched: int, total: int, mismatches: [concepts_not_found]}
    """
    try:
        text = (artifact_text or "").lower()
        key_concepts = [k.lower() for k in (understanding.get("key_concepts") or []) if k]
        if not key_concepts:
            # fallback: check disciplines or summary presence
            summary = (understanding.get("summary") or "").strip()
            if not summary:
                return {"score": 0.0, "matched": 0, "total": 0, "mismatches": []}
            # if there's a summary assume weak alignment if any summary words appear
            words = [w for w in summary.split() if len(w) > 3][:8]
            matched = sum(1 for w in words if w.lower() in text)
            total = len(words) if words else 1
            return {"score": matched / total, "matched": matched, "total": total, "mismatches": [w for w in words if w.lower() not in text]}

        matched = 0
        mismatches = []
        for k in key_concepts:
            if k and k in text:
                matched += 1
            else:
                mismatches.append(k)

        total = len(key_concepts)
        score = matched / total if total > 0 else 0.0

        # Attempt semantic augmentation using embeddings if available
        try:
            from sentence_transformers import SentenceTransformer # type: ignore
            import numpy as _np
            model = SentenceTransformer('all-MiniLM-L6-v2')
            # build understanding vector from summary + key concepts
            u_text = ' '.join([understanding.get('summary') or ''] + key_concepts)
            u_emb = model.encode(u_text, convert_to_numpy=True)
            c_emb = model.encode(artifact_text or '', convert_to_numpy=True)
            # cosine similarity
            denom = (_np.linalg.norm(u_emb) * _np.linalg.norm(c_emb))
            sim = float((_np.dot(u_emb, c_emb) / denom)) if denom > 0 else 0.0
            # combine lexical score with semantic similarity (average)
            combined_score = round((score + sim) / 2.0, 3)
            return {"score": combined_score, "matched": matched, "total": total, "mismatches": mismatches, "semantic_similarity": round(sim, 3)}
        except Exception:
            return {"score": round(score, 3), "matched": matched, "total": total, "mismatches": mismatches}
    except Exception:
        return {"score": 0.0, "matched": 0, "total": 0, "mismatches": []}


def score_and_select(candidates: list, understanding: Dict, knowledge: Dict, weights: Optional[Dict] = None) -> Dict:
    """Score candidates by combining content-accuracy (alignment with understanding & knowledge)
    and structural strength (feasibility / robustness). Return selection and scores.

    Expected candidate shape: dict with text fields like 'solution' or 'idea' and optional metadata keys
    like 'feasibility', 'novelty'. If missing, defaults are used.
    """
    weights = weights or {"accuracy": 0.6, "structure": 0.4}
    results = []
    k_text = "" if not isinstance(knowledge, dict) else (knowledge.get("text") or "")

    for c in (candidates or []):
        if isinstance(c, dict):
            cand_text = c.get("solution") or c.get("idea") or json.dumps(c, ensure_ascii=False)
        else:
            cand_text = str(c)

        # accuracy: combine relevance to understanding and overlap with knowledge text
        rel = validate_relevance(understanding, cand_text)
        # simple knowledge overlap: count shared tokens (weak RAG check)
        try:
            ktoks = set([t for t in k_text.split() if len(t) > 3])
            ctoks = set([t for t in cand_text.split() if len(t) > 3])
            overlap = len(ktoks & ctoks)
            kscore = overlap / (len(ktoks) + 1)
        except Exception:
            kscore = 0.0

        accuracy = float(rel.get("score", 0.0)) * 0.75 + float(kscore) * 0.25

        # structure: prefer higher 'feasibility' or 'robustness' metadata if present
        struct = 0.5
        if isinstance(c, dict):
            if c.get("feasibility") is not None:
                try:
                    struct = float(c.get("feasibility")) # type: ignore
                except Exception:
                    struct = struct
            elif c.get("robustness") is not None:
                try:
                    struct = float(c.get("robustness")) # type: ignore
                except Exception:
                    struct = struct

        # clamp
        struct = max(0.0, min(1.0, float(struct)))

        combined = weights.get("accuracy", 0.6) * accuracy + weights.get("structure", 0.4) * struct
        results.append({"candidate": c, "accuracy": round(accuracy, 3), "structure": round(struct, 3), "score": round(combined, 0 if math.isnan(combined) else 3), "relevance": rel})

    # sort by score desc
    results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    selected = results[0] if results else None
    return {"selected": selected, "ranked": results}



def orchestrate_environment_solution(problem: str, constraints: Optional[dict] = None, seed: int = 42, live_provider: Optional[str] = None, test_type: Optional[str] = None) -> Dict:
    constraints = constraints or {}
    # ensure gk variable exists for later calls even if retrieval fails
    gk = None

    try:
        gk = get_engine("knowledge")
        # prepare context hints for the knowledge engine / external provider
        gk_ctx = constraints.get("_context", []) if isinstance(constraints, dict) else []
        if live_provider:
            gk_ctx = list(gk_ctx) + [f"provider:{live_provider}"]
        if test_type:
            gk_ctx = list(gk_ctx) + [f"test_type:{test_type}"]
        gk_out = gk.ask(problem, context=gk_ctx if gk_ctx else None) if hasattr(gk, "ask") else {"ok": False, "text": ""}
    except Exception as e:
        gk_out = {"ok": False, "error": str(e), "text": ""}

    try:
        understanding = synthesize_understanding(problem, gk if 'gk' in locals() else None, seed=seed, live_provider=live_provider, test_type=test_type)
    except Exception:
        understanding = {"summary": "", "relevant_disciplines": [], "key_concepts": [], "assumptions": []}

    constraints = dict(constraints)
    constraints.setdefault("_understanding", understanding)

    try:
        ci = get_engine("creative")
        if hasattr(ci, "design_solutions_for_hard_problems"):
            ideas = ci.design_solutions_for_hard_problems(problem, attempts=3, decomposition_depth=3, constraints=constraints)
        else:
            ideas = ci.generate_ideas(problem, n=5)
    except Exception as e:
        ideas = [{"error": str(e)}]

    # run selection & validation that balance content accuracy with structure
    try:
        selection = score_and_select(ideas, understanding, gk_out)
        ranked = selection.get("ranked", [])
        sel = selection.get("selected")
        selected_candidate = sel.get("candidate") if sel else (ideas[0] if isinstance(ideas, list) and ideas else (ideas if isinstance(ideas, dict) else {"idea": "no idea"}))
    except Exception:
        ranked = []
        selected_candidate = ideas[0] if isinstance(ideas, list) and ideas else (ideas if isinstance(ideas, dict) else {"idea": "no idea"})

    try:
        st = get_engine("strategic")
        if hasattr(st, "plan"):
            objective = selected_candidate.get("solution") if isinstance(selected_candidate, dict) and selected_candidate.get("solution") else (selected_candidate.get("idea") if isinstance(selected_candidate, dict) and selected_candidate.get("idea") else str(selected_candidate))
            try:
                plan = st.plan(objective, n=3, context={"understanding": understanding})
            except TypeError:
                plan = st.plan(objective, n=3)
        else:
            plan = {"note": "strategic engine missing plan/roadmap"}
    except Exception as e:
        plan = {"error": str(e)}

    try:
        nlp = get_engine("nlp")
        facts_for_nlp = []
        if understanding.get("summary"):
            facts_for_nlp.append({"object": understanding.get("summary"), "source": "synthesis", "confidence": 0.95})
        if isinstance(gk_out, dict) and gk_out.get("ok") and gk_out.get("text"):
            facts_for_nlp.append({"object": gk_out.get("text"), "source": gk_out.get("engine"), "confidence": 0.9})
        cand_text = selected_candidate.get("solution") if isinstance(selected_candidate, dict) and selected_candidate.get("solution") else (selected_candidate.get("idea") if isinstance(selected_candidate, dict) and selected_candidate.get("idea") else str(selected_candidate))
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

    # validate plan and explanation against the synthesized understanding
    try:
        plan_text = json.dumps(plan, ensure_ascii=False) if isinstance(plan, dict) else str(plan)
    except Exception:
        plan_text = str(plan)

    plan_validation = validate_relevance(understanding, plan_text)
    explanation_validation = validate_relevance(understanding, explanation if isinstance(explanation, str) else json.dumps(explanation, ensure_ascii=False))

    envelope = {
        "problem": problem,
        "understanding": understanding,
        "knowledge": gk_out,
        "creative_candidates": ideas,
        "ranked_candidates": ranked,
        "selected_candidate": selected_candidate,
        "strategic_plan": plan,
        "public_explanation": explanation,
        "validation": {
            "plan": plan_validation,
            "explanation": explanation_validation,
        },
    }

    return envelope
