# -*- coding: utf-8 -*-
import os
os.environ["AGL_C_LAYER_PERCEPTION"] = "1"

def test_perception_reads():
    from Core.C_Layer.perception_loop import PerceptionLoop
    pl = PerceptionLoop(provider=lambda: {"load":0.8, "stability_metric":0.85})
    ctx = pl.read()
    assert ctx["load"] == 0.8 and ctx["stability_metric"] == 0.85
