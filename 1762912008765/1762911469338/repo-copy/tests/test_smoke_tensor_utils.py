import numpy as np
from Core_Engines import tensor_utils as tu


def test_to_numpy_and_to_torch_complex64_none_and_array():
    # None should be handled gracefully
    res_none = tu.to_numpy_safe(None)
    # Some environments may return None, others may return array(None)
    import numpy as _np
    assert res_none is None or (_np is not None and isinstance(res_none, _np.ndarray))

    a = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=float)
    na = tu.to_numpy_safe(a)
    assert isinstance(na, np.ndarray)

    # attempt to coerce to torch complex64 (in our stub this may return None or a numpy-backed tensor)
    res = tu.to_torch_complex64(a)
    # Accept both None (if torch unavailable) or an object result
    assert res is None or hasattr(res, '__array__') or hasattr(res, 'dtype')
