import os
import importlib


def test_load_learned_facts_as_context(tmp_path, monkeypatch):
    # Point artifacts dir to tmp_path for isolation
    monkeypatch.setenv("AGL_ARTIFACTS_DIR", str(tmp_path))
    # import module freshly
    import Self_Improvement.continual_learning as cl
    importlib.reload(cl)

    # Ensure file is empty initially
    facts = cl.load_learned_facts(max_items=10)
    assert facts == []

    # Record a learned fact (above threshold)
    problem = {"title": "اختبار", "question": "ما هي أعراض X؟"}
    ok = cl.record_learned_fact(problem, answer="أعراض X تشمل A و B.", score=0.95, source="test", min_score=0.8)
    assert ok is True

    # Reload to ensure module paths are stable
    importlib.reload(cl)

    ctx = cl.load_learned_facts_as_context(max_items=5)
    assert isinstance(ctx, str)
    assert "أعراض X" in ctx or "A و B" in ctx
