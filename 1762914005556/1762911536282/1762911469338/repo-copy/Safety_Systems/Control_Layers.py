"""Control layer shim that re-exports the project's Safety_Control implementation.
"""
try:
    from Safety_Control.Safety_Control_Layer import ControlLayers  # type: ignore
except Exception:
    # Minimal fallback
    class ControlLayers:
        def __init__(self):
            pass
        def derive_risk_level(self, checks_passed: bool, signals: dict, confidence: float) -> str: # type: ignore
            if not checks_passed:
                return "high"
            any_error = any((v or {}).get("error") for v in (signals or {}).values())
            if any_error:
                return "medium"
            return "low" if (confidence or 0.0) >= 0.5 else "medium"

        def evaluate_improvement_safety(self, integrated_solution):
            signals = integrated_solution.get('signals', {}) or {}
            confidence = float(integrated_solution.get('confidence', 0.0))
            checks_passed = bool(integrated_solution.get('checks_passed', True))
            risk = self.derive_risk_level(checks_passed, signals, confidence)
            return {"approved": checks_passed and risk != "high", "risk_level": risk}

        def derive_risk_level(self, checks_passed: bool, signals: dict, confidence: float) -> str:
            # If core checks fail, mark as high risk
            if not checks_passed:
                return "high"
            # any engine reported an error -> medium
            any_error = any(bool(v.get('error')) for v in (signals or {}).values())
            if any_error:
                return "medium"
            # If all checks passed and no errors, decrease risk when confidence >= 0.5
            return "low" if (confidence or 0.0) >= 0.5 else "medium"

