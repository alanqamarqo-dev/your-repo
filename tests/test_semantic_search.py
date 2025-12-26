
import sys
import os
import asyncio
import time

# Add root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines import bootstrap_register_all_engines

async def main():
    print("🚀 Starting Semantic Search Verification Test...")
    
    # 1. Bootstrap engines
    print("   ⚙️ Bootstrapping engines...")
    registry = {}
    bootstrap_register_all_engines(registry=registry, allow_optional=True, verbose=False)
    
    # 2. Create Unified AGI System
    print("   🧠 Creating Unified AGI System...")
    try:
        from repo_copy.dynamic_modules.unified_agi_system import create_unified_agi_system # type: ignore
        unified_system = create_unified_agi_system(registry)
    except ImportError:
        from dynamic_modules.unified_agi_system import create_unified_agi_system
        unified_system = create_unified_agi_system(registry)
        
    if not unified_system.conscious_bridge:
        print("   ❌ ConsciousBridge not available. Aborting.")
        return

    bridge = unified_system.conscious_bridge
    
    # 3. Populate Memory with distinct topics
    print("\n   📥 Populating Memory with test events...")
    
    memories = [
        {"input": "How to bake a cake?", "output": "Mix flour, sugar, eggs, and bake at 350F.", "topic": "cooking"},
        {"input": "Explain quantum entanglement", "output": "Spooky action at a distance where particles correlate.", "topic": "physics"},
        {"input": "Best way to learn Python", "output": "Practice coding daily and build projects.", "topic": "programming"},
        {"input": "Capital of France", "output": "The capital of France is Paris.", "topic": "geography"}
    ]
    
    for mem in memories:
        bridge.put(
            type="test_memory",
            payload=mem,
            to="ltm", # Put in LTM for semantic search
            pinned=True
        )
    
    # Force build index (if applicable)
    print("   🔨 Building Semantic Index...")
    indexed_count = bridge.build_semantic_index()
    print(f"   📊 Indexed {indexed_count} documents.")

    # 4. Run Search Queries
    queries = [
        ("baking instructions", "cooking"),
        ("physics particles", "physics"),
        ("coding tips", "programming"),
        ("Paris location", "geography")
    ]
    
    print("\n   🔍 Running Search Queries...")
    
    passed = 0
    for query_text, expected_topic in queries:
        print(f"\n   ❓ Query: '{query_text}' (Expect: {expected_topic})")
        results = bridge.semantic_search(query_text, top_k=1)
        
        if results:
            top_result = results[0]
            payload = top_result.get('payload', {})
            topic = payload.get('topic', 'unknown')
            score = top_result.get('_score', 0.0) # Fallback score or similarity
            
            print(f"      Found: '{payload.get('input')}' (Topic: {topic})")
            
            if topic == expected_topic:
                print("      ✅ Match!")
                passed += 1
            else:
                print("      ❌ Mismatch.")
        else:
            print("      ⚠️ No results found.")

    print(f"\n   📈 Result: {passed}/{len(queries)} queries passed.")
    
    if passed == len(queries):
        print("   ✅ Semantic Search is WORKING.")
    elif passed > 0:
        print("   ⚠️ Semantic Search is PARTIALLY working (might be keyword fallback).")
    else:
        print("   ❌ Semantic Search FAILED.")

    print("\n   🏁 Test finished.")

if __name__ == "__main__":
    asyncio.run(main())
