#!/usr/bin/env python3
"""Run a suite of hybrid AGL tests (1..5) and produce a terminal report.

Saves full results to reports/aglh_test_suite_results.json and prints a
concise summary (duration, confidence, per-criterion scores, category).
"""
from __future__ import annotations

import os
import time
import json
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from AGL import create_agl_instance


REPORTS_DIR = Path('reports')
REPORTS_DIR.mkdir(exist_ok=True)
OUT_PATH = REPORTS_DIR / 'aglh_test_suite_results.json'


def build_tests():
    tests = []
    # Test 1
    story = (
        "كان أحمد يلعب في الحديقة. رأى قطة جميلة تلاحق فراشة.\n"
        "ثم سمع صوت بكاء طفل صغير. ترك القطة وركض لمساعدة الطفل.\n"
    )
    q1 = (
        "قصة:\n" + story + "\nالأسئلة:\n"
        "1. لماذا ترك أحمد القطة؟\n"
        "2. ما هي المشاعر المحتملة لأحمد في كل موقف؟\n"
        "3. كيف كان يمكن أن يتصرف بشكل مختلف؟"
    )
    tests.append({'id': 1, 'name': 'الفهم والسياق', 'prompt': q1})

    # Test 2: irrigation system
    reqs = [
        "توفير 30% من المياه",
        "مراعاة أنواع النباتات المختلفة",
        "التكيف مع أحوال الطقس",
        "التكلفة لا تتجاوز 200 دولار"
    ]
    q2 = "المهمة: تصميم نظام ري ذكي لحديقة\nالمتطلبات:\n" + '\n'.join(f'- {r}' for r in reqs) + "\n\nالمطلوب: خطة تنفيذ مفصلة مع مبررات لكل اختيار"
    tests.append({'id': 2, 'name': 'حل المشكلات المعقدة', 'prompt': q2})

    # Test 3: cross-domain
    concept = 'مبدأ حفظ الطاقة: الطاقة لا تفنى ولا تستحدث ولكن تتحول من شكل لآخر'
    q3 = (
        f"تعلم وتطبيق:\nالمفهوم الجديد = \"{concept}\"\n\nالمطلوب:\n1. شرح المبدأ بكلماتك الخاصة\n2. تطبيق المبدأ في مجال الاقتصاد أو العلاقات الاجتماعية\n3. استنتاج قاعدة جديدة بناءً على هذا المبدأ"
    )
    tests.append({'id': 3, 'name': 'التعلم والتبادل بين المجالات', 'prompt': q3})

    # Test 4: creativity
    problem = 'كيف نساعد كبار السن على تذكر تناول الأدوية في أوقاتها؟'
    q4 = (
        f"الإبداع والابتكار:\nالمشكلة = \"{problem}\"\n\nالمطلوب:\n1. 3 أفكار إبداعية لحل المشكلة\n2. اختيار أفضل فكرة وتطويرها\n3. تحديد التحديات وكيفية التغلب عليها"
    )
    tests.append({'id': 4, 'name': 'الإبداع والابتكار', 'prompt': q4})

    # Test 5: strategic planning
    q5 = (
        "التفكير الاستراتيجي:\nالهدف = \"زيادة الوعي البيئي في الحي خلال 6 أشهر\"\n"
        "الميزانية = \"500 دولار\"\nالمشاركون = \"متطوعون من الشباب\"\n\n"
        "المطلوب: خطة استراتيجية شاملة تشمل: مراحل التنفيذ، مؤشرات النجاح، إدارة المخاطر، الاستدامة"
    )
    tests.append({'id': 5, 'name': 'التفكير الاستراتيجي', 'prompt': q5})

    return tests


def score_from_conf(conf: float) -> dict:
    # conf is 0..1, map to 1..10 scale
    val = max(0.0, min(1.0, float(conf or 0.0)))
    base = int(round(val * 10))
    # distribute same base across criteria for now
    return {
        'understanding': base,
        'reasoning': base,
        'creativity': base,
        'integration': base,
        'learning': base,
        'overall_percent': round(val * 100, 1),
        'category': ('ضعيف' if base < 4 else 'مقبول' if base < 6 else 'جيد' if base < 8 else 'ممتاز')
    }


def run_suite():
    agl = create_agl_instance({'operational_mode': 'supervised_autonomy'})
    tests = build_tests()
    results = {'suite': 'aglhybrid_v1', 'timestamp': time.time(), 'tests': []}

    for t in tests:
        print(f"Running test {t['id']}: {t['name']}")
        start = time.time()
        try:
            out = agl.process_complex_problem(t['prompt'], context={'audience': 'evaluation'})
        except Exception as e:
            out = {'ok': False, 'error': str(e)}
        duration = time.time() - start

        # try to extract confidence
        conf = None
        try:
            conf = out.get('confidence_score') or (out.get('solution') or {}).get('confidence') or out.get('confidence')
        except Exception:
            conf = None

        scores = score_from_conf(conf or 0.0)

        results['tests'].append({
            'id': t['id'],
            'name': t['name'],
            'prompt': t['prompt'],
            'duration_seconds': duration,
            'confidence': conf,
            'scores': scores,
            'raw_output': out
        })

        # print per-test summary
        print(f"  duration: {duration:.2f}s  confidence: {scores['overall_percent']}%  category: {scores['category']}")

    # write results
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # print final summary table
    print('\n=== Suite Summary ===')
    for r in results['tests']:
        s = r['scores']
        print(f"Test {r['id']} {r['name']}: {s['overall_percent']}% ({s['category']}) - duration {r['duration_seconds']:.2f}s")

    print(f"\nFull suite results written to: {OUT_PATH}")


if __name__ == '__main__':
    run_suite()
