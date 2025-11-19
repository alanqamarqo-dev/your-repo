# -*- coding: utf-8 -*-
import os, json, pathlib
os.environ["AGL_C_LAYER_SNAPSHOTS"] = "1"
os.environ["AGL_C_LAYER_SNAPSHOTS_N"] = "3"

def test_snapshots():
    from Core.C_Layer.state_logger import StateLogger
    lg = StateLogger()
    p = lg.snapshot({"hello":"world"})
    assert p and pathlib.Path(p).exists()
    data = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    assert data["hello"] == "world"
