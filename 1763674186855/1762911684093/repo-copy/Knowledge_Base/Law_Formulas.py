from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from sympy import symbols, sympify

@dataclass
class LawFormula:
    id: str
    name: str
    domain: str
    variables: List[str]
    equation_str: str            # بصيغة f(...)=0 مثل: "F - m*a"
    assumptions: Optional[Dict[str, Any]] = None
    units: Optional[Dict[str, str]] = None
    notes: str = ""

    def to_sympy(self):
        loc = {v: symbols(v) for v in self.variables}
        return sympify(self.equation_str, locals=loc)

class LawFormulaStore:
    def __init__(self):
        self._items: Dict[str, LawFormula] = {}
    def add(self, f: LawFormula): self._items[f.id] = f
    def get(self, fid: str) -> LawFormula: return self._items[fid]
    def all(self) -> List[LawFormula]: return list(self._items.values())
