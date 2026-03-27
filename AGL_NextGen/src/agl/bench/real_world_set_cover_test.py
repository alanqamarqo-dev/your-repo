"""Real-world style executable challenge: Minimum Set Cover.

Goal:
- Ask the AGL system for a minimum set cover solution on a fixed instance.
- Verify correctness AND optimality via brute-force search (deterministic).

This is intentionally harder than the current proxy criteria because:
- It requires solving a combinatorial optimization problem exactly.
- We verify the answer by computation, not by keyword matching.

Usage (PowerShell):
  python -m agl.bench.real_world_set_cover_test

Notes:
- This does NOT claim 'no AI can solve it'; it is simply a strong, checkable task.
"""

from __future__ import annotations

import itertools
import re
import sys
import time
from typing import Iterable, List, Sequence, Set, Tuple


def _bruteforce_min_set_cover(universe: Sequence[int], sets: Sequence[Set[int]]) -> Tuple[int, Tuple[int, ...]]:
    u = set(universe)
    n = len(sets)
    for k in range(1, n + 1):
        for combo in itertools.combinations(range(n), k):
            covered: Set[int] = set()
            for i in combo:
                covered |= sets[i]
            if covered >= u:
                return k, combo
    return n + 1, tuple()


def _parse_indices(text: str, n_sets: int) -> List[int]:
    """Extract 1-based or 0-based indices from a model answer."""
    if not text:
        return []

    # Many system responses echo the full prompt (which contains lots of numbers).
    # Prefer parsing from the "Math:" segment if present.
    t = text
    if "Math:" in t:
        t = t.split("Math:", 1)[1]
        # Stop at the next pipeline segment (Ghost/Map/etc) to avoid unrelated numbers.
        if "|" in t:
            t = t.split("|", 1)[0]

    # Prefer patterns like: [1,3,5] or {2,4}
    nums = [int(x) for x in re.findall(r"-?\d+", t)]
    # Filter plausible indices.
    cand = [x for x in nums if 0 <= x <= n_sets or 1 <= x <= n_sets]

    # If any 0 appears, assume 0-based.
    if any(x == 0 for x in cand):
        return sorted(set(x for x in cand if 0 <= x < n_sets))

    # Otherwise assume 1-based.
    one_based = [x for x in cand if 1 <= x <= n_sets]
    return sorted(set(x - 1 for x in one_based))


def _covers(universe: Sequence[int], sets: Sequence[Set[int]], idxs: Iterable[int]) -> bool:
    u = set(universe)
    covered: Set[int] = set()
    for i in idxs:
        if 0 <= i < len(sets):
            covered |= sets[i]
    return covered >= u


def main() -> int:
    # Fixed deterministic instance.
    # Universe elements: 1..12
    universe = list(range(1, 13))

    sets = [
        {1, 2, 3},
        {4, 5, 6},
        {7, 8},
        {9, 10},
        {11, 12},
        {2, 5, 8, 11},
        {1, 4, 7, 10},
        {3, 6, 9, 12},
        {2, 4, 6, 8, 10, 12},
        {1, 5, 9, 11},
    ]

    # Compute optimum.
    t0 = time.time()
    opt_k, opt_combo = _bruteforce_min_set_cover(universe, sets)
    opt_ms = (time.time() - t0) * 1000.0

    prompt_lines = [
        "حل مهمة تحسين حقيقية (Minimum Set Cover) بشكل أمثل.",
        "المطلوب: اختر أقل عدد من المجموعات (Sets) التي تغطي كل عناصر الكون U.",
        "أعد الإجابة فقط كقائمة أرقام للمجموعات المختارة.",
        "مهم: يجب أن تكون الإجابة أمثلية (أقل عدد ممكن)، وسنقوم بالتحقق حسابياً.",
        "",
        f"U = {universe}",
        "Sets (مرقمة من 1 إلى 10):",
    ]
    for i, s in enumerate(sets, start=1):
        prompt_lines.append(f"{i}: {sorted(s)}")

    prompt = "\n".join(prompt_lines)

    # Ask the system.
    try:
        from agl.core.super_intelligence import AGL_Super_Intelligence

        asi = AGL_Super_Intelligence()
    except Exception as e:
        print(f"[FAIL] Could not initialize AGL_Super_Intelligence: {e}")
        return 2

    t1 = time.time()
    answer = asi.process_query(prompt)
    latency_ms = (time.time() - t1) * 1000.0

    answer_text = str(answer or "")
    idxs = _parse_indices(answer_text, n_sets=len(sets))

    ok_cover = _covers(universe, sets, idxs)
    ok_opt = ok_cover and (len(idxs) == opt_k)

    print("=" * 70)
    print("AGL Real-World Challenge: Minimum Set Cover")
    print("=" * 70)
    print(f"Computed optimum: k={opt_k}, combo(1-based)={[i+1 for i in opt_combo]} (bruteforce {opt_ms:.2f}ms)")
    print(f"AGL answer latency: {latency_ms:.2f}ms")
    print(f"AGL raw answer: {answer_text.strip()}")
    print(f"Parsed indices (1-based): {[i+1 for i in idxs]}")
    print(f"Covers U: {ok_cover}")
    print(f"Optimal size: {ok_opt}")

    if ok_opt:
        print("[PASS] Correct AND optimal.")
        return 0

    if ok_cover:
        print("[FAIL] Correct cover but NOT optimal.")
        return 1

    print("[FAIL] Does not cover the universe.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
