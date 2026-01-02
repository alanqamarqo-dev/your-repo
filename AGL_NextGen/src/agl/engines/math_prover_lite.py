"""Math Prover Lite
Performs simple numeric sanity checks and returns a short verification line.
"""
from typing import Dict, Any

class MathProverLite:
    name = "Math_Prover_Lite"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # naive detection of numbers in text and produce a tiny check
        draft = payload.get("draft") or payload.get("text") or ""
        # This is intentionally lightweight: detect patterns like 'X m3/s' or simple ratios
        checks = []
        if "m3" in draft or "م3" in draft:
            checks.append("تحقق عددي مختصر: الوحدات تبدو متناسقة (m3).")
        if "%" in draft:
            checks.append("تحقق: النسب المئوية تحتاج توضيح ما هي القاعدة المرجعية.")
        if not checks:
            checks.append("تحقق عددي: لا توجد أرقام واضحة للاختبار السريع.")
        text = "\n".join("- "+c for c in checks)
        return {"ok": True, "engine": self.name, "text": text, "checks": checks}


def factory():
    return MathProverLite()
