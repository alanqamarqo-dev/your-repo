from Core_Engines.Perception_Context import PerceptionContext


def test_extract_empty_and_partial():
    pc = PerceptionContext()
    out_empty = pc.extract({})
    assert set(out_empty.keys()) == {'context', 'meta', 'confidence'}
    assert out_empty['confidence'] == 0.6
    out = pc.extract({"V": 12})
    assert 'context' in out and 'meta' in out
    # either surfaced as a context key or present in meta keys
    assert ('V' in out.get('context', {})) or ('V' in out.get('meta', {}).get('keys', []))
