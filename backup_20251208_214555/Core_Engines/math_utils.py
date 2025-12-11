"""High-precision math utilities used across engines.

This module provides safe expression evaluation using Python's
`fractions.Fraction` for exact rational arithmetic and falls back to
`decimal.Decimal` or `sympy` if available for symbolic/exact work.

APIs:
- evaluate_expression(expr_str): safely evaluate arithmetic expressions
  returning either Fraction or Decimal/float depending on available libs.
- solve_linear_equation(lhs_str, rhs_str): solve ax + b = c for x using
  exact rational arithmetic when possible.
"""
from __future__ import annotations

import ast
import operator as _operator
from fractions import Fraction
from decimal import Decimal, getcontext
from typing import Union, Tuple

# try to use sympy for symbolic/exact math if installed
try:
    import sympy as _sympy  # type: ignore
    _HAS_SYMPY = True
except Exception:
    _HAS_SYMPY = False

# increase decimal precision globally (can be tuned)
getcontext().prec = 50


_SAFE_OPERATORS = {
    ast.Add: _operator.add,
    ast.Sub: _operator.sub,
    ast.Mult: _operator.mul,
    ast.Div: _operator.truediv,
    ast.Pow: _operator.pow,
    ast.USub: _operator.neg,
    ast.UAdd: _operator.pos,
}


def _eval_node(node) -> Union[Fraction, Decimal, int]:
    if isinstance(node, ast.Num):
        # ast.Num for Python <3.8, numeric literal
        return Fraction(node.n)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return Fraction(node.value)
        raise ValueError("Unsupported constant type")
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op = type(node.op)
        if op in _SAFE_OPERATORS:
            func = _SAFE_OPERATORS[op]
            # operate using Fraction for exactness
            return Fraction(func(left, right))
        raise ValueError(f"Unsupported operator: {op}")
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op = type(node.op)
        if op in _SAFE_OPERATORS:
            return Fraction(_SAFE_OPERATORS[op](operand))
        raise ValueError(f"Unsupported unary operator: {op}")
    if isinstance(node, ast.Expr):
        return _eval_node(node.value)
    if isinstance(node, ast.Paren):
        return _eval_node(node.value)
    raise ValueError(f"Unsupported AST node: {type(node)}")


def evaluate_expression(expr: str) -> Union[Fraction, Decimal, float]:
    """Safely evaluate an arithmetic expression and return exact Fraction
    when possible. Supports + - * / ** and parentheses. If sympy is
    available, prefer sympy.Rational for exact results and symbolics.
    """
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty expression")

    # try sympy first for robustness
    if _HAS_SYMPY:
        try:
            s = _sympy.sympify(expr)
            # try to rationalize if numeric
            if s.is_Number:
                return _sympy.Rational(s)
            return s
        except Exception:
            pass

    # parse AST and evaluate using Fraction
    try:
        node = ast.parse(expr, mode='eval')
        val = _eval_node(node.body)
        return val
    except Exception:
        # last-resort: use Decimal with limited safety
        try:
            # remove any unsafe chars
            clean = ''.join(ch for ch in expr if ch.isdigit() or ch in '+-*/().eE')
            return Decimal(clean)
        except Exception as e:
            raise ValueError(f"Could not evaluate expression: {e}")


def solve_linear_equation(lhs: str, rhs: str, var: str = 'x') -> Tuple[Union[Fraction, Decimal, float], str]:
    """Solve equation of form ax + b = c for variable `var`.

    Returns (solution, representation_string).
    Uses sympy if available for robustness; otherwise uses Fraction.
    """
    if _HAS_SYMPY:
        try:
            sym_var = _sympy.symbols(var)
            sym_lhs = _sympy.sympify(lhs)
            sym_rhs = _sympy.sympify(rhs)
            sol = _sympy.solve(_sympy.Eq(sym_lhs, sym_rhs), sym_var)
            if sol:
                return sol[0], str(sol[0])
        except Exception:
            pass

    # fallback: attempt to extract coefficient and constants using Fractions
    # sanitize strings to keep digits, var, +-*/().
    import re

    def keep(s):
        return re.sub(r'[^0-9\.%s\+\-\*\/\(\) ]' % var, '', s)

    lhs_c = keep(lhs)
    rhs_c = keep(rhs)

    # find coefficient of var in lhs
    m = re.search(r'([+-]?\d*\.?\d*)%s' % var, lhs_c)
    if m:
        coeff_str = m.group(1)
        if coeff_str in ('', '+'):
            a = Fraction(1)
        elif coeff_str == '-':
            a = Fraction(-1)
        else:
            a = Fraction(coeff_str)
    else:
        raise ValueError('Variable not found')

    # compute constant terms
    left_rest = re.sub(r'([+-]?\d*\.?\d*)%s' % var, '', lhs_c)
    left_rest = left_rest.strip()
    b = Fraction(0)
    if left_rest:
        try:
            b = evaluate_expression(left_rest)
        except Exception:
            b = Fraction(0)

    c = evaluate_expression(rhs_c)

    # ensure Fraction types
    if not isinstance(a, Fraction):
        a = Fraction(a)
    if not isinstance(b, Fraction):
        b = Fraction(b)
    if not isinstance(c, Fraction):
        c = Fraction(c)

    if a == 0:
        raise ZeroDivisionError('Coefficient is zero')

    sol = (c - b) / a
    return sol, f"{var} = {sol}"
