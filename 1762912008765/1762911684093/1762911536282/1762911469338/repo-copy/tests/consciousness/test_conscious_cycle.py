import json
import pathlib

from Core_Consciousness import SelfModel, PerceptionLoop, IntentGenerator, StateLogger


def test_conscious_cycle_tmpdir(tmp_path, monkeypatch):
    art = tmp_path / "artifacts"
    art.mkdir()
    monkeypatch.chdir(tmp_path)

    sm = SelfModel()
    pl = PerceptionLoop(self_model=sm, sample_scope="all")
    snap = pl.run_once()
    assert isinstance(snap, dict) and snap, "Perception snapshot should be non-empty dict"

    intent = IntentGenerator().decide(snap)
    assert intent, "Intent should be non-empty / truthy"

    StateLogger().log(snap, intent)

    p = pathlib.Path("artifacts/perception_log.json")
    s = pathlib.Path("artifacts/conscious_state_log.jsonl")
    assert p.exists(), "perception_log.json must be written"
    assert s.exists(), "conscious_state_log.jsonl must be written"

    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "perception_log.json should contain a dict-like snapshot"
