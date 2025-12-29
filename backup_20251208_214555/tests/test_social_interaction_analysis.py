# -*- coding: utf-8 -*-
from Core_Engines.Social_Interaction import SocialInteractionEngine

def test_analyze_social_cues_basic():
    eng = SocialInteractionEngine()
    cues1 = eng.analyze_social_cues("شكرا لكن لدي مشكلة مزعجة")
    assert cues1["sentiment"] in ("negative","neutral")
    assert cues1["politeness"] in ("polite","neutral")
    assert cues1["stance"] in ("disagree","neutral")

    cues2 = eng.analyze_social_cues("هذا رائع وممتاز، أحب النتيجة!")
    assert cues2["sentiment"] == "positive"
    assert 0.0 <= cues2["intensity"] <= 1.0
