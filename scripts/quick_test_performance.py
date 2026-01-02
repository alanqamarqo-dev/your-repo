import os
import sys
import asyncio
import time

sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines import bootstrap_register_all_engines
from dynamic_modules.unified_agi_system import UnifiedAGISystem

os.environ["AGL_LLM_MODEL"] = "qwen2.5:7b-instruct"

async def quick_test():
    print("🧪 Quick Performance Test")
    print("="*50)
    
    # Bootstrap engines
    registry = {}
    bootstrap_register_all_engines(registry=registry, verbose=False, max_seconds=10)
    print(f"✅ {len(registry)} engines registered\n")
    
    # Initialize AGI
    agi = UnifiedAGISystem(engine_registry=registry)
    
    # Simple test with simulation
    test_prompt = """صمم خوارزمية بسيطة لحساب كفاءة الطاقة الشمسية:
- المدخل: شدة الضوء (W/m²)
- المخرج: الطاقة المحولة (Joules)
قدم كود Python بسيط."""
    
    print("🔬 Running test...")
    start_time = time.time()
    
    result = await agi.process_with_full_agi(test_prompt)
    
    duration = time.time() - start_time
    
    print("\n" + "="*50)
    print(f"⏱️  Total Time: {duration:.2f} seconds")
    print(f"📊 Result Preview: {str(result)[:200]}...")
    print("="*50)
    
    return duration

if __name__ == "__main__":
    duration = asyncio.run(quick_test())
    print(f"\n🎯 Final Performance: {duration:.2f}s")
