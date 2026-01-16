from typing import Dict, Any


class BaseSolver:
    def solve(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()
