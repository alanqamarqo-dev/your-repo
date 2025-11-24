import AGL

def test_version():
    assert getattr(AGL, '__version__', '0.0.0') >= '0.3.1'
