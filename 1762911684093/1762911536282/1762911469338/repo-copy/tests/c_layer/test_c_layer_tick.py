# -*- coding: utf-8 -*-
import os
os.environ["AGL_C_LAYER"] = "1"
os.environ["AGL_C_LAYER_INTENT"] = "1"
os.environ["AGL_C_LAYER_PERCEPTION"] = "1"
os.environ["AGL_C_LAYER_SNAPSHOTS"] = "1"
os.environ["AGL_C_LAYER_SNAPSHOT_EVERY"] = "1"  # لقطة كل tick

class _Reg:
    def prioritize(self, _): pass

class _Meta:
    def adjust_engine_weight(self, *_): pass
    def set_scope(self, *_): pass

def test_tick_end_to_end(tmp_path, monkeypatch):
    from Core.C_Layer.c_layer import CLayer
    cl = CLayer(_Reg(), _Meta(), context_provider=lambda: {"load":0.9,"stability_metric":0.8,"trace_id":"t1"})
    out = cl.tick(extra_state={"note":"ok"})
    assert out["enabled"] and "TRIGGER_SNAPSHOT" in out["intents"]
    assert out["snapshot"]
