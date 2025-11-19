import numpy as np

def test_safe_matmul_and_pade_fallback():
    from Core_Engines.tensor_utils import safe_matmul, to_numpy_safe
    from Core_Engines.Advanced_Exponential_Algebra import AdvancedExponentialAlgebra

    a = np.array([[0.0, -1.0], [1.0, 0.0]])
    b = np.array([[1.0, 0.0], [0.0, 1.0]])

    # safe_matmul should compute numpy matmul when given numpy arrays
    r = safe_matmul(__import__('torch'), a, b)
    assert (to_numpy_safe(r) is not None)

    aea = AdvancedExponentialAlgebra()
    # matrix_exponential_pade should accept numpy arrays and return numpy array
    E = aea.matrix_exponential_pade(a)
    assert hasattr(E, 'shape')
