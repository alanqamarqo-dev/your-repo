import torch
from Core_Engines.Advanced_Exponential_Algebra import AdvancedExponentialAlgebra
A = torch.tensor([[0.0,1.0],[-1.0,0.0]])
aea = AdvancedExponentialAlgebra()
expA = aea.matrix_exponential_pade(A)
print('returned type:', type(expA))
try:
    import numpy as np
    print('is ndarray?', isinstance(expA, np.ndarray))
except Exception:
    pass
print('has dtype?', getattr(expA, 'dtype', None))
print('has shape?', getattr(expA, 'shape', None))
print('repr first:', repr(expA)[:400])
