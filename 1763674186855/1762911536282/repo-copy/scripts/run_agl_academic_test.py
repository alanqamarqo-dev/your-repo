"""Run the AGI Academic Strict test against the local AGL RAG/LLM endpoint.

This script calls Integration_Layer.rag_wrapper.rag_answer(query, context)
for each of the 10 parts and writes the responses to stdout and to
`artifacts/ag_test_results.json`.

Usage (PowerShell):
  # set env as needed (example using ollama-http)
  $env:AGL_FEATURE_ENABLE_RAG='1'
  $env:AGL_LLM_PROVIDER='ollama-http'
  $env:AGL_LLM_BASEURL='http://127.0.0.1:11434'
  $env:AGL_LLM_MODEL='qwen2.5:7b-instruct'
  $env:AGL_FORCE_REAL='1'   # optional: force real-only
  py -3 scripts\run_agl_academic_test.py

The script is intentionally simple: it prints engine tags and answers,
and saves JSON results to artifacts/ag_test_results.json.
"""
import json
import os
import time
from typing import Any, Dict, List

try:
    from Integration_Layer.rag_wrapper import rag_answer
except Exception as e:
    raise SystemExit("Failed to import rag_answer from Integration_Layer.rag_wrapper: %s" % e)

TEST_PROMPTS: List[Dict[str, Any]] = [
    {
        "id": "1.1",
        "title": "منطق رمزي متعدد المستويات",
        "query": (
            "إذا كان:\n- كل أ هو ب\n- بعض ب هو ج\n- لا شيء من ج هو د\n\n"
            "السؤال: هل يمكن أن يكون بعض أ هو د؟ برّر إجابتك باستخدام قواعد المنطق الرسمي واذكر جميع الافتراضات."
        ),
    },
    {
        "id": "1.2",
        "title": "تحليل الخوارزمية المعقدة",
        "query": (
            "حلل الخوارزمية التالية وأوجد تعقيدها الزمني Big-O واقترح تحسينات."
            "\n\n" +
            "def mysterious_algorithm(n):\n"
            "    if n <= 1:\n"
            "        return n\n"
            "    result = 0\n"
            "    for i in range(1, n):\n"
            "        for j in range(1, n, i):\n"
            "            result += (i * j) % n\n"
            "    return result + mysterious_algorithm(n-1)\n\n"
            "أجب خطوة بخطوة: 1) ما الذي تفعله الخوارزمية؟ 2) تعقيدها Big-O؟ 3) كيف تُحسّنها؟"
        ),
    },
    {
        "id": "2.1",
        "title": "تصميم تجربة علمية",
        "query": (
            "صمم تجربة علمية محكمة لاختبار الفرضية: 'المواد النانوية الكربونية يمكنها تحسين كفاءة الخلايا الشمسية'.\n"
            "حدد المتغيرات المستقلة والتابعة، مجموعة التحكم والتجريبية، طريقة جمع البيانات والتحليل الإحصائي، كيفية استبعاد العوامل المربكة، ومعايير النجاح والفشل."
        ),
    },
    {
        "id": "2.2",
        "title": "تحليل البيانات المعقدة",
        "query": (
            "لديك مجموعة بيانات زمنية:\n"
            "الزمن: [1..10], درجة_الحرارة: [20,22,25,24,23,21,20,19,18,17],\n"
            "الرطوبة: [60,65,70,68,62,58,55,50,48,45], الضغط: [1010,1012,1015,1013,1011,1008,1005,1002,1000,998]\n"
            "اكتشف الأنماط والعلاقات السببية وقدّم نموذج تنبؤي مبسّط وبرّر اختيارك.")
    },
    {
        "id": "3.1",
        "title": "تصميم نظام زراعي صحراوي",
        "query": (
            "صمم نظام زراعة في المناطق الصحراوية باستخدام الطاقة الشمسية فقط والمياه المالحة ومواد محلية رخيصة وتقنيات AI.\n"
            "اشرح المبادئ العلمية، التصميم الهندسي، الجدوى الاقتصادية، والتأثير البيئي والاجتماعي.")
    },
    {
        "id": "3.2",
        "title": "قصة إبداعية متقاطعة",
        "query": (
            "اكتب قصة قصيرة تمزج فيزياء الكم، الفلسفة الوجودية، الاقتصاد السلوكي، والأساطير الإغريقية. يجب أن تحتوي على حبكة متماسكة، شخصيات معقدة، استعارات متعددة المستويات ونهاية تترك أثراً فكرياً.")
    },
    {
        "id": "4.1",
        "title": "تحليل موقف اجتماعي معقد",
        "query": (
            "في شركة ناشئة: المؤسس كاريزمي لكنه متسلط، الفريق مبدع لكنه مشتت، المستثمرون يطالبون بنتائج سريعة، المنافسة شرسة.\n"
            "حلل الديناميكيات النفسية، الصراعات الخفية والظاهرية، اقترح خطة لتحسين البيئة وكيف توازن بين الإبداع والانضباط.")
    },
    {
        "id": "4.2",
        "title": "إطار أخلاقي لاستخدام AI",
        "query": (
            "طور إطاراً أخلاقياً لاستخدام الذكاء الاصطناعي في: التشخيص الطبي، التداول المالي، المراقبة الأمنية، والتعليم الشخصي.\n"
            "حدد المبادئ الأساسية، كيفية معالجة التعارض، آليات المراقبة والمساءلة، وتأثير ذلك على حقوق الإنسان.")
    },
    {
        "id": "5.1",
        "title": "تعلم لغة جديدة (إندونيسية)",
        "query": (
            "من الأمثلة: 'Saya makan nasi', 'Kamu minum air', 'Dia membaca buku'. استنتج القواعد الإنشائية وأنشئ 5 جمل إندونيسية جديدة وصِف كيف تعلمت القواعد خطوة بخطوة.")
    },
    {
        "id": "5.2",
        "title": "حل المشكلات التكيفي",
        "query": (
            "ثلاث مراحل من مجموعات الأعداد:\n"
            "1) 2,6,12,20,30,?\n"
            "2) الآن القاعدة تغيرت: 2,6,12,20,30,40,?\n"
            "3) القاعدة تغيرت مرة أخرى: 2,6,12,20,30,40,56,?\n"
            "اشرح كيف تكيفت مع كل تغيير، الاستراتيجيات، وكيف تتعلم من الأخطاء.")
    },
]

RESULTS: Dict[str, Any] = {}

# helper: call rag_answer and tolerate exceptions

def call_agl(query: str, context: str = "") -> Dict[str, Any]:
    try:
        resp = rag_answer(query, context)
        # normalize
        ans = resp.get("answer") if isinstance(resp, dict) else str(resp)
        engine = resp.get("engine") if isinstance(resp, dict) else "unknown"
        return {"ok": True, "engine": engine, "answer": ans}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main():
    start = time.time()
    out = []
    for item in TEST_PROMPTS:
        print("\n=== Part %s: %s ===" % (item['id'], item['title']))
        sys_query = item['query']
        res = call_agl(sys_query)
        if res.get('ok'):
            print("[engine]", res['engine'])
            print(res['answer'])
        else:
            print("[ERROR]", res.get('error'))
        out.append({"id": item['id'], "title": item['title'], "resp": res})

    RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "ag_test_results.json")
    RESULTS_PATH = os.path.abspath(RESULTS_PATH)
    try:
        os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
        with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
            json.dump({"timestamp": time.time(), "results": out}, f, ensure_ascii=False, indent=2)
        print("\nSaved results to:", RESULTS_PATH)
    except Exception as e:
        print("Failed to save results:", e)

    print("\nTotal elapsed: %.2f seconds" % (time.time() - start))

if __name__ == '__main__':
    main()
