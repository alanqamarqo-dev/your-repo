"""Utilities to compute/persist uncertainty estimates (CI) for models.

This is a minimal stub that exposes the API used by the orchestrator.
"""
from typing import Any, Dict, List


def pred_confidence_intervals(y_true, y_pred, alpha=0.05) -> Dict[str, float]:
    """Return a trivial CI summary for predictions (stub).

    Real implementation: bootstrap or analytic delta-method.
    """
    return {"lower_mean": 0.0, "upper_mean": 0.0, "alpha": alpha}


def param_confidence_intervals(params, alpha=0.05) -> Dict[str, List[float]]:
    return {k: [v - 0.1 * abs(v), v + 0.1 * abs(v)] for k, v in (params or {}).items()}
