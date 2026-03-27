import sys
import os
import time

# Setup paths
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Recursive_Improver import RecursiveImprover

def test_evolution():
    print("🧬 Initializing Recursive Improver...")
    improver = RecursiveImprover()
    
    target_engine = "Volition_Engine"
    goal = "Add detailed docstrings to all methods and improve the 'update_state' logic to be more robust."
    
    print(f"🎯 Target: {target_engine}")
    print(f"📝 Goal: {goal}")
    
    start_time = time.time()
    # Enable apply_changes=True to test Hot Swapping
    result = improver.analyze_and_improve(target_engine, goal, apply_changes=True)
    duration = time.time() - start_time
    
    print("\n📊 Evolution Results:")
    print(f"   Status: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"   Mode: {result.get('mode')}")
        if result.get('mode') == 'applied':
            print(f"   Backup: {result.get('backup')}")
            print("   ✅ Code successfully updated and reloaded!")
        else:
            print(f"   Saved Path: {result.get('saved_at')}")
            
        print(f"   Time Taken: {duration:.2f}s")
    else:
        print(f"   Error: {result.get('message')}")

if __name__ == "__main__":
    test_evolution()
