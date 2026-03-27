from agl.lib.solvers.BaseSolver import BaseSolver
from typing import Dict, Any


class QuantumSolver(BaseSolver):
    def solve(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        # minimal smoke: if goal is probability, return a dummy probability
        goal = problem.get("goal")
        if goal == "probability":
            return {"ok": True, "result": "p=0.5 (approx)", "steps": ["apply U to |ψ>, compute overlap"], "uncertainty": 0.2, "domain": "quantum"}
        return {"ok": False, "message": "QuantumSolver: unsupported goal", "domain": "quantum"}
