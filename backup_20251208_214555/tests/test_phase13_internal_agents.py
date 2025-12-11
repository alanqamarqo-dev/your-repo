import os

from Self_Improvement.internal_agents import (
    select_agent_for_problem,
    apply_agent_to_prompt,
)


def test_phase13_select_med_agent_by_keywords():
    problem = {
        "title": "سؤال طبي",
        "question": "ما هي أسباب ارتفاع ضغط الدم ومضاعفاته؟",
    }
    agent = select_agent_for_problem(problem)
    assert agent is not None
    assert agent.name == "med_agent"


def test_phase13_select_plan_agent_by_keywords():
    problem = {
        "title": "خطة مشروع",
        "question": "أريد خطة تنفيذ مشروع بحث عن تهريب الأدوية.",
    }
    agent = select_agent_for_problem(problem)
    assert agent is not None
    assert agent.name == "plan_agent"


def test_phase13_apply_agent_to_prompt_and_meta():
    problem = {
        "title": "استشارة طبية",
        "question": "اشرح داء السكري من حيث التعريف والمضاعفات.",
    }
    base_prompt = "اشرح الإجابة للمستخدم."
    meta = {}
    final_prompt = apply_agent_to_prompt(problem, base_prompt, meta)
    # يجب أن يكون تم حقن رأس الوكيل
    assert "[AGENT:med_agent]" in final_prompt
    assert "أنت وكيل داخلي متخصص في الطب" in final_prompt
    # يجب تسجيل الوكيل في meta
    assert meta.get("internal_agent") == "med_agent"


def test_phase13_no_agent_match_returns_same_prompt():
    problem = {
        "title": "سؤال عام",
        "question": "اكتب لي جملة ترحيبية عشوائية.",
    }
    base_prompt = "اكتب جملة ترحيبية."
    meta = {}
    final_prompt = apply_agent_to_prompt(problem, base_prompt, meta)
    # لا توجد كلمات طبية أو تخطيطية أو برمجية واضحة → لا وكيل
    assert final_prompt == base_prompt
    assert "internal_agent" not in meta
