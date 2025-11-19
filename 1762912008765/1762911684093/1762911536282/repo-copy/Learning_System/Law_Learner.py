# -*- coding: utf-8 -*-
from __future__ import annotations
from sympy import symbols, simplify
from typing import Any, Dict, List
import numpy as np


class LawLearner:
    """Simple restricted proposal generator for laws.

    propose_scale_bias returns a proposal expression and parameter names.
    """

    def __init__(self, parser: Any):
        self.parser = parser

    def propose_scale_bias(self, base_equation_str: str) -> Dict[str, Any]:
        # simple kernel: take expr == 0 and propose expr + alpha + beta
        alpha, beta = symbols("alpha beta", real=True)
        expr = self.parser.normalize(base_equation_str)
        proposal = simplify(expr + alpha + beta)
        return {"proposal_expr": proposal, "params": ["alpha", "beta"]}

    def fit_params(self, base_equation_str: str, samples: List[Dict[str, float]]) -> Dict[str, Any]:
        """Fit alpha,beta to samples using least-squares.

        samples: list of dicts mapping variable name to numeric value, e.g. {'F': 10, 'm': 2, 'a':5}
        Assumes base_equation_str is of the form 'expr = 0' or similar where proposal is expr + alpha + beta.
        Returns: {alpha, beta, rmse, confidence}
        """
        # build design matrix: for each sample, evaluate expr (numeric) without alpha/beta, then fit residual = -alpha - beta
        expr = self.parser.normalize(base_equation_str)
        # convert sympy expr to a lambda for numeric evaluation
        try:
            from sympy import lambdify
            vars_in_expr = sorted(list(expr.free_symbols), key=lambda s: s.name)
            f = lambdify(vars_in_expr, expr, 'numpy')
        except Exception:
            return {"error": "symbolic_lambdify_failed"}

        # prepare data
        y = []
        A = []
        for s in samples:
            try:
                vals = [s.get(str(v), 0.0) for v in vars_in_expr]
                val = float(f(*vals))
                # model: val + alpha + beta = 0  ->  alpha + beta = -val
                y.append(-val)
                # we fit two params: alpha and beta (both multiply 1)
                A.append([1.0, 1.0])
            except Exception:
                continue

        if len(y) < 2:
            return {"error": "not_enough_samples", "n": len(y)}

        A = np.array(A)
        y = np.array(y)
        # least squares
        sol, *_ = np.linalg.lstsq(A, y, rcond=None)
        alpha_hat, beta_hat = float(sol[0]), float(sol[1])
        preds = A.dot(sol)
        mse = float(np.mean((preds - y) ** 2))
        rmse = float(np.sqrt(mse))
        # confidence heuristic: 1/(1+rmse) clipped
        confidence = max(0.0, min(1.0, 1.0 / (1.0 + rmse)))
        return {"alpha": alpha_hat, "beta": beta_hat, "rmse": rmse, "confidence": confidence}


def fit_single_coeff_linear(formula: str, y_name: str, x_name: str, data: dict):
    """Fit y = c * x simple linear coefficient from data dict.

    data: {'y_name': [...], 'x_name': [...]}
    Returns: {'coef', 'rmse', 'n', 'confidence'}
    """
    import math
    y = data.get(y_name, [])
    x = data.get(x_name, [])
    if not y or not x or len(y) != len(x):
        raise ValueError("Invalid data: unequal or empty lengths")
    num = sum(xi*yi for xi, yi in zip(x, y))
    den = sum(xi*xi for xi in x)
    if den == 0:
        raise ValueError("Cannot fit: all x are zero")
    c = num/den
    residuals = [(yi - c*xi) for xi, yi in zip(x, y)]
    rmse = math.sqrt(sum(r*r for r in residuals)/len(x))
    n = len(x)
    confidence = max(0.0, min(1.0, (1.0/(1.0 + rmse)) * (1.0 - math.exp(-n/20))))
    return {"coef": c, "rmse": rmse, "n": n, "confidence": confidence}


def fit_linear_with_intercept(formula: str, y_name: str, x_name: str, data: dict):
    """Fit y = a*x + b using least squares.
    Returns {'a','b','rmse','n','confidence'}
    """
    import numpy as _np, math as _math
    y = data.get(y_name, [])
    x = data.get(x_name, [])
    if not y or not x or len(y) != len(x):
        raise ValueError("Invalid data: unequal or empty lengths")
    A = _np.vstack([_np.array(x), _np.ones(len(x))]).T
    yv = _np.array(y)
    sol, *_ = _np.linalg.lstsq(A, yv, rcond=None)
    a, b = float(sol[0]), float(sol[1])
    preds = A.dot(sol)
    residuals = yv - preds
    rmse = float(_math.sqrt(float((_np.mean(residuals**2)))))
    n = len(x)
    confidence = max(0.0, min(1.0, (1.0/(1.0 + rmse)) * (1.0 - _math.exp(-n/20))))
    return {"a": a, "b": b, "rmse": rmse, "n": n, "confidence": confidence}


def fit_power_law(formula: str, y_name: str, x_name: str, data: dict):
    """Fit y = a * x^n by log-transform: log y = log a + n log x.
    Returns {'a','n','rmse','n_samples','confidence'}
    """
    import numpy as _np, math as _math
    y = data.get(y_name, [])
    x = data.get(x_name, [])
    if not y or not x or len(y) != len(x):
        raise ValueError("Invalid data: unequal or empty lengths")
    lx = _np.log(_np.array(x))
    ly = _np.log(_np.array(y))
    A = _np.vstack([lx, _np.ones(len(lx))]).T
    sol, *_ = _np.linalg.lstsq(A, ly, rcond=None)
    n_exp = float(sol[0])
    log_a = float(sol[1])
    a = _math.exp(log_a)
    preds = _np.exp(A.dot(sol))
    residuals = _np.array(y) - preds
    rmse = float(_math.sqrt(float((_np.mean(residuals**2)))))
    n = len(x)
    confidence = max(0.0, min(1.0, (1.0/(1.0 + rmse)) * (1.0 - _math.exp(-n/20))))
    return {"a": a, "n": n_exp, "rmse": rmse, "n_samples": n, "confidence": confidence}


def fit_model_auto(formula: str, y_name: str, x_name: str, data: dict, model: str = "auto"):
    """High-level helper that chooses fitting routine based on model hint.
    model: 'linear', 'linear_intercept', 'power', or 'auto'
    """
    # simple dispatch
    if model == "linear":
        return fit_single_coeff_linear(formula, y_name, x_name, data)
    if model == "linear_intercept":
        return fit_linear_with_intercept(formula, y_name, x_name, data)
    if model == "power":
        return fit_power_law(formula, y_name, x_name, data)
    # auto: pick linear_intercept if more than 2 samples, else single coeff
    n = len(data.get(x_name, []))
    if n >= 3:
        return fit_linear_with_intercept(formula, y_name, x_name, data)
    return fit_single_coeff_linear(formula, y_name, x_name, data)
