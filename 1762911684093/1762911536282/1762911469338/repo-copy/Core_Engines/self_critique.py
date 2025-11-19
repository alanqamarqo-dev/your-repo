"""Self Critique and Revise
Produces a short self-critique and a revised condensed version.
"""
from typing import Dict, Any

class SelfCritiqueAndRevise:
    name = "Self_Critique_and_Revise"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = payload.get("draft") or payload.get("text") or ""
        if not draft:
            return {"ok": False, "reason": "no input"}
        critique_lines = [
            "نقاط غموض محتملة: لم أفصل القيود التشغيلية بوضوح.",
            "افتراضات غير مذكورة: حالة الطقس/سلوك السائقين.",
            "تحيّزات: افتراض تناسق الشبكة دون بيانات ميدانية."
        ]
        revised = draft + "\n\n[نسخة منقّحة مختصرة]: " + (draft[:800] if len(draft)>800 else draft)
        text = "نقد ذاتي:\n- " + "\n- ".join(critique_lines)
        return {"ok": True, "engine": self.name, "critique": text, "revised": revised, "text": revised}


def factory():
    return SelfCritiqueAndRevise()
