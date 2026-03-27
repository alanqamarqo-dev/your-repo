import asyncio
import sys
import os
import time
import json

# --- Path Setup ---
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

# --- Imports ---
from dynamic_modules.unified_agi_system import UnifiedAGISystem
from Core_Engines import bootstrap_register_all_engines

async def main():
    print("🚀 Initializing AGL System for Quality Test...")
    
    # 1. Bootstrap Engines
    registry = {}
    print("   - Bootstrapping engines...")
    bootstrap_register_all_engines(registry, allow_optional=True, max_seconds=60)
    
    # 2. Initialize Unified System
    print("   - Initializing UnifiedAGISystem...")
    agi = UnifiedAGISystem(registry)
    
    # 3. Define Question
    question = "اشرح العلاقة بين الزمن والوعي في فيزياء هيكل، وكيف يؤثر ذلك على اتخاذ القرار؟"
    print(f"\n❓ Question: {question}")
    
    # 4. Run Processing
    print("\n⏳ Processing...")
    start_time = time.time()
    
    try:
        result = await agi.process_with_full_agi(question)
        duration = time.time() - start_time
        
        print(f"\n✅ Done in {duration:.2f} seconds.")
        
        # 5. Print Result
        print("\n📝 Answer:")
        print("-" * 50)
        
        # Extract answer from result
        answer = result.get('integrated_output', '')
        if not answer:
            answer = result.get('final_response', '')
        if not answer:
            answer = str(result)
            
        print(answer)
        print("-" * 50)
        
        # Check for Heikal/Holographic traces
        if 'emotional_intensity' in result.get('context', {}):
            print(f"\n❤️ Emotional Intensity: {result['context']['emotional_intensity']}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
