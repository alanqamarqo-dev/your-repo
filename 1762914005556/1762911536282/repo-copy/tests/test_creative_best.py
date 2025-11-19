from Core_Engines.Creative_Innovation import CreativeInnovationEngine

def test_creative_out():
    e = CreativeInnovationEngine()
    assert len(e.lateral_think("المنتج")) == 7
    assert len(e.novel_ideas("المنتج",3)) == 3
