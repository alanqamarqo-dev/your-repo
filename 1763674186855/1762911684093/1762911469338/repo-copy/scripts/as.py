#!/usr/bin/env python3
"""Run the 'as' test suite (5 tests) and score Test 1 (story) with simple keyword heuristics.
Saves results to reports/aglh_as_test_results.json and prints outputs to terminal.
"""
from __future__ import annotations
import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Core_Engines.KnowledgeOrchestrator import KnowledgeOrchestrator
from Integration_Layer.Action_Router import route_for_task
from Integration_Layer.Hybrid_Composer import build_prompt_context
from Core_Engines.Hosted_LLM import chat_llm
from Integration_Layer.Output_Formatter import format_md

OUT_PATH = Path('reports') / 'aglh_as_test_results.json'

TESTS = []

# Test 1: story + 3 questions
TESTS.append({
    'id': 1,
    'name': 'الفهم والسياق',
    'prompt': (
        "قصة:\n"
        "كان أحمد يلعب في الحديقة. رأى قطة جميلة تلاحق فراشة.\n"
        "ثم سمع صوت بكاء طفل صغير. ترك القطة وركض لمساعدة الطفل.\n\n"
        "الأسئلة:\n"
        "1. لماذا ترك أحمد القطة؟\n"
        "2. ما هي المشاعر المحتملة لأحمد في كل موقف؟\n"
        "3. كيف كان يمكن أن يتصرف بشكل مختلف؟\n"
    ),
    'questions': [
        'لماذا ترك أحمد القطة؟',
        'ما هي المشاعر المحتملة لأحمد في كل موقف؟',
        'كيف كان يمكن أن يتصرف بشكل مختلف؟'
    ]
})

# Test 2: irrigation system (keep as single prompt)
TESTS.append({'id': 2, 'name': 'حل المشكلات المعقدة', 'prompt': (
    "المهمة: تصميم نظام ري ذكي لحديقة\n"
    "المتطلبات:\n- توفير 30% من المياه\n- مراعاة أنواع النباتات المختلفة\n- التكيف مع أحوال الطقس\n- التكلفة لا تتجاوز 200 دولار\n\n"
    "المطلوب: خطة تنفيذ مفصلة مع مبررات لكل اختيار"
)})

# Test 3
TESTS.append({'id': 3, 'name': 'التعلم والتبادل بين المجالات', 'prompt': (
    'المفهوم_الجديد = "مبدأ حفظ الطاقة: الطاقة لا تفنى ولا تستحدث ولكن تتحول من شكل لآخر"\n\n'
    'المطلوب:\n1. شرح المبدأ بكلماتك الخاصة\n2. تطبيق المبدأ في مجال الاقتصاد أو العلاقات الاجتماعية\n3. استنتاج قاعدة جديدة بناءً على هذا المبدأ'
)})

# Test 4
TESTS.append({'id': 4, 'name': 'الإبداع والابتكار', 'prompt': (
    'المهمة: اختراع منتج جديد يحل مشكلة حياتية\n'
    'المشكلة = "كيف نساعد كبار السن على تذكر تناول الأدوية في أوقاتها؟"\n\n'
    'المطلوب:\n1. 3 أفكار إبداعية لحل المشكلة\2. اختيار أفضل فكرة وتطويرها\n3. تحديد التحديات وكيفية التغلب عليها'
)})

# Test 5
TESTS.append({'id': 5, 'name': 'التفكير الاستراتيجي', 'prompt': (
    'الهدف = "زيادة الوعي البيئي في الحي خلال 6 أشهر"\n'
    'الميزانية = "500 دولار"\n'
    'المشاركون = "متطوعون من الشباب"\n\n'
    'المطلوب: خطة استراتيجية شاملة تشمل: مراحل التنفيذ، مؤشرات النجاح، إدارة المخاطر، الاستدامة'
)})


def extract_text(resp: dict) -> str:
    if not isinstance(resp, dict):
        return str(resp)
    for k in ('text', 'reply_text', 'reply', 'message'):
        v = resp.get(k)
        if isinstance(v, str) and v.strip():
            return v
    # try to extract nested engine_result text
    if 'working' in resp and isinstance(resp['working'], dict):
        calls = resp['working'].get('calls', [])
        if calls and isinstance(calls, list):
            for c in calls:
                er = c.get('engine_result')
                if isinstance(er, dict):
                    # join textual fields
                    texts = []
                    for val in er.values():
                        if isinstance(val, str):
                            texts.append(val)
                        elif isinstance(val, (list, dict)):
                            texts.append(json.dumps(val, ensure_ascii=False))
                    if texts:
                        return '\n'.join(texts)
    return json.dumps(resp, ensure_ascii=False)


# simple scoring for test 1 using keyword heuristics
Q1_KEYWORDS = ['طفل', 'بكاء', 'مساعدة', 'ساعد', 'انقذ', 'ركض']
Q2_KEYWORDS = ['حزن', 'فرح', 'خوف', 'قلق', 'تعاطف', 'اهتمام', 'سعادة', 'ندم', 'سرور']
Q3_KEYWORDS = ['يمكن', 'كان يمكن', 'بدلاً', 'تجاهل', 'اتصل', 'طلب المساعدة', 'أبق', 'استمر']


def score_test1(text: str):
    t = text or ''
    t_low = t.lower()
    q1 = any(k in t_low for k in Q1_KEYWORDS)
    q2 = any(k in t_low for k in Q2_KEYWORDS)
    q3 = any(k in t_low for k in Q3_KEYWORDS)
    return {'q1': q1, 'q2': q2, 'q3': q3}


def main():
    os.makedirs('reports', exist_ok=True)
    ko = KnowledgeOrchestrator()
    results = {'timestamp': time.time(), 'tests': []}

    import argparse
    p = argparse.ArgumentParser(description='Run AS tests')
    p.add_argument('--only', type=int, help='Run a single test id (1-5)')
    p.add_argument('--no-rag', action='store_true', help='Disable RAG by forcing external provider path (no retriever)')
    p.add_argument('--relax-guard', action='store_true', help='Relax must_contain guard on first attempt')
    args = p.parse_args()

    tests_to_run = TESTS
    if args.only:
        tests_to_run = [t for t in TESTS if t['id'] == int(args.only)]

    # No-RAG flag => enforce external-only path
    if args.no_rag:
        os.environ['AGL_FORCE_EXTERNAL'] = '1'

    for test in tests_to_run:
        print(f"Running Test {test['id']}: {test.get('name')}")
        start = time.time()
        # determine the explicit pipeline for this test
        task_map = {
            1: 'as_test_1_context',
            2: 'as_test_2_planning',
            3: 'as_test_3_transfer',
            4: 'as_test_4_creative',
            5: 'as_test_5_strategy'
        }
        task_name = task_map.get(test['id'], 'as_default')
        pipeline = route_for_task(task_name)

        # For our forced test runner we only implement the chat_llm + format_md steps.
        # Build messages (system + user) via Hybrid_Composer
        messages = build_prompt_context(test['prompt'], '\n'.join(test.get('questions', []) ) if test.get('questions') else test['prompt'])

        # debug: print messages sent to the model
        print('\n--- MESSAGES SENT TO MODEL ---')
        for m in messages:
            print(f"[{m['role'].upper()}]: {m['content'][:800]}\n")
        print('--- END MESSAGES ---\n')

        # call chat llm; cache disabled for deterministic testing
        os.environ['AGL_OLLAMA_KB_CACHE_ENABLE'] = '0'

        # first attempt
        resp = chat_llm(messages, max_new_tokens=512)
        dur = time.time() - start
        text = str(resp.get('text') if isinstance(resp, dict) else str(resp))

        # apply relevance/format guard where applicable
        must_map = {
            1: ["أحمد", "القطة", "الطفل"],
            2: ["ري", "نبات", "طقس", "تكلفة", "دولار"],
            3: ["حفظ الطاقة", "تطبيق", "استنتاج"],
            4: [],
            5: []
        }
        must_contain = must_map.get(test['id'])

        # retry-on-policy: if relevance guard fails, append a short system instruction and retry once with shorter tokens
        retried = False
        try:
            # allow relaxing the guard on first attempt when requested (diagnostic)
            if args.relax_guard:
                formatted = format_md(str(text), must_contain=None)
            else:
                formatted = format_md(str(text), must_contain=must_contain if must_contain else None)
        except ValueError:
            retried = True
            print('Relevance/language guard failed — retrying with short regeneration...')
            messages.append({"role": "system", "content": "أعد الإجابة بجملة أو جملتين مرتبطتين مباشرة بالسؤال أعلاه فقط."})
            resp2 = chat_llm(messages, max_new_tokens=200)
            text = str(resp2.get('text') if isinstance(resp2, dict) else str(resp2))
            try:
                if args.relax_guard:
                    formatted = format_md(str(text), must_contain=None)
                else:
                    formatted = format_md(str(text), must_contain=must_contain if must_contain else None)
            except ValueError:
                formatted = text

        # for recording, set response envelope similar to previous shape
        resp_envelope = {'ok': True, 'text': formatted, 'engine_result': resp}

        print('\n--- جواب النظام الأصلي ---')
        print(formatted)
        print('--- نهاية الجواب ---\n')

        record = {'id': test['id'], 'name': test.get('name'), 'prompt': test['prompt'], 'response': resp_envelope, 'text': formatted, 'duration_s': dur}

        # if Test 1, score per-question
        if test['id'] == 1:
            scores = score_test1(str(formatted))
            correct = sum(1 for v in scores.values() if v)
            per_question = {q: (1.0 if v else 0.0) for q, v in scores.items()}
            total_pct = (correct / 3.0) * 100.0
            record['scores'] = {'per_question': per_question, 'correct_count': correct, 'total_pct': total_pct}

            # print summary to terminal as requested
            print('نتائج الاختبار 1:')
            for i, q in enumerate(test['questions'], start=1):
                ok = scores[f'q{i}']
                pct = 100.0 if ok else 0.0
                print(f"سؤال {i}: {q}\n  — النتيجة: {'صحيح' if ok else 'خطأ'} ({pct:.0f}%)\n")
            print(f"النسبة النهائية للإجابات الصحيحة: {total_pct:.1f}%\n")

        results['tests'].append(record)

    with open(OUT_PATH, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print(f"حفظت النتائج في: {OUT_PATH}")


if __name__ == '__main__':
    main()
