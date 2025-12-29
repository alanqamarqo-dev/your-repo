import os
import json

import pytest

from Self_Improvement.Knowledge_Graph import agl_pipeline


def test_phase9_runtime_context_basic(monkeypatch):
    os.environ["AGL_FAST_MODE"] = "1"

    q = "اشرح ارتفاع ضغط الدم من حيث: التعريف، الأسباب، المضاعفات، طرق الوقاية."
    result = agl_pipeline(q)

    assert "provenance" in result
    prov = result["provenance"]
    assert prov is not None
    # runtime_context may be directly on provenance dict
    assert "runtime_context" in prov

    ctx = prov["runtime_context"]
    assert ctx["title"].startswith("اشرح ارتفاع ضغط الدم")
    assert ctx["stage"] in ("analysis", "execution", "analysis_retry")
    assert ctx["attempts"] >= 1
    assert 0.0 <= float(ctx.get("progress", 0.0)) <= 1.0


def test_phase9_runtime_context_on_error(monkeypatch):
    # Ensure FAST_MODE for speed
    # Disable FAST_MODE so the hosted adapter path is exercised and our monkeypatch can raise
    os.environ["AGL_FAST_MODE"] = "0"

    # Simulate a top-level pipeline error by monkeypatching the CIE collaborative_solve
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine

    def _raise_exc(self, *a, **k):
        raise RuntimeError("simulated failure for testing")

    monkeypatch.setattr(CognitiveIntegrationEngine, 'collaborative_solve', _raise_exc)

    try:
        q = "ما هي أعراض الإنفلونزا؟"
        result = agl_pipeline(q)

        prov = result.get("provenance") or {}
        ctx = prov.get("runtime_context")

        assert ctx is not None
        assert ctx["stage"] == "analysis_retry"
        assert ctx["last_error"] is not None
        assert "simulated failure" in ctx["last_error"]
    finally:
        # restore nothing else needed; monkeypatch fixture will undo class patch
        pass
