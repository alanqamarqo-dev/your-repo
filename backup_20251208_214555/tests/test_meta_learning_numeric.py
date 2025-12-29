import pytest
from Core_Engines.Meta_Learning import MetaLearningEngine


def test_affine_extraction_and_prediction():
    m = MetaLearningEngine()
    examples = [(1, 3), (2, 5), (3, 7)]  # y = 2x + 1
    principles = m.extract_principles(examples)
    ids = [p['id'] for p in principles]
    assert 'affine' in ids
    pred = m.few_shot_predict(10)
    # expecting y = 2*10 + 1 = 21
    assert abs(pred - 21) < 1e-6
