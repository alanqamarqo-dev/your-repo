# -*- coding: utf-8 -*-
from Integration_Layer.Domain_Router import route_intent

def test_nlp_translate():
    out = route_intent("intent_nlp", {"mode":"translate","text":"مرحبا","to":"en"})
    assert isinstance(out, (dict, str))

def test_gk_linking():
    out = route_intent("intent_gk", {"task":"link","concepts":["طاقة","اقتصاد","فيزياء"]})
    assert out is not None

def test_ci_ideas():
    out = route_intent("intent_ci", {"mode":"ideas","topic":"تقليل الهدر اللوجستي","k":3})
    assert isinstance(out, list) or out is not None

def test_st_plan():
    out = route_intent("intent_st", {"mode":"plan","goal":"اختراق سوق جديد","constraints":{"budget":"low"}})
    assert isinstance(out, dict) or out is not None

def test_ml_fewshot():
    out = route_intent("intent_ml", {"mode":"fewshot","examples":[{"x":"A","y":1},{"x":"B","y":2}]})
    assert out is not None

def test_vs_analyze():
    out = route_intent("intent_vs", {"mode":"analyze","text":"الكرة فوق الطاولة"})
    assert isinstance(out, dict) and out.get("relation") == "above"

def test_si_empathy():
    out = route_intent("intent_si", {"mode":"empathy","message":"أنا متوتر قبل الامتحان"})
    assert out is not None
