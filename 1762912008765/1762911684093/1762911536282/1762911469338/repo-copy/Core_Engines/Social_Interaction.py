# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os

def _to_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

_AGL_SOCIAL_CTX_CHARS = _to_int("AGL_SOCIAL_CTX_CHARS", 200)


try:
    from Core_Engines.engine_base import Engine  # type: ignore
    try:
        from Core_Engines.engine_base import EngineRegistry
    except Exception:
        EngineRegistry = None  # type: ignore
except Exception:
    class Engine:
        name: str = "EngineBase"
        version: str = "0.0"
        capabilities: List[str] = []
        def info(self) -> Dict[str, Any]:
            return {"name": self.name, "version": self.version, "capabilities": self.capabilities}
        def configure(self, **kwargs: Any) -> None:  # minimal protocol implementation
            for k, v in kwargs.items():
                setattr(self, k, v)
        def healthcheck(self) -> Dict[str, Any]:
            return {"ok": True}


class SocialInteractionEngine(Engine):
    """
    محرك التفاعل الاجتماعي (قائم على قواعد بسيطة):
    - تحليل مشاعر ونبرة ولباقة واتجاه (اتفاق/اختلاف)
    - توليد ردود متعاطفة ومتكيّفة الأسلوب
    - وساطة لاستخراج أرضية مشتركة
    - قياس الألفة من سجل الحوار
    """
    name = "SocialInteractionEngine"
    version = "2.0.0"
    capabilities = [
        "social_cue_analysis",
        "empathetic_response_generation",
        "conflict_mediation",
        "rapport_scoring"
    ]

    POS_WORDS = {"great","amazing","thanks","thank","love","like","happy","glad","awesome","excellent","تمام","رائع","ممتاز","جميل","أحسنت","شكرا"}
    NEG_WORDS = {"bad","hate","angry","upset","sad","terrible","awful","worst","annoyed","issue","problem","غاضب","سيء","سئ","محبط","حزين","كارثي","أسوأ","مشكلة","خطأ"}
    POLITE_MARKERS = {"please","thanks","thank you","لو سمحت","فضلا","من فضلك","شكرا"}
    DISAGREE_MARKERS = {"but","however","لا أوافق","أختلف","لكن","غير صحيح","لا أتفق"}
    AGREE_MARKERS = {"agree","yes","بالضبط","أتفق","صحيح","نعم","تمام"}

    def analyze_social_cues(self, text: str) -> Dict[str, Any]:
        t = (text or "").lower()
        words = set(t.replace("،"," ").replace("."," ").split())

        pos = sum(1 for w in words if (w in self.POS_WORDS))
        neg = sum(1 for w in words if (w in self.NEG_WORDS))

        sentiment = "neutral"
        intensity = 0.0
        if pos > neg:
            sentiment = "positive"; intensity = min(1.0, pos/(pos+neg+1))
        elif neg > pos:
            sentiment = "negative"; intensity = min(1.0, neg/(pos+neg+1))

        politeness = "polite" if any(m in t for m in self.POLITE_MARKERS) else "neutral"
        stance = "disagree" if any(m in t for m in self.DISAGREE_MARKERS) else ("agree" if any(m in t for m in self.AGREE_MARKERS) else "neutral")
        needs_empathy = (sentiment == "negative") or ("tired" in t or "overwhelmed" in t or "متعب" in t or "مرهق" in t)

        return {
            "sentiment": sentiment,
            "intensity": round(float(intensity), 3),
            "politeness": politeness,
            "stance": stance,
            "needs_empathy": needs_empathy
        }

    def generate_response(self, user_text: str, style: str = "neutral", goal: str = "support") -> str:
        cues = self.analyze_social_cues(user_text)
        # لبنة تعاطف
        empathic = ""
        if cues["needs_empathy"]:
            empathic = "متفهم لمشاعرك، " if "ar" in style or "arabic" in style or any(ch in style for ch in ['ا','ع']) else "I hear you—"
        elif cues["sentiment"] == "positive":
            empathic = "سعيد بسماع ذلك! " if "ar" in style or "arabic" in style or any(ch in style for ch in ['ا','ع']) else "That's great! "

        # تكييف الأسلوب
        if style in ("formal","رسمي"):
            opener = "أقدّر مشاركتك. "
        elif style in ("friendly","ودي"):
            opener = "خلّينا نحلّها سوا. "
        elif style in ("coach","مدرّب"):
            opener = "خطوة بخطوة سنصل للحل. "
        else:
            opener = ""

        # هدف الرد
        if goal == "support":
            body = "ما أهم نتيجة ترغب فيها الآن؟ سأقترح لك خيارين عمليين."
        elif goal == "clarify":
            body = "هل تقصد المشكلة تحدث دائمًا أم أحيانًا؟ وما العلامة التي تودّ تحسينها أولًا؟"
        elif goal == "resolve":
            body = "سأقترح مسارين: (1) إجراء سريع لتخفيف الأثر، (2) معالجة جذرية لضمان الاستقرار."
        else:
            body = "حاضر."

        # خاتمة حسب اللباقة
        closing = " شكرا لتفاصيلك." if cues["politeness"] == "polite" else ""

        return (empathic + opener + body + closing).strip()

    # compatibility alias
    def empathic_reply(self, text: str) -> str:
        return self.generate_response(text, style="friendly", goal="support")

    def mediate_between(self, positions: List[str]) -> Dict[str, Any]:
        """
        يستخرج قيم/مصالح مشتركة ويعيد صياغتها كبنود اتفاق أولية.
        """
        if not positions:
            return {"common": [], "summary": "لا توجد مواقف."}

        # مؤشرات بسيطة
        wants_speed = any("speed" in p.lower() or "سريع" in p for p in positions)
        wants_quality = any("quality" in p.lower() or "جودة" in p for p in positions)
        wants_cost = any("cost" in p.lower() or "تكلفة" in p for p in positions)
        wants_safety = any("safety" in p.lower() or "سلامة" in p for p in positions)

        common = []
        if sum([wants_speed, wants_quality, wants_cost, wants_safety]) >= 2:
            if wants_quality: common.append("الحفاظ على جودة مقبولة")
            if wants_speed:   common.append("الإسراع بجدول زمني واقعي")
            if wants_cost:    common.append("ضبط التكلفة ضمن سقف محدد")
            if wants_safety:  common.append("عدم المساس بالسلامة")

        summary = "تم تحديد أرضية مشتركة مبدئية." if common else "التباين مرتفع؛ نبدأ بتحديد القيود ثم المقايضات."
        return {"common": common, "summary": summary}

    def rapport_score(self, history: List[Dict[str, str]]) -> float:
        """
        history: [{role:'user'|'agent', 'text': str}]
        النقاط: +1 شكر، +1 اتفاق، -1 سلبية قوية، +0.5 توالي ردود قصيرة متعاونة.
        يعاد الناتج ضمن [0,100].
        """
        score = 50.0
        last_agent_short = False
        for turn in history:
            text = (turn.get("text") or "").lower()
            cues = self.analyze_social_cues(text)
            if "شكرا" in text or "thanks" in text or "thank you" in text:
                score += 1.0
            if cues["stance"] == "agree":
                score += 1.0
            if cues["sentiment"] == "negative" and cues["intensity"] > 0.5:
                score -= 1.0
            if turn.get("role") == "agent":
                is_short = len(text.split()) <= 6
                if is_short and last_agent_short:
                    score += 0.5  # إيقاع سريع ومتعاون
                last_agent_short = is_short
        return float(max(0.0, min(100.0, score)))

    # backward-compatible alias
    def group_dynamics(self, opinions: List[str]) -> Dict[str, Any]:
        """Compatibility wrapper: analyze simple group opinions and return mediation summary"""
        med = self.mediate_between(opinions)
        # derive simple cohesion/conflict metrics
        total = max(1, len(opinions))
        agree = sum(1 for o in opinions if any(a in o for a in self.AGREE_MARKERS))
        disagree = sum(1 for o in opinions if any(d in o for d in self.DISAGREE_MARKERS))
        cohesion = round(agree / total, 3)
        conflict = round(disagree / total, 3)
        out = {"summary": med.get("summary"), "common": med.get("common"), "cohesion": cohesion, "conflict": conflict}
        return out


# register engine if registry is present
try:
    if 'EngineRegistry' in globals() and EngineRegistry is not None: # type: ignore
        EngineRegistry.register(SocialInteractionEngine()) # type: ignore
except Exception:
    pass


# compatibility: provide small process_task and alias expected by ENGINE_SPECS
def _social_process_task_wrapper(instance: SocialInteractionEngine, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        text = payload.get("text") or payload.get("input") or ""
        if payload.get("action") == "analyze":
            return {"ok": True, "engine": instance.name, "analysis": instance.analyze_social_cues(str(text))}
        if payload.get("action") == "reply":
            return {"ok": True, "engine": instance.name, "reply": instance.generate_response(str(text), style=payload.get("style","friendly"))}
        return {"ok": True, "engine": instance.name, "status": instance.rapport_score(payload.get("history", []))}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# add a simple process_task method on the class if missing
if not hasattr(SocialInteractionEngine, 'process_task'):
    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return _social_process_task_wrapper(self, payload)

    setattr(SocialInteractionEngine, 'process_task', process_task)

# alias expected by older code
SocialInteraction = SocialInteractionEngine  # type: ignore

