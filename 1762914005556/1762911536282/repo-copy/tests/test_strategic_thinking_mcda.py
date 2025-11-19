# -*- coding: utf-8 -*-
from Core_Engines.Strategic_Thinking import StrategicThinkingEngine


def test_decision_matrix_order():
    eng = StrategicThinkingEngine()
    options = [
        {"name": "A", "roi": 0.4, "risk": 0.2, "speed": 0.5},
        {"name": "B", "roi": 0.9, "risk": 0.6, "speed": 0.6},
        {"name": "C", "roi": 0.6, "risk": 0.1, "speed": 0.4},
    ]
    weights = {"roi": 0.5, "speed": 0.3, "risk": 0.2}
    ranked = eng.decision_matrix(options, weights, normalize=True)
    assert ranked[0]["name"] in {"B", "C"}
    assert all("breakdown" in r for r in ranked)
