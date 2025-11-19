# -*- coding: utf-8 -*-
from Core_Engines.Creative_Innovation import CreativeInnovationEngine


def test_generate_ideas_len_and_order():
    eng = CreativeInnovationEngine(seed=7)
    ideas = eng.generate_ideas("تقليل الازدحام المروري", n=5, constraints={"budget": 5000})
    assert isinstance(ideas, list) and len(ideas) == 5
    composites = [x["scores"]["composite"] for x in ideas]
    assert composites == sorted(composites, reverse=True)


def test_scamper_has_all_ops():
    eng = CreativeInnovationEngine()
    res = eng.lateral_thinking("تحسين التعلم الإلكتروني", technique="SCAMPER")
    ops = [s["op"] for s in res["steps"]]
    assert len(ops) == 7
    assert "Substitute" in ops and "Combine" in ops and "Reverse/Rearrange" in ops


def test_novelty_score_is_deterministic():
    eng = CreativeInnovationEngine(seed=1)
    a = eng.evaluate_novelty("فكرة أ", knowledge_fingerprints=["abcd"*16])
    b = eng.evaluate_novelty("فكرة أ", knowledge_fingerprints=["abcd"*16])
    assert a == b
    assert 0.0 <= a <= 1.0
