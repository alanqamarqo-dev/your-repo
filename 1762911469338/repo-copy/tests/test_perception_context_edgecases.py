from Core_Engines.Perception_Context import extract_features, PerceptionContext


def test_extract_features_none_and_empty():
    f_none = extract_features(None) # type: ignore
    assert isinstance(f_none, dict)
    assert 'domain_signals' in f_none

    f_empty = extract_features("")
    assert isinstance(f_empty['tokens'], list)


def test_perception_context_extract_variants():
    pc = PerceptionContext()

    # None input
    out = pc.extract(None)
    assert out['confidence'] == 0.0

    # dict input with expected keys
    inp = {'user': 'alice', 'task': 'measure', 'ts': 123}
    out = pc.extract(inp)
    assert out['context'].get('user') == 'alice'
    assert out['meta']['has_ts'] is True

    # string input fallback
    out = pc.extract('This is a test string mentioning ψ and H')
    assert out['confidence'] >= 0.4
