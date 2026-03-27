from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os


@dataclass
class CognitiveMode:
    """إعدادات نمط التفكير لمهمة واحدة."""

    use_cot: bool
    cot_depth: str  # "none" / "short" / "deep"
    samples: int
    use_rag: bool
    use_internal_agents: bool
    use_self_critique: bool
    risk_level: str  # "low" / "medium" / "high"


def _text_from_problem(problem: Dict[str, Any]) -> str:
    title = str(problem.get("title") or "")
    question = str(problem.get("question") or "")
    return f"{title} {question}".strip().lower()


def _is_medical_high_risk(problem: Dict[str, Any]) -> bool:
    """يكتشف إن السؤال طبي وحساس/خطر نسبياً."""
    text = _text_from_problem(problem)
    medical_kw = [
        "ارتفاع ضغط",
        "ضغط الدم",
        "سكري",
        "السكري",
        "فشل كلوي",
        "كلوي",
        "kidney",
        "renal",
        "dose",
        "جرعة",
        "جرعات",
        "سمية",
        "toxicity",
        "مضاعفات",
        "complications",
    ]
    hits = sum(1 for kw in medical_kw if kw in text)
    return hits >= 2


def _is_simple_factoid(problem: Dict[str, Any]) -> bool:
    """أسئلة معلوماتية بسيطة مثل: تعريف، أعراض، أسباب بدون تعقيد كبير."""
    text = _text_from_problem(problem)
    simple_kw = ["عرّف", "تعريف", "what is", "ما هو", "ما هي", "أعراض", "symptoms"]
    hits = sum(1 for kw in simple_kw if kw in text)
    return hits >= 1 and len(text) < 140  # سؤال قصير نسبيًا


def _is_planning_or_project(problem: Dict[str, Any]) -> bool:
    text = _text_from_problem(problem)
    plan_kw = ["خطة", "تخطيط", "مشروع", "roadmap", "plan", "steps", "مراحل"]
    hits = sum(1 for kw in plan_kw if kw in text)
    return hits >= 1


def choose_cognitive_mode(
    problem: Dict[str, Any],
    runtime_context: Optional[Dict[str, Any]] = None,
    profile_snapshot: Optional[Dict[str, Any]] = None,
) -> CognitiveMode:
    """
    يختار نمط التفكير بناءً على:
    - نص السؤال
    - نوع المجال (إن وُجد)
    - سياق التنفيذ (مثلاً ميزانية الوقت)
    - بروفايل النظام (لو أرسلت له)
    يحترم متغيّر البيئة `AGL_FAST_MODE` لجعل الاختبارات سريعة.
    """
    fast = os.getenv("AGL_FAST_MODE") == "1"

    # إعدادات افتراضية آمنة
    mode = CognitiveMode(
        use_cot=False,
        cot_depth="none",
        samples=1,
        use_rag=False,
        use_internal_agents=False,
        use_self_critique=False,
        risk_level="low",
    )

    # 1) أسئلة بسيطة → إجابة مباشرة أو CoT قصير فقط
    if _is_simple_factoid(problem) and not _is_medical_high_risk(problem):
        mode.use_cot = not fast  # في الوضع العادي: CoT قصير، في FAST: بدون
        mode.cot_depth = "short" if mode.use_cot else "none"
        mode.samples = 1
        mode.use_rag = False
        mode.use_internal_agents = True
        mode.use_self_critique = False
        mode.risk_level = "low"
        return mode

    # 2) أسئلة تخطيط/مشروع → تفكير أعمق قليلًا
    if _is_planning_or_project(problem):
        mode.use_cot = True
        mode.cot_depth = "short" if fast else "deep"
        mode.samples = 1 if fast else 2
        mode.use_rag = False
        mode.use_internal_agents = True
        mode.use_self_critique = not fast
        mode.risk_level = "medium"
        return mode

    # 3) حالات طبية عالية الخطورة → CoT عميق + self-critique
    if _is_medical_high_risk(problem):
        mode.use_cot = True
        mode.cot_depth = "deep"
        mode.samples = 1 if fast else 3
        mode.use_rag = not fast
        mode.use_internal_agents = True
        mode.use_self_critique = not fast
        mode.risk_level = "high"
        return mode

    # 4) باقي الحالات العامة
    mode.use_cot = not fast
    mode.cot_depth = "short" if mode.use_cot else "none"
    mode.samples = 1
    mode.use_rag = False
    mode.use_internal_agents = True
    mode.use_self_critique = not fast
    mode.risk_level = "medium"
    return mode
