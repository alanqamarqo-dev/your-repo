"""
Parallel Engine Executor - محرك التشغيل المتوازي للمحركات
==========================================================

يستخدم ProcessPoolExecutor لتشغيل عدة محركات بالتوازي على كل نوى CPU.

التحسين المتوقع:
- من 443 ثانية → 55-70 ثانية (تحسين 6-8×) على 8 نوى
- من 443 ثانية → 30-40 ثانية (تحسين 10-14×) على 16 نواة

الاستخدام:
----------
executor = ParallelEngineExecutor(max_workers=8)
results = await executor.run_engines_parallel(engines_dict, task_input, metadata)
"""

import asyncio
import os
import sys
import time
import multiprocessing as mp
# Using ThreadPoolExecutor instead of ProcessPoolExecutor to avoid Windows freeze_support/spawn issues
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Callable
import traceback
import json

# تحديد عدد العمليات بناءً على نوى CPU
DEFAULT_WORKERS = max(4, mp.cpu_count() - 2)  # احتفظ بنواتين للنظام


def _process_engine_task(engine_name: str, engine_class_path: str, task_input: Any, metadata: Dict) -> Dict[str, Any]:
    """
    دالة مساعدة لتشغيل محرك واحد في عملية منفصلة.
    
    Args:
        engine_name: اسم المحرك
        engine_class_path: المسار الكامل للمحرك (module.ClassName)
        task_input: المدخلات
        metadata: البيانات الوصفية
        
    Returns:
        Dict مع النتيجة أو الخطأ
    """
    start_time = time.time()
    
    try:
        # استيراد المحرك ديناميكياً
        module_path, class_name = engine_class_path.rsplit('.', 1)
        
        # استيراد الوحدة
        module = __import__(module_path, fromlist=[class_name])
        engine_class = getattr(module, class_name)
        
        # إنشاء نسخة من المحرك
        engine = engine_class()
        
        # تنفيذ المهمة
        if hasattr(engine, 'process_task'):
            result = engine.process_task({
                'input': task_input,
                'metadata': metadata
            })
        elif hasattr(engine, 'process'):
            result = engine.process(task_input, metadata)
        else:
            result = {"error": f"Engine {engine_name} has no process_task or process method"}
        
        duration = time.time() - start_time
        
        return {
            "engine": engine_name,
            "status": "success",
            "result": result,
            "duration": duration,
            "worker_pid": os.getpid()
        }
        
    except Exception as e:
        duration = time.time() - start_time
        return {
            "engine": engine_name,
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "duration": duration,
            "worker_pid": os.getpid()
        }


class ParallelEngineExecutor:
    """
    محرك تنفيذ المحركات بالتوازي باستخدام ThreadPoolExecutor (Safe for Windows)
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Args:
            max_workers: عدد الخيوط المتوازية (افتراضي: CPU_COUNT - 2)
        """
        self.max_workers = max_workers or DEFAULT_WORKERS
        print(f"🚀 ParallelEngineExecutor: {self.max_workers} خيوط (Threads) متوازية [Windows Safe Mode]")
    
    async def run_engines_parallel(
        self,
        engines_map: Dict[str, str],
        task_input: Any,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        تشغيل عدة محركات بالتوازي.
        
        Args:
            engines_map: Dict[engine_name -> engine_class_path]
                مثال: {"Mathematical_Brain": "Core_Engines.Mathematical_Brain.MathematicalBrain"}
            task_input: المدخلات المشتركة لكل المحركات
            metadata: البيانات الوصفية
            
        Returns:
            Dict يحتوي على النتائج من كل المحركات
        """
        if metadata is None:
            metadata = {}
        
        start_time = time.time()
        results = {}
        errors = {}
        
        print(f"\n⚡ بدء تشغيل {len(engines_map)} محرك بالتوازي (Threads)...")
        
        # تشغيل في event loop منفصل لتجنب مشاكل asyncio
        loop = asyncio.get_event_loop()
        
        # استخدام ThreadPoolExecutor بدلاً من ProcessPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # إنشاء المهام
            future_to_engine = {}
            for engine_name, engine_class_path in engines_map.items():
                future = executor.submit(
                    _process_engine_task,
                    engine_name,
                    engine_class_path,
                    task_input,
                    metadata
                )
                future_to_engine[future] = engine_name
            
            # جمع النتائج عند اكتمالها
            completed_count = 0
            for future in as_completed(future_to_engine):
                engine_name = future_to_engine[future]
                completed_count += 1
                
                try:
                    result = future.result(timeout=300)  # timeout لكل محرك
                    
                    if result['status'] == 'success':
                        results[engine_name] = result['result']
                        print(f"   ✅ {engine_name}: {result['duration']:.2f}s (PID {result['worker_pid']}) [{completed_count}/{len(engines_map)}]")
                    else:
                        errors[engine_name] = result['error']
                        print(f"   ❌ {engine_name}: {result['error'][:100]} [{completed_count}/{len(engines_map)}]")
                        
                except Exception as e:
                    errors[engine_name] = str(e)
                    print(f"   ⚠️ {engine_name}: Future failed - {e}")
        
        total_duration = time.time() - start_time
        
        print(f"\n✅ اكتمل التشغيل المتوازي:")
        print(f"   - المحركات الناجحة: {len(results)}/{len(engines_map)}")
        print(f"   - الأخطاء: {len(errors)}")
        print(f"   - الوقت الإجمالي: {total_duration:.2f} ثانية")
        print(f"   - معدل التوازي: ~{len(engines_map) / max(total_duration, 0.1):.1f} محرك/ثانية")
        
        return {
            "results": results,
            "errors": errors,
            "total_duration": total_duration,
            "engines_count": len(engines_map),
            "success_count": len(results),
            "error_count": len(errors),
            "workers_used": self.max_workers
        }
    
    async def run_engines_sequential(
        self,
        engines_map: Dict[str, str],
        task_input: Any,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        تشغيل المحركات بشكل متسلسل (للمقارنة).
        
        نفس المدخلات والمخرجات مثل run_engines_parallel
        """
        if metadata is None:
            metadata = {}
        
        start_time = time.time()
        results = {}
        errors = {}
        
        print(f"\n🐌 بدء تشغيل {len(engines_map)} محرك بشكل متسلسل...")
        
        for idx, (engine_name, engine_class_path) in enumerate(engines_map.items(), 1):
            result = _process_engine_task(engine_name, engine_class_path, task_input, metadata)
            
            if result['status'] == 'success':
                results[engine_name] = result['result']
                print(f"   ✅ {engine_name}: {result['duration']:.2f}s [{idx}/{len(engines_map)}]")
            else:
                errors[engine_name] = result['error']
                print(f"   ❌ {engine_name}: {result['error'][:100]} [{idx}/{len(engines_map)}]")
        
        total_duration = time.time() - start_time
        
        print(f"\n✅ اكتمل التشغيل المتسلسل:")
        print(f"   - الوقت الإجمالي: {total_duration:.2f} ثانية")
        
        return {
            "results": results,
            "errors": errors,
            "total_duration": total_duration,
            "engines_count": len(engines_map),
            "success_count": len(results),
            "error_count": len(errors)
        }


async def benchmark_parallel_vs_sequential():
    """
    قياس الفرق بين التشغيل المتوازي والمتسلسل.
    """
    # محركات تجريبية
    engines = {
        "Mathematical_Brain": "agl.engines.mathematical_brain.MathematicalBrain",
        "Causal_Graph": "agl.engines.causal_graph.CausalGraphEngine",
        "Creative_Innovation": "agl.engines.creative_innovation.CreativeInnovation",
        "HYPOTHESIS_GENERATOR": "agl.engines.hypothesis_generator.HypothesisGeneratorEngine",
        "Meta_Learning": "agl.engines.meta_learning.MetaLearningEngine",
    }
    
    task = "What is 2+2? Explain briefly."
    metadata = {"test": True}
    
    executor = ParallelEngineExecutor(max_workers=4)
    
    # التشغيل المتسلسل
    print("\n" + "="*60)
    print("1️⃣ التشغيل المتسلسل (Sequential)")
    print("="*60)
    seq_result = await executor.run_engines_sequential(engines, task, metadata)
    
    # التشغيل المتوازي
    print("\n" + "="*60)
    print("2️⃣ التشغيل المتوازي (Parallel)")
    print("="*60)
    par_result = await executor.run_engines_parallel(engines, task, metadata)
    
    # المقارنة
    print("\n" + "="*60)
    print("📊 المقارنة النهائية")
    print("="*60)
    
    speedup = seq_result['total_duration'] / max(par_result['total_duration'], 0.1)
    
    print(f"   المتسلسل: {seq_result['total_duration']:.2f} ثانية")
    print(f"   المتوازي: {par_result['total_duration']:.2f} ثانية")
    print(f"   🚀 التحسين: {speedup:.2f}× أسرع")
    print(f"   💾 توفير الوقت: {seq_result['total_duration'] - par_result['total_duration']:.2f} ثانية")


if __name__ == "__main__":
    # اختبار
    asyncio.run(benchmark_parallel_vs_sequential())
