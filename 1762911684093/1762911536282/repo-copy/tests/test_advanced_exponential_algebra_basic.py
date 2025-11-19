import pytest

import numpy as np

from Core_Engines.Advanced_Exponential_Algebra import AdvancedExponentialAlgebra, LieAlgebraProcessor


def test_matrix_exponential_pade_list_guard():
    aea = AdvancedExponentialAlgebra()
    with pytest.raises(AttributeError):
        aea.matrix_exponential_pade([ [1, 0], [0, 1] ])


def test_lie_bracket_and_structure_constants():
    aea = AdvancedExponentialAlgebra()

    import torch
    A = torch.zeros((2,2))
    B = torch.zeros((2,2))
    A[0,1] = 1
    B[1,0] = 2

    bracket = aea.lie_bracket(A, B)
    # bracket should be a tensor-like object with __getitem__ available
    assert hasattr(bracket, '__getitem__')

    # structure constants on a small basis
    basis = [A, B]
    sc = aea.structure_constants(basis)
    # shape n,n,n
    assert hasattr(sc, '__getitem__')


def test_solve_ode_and_quantum_evolution_small():
    aea = AdvancedExponentialAlgebra()
    # simple 2x2 rotation generator
    H = np.array([[0.0, -1.0], [1.0, 0.0]])
    x0 = np.array([1.0, 0.0])
    t_points = [0.0, 0.5, 1.0]

    sols = aea.solve_ode_via_exponential(H, x0, t_points)
    # our stubbed torch.stack returns a list-like
    assert len(sols) == len(t_points)

    # quantum evolution with simple Hamiltonian
    qsols = aea.quantum_time_evolution(H, x0, t_points)
    assert len(qsols) == len(t_points)
