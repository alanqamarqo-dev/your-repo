"""
اختبار سريع للتشغيل المتوازي - Test Parallel Engine Executor
===============================================================

يختبر ParallelEngineExecutor مع 5 محركات بسيطة لقياس التحسين.
"""

import asyncio
import time
import sys
import os

# Setup path
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.join(root_dir, 'repo-copy')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from Core_Engines.Parallel_Engine_Executor import ParallelEngineExecutor


async def test_parallel_execution():
    print("\n" + "="*70)
    print("🧪 اختبار التشغيل المتوازي للمحركات")
    print("="*70)
    
    # تحديد المحركات للاختبار
    engines = {
        "Mathematical_Brain": "Core_Engines.Mathematical_Brain.MathematicalBrain",
        "Causal_Graph": "Core_Engines.Causal_Graph.CausalGraphEngine",
        "Creative_Innovation": "Core_Engines.Creative_Innovation.CreativeInnovationEngine",
        "HYPOTHESIS_GENERATOR": "Core_Engines.HYPOTHESIS_GENERATOR.HypothesisGeneratorEngine",
        "Meta_Learning": "Core_Engines.Meta_Learning.MetaLearningEngine",
    }
    
    task = "What is 2+2? Provide a brief explanation."
    metadata = {"test": True, "priority": "normal"}
    
    executor = ParallelEngineExecutor(max_workers=4)
    
    # ==================== 1. التشغيل المتسلسل ====================
    print("\n" + "-"*70)
    print("1️⃣ التشغيل المتسلسل (Sequential Execution)")
    print("-"*70)
    
    seq_start = time.time()
    seq_result = await executor.run_engines_sequential(engines, task, metadata)
    seq_duration = time.time() - seq_start
    
    print(f"\n📊 النتائج المتسلسلة:")
    print(f"   - الوقت الإجمالي: {seq_duration:.2f} ثانية")
    print(f"   - المحركات الناجحة: {seq_result['success_count']}/{seq_result['engines_count']}")
    print(f"   - الأخطاء: {seq_result['error_count']}")
    
    # ==================== 2. التشغيل المتوازي ====================
    print("\n" + "-"*70)
    print("2️⃣ التشغيل المتوازي (Parallel Execution)")
    print("-"*70)
    
    par_start = time.time()
    par_result = await executor.run_engines_parallel(engines, task, metadata)
    par_duration = time.time() - par_start
    
    print(f"\n📊 النتائج المتوازية:")
    print(f"   - الوقت الإجمالي: {par_duration:.2f} ثانية")
    print(f"   - المحركات الناجحة: {par_result['success_count']}/{par_result['engines_count']}")
    print(f"   - الأخطاء: {par_result['error_count']}")
    print(f"   - العمليات المستخدمة: {par_result['workers_used']}")
    
    # ==================== 3. المقارنة ====================
    print("\n" + "="*70)
    print("📊 المقارنة النهائية")
    print("="*70)
    
    speedup = seq_duration / max(par_duration, 0.001)
    time_saved = seq_duration - par_duration
    efficiency = (speedup / par_result['workers_used']) * 100
    
    print(f"\n🔢 إحصائيات التحسين:")
    print(f"   التشغيل المتسلسل:    {seq_duration:.2f} ثانية")
    print(f"   التشغيل المتوازي:     {par_duration:.2f} ثانية")
    print(f"   🚀 معامل التسريع:      {speedup:.2f}×")
    print(f"   ⏱️  الوقت الموفَّر:      {time_saved:.2f} ثانية ({time_saved/seq_duration*100:.1f}%)")
    print(f"   ⚡ الكفاءة:             {efficiency:.1f}%")
    print(f"   💻 النوى المستخدمة:    {par_result['workers_used']}")
    
    # ==================== 4. التوقعات للمهام الكبيرة ====================
    print("\n" + "="*70)
    print("📈 توقعات للمهمات الكبيرة")
    print("="*70)
    
    # مهمة Quantum Relativity Unification أخذت 443 ثانية مع ~50 محرك
    original_large_task_time = 443  # ثانية
    engines_in_large_task = 50
    
    # حساب الوقت المتوقع مع التوازي
    estimated_parallel_time = original_large_task_time / speedup
    estimated_time_saved = original_large_task_time - estimated_parallel_time
    
    print(f"\n🌌 مهمة Quantum Relativity Unification:")
    print(f"   الوقت الأصلي (متسلسل):     {original_large_task_time:.0f} ثانية (~7 دقائق)")
    print(f"   الوقت المتوقع (متوازي):    {estimated_parallel_time:.0f} ثانية (~{estimated_parallel_time/60:.1f} دقيقة)")
    print(f"   ⚡ التوفير المتوقع:         {estimated_time_saved:.0f} ثانية (~{estimated_time_saved/60:.1f} دقيقة)")
    print(f"   🚀 معامل التسريع:          {speedup:.2f}×")
    
    print("\n" + "="*70)
    print("✅ الاختبار اكتمل بنجاح!")
    print("="*70 + "\n")
    
    return {
        "sequential_time": seq_duration,
        "parallel_time": par_duration,
        "speedup": speedup,
        "efficiency": efficiency,
        "time_saved": time_saved,
        "workers": par_result['workers_used']
    }


if __name__ == "__main__":
    result = asyncio.run(test_parallel_execution())
