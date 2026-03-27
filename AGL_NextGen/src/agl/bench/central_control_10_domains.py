import time
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class DomainTask:
    domain: str
    query: str


def _tasks() -> List[DomainTask]:
    return [
        DomainTask(
            domain="Math",
            query=(
                "احسب بدقة. ضع: x = (37*19) - (144/12) + (5**3). "
                "أعد قيمة x فقط كرقم."
            ),
        ),
        DomainTask(
            domain="Optimization",
            query=(
                "حل مهمة تحسين حقيقية (Minimum Set Cover) بشكل أمثل. "
                "المطلوب: اختر أقل عدد من المجموعات (Sets) التي تغطي كل عناصر الكون U. "
                "أعد الإجابة فقط كقائمة أرقام للمجموعات المختارة. "
                "U = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]\n"
                "Sets (مرقمة من 1 إلى 10):\n"
                "1: [1, 2, 3]\n"
                "2: [4, 5, 6]\n"
                "3: [7, 8]\n"
                "4: [9, 10]\n"
                "5: [11, 12]\n"
                "6: [2, 5, 8, 11]\n"
                "7: [1, 4, 7, 10]\n"
                "8: [3, 6, 9, 12]\n"
                "9: [2, 4, 6, 8, 10, 12]\n"
                "10: [1, 5, 9, 11]"
            ),
        ),
        DomainTask(
            domain="Programming",
            query=(
                """لدي كود بايثون:
def f(a, b=[]):
    b.append(a)
    return b

المشكلة تظهر عند استدعائه عدة مرات. ما السبب وما هو الإصلاح الصحيح؟
أجب باختصار شديد."""
            ),
        ),
        DomainTask(
            domain="Data Analysis",
            query=(
                "تحليل بيانات سريع: data = [2, 4, 4, 4, 5, 5, 7, 9]. "
                "أعد: count, min, max, sorted(data)."
            ),
        ),
        DomainTask(
            domain="Physics",
            query=(
                "اشرح باختصار شديد ماذا يعني قانون نيوتن الثاني F=ma "
                "وأعط مثالاً رقمياً صغيراً."
            ),
        ),
        DomainTask(
            domain="Cybersecurity (Defensive)",
            query=(
                "أعطني 6 نصائح عملية لرفع أمان حساباتي وحماية الخصوصية "
                "بدون شرح طويل."
            ),
        ),
        DomainTask(
            domain="Language (Translation)",
            query=(
                "ترجم إلى الإنجليزية ترجمة طبيعية: \"الوقت كالسيف إن لم تقطعه قطعك\". "
                "أعد جملة واحدة فقط."
            ),
        ),
        DomainTask(
            domain="Project Management",
            query=(
                "ضع خطة من 5 خطوات لإطلاق مشروع برمجي صغير خلال أسبوعين، "
                "واجعل كل خطوة سطر واحد فقط."
            ),
        ),
        DomainTask(
            domain="Ethics",
            query=(
                "لدي فريق عمل يريد استخدام مراقبة شديدة لزيادة الإنتاجية. "
                "اذكر 3 مخاطر أخلاقية و3 بدائل أقل انتهاكاً للخصوصية."
            ),
        ),
        DomainTask(
            domain="Creative Writing",
            query=(
                "اكتب هايكو عربي قصير (3 أسطر) عن المطر."
            ),
        ),
    ]


def run_via_central_control(tasks: List[DomainTask]) -> List[Tuple[DomainTask, float, str]]:
    # Import here so this file can be imported without triggering the heavy boot.
    from agl.core.super_intelligence import AGL_Super_Intelligence

    controller = AGL_Super_Intelligence()
    results: List[Tuple[DomainTask, float, str]] = []

    for t in tasks:
        start = time.perf_counter()
        text = controller.process_query(t.query)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        results.append((t, elapsed_ms, str(text)))

    return results


def main() -> int:
    tasks = _tasks()
    results = run_via_central_control(tasks)

    print("=" * 72)
    print("AGL Central Control: 10 Domains Run")
    print("=" * 72)

    for idx, (task, elapsed_ms, text) in enumerate(results, start=1):
        print(f"\n[{idx}/10] Domain: {task.domain} | latency={elapsed_ms:.2f}ms")
        print("-" * 72)
        # Avoid flooding the terminal; show full answer but trimmed if massive.
        preview = text if len(text) <= 4000 else (text[:4000] + "\n...<truncated>...")
        print(preview)

    print("\nDONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
