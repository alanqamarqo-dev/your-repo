import pytest
from tests.helpers.engine_ask import ask_engine

ENGINES = [
    "Analogy_Mapping_Engine",
    "Reasoning_Layer",
    "Creative_Innovation",
    "Protocol_Designer",
    "General_Knowledge",
]

PROMPT = (
    "اشرح كيف نطبّق مفهوم تدفّق الماء (قنوات، ضغط، صمامات، فقدان احتكاك)"
    " لتصميم نظام تعليمي مرن (مسارات تعلم، نقاط اختناق، تغذية راجعة، قياس تدفّق المحتوى)."
    " أعطِ قيودًا ومقايضات وخطوات تنفيذ."
)

@pytest.mark.parametrize("engine", ENGINES)
def test_engine_handles_same_prompt(engine):
    res = ask_engine(engine, PROMPT)
    assert isinstance(res, dict) and res.get("ok") is True
    text = (res.get("text") or "").strip()
    assert text, f"{engine} returned empty text"
    if engine == "Analogy_Mapping_Engine":
        assert res.get("domain") == "education"
        assert isinstance(res.get("map"), (list, tuple)) and len(res["map"]) >= 4
