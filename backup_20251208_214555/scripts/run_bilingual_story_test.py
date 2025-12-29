#!/usr/bin/env python3
"""Run a bilingual (Arabic / English) story QA test using the in-repo CognitiveIntegrationEngine.

This script:
- defines a 10-line Arabic story and a matching 10-line English story
- defines 10 questions + expected answers for each language
- asks the CIE each question (passing the appropriate story in the problem)
- prints question, expected answer, system answer, and correctness
- prints final correctness percentages per language

This is a lightweight, fuzzy-check evaluation (substring match, case-insensitive).
"""
import sys
from pprint import pprint
import re


def extract_answer_from_winner(winner: dict) -> str:
    """
    يحاول استخراج نص الجواب من هيكل winner القادم من CognitiveIntegrationEngine.
    يبحث في عدة مفاتيح محتملة ويعود بأفضل نص متاح.
    """
    if not winner:
        return ""

    # أولاً: لو فيه content جوّا winner
    payload = winner.get("content", winner) if isinstance(winner, dict) else winner

    # لو payload قاموس (dict)، نجرّب المفاتيح بالترتيب
    if isinstance(payload, dict):
        # 1) مفاتيح مباشرة داخل content
        for key in ("text", "answer", "response", "result"):
            v = payload.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()

        # 2) idea منفردة
        v = payload.get("idea")
        if isinstance(v, str) and v.strip():
            return v.strip()

        # 3) قائمة أفكار ideas
        ideas = payload.get("ideas")
        if isinstance(ideas, list) and ideas:
            first = ideas[0]
            if isinstance(first, dict) and "idea" in first and isinstance(first["idea"], str) and first["idea"].strip():
                return first["idea"].strip()
            if isinstance(first, str) and first.strip():
                return first.strip()

    # لو winner نفسه فيه نص في هذه المفاتيح
    if isinstance(winner, dict):
        for key in ("text", "answer", "response", "result", "idea"):
            v = winner.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()

    # آخر حل: نحول الـ winner لنص
    try:
        return str(winner)
    except Exception:
        return ""

def norm_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = s.strip()
    s = s.lower()
    # remove extra whitespace
    s = re.sub(r"\s+", " ", s)
    return s


def is_match(expected: str, actual: str) -> bool:
    e = norm_text(expected)
    a = norm_text(actual)
    if not e:
        return False
    # If exact substring in either direction, accept
    if e in a or a in e:
        return True
    # fallback: token overlap > 60%
    etoks = [t for t in re.split(r"\W+", e) if t]
    atoks = [t for t in re.split(r"\W+", a) if t]
    if not etoks or not atoks:
        return False
    common = set(etoks) & set(atoks)
    if len(common) / max(1, len(etoks)) >= 0.6:
        return True
    return False


def run_tests():
    # local import to use repository code
    try:
        from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
    except Exception as e:
        print("Failed to import CognitiveIntegrationEngine:", e)
        sys.exit(1)

    cie = CognitiveIntegrationEngine()
    cie.connect_engines()

    arabic_story_lines = [
        "كان يا مكان في قديم الزمان ولدٌ اسمه علي.",
        "في صباحٍ مشمس خرج علي ليلعب في الحديقة.",
        "بين الأشجار وجد قطة صغيرة ضائعة تبكي.",
        "كانت القطة رمادية اللون وعيناها كبيرتان.",
        "أخذ علي القطة ووضعها في سلةٍ صغيرة وحملها معه.",
        "سأل الجيران إن كانوا يعرفون صاحبها لكنه لم يجد إجابة.",
        "بعد ذلك ذهب إلى الملجأ المحلي وسأل عن قطة مماثلة.",
        "الموظف في الملجأ ساعده في البحث عن صاحب القطة عبر إعلان.",
        "في المساء جاء رجلٌ مسن يبكي وقال إنها قطة حفيده الضائع.",
        "عاد علي والقط إلى بيت الرجل، وشعر بالسعادة لأنه فعل الخير.",
    ]

    english_story_lines = [
        "Once upon a time there was a boy named Ali.",
        "One sunny morning Ali went out to play in the park.",
        "Among the trees he found a small lost kitten crying.",
        "The kitten was gray and had big eyes.",
        "Ali put the kitten in a small basket and took it with him.",
        "He asked neighbors if they knew the owner but found no answer.",
        "Later he went to the local shelter and inquired about a similar cat.",
        "A shelter worker helped him post a notice to find the owner.",
        "In the evening an old man arrived saying it was his grandson's lost cat.",
        "Ali returned the cat to the man and felt happy for doing good.",
    ]

    arabic_story = "\n".join(arabic_story_lines)
    english_story = "\n".join(english_story_lines)

    arabic_qas = [
        ("من هو بطل القصة؟", "علي"),
        ("متى خرج علي؟", "صباح مشمس"),
        ("ماذا وجد بين الأشجار؟", "قطة صغيرة ضائعة"),
        ("ما لون القطة؟", "رمادية"),
        ("أين وضع علي القطة عندما وجدها؟", "في سلة"),
        ("هل وجد الجيران صاحب القطة؟", "لا"),
        ("إلى أين ذهب علي ليسأل عن القطة؟", "الملجأ المحلي"),
        ("ماذا فعل موظف الملجأ؟", "ساعده في البحث/نشر إعلان"),
        ("من جاء في المساء؟", "رجل مسن/صاحب القطة/جد"),
        ("كيف شعر علي في النهاية؟", "سعيد/فعل الخير"),
    ]

    english_qas = [
        ("Who is the main character?", "Ali"),
        ("When did Ali go out?", "a sunny morning"),
        ("What did he find among the trees?", "a small lost kitten"),
        ("What color was the kitten?", "gray"),
        ("Where did Ali put the kitten?", "in a small basket"),
        ("Did neighbors know the owner?", "no"),
        ("Where did he go next to ask about the cat?", "the local shelter"),
        ("What did the shelter worker do?", "helped him post a notice/helped search"),
        ("Who came in the evening?", "an old man"),
        ("How did Ali feel at the end?", "happy"),
    ]

    results = {"arabic": [], "english": []}

    print("\n=== Arabic story test ===\n")
    for i, (q, expected) in enumerate(arabic_qas, start=1):
        problem = {"title": q, "story": arabic_story}
        res = cie.collaborative_solve(problem, domains_needed=("language", "analysis"))
        winner = res.get("winner") or {}
        ans_str = extract_answer_from_winner(winner)
        ok = is_match(expected, ans_str)
        results['arabic'].append(ok)
        print(f"Q{i}: {q}")
        print(f"Expected: {expected}")
        print(f"System answer: {ans_str}")
        print(f"OK: {ok}\n")

    print("\n=== English story test ===\n")
    for i, (q, expected) in enumerate(english_qas, start=1):
        problem = {"title": q, "story": english_story}
        res = cie.collaborative_solve(problem, domains_needed=("language", "analysis"))
        winner = res.get("winner") or {}
        ans_str = extract_answer_from_winner(winner)
        ok = is_match(expected, ans_str)
        results['english'].append(ok)
        print(f"Q{i}: {q}")
        print(f"Expected: {expected}")
        print(f"System answer: {ans_str}")
        print(f"OK: {ok}\n")

    for lang in ('arabic', 'english'):
        total = len(results[lang])
        correct = sum(1 for v in results[lang] if v)
        pct = (correct / total * 100) if total else 0.0
        print(f"{lang.capitalize()} correctness: {correct}/{total} = {pct:.1f}%")


if __name__ == '__main__':
    run_tests()
