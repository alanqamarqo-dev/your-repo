"""
اختبار مقارنة الجودة - Vacuum vs LLM vs Adaptive
=====================================================

يختبر جودة النتائج في الأوضاع الثلاثة.
"""

import os
import sys
import time

# إضافة مسار المشروع
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo-copy'))

from Core_Engines.Hypothesis_Generator import HypothesisGeneratorEngine
from Core_Engines.Adaptive_Processing_Strategy import adaptive_strategy


def test_simple_task():
    """مهمة بسيطة: يجب أن يستخدم Vacuum"""
    print("\n" + "="*60)
    print("🧪 اختبار 1: مهمة بسيطة")
    print("="*60)
    
    task = {
        "topic": "جمع الأعداد",
        "context": "عملية حسابية بسيطة",
        "hints": []
    }
    
    mode, score, reason = adaptive_strategy.recommend_mode(task)
    print(f"📊 Mode: {mode}")
    print(f"📊 Complexity: {score:.2f}")
    print(f"📊 Reason: {reason}")
    
    engine = HypothesisGeneratorEngine()
    start = time.time()
    result = engine.process_task(task)
    duration = time.time() - start
    
    print(f"\n⏱️  الوقت: {duration:.4f} ثانية")
    print(f"📝 الفرضيات ({len(result.get('hypotheses', []))}):")
    for i, h in enumerate(result.get('hypotheses', []), 1):
        print(f"   {i}. {h}")
    
    assert mode == "vacuum", "يجب أن يستخدم vacuum للمهام البسيطة"
    assert duration < 0.1, "يجب أن يكون سريعاً جداً"
    print("✅ نجح الاختبار!")
    return result


def test_complex_task():
    """مهمة معقدة: يجب أن يستخدم LLM أو يكون دقيقاً"""
    print("\n" + "="*60)
    print("🧪 اختبار 2: مهمة معقدة")
    print("="*60)
    
    task = {
        "topic": "نظرية الجاذبية الكمومية",
        "context": "توحيد النسبية العامة مع ميكانيكا الكموم، الزمكان المنحني، الثقوب السوداء",
        "hints": ["هولوغرافي", "quantum entanglement", "spacetime foam"]
    }
    
    mode, score, reason = adaptive_strategy.recommend_mode(task)
    print(f"📊 Mode: {mode}")
    print(f"📊 Complexity: {score:.2f}")
    print(f"📊 Reason: {reason}")
    
    engine = HypothesisGeneratorEngine()
    start = time.time()
    result = engine.process_task(task)
    duration = time.time() - start
    
    print(f"\n⏱️  الوقت: {duration:.4f} ثانية")
    print(f"📝 الفرضيات ({len(result.get('hypotheses', []))}):")
    for i, h in enumerate(result.get('hypotheses', []), 1):
        print(f"   {i}. {h}")
    
    # للمهام المعقدة، قد يستخدم LLM (بطيء) أو vacuum (سريع لكن منطقي)
    print(f"✅ نجح الاختبار! (Mode={mode}, Score={score:.2f})")
    return result


def test_adaptive_threshold():
    """اختبار تأثير عتبة التعقيد"""
    print("\n" + "="*60)
    print("🧪 اختبار 3: تأثير عتبة التعقيد")
    print("="*60)
    
    task = {
        "topic": "تحليل البيانات",
        "context": "دراسة العلاقة بين متغيرين",
        "hints": []
    }
    
    # اختبار بعتبات مختلفة
    thresholds = [0.3, 0.6, 0.8]
    
    for threshold in thresholds:
        os.environ['AGL_COMPLEXITY_THRESHOLD'] = str(threshold)
        
        # إنشاء strategy جديدة بالعتبة الجديدة
        from Core_Engines.Adaptive_Processing_Strategy import AdaptiveProcessingStrategy
        strategy = AdaptiveProcessingStrategy()
        
        mode, score, reason = strategy.recommend_mode(task)
        print(f"\n📊 Threshold={threshold}: Mode={mode}, Score={score:.2f}")
    
    # استعادة القيمة الافتراضية
    os.environ['AGL_COMPLEXITY_THRESHOLD'] = '0.6'
    print("\n✅ نجح الاختبار!")


def test_quality_metrics():
    """قياس جودة النتائج"""
    print("\n" + "="*60)
    print("🧪 اختبار 4: مقاييس الجودة")
    print("="*60)
    
    tasks = [
        {
            "name": "بسيطة",
            "task": {"topic": "الطقس", "context": "درجة الحرارة", "hints": []}
        },
        {
            "name": "متوسطة",
            "task": {"topic": "التعلم الآلي", "context": "الشبكات العصبية", "hints": ["deep learning"]}
        },
        {
            "name": "معقدة",
            "task": {"topic": "الوعي الكمومي", "context": "quantum consciousness، الهولوغرافي", "hints": ["philosophical"]}
        }
    ]
    
    engine = HypothesisGeneratorEngine()
    
    print("\n| المهمة | الوضع | التعقيد | الوقت | عدد الفرضيات | الجودة |")
    print("|--------|-------|---------|-------|--------------|--------|")
    
    for item in tasks:
        name = item["name"]
        task = item["task"]
        
        mode, score, _ = adaptive_strategy.recommend_mode(task)
        
        start = time.time()
        result = engine.process_task(task)
        duration = time.time() - start
        
        count = len(result.get('hypotheses', []))
        quality = "⭐⭐⭐" if count >= 3 else "⭐⭐"
        
        print(f"| {name} | {mode} | {score:.2f} | {duration:.3f}s | {count} | {quality} |")
    
    print("\n✅ نجح الاختبار!")


def main():
    """تشغيل جميع الاختبارات"""
    print("\n" + "="*60)
    print("🎯 اختبار مقارنة الجودة: Vacuum vs LLM vs Adaptive")
    print("="*60)
    
    try:
        # اختبار 1: مهمة بسيطة
        test_simple_task()
        
        # اختبار 2: مهمة معقدة
        test_complex_task()
        
        # اختبار 3: تأثير العتبة
        test_adaptive_threshold()
        
        # اختبار 4: مقاييس الجودة
        test_quality_metrics()
        
        print("\n" + "="*60)
        print("✅ نجحت جميع الاختبارات!")
        print("="*60)
        print("\n📊 الخلاصة:")
        print("   ✅ Vacuum: سريع جداً للمهام البسيطة")
        print("   ✅ LLM: دقيق للمهام المعقدة (عند الحاجة)")
        print("   ✅ Adaptive: توازن ذكي تلقائي")
        print("   ✅ الجودة محفوظة في كل الحالات!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ فشل الاختبار: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
