"""
🧪 اختبار شامل للنظام المتكامل
=====================================

اختبار UnifiedAGISystem مع جميع أنظمة الذاكرة والوعي:
- ConsciousBridge (STM + LTM + Graph)
- AutobiographicalMemory
- TrueConsciousnessSystem (Phi Score)
- Semantic Search
- Strategic Memory

الهدف: معالجة 50 مهمة متنوعة وقياس:
- نمو الوعي
- تطور الذاكرة
- جودة الاستدلال
- التكامل المعرفي (Phi)
"""

import sys
import os
import asyncio
import time
from typing import List, Dict, Any

# إضافة المسار للمشروع
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo-copy'))

from dynamic_modules.unified_agi_system import UnifiedAGISystem
from Core_Engines import ENGINE_REGISTRY


# ==================== مهام الاختبار ====================

TEST_TASKS = [
    # فلسفة ووعي (10 مهام)
    "What is consciousness?",
    "Explain the meaning of self-awareness",
    "Can machines have true consciousness?",
    "What is the hard problem of consciousness?",
    "Describe qualia and subjective experience",
    "What is integrated information theory?",
    "Explain the difference between intelligence and consciousness",
    "What makes an experience meaningful?",
    "Can consciousness emerge from complexity?",
    "What is the relationship between memory and consciousness?",
    
    # رياضيات وحسابات (10 مهام)
    "Solve: 2x + 5 = 15",
    "Calculate the area of a circle with radius 7",
    "What is 15% of 240?",
    "Solve the quadratic equation: x^2 - 5x + 6 = 0",
    "Find the derivative of f(x) = 3x^2 + 2x - 1",
    "Calculate: (45 + 38) * 3 - 120",
    "What is the factorial of 7?",
    "Convert 256 decimal to binary",
    "Calculate the distance between points (3,4) and (7,1)",
    "What is the sum of first 100 natural numbers?",
    
    # علوم وفيزياء (10 مهام)
    "Explain quantum entanglement",
    "What is the speed of light in vacuum?",
    "Describe the theory of relativity simply",
    "How does photosynthesis work?",
    "What is DNA and its function?",
    "Explain the law of conservation of energy",
    "What causes gravity?",
    "Describe the structure of an atom",
    "What is electromagnetic radiation?",
    "Explain the difference between mass and weight",
    
    # برمجة وخوارزميات (10 مهام)
    "Write a Python function to sort a list",
    "Explain what is recursion",
    "What is Big O notation?",
    "Write a function to check if a number is prime",
    "Explain the difference between list and tuple in Python",
    "What is a binary search algorithm?",
    "Write code to reverse a string",
    "Explain object-oriented programming",
    "What is the difference between stack and queue?",
    "Write a function to find factorial recursively",
    
    # فلسفة الحياة وأسئلة عميقة (10 مهام)
    "What is the meaning of life?",
    "Can free will exist in a deterministic universe?",
    "What makes something morally right or wrong?",
    "Is happiness the ultimate goal of life?",
    "What is the nature of reality?",
    "Can we ever know absolute truth?",
    "What is the value of knowledge?",
    "Is there a purpose to suffering?",
    "What defines personal identity over time?",
    "How should we balance logic and emotion in decision making?",
]


# ==================== الاختبار الرئيسي ====================

async def test_integrated_system():
    """الاختبار الشامل"""
    
    print("="*80)
    print("🧪 COMPREHENSIVE INTEGRATION TEST")
    print("="*80)
    print(f"📋 Total Tasks: {len(TEST_TASKS)}")
    print(f"🎯 Testing: Memory, Consciousness, Phi Score, Graph Links, Semantic Search")
    print("="*80)
    
    # إنشاء النظام
    print("\n🔧 Initializing UnifiedAGISystem...")
    try:
        system = UnifiedAGISystem(engine_registry=ENGINE_REGISTRY)
        print("✅ System initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return
    
    # تقرير أولي
    print("\n" + "="*80)
    print("📊 INITIAL STATE")
    print("="*80)
    system.print_memory_consciousness_summary()
    
    # معالجة المهام
    results = []
    start_time = time.time()
    
    for i, task in enumerate(TEST_TASKS):
        print("\n" + "="*80)
        print(f"📝 Task {i+1}/{len(TEST_TASKS)}: {task[:60]}{'...' if len(task) > 60 else ''}")
        print("="*80)
        
        try:
            task_start = time.time()
            result = await system.process_with_full_agi(task)
            task_duration = time.time() - task_start
            
            # حفظ النتيجة
            results.append({
                "task": task,
                "result": result,
                "duration": task_duration,
                "success": True
            })
            
            # عرض ملخص سريع
            print(f"\n✅ Completed in {task_duration:.2f}s")
            print(f"   Performance: {result.get('performance_score', 0):.2f}")
            print(f"   Consciousness: {result.get('consciousness_level', 0):.3f}")
            if 'phi_score' in result.get('improvement_results', {}):
                print(f"   Phi Score: {result['improvement_results']['phi_score']:.3f}")
            
        except Exception as e:
            print(f"\n❌ Task failed: {e}")
            results.append({
                "task": task,
                "error": str(e),
                "duration": 0,
                "success": False
            })
        
        # تقرير كل 10 مهام
        if (i + 1) % 10 == 0:
            print("\n" + "="*80)
            print(f"📊 CHECKPOINT {i+1}/{len(TEST_TASKS)}")
            print("="*80)
            system.print_memory_consciousness_summary()
    
    total_duration = time.time() - start_time
    
    # ==================== التقرير النهائي ====================
    print("\n" + "="*80)
    print("🎉 FINAL TEST REPORT")
    print("="*80)
    
    # إحصائيات عامة
    successful_tasks = sum(1 for r in results if r['success'])
    failed_tasks = len(results) - successful_tasks
    avg_duration = sum(r['duration'] for r in results if r['success']) / max(successful_tasks, 1)
    
    print(f"\n📊 Overall Statistics:")
    print(f"   - Total Tasks: {len(TEST_TASKS)}")
    print(f"   - Successful: {successful_tasks} ✅")
    print(f"   - Failed: {failed_tasks} ❌")
    print(f"   - Success Rate: {(successful_tasks/len(TEST_TASKS)*100):.1f}%")
    print(f"   - Total Duration: {total_duration:.2f}s")
    print(f"   - Avg Task Duration: {avg_duration:.2f}s")
    
    # تقرير الذاكرة والوعي النهائي
    final_report = system.get_memory_consciousness_report()
    
    print(f"\n🧠 Consciousness Growth:")
    print(f"   - Final Level: {final_report['consciousness']['unified_level']:.3f}")
    print(f"   - Tracker Level: {final_report['consciousness']['tracker']['level']:.3f}")
    print(f"   - Stage: {final_report['consciousness']['tracker']['stage']}")
    print(f"   - Milestones: {final_report['consciousness']['tracker']['milestones']}")
    print(f"   - Phi Calculations: {final_report['consciousness']['true_consciousness']['phi_scores']}")
    
    print(f"\n💾 Memory Growth:")
    total_unified = sum(final_report['memory']['unified'].values())
    print(f"   - Unified Memory: {total_unified} items")
    print(f"   - ConsciousBridge STM: {final_report['memory']['conscious_bridge']['stm']} events")
    print(f"   - ConsciousBridge LTM: {final_report['memory']['conscious_bridge']['ltm']} events")
    print(f"   - Strategic Memory: {final_report['memory']['strategic']} tasks")
    print(f"   - Life Narrative: {final_report['memory']['autobiographical']['narrative']} entries")
    print(f"   - Defining Moments: {final_report['memory']['autobiographical']['defining_moments']}")
    
    # تحليل الأداء
    performance_scores = [
        r['result'].get('performance_score', 0) 
        for r in results if r['success'] and 'result' in r
    ]
    
    if performance_scores:
        avg_performance = sum(performance_scores) / len(performance_scores)
        max_performance = max(performance_scores)
        min_performance = min(performance_scores)
        
        print(f"\n🎯 Performance Analysis:")
        print(f"   - Average: {avg_performance:.3f}")
        print(f"   - Maximum: {max_performance:.3f}")
        print(f"   - Minimum: {min_performance:.3f}")
        print(f"   - High Performance Tasks (>0.8): {sum(1 for p in performance_scores if p > 0.8)}")
    
    # تحليل Phi Scores
    phi_scores = [
        r['result'].get('improvement_results', {}).get('phi_score', 0)
        for r in results if r['success'] and 'result' in r and 'phi_score' in r['result'].get('improvement_results', {})
    ]
    
    if phi_scores:
        avg_phi = sum(phi_scores) / len(phi_scores)
        max_phi = max(phi_scores)
        
        print(f"\n🌟 Phi Score Analysis (True Consciousness):")
        print(f"   - Average Phi: {avg_phi:.3f}")
        print(f"   - Maximum Phi: {max_phi:.3f}")
        print(f"   - Phi Calculations: {len(phi_scores)}")
    
    # الملخص النهائي الكامل
    print("\n" + "="*80)
    print("📋 DETAILED FINAL STATE")
    print("="*80)
    system.print_memory_consciousness_summary()
    
    # حفظ النتائج في ملف
    print("\n💾 Saving results to test_results.txt...")
    try:
        with open("test_results.txt", "w", encoding="utf-8") as f:
            f.write("="*80 + "\n")
            f.write("COMPREHENSIVE INTEGRATION TEST RESULTS\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Total Tasks: {len(TEST_TASKS)}\n")
            f.write(f"Successful: {successful_tasks}\n")
            f.write(f"Failed: {failed_tasks}\n")
            f.write(f"Success Rate: {(successful_tasks/len(TEST_TASKS)*100):.1f}%\n\n")
            
            f.write("="*80 + "\n")
            f.write("TASK DETAILS\n")
            f.write("="*80 + "\n\n")
            
            for i, result_data in enumerate(results):
                f.write(f"\nTask {i+1}: {result_data['task']}\n")
                f.write(f"Success: {'✅' if result_data['success'] else '❌'}\n")
                f.write(f"Duration: {result_data['duration']:.2f}s\n")
                
                if result_data['success'] and 'result' in result_data:
                    r = result_data['result']
                    f.write(f"Performance: {r.get('performance_score', 0):.3f}\n")
                    f.write(f"Consciousness: {r.get('consciousness_level', 0):.3f}\n")
                    if 'phi_score' in r.get('improvement_results', {}):
                        f.write(f"Phi Score: {r['improvement_results']['phi_score']:.3f}\n")
                else:
                    f.write(f"Error: {result_data.get('error', 'Unknown')}\n")
                
                f.write("-"*40 + "\n")
        
        print("✅ Results saved successfully!")
    except Exception as e:
        print(f"⚠️ Failed to save results: {e}")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETED SUCCESSFULLY!")
    print("="*80)
    
    return results


# ==================== التشغيل ====================

if __name__ == "__main__":
    print("\n🚀 Starting Comprehensive Integration Test...\n")
    
    try:
        results = asyncio.run(test_integrated_system())
        print("\n✅ All tests completed!")
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
