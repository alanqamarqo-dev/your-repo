# -*- coding: utf-8 -*-
"""
إعدادات اختبار AGI الشامل
"""

AGI_TEST_CONFIG = {
    "scoring_weights": {
        "mathematical_reasoning": 0.15,
        "linguistic_intelligence": 0.15,
        "creative_thinking": 0.15,
        "emotional_social": 0.15,
        "learning_adaptation": 0.15,
        "strategic_planning": 0.15,
        "knowledge_integration": 0.10
    },

    "performance_thresholds": {
        "S_level": 0.90,
        "A_level": 0.80,
        "B_level": 0.70,
        "C_level": 0.60
    },

    "test_timeout": 3600,  # ثانية
    "max_retries": 3,

    "output_formats": ["json", "html", "pdf"],
    "language": "arabic"
}
