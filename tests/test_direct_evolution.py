
import sys
import os
import time
from pathlib import Path

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Recursive_Improver import RecursiveImprover

def run_direct_evolution():
    print("🧬 Starting Direct Evolution Test...")
    
    # 1. Setup
    improver = RecursiveImprover()
    target_file = "target_script.py"
    target_path = os.path.abspath(target_file)
    
    print(f"   🎯 Target File: {target_file}")
    
    # Read original content for comparison
    with open(target_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    print(f"   📄 Original Length: {len(original_content)} chars")

    # 2. Define Goal
    goal = (
        "Optimize the Fibonacci function using memoization or iteration for better performance. "
        "Add type hints to all functions. "
        "Use list comprehension in process_data. "
        "Add docstrings."
    )
    print(f"   🎯 Goal: {goal}")

    # 3. Execute Improvement (Mocking the internal read/write because RecursiveImprover expects engine names)
    # We will bypass the 'engine_name' lookup and feed the code directly if possible, 
    # but RecursiveImprover is designed for 'Core_Engines'.
    # So we will monkey-patch 'read_engine_code' to read our local file.
    
    original_read_method = improver.read_engine_code
    improver.read_engine_code = lambda name: original_content
    
    # We also need to handle the file writing manually since 'apply_changes' targets Core_Engines
    # So we will run with apply_changes=False to get the code, then write it ourselves.
    
    print("   🧠 Thinking (LLM)...")
    result = improver.analyze_and_improve("Dummy_Target", goal, apply_changes=False)
    
    if result.get('status') == 'success':
        # The result['preview'] might be truncated, so we need to check where the full code is saved
        saved_path = result.get('saved_at')
        if saved_path and os.path.exists(saved_path):
            with open(saved_path, 'r', encoding='utf-8') as f:
                new_code = f.read()
            
            print(f"   ✅ Evolution Successful!")
            print(f"   📄 New Length: {len(new_code)} chars")
            
            # Overwrite the target file manually to simulate 'apply_changes'
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(new_code)
            print(f"   💾 Applied changes to {target_file}")
            
        else:
            print("   ❌ Could not find the generated file.")
    else:
        print(f"   ❌ Evolution Failed: {result.get('message')}")

if __name__ == "__main__":
    run_direct_evolution()
