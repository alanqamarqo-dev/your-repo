# -*- coding: utf-8 -*-
from Integration_Layer.Domain_Router import route_intent

def test_cross_engine_environment_case():
    gk = route_intent("intent_gk", {"task":"link","concepts":["تلوث","تحلية","طاقة شمسية"]})
    ci = route_intent("intent_ci", {"mode":"solve","problem":"تقليل ملوحة المياه بتكلفة منخفضة"})
    st = route_intent("intent_st", {"mode":"scenario","options":["Pilot","Scale"],"horizon":12})
    nlp = route_intent("intent_nlp", {"mode":"explain","text":"اشرح الحل بشكل مبسط","style":"simple"})
    assert gk is not None and ci is not None and st is not None and nlp is not None
