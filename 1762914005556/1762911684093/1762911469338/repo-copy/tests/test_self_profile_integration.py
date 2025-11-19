import os, sys, time, json
# ensure repo root is on path for imports when pytest runs from repo root
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))

from Core_Memory.bridge_singleton import get_bridge
from Core_Consciousness.Self_Model import SelfModel, ReflectiveCortex
from Core_Consciousness.Perception_Loop import _emit_bio_from_event


def setup_module(_m):
    # ensure artifacts path is ephemeral for tests
    os.environ["AGL_ARTIFACTS_DIR"] = os.environ.get("AGL_ARTIFACTS_DIR", "tests/tmp_artifacts")


def test_persist_and_load_profile_roundtrip(tmp_path):
    os.environ["AGL_ARTIFACTS_DIR"] = str(tmp_path)
    br = get_bridge()
    sm = SelfModel()
    sm.set_identity_label("label", "agent#1")
    sm.set_core_value("curiosity", 0.8, mode="abs")
    sm.add_biography_event(kind="init", note="boot", source="test")
    ok = sm.persist_profile(br)
    assert ok is True

    sm2 = SelfModel()
    loaded = sm2.load_profile_from_bridge(br)
    assert loaded is True
    assert sm2.identity.get("label") == "agent#1"
    assert sm2.core_values.get("curiosity", 0) >= 0.79
    assert any(e.get("kind") == "init" or e.get("note") == "boot" for e in sm2.biography)


def test_emit_bio_on_failure_and_feedback(tmp_path):
    os.environ["AGL_ARTIFACTS_DIR"] = str(tmp_path)
    br = get_bridge()
    sm = SelfModel()
    # failure
    evt_fail = {"payload": {"error": "timeout", "tags": ["pipeline", "failure"]}}
    _emit_bio_from_event(sm, evt_fail)
    # feedback
    evt_fb = {"payload": {"user_feedback": "great result", "tags": ["success"]}}
    _emit_bio_from_event(sm, evt_fb)

    sm.persist_profile(br)
    sm2 = SelfModel()
    sm2.load_profile_from_bridge(br)
    kinds = [e.get("kind") for e in sm2.biography]
    assert "failure" in kinds and "feedback" in kinds


def test_reflective_cortex_adjusts_values(tmp_path):
    os.environ["AGL_ARTIFACTS_DIR"] = str(tmp_path)
    sm = SelfModel()
    rc = ReflectiveCortex(sm)
    # history with repeated failure on t1
    history = [
        {"task": "t1", "success": False},
        {"task": "t1", "success": False},
        {"task": "t2", "success": True},
    ]
    base_hum = sm.core_values.get("humility", 0.3)
    rc.reflect_on_performance(history)
    # expecting humility to increase or stay same (no large drops)
    assert sm.core_values.get("humility", 0) >= base_hum
    # ensure a biography/reflective entry exists
    assert any(e.get("kind") in ("reflection", "reflective", "reflection", "reflection") or "Reflective" in str(e.get("note")) for e in sm.biography)
