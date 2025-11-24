from Core_Engines.General_Knowledge import GeneralKnowledgeEngine

def test_gk_retrieve_validate():
    gk = GeneralKnowledgeEngine()
    assert gk.retrieve("force")[0][0].startswith("physics")
    assert gk.validate("A fact.")
