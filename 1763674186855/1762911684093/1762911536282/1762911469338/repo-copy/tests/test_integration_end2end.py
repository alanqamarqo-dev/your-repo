import uuid
from Integration_Layer.Conversation_Manager import start_session, auto_route


def new_session():
    sid = "sess-" + uuid.uuid4().hex[:8]
    start_session(sid)
    return sid


def test_translate_flow_ar_en():
    sid = new_session()
    out = auto_route(sid, "ترجم hello")
    assert out is not None
    assert isinstance(out, dict)


def test_multi_turn_brainstorm_to_plan():
    sid = new_session()
    r1 = auto_route(sid, "أعطني فكرة لميزة اجتماعية مبتكرة")
    assert isinstance(r1, dict)
    r2 = auto_route(sid, "حوله لخطة ربع سنوية")
    assert isinstance(r2, dict)


def test_info_qa_then_visual():
    sid = new_session()
    r1 = auto_route(sid, "ما هو قانون نيوتن الثاني؟")
    assert isinstance(r1, dict)
    r2 = auto_route(sid, "أرني توصيفًا بصريًا مبسطًا")
    assert isinstance(r2, dict)


def test_meta_learn_few_shot():
    sid = new_session()
    few_shot_prompt = "تعلّم من لقطة قليلة: مثال: مدخل=2 مخرج=4; مدخل=3 مخرج=6"
    r = auto_route(sid, few_shot_prompt)
    assert isinstance(r, dict)


def test_social_empathy():
    sid = new_session()
    r = auto_route(sid, "أنا حزين وأحتاج دعم")
    assert isinstance(r, dict)


def test_fallback_resilience():
    sid = new_session()
    r = auto_route(sid, "؟؟؟ !!! $$ بلا سياق مفهوم")
    assert isinstance(r, dict)
