# -*- coding: utf-8 -*-
from Core_Engines.Strategic_Thinking import StrategicThinkingEngine


def test_risk_register_priority_and_bands():
    eng = StrategicThinkingEngine()
    risks = [
        {"name": "Supply", "likelihood": 0.8, "impact": 0.7},
        {"name": "Legal", "likelihood": 0.3, "impact": 0.9},
        {"name": "Ops", "likelihood": 0.4, "impact": 0.3},
    ]
    reg = eng.risk_register(risks)
    assert reg[0]["priority"] >= reg[1]["priority"] >= reg[2]["priority"]
    assert reg[0]["band"] in {"High", "Medium"}


def test_allocate_resources_budget_respected():
    eng = StrategicThinkingEngine()
    projects = [
        {"name": "P1", "value": 100, "cost": 40, "risk": 0.2},
        {"name": "P2", "value": 80, "cost": 20, "risk": 0.5},
        {"name": "P3", "value": 60, "cost": 15, "risk": 0.1},
        {"name": "P4", "value": 50, "cost": 30, "risk": 0.9},
    ]
    res = eng.allocate_resources(projects, budget=60, risk_aversion=0.3)
    assert res["spent"] <= 60 + 1e-9
    assert len(res["selected"]) >= 2
