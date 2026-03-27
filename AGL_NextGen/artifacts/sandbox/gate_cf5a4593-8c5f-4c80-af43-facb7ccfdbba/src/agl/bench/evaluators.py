from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence, Tuple


@dataclass(frozen=True)
class EvalResult:
    ok: bool
    score: float
    reason: str


def _norm_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


_ARABIC_INDIC = str.maketrans(
    {
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
        # Eastern Arabic-Indic (Persian)
        "۰": "0",
        "۱": "1",
        "۲": "2",
        "۳": "3",
        "۴": "4",
        "۵": "5",
        "۶": "6",
        "۷": "7",
        "۸": "8",
        "۹": "9",
    }
)


def _normalize_digits(s: str) -> str:
    return (s or "").translate(_ARABIC_INDIC)


def exact_match(expected: str) -> Callable[[str], EvalResult]:
    exp = _norm_text(expected)

    def _eval(out: str) -> EvalResult:
        got = _norm_text(out)
        ok = got == exp
        return EvalResult(ok=ok, score=1.0 if ok else 0.0, reason="exact_match" if ok else f"mismatch: expected={expected!r}")

    return _eval


def contains_keywords(keywords: list[str], *, min_hits: Optional[int] = None) -> Callable[[str], EvalResult]:
    kws = [k.strip().lower() for k in keywords if k.strip()]
    need = min_hits if min_hits is not None else max(1, len(kws))

    def _eval(out: str) -> EvalResult:
        got = _norm_text(out)
        hits = sum(1 for k in kws if k and k in got)
        ok = hits >= need
        score = 0.0 if not kws else min(1.0, hits / max(1, len(kws)))
        return EvalResult(ok=ok, score=score, reason=f"keywords: {hits}/{len(kws)}")

    return _eval


def hypothesis_with_prediction(
    *, must_contain: Sequence[str], expected_number: float, tol: float = 0.5
) -> Callable[[str], EvalResult]:
    """Proxy for 'epistemic autonomy'.

    Requires:
    - mentions key tokens (e.g. variable names) AND
    - contains a numeric prediction close to expected_number
    """

    kws = [str(k).strip().lower() for k in (must_contain or []) if str(k).strip()]
    exp = float(expected_number)

    def _eval(out: str) -> EvalResult:
        txt = _norm_text(_normalize_digits(out or ""))
        hits = sum(1 for k in kws if k and k in txt)
        if kws and hits < max(1, len(kws)):
            return EvalResult(ok=False, score=0.0, reason=f"missing_tokens {hits}/{len(kws)}")

        # Consider all numeric candidates and pick the closest to expected_number.
        # This avoids penalizing outputs that include a data table or 'x=6' before the prediction.
        matches = _NUM_RE.findall(txt)
        if not matches:
            return EvalResult(ok=False, score=0.0, reason="no_number_found")
        nums = []
        for m in matches:
            try:
                nums.append(float(m))
            except Exception:
                continue
        if not nums:
            return EvalResult(ok=False, score=0.0, reason="parse_number_failed")

        got = min(nums, key=lambda n: abs(n - exp))
        err = abs(got - exp)
        ok = err <= float(tol)
        return EvalResult(ok=ok, score=1.0 if ok else 0.0, reason=f"pred err={err:g}")

    return _eval


def plan_with_fallback(*, min_steps: int = 3, must_include_fallback: bool = True) -> Callable[[str], EvalResult]:
    """Proxy for subgoal generation + strategy change on failure.

    Requires structured steps and an explicit fallback clause like 'إذا فشل' / 'if fails'.
    """

    base = plan_steps(min_steps=min_steps)

    def _eval(out: str) -> EvalResult:
        ev = base(out)
        if not ev.ok:
            return ev
        if not must_include_fallback:
            return ev
        txt = _norm_text(out)
        if ("اذا فشل" in txt) or ("إذا فشل" in out) or ("if fails" in txt) or ("if fail" in txt):
            return EvalResult(ok=True, score=1.0, reason="ok_with_fallback")
        return EvalResult(ok=False, score=0.0, reason="missing_fallback")

    return _eval


def causal_intervention_answer(*, must_contain: Sequence[str]) -> Callable[[str], EvalResult]:
    """Proxy for causal understanding on interventions.

    Requires that the answer contains all key terms (e.g. do(X), effect variable) and an explanation cue.
    """

    kws = [str(k).strip().lower() for k in (must_contain or []) if str(k).strip()]

    def _eval(out: str) -> EvalResult:
        txt = _norm_text(out)
        hits = sum(1 for k in kws if k and k in txt)
        if kws and hits < len(kws):
            return EvalResult(ok=False, score=0.0, reason=f"missing_terms {hits}/{len(kws)}")

        # require a 'because/why' marker
        if ("because" in txt) or ("why" in txt) or ("لأن" in out) or ("سبب" in txt):
            return EvalResult(ok=True, score=1.0, reason="ok")
        return EvalResult(ok=False, score=0.0, reason="missing_explanation")

    return _eval


_NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def numeric_answer(expected: float, *, tol: float = 1e-6) -> Callable[[str], EvalResult]:
    exp = float(expected)

    def _eval(out: str) -> EvalResult:
        txt = _normalize_digits(out or "")
        m = _NUM_RE.search(txt)
        if not m:
            return EvalResult(ok=False, score=0.0, reason="no_number_found")
        try:
            got = float(m.group(0))
        except Exception:
            return EvalResult(ok=False, score=0.0, reason="parse_number_failed")
        err = abs(got - exp)
        ok = err <= float(tol)
        # soft score
        score = 1.0 if ok else max(0.0, 1.0 - (err / max(1.0, abs(exp))))
        return EvalResult(ok=ok, score=score, reason=f"numeric err={err:g}")

    return _eval


def causal_edges(expected: Sequence[Tuple[str, str]], *, min_matches: int = 1) -> Callable[[str], EvalResult]:
    """Score outputs from CausalGraphEngine.

    The engine output is a dict with an 'edges' list. In the bench runner we store
    the engine output as text, so we parse it back using JSON or Python literal.
    """

    exp_pairs = [(str(c).strip(), str(e).strip()) for (c, e) in expected]
    need = max(1, int(min_matches))

    def _try_parse(text: str) -> Any:
        t = (text or "").strip()
        if not t:
            return None
        try:
            return json.loads(t)
        except Exception:
            pass
        try:
            return ast.literal_eval(t)
        except Exception:
            return None

    def _eval(out: str) -> EvalResult:
        obj = _try_parse(out)
        edges = []
        if isinstance(obj, dict) and isinstance(obj.get("edges"), list):
            edges = [e for e in obj.get("edges", []) if isinstance(e, dict)]

        hits = 0
        for want_cause, want_effect in exp_pairs:
            found = False
            for e in edges:
                cause = str(e.get("cause", "")).strip()
                effect = str(e.get("effect", "")).strip()
                if cause == want_cause and effect == want_effect:
                    found = True
                    break
            if found:
                hits += 1

        ok = hits >= need
        return EvalResult(ok=ok, score=1.0 if ok else 0.0, reason=f"causal_edges hits={hits}/{len(exp_pairs)}")

    return _eval


def math_solution_with_steps(expected: float, *, tol: float = 1e-6, min_steps: int = 2) -> Callable[[str], EvalResult]:
    """Evaluate MathematicalBrain structured outputs for subgoal/plan-like step generation.

    MathematicalBrain returns dicts like:
      {'analysis': {...}, 'solution': {'status':'ok','solution':'5','steps':[...]} }
    We parse the text back into a dict and check:
      - final solution numeric correctness
      - number of steps >= min_steps
    """

    exp = float(expected)
    need_steps = max(0, int(min_steps))

    def _try_parse(text: str) -> Any:
        t = (text or "").strip()
        if not t:
            return None
        try:
            return json.loads(t)
        except Exception:
            pass
        try:
            return ast.literal_eval(t)
        except Exception:
            return None

    def _eval(out: str) -> EvalResult:
        obj = _try_parse(out)
        if not isinstance(obj, dict):
            return EvalResult(ok=False, score=0.0, reason="not_structured_output")

        sol_block = obj.get("solution")
        steps = []
        sol_text = None

        if isinstance(sol_block, dict):
            sol_text = sol_block.get("solution")
            steps = sol_block.get("steps") if isinstance(sol_block.get("steps"), list) else []
        elif "result" in obj:
            sol_text = obj.get("result")

        if sol_text is None:
            return EvalResult(ok=False, score=0.0, reason="missing_solution")

        # numeric check
        txt = _normalize_digits(str(sol_text))
        m = _NUM_RE.search(txt)
        if not m:
            return EvalResult(ok=False, score=0.0, reason="solution_not_numeric")
        try:
            got = float(m.group(0))
        except Exception:
            return EvalResult(ok=False, score=0.0, reason="parse_solution_failed")

        err = abs(got - exp)
        ok_num = err <= float(tol)
        ok_steps = (len(steps) >= need_steps)
        ok = ok_num and ok_steps

        if not ok:
            return EvalResult(
                ok=False,
                score=0.0,
                reason=f"num_ok={ok_num} err={err:g} steps={len(steps)}/{need_steps}",
            )
        return EvalResult(ok=True, score=1.0, reason=f"ok steps={len(steps)}")

    return _eval


def plan_steps(*, min_steps: int = 3) -> Callable[[str], EvalResult]:
    """Evaluate a plan-like output containing a list of steps.

    Works with MicroPlanner output:
      {'plan': {'title': '...', 'steps': ['1) ...', '2) ...', ...}, 'text': '...'}
    """

    need = max(1, int(min_steps))

    def _try_parse(text: str) -> Any:
        t = (text or "").strip()
        if not t:
            return None
        try:
            return json.loads(t)
        except Exception:
            pass
        try:
            return ast.literal_eval(t)
        except Exception:
            return None

    def _eval(out: str) -> EvalResult:
        obj = _try_parse(out)
        if not isinstance(obj, dict):
            return EvalResult(ok=False, score=0.0, reason="not_structured_output")

        plan = obj.get("plan") if isinstance(obj.get("plan"), dict) else None
        steps = plan.get("steps") if isinstance(plan, dict) and isinstance(plan.get("steps"), list) else []

        if len(steps) < need:
            return EvalResult(ok=False, score=0.0, reason=f"too_few_steps {len(steps)}/{need}")

        # basic numbering check for first N steps: '1)' / '2)' ...
        ok_numbering = True
        for i in range(need):
            prefix = f"{i+1})"
            if not str(steps[i]).lstrip().startswith(prefix):
                ok_numbering = False
                break

        if not ok_numbering:
            return EvalResult(ok=False, score=0.0, reason="bad_step_numbering")

        return EvalResult(ok=True, score=1.0, reason=f"ok steps={len(steps)}")

    return _eval


def plan_steps_with_keywords(
    keywords: Sequence[str], *, min_steps: int = 3, min_keyword_hits: int = 1
) -> Callable[[str], EvalResult]:
    """Plan evaluator that requires both structure and prompt-relevant content.

    This avoids 'template plans' that contain numbered steps but ignore the task.
    """

    base = plan_steps(min_steps=min_steps)
    kws = [k.strip().lower() for k in (keywords or []) if str(k).strip()]
    need_hits = max(0, int(min_keyword_hits))

    def _eval(out: str) -> EvalResult:
        r = base(out)
        if not r.ok:
            return r

        if not kws or need_hits == 0:
            return r

        text = _norm_text(out)
        hits = sum(1 for k in kws if k and k in text)
        if hits < need_hits:
            return EvalResult(ok=False, score=0.0, reason=f"missing_keywords hits={hits}/{len(kws)}")
        return EvalResult(ok=True, score=1.0, reason=f"ok keywords={hits}/{len(kws)}")

    return _eval


def plan_steps_keywords_in_steps(
    keywords: Sequence[str], *, min_steps: int = 3, min_keyword_hits: int = 1
) -> Callable[[str], EvalResult]:
    """Stricter planner evaluator: keywords must appear inside step texts.

    This avoids passing simply because the plan title echoes the prompt.
    """

    need = max(1, int(min_steps))
    kws = [k.strip().lower() for k in (keywords or []) if str(k).strip()]
    need_hits = max(0, int(min_keyword_hits))

    def _try_parse(text: str) -> Any:
        t = (text or "").strip()
        if not t:
            return None
        try:
            return json.loads(t)
        except Exception:
            pass
        try:
            return ast.literal_eval(t)
        except Exception:
            return None

    def _eval(out: str) -> EvalResult:
        obj = _try_parse(out)
        if not isinstance(obj, dict):
            return EvalResult(ok=False, score=0.0, reason="not_structured_output")

        plan = obj.get("plan") if isinstance(obj.get("plan"), dict) else None
        steps = plan.get("steps") if isinstance(plan, dict) and isinstance(plan.get("steps"), list) else []
        if len(steps) < need:
            return EvalResult(ok=False, score=0.0, reason=f"too_few_steps {len(steps)}/{need}")

        # numbering check
        for i in range(need):
            prefix = f"{i+1})"
            if not str(steps[i]).lstrip().startswith(prefix):
                return EvalResult(ok=False, score=0.0, reason="bad_numbering")

        if not kws or need_hits == 0:
            return EvalResult(ok=True, score=1.0, reason="ok")

        step_text = _norm_text(" ".join(str(s) for s in steps))
        hits = sum(1 for k in kws if k and k in step_text)
        if hits < need_hits:
            return EvalResult(ok=False, score=0.0, reason=f"missing_keywords_in_steps hits={hits}/{len(kws)}")
        return EvalResult(ok=True, score=1.0, reason=f"ok keywords_in_steps={hits}/{len(kws)}")

    return _eval
