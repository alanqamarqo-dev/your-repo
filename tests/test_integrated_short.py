
import sys
import os
import asyncio
import time

# Add root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines import bootstrap_register_all_engines

async def test_integration_short():
    print("🚀 Starting Short Integration Test (Phase 8 Preview)...")
    
    # 1. Bootstrap engines
    print("   ⚙️ Bootstrapping engines...")
    registry = {}
    bootstrap_register_all_engines(registry=registry, allow_optional=True, verbose=False)
    
    # 2. Create Unified AGI System
    print("   🧠 Creating Unified AGI System...")
    try:
        from repo_copy.dynamic_modules.unified_agi_system import create_unified_agi_system
        system = create_unified_agi_system(registry)
    except ImportError:
        from dynamic_modules.unified_agi_system import create_unified_agi_system
        system = create_unified_agi_system(registry)
    
    # 3. Define Test Tasks (Just 3 tasks for quick verification)
    test_tasks = [
        "What is consciousness?",
        "Solve: 2x + 5 = 15",
        "Explain quantum entanglement"
    ]
    
    print(f"   📋 Scheduled {len(test_tasks)} tasks for execution.")
    
    results = []
    start_time = time.time()
    
    for i, task in enumerate(test_tasks):
        print(f"\n{'='*60}")
        print(f"Task {i+1}/{len(test_tasks)}: {task}")
        print(f"{'='*60}")
        
        try:
            # Process task
            result = await system.process_with_full_agi(task)
            results.append(result)
            
            # Extract answer for display
            answer = "N/A"
            if isinstance(result, dict):
                if 'reasoning' in result and 'answer' in result['reasoning']:
                    answer = result['reasoning']['answer']
                elif 'output' in result:
                    answer = result['output']
            
            print(f"   ✅ Result: {str(answer)[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Error processing task: {e}")
            import traceback
            traceback.print_exc()
        
        # Report after each task for this short test
        system.print_memory_consciousness_summary()
            
        # Small pause
        await asyncio.sleep(1)
    
    duration = time.time() - start_time
    
    # Final Report
    print("\n" + "="*60)
    print("🎉 FINAL REPORT - SHORT TEST")
    print("="*60)
    
    report = system.get_memory_consciousness_report()
    print(f"✅ Tasks Completed: {len(results)}/{len(test_tasks)}")
    print(f"⏱️ Total Duration: {duration:.2f}s")
    print(f"🧠 Final Consciousness Level: {report['consciousness']['unified_level']:.3f}")
    print(f"💾 Final LTM Count: {report['memory']['conscious_bridge']['ltm']}")
    
    if report['memory']['conscious_bridge']['ltm'] > 0:
        print("   ✅ LTM Persistence Verified (Items saved to DB).")
    else:
        print("   ⚠️ LTM Count is 0. Check thresholds or DB connection.")

    print("\n   🏁 Test finished.")

if __name__ == "__main__":
    asyncio.run(test_integration_short())
