import sys
import types
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pytest

import Self_Improvement.Knowledge_Graph as KG


def test_rag_error_fallback(monkeypatch):
    # create fake Integration_Layer.rag_wrapper that returns an error-shaped response
    pkg = types.ModuleType("Integration_Layer")
    mod = types.ModuleType("Integration_Layer.rag_wrapper")

    def rag_answer(*args, **kwargs):
        return {"answer": json.dumps({"_error": "cannot produce JSON"}, ensure_ascii=False)}

    mod.rag_answer = rag_answer
    pkg.rag_wrapper = mod
    monkeypatch.setitem(sys.modules, "Integration_Layer", pkg)
    monkeypatch.setitem(sys.modules, "Integration_Layer.rag_wrapper", mod)

    # fake collaborative_solve to return a provenance with a gen_creativity winner
    fake_res = {
        "winner": {
            "engine": "gen_creativity",
            "content": {"ideas": [{"idea": "idea-1"}, {"idea": "idea-2"}]},
            "score": 0.9,
        },
        "top": [],
    }

    def fake_collab(self, prob, domains_needed=None):
        return fake_res

    monkeypatch.setattr(KG.CognitiveIntegrationEngine, "collaborative_solve", fake_collab)

    # Run pipeline
    res = KG.agl_pipeline("سؤال تجريبي")
    ans = res.get("answer")

    assert isinstance(ans, str)
    assert "_error" not in ans
    assert "idea-1" in ans
