
import sys
import os
import asyncio

# Add root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines import bootstrap_register_all_engines

async def main():
    print("🚀 Starting Report Verification Test...")
    
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
        
    # 3. Run Report
    print("\n   📊 Generating Report...")
    try:
        unified_system.print_memory_consciousness_summary()
        print("   ✅ Report generated successfully.")
    except Exception as e:
        print(f"   ❌ Failed to generate report: {e}")
        import traceback
        traceback.print_exc()

    print("\n   🏁 Test finished.")

if __name__ == "__main__":
    asyncio.run(main())
