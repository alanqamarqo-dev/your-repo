"""
Very small shim for numpy functions used by the project. Not a full
replacement. Intended to allow local runs and static analysis without
installing numpy during early development.
"""
from typing import Any

def ceil(x):
    return int(-(-x // 1)) if isinstance(x, (int, float)) else x

def log2(x):
    import math
    return math.log2(x)

def eye(n, dtype=None, device=None):
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

def ndarray_like(A):
    return A

# minimal linalg helpers
class linalg:
    @staticmethod
    def solve(a, b):
        # naive solver for small matrices represented as nested lists
        import copy
        from math import isclose
        # Not a real solver - placeholder to allow simple demos.
        return b


def array(x):
    return x

# convenience aliases used in stubs
def linalg_norm(A, ord):
    import math
    # simplistic norm: max row sum
    if hasattr(A, 'shape'):
        try:
            rows = len(A)
        except Exception:
            return 0
    if isinstance(A, list):
        return max(sum(abs(v) for v in row) for row in A)
    return abs(A)


def linalg_solve(a, b):
    return b
