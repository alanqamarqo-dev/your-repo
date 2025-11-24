import re
from typing import Optional

# try to import get_engine lazily to avoid hard circular imports at module load
def _get_nlp_engine():
    try:
        from Integration_Layer.Domain_Router import get_engine
        return get_engine("nlp")
    except Exception:
        return None

INTENTS = {
    "ohm": ["قانون اوم", "ohm", "v=i*r", "v=ir", "قانون أوم", "أوم"],
    "rc": ["rc", "ثابت الزمن", "tau", "τ", "rc_step"],
    "predict": ["احسب", "احسبي", "compute", "calculate", "estimate", "توقّع", "ما قيمة", "كم"],
    "explain": ["اشرح", "why", "explain", "لماذا"],
    "report": ["تقرير", "report"],
    "discover": ["اقترح قانون", "نموذج جديد", "اكتشف نموذج", "discover model"],
    "target_current": ["التيار", "current", "I="],
    "target_resistance": ["المقاومة", "resistance", "R="],
    "target_voltage": ["الجهد", "voltage", "V="]
}


# Arabic diacritics and tatweel removal + small normalization helper
_AR_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")
def _norm(s: str) -> str:
    s = s or ""
    s = s.lower()
    s = _AR_DIAC.sub("", s)  # إزالة التشكيل والمد
    # توحيد الهمزات
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = re.sub(r"\s+", " ", s).strip()
    return s


META_PATTERNS = [
    "few shot", "few-shot", "fewshot", "meta learn", "metalearn",
    "تعلم من لقطة قليلة", "تعلم من لقطه قليله", "تعلم من قلة بيانات",
    "لقطة قليلة", "تعلم لقطة قليلة", "تعلم بلقطات قليلة", "لقطات قليلة",
    "تعلم بالتعميم", "لقطات", "لقطة", "تعلم بالتعميم"
]


def detect_intent(text: str) -> str:
    t = _norm(text)

    # Arabic question triggers that should map to informational queries
    ASK_TRIGGERS = ["ما هو", "ما هي", "ماهو", "متى", "لماذا", "كيف", "من هو", "كم"]

    # if the text contains common question starters, treat as ask_info
    for trig in ASK_TRIGGERS:
        if trig in text:
            return "ask_info"

    # If the question seems linguistically complex or contains ambiguous pronouns,
    # prefer asking the LLM (when available) to classify the intent. This is
    # best-effort: if the LLM/classifier is unavailable or fails, fall back to
    # the rule-based heuristics below.
    try:
        # simple heuristic for ambiguity: long question or coreference pronouns
        if len(t) > 80 or any(p in t for p in ["هو", "هي", "ذلك", "هذه", "هؤلاء", "هم", "هن", "ذلك"]):
            nlp = _get_nlp_engine()
            if nlp is not None:
                # Prefer an explicit classifier if present
                for method in ("classify_intent", "detect_intent", "intent_classify"):
                    if hasattr(nlp, method):
                        try:
                            lab = getattr(nlp, method)(text)
                            if isinstance(lab, dict) and "intent" in lab:
                                lab = lab.get("intent")
                            if isinstance(lab, (list, tuple)) and lab:
                                lab = lab[0]
                            if isinstance(lab, str):
                                lab = lab.strip().lower()
                                if lab in ("ask_info","translate","plan","brainstorm","visual","meta_learn","social"):
                                    return lab
                        except Exception:
                            pass
                # Fallback: prompt-style classification via respond/helpful
                for method in ("classify", "respond", "helpful", "reply"):
                    if hasattr(nlp, method):
                        try:
                            prompt = (
                                "Classify the user's intent into one of: ask_info, translate, plan, "
                                "brainstorm, visual, meta_learn, social. Respond with only the label.\n\n"
                                f"User: {text}\nLabel:"
                            )
                            out = getattr(nlp, method)(prompt)
                            if isinstance(out, dict):
                                out = out.get("text") or out.get("reply") or str(out)
                            if isinstance(out, (list, tuple)) and out:
                                out = out[0]
                            if isinstance(out, str):
                                lab = out.strip().split()[0].strip().lower()
                                if lab in ("ask_info","translate","plan","brainstorm","visual","meta_learn","social"):
                                    return lab
                        except Exception:
                            pass
    except Exception:
        # never let LLM failures break intent detection
        pass

    # أولوية meta_learn قبل ask_info
    for kw in META_PATTERNS:
        if _norm(kw) in t:
            return "meta_learn"

    # بقية القواعد كما هي…
    if any(k in t for k in ["ترجم", "translate", "ترجمة"]):
        return "translate"
    if any(k in t for k in ["خطة", "plan"]):
        return "plan"
    if any(k in t for k in ["فكرة", "ابتكر", "brainstorm"]):
        return "brainstorm"
    if any(k in t for k in ["visual", "صورة ثلاثي", "3d", "ثلاثي الابعاد", "ثلاثي الأبعاد"]):
        return "visual"
    if any(k in t for k in ["حزين", "تعاطف", "support", "empathy", "social"]):
        return "social"

    # افتراضي
    return "ask_info"


# backward-compatible alias used by older tests / modules
def recognize_intent(text: str) -> dict:
    """Backward-compatible recognizer used by older modules/tests.

    Returns a dict with at least keys: task, law (law may be None).
    """
    # base intent string
    base = detect_intent(text)
    # heuristics to populate task/law for legacy callers
    t = _norm(text)
    law = None
    task = None

    # detect Ohm/electrical inference requests
    if any(k in t for k in ["قانون اوم", "اوم", "v=", "i=", "r="]):
        law = "ohm"
        # older tests accept either 'solve_ohm' or ('infer','ohm') mapping
        task = "solve_ohm"

    # prefer meta learn mapping if detected
    if base == "meta_learn":
        task = "meta_learn"

    # fallback: map base intent to task
    if task is None:
        task = base

    return {"task": task, "law": law}
