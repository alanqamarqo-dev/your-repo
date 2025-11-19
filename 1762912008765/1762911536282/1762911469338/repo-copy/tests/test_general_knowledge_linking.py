from Core_Engines.General_Knowledge import GeneralKnowledgeEngine
from Knowledge_Base.adapters.kb_local import LocalKBAdapter


def test_gk_link_concepts():
    gk = GeneralKnowledgeEngine(kb_adapters={"local": LocalKBAdapter("Knowledge_Base/seed_knowledge.jsonl")})
    links = gk.link_concepts("أين تقع باريس؟")
    assert isinstance(links, dict)
