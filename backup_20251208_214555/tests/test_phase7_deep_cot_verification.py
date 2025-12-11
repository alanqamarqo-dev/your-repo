import os
from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter


def test_phase7_deep_cot_path(monkeypatch):
    # ensure FAST_MODE is off so deep path is used
    monkeypatch.setenv("AGL_FAST_MODE", "0")
    monkeypatch.setenv("AGL_DEEP_COT", "1")
    monkeypatch.setenv("AGL_COT_SAMPLES", "3")

    adapter = HostedLLMAdapter()

    called = {"count": 0}

    def fake_run_deep_cot(prompt, question, task_type="qa_single"):
        called["count"] += 1
        return {
            "reasoning": "خطوات تحليل وهمية",
            "answer": "هذه إجابة تجريبية من deep_cot",
        }

    # monkeypatch the instance method
    monkeypatch.setattr(adapter, "_run_deep_cot", fake_run_deep_cot)

    task = {
        "question": "ما هو داء السكري؟ عرّفه باختصار.",
        "task_type": "qa_single",
    }

    result = adapter.process_task(task)

    assert called["count"] == 1
    assert result["content"]["answer"] == "هذه إجابة تجريبية من deep_cot"
    assert result["content"]["note"] == "deep_cot_v1"
