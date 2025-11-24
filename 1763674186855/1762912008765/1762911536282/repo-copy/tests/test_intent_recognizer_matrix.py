import pytest
from Integration_Layer.Intent_Recognizer import detect_intent

@pytest.mark.parametrize("text,expected", [
    ("ترجم هذه الجملة", "translate"),
    ("translate to arabic", "translate"),
    ("خطة تسويقية ربع سنوية", "plan"),
    ("أعطني فكرة لميزة مبتكرة", "brainstorm"),
    ("visual ثلاثي الأبعاد", "visual"),
    ("تعلّم من لقطة قليلة", "meta_learn"),
    ("أنا حزين وأحتاج دعم", "social"),
    ("ما هو قانون نيوتن؟", "ask_info"),
    ("", "ask_info"),                 # فراغ -> افتراضي
    ("%%%%", "ask_info"),             # رموز فقط -> افتراضي
])
def test_detect_intent_matrix(text, expected):
    assert detect_intent(text) == expected
