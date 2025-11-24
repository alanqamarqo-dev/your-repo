# -*- coding: utf-8 -*-
from Core_Engines.Creative_Innovation import CreativeInnovationEngine


def test_composite_scoring_balance():
    eng = CreativeInnovationEngine(seed=99)
    ideas = eng.generate_ideas("إدارة النفايات المنزلية", n=3,
                               constraints={"budget": 1000, "sustainability": True})
    for x in ideas:
        s = x["scores"]
        assert 0.0 <= s["novelty"] <= 1.0
        assert 0.0 <= s["feasibility"] <= 1.0
        assert abs(s["composite"] - round(0.6*s["novelty"] + 0.4*s["feasibility"], 3)) < 1e-9
