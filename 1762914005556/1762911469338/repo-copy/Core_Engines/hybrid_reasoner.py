# AGL/Core_Engines/hybrid_reasoner.py
from typing import Dict, Any, List
import re

KEYS_IRRIG = ["مضخ", "تدفق", "ضغط", "رشاش", "شبك", "جاذبي", "أنابيب", "تنقيط", "صمام"]
KEYS_TRAFF = ["إشار", "مرور", "تقاطع", "تدفق المركبات", "أولوية", "حارات", "توقيت"]
KEYS_LINK  = ["تشابه", "تماثل", "محاكاة", "تطبيق نفس", "خرائط", "قانون حفظ", "نموذج شبكي"]


def _score(text: str, keys: List[str]) -> int:
    t = text or ""
    return sum(1 for k in keys if k in t)


def _dedupe_lines(lines: List[str]) -> List[str]:
    seen, out = set(), []
    for ln in lines:
        k = re.sub(r"\s+", " ", ln.strip())
        if len(k) >= 3 and k not in seen:
            seen.add(k); out.append(ln)
    return out


def _outline(text: str) -> List[str]:
    # بسّط استخراج نقاط رئيسية
    parts = re.split(r"[•\-\u2022]|[\n\r]+", text or "")
    parts = [p.strip(" -\t") for p in parts if p.strip()]
    try:
        import os
        _OUTLINE_LIMIT = int(os.environ.get('AGL_HYBRID_OUTLINE_LIMIT', '40'))
    except Exception:
        _OUTLINE_LIMIT = 40
    return _dedupe_lines(parts[:_OUTLINE_LIMIT])


def unify(question: str, llm: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    t_llm  = llm.get("text") or llm.get("reply_text") or llm.get("answer") or ""
    t_meta = meta.get("text") or meta.get("reply_text") or meta.get("answer") or ""
    # تقييم بسيط للمجالين والربط
    s_llm  = _score(t_llm,  KEYS_IRRIG)+_score(t_llm,  KEYS_TRAFF)+_score(t_llm,  KEYS_LINK)
    s_meta = _score(t_meta, KEYS_IRRIG)+_score(t_meta, KEYS_TRAFF)+_score(t_meta, KEYS_LINK)

    # ادمج مخططين ثم ألّف جوابًا موحّدًا
    ol = _outline(t_llm); om = _outline(t_meta)
    merged = _dedupe_lines(ol + om)

    # إن لم نجد نقاط كافية، نعيد الأفضل نصًا كما هو
    best_text = t_llm if s_llm >= s_meta else t_meta
    try:
        import os
        _HYBRID_MIN_POINTS = int(os.environ.get('AGL_HYBRID_MIN_POINTS', '4'))
    except Exception:
        _HYBRID_MIN_POINTS = 4

    if len(merged) < _HYBRID_MIN_POINTS:
        return {
            "ok": True,
            "mode": "fallback_best",
            "text": best_text
        }

    # تركيب نهائي منسّق
    header = "حلّ موحّد (نهج هجين: تحليل + توليد)\n"
    body = "\n".join(f"- {x}" for x in merged)
    footer = "\n\nخلاصة: جُمعت النقاط أعلاه بعد ترجيح الصلة بالمجالين وربط المبادئ المشتركة."
    return {
        "ok": True,
        "mode": "hybrid_outline",
        "text": header + body + footer,
        "scores": {"llm": s_llm, "meta": s_meta}
    }
