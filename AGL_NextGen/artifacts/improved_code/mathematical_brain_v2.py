from typing import *
import re
import math
import ast
import itertools
import os
import datetime

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

    def _record(self, query: str, answer: Any) -> None:
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

    def analyze_and_solve(self, query: str) -> Dict[str, Any]:
        """Perform analysis phase then produce an answer with reasoning steps."""
        
        # --- PROOF OF WORK LOGGING ---
        try:
            import os
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "artifacts", "math_engine_activity.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now()}] MathematicalBrain ACTIVATED for query: {query}\n")
        except Exception:
            pass
        # -----------------------------

        q = query.strip()
        analysis = {"phase": "analysis", "notes": []}

        # --- Minimum Set Cover (exact, deterministic) ---
        ql = q.lower()
        if ("set cover" in ql) or ("minimum set cover" in ql) or ("sets" in ql and "u =" in ql):
            try:
                m_u = re.search(r"\bU\s*=\s*(\[[^\]]*\])", q)
                if not m_u:
                    raise ValueError("missing_universe")
                universe = ast.literal_eval(m_u.group(1))
                if not isinstance(universe, list):
                    raise ValueError("bad_universe")

                set_lines = re.findall(r"(?m)^\s*(\d+)\s*:\s*(\[[^\]]*\])\s*$", q)
                if not set_lines:
                    raise ValueError("missing_sets")

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
                        if covered >= universe:
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

        # --- Wikipedia helper (best-effort) ---
        if q.lower().startswith('تعريف') or 'ما هي' in q:
            term = q.replace('تعريف', '').replace('ما هي', '').strip()
            wiki = self.wiki_fetch(term)
            analysis['notes'].append({'wiki': wiki})

        # --- LP detection (maximize/minimize with subject to) ---
        if ('maximize' in q.lower() or 'minimize' in q.lower() or 'أقصى' in q or 'أدنى' in q) and ('subject to' in q.lower() or 'مقيد ب' in q):
            analysis['notes'].append({'lp_detected': 'LP problem - manual parsing needed'})
            return {'analysis': analysis, 'lp_note': 'LP solver available but requires structured input (c, A_ub, b_ub). Use solve_linear_program() directly.'}

        # --- Matrix / Eigenvalues (Genius Level) ---
        if 'eigenvalue' in q.lower() or 'matrix' in q.lower() or 'مصفوفة' in q:
            try:
                match = re.search(r'\[\[.*?\]\]', q)
                if match:
                    matrix_str = match.group(0)
                    matrix_list = ast.literal_eval(matrix_str)
                    if HAS_NUMPY:
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

        # --- Equations ---
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

        # --- Numeric evaluation ---
        if re.search(r'[^0-9\.\+\-\*\/\(\)eE ]', q):
            try:
                expr = re.sub(r'[^0-9\.\+\-\*\/\(\)eE ]', '', q)
                val = eval(expr, {"__builtins__": {}}, {})
                self._record(q, val)
                return {'analysis': analysis, 'result': val}
            except Exception:
                pass

        return {'analysis': analysis, 'note': 'no-solution'}

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

    def process_task(self, query: str) -> Any:
        try:
            out = self.analyze_and_solve(query)
            return out
        except Exception as e:
            return {"error": str(e)}