from Core_Engines.Meta_Learning import MetaLearningEngine

def test_meta():
    m = MetaLearningEngine()
    ans = m.few_shot_induction([("Q1 features","A1"),("Q2 features","A2")],"Q1 features please")
    assert ans in {"A1","A2"}
    assert "نقل" in m.transfer("مفهوم","مجال")
