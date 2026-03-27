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


def json_field_truthy(field: str) -> Callable[[str], EvalResult]:
    """Evaluate structured outputs by requiring a top-level field to be truthy.

    The bench runner passes JSON for tasks tagged with 'structured'.
    This is useful for smoke tests of engines that return dicts.
    """

    key = str(field)

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
            return EvalResult(ok=False, score=0.0, reason="not_a_dict")
        ok = bool(obj.get(key))
        return EvalResult(ok=ok, score=1.0 if ok else 0.0, reason=f"field_truthy {key}={obj.get(key)!r}")

    return _eval


def json_field_equals(field: str, expected: Any) -> Callable[[str], EvalResult]:
    """Evaluate structured outputs by requiring a top-level field to equal expected."""

    key = str(field)
    want = expected

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
            return EvalResult(ok=False, score=0.0, reason="not_a_dict")
        got = obj.get(key)
        ok = got == want
        return EvalResult(ok=ok, score=1.0 if ok else 0.0, reason=f"field_equals {key} got={got!r} want={want!r}")

    return _eval


def holo_cache_speedup(
    *,
    min_hit_delta: int = 1,
    min_speedup_ratio: float = 1.05,
) -> Callable[[str], EvalResult]:
    """Evaluate the holographic LLM cache probe.

    Expects a structured result dict containing:
      result.metrics.first_ms
      result.metrics.second_ms
      result.metrics.hit_delta
      result.metrics.holo_enabled

    We require within the same probe call:
      - holographic is enabled
      - second call increments holographic_hits (hit_delta>=min_hit_delta)
      - second_ms is faster than first_ms by min_speedup_ratio
    """

    need_hits = max(0, int(min_hit_delta))
    need_ratio = float(min_speedup_ratio)

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
            return EvalResult(ok=False, score=0.0, reason="not_a_dict")

        metrics = None
        if isinstance(obj.get("metrics"), dict):
            metrics = obj.get("metrics")
        elif isinstance(obj.get("result"), dict) and isinstance(obj["result"].get("metrics"), dict):
            metrics = obj["result"].get("metrics")

        if not isinstance(metrics, dict):
            return EvalResult(ok=False, score=0.0, reason="missing_metrics")

        holo_enabled = bool(metrics.get("holo_enabled"))
        try:
            first_ms = float(metrics.get("first_ms"))
            second_ms = float(metrics.get("second_ms"))
        except Exception:
            return EvalResult(ok=False, score=0.0, reason="missing_first_second_ms")

        try:
            hit_delta = int(metrics.get("hit_delta") or 0)
        except Exception:
            hit_delta = 0

        if not holo_enabled:
            return EvalResult(ok=False, score=0.0, reason="holo_not_enabled")

        # Guard against division by zero
        if first_ms <= 0:
            return EvalResult(ok=False, score=0.0, reason="invalid_first_ms")

        speedup = first_ms / max(1e-9, second_ms)
        ok_hits = hit_delta >= need_hits
        ok_speed = speedup >= need_ratio
        ok = ok_hits and ok_speed
        score = 1.0 if ok else max(0.0, min(1.0, (speedup / max(1e-9, need_ratio))))
        return EvalResult(ok=ok, score=score, reason=f"holo_cache speedup={speedup:.2f}x hits={hit_delta} need_hits={need_hits}")

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


def plan_with_fallback_keywords_in_steps(
    keywords: Sequence[str], *, min_steps: int = 3, min_keyword_hits: int = 1
) -> Callable[[str], EvalResult]:
    """Stricter subgoal evaluator.

    Requires:
      - structured numbered steps
      - required keywords inside step texts
      - an explicit fallback marker (اذا فشل/إذا فشل/if fails)

    Note: the runner passes JSON for 'structured' tasks, so we parse it.
    """

    base = plan_steps_keywords_in_steps(keywords, min_steps=min_steps, min_keyword_hits=min_keyword_hits)

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
        r = base(out)
        if not r.ok:
            return r

        obj = _try_parse(out)
        if not isinstance(obj, dict):
            return EvalResult(ok=False, score=0.0, reason="not_structured_output")

        plan = obj.get("plan") if isinstance(obj.get("plan"), dict) else None
        steps = plan.get("steps") if isinstance(plan, dict) and isinstance(plan.get("steps"), list) else []
        step_text = _norm_text(" ".join(str(s) for s in steps))

        if ("اذا فشل" in step_text) or ("إذا فشل" in " ".join(str(s) for s in steps)) or ("if fails" in step_text) or ("if fail" in step_text):
            return EvalResult(ok=True, score=1.0, reason="ok_with_fallback_and_keywords")
        return EvalResult(ok=False, score=0.0, reason="missing_fallback")

    return _eval


def causal_intervention_numeric(
    *, must_contain: Sequence[str], expected_number: float, tol: float = 0.5
) -> Callable[[str], EvalResult]:
    """Harder causal proxy: require do-terms + explanation cue + numeric prediction.

    We parse plain text only. This intentionally resists 'template' answers by
    requiring a numeric value near expected_number.
    """

    kws = [str(k).strip().lower() for k in (must_contain or []) if str(k).strip()]
    exp = float(expected_number)

    def _eval(out: str) -> EvalResult:
        txt_raw = out or ""
        txt = _norm_text(_normalize_digits(txt_raw))

        # must contain key terms
        hits = sum(1 for k in kws if k and k in txt)
        if kws and hits < len(kws):
            return EvalResult(ok=False, score=0.0, reason=f"missing_terms {hits}/{len(kws)}")

        # require explanation marker
        if not (("because" in txt) or ("why" in txt) or ("لأن" in txt_raw) or ("سبب" in txt) or ("لانه" in txt)):
            return EvalResult(ok=False, score=0.0, reason="missing_explanation")

        # numeric prediction
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
