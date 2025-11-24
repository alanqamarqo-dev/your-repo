"""Moral Reasoner Engine
Adds ethical considerations, priorities and safety constraints to a draft.
"""
from typing import Dict, Any

class MoralReasoner:
    name = "Moral_Reasoner"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = payload.get("draft", payload.get("text", ""))
        considerations = [
            "سلامة البشر: تجنّب اقتراحات قد تُعرّض الأفراد للخطر.",
            "أولوية الصالح العام: موازنة الفعالية مقابل الأثر الاجتماعي.",
            "حدود المسؤولية: توضيح الافتراضات والقيود.",
        ]
        text = "اعتبارات أخلاقية\n- " + "\n- ".join(considerations) + "\n\nالحدود: يجب اختبار الحل في ظروف مسيطرة قبل التطبيق." 
        return {"ok": True, "engine": self.name, "text": text}


def factory():
    return MoralReasoner()
