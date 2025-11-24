"""
Minimal local stub of a subset of the `torch` API used in this project.
This is intentionally lightweight and implemented on top of the included
`stubs.numpy` shim so static analyzers (pyright) and simple local runs
can import `torch` without the real heavy dependency.
"""
from typing import Any
from stubs import numpy as np


def norm(A: Any, ord: float = 2.0):
    return np.linalg_norm(A, ord)


def eye(n: int, dtype=None, device=None):
    return np.eye(n)


class linalg:
    @staticmethod
    def solve(a, b):
        return np.linalg_solve(a, b)


Tensor = Any
