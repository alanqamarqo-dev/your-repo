"""
اختبار unified_agi_system مع Holographic LLM - سؤال آمن
"""
import asyncio
import os
import sys
import time

# Set environment variables for Holographic LLM
os.environ["AGL_USE_HOLOGRAPHIC_LLM"] = "1"
os.environ["AGL_HOLO_KEY"] = "42"
os.environ["AGL_FEATURE_ENABLE_RAG"] = "0"  # Disable RAG to isolate holographic

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo-copy"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "dynamic_modules"))

from dynamic_modules.unified_agi_system import UnifiedAGISystem

async def test_unified_with_holographic():
    """Test unified AGI system with holographic LLM"""
    print("=" * 80)
    print("🌌 UNIFIED AGI SYSTEM + HOLOGRAPHIC LLM TEST")
    print("=" * 80)
    
    # Step 1: Get engine registry
    print("\n🛠️ Step 1: Bootstrapping Engines...")
    from repo_copy.Core_Engines import get_bootstrap_registry
    registry = get_bootstrap_registry()
    
    # Step 2: Create unified AGI system
    print("\n🛠️ Step 2: Creating Unified AGI System...")
    system = UnifiedAGISystem(engine_registry=registry)
    
    # Check holographic status
    if hasattr(system, 'holographic_llm') and system.holographic_llm:
        print(f"\n✅ Holographic LLM Status: ✅ Enabled")
        print(f"   Storage: {system.holographic_llm.storage_path}")
        print(f"   Security Key: {system.holographic_llm.security_key}")
    else:
        print(f"\n❌ Holographic LLM Status: ❌ Disabled")
        return
    
    # Step 3: First query (will use LLM and store in holographic memory)
    print("\n🔬 Step 3: Processing Safe Query (First Time)")
    query = "ما هي فوائد الطاقة المتجددة؟"
    print(f"   Query: {query}")
    
    start_time = time.time()
    result1 = await system.process_with_full_agi(query)
    time1 = time.time() - start_time
    
    print(f"\n✅ Result 1:")
    print(f"   Status: {result1.get('status', 'unknown')}")
    print(f"   Response length: {len(str(result1.get('response', '')))} chars")
    print(f"   Time: {time1:.4f}s")
    if 'holographic_used' in result1:
        print(f"   🌌 Holographic Used: {result1['holographic_used']}")
    
    # Step 4: Repeat query (should be instant from holographic memory)
    print(f"\n🔬 Step 4: Same Query (Should be instant from hologram)")
    
    start_time = time.time()
    result2 = await system.process_with_full_agi(query)
    time2 = time.time() - start_time
    
    print(f"\n✅ Result 2:")
    print(f"   Status: {result2.get('status', 'unknown')}")
    print(f"   Response length: {len(str(result2.get('response', '')))} chars")
    print(f"   Time: {time2:.4f}s")
    if 'holographic_used' in result2:
        print(f"   🌌 Holographic Used: {result2['holographic_used']}")
    
    # Calculate speedup
    if time2 > 0:
        speedup = time1 / time2
        print(f"\n⚡ Speedup: {speedup:.2f}× faster on repeat!")
    
    # Step 5: Get holographic statistics
    if hasattr(system, 'holographic_llm') and system.holographic_llm:
        stats = system.holographic_llm.get_statistics()
        print(f"\n📊 Holographic LLM Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    print("\n" + "=" * 80)
    print("🎯 TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_unified_with_holographic())
