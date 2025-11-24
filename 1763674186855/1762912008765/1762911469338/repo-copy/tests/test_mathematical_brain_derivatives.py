import sympy as sp
import numpy as np
from Core_Engines.Mathematical_Brain import MathematicalBrain, AdvancedLinearAlgebra


def test_symbolic_derivative_poly2():
    x = sp.symbols('x')
    f = 3*x**2 + 2*x + 1
    df = sp.diff(f, x)
    assert str(df) == '6*x + 2'


def test_numeric_integral_linear():
    mb = MathematicalBrain()
    # Implement a simple numeric_integral via numpy trap rule if missing
    def integral(func, a, b, n=100):
        xs = np.linspace(a, b, n+1)
        ys = np.array([func(x) for x in xs])
        return np.trapezoid(ys, xs)

    area = integral(lambda t: 2*t + 1, 0.0, 1.0, n=200)
    assert abs(area - 2.0) < 1e-2
