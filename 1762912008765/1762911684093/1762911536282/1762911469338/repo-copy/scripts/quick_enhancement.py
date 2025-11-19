# -*- coding: utf-8 -*-
"""Quick enhancement runner: generate many enriched events, add to LTM, export, reindex, and run quality tests."""
import sys
sys.path.insert(0, r'D:\AGL\repo-copy')

from scripts.enrich_memory_data import create_massive_enriched_events
from Core_Memory.bridge_singleton import get_bridge
from scripts.test_search_quality import test_search_improvements, measure_improvement


def execute_quick_enhancement(target_count: int = 2000):
    bridge = get_bridge()

    print("🎯 بدء التحسين السريع...")

    # 1. إنشاء الأحداث
    print(f"1. إنشاء {target_count} حدث غني...")
    new_events = create_massive_enriched_events(target_count)

    for event in new_events:
        bridge.ltm[event['id']] = event

    print(f"   ✅ تم إضافة {len(new_events)} حدث جديد إلى الذاكرة (LT M)")

    # 2. تصدير إلى DB
    print("2. تصدير إلى قاعدة البيانات...")
    try:
        exported = bridge.export_ltm_to_db()
        print(f"   ✅ تم تصدير {exported} حدث إلى قاعدة البيانات")
    except Exception as e:
        print('   ❌ خطأ أثناء التصدير:', e)

    # 3. إعادة الفهرسة
    print("3. إعادة الفهرسة (قد تأخذ وقتًا)...")
    try:
        indexed_count = bridge.build_semantic_index()
        print(f"   ✅ تم فهرسة {indexed_count} مستند")
    except Exception as e:
        print('   ❌ خطأ أثناء إعادة الفهرسة:', e)

    # 4. اختبار الجودة
    print("4. اختبار جودة البحث المحسن...")
    try:
        test_search_improvements()
        avg_score = measure_improvement()
        print(f"\n🎉 التحسين السريع اكتمل! متوسط درجة التحسن: {avg_score:.3f}")
    except Exception as e:
        print('   ❌ خطأ أثناء اختبار الجودة:', e)

    return True


if __name__ == '__main__':
    execute_quick_enhancement(2000)
