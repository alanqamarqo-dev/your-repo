# agl_universal.py
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional
from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
from Integration_Layer.rag_wrapper import rag_answer  # عدِّل المسار إذا لزم
import os

DEFAULT_UNIVERSAL_SYSTEM_PROMPT = (
    "أنت طبقة الإخراج النهائية لنظام AGL.\n"
    "ستصلك نتائج من عدة محركات (تخطيط، تحليل، إبداع، استرجاع معرفي، ذاكرة...)\n"
    "مهمتك:\n"
    "1) دمج هذه النتائج.\n"
    "2) استخراج إجابة نهائية واضحة، دقيقة، ومهيكلة.\n"
    "3) إذا كانت هناك خطوات/أفكار متعارضة، اختر الأنسب مع ذكر السبب باختصار.\n"
)


def _safe_get(d: Dict[str, Any], *path: str) -> Optional[Any]:
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return None
        if key not in cur:
            return None
        cur = cur[key]
    return cur


def build_answer_context(
    problem: Dict[str, Any],
    collab_result: Dict[str, Any],
    health_snapshot: Optional[Dict[str, Any]] = None,
    max_chars: int = 6000,
) -> str:
    """
    يبني سياق نصي موحّد لتمريره إلى `rag_answer`.
    """
    parts: List[str] = []

    # السؤال / المهمة الأصلية
    question = (
        problem.get("question")
        or problem.get("prompt")
        or problem.get("task")
        or str(problem)
    )
    parts.append("### السؤال / المهمة الأصلية\n")
    parts.append(str(question))

    # الفائز (winner)
    winner = collab_result.get("winner") or {}
    parts.append("\n\n### المحرك الفائز (Winner)\n")
    parts.append(f"- engine: {winner.get('engine')}")
    parts.append(f"- score: {winner.get('score')}")
    parts.append(f"- domains: {winner.get('domains')}")
    parts.append("\nمحتوى الفائز (كما هو):\n")
    parts.append(str(winner.get("content")))

    # أفضل المقترحات (top proposals)
    top = collab_result.get("top") or []
    if top:
        parts.append("\n\n### أفضل المقترحات (Top Proposals)\n")
        for i, prop in enumerate(top, start=1):
            parts.append(f"\n#### Proposal #{i}")
            parts.append(f"- engine: {prop.get('engine')}")
            parts.append(f"- score: {prop.get('score')}")
            parts.append(f"- domains: {prop.get('domains')}")
            parts.append("المحتوى:\n")
            parts.append(str(prop.get("content")))

    # الذاكرة المجمعة
    mem = collab_result.get("memory_consolidated")
    if mem:
        parts.append("\n\n### الذاكرة المجمّعة (Memory Consolidated)\n")
        parts.append(str(mem))

    # مقتطف من مقاييس الصحة (Health Snapshot)
    if health_snapshot:
        parts.append("\n\n### مقاييس أداء المحركات (Health Snapshot)\n")
        engines = health_snapshot.get("engines") or {}
        for name, m in engines.items():
            parts.append(
                f"- {name}: calls={m.get('calls')}, "
                f"successes={m.get('successes')}, "
                f"fails={m.get('fails')}, "
                f"avg_quality={m.get('avg_quality')}, "
                f"avg_latency_ms={m.get('avg_latency_ms')}"
            )

    context = "\n".join(parts)

    # تقليم إذا تجاوز الحد
    if len(context) > max_chars:
        # نحتفظ بالجزء الأخير كي يشمل عادةً ملخصات الفائز/المقترحات
        context = context[-max_chars:]

    return context


def universal_answer(
    question: str,
    cie: Optional[CognitiveIntegrationEngine] = None,
    domains_needed: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
    max_context_chars: int = 6000,
    rag_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    واجهة موحّدة:
    - تستدعي CIE بكافة المحركات المطلوبة
    - تبني سياقاً موحّداً
    - تمرّر السياق إلى `rag_answer` لتحصل على الإجابة النهائية
    - تعيد حزمة تحتوي على الإجابة النهائية + النتائج الوسيطة
    """
    # 1) تهيئة CIE إن لم يُمرَّر
    if cie is None:
        cie = CognitiveIntegrationEngine()
        try:
            cie.connect_engines()
        except Exception:
            # إذا كان هناك اختلاف بالاسم استخدم واجهة ربط أخرى أو تجاوز
            pass

    # 2) نطاقات افتراضية إن لم تحدد
    if domains_needed is None:
        domains_needed = ["language", "analysis", "knowledge"]

    # 3) بناء كائن المشكلة الموحد
    problem: Dict[str, Any] = {
        "mode": "universal_answer",
        "question": question,
        "task": "answer_user_question",
    }

    # 4) استدعاء التعاون الجماعي
    collab_result = cie.collaborative_solve(
        problem,
        domains_needed=tuple(domains_needed),
    )

    # 5) لقطة من HealthMonitor إن وجدت
    health_snapshot: Optional[Dict[str, Any]] = None
    try:
        if hasattr(cie, "health") and callable(getattr(cie.health, "snapshot", None)):
            health_snapshot = cie.health.snapshot()
    except Exception:
        health_snapshot = None

    # 6) بناء السياق
    context = build_answer_context(
        problem=problem,
        collab_result=collab_result,
        health_snapshot=health_snapshot,
        max_chars=max_context_chars,
    )

    # 7) استدعاء RAG (مع مرونة لتواقيع مختلفة)
    if system_prompt is None:
        system_prompt = DEFAULT_UNIVERSAL_SYSTEM_PROMPT
    if rag_kwargs is None:
        rag_kwargs = {}

    # بعض إصدارات rag_answer قد تتطلب تواقيع مختلفة؛ نجرب النداء بأكثر من شكل
    final_answer = None
    try:
        # افتراضي: rag_answer(question=..., context=..., system_prompt=..., **kwargs)
        final_answer = rag_answer(
            question=question,
            context=context,
            system_prompt=system_prompt,
            **rag_kwargs,
        )
    except TypeError:
        try:
            # بديل: rag_answer(question, context, system_prompt, **kwargs)
            final_answer = rag_answer(question, context, system_prompt, **(rag_kwargs or {}))
        except TypeError:
            try:
                # بديل مبسط: rag_answer(question, context)
                final_answer = rag_answer(question, context)
            except Exception as exc:
                # فشل كل المحاولات -> نعيد استجابة احتياطية
                final_answer = {
                    "_error": "rag_call_failed",
                    "exc": str(exc),
                    "fallback_summary": "لم يتم توليد إجابة نهائية بسبب فشل استدعاء RAG",
                }

    # 8) حزمة الإرجاع
    return {
        "answer": final_answer,
        "question": question,
        "context": context,
        "cie_result": collab_result,
        "health": health_snapshot,
    }


def solve_universal(
    problem: Dict[str, Any],
    domains_needed: Optional[List[str]] = None,
    fanout_all: bool = True,
    cie: Optional[CognitiveIntegrationEngine] = None,
) -> Dict[str, Any]:
    """
    واجهة مبسطة تُستخدم كسكربت إدخال واحد:
    - تُعدّل env لتمكين fanout (اختياري)
    - تُنشئ/تستخدم CIE وتستدعي `collaborative_solve`
    - تُرجع حزمة (bundle) تحتوي على winner/top/memory_consolidated/health
    """
    if fanout_all:
        try:
            os.environ["AGL_FANOUT_ALL"] = "1"
        except Exception:
            pass

    if cie is None:
        cie = CognitiveIntegrationEngine()
        try:
            cie.connect_engines()
        except Exception:
            # best-effort connect
            pass

    if domains_needed is None:
        domains_needed = ("analysis", "language", "knowledge")

    collab_result = cie.collaborative_solve(
        problem,
        domains_needed=tuple(domains_needed),
    )

    # health snapshot if available
    health_snapshot = None
    try:
        if hasattr(cie, "health") and callable(getattr(cie.health, "snapshot", None)):
            health_snapshot = cie.health.snapshot()
    except Exception:
        health_snapshot = None

    bundle = {
        "problem": problem,
        "winner": collab_result.get("winner"),
        "top": collab_result.get("top"),
        "memory_consolidated": collab_result.get("memory_consolidated"),
        "cie_result": collab_result,
        "health": health_snapshot,
    }

    return bundle


if __name__ == "__main__":
    # مثال سريع للاختبار اليدوي
    q = "صمّم نظام تعليم ذكي لليمن بحلول عام 2030 يدمج التعليم الحضوري والرقمي."
    cie = CognitiveIntegrationEngine()
    try:
        cie.connect_engines()
    except Exception:
        pass

    result = universal_answer(q, cie=cie)
    print("\n================= ANSWER =================\n")
    print(result["answer"])
    print("\n================= WINNER =================\n")
    print(result["cie_result"].get("winner"))
