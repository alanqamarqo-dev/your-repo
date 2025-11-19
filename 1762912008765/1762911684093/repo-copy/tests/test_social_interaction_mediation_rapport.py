# -*- coding: utf-8 -*-
from Core_Engines.Social_Interaction import SocialInteractionEngine

def test_mediation_and_rapport():
    eng = SocialInteractionEngine()
    res = eng.mediate_between([
        "We need speed and acceptable quality",
        "Focus on safety and quality, but cost matters",
    ])
    assert "summary" in res and "common" in res

    history = [
        {"role":"user","text":"شكرا لك"},
        {"role":"agent","text":"على الرحب"},
        {"role":"user","text":"أتفق معك"},
        {"role":"agent","text":"تمام"},
        {"role":"user","text":"لكن لدي مشكلة سيئة للغاية"},
    ]
    score = eng.rapport_score(history)
    assert 0.0 <= score <= 100.0
