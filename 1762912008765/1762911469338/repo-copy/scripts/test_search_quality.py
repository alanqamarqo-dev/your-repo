# -*- coding: utf-8 -*-
import os
from Core_Memory.bridge_singleton import get_bridge

# allow overriding search/top-k via env var
_AGL_ROUTER_RESULT_LIMIT = int(os.environ.get('AGL_ROUTER_RESULT_LIMIT', '8'))


def test_search_improvements():
    bridge = get_bridge()

    test_queries = [
        "نفط أسعار 2020",
        "ذكاء اصطناعي تعلم آلة",
        "اقتصاد تضخم أسواق",
        "صحة جائحة كوفيد",
        "طاقة متجددة مستدامة",
        "تكنولوجيا بلوك تشين",
        "طب أمراض مزمنة",
        "هندسة مواد ذكية"
    ]

    print("=== اختبار جودة البحث بعد التحسينات ===")

    for query in test_queries:
        print(f"\nالاستعلام: '{query}'")
        results = bridge.semantic_search(query, top_k=_AGL_ROUTER_RESULT_LIMIT)

        if results:
            for i, result in enumerate(results):
                text = result.get('payload', {}).get('text', '')
                if len(text) > 100:
                    text = text[:100] + '...'
                score = result.get('_score', 0)
                category = result.get('payload', {}).get('category', 'غير مصنف')
                print(f"  {i+1}. [{category}] score: {score:.3f} - {text}")
        else:
            print("  ❌ لا توجد نتائج")

    return len(test_queries)


def measure_improvement():
    bridge = get_bridge()

    benchmark_queries = {
        "نفط": ["نفط", "طاقة", "أسعار", "2020"],
        "ذكاء اصطناعي": ["ذكاء", "اصطناعي", "تعلم", "آلة"],
        "اقتصاد": ["اقتصاد", "تضخم", "أسواق", "استثمار"]
    }

    improvement_scores = []

    for query, expected_keywords in benchmark_queries.items():
        results = bridge.semantic_search(query, top_k=_AGL_ROUTER_RESULT_LIMIT)
        match_score = 0

        for result in results:
            text = result.get('payload', {}).get('text', '').lower()
            matches = sum(1 for keyword in expected_keywords if keyword in text)
            match_score += matches / len(expected_keywords)

        if results:
            match_score /= len(results)
            improvement_scores.append(match_score)
            print(f"استعلام '{query}': درجة المطابقة = {match_score:.3f}")

    avg_score = sum(improvement_scores) / len(improvement_scores) if improvement_scores else 0
    print(f"\n🎯 متوسط درجة التحسن: {avg_score:.3f}")

    return avg_score


if __name__ == '__main__':
    test_search_improvements()
    measure_improvement()
