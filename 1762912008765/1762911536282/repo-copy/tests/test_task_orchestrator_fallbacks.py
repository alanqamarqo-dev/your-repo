import pytest
from Integration_Layer.Task_Orchestrator import execute_pipeline
from Core_Engines.engine_base import Engine

class DummyOk(Engine):
    def step(self, ctx):
        return {**ctx, "ok": True, "text": "ok"}

class DummyFail(Engine):
    def step(self, ctx):
        raise RuntimeError("boom")

def test_success_pipeline(monkeypatch):
    # حقن محركات في السجلّ
    from Integration_Layer import Domain_Router as DR
    DR._ENGINE_REGISTRY["e1"] = DummyOk() # type: ignore
    DR._ENGINE_REGISTRY["e2"] = DummyOk() # type: ignore
    pipe = [("e1","step"), ("e2","step")]
    out = execute_pipeline(pipe, {"text":"x"})
    assert out.get("ok") is True

def test_step_fallback_if_available(monkeypatch):
    """
    يختبر مسارات fallback إن وُجدت البنية في Task_Orchestrator، وإلا يتخطّى الاختبار.
    """
    from Integration_Layer import Domain_Router as DR
    DR._ENGINE_REGISTRY["bad"] = DummyFail() # type: ignore
    DR._ENGINE_REGISTRY["good"] = DummyOk() # type: ignore

    try:
        from Integration_Layer import Task_Orchestrator as TO
    except Exception:
        pytest.skip("Task_Orchestrator import failed unexpectedly.")

    if not hasattr(TO, "FALLBACKS"):
        pytest.skip("FALLBACKS dict not available; skipping fallback test.")

    TO.FALLBACKS[("bad","step")] = [("good","step")] # type: ignore
    pipe = [("bad","step")]
    out = execute_pipeline(pipe, {"text":"x"})
    assert out.get("ok") is True

def test_exhausted_fallbacks_or_no_fallbacks(monkeypatch):
    """
    في حال لا توجد مسارات بديلة أو كانت كلها تفشل، نتوقع تحذير/عدم نجاح
    لكن دون انهيار النظام.
    """
    from Integration_Layer import Domain_Router as DR
    DR._ENGINE_REGISTRY["bad1"] = DummyFail() # type: ignore
    DR._ENGINE_REGISTRY["bad2"] = DummyFail() # type: ignore

    try:
        from Integration_Layer import Task_Orchestrator as TO
        if hasattr(TO, "FALLBACKS"):
            TO.FALLBACKS[("bad1","step")] = [("bad2","step")] # type: ignore
    except Exception:
        pass  # لا بأس

    pipe = [("bad1","step")]
    out = execute_pipeline(pipe, {"text":"x"})
    assert (out.get("ok") is False) or ("warning" in out) or ("error" in out)
