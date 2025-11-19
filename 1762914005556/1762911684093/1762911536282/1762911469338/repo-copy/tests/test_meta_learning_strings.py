from Core_Engines.Meta_Learning import MetaLearningEngine


def test_reverse_rule_detection_and_apply():
    m = MetaLearningEngine()
    examples = [("abc", "cba"), ("dog", "god")]
    principles = m.extract_principles(examples)
    ids = [p['id'] for p in principles]
    assert 'reverse' in ids
    out = m.few_shot_predict('hello')
    assert out == 'olleh'


def test_upper_and_suffix_rules():
    m = MetaLearningEngine()
    examples = [("hi", "HI"), ("bye", "BYE")]
    principles = m.extract_principles(examples)
    assert any(p['id'] == 'upper' for p in principles)

    m2 = MetaLearningEngine()
    examples2 = [("a", "ax"), ("b", "bx")]
    principles2 = m2.extract_principles(examples2)
    assert any(p['id'] == 'add_suffix' for p in principles2)
    pred = m2.few_shot_predict('z')
    assert pred == 'zx'
