import os
import pytest
from Integration_Layer.Task_Orchestrator import TaskOrchestrator, normalize_text, stable_inputs_hash


def test_normalize_and_hash():
    s = "  اختبار  \n"
    assert normalize_text(s) == "اختبار"
    h = stable_inputs_hash("مهمة تجريبية", 42)
    assert isinstance(h, str) and len(h) == 64


def test_process_task_empty():
    to = TaskOrchestrator()
    res = to.process_task(None)
    assert res.get("error") == "empty_task"


def test_process_task_differential_routing():
    to = TaskOrchestrator()
    res = to.process_task("حل معادلة تفاضلية بسيطة")
    # either returns solution or an error string, but should not crash
    assert isinstance(res, dict)

