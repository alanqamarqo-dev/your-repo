# tools/zero_shot_qa_eval.py

import json
import os
import time
from typing import Dict, List, Any

from Self_Improvement.Knowledge_Graph import agl_pipeline, extract_plain_answer
from Self_Improvement.continual_learning import record_learned_fact


HERE = os.path.dirname(__file__)
BENCHMARK_PATH = os.path.join(HERE, "zero_shot_qa_benchmark.json")

ARTIFACTS_DIR = os.path.join(os.path.dirname(HERE), "artifacts")
EVAL_JSON_PATH = os.path.join(ARTIFACTS_DIR, "zero_shot_qa_eval.json")
COLLECTIVE_MEMORY_PATH = os.getenv(
    "AGL_COLLECTIVE_MEMORY_PATH",
    os.path.join(ARTIFACTS_DIR, "collective_memory.jsonl"),
)

# Backwards-compatible names expected by tests
OUT_PATH = EVAL_JSON_PATH
MEMORY_PATH = COLLECTIVE_MEMORY_PATH


def _normalize_arabic(text: str) -> str:
    """تبسيط بسيط للنص العربي لزيادة مطابقة الكلمات."""
    if not isinstance(text, str):
        return ""
    s = text.strip().lower()
    # إزالة التشكيل والتطويل
    for ch in ["َ", "ً", "ُ", "ٌ", "ِ", "ٍ", "ْ", "ّ", "ـ"]:
        s = s.replace(ch, "")
    # توحيد الألف
    for ch in ["أ", "إ", "آ"]:
        s = s.replace(ch, "ا")
    # توحيد الياء/الألف المقصورة
    s = s.replace("ى", "ي")
    return s


def _compute_hits(answer: str, expected_groups: List[List[str]]) -> tuple:
    norm_answer = _normalize_arabic(answer)
    hits: List[str] = []
    missing: List[str] = []

    for group in expected_groups:
        group_hit = False
        for kw in group:
            kw_norm = _normalize_arabic(kw)
            if kw_norm and kw_norm in norm_answer:
                hits.append(kw)
                group_hit = True
                break
        if not group_hit and group:
            # نمثل المجموعة بالكلمة الأولى كـ label
            missing.append(group[0])

    score = 0.0
    if expected_groups:
        score = len(hits) / float(len(expected_groups))
    return hits, missing, score


def run_zero_shot_eval() -> Dict[str, Any]:
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    print("=== ZERO-SHOT QA EVAL START ===\n")

    per_question_results: Dict[str, Any] = {}
    scores: List[float] = []
    memory_rows: List[Dict[str, Any]] = []

    for qid, item in benchmark.items():
        q = item["q"]
        expected_keys = item.get("expected_keys", [])

        print("---")
        print(f"[Q] {qid}: {q}")

        t0 = time.time()
        result = agl_pipeline(q)
        t1 = time.time()

        answer_text = extract_plain_answer(result)
        hits, missing, score = _compute_hits(answer_text, expected_keys)
        latency = round(t1 - t0, 2)

        print(f"[ANS] {answer_text}")
        print(f"[HITS] {hits}")
        print(f"[MISSING] {missing}")
        print(f"[SCORE] {score:.2f}   (time={latency:.2f}s)\n")

        scores.append(score)
        per_question_results[qid] = {
            "id": qid,
            "question": q,
            "answer": answer_text,
            "hits": hits,
            "missing": missing,
            "score": score,
            "latency_s": latency,
            "ts": t1,
        }

        # سجل حقيقة متعلّمة إن كانت الإجابة قوية كفاية
        try:
            # In FAST_MODE the benchmark runs deterministically and may record
            # temporary learned facts that would contaminate subsequent
            # questions within the same run. To keep each question independent
            # during evaluation, skip recording learned facts when FAST_MODE is
            # enabled. This preserves expected benchmark behavior.
            IS_FAST = os.getenv("AGL_FAST_MODE") == "1"
            if not IS_FAST:
                record_learned_fact(
                    problem={"title": qid, "question": q},
                    answer=answer_text,
                    score=score,
                    source=("zero_shot_qa_eval_fast" if IS_FAST else "zero_shot_qa_eval"),
                    min_score=0.8,
                )
            else:
                # in fast mode, we intentionally skip persisting learned facts
                # to avoid cross-question contamination during the benchmark
                pass
        except Exception:
            # best-effort: do not break the benchmark if recording fails
            pass

        # سطر واحد للذاكرة الجماعية
        memory_rows.append(per_question_results[qid])

    overall = round(sum(scores) / len(scores), 2) if scores else 0.0

    print("=== SUMMARY ===")
    for qid, row in per_question_results.items():
        print(f"{qid}: score={row['score']:.2f}, time={row['latency_s']:.2f}s")
    print(f"\nOVERALL_AVG_SCORE = {overall:.2f}")
    print("=== ZERO-SHOT QA EVAL END ===\n")

    summary = {
        "results": per_question_results,
        "overall_avg_score": overall,
        "ts": time.time(),
    }

    # حفظ ملف التلخيص
    with open(EVAL_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # إضافة إلى الذاكرة الجماعية
    with open(COLLECTIVE_MEMORY_PATH, "a", encoding="utf-8") as f:
        for row in memory_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[INFO] saved eval summary to {EVAL_JSON_PATH}")
    print(f"[INFO] appended {len(memory_rows)} rows to {COLLECTIVE_MEMORY_PATH}")

    return summary


if __name__ == "__main__":
    run_zero_shot_eval()


def main():
    """Backward-compatible entrypoint for tests."""
    return run_zero_shot_eval()
