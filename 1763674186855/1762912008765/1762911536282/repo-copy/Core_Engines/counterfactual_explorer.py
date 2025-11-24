"""Counterfactual Explorer
Generates short 'what-if' scenarios with brief justification.
"""
from typing import Dict, Any

class CounterfactualExplorer:
    name = "Counterfactual_Explorer"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = payload.get("draft") or payload.get("text") or ""
        variants = [
            {"scenario": "ميزانية أصغر", "reason": "يبسط التصميم ويقلل التكلفة لكنه يزيد المخاطر"},
            {"scenario": "جفاف أشد", "reason": "يزيد الحاجة لتقنيات حفظ المياه/تغيير التوقيت"},
            {"scenario": "تحفيز إشارات ذكية", "reason": "قد يقلل الازدحام دون تغيير البنية التحتية"},
        ]
        lines = [f"- {v['scenario']}: {v['reason']}" for v in variants]
        text = "بدائل (ماذا لو):\n" + "\n".join(lines)
        return {"ok": True, "engine": self.name, "text": text, "variants": variants}


def factory():
    return CounterfactualExplorer()
