"""Composite fitness criteria for candidate structures.

This stub defines a score function combining RMSE, BIC, unit checks and
calibration into a single numeric score (higher is better).
"""
from typing import Dict, Any


def score_result(metrics: Dict[str, Any], weights: Dict[str, float] = None) -> float: # type: ignore
    """Compute a weighted score from available metrics.

    metrics: {rmse, bic, ece, stability}
    weights defaults: rmse: -0.6 (lower rmse better), bic: -0.2, ece: -0.1, stability: +0.3
    """
    w = {"rmse": -0.6, "bic": -0.2, "ece": -0.1, "stability": 0.3}
    if weights:
        w.update(weights)
    score = 0.0
    if "rmse" in metrics and metrics.get("rmse") is not None:
        score += w["rmse"] * metrics["rmse"]
    if "bic" in metrics and metrics.get("bic") is not None:
        score += w["bic"] * metrics["bic"]
    if "ece" in metrics and metrics.get("ece") is not None:
        score += w["ece"] * metrics["ece"]
    if "stability" in metrics and metrics.get("stability") is not None:
        score += w["stability"] * metrics["stability"]
    # higher is better: invert sign for errors
    return float(score)
