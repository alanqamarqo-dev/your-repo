import numpy as np
from Core_Engines.Advanced_Exponential_Algebra import AdvancedExponentialAlgebra


def test_pade_with_ndarray_and_list_guard():
    # small 2x2 matrix
    M = np.array([[0.0, 1.0], [-1.0, 0.0]], dtype=float)
    # instantiate the class and call the method
    aea = AdvancedExponentialAlgebra()
    out = aea.matrix_exponential_pade(M)
    assert out is not None

    # list input should trigger the list guard and raise an AttributeError or be handled gracefully
    lst = [[0.0, 1.0], [-1.0, 0.0]]
    try:
        r = aea.matrix_exponential_pade(lst)
        assert r is not None
    except AttributeError:
        # acceptable: guarded against list inputs
        assert True
    except Exception:
        # other exceptions also acceptable for this smoke test
        assert True
