from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from .evaluators import (
    EvalResult,
    numeric_answer,
    causal_edges,
    math_solution_with_steps,
    plan_steps,
    plan_steps_with_keywords,
    plan_steps_keywords_in_steps,
)


@dataclass(frozen=True)
class BenchTask:
    id: str
    prompt: str
    evaluator: Callable[[str], EvalResult]
    tags: List[str]


def deterministic_tasks() -> List[BenchTask]:
    """Deterministic tasks so scoring is truly measurable.

    These are intentionally simple. The purpose is to validate:
      - stability (repeatability)
      - speed
      - exactness / correctness

    You can extend this list later.
    """

    return [
        BenchTask(
            id="math.add.1",
            prompt="17+25",
            evaluator=numeric_answer(42, tol=0.0),
            tags=["math", "exact"],
        ),
        BenchTask(
            id="math.mul.1",
            prompt="7*8",
            evaluator=numeric_answer(56, tol=0.0),
            tags=["math", "exact"],
        ),
        BenchTask(
            id="math.eq.1",
            prompt="2x+5=15",
            evaluator=numeric_answer(5, tol=0.0),
            tags=["math", "exact"],
        ),
        BenchTask(
            id="text.extract.1",
            prompt="استخرج الرقم من النص التالي وأعده فقط: 'الكود هو 9057'.",
            evaluator=numeric_answer(9057, tol=0.0),
            tags=["text", "exact"],
        ),
        BenchTask(
            id="math.eval.1",
            prompt="(12/3)+4",
            evaluator=numeric_answer(8, tol=0.0),
            tags=["math", "exact"],
        ),
    ]


def deterministic_holdout_tasks() -> List[BenchTask]:
    """Holdout variants for deterministic suite (unseen prompts)."""

    return [
        BenchTask(
            id="holdout.math.add.1",
            prompt="19+23",
            evaluator=numeric_answer(42, tol=0.0),
            tags=["math", "exact", "holdout"],
        ),
        BenchTask(
            id="holdout.math.mul.1",
            prompt="9*6",
            evaluator=numeric_answer(54, tol=0.0),
            tags=["math", "exact", "holdout"],
        ),
        BenchTask(
            id="holdout.math.eq.1",
            prompt="4x-8=12",
            evaluator=numeric_answer(5, tol=0.0),
            tags=["math", "exact", "holdout"],
        ),
        BenchTask(
            id="holdout.text.extract.1",
            prompt="استخرج الرقم من النص التالي وأعده فقط: 'رقم الطلب: 9057'.",
            evaluator=numeric_answer(9057, tol=0.0),
            tags=["text", "exact", "holdout"],
        ),
        BenchTask(
            id="holdout.math.eval.1",
            prompt="(18/3)+6",
            evaluator=numeric_answer(12, tol=0.0),
            tags=["math", "exact", "holdout"],
        ),
    ]


def causal_tasks() -> List[BenchTask]:
    """Offline causal extraction tasks (no LLM required).

    These are designed for CausalGraphEngine which extracts (cause -> effect) pairs
    when cues like "يسبب" / "causes" are present.
    """

    return [
        BenchTask(
            id="causal.ar.1",
            prompt="التدخين يسبب السرطان",
            evaluator=causal_edges([("التدخين", "السرطان")], min_matches=1),
            tags=["causal", "offline"],
        ),
        BenchTask(
            id="causal.ar.2",
            prompt="قلة النوم يؤدي إلى ضعف التركيز",
            evaluator=causal_edges([("قلة النوم", "ضعف التركيز")], min_matches=1),
            tags=["causal", "offline"],
        ),
        BenchTask(
            id="causal.en.1",
            prompt="Rain causes wet ground",
            evaluator=causal_edges([("Rain", "wet ground")], min_matches=1),
            tags=["causal", "offline"],
        ),
    ]


def causal_holdout_tasks() -> List[BenchTask]:
    """Holdout variants for causal suite (unseen sentences)."""

    return [
        BenchTask(
            id="holdout.causal.ar.1",
            prompt="الرياضة تقلل التوتر",
            evaluator=causal_edges([("الرياضة", "التوتر")], min_matches=1),
            tags=["causal", "offline", "holdout"],
        ),
        BenchTask(
            id="holdout.causal.ar.2",
            prompt="الضوضاء تسبب الصداع",
            evaluator=causal_edges([("الضوضاء", "الصداع")], min_matches=1),
            tags=["causal", "offline", "holdout"],
        ),
        BenchTask(
            id="holdout.causal.en.1",
            prompt="Lack of exercise causes fatigue",
            evaluator=causal_edges([("Lack of exercise", "fatigue")], min_matches=1),
            tags=["causal", "offline", "holdout"],
        ),
    ]


def planning_tasks() -> List[BenchTask]:
    """Offline subgoal/plan tasks.

    We treat the Mathematical_Brain equation solver 'steps' as a measurable
    form of subgoal generation.
    """

    return [
        BenchTask(
            id="plan.eq.1",
            prompt="2x+5=15",
            evaluator=math_solution_with_steps(5, tol=0.0, min_steps=2),
            tags=["plan", "offline"],
        ),
        BenchTask(
            id="plan.eq.2",
            prompt="3x-9=0",
            evaluator=math_solution_with_steps(3, tol=0.0, min_steps=2),
            tags=["plan", "offline"],
        ),
    ]


def planning_holdout_tasks() -> List[BenchTask]:
    """Holdout variants for planning/steps suite."""

    return [
        BenchTask(
            id="holdout.plan.eq.1",
            prompt="5x+10=35",
            evaluator=math_solution_with_steps(5, tol=0.0, min_steps=2),
            tags=["plan", "offline", "holdout"],
        ),
        BenchTask(
            id="holdout.plan.eq.2",
            prompt="6x-12=0",
            evaluator=math_solution_with_steps(2, tol=0.0, min_steps=2),
            tags=["plan", "offline", "holdout"],
        ),
    ]


def planner_tasks() -> List[BenchTask]:
    """Non-math planning tasks (measurable format, offline).

    These are evaluated structurally: 3+ numbered steps.
    """

    return [
        BenchTask(
            id="planner.simple.1",
            prompt="اكتب خطة من 3 خطوات لعمل نسخة احتياطية لملف مهم.",
            evaluator=plan_steps_with_keywords(["نسخة", "احتياط"], min_steps=3, min_keyword_hits=1),
            tags=["planner", "offline", "structured"],
        ),
        BenchTask(
            id="planner.simple.2",
            prompt="اكتب خطة من 3 خطوات لتنظيم مجلد مشروع بايثون.",
            evaluator=plan_steps_with_keywords(["مجلد", "بايثون"], min_steps=3, min_keyword_hits=1),
            tags=["planner", "offline", "structured"],
        ),
    ]


def planner_holdout_tasks() -> List[BenchTask]:
    """Holdout variants for non-math planner suite."""

    return [
        BenchTask(
            id="holdout.planner.1",
            prompt="اكتب خطة من 3 خطوات لعمل نسخة احتياطية لصور عائلية على قرص خارجي.",
            evaluator=plan_steps_with_keywords(["صور", "قرص"], min_steps=3, min_keyword_hits=1),
            tags=["planner", "offline", "structured", "holdout"],
        ),
        BenchTask(
            id="holdout.planner.2",
            prompt="اكتب خطة من 3 خطوات لتنظيم مشروع بايثون مع ملفات tests وsrc.",
            evaluator=plan_steps_with_keywords(["tests", "src"], min_steps=3, min_keyword_hits=1),
            tags=["planner", "offline", "structured", "holdout"],
        ),
    ]


def planner_strict_holdout_tasks() -> List[BenchTask]:
    """Stricter holdout variants: keywords must appear in step texts.

    This suite intentionally fails on the current MicroPlanner (generic steps),
    and is meant to be improved via controlled self-modification.
    """

    return [
        BenchTask(
            id="holdout.planner_strict.1",
            prompt="اكتب خطة من 3 خطوات لعمل نسخة احتياطية لصور عائلية على قرص خارجي.",
            evaluator=plan_steps_keywords_in_steps(["صور", "قرص"], min_steps=3, min_keyword_hits=1),
            tags=["planner", "offline", "structured", "holdout", "strict"],
        ),
        BenchTask(
            id="holdout.planner_strict.2",
            prompt="اكتب خطة من 3 خطوات لتنظيم مشروع بايثون مع ملفات tests وsrc.",
            evaluator=plan_steps_keywords_in_steps(["tests", "src"], min_steps=3, min_keyword_hits=1),
            tags=["planner", "offline", "structured", "holdout", "strict"],
        ),
    ]


def default_tasks() -> List[BenchTask]:
    """Backward-compatible default: deterministic baseline."""

    return deterministic_tasks()


def task_index(tasks: List[BenchTask]) -> Dict[str, BenchTask]:
    return {t.id: t for t in tasks}
