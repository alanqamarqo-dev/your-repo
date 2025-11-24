import json
import shutil
import time
import statistics
from pathlib import Path
from typing import Tuple

import pytest

from Core_Consciousness import SelfModel, PerceptionLoop, IntentGenerator, State_Logger, StateLogger
from Core_Consciousness import IntentGenerator as IG


def _metrics_tuple(snapshot: dict) -> Tuple[float, float, float]:
    # snapshot: the 'snapshot' dict inside perception run
    s = snapshot.get('snapshot') if isinstance(snapshot, dict) else None
    if not s:
        return (0.0, 0.0, 0.0)
    return (float(s.get('mood', 0.0)), float(s.get('energy', 0.0)), float(s.get('confidence', 0.0)))


def test_meta_loop_stability(tmp_path, monkeypatch):
    """Run repeated perception->intent->state cycles and assert the closed-loop stabilizes.

    Measures:
    - iteration latency (ms)
    - mean delta between successive (mood, energy, confidence)
    - first iteration index where delta < eps (stability)
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('AGL_TEST_SCAFFOLD_FORCE', '1')
    monkeypatch.setenv('AGL_LLM_PROVIDER', 'offline')

    sm = SelfModel()
    # interval doesn't matter for run_once; use small value
    pl = PerceptionLoop(self_model=sm, interval=0.0, sample_scope='all')
    ig = IG()
    sl = StateLogger()

    max_iters = 12
    eps = 0.02

    latencies = []
    deltas = []
    prev = None
    stable_at = None

    trace = []
    try:
        for i in range(max_iters):
            t0 = time.time()
            snap = pl.run_once(trace_debug=(i == 0))
            intent = ig.decide(snap)
            sl.log(snap, intent)
            t1 = time.time()

            lat_ms = (t1 - t0) * 1000.0
            latencies.append(lat_ms)

            cur = _metrics_tuple(snap)
            if prev is not None:
                delta = sum(abs(cur[j] - prev[j]) for j in range(3)) / 3.0
                deltas.append(delta)
                if delta < eps and stable_at is None:
                    stable_at = i
            prev = cur

            trace.append({"i": i, "snap": snap, "intent": intent, "lat_ms": lat_ms})
    except AssertionError:
        raise
    except Exception as exc:  # capture unexpected exceptions and write diagnostics
        # write diagnostic trace to artifacts
        out = Path("artifacts/meta_loop_trace.jsonl")
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for row in trace:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        # try to copy perception/state logs
        try:
            shutil.copyfile("artifacts/perception_log.json", "artifacts/failed_run/perception_log.json")
        except Exception:
            pass
        try:
            shutil.copyfile("artifacts/conscious_state_log.jsonl", "artifacts/failed_run/conscious_state_log.jsonl")
        except Exception:
            pass
        pytest.fail(f"Meta loop instability (exception): {exc}")

    # if final assertions fail, write debug outputs and re-raise via pytest.fail below

    # basic latency expectation: median iteration should be reasonable
    med_lat = statistics.median(latencies)
    if not (med_lat < 5000):
        # write diagnostics
        out = Path("artifacts/meta_loop_trace.jsonl")
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for row in trace:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        pytest.fail(f"Median iteration latency too high: {med_lat:.1f}ms; diagnostic trace written to {out}")

    # expect at least one delta computed
    if not deltas:
        out = Path("artifacts/meta_loop_trace.jsonl")
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for row in trace:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        pytest.fail("No deltas measured; loop didn't run multiple iterations. Diagnostic trace written.")

    # expect stabilization within allotted iterations
    if stable_at is None:
        out = Path("artifacts/meta_loop_trace.jsonl")
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for row in trace:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        pytest.fail(f"Loop did not stabilize within {max_iters} iterations; diagnostic trace written to {out}")

    # checks on variance reduction: last half mean <= first half mean * 1.1 (allow small noise)
    if len(deltas) >= 4:
        half = len(deltas) // 2
        first_mean = statistics.mean(deltas[:half])
        last_mean = statistics.mean(deltas[half:])
        if not (last_mean <= first_mean * 1.1):
            out = Path("artifacts/meta_loop_trace.jsonl")
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("w", encoding="utf-8") as f:
                for row in trace:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            pytest.fail(f"Variance did not decrease (first_mean={first_mean:.4f}, last_mean={last_mean:.4f}); diagnostic trace written to {out}")

    # number of self-corrections before first stability should be small
    if not (stable_at <= 8):
        out = Path("artifacts/meta_loop_trace.jsonl")
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for row in trace:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        pytest.fail(f"Stabilized too late: iteration {stable_at}; diagnostic trace written to {out}")
