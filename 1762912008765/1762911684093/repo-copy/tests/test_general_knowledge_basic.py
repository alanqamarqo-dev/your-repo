from Core_Engines.General_Knowledge import GeneralKnowledgeEngine
from Core_Engines.GK_types import GKQuery
from Knowledge_Base.adapters.kb_local import LocalKBAdapter


def test_gk_basic_answer():
    gk = GeneralKnowledgeEngine(kb_adapters={"local": LocalKBAdapter("Knowledge_Base/seed_knowledge.jsonl")})
    ans = gk.answer(GKQuery(text="ما هي عاصمة فرنسا؟"))
    assert hasattr(ans, "answer_text")
    assert ans.confidence > 0
    assert isinstance(ans.supporting_facts, list)
