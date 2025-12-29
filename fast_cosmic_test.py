"""
Fast Cosmic Intelligence Test - Optimized with Holographic LLM
"""
import asyncio
import os
import sys
import time
import json

# Environment setup
os.environ["AGL_USE_HOLOGRAPHIC_LLM"] = "1"
os.environ["AGL_HOLO_KEY"] = "42"
os.environ["AGL_FEATURE_ENABLE_RAG"] = "0"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo-copy"))

print("="*80)
print("🌌 Fast Cosmic Intelligence Test - Holographic Optimized")
print("="*80)

# Simple test questions (avoiding ethical blocks)
test_questions = [
    {
        "title": "Renewable Energy Benefits",
        "question": "ما هي فوائد الطاقة المتجددة للبيئة والاقتصاد؟"
    },
    {
        "title": "Solar Power Mechanism",
        "question": "كيف تعمل الألواح الشمسية في توليد الكهرباء؟"
    },
    {
        "title": "Water Cycle",
        "question": "اشرح دورة الماء في الطبيعة بالتفصيل."
    },
    {
        "title": "Plant Photosynthesis",
        "question": "كيف تقوم النباتات بعملية البناء الضوئي؟"
    },
    {
        "title": "Gravity Explanation",
        "question": "ما هي الجاذبية وكيف تعمل في الكون؟"
    }
]

async def run_fast_tests():
    """Run tests with single system instance for speed"""
    # Fix import paths
    sys.path.insert(0, "D:/AGL/repo-copy")
    sys.path.insert(0, "D:/AGL/repo-copy/dynamic_modules")
    
    from Core_Engines import bootstrap_register_all_engines
    from unified_agi_system import UnifiedAGISystem
    
    # Initialize ONCE
    print("\n🚀 Step 1: Initializing AGL System (ONE TIME)...")
    
    # Create registry
    registry = {}
    bootstrap_register_all_engines(registry, allow_optional=True, max_seconds=60)
    
    system = UnifiedAGISystem(engine_registry=registry)
    
    print(f"✅ {len(registry)} engines loaded")
    if hasattr(system, 'holographic_llm') and system.holographic_llm:
        print("✅ Holographic LLM: READY")
    
    # Run all tests with SAME instance
    print("\n🔬 Step 2: Running Tests...")
    print(f"📝 {len(test_questions)} questions to test\n")
    
    results = []
    total_start = time.time()
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_questions)}: {test['title']}")
        print(f"{'='*80}")
        print(f"Question: {test['question']}")
        
        start = time.time()
        result = await system.process_with_full_agi(test['question'])
        elapsed = time.time() - start
        
        # Extract answer
        answer = None
        if 'response' in result:
            answer = result['response']
        elif 'text' in result:
            answer = result['text']
        elif isinstance(result, dict):
            answer = json.dumps(result, ensure_ascii=False, indent=2)
        
        if isinstance(answer, dict):
            if 'text' in answer:
                answer = answer['text']
            else:
                answer = json.dumps(answer, ensure_ascii=False, indent=2)
        
        answer_str = str(answer) if answer else "No answer"
        print(f"\n⏱️  Time: {elapsed:.2f}s")
        print(f"📝 Answer ({len(answer_str)} chars):")
        print(f"   {answer_str[:300]}...")
        
        results.append({
            'test': i,
            'title': test['title'],
            'time': elapsed,
            'answer_length': len(answer_str)
        })
    
    total_time = time.time() - total_start
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY")
    print(f"{'='*80}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Tests: {len(results)}")
    avg_time = total_time / len(results) if results else 0
    print(f"Average per test: {avg_time:.2f}s")
    
    # Holographic stats
    if hasattr(system, 'holographic_llm') and system.holographic_llm:
        stats = system.holographic_llm.get_statistics()
        print(f"\n🌌 Holographic LLM Stats:")
        print(f"   Hits: {stats.get('holographic_hits', 0)}")
        print(f"   API calls: {stats.get('api_calls', 0)}")
        
        efficiency = stats.get('efficiency_ratio', 0)
        if isinstance(efficiency, str):
            efficiency = float(efficiency.replace('%', '').strip()) if '%' in str(efficiency) else 0
        print(f"   Efficiency: {efficiency:.1f}%")
        
        print(f"   Avg retrieval: {stats.get('average_retrieval_time', 0):.4f}s")
    
    # Results table
    print(f"\n📋 Results:")
    for r in results:
        print(f"   {r['test']}. {r['title']}: {r['time']:.2f}s ({r['answer_length']} chars)")
    
    print(f"\n{'='*80}")
    print("✅ TEST COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(run_fast_tests())
