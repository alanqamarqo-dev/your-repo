"""Run a single conscious cycle: perception -> intent -> state logging.

Deterministic and CI-friendly (no network calls). Writes artifacts/perception_log.json
and artifacts/conscious_state_log.jsonl
"""
import json
import pathlib
import time

from Core_Consciousness import SelfModel, PerceptionLoop, IntentGenerator, StateLogger


def main():
    ART = pathlib.Path("artifacts")
    ART.mkdir(exist_ok=True)

    sm = SelfModel()
    pl = PerceptionLoop(self_model=sm, sample_scope="all")
    snapshot = pl.run_once()

    intent = IntentGenerator().decide(snapshot)
    StateLogger().log(snapshot, intent)

    print(json.dumps({
        "snapshot_keys": list(snapshot.keys()),
        "intent": intent,
        "logs": {
            "perception_log": str((ART / "perception_log.json").resolve()),
            "state_log": str((ART / "conscious_state_log.jsonl").resolve()),
        }
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
