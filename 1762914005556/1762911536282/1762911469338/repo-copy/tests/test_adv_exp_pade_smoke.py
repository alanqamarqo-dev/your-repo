import numpy as np
from scipy.linalg import expm
from Core_Engines.Advanced_Exponential_Algebra import AdvancedExponentialAlgebra


def test_exp_pade_matches_scipy_small():
    A = np.array([[0.0, 1.0], [-2.0, 3.0]])
    aea = AdvancedExponentialAlgebra()
    my = aea.matrix_exponential_pade(A)
    ref = expm(A)
    assert np.allclose(my, ref, atol=1e-6) # type: ignore
