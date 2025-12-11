import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pytest
import types

import Self_Improvement.Knowledge_Graph as KG


def test_basic_and_memory_and_critic(monkeypatch):
    # 1) basic happy path: collaborative_solve returns winner
    fake_res = {
        "winner": {"engine": "gen_creativity", "content": {"ideas": [{"idea": "x"}]}, "score": 0.8},
        "top": [],
    }

    def fake_collab(self, prob, domains_needed=None):
        return fake_res

    monkeypatch.setattr(KG.CognitiveIntegrationEngine, "collaborative_solve", fake_collab)

    # intercept collective.share_learning to capture writes
    mem_log = []

    def fake_share(self, engine_name, learning_data, verified_by=None):
        mem_log.append((engine_name, learning_data))
        return learning_data

    monkeypatch.setattr(KG.CollectiveMemorySystem, "share_learning", fake_share)

    # run pipeline once
    out1 = KG.agl_pipeline("سؤال عادي")
    assert isinstance(out1.get("answer"), str)
    assert out1.get("provenance") and out1["provenance"].get("winner")

    # run pipeline second time to ensure memory write called
    out2 = KG.agl_pipeline("سؤال عادي")
    assert len(mem_log) >= 2

    # 2) critic-block: simulate critic present and returns 'danger'
    def fake_connect(self):
        # ensure engines_registry has critic key
        self.engines_registry = {"critic": {}}

    def fake_query_engine(self, engine_name, problem, context=None):
        if engine_name == 'critic':
            return {"result": "This is dangerous and illegal"}
        return {}

    monkeypatch.setattr(KG.CognitiveIntegrationEngine, "connect_engines", fake_connect)
    monkeypatch.setattr(KG.CognitiveIntegrationEngine, "query_engine", fake_query_engine)

    out3 = KG.agl_pipeline("نفّذ شيء غير قانوني")
    assert isinstance(out3.get("answer"), str)
    assert "غ" in out3.get("answer") or "عذراً" in out3.get("answer")
