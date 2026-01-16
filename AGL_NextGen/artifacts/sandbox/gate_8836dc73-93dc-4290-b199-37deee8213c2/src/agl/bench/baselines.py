from __future__ import annotations

import ast
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Tuple


def _insert_implicit_mul(expr: str) -> str:
    # Turn "2x" into "2*x" and ")x" into ")*x".
    s = (expr or "").strip()
    s = re.sub(r"(\d)\s*x\b", r"\1*x", s)
    s = re.sub(r"\)\s*x\b", r")*x", s)
    return s


class _LinearParseError(ValueError):
    pass


def _linear_from_ast(node: ast.AST) -> Tuple[float, float]:
    """Return (a, b) for expression a*x + b."""

    if isinstance(node, ast.Expression):
        return _linear_from_ast(node.body)

    if isinstance(node, ast.Num):  # py<3.8
        return (0.0, float(node.n))

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return (0.0, float(node.value))
        raise _LinearParseError("non-numeric constant")

    if isinstance(node, ast.Name):
        if node.id == "x":
            return (1.0, 0.0)
        raise _LinearParseError("unknown name")

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        a, b = _linear_from_ast(node.operand)
        if isinstance(node.op, ast.USub):
            return (-a, -b)
        return (a, b)

    if isinstance(node, ast.BinOp):
        if isinstance(node.op, (ast.Add, ast.Sub)):
            a1, b1 = _linear_from_ast(node.left)
            a2, b2 = _linear_from_ast(node.right)
            if isinstance(node.op, ast.Sub):
                return (a1 - a2, b1 - b2)
            return (a1 + a2, b1 + b2)

        if isinstance(node.op, ast.Mult):
            a1, b1 = _linear_from_ast(node.left)
            a2, b2 = _linear_from_ast(node.right)
            # (a1*x+b1)*(a2*x+b2) must be linear: at least one side constant
            if a1 != 0.0 and a2 != 0.0:
                raise _LinearParseError("non-linear multiply")
            if a1 == 0.0 and a2 == 0.0:
                return (0.0, b1 * b2)
            if a1 == 0.0:
                return (a2 * b1, b2 * b1)
            return (a1 * b2, b1 * b2)

        if isinstance(node.op, ast.Div):
            a1, b1 = _linear_from_ast(node.left)
            a2, b2 = _linear_from_ast(node.right)
            if a2 != 0.0:
                raise _LinearParseError("division by expression")
            if b2 == 0.0:
                raise _LinearParseError("division by zero")
            return (a1 / b2, b1 / b2)

    raise _LinearParseError("unsupported expression")


def _solve_linear_equation(equation: str) -> float:
    s = _insert_implicit_mul(equation)
    if "=" not in s:
        raise _LinearParseError("not an equation")

    left, right = [p.strip() for p in s.split("=", 1)]

    left_ast = ast.parse(left, mode="eval")
    right_ast = ast.parse(right, mode="eval")

    a1, b1 = _linear_from_ast(left_ast)
    a2, b2 = _linear_from_ast(right_ast)

    a = a1 - a2
    b = b2 - b1
    if a == 0.0:
        raise _LinearParseError("no unique solution")
    return b / a


_AR_CAUSAL = re.compile(
    r"^\s*(?P<c>.+?)\s*(?:يسبب|تسبب|يؤدي\s*إلى|يؤدي\s*الى|يؤدي\s*لـ|يؤدي\s*ل)\s*(?P<e>.+?)\s*$"
)
_EN_CAUSAL = re.compile(r"^\s*(?P<c>.+?)\s*(?:causes|leads\s+to)\s*(?P<e>.+?)\s*$", re.IGNORECASE)


@dataclass
class BaselineAnswer:
    ok: bool
    text: str
    data: Dict[str, Any]


class BaselineEngine:
    """Very simple baselines for measuring *relative* progress.

    Goal: provide a non-LLM, cheap reference point.
    """

    name = "BaselineEngine"

    def answer(self, prompt: str) -> BaselineAnswer:
        p = (prompt or "").strip()

        # Linear equations with x
        if "x" in p and "=" in p:
            try:
                x = _solve_linear_equation(p)
                return BaselineAnswer(ok=True, text=str(x).rstrip("0").rstrip(".") if "." in str(x) else str(x), data={"result": x})
            except Exception as e:
                return BaselineAnswer(ok=False, text="", data={"error": str(e)})

        # Basic arithmetic
        if any(op in p for op in ("+", "-", "*", "/", "(", ")")) and re.fullmatch(r"[0-9\s\+\-\*/\(\)\.]+", p):
            try:
                # Parse-safe arithmetic using AST whitelist.
                node = ast.parse(p, mode="eval")
                val = self._eval_arith(node)
                return BaselineAnswer(ok=True, text=str(val).rstrip("0").rstrip(".") if isinstance(val, float) else str(val), data={"result": val})
            except Exception as e:
                return BaselineAnswer(ok=False, text="", data={"error": str(e)})

        # Numeric extraction from Arabic text
        m = re.search(r"\d+", p)
        if m and ("استخرج" in p or "الرقم" in p or "رقم" in p):
            return BaselineAnswer(ok=True, text=m.group(0), data={"result": int(m.group(0))})

        # Causal extraction
        m = _AR_CAUSAL.match(p) or _EN_CAUSAL.match(p)
        if m:
            c = m.group("c").strip()
            e = m.group("e").strip()
            data = {"edges": [{"cause": c, "effect": e}]}
            return BaselineAnswer(ok=True, text=str(data), data=data)

        # Planner: intentionally generic (often fails keyword-aware evaluator)
        if "خطة" in p or "plan" in p.lower():
            plan = {
                "plan": {
                    "title": "خطة عامة",
                    "steps": [
                        "1) جهّز ما تحتاجه.",
                        "2) نفّذ الخطوات الأساسية.",
                        "3) تحقّق من النتيجة واحفظها.",
                    ],
                },
                "text": "خطة عامة من 3 خطوات",
            }
            return BaselineAnswer(ok=True, text=str(plan), data=plan)

        return BaselineAnswer(ok=True, text="", data={"result": ""})

    def _eval_arith(self, node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return self._eval_arith(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = self._eval_arith(node.operand)
            return -v if isinstance(node.op, ast.USub) else v
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a = self._eval_arith(node.left)
            b = self._eval_arith(node.right)
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                return a * b
            return a / b
        raise ValueError("unsupported arithmetic")


def baseline_ask(prompt: str) -> Dict[str, Any]:
    eng = BaselineEngine()
    start = time.time()
    ans = eng.answer(prompt)
    latency_ms = (time.time() - start) * 1000.0
    out: Dict[str, Any] = {
        "ok": bool(ans.ok),
        "engine": eng.name,
        "text": ans.text,
        "data": ans.data,
        "metrics": {"latency_ms": latency_ms},
    }
    return {"result": out, "latency_ms": latency_ms, "text": ans.text}
