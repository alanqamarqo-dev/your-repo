from agl.lib.solvers.BaseSolver import BaseSolver
from typing import Dict, Any


class PhysicsSolver(BaseSolver):
    def solve(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        # Simple handling of electrical Ohm-style problems from 'given'
        given = problem.get("given", {})
        V = given.get("V")
        I = given.get("I")
        R = given.get("R")
        try:
            if V is None and I is not None and R is not None:
                return {"ok": True, "result": f"V={float(I)*float(R)}", "steps": ["V = I * R"], "uncertainty": 0.01, "domain": "electrical"}
            if I is None and V is not None and R is not None:
                return {"ok": True, "result": f"I={float(V)/float(R)}", "steps": ["I = V / R"], "uncertainty": 0.01, "domain": "electrical"}
            if R is None and V is not None and I is not None:
                return {"ok": True, "result": f"R={float(V)/float(I)}", "steps": ["R = V / I"], "uncertainty": 0.01, "domain": "electrical"}
        except Exception:
            return {"ok": False, "message": "PhysicsSolver: invalid numeric values", "domain": "electrical"}

        return {"ok": False, "message": "PhysicsSolver: insufficient data or unknown subdomain", "domain": "physics"}
