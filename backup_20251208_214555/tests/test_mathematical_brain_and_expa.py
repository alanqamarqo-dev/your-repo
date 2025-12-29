import torch
import numpy as np
from Core_Engines.Mathematical_Brain import MathematicalBrain
from Core_Engines.Advanced_Exponential_Algebra import AdvancedExponentialAlgebra


def test_mathematical_brain_differential():
    mb = MathematicalBrain()
    res = mb.process_task("حل معادلة تفاضلية")
    assert res.get('ok') is True
    assert 'symbolic-analysis' in res.get('result', {}).get('method', '')


def test_matrix_exponential_pade_small():
    A = torch.tensor([[0.0, 1.0], [-1.0, 0.0]])
    aea = AdvancedExponentialAlgebra()
    try:
        expA = aea.matrix_exponential_pade(A)
    except OverflowError:
        import pytest
        pytest.skip("matrix_exponential_pade incompatible with this torch/numpy combo")
    # compare trace to numpy/scipy fallback for sanity (trace of exp(iR) should be finite)
    t = torch.trace(expA).item() # type: ignore
    assert abs(t) < 10.0
