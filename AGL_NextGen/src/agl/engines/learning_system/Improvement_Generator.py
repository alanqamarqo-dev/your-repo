# -*- coding: utf-8 -*-
from __future__ import annotations


class ImprovementGenerator:  # type: ignore
    """
    يستقبل تحليلات FeedbackAnalyzer ويخرج "خطة تحسين" قابلة للتطبيق:
    - تعديل أوزان الدمج (fusion weights)
    - ضبط عتبات بوابة الثقة
    - TODO: اقتراح تدريب/أمثلة إضافية (لاحقًا)
    """

    def generate_targeted_improvements(self, feedback: dict) -> dict:
        weights = dict(feedback.get("suggested_fusion_weights", {}))
        gaps = feedback.get("gaps", {})
        conf_gap = float(gaps.get("confidence_gap", 0.0))

        # تعديل بسيط على الأوزان إن كان gap > 0
        if conf_gap > 0:
            # نعزّز المحركات القوية ونقلل الضعيفة قليلًا
            comps = gaps.get("components", {})
            for name, info in comps.items():
                score = float(info.get("score", 0.0))
                if score >= 0.8:
                    weights[name] = round(weights.get(name, 1.0) + 0.05, 3)
                elif score < 0.5:
                    weights[name] = round(max(0.35, weights.get(name, 1.0) - 0.05), 3)

        # ضبط بوابة الثقة
        plan = {
            "fusion_weights": weights,
            "confidence_gate": {
                "target": feedback.get("target_confidence", 0.80),
                "min_pass": 0.70  # لا تقبل أقل من 0.70 الآن
            },
            "notes": ["auto-tuned by ImprovementGenerator"]
        }
        return plan
