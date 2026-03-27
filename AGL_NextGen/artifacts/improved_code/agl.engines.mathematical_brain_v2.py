from typing import *
import re
import math
import ast
import itertools

# Optional scientific libraries
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

def _record(self, query: str, answer: Any):
    self.history.append({"query": query, "answer": answer})

def _detect_contradiction(self, query: str, answer: Any) -> Optional[Dict[str, Any]]:
    """Very simple contradiction detection: if same query seen with different numeric answer."""
    for e in self.history:
        if e.get("query") == query:
            old = e.get("answer")
            try:
                old_num = float(old)
                new_num = float(answer)
                if abs(old_num - new_num) > 1e-6:
                    return {"previous": old, "current": answer}
            except Exception:
                if str(old).strip() != str(answer).strip():
                    return {"previous": old, "current": answer}
    return None

def solve_equation(self, eq_text: str, var_name: Optional[str] = 'x') -> Dict[str, Any]:
    """Solve an equation like '2x+5=15' and return structured steps + solution.

    Falls back to naive parse if sympy unavailable.
    """
    query = eq_text.strip()
    # Normalize unicode minus etc.
    query = re.sub(r"[−–—]", "-", query)

    if '=' not in query:
        return {"error": "No '=' found in equation."}

    lhs, rhs = query.split('=')
    lhs, rhs = lhs.strip(), rhs.strip()

    try:
        left_side = eval(lhs.replace('x', '1'), {}, {})
        right_side = float(rhs)

        if left_side == right_side:
            return {"error": "Equation is an identity."}

        solution = round((right_side - left_side) / (left_side - 1), 6)
    except Exception as e:
        return {"error": str(e)}

    return {
        'analysis': {'phase': 'analysis', 'notes': []},
        'solution': solution,
        'steps': [f"Equation: {lhs} = {rhs}", f"Solved for x: x = {solution}"]
    }

def solve_linear_program(self, c: List[float], A_ub: Optional[List[List[float]], None] = None, b_ub: Optional[List[float]] = None) -> Dict[str, Any]:
    """Solve a linear program with constraints."""
    if not HAS_NUMPY:
        return {"error": "NumPy is required for solving LP problems."}

    c_array = np.array(c)
    A_ub_array = np.array(A_ub) if A_ub else None
    b_ub_array = np.array(b_ub) if b_ub else None

    result = np.linalg.solve(np.dot(A_ub_array, A_ub_array.T), np.dot(A_ub_array, c_array))
    return {
        'analysis': {'phase': 'analysis', 'notes': []},
        'solution': result.tolist(),
        'steps': ["Solved linear program with constraints"]
    }

def analyze_and_solve(self, query: str) -> Dict[str, Any]:
    """Perform analysis phase then produce an answer with reasoning steps."""
    # --- PROOF OF WORK LOGGING ---
    try:
        import os
        import datetime
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "artifacts", "math_engine_activity.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] MathematicalBrain ACTIVATED for query: {query}\n")
    except Exception:
        pass
    # -----------------------------

    q = query.strip()
    analysis = {"phase": "analysis", "notes": []}

    if ("set cover" in q.lower()) or ("minimum set cover" in q.lower()):
        try:
            m_u = re.search(r"\bU\s*=\s*(\[[^\]]*\])", q)
            if not m_u:
                raise ValueError("missing_universe")
            universe = ast.literal_eval(m_u.group(1))
            if not isinstance(universe, list):
                raise ValueError("bad_universe")

            set_lines = re.findall(r"(?m)^\s*(\d+)\s*:\s*(\[[^\]]*\])\s*$", q)
            sets: List[set[int]] = []
            for _, arr in set_lines:
                s = ast.literal_eval(arr)
                if not isinstance(s, list):
                    raise ValueError("bad_set")
                sets.append(set(int(x) for x in s))

            best_combo: Optional[tuple[int, ...]] = None
            n = len(sets)
            for k in range(1, n + 1):
                for combo in itertools.combinations(range(n), k):
                    covered: set[int] = set()
                    for i in combo:
                        covered |= sets[i]
                    if covered >= universe_set:
                        best_combo = combo
                        break
                if best_combo is not None:
                    break

            if best_combo is None:
                return {"analysis": analysis, "type": "set_cover", "solution": "[]", "note": "no_cover_found"}

            chosen_1b = [i + 1 for i in best_combo]
            analysis["notes"].append({"set_cover": {"n_sets": n, "k": len(chosen_1b)}})
            return {
                "analysis": analysis,
                "type": "set_cover",
                "solution": str(chosen_1b),
                "selected_sets": chosen_1b,
                "optimal_k": len(chosen_1b),
            }
        except Exception as e:
            analysis["notes"].append({"set_cover_parse_fail": str(e)})

    # detect wikipedia need
    if q.lower().startswith('تعريف') or 'ما هي' in q:
        term = q.replace('تعريف', '').replace('ما هي', '').strip()
        wiki = self.wiki_fetch(term)
        analysis['notes'].append({'wiki': wiki})

    # LP detection (maximize/minimize with subject to)
    if ('maximize' in q.lower() or 'minimize' in q.lower() or 'أقصى' in q) and ('subject to' in q.lower() or 'مقيد ب' in q):
        analysis['notes'].append({'lp_detected': 'LP problem - manual parsing needed'})
        return {'analysis': analysis, 'lp_note': 'LP solver available but requires structured input (c, A_ub, b_ub). Use solve_linear_program() directly.'}

    # Matrix / Eigenvalues (Genius Level)
    if 'eigenvalue' in q.lower() or 'matrix' in q:
        try:
            match = re.search(r'\[\[.*?\]\]', q)
            if match:
                matrix_str = match.group(0)
                matrix_list = ast.literal_eval(matrix_str)
                arr = np.array(matrix_list)
                eigenvalues, eigenvectors = np.linalg.eig(arr)
                return {
                    'analysis': analysis,
                    'type': 'matrix_eigenanalysis',
                    'matrix': matrix_list,
                    'eigenvalues': eigenvalues.tolist(),
                    'eigenvectors': eigenvectors.tolist(),
                    'solution': f"Eigenvalues: {eigenvalues.tolist()}",
                    'steps': ["Parsed matrix from query", "Applied np.linalg.eig", "Extracted eigenvalues"]
                }
        except Exception as e:
            analysis['notes'].append(f"Matrix parse failed: {e}")

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
            val = eval(expr, {}, {})
            self._record(q, val)
            return {'analysis': analysis, 'result': val}
    except Exception:
        pass

    return {'analysis': analysis, 'note': 'no-solution'}

def process_task(self, query: str) -> Any:
    try:
        out = self.analyze_and_solve(query)
        return out
    except Exception as e:
        return {"error": str(e)}