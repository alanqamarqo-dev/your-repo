from __future__ import annotations
from sympy import simplify
from sympy.parsing.sympy_parser import parse_expr
from typing import Any
from Knowledge_Base.Domain_Expertise import ALIASES


def _apply_aliases_to_expr(s: str) -> str:
    if not s or not isinstance(s, str):
        return s
    out = s
    for a, b in (ALIASES or {}).items():
        out = out.replace(f" {a} ", f" {b} ")
        out = out.replace(f"({a})", f"({b})")
        out = out.replace(f"{a}*", f"{b}*")
        out = out.replace(f"*{a}", f"*{b}")
        out = out.replace(f"{a}", f"{b}")
    return out


class LawParser:
    """Simple law expression parser/normalizer using SymPy.

    - normalize: accepts strings like 'F=ma' or '2*x + 3 = y' and returns a
      simplified SymPy expression representing (lhs)-(rhs) when '=' present.
    - equivalent: checks symbolic equivalence (a - b) simplifies to 0.
    """

    def normalize(self, expr_str: str) -> Any:
        if not isinstance(expr_str, str):
            raise TypeError("expr_str must be a string")
        # apply aliases before parsing
        expr_str = _apply_aliases_to_expr(expr_str)
        # Convert equality into a single expression (lhs) - (rhs)
        if "=" in expr_str:
            left, right = expr_str.split("=", 1)
            expr_str = f"({left}) - ({right})"
        return simplify(parse_expr(expr_str))

    def equivalent(self, a: Any, b: Any) -> bool:
        # SymPy simplify returns 0 for equivalent expressions
        return simplify(a - b) == 0


def create_engine(config: dict | None = None):
    parser = LawParser()

    class _Engine:
        def __init__(self, impl):
            self.impl = impl
            self.name = 'Law_Parser'

        def process_task(self, payload: dict) -> dict:
            try:
                action = payload.get('action')
                if action == 'normalize':
                    expr = payload.get('expr', '')
                    return {'ok': True, 'normalized': str(self.impl.normalize(expr))}
                if action == 'equivalent':
                    a = payload.get('a')
                    b = payload.get('b')
                    na = self.impl.normalize(a)
                    nb = self.impl.normalize(b)
                    return {'ok': True, 'equivalent': bool(self.impl.equivalent(na, nb))}
                return {'ok': True, 'msg': 'noop'}
            except Exception as e:
                return {'ok': False, 'error': str(e)}

    return _Engine(parser)
