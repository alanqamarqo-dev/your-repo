
import sys
import os
import asyncio
import time

# Add root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines import bootstrap_register_all_engines

async def main():
    print("🚀 Starting Graph Relations Test...")
    
    # 1. Bootstrap engines
    print("   ⚙️ Bootstrapping engines...")
    registry = {}
    bootstrap_register_all_engines(registry=registry, allow_optional=True, verbose=False)
    
    # 2. Create Unified AGI System
    print("   🧠 Creating Unified AGI System...")
    try:
        from repo_copy.dynamic_modules.unified_agi_system import create_unified_agi_system
        unified_system = create_unified_agi_system(registry)
    except ImportError:
        from dynamic_modules.unified_agi_system import create_unified_agi_system
        unified_system = create_unified_agi_system(registry)
        
    # 3. Run TWO consecutive queries to trigger linking
    query1 = "What is the first law of thermodynamics?"
    query2 = "How does it relate to entropy?"
    
    print(f"\n   1️⃣ Running Query 1: {query1}")
    await unified_system.process_with_full_agi(query1)
    
    print(f"\n   2️⃣ Running Query 2: {query2}")
    await unified_system.process_with_full_agi(query2)
    
    # 4. Verify Link in ConsciousBridge
    print("\n   🔎 Verifying Graph Link...")
    if unified_system.conscious_bridge:
        graph = unified_system.conscious_bridge.graph
        print(f"   📊 Graph Size: {len(graph)} nodes with outgoing edges")
        
        # Check if we have any links
        found_link = False
        for src, edges in graph.items():
            for edge in edges:
                src_id, rel, dst_id = edge
                print(f"   🔗 Found Edge: {src_id[:8]}... --[{rel}]--> {dst_id[:8]}...")
                found_link = True
        
        if found_link:
            print("   ✅ SUCCESS: Events are being linked causally!")
        else:
            print("   ⚠️ WARNING: No links found in graph.")
    else:
        print("   ❌ ConsciousBridge not available.")

    print("\n   🏁 Test finished.")

if __name__ == "__main__":
    asyncio.run(main())
