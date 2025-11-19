from Core_Engines.Meta_Learning import MetaLearningEngine


def test_transfer_and_self_improve():
    m = MetaLearningEngine()
    examples = [(1, 2), (2, 4)]  # y=2x
    m.extract_principles(examples)
    before = m.list_principles()
    assert any(p['id'] == 'affine' for p in before)

    res = m.cross_domain_transfer({'affine': 'affine_copy'})
    assert res['count'] == 1
    assert 'affine_copy' in res['new_ids']

    fb = [{'id': 'affine_copy', 'correct': True}, {'id': 'affine', 'correct': False}]
    out = m.self_improve(fb, lr=0.5)
    assert 'affine_copy' in out and 'affine' in out
    assert 0.0 <= out['affine'] <= 1.0
