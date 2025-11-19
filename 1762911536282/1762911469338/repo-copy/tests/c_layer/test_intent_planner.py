# -*- coding: utf-8 -*-
import os
os.environ["AGL_C_LAYER_INTENT"] = "1"


class _Reg:
    def __init__(self): self.ops=[]
    def prioritize(self, front): self.ops.append(("prioritize", tuple(front)))

class _Meta:
    def __init__(self): self.ops=[]
    def adjust_engine_weight(self, e, d): self.ops.append(("adjust", e, d))
    def set_scope(self, s): self.ops.append(("scope", s))

def test_planner_basic():
    from Core.C_Layer.intent_types import Intent, IntentKind
    from Core.C_Layer.intent_planner import IntentPlanner
    reg, meta = _Reg(), _Meta()
    pl = IntentPlanner(reg, meta)
    logs = pl.apply([
        Intent(IntentKind.ADJUST_WEIGHT, {"engine":"Consistency_Checker","delta":0.2}),
        Intent(IntentKind.REORDER_ENGINES, {"priority_front":["Meta_Learning","Reasoning_Planner"]}),
        Intent(IntentKind.SET_SCOPE, {"scope":"stm"}),
    ])
    assert any("Adjusted weight" in l for l in logs)
    assert ("prioritize", ("Meta_Learning","Reasoning_Planner")) in reg.ops
    assert ("scope","stm") in meta.ops
