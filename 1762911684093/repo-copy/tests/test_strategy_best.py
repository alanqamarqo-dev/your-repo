from Core_Engines.Strategic_Thinking import StrategicThinkingEngine

def test_strategy():
    s = StrategicThinkingEngine()
    assert len(s.plan("النمو",3)) == 3
    m = s.evaluate("خيار"); assert set(m) == {"benefit","risk","tradeoff"}
    assert len(s.scenarios("النمو")) == 3
