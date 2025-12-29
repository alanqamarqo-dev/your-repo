import argparse
import json
import os
from datetime import datetime, timezone

from Self_Improvement.Knowledge_Graph import agl_pipeline


def load_benchmark(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def keyword_score(answer_text, expected_keywords):
    """
    تقييم بسيط:
    - يحسب كم كلمة من expected_keywords ظهرت في answer_text
    - يرجّع (hits, total, ratio)
    """
    if not expected_keywords:
        return 0, 0, 0.0

    text = (answer_text or "").lower()
    hits = 0
    for kw in expected_keywords:
        if not kw:
            continue
        # نستخدم lowercase لكن للأحرف العربية ما يفرق كثير، يبقى النص كما هو
        if kw.lower() in text:
            hits += 1
    total = len([k for k in expected_keywords if k])
    ratio = hits / total if total > 0 else 0.0
    return hits, total, ratio


def run_zero_shot(bench_path, limit=None, out_path=None, min_pass_ratio=0.4):
    benchmark = load_benchmark(bench_path)
    if limit is not None:
        benchmark = benchmark[:limit]

    results = []
    passed = 0
    failed = 0

    for idx, item in enumerate(benchmark, start=1):
        qid = item.get("id", f"item_{idx}")
        question = item["question"]
        expected_keywords = item.get("expected_keywords", [])
        domain = item.get("domain", "unknown")

        print(f"[{idx}/{len(benchmark)}] Running zero-shot for id={qid} (domain={domain})...")
        out = agl_pipeline(question)

        answer = out.get("answer", "")
        provenance = out.get("provenance", {})

        hits, total, ratio = keyword_score(answer, expected_keywords)
        passed_flag = ratio >= min_pass_ratio

        if passed_flag:
            passed += 1
        else:
            failed += 1

        print(f"  -> hits={hits}/{total} (ratio={ratio:.2f}) | {'PASS' if passed_flag else 'FAIL'}")
        print(f"  answer (truncated to 200 chars): {answer[:200]!r}")
        print()

        results.append(
            {
                "id": qid,
                "question": question,
                "domain": domain,
                "expected_keywords": expected_keywords,
                "answer": answer,
                "keyword_hits": hits,
                "keyword_total": total,
                "keyword_ratio": ratio,
                "passed": passed_flag,
                "provenance": provenance,
            }
        )

    total_items = len(benchmark)
    pass_rate = (passed / total_items) * 100 if total_items > 0 else 0.0

    print("=== Zero-shot benchmark summary ===")
    print(f"Total items : {total_items}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {failed}")
    print(f"Pass rate   : {pass_rate:.1f}% (threshold ratio={min_pass_ratio:.2f})")

    # حفظ النتائج في artifacts
    if out_path is None:
        os.makedirs("artifacts", exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = os.path.join("artifacts", f"zero_shot_runs_{ts}.jsonl")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # write JSONL using stdlib to avoid external dependency
    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nDetailed run records saved to: {out_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run a simple zero-shot benchmark using agl_pipeline."
    )
    parser.add_argument(
        "--bench-path",
        type=str,
        default="benchmarks/zero_shot_holdout.jsonl",
        help="Path to the zero-shot benchmark JSONL file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of items to run.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Optional output JSONL path (default: artifacts/zero_shot_runs_<ts>.jsonl)",
    )
    parser.add_argument(
        "--min-pass-ratio",
        type=float,
        default=0.4,
        help="Minimum ratio of keyword hits to consider an item PASS.",
    )

    args = parser.parse_args(argv)
    run_zero_shot(
        bench_path=args.bench_path,
        limit=args.limit,
        out_path=args.out,
        min_pass_ratio=args.min_pass_ratio,
    )


if __name__ == "__main__":
    raise SystemExit(main())
