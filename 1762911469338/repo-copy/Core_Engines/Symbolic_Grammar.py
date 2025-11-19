"""Symbolic grammar stub: generate symbolic expressions under unit constraints.

This module provides a tiny grammar example and a units-check helper.
Real grammar generation, parsing, and unit arithmetic should be added later.
"""
from typing import Dict, List, Any


GRAMMAR = {
    "operators": ["+", "-", "*", "/"],
    "functions": ["sin", "cos", "log", "exp", "sqrt"],
}


def generate_from_grammar(vars: List[str], max_depth: int = 2, limit: int = 10):
    """Yield a few example expressions formed from vars using the toy grammar."""
    out = []
    for i, v in enumerate(vars[:limit]):
        out.append(f"1.0*{v}")
        out.append(f"{v} + {v}**2")
        if i % 2 == 0:
            out.append(f"sin({v})")
    return out[:limit]


def units_consistent(expr: str, var_units: Dict[str, str]) -> bool:
    """Very small placeholder: check units by trivial heuristics.

    Real implementation should parse expression and compute unit algebra.
    """
    # placeholder: reject division by zero-like tokens
    if "//" in expr or "**-" in expr:
        return False
    return True
