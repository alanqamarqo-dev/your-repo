"""High-precision MathematicalBrain implementation.

Uses sympy when available for symbolic solving, scipy for LP, and
graceful fallbacks if libraries are missing. Also provides:
- history tracking, basic contradiction detection and auto-fix,
- step-by-step reasoning for linear equations,
- a lightweight wikipedia fetch helper (best-effort).
"""

from typing import Any, Dict, List, Optional
import re
import math

# Optional scientific libraries
try:
    import sympy as sp
    HAS_SYMPY = True
except Exception:
    sp = None
    HAS_SYMPY = False

try:
    from scipy.optimize import linprog
    HAS_SCIPY = True
except Exception:
    linprog = None
    HAS_SCIPY = False

try:
    import numpy as np
    HAS_NUMPY = True
except Exception:
    np = None
    HAS_NUMPY = False

try:
    import wikipediaapi # type: ignore
    HAS_WIKIAPI = True
except Exception:
    wikipediaapi = None
    HAS_WIKIAPI = False


class MathematicalBrain:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []  # list of {query, answer}

    # ------------------ Helpers ------------------
    def _record(self, query: str, answer: Any):
        self.history.append({"query": query, "answer": answer})

    def _detect_contradiction(self, query: str, answer: Any) -> Optional[Dict[str, Any]]:
        """Very simple contradiction detection: if same query seen with different numeric answer."""
        for e in self.history:
            if e.get("query") == query:
                old = e.get("answer")
                # try numeric compare
                try:
                    old_num = float(old)
                    new_num = float(answer)
                    if abs(old_num - new_num) > 1e-6:
                        return {"previous": old, "current": answer}
                except Exception:
                    if str(old).strip() != str(answer).strip():
                        return {"previous": old, "current": answer}
        return None

    # ------------------ Equation solving ------------------
    def solve_equation(self, eq_text: str, var_name: str = "x") -> Dict[str, Any]:
        """Solve an equation like '2x+5=15' and return structured steps + solution.

        Falls back to naive parse if sympy unavailable.
        """
        query = eq_text.strip()
        # Normalize unicode minus etc.
        query = re.sub(r"[−–—]", "-", query)

        if '=' not in query:
            return {"error": "No '=' found in equation."}

        lhs, rhs = query.split('=', 1)

        # Auto-detect variable name if not present in provided var_name
        if var_name is None or var_name == '' or var_name not in query:
            mvar = re.search(r"[a-zA-Z]", query)
            if mvar:
                var_name = mvar.group(0)
            else:
                var_name = 'x'

        # Try sympy first
        if HAS_SYMPY:
            try:
                symbol = sp.symbols(var_name)
                expr_lhs = sp.sympify(lhs)
                expr_rhs = sp.sympify(rhs)
                eq = sp.Eq(expr_lhs, expr_rhs)
                sol = sp.solve(eq, symbol)
                steps = [f"Parsed: {sp.srepr(eq)}"]
                # produce simple algebraic manipulation steps
                try:
                    # isolate symbol (sympy has solve but we provide simple step)
                    steps.append(f"Isolate {var_name}: {sp.solve(eq, symbol)}")
                except Exception:
                    pass
                result = sol[0] if isinstance(sol, (list, tuple)) and sol else sol
                out = {"status": "ok", "solution": str(result), "steps": steps}
                self._record(query, str(result))
                return out
            except Exception as e:
                # fall through to simple parser
                pass

        # Fallback: try naive linear parse
        try:
            # Keep only digits, var, ops on each side (EXCLUDE 'e' to prevent math constant issues)
            clean = lambda s: re.sub(r'[^0-9\+\-\*/\.%s()]' % var_name, '', s)
            L = clean(lhs)
            R = clean(rhs)
            # attempt to convert to ax+b=c
            # find coefficient of var
            m = re.search(r'(-?\d*\.?\d*)' + re.escape(var_name), L)
            if m:
                coeff = m.group(1)
                if coeff in ['', '+']:
                    a = 1.0
                elif coeff == '-':
                    a = -1.0
                else:
                    a = float(coeff)
                # remove var term
                rest = re.sub(r'(-?\d*\.?\d*)' + re.escape(var_name), '', L)
                # Safe eval with empty namespace to prevent 'e' or other symbols
                b = float(eval(rest, {"__builtins__": {}}, {})) if rest.strip() else 0.0
                c = float(eval(R, {"__builtins__": {}}, {})) if R.strip() else 0.0
                if a == 0:
                    return {"error": "Coefficient zero"}
                x = (c - b) / a
                if abs(x - round(x)) < 1e-9:
                    x = int(round(x))
                self._record(query, x)
                return {"status": "ok", "solution": str(x), "steps": [f"a={a}", f"b={b}", f"c={c}", f"x=(c-b)/a={x}"]}
            else:
                return {"error": "Variable not found"}
        except Exception as e:
            return {"error": str(e)}

    # Backwards-compatible wrapper
    def solve_linear_equation(self, lhs: str, rhs: str, var: str = 'x'):
        eq = f"{lhs}={rhs}"
        return self.solve_equation(eq, var_name=var)

    # ------------------ Linear programming (LP) ------------------
    def solve_linear_program(self, c, A_ub=None, b_ub=None, A_eq=None, b_eq=None, bounds=None):
        """Solve a linear program minimize c^T x subject to constraints.

        Expects inputs as Python lists or numpy arrays. Returns dict with solution.
        """
        if not HAS_SCIPY:
            return {"error": "scipy not available"}
        try:
            res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
            if res.success:
                return {"status": "ok", "x": res.x.tolist(), "fun": float(res.fun)}
            else:
                return {"status": "fail", "message": res.message}
        except Exception as e:
            return {"error": str(e)}

    # ------------------ Wikipedia helper (best-effort) ------------------
    def wiki_fetch(self, term: str, lang: str = 'ar') -> Dict[str, Any]:
        if HAS_WIKIAPI:
            try:
                wiki = wikipediaapi.Wikipedia(lang)
                page = wiki.page(term)
                if page.exists():
                    return {"status": "ok", "title": page.title, "summary": page.summary[:1000]}
                return {"status": "not_found"}
            except Exception as e:
                return {"error": str(e)}
        # graceful fallback: try to use requests to MediaWiki API (may fail if offline)
        try:
            import requests
            url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{term}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                j = r.json()
                return {"status": "ok", "title": j.get('title'), "summary": j.get('extract')}
            return {"status": "failed", "code": r.status_code}
        except Exception as e:
            return {"error": "no-wiki-backend", "detail": str(e)}

    # ------------------ High-level processing ------------------
    def analyze_and_solve(self, query: str) -> Dict[str, Any]:
        """Perform analysis phase then produce an answer with reasoning steps."""
        q = query.strip()
        analysis = {"phase": "analysis", "notes": []}

        # detect wikipedia need
        if q.lower().startswith('تعريف') or 'ما هي' in q:
            term = q.replace('تعريف', '').replace('ما هي', '').strip()
            wiki = self.wiki_fetch(term)
            analysis['notes'].append({'wiki': wiki})

        # LP detection (maximize/minimize with subject to)
        if ('maximize' in q.lower() or 'minimize' in q.lower() or 'أقصى' in q or 'أدنى' in q) and ('subject to' in q.lower() or 'مقيد ب' in q):
            analysis['notes'].append({'lp_detected': 'LP problem - manual parsing needed'})
            return {'analysis': analysis, 'lp_note': 'LP solver available but requires structured input (c, A_ub, b_ub). Use solve_linear_program() directly.'}

        # equations
        if '=' in q:
            sol = self.solve_equation(q)
            contradiction = None
            if sol.get('status') == 'ok':
                contradiction = self._detect_contradiction(q, sol.get('solution'))
                if contradiction:
                    # try higher precision re-eval with sympy if available
                    if HAS_SYMPY:
                        try:
                            s = self.solve_equation(q)
                            sol['auto_fixed'] = s
                            self._record(q, s.get('solution'))
                        except Exception:
                            pass
            return {'analysis': analysis, 'solution': sol, 'contradiction': contradiction}

        # otherwise, try numeric evaluation
        try:
            expr = re.sub(r'[^0-9\.\+\-\*\/\(\)eE ]', '', q)
            if expr.strip():
                # Safe eval without builtins
                val = eval(expr, {"__builtins__": {}}, {})
                self._record(q, val)
                return {'analysis': analysis, 'result': val}
        except Exception:
            pass

        return {'analysis': analysis, 'note': 'no-solution'}

    # Compatibility: process_task used by server
    def process_task(self, query: str) -> Any:
        try:
            out = self.analyze_and_solve(query)
            return out
        except Exception as e:
            return {"error": str(e)}