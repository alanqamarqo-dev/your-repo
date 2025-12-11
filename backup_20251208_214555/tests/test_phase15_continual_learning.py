from pathlib import Path
import os
import json
import importlib

from Self_Improvement import continual_learning as cl


def test_phase15_record_and_load_learned_facts(tmp_path, monkeypatch):
    # Point artifacts dir to a temp path
    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setenv("AGL_ARTIFACTS_DIR", str(artifacts_dir))

    # Reload module so that ARTIFACTS_DIR/LEARNED_FACTS_PATH are set from env
    importlib.reload(cl)

    problem = {
        "title": "flu_symptoms",
        "question": "ما هي أعراض الإنفلونزا؟",
    }
    answer = "حمى، صداع، سعال، آلام عضلية، إرهاق."
    score = 0.9

    ok = cl.record_learned_fact(problem, answer, score, source="unit_test", min_score=0.8)
    assert ok is True

    # the file must be created
    assert cl.LEARNED_FACTS_PATH.exists()

    rows = cl.load_learned_facts()
    assert len(rows) == 1
    row = rows[0]
    assert row["title"] == "flu_symptoms"
    assert "حمى" in row["answer"]
    assert row["score"] == score
    assert row["source"] == "unit_test"
