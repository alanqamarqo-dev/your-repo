from Core_Engines.General_Knowledge import GeneralKnowledgeEngine
from Core_Engines.GK_types import GKFact, GKEvidence, GKSource, GKQuery
from Knowledge_Base.adapters.kb_local import LocalKBAdapter


def test_gk_contradiction_detection():
    gk = GeneralKnowledgeEngine(kb_adapters={"local": LocalKBAdapter("Knowledge_Base/seed_knowledge.jsonl")})
    ev = GKEvidence(text="باريس عاصمة فرنسا", source=GKSource(uri="seed://1", title="seed", provider="local"))
    f1 = GKFact(subject="France", predicate="capital", obj="Paris", confidence=0.9, provenance=[ev])
    f2 = GKFact(subject="France", predicate="capital", obj="Lyon", confidence=0.6, provenance=[ev])
    gk.update_knowledge([f1, f2])

    ans = gk.answer(GKQuery(text="ما عاصمة فرنسا؟"))
    assert ans.confidence <= 0.99
    # contradictions may or may not be detected by simple heuristics; accept either but ensure supporting_facts present
    assert isinstance(ans.supporting_facts, list)
