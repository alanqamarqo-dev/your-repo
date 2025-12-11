import os

from Self_Improvement.cognitive_mode import (
    choose_cognitive_mode,
    CognitiveMode,
)


def test_phase14_simple_factoid_low_risk_fast_mode(monkeypatch):
    # وضع الاختبارات السريع
    monkeypatch.setenv("AGL_FAST_MODE", "1")
    problem = {
        "title": "سؤال بسيط",
        "question": "ما هي أعراض الإنفلونزا؟",
    }
    mode: CognitiveMode = choose_cognitive_mode(problem)
    # في FAST_MODE: بدون CoT، لكن مع وكيل داخلي
    assert mode.use_cot is False
    assert mode.cot_depth == "none"
    assert mode.samples == 1
    assert mode.use_internal_agents is True
    assert mode.risk_level == "low"


def test_phase14_medical_high_risk_normal_mode(monkeypatch):
    # إلغاء FAST_MODE
    monkeypatch.setenv("AGL_FAST_MODE", "0")
    problem = {
        "title": "استشارة طبية مفصلة",
        "question": "اشرح ارتفاع ضغط الدم من حيث التعريف والأسباب والمضاعفات والوقاية.",
    }
    mode: CognitiveMode = choose_cognitive_mode(problem)
    assert mode.use_cot is True
    assert mode.cot_depth == "deep"
    assert mode.samples >= 2  # في الوضع العادي نأخذ أكثر من عينة
    assert mode.use_internal_agents is True
    assert mode.use_self_critique is True
    assert mode.risk_level == "high"


def test_phase14_planning_question_uses_planning_mode(monkeypatch):
    monkeypatch.setenv("AGL_FAST_MODE", "0")
    problem = {
        "title": "خطة مشروع بحث",
        "question": "أريد خطة مفصلة لإعداد بحث عن تهريب الأدوية في محافظة مأرب.",
    }
    mode: CognitiveMode = choose_cognitive_mode(problem)
    assert mode.use_cot is True
    assert mode.cot_depth in ("short", "deep")
    assert mode.use_internal_agents is True
    assert mode.risk_level == "medium"


def test_phase14_general_question_default_mode(monkeypatch):
    monkeypatch.setenv("AGL_FAST_MODE", "0")
    problem = {
        "title": "سؤال عام",
        "question": "اشرح لي بإيجاز مفهوم الذكاء الاصطناعي التوليدي.",
    }
    mode: CognitiveMode = choose_cognitive_mode(problem)
    # لا هو طبي خطر، ولا تخطيط معقد → إعدادات عامة
    assert mode.risk_level in ("low", "medium")
    assert mode.samples >= 1
    assert mode.use_internal_agents is True
