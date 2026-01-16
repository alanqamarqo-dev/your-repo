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
    hypothesis_with_prediction,
    plan_with_fallback,
    causal_intervention_answer,
    json_field_equals,
    json_field_truthy,
    holo_cache_speedup,
    plan_with_fallback_keywords_in_steps,
    causal_intervention_numeric,
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


def criteria_1_autonomy_tasks() -> List[BenchTask]:
    """Proxy suite for 'الاستقلال المعرفي'.

    Uses a synthetic 'raw data' prompt and requires a hypothesis + numeric prediction.
    """

    prompt = (
        "بيانات خام (x,y):\n"
        "1,2\n2,4\n3,6\n4,8\n5,10\n\n"
        "كوّن فرضية قصيرة تشرح العلاقة، ثم أعطِ تنبؤاً: إذا x=6 فما قيمة y؟"
    )
    return [
        BenchTask(
            id="criteria1.autonomy.hypothesis.1",
            prompt=prompt,
            evaluator=hypothesis_with_prediction(must_contain=["x", "y"], expected_number=12.0, tol=0.6),
            tags=["text", "holdout", "criteria", "criteria1", "autonomy"],
        )
    ]


def criteria_1_autonomy_tasks_strict() -> List[BenchTask]:
    """Stricter autonomy suite: multiple (x,y) patterns + predictions."""

    prompts = [
        (
            "criteria1s.autonomy.hypothesis.1",
            (
                "بيانات خام (x,y):\n"
                "1,3\n2,6\n3,9\n4,12\n\n"
                "كوّن فرضية قصيرة تشرح العلاقة بين x و y، ثم أعطِ تنبؤاً: إذا x=7 فما قيمة y؟"
            ),
            21.0,
        ),
        (
            "criteria1s.autonomy.hypothesis.2",
            (
                "بيانات خام (x,y):\n"
                "1,3\n2,5\n3,7\n4,9\n\n"
                "كوّن فرضية قصيرة تشرح العلاقة بين x و y، ثم أعطِ تنبؤاً: إذا x=6 فما قيمة y؟"
            ),
            13.0,
        ),
        (
            "criteria1s.autonomy.hypothesis.3",
            (
                "بيانات خام (x,y):\n"
                "2,1\n4,2\n6,3\n8,4\n\n"
                "كوّن فرضية قصيرة تشرح العلاقة بين x و y، ثم أعطِ تنبؤاً: إذا x=10 فما قيمة y؟"
            ),
            5.0,
        ),
        (
            "criteria1s.autonomy.hypothesis.4",
            (
                "بيانات خام (x,y):\n"
                "1,9\n2,8\n3,7\n4,6\n\n"
                "كوّن فرضية قصيرة تشرح العلاقة بين x و y، ثم أعطِ تنبؤاً: إذا x=6 فما قيمة y؟"
            ),
            4.0,
        ),
        (
            "criteria1s.autonomy.hypothesis.5",
            (
                "بيانات خام (x,y):\n"
                "1,2\n2,6\n3,10\n4,14\n\n"
                "كوّن فرضية قصيرة تشرح العلاقة بين x و y، ثم أعطِ تنبؤاً: إذا x=5 فما قيمة y؟"
            ),
            18.0,
        ),
        (
            "criteria1s.autonomy.hypothesis.6",
            (
                "بيانات خام (x,y):\n"
                "0,1\n1,3\n2,5\n3,7\n\n"
                "كوّن فرضية قصيرة تشرح العلاقة بين x و y، ثم أعطِ تنبؤاً: إذا x=4 فما قيمة y؟"
            ),
            9.0,
        ),
        (
            "criteria1s.autonomy.hypothesis.7",
            (
                "بيانات خام (x,y):\n"
                "1,10\n2,8\n3,6\n4,4\n\n"
                "كوّن فرضية قصيرة تشرح العلاقة بين x و y، ثم أعطِ تنبؤاً: إذا x=6 فما قيمة y؟"
            ),
            0.0,
        ),
        (
            "criteria1s.autonomy.hypothesis.8",
            (
                "بيانات خام (x,y):\n"
                "1,5\n2,8\n3,11\n4,14\n\n"
                "كوّن فرضية قصيرة تشرح العلاقة بين x و y، ثم أعطِ تنبؤاً: إذا x=6 فما قيمة y؟"
            ),
            20.0,
        ),
        (
            "criteria1s.autonomy.hypothesis.9",
            (
                "بيانات خام (x,y):\n"
                "1,100\n2,200\n3,300\n4,400\n\n"
                "كوّن فرضية قصيرة تشرح العلاقة بين x و y، ثم أعطِ تنبؤاً: إذا x=7 فما قيمة y؟"
            ),
            700.0,
        ),
        (
            "criteria1s.autonomy.hypothesis.10",
            (
                "بيانات خام (x,y):\n"
                "2,9\n4,13\n6,17\n8,21\n\n"
                "كوّن فرضية قصيرة تشرح العلاقة بين x و y، ثم أعطِ تنبؤاً: إذا x=10 فما قيمة y؟"
            ),
            25.0,
        ),
    ]

    out: List[BenchTask] = []
    for tid, prompt, expected in prompts:
        out.append(
            BenchTask(
                id=tid,
                prompt=prompt,
                evaluator=hypothesis_with_prediction(must_contain=["x", "y"], expected_number=float(expected), tol=0.8),
                tags=["text", "holdout", "criteria", "criteria1", "autonomy", "strict"],
            )
        )
    return out


def criteria_2_superiority_tasks() -> List[BenchTask]:
    """Proxy suite for 'التفوق القابل للقياس'.

    We measure against baseline engines using the comparator externally.
    These tasks are chosen where the baseline is typically weak (structured planning).
    """

    base = planner_strict_holdout_tasks()
    return [
        BenchTask(
            id=f"criteria2.{t.id}",
            prompt=t.prompt,
            evaluator=t.evaluator,
            tags=list(dict.fromkeys([x for x in (t.tags or []) if x != "offline"] + ["criteria", "criteria2", "superiority"])),
        )
        for t in base
    ]


def criteria_3_self_learning_tasks() -> List[BenchTask]:
    """Proxy suite for 'التعلم الذاتي الحقيقي'.

    This reuses the strict planner holdout which is designed to improve via the gated loop.
    """

    base = planner_strict_holdout_tasks()
    return [
        BenchTask(
            id=f"criteria3.{t.id}",
            prompt=t.prompt,
            evaluator=t.evaluator,
            tags=list(dict.fromkeys([x for x in (t.tags or []) if x != "offline"] + ["criteria", "criteria3", "self_learning"])),
        )
        for t in base
    ]


def criteria_4_subgoals_tasks() -> List[BenchTask]:
    """Proxy suite for 'توليد أهداف فرعية' + تغيير الاستراتيجية عند الفشل."""

    return [
        BenchTask(
            id="criteria4.subgoals.fallback.1",
            prompt=(
                "اكتب خطة من 3 خطوات لنقل مشروع بايثون إلى جهاز جديد. "
                "يجب أن تتضمن الخطة ماذا تفعل إذا فشلت الخطوة الثانية (خطة بديلة)."
            ),
            evaluator=plan_with_fallback(min_steps=3, must_include_fallback=True),
            tags=["planner", "structured", "holdout", "criteria", "criteria4", "subgoals"],
        )
    ]


def criteria_4_subgoals_tasks_strict() -> List[BenchTask]:
    """Stricter subgoals suite: multiple prompts requiring explicit fallback."""

    prompts = [
        (
            "criteria4s.subgoals.fallback.1",
            "اكتب خطة من 3 خطوات لترقية مشروع بايثون يعتمد على requirements.txt. يجب أن تتضمن الخطة ماذا تفعل إذا فشلت الخطوة الثانية (خطة بديلة).",
        ),
        (
            "criteria4s.subgoals.fallback.2",
            "اكتب خطة من 3 خطوات لنقل صور عائلية إلى قرص خارجي ثم التحقق منها. يجب أن تتضمن الخطة ماذا تفعل إذا فشلت الخطوة الثانية (خطة بديلة).",
        ),
        (
            "criteria4s.subgoals.fallback.3",
            "اكتب خطة من 3 خطوات لتنظيم مشروع بايثون مع src وtests وCI بسيط. يجب أن تتضمن الخطة ماذا تفعل إذا فشلت الخطوة الثانية (خطة بديلة).",
        ),
        (
            "criteria4s.subgoals.fallback.4",
            "اكتب خطة من 3 خطوات لإعداد نسخ احتياطي لملفات مهمة. يجب أن تتضمن الخطة ماذا تفعل إذا فشلت الخطوة الثانية (خطة بديلة).",
        ),
        (
            "criteria4s.subgoals.fallback.5",
            "اكتب خطة من 3 خطوات لترتيب صور عائلية حسب السنوات. يجب أن تتضمن الخطة ماذا تفعل إذا فشلت الخطوة الثانية (خطة بديلة).",
        ),
        (
            "criteria4s.subgoals.fallback.6",
            "اكتب خطة من 3 خطوات لإعداد قرص خارجي لنسخ صور عائلية. يجب أن تتضمن الخطة ماذا تفعل إذا فشلت الخطوة الثانية (خطة بديلة).",
        ),
        (
            "criteria4s.subgoals.fallback.7",
            "اكتب خطة من 3 خطوات لتجهيز مشروع بايثون جديد مع src وtests. يجب أن تتضمن الخطة ماذا تفعل إذا فشلت الخطوة الثانية (خطة بديلة).",
        ),
        (
            "criteria4s.subgoals.fallback.8",
            "اكتب خطة من 3 خطوات لتصدير مشروع بايثون إلى جهاز آخر. يجب أن تتضمن الخطة ماذا تفعل إذا فشلت الخطوة الثانية (خطة بديلة).",
        ),
        (
            "criteria4s.subgoals.fallback.9",
            "اكتب خطة من 3 خطوات لتحديث dependencies ثم تشغيل tests. يجب أن تتضمن الخطة ماذا تفعل إذا فشلت الخطوة الثانية (خطة بديلة).",
        ),
        (
            "criteria4s.subgoals.fallback.10",
            "اكتب خطة من 3 خطوات لتنظيم مجلد صور عائلية ثم نقلها إلى قرص خارجي. يجب أن تتضمن الخطة ماذا تفعل إذا فشلت الخطوة الثانية (خطة بديلة).",
        ),
    ]

    return [
        BenchTask(
            id=tid,
            prompt=prompt,
            evaluator=plan_with_fallback(min_steps=3, must_include_fallback=True),
            tags=["planner", "structured", "holdout", "criteria", "criteria4", "subgoals", "strict"],
        )
        for tid, prompt in prompts
    ]


def criteria_5_causal_tasks_strict() -> List[BenchTask]:
    """Stricter causal suite: multiple intervention prompts."""

    prompts = [
        (
            "criteria5s.causal.intervention.1",
            "لدينا علاقة سببية: X -> Y. إذا قمنا بتدخل do(X=1) فماذا يحدث لـ Y؟ اشرح لماذا (because/لأن).",
        ),
        (
            "criteria5s.causal.intervention.2",
            "لدينا علاقة سببية: X -> Y. إذا قمنا بتدخل do(X=0) فماذا يحدث لـ Y؟ اشرح لماذا (because/لأن).",
        ),
        (
            "criteria5s.causal.intervention.3",
            "افترض علاقة سببية بسيطة: X يؤثر على Y. ماذا تتوقع عند do(X=5) بالنسبة لـ Y؟ اشرح لماذا (because/لأن).",
        ),
        (
            "criteria5s.causal.intervention.4",
            "لدينا علاقة سببية: X -> Y. إذا قمنا بتدخل do(X=2) فماذا يحدث لـ Y؟ اشرح لماذا (because/لأن).",
        ),
        (
            "criteria5s.causal.intervention.5",
            "لدينا علاقة سببية: X -> Y. إذا قمنا بتدخل do(X=10) فماذا يحدث لـ Y؟ اشرح لماذا (because/لأن).",
        ),
        (
            "criteria5s.causal.intervention.6",
            "إذا كانت لدينا علاقة سببية: X -> Y، ما التغير المتوقع في Y عند do(X=-1)؟ اشرح لماذا (because/لأن).",
        ),
        (
            "criteria5s.causal.intervention.7",
            "لدينا علاقة سببية: X -> Y. ماذا تتوقع يحدث لـ Y لو فعلنا do(X=0)؟ اشرح لماذا (because/لأن).",
        ),
        (
            "criteria5s.causal.intervention.8",
            "في نموذج سببي بسيط: X يؤثر على Y. ماذا تتوقع عند do(X=3) بالنسبة لـ Y؟ اشرح لماذا (because/لأن).",
        ),
        (
            "criteria5s.causal.intervention.9",
            "لدينا علاقة سببية: X -> Y. إذا قمنا بتدخل do(X=1) فما أثر ذلك على Y؟ اشرح لماذا (because/لأن).",
        ),
        (
            "criteria5s.causal.intervention.10",
            "علاقة سببية: X -> Y. ماذا يعني do(X=0) وما أثره على Y؟ اشرح لماذا (because/لأن).",
        ),
    ]

    return [
        BenchTask(
            id=tid,
            prompt=prompt,
            evaluator=causal_intervention_answer(must_contain=["do", "x", "y"]),
            tags=["causal", "holdout", "criteria", "criteria5", "causal", "strict"],
        )
        for tid, prompt in prompts
    ]


def criteria_5_causal_tasks() -> List[BenchTask]:
    """Proxy suite for 'الفهم السببي العميق' (تدخل + تفسير)."""

    return [
        BenchTask(
            id="criteria5.causal.intervention.1",
            prompt=(
                "لدينا علاقة سببية: X -> Y. إذا قمنا بتدخل do(X=0) فماذا يحدث لـ Y؟ "
                "اشرح لماذا (because/لأن)."
            ),
            evaluator=causal_intervention_answer(must_contain=["do", "x", "y"]),
            tags=["causal", "holdout", "criteria", "criteria5", "causal"],
        )
    ]


def criteria_suite_names() -> List[str]:
    return [
        "criteria_all",
        "criteria_all_strict",
        "criteria_all_hard",
        "nextgen_smoke",
        "criteria_1_autonomy",
        "criteria_2_superiority",
        "criteria_3_self_learning",
        "criteria_4_subgoals",
        "criteria_5_causal",
    ]


def criteria_all_hard_tasks() -> List[BenchTask]:
    """Harder gate intended to reduce template/keyword gaming.

    This suite is still deterministic, but:
      - planning requires prompt tokens inside step texts
      - subgoals require explicit fallback inside steps
      - causal requires do-terms + explanation marker + numeric prediction
    """

    tasks: List[BenchTask] = []

    # Criteria 1 (Autonomy proxy): hypothesis + numeric prediction holdouts
    hyp_prompts = [
        (
            "criteria1h.autonomy.hypothesis.1",
            "بيانات (x,y):\n0,1\n1,3\n2,5\n3,7\n\nكوّن فرضية قصيرة ثم أعطِ تنبؤاً: إذا x=10 فما قيمة y؟",
            21.0,
        ),
        (
            "criteria1h.autonomy.hypothesis.2",
            "بيانات (x,y):\n1,2\n2,4\n3,6\n4,8\n\nكوّن فرضية قصيرة ثم أعطِ تنبؤاً: إذا x=9 فما قيمة y؟",
            18.0,
        ),
        (
            "criteria1h.autonomy.hypothesis.3",
            "بيانات (x,y):\n1,4\n2,7\n3,10\n4,13\n\nكوّن فرضية قصيرة ثم أعطِ تنبؤاً: إذا x=6 فما قيمة y؟",
            19.0,
        ),
    ]
    for tid, prompt, exp in hyp_prompts:
        tasks.append(
            BenchTask(
                id=tid,
                prompt=prompt,
                evaluator=hypothesis_with_prediction(must_contain=["x", "y"], expected_number=float(exp), tol=0.6),
                tags=["text", "holdout", "criteria", "criteria1", "autonomy", "hard"],
            )
        )

    # Criteria 2 (Superiority proxy): planning must embed concrete prompt tokens in steps
    plan_prompts = [
        ("criteria2h.superiority.plan.1", "اكتب خطة 3 خطوات لترحيل مشروع بايثون إلى جهاز جديد مع venv وrequirements.txt.", ["venv", "requirements.txt"]),
        ("criteria2h.superiority.plan.2", "اكتب خطة 3 خطوات لإعداد CI يشغل pytest ويولد تقرير coverage.", ["pytest", "coverage"]),
        ("criteria2h.superiority.plan.3", "اكتب خطة 3 خطوات لتنظيم repo: مجلد src ومجلد tests وملف pyproject.toml.", ["src", "tests", "pyproject.toml"]),
    ]
    for tid, prompt, kws in plan_prompts:
        tasks.append(
            BenchTask(
                id=tid,
                prompt=prompt,
                evaluator=plan_steps_keywords_in_steps(kws, min_steps=3, min_keyword_hits=2 if len(kws) >= 2 else 1),
                tags=["planner", "structured", "holdout", "criteria", "criteria2", "superiority", "hard"],
            )
        )

    # Criteria 3 (Self-learning proxy): force fallback + concrete tokens inside step texts
    sl_prompts = [
        ("criteria3h.self_learning.fallback.1", "ضع خطة 3 خطوات لتشغيل tests. إذا فشل pytest بسبب ImportError اذكر خطة بديلة داخل الخطوات.", ["pytest", "importerror"]),
        ("criteria3h.self_learning.fallback.2", "ضع خطة 3 خطوات لإصلاح مشكلة "
         "'ModuleNotFoundError' في مشروع بايثون. اذكر fallback إذا فشل الحل الأول.", ["modulenotfounderror", "pip"]),
    ]
    for tid, prompt, kws in sl_prompts:
        tasks.append(
            BenchTask(
                id=tid,
                prompt=prompt,
                evaluator=plan_with_fallback_keywords_in_steps(kws, min_steps=3, min_keyword_hits=1),
                tags=["planner", "structured", "holdout", "criteria", "criteria3", "self_learning", "hard"],
            )
        )

    # Criteria 4 (Subgoals): fallback + keywords
    sg_prompts = [
        ("criteria4h.subgoals.fallback.1", "اكتب خطة 3 خطوات لعمل backup إلى قرص خارجي. إذا فشل النسخ اذكر fallback داخل الخطوات.", ["backup", "قرص"]),
        ("criteria4h.subgoals.fallback.2", "اكتب خطة 3 خطوات لتحميل نموذج في ollama. إذا فشل pull اذكر fallback داخل الخطوات.", ["ollama", "pull"]),
    ]
    for tid, prompt, kws in sg_prompts:
        tasks.append(
            BenchTask(
                id=tid,
                prompt=prompt,
                evaluator=plan_with_fallback_keywords_in_steps(kws, min_steps=3, min_keyword_hits=1),
                tags=["planner", "structured", "holdout", "criteria", "criteria4", "subgoals", "hard"],
            )
        )

    # Criteria 5 (Causal): do-terms + explanation + numeric prediction
    causal_prompts = [
        (
            "criteria5h.causal.intervention.numeric.1",
            "نموذج سببي: Y = 2*X + 1. نفّذ تدخل do(X=4). ما قيمة Y؟ اذكر do(X=4) وفسّر لأن/because.",
            9.0,
        ),
        (
            "criteria5h.causal.intervention.numeric.2",
            "نموذج سببي: Y = 3*X - 2. نفّذ تدخل do(X=0). ما قيمة Y؟ اذكر do(X=0) وفسّر لأن/because.",
            -2.0,
        ),
        (
            "criteria5h.causal.intervention.numeric.3",
            "نموذج سببي: Y = X + 10. نفّذ تدخل do(X=-1). ما قيمة Y؟ اذكر do(X=-1) وفسّر لأن/because.",
            9.0,
        ),
    ]
    for tid, prompt, exp in causal_prompts:
        tasks.append(
            BenchTask(
                id=tid,
                prompt=prompt,
                evaluator=causal_intervention_numeric(must_contain=["do", "x", "y"], expected_number=float(exp), tol=0.6),
                tags=["causal", "holdout", "criteria", "criteria5", "causal", "hard"],
            )
        )

    return tasks


def nextgen_smoke_tasks() -> List[BenchTask]:
    """Small end-to-end smoke suite for NextGen engines.

    Goal: verify key engines can be invoked and produce outputs that match their expected schemas.
    """

    return [
        BenchTask(
            id="nextgen_smoke.planner.basic",
            prompt="اكتب خطة من 3 خطوات لتنظيم مشروع بايثون بسيط مع src وtests.",
            evaluator=plan_steps(min_steps=3),
            tags=["criteria", "planner", "structured", "smoke"],
        ),
        BenchTask(
            id="nextgen_smoke.hypothesis.prediction",
            prompt=(
                "بيانات (x,y):\n"
                "1,3\n2,5\n3,7\n4,9\n\n"
                "كوّن فرضية قصيرة تشرح العلاقة بين x و y، ثم أعطِ تنبؤاً: إذا x=6 فما قيمة y؟"
            ),
            evaluator=hypothesis_with_prediction(must_contain=["x", "y"], expected_number=13.0, tol=0.6),
            tags=["criteria", "autonomy", "hypothesis", "smoke"],
        ),
        BenchTask(
            id="nextgen_smoke.causal_edges.basic",
            prompt="التدخين يسبب السرطان.\nالتمرين يؤدي إلى تحسن الصحة.",
            evaluator=causal_edges([("التدخين", "السرطان"), ("التمرين", "تحسن الصحة")], min_matches=1),
            tags=["criteria", "causal", "structured", "smoke"],
        ),
        BenchTask(
            id="nextgen_smoke.units_validator.valid",
            prompt="تحقق من الوحدات: السرعة = 10 m/s، والكتلة = 2 kg.",
            evaluator=json_field_truthy("valid"),
            tags=["units", "structured", "smoke"],
        ),
        BenchTask(
            id="nextgen_smoke.units_validator.engine",
            prompt="تأكيد محرك الوحدات يعمل: 5 km و 3 cm.",
            evaluator=json_field_equals("ok", True),
            tags=["units", "structured", "smoke"],
        ),
        BenchTask(
            id="nextgen_smoke.consistency_checker.ok",
            prompt="اختبار سريع لمحرك الاتساق (بدون بيانات إضافية).",
            evaluator=json_field_equals("ok", True),
            tags=["consistency", "structured", "smoke"],
        ),
        BenchTask(
            id="nextgen_smoke.math_brain.steps",
            prompt="حل المعادلة: x + 7 = 20 مع خطوات.",
            evaluator=math_solution_with_steps(13.0, tol=1e-6, min_steps=2),
            tags=["math", "structured", "smoke"],
        ),
        BenchTask(
            id="nextgen_smoke.holo_cache.probe",
            prompt="HOLO_CACHE_PROBE",
            evaluator=holo_cache_speedup(min_hit_delta=1, min_speedup_ratio=1.01),
            tags=["holo_cache", "structured", "smoke"],
        ),
    ]


def criteria_tasks_for_suite(name: str) -> List[BenchTask]:
    n = (name or "").strip().lower()
    if n in ("nextgen_smoke", "smoke", "nextgen"):
        return nextgen_smoke_tasks()
    if n in ("criteria_all_hard", "criteria_hard", "hard"):
        return criteria_all_hard_tasks()
    if n in ("criteria_all", "criteria", "all_criteria", "all"):
        tasks: List[BenchTask] = []
        tasks.extend(criteria_1_autonomy_tasks())
        tasks.extend(criteria_2_superiority_tasks())
        tasks.extend(criteria_3_self_learning_tasks())
        tasks.extend(criteria_4_subgoals_tasks())
        tasks.extend(criteria_5_causal_tasks())
        return tasks
    if n in ("criteria_all_strict", "criteria_strict", "all_strict"):
        tasks = []
        tasks.extend(criteria_1_autonomy_tasks_strict())
        # Expand c2/c3 to 10 planner tasks each (structure-focused to avoid keyword overfitting).
        c23_prompts = [
            "اكتب خطة من 3 خطوات لعمل نسخة احتياطية لصور عائلية على قرص خارجي.",
            "اكتب خطة من 3 خطوات لتنظيم مشروع بايثون مع ملفات tests وsrc.",
            "اكتب خطة من 3 خطوات لترتيب مشروع بايثون قائم وإضافة مجلد tests.",
            "اكتب خطة من 3 خطوات لإنشاء مشروع بايثون جديد يبدأ بـ src وtests.",
            "اكتب خطة من 3 خطوات لنقل مشروع بايثون إلى جهاز جديد.",
            "اكتب خطة من 3 خطوات لتنظيف مجلد صور عائلية ثم نسخه إلى قرص خارجي.",
            "اكتب خطة من 3 خطوات لإعداد بيئة بايثون ثم تشغيل tests.",
            "اكتب خطة من 3 خطوات لعمل backup ثم التحقق من الملفات على قرص خارجي.",
            "اكتب خطة من 3 خطوات لتنظيم بنية src ثم إضافة tests بسيطة.",
            "اكتب خطة من 3 خطوات لتوثيق مشروع بايثون وتشغيل tests بعد التعديل.",
        ]
        for i, p in enumerate(c23_prompts, start=1):
            tasks.append(
                BenchTask(
                    id=f"criteria2s.superiority.plan.{i}",
                    prompt=p,
                    evaluator=plan_steps(min_steps=3),
                    tags=["planner", "structured", "holdout", "criteria", "criteria2", "superiority", "strict"],
                )
            )
        for i, p in enumerate(c23_prompts, start=1):
            tasks.append(
                BenchTask(
                    id=f"criteria3s.self_learning.plan.{i}",
                    prompt=p,
                    evaluator=plan_steps(min_steps=3),
                    tags=["planner", "structured", "holdout", "criteria", "criteria3", "self_learning", "strict"],
                )
            )
        tasks.extend(criteria_4_subgoals_tasks_strict())
        tasks.extend(criteria_5_causal_tasks_strict())
        return tasks
    if n in ("criteria_1_autonomy", "c1", "autonomy"):
        return criteria_1_autonomy_tasks()
    if n in ("criteria_2_superiority", "c2", "superiority"):
        return criteria_2_superiority_tasks()
    if n in ("criteria_3_self_learning", "c3", "self_learning"):
        return criteria_3_self_learning_tasks()
    if n in ("criteria_4_subgoals", "c4", "subgoals"):
        return criteria_4_subgoals_tasks()
    if n in ("criteria_5_causal", "c5", "causal"):
        return criteria_5_causal_tasks()
    return []


def default_tasks() -> List[BenchTask]:
    """Backward-compatible default: deterministic baseline."""

    return deterministic_tasks()


def task_index(tasks: List[BenchTask]) -> Dict[str, BenchTask]:
    return {t.id: t for t in tasks}
