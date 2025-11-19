# -*- coding: utf-8 -*-
from Core_Engines.Strategic_Thinking import StrategicThinkingEngine


def test_scenario_2x2_and_decision_tree():
    eng = StrategicThinkingEngine()
    scen = eng.scenario_analysis(
        "نمو السوق",
        ("الطلب", ["مرتفع", "منخفض"]),
        ("المنافسة", ["شديدة", "ضعيفة"]),
    )
    assert len(scen["grid"]) == 4
    tree = eng.decision_tree_ev([
        {"name": "Launch", "prob": 0.6, "payoff": 120},
        {"name": "Wait",   "prob": 0.4, "payoff": 40},
    ])
    assert abs(tree["ev"] - (0.6*120 + 0.4*40)) < 1e-6
    assert tree["best"] == "Launch"
