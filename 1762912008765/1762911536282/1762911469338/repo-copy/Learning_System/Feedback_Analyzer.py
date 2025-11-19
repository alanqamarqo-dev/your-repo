# -*- coding: utf-8 -*-
from __future__ import annotations
import math
from typing import Dict, Any


class FeedbackAnalyzer: # type: ignore
    """
    Analyze run outputs and suggest improvement areas. This class exposes a
    pure helper `compute_gaps` that can be unit-tested separately from any
    file I/O.
    """
    def compute_gaps(self, conf: float, signals: dict, safety: dict) -> dict:
        def _score(of):
            if isinstance(of, dict):
                return float(of.get("score", 0.0))
            return 0.0

        m = _score(signals.get("mathematical_brain", {}))
        q = _score(signals.get("quantum_processor", {}))
        c = _score(signals.get("code_generator", {}))
        p = _score(signals.get("protocol_designer", {}))

        target_conf = 0.80
        risk_level = safety.get("risk_level", "unknown")

        gaps = {
            "confidence_gap": round(target_conf - conf, 4),
            "risk_is_high": (risk_level in ("medium", "high")),
            "components": {
                "mathematical_brain": {"score": m, "needs_boost": m < 0.75},
                "quantum_processor":  {"score": q, "needs_boost": q < 0.65},
                "code_generator":     {"score": c, "needs_boost": c < 0.80},
                "protocol_designer":  {"score": p, "needs_boost": p < 0.65},
            },
        }

        base_weights = {
            "mathematical_brain": 1.0,
            "quantum_processor":  0.6,
            "code_generator":     1.1 if c >= 0.8 else 1.0,
            "protocol_designer":  0.6,
        }
        if gaps["risk_is_high"]:
            if q < 0.5: base_weights["quantum_processor"] = 0.4
            if p < 0.5: base_weights["protocol_designer"]  = 0.4

        return {"target_confidence": target_conf, "observed_confidence": conf, "gaps": gaps, "suggested_fusion_weights": base_weights}

    def analyze_performance_feedback(self, run_record: dict) -> dict:
        sol = run_record.get("solution", {})
        signals = run_record.get("signals", {})
        conf = float(run_record.get("confidence_score", sol.get("confidence", 0.0)))
        safety = run_record.get("safety", {})
        return self.compute_gaps(conf, signals, safety)

