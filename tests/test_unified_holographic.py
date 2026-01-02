"""
Test Unified AGI System with Holographic LLM
=============================================

اختبار النظام الموحد مع Holographic LLM
"""

import os
import sys
import asyncio

# Set environment
os.environ['AGL_USE_HOLOGRAPHIC_LLM'] = '1'
os.environ['AGL_HOLO_KEY'] = '42'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo-copy'))

print("="*70)
print("🌌 UNIFIED AGI SYSTEM + HOLOGRAPHIC LLM TEST")
print("="*70)

async def main():
    from dynamic_modules.unified_agi_system import create_unified_agi_system
    
    # Create minimal engine registry
    engine_registry = {}
    
    print("\n📦 Step 1: Creating Unified AGI System...")
    system = create_unified_agi_system(engine_registry)
    
    # Check if Holographic LLM is enabled
    print(f"\n✨ Holographic LLM Status: {'✅ Enabled' if system.holographic_llm_enabled else '❌ Disabled'}")
    
    if not system.holographic_llm_enabled:
        print("⚠️ Holographic LLM not available - test aborted")
        return
    
    # Test query
    query = "ما هو الذكاء الاصطناعي العام؟"
    
    print(f"\n🔧 Step 2: Processing Query (First Time)")
    print(f"   Query: {query}")
    
    result1 = await system.process_with_full_agi(query)
    
    print(f"\n✅ Result 1:")
    print(f"   Status: {result1.get('status', 'unknown')}")
    print(f"   Response length: {len(str(result1.get('integrated_output', '')))} chars")
    
    # Second query - should be instant from hologram
    print(f"\n🔧 Step 3: Same Query (Should be instant)")
    
    result2 = await system.process_with_full_agi(query)
    
    print(f"\n✅ Result 2:")
    print(f"   Status: {result2.get('status', 'unknown')}")
    print(f"   Response length: {len(str(result2.get('integrated_output', '')))} chars")
    
    # Get statistics
    if system.holographic_llm:
        print(f"\n📊 Holographic LLM Statistics:")
        stats = system.holographic_llm.get_statistics()
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    print("\n" + "="*70)
    print("🏁 TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
