# -*- coding: utf-8 -*-
from Core_Engines.Social_Interaction import SocialInteractionEngine

def test_generate_response_styles():
    eng = SocialInteractionEngine()
    txt = "أنا متعب من هذه المشكلة"
    r_formal = eng.generate_response(txt, style="formal", goal="support")
    r_friendly = eng.generate_response(txt, style="friendly", goal="clarify")
    assert isinstance(r_formal, str) and len(r_formal) > 0
    assert isinstance(r_friendly, str) and len(r_friendly) > 0
    # يجب أن تحتوي على لمسة تعاطف
    assert ("متفهم" in r_formal) or ("hear you" in r_formal.lower())
