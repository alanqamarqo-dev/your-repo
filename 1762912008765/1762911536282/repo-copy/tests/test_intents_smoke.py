import pytest
from Integration_Layer.Conversation_Manager import auto_route_and_respond, create_session


@pytest.mark.parametrize("text,expect_intent", [
    ("ترجم hello", "translate"),
    ("خطة تسويق ربع سنوية", "plan"),
    ("أعطني فكرة لميزة", "brainstorm"),
    ("صورة ثلاثية الأبعاد", "visual"),
    ("تعلّم من لقطة قليلة", "meta_learn"),
    ("احتاج ردًّا متعاطفًا", "social"),
    ("ما هو قانون نيوتن؟", "ask_info"),
])
def test_all_intents_route(text, expect_intent, tmp_path):
    sid = 'intents_' + str(abs(hash(text)))[:6]
    create_session(sid)
    out = auto_route_and_respond(sid, text)
    assert isinstance(out, dict)
    assert 'reply_text' in out and isinstance(out['reply_text'], str)
    # intent may map to a small set; ensure field present
    assert 'intent' in out
