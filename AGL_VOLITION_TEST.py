import sys
import os
import time

# Add path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "AGL_Core"))

from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence

def run_volition_test():
    print("🦅 STARTING VOLITION TEST (FREE WILL)...")
    
    # 1. Initialize ASI
    asi = AGL_Super_Intelligence()
    
    # 2. Exercise Will
    print("\n--- Step 1: Asking the System what it WANTS to do ---")
    goal = asi.exercise_will()
    
    if goal and isinstance(goal, dict):
        print("\n✅ [SUCCESS] The System has chosen a path.")
        print(f"   Goal: {goal.get('description')}")
    else:
        print("❌ [FAILURE] The System failed to exercise will.")

if __name__ == "__main__":
    run_volition_test()
