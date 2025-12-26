
import sys
import os
import asyncio
import logging

# Add root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

# Mock dependencies if needed, but let's try to run with real ones first
# We need to ensure Core_Engines is available
from Core_Engines import bootstrap_register_all_engines

async def main():
    print("🚀 Starting Phi Score Integration Test...")
    
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
        # Try alternative path
        from dynamic_modules.unified_agi_system import create_unified_agi_system
        unified_system = create_unified_agi_system(registry)
        
    # 3. Run a test query
    query = "Analyze the relationship between quantum entanglement and consciousness."
    print(f"   ❓ Query: {query}")
    
    print("   🏃 Running process_with_full_agi...")
    result = await unified_system.process_with_full_agi(query)
    
    print("\n   ✅ Processing complete.")
    # Check if Phi score was calculated (it prints to stdout, but we can also check if we can access it if we returned it)
    # The current implementation prints it.
    
    print("   🏁 Test finished.")

if __name__ == "__main__":
    asyncio.run(main())
