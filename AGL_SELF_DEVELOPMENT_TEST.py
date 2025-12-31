"""
AGL Self-Development Test
Verifies that the system can autonomously evolve its own codebase (using the sandbox).
"""
import sys
import os
import time

# Add path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "AGL_Core"))

from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence
import AGL_Core.AGL_Self_Dev_Sandbox as sandbox

def test_self_development():
    print("🧪 STARTING SELF-DEVELOPMENT TEST...")
    
    # 1. Initialize System
    asi = AGL_Super_Intelligence()
    
    # 2. Check Initial State
    print(f"   -> Initial Sandbox Version: {sandbox.version()}")
    initial_attrs = dir(sandbox)
    
    # 3. Trigger Evolution
    print("   -> Triggering Evolution...")
    asi.trigger_autonomous_evolution()
    
    # 4. Verify Change
    import importlib
    importlib.reload(sandbox)
    
    new_attrs = dir(sandbox)
    diff = set(new_attrs) - set(initial_attrs)
    
    print(f"   -> New Attributes: {diff}")
    
    if diff:
        print("✅ TEST PASSED: System successfully evolved the sandbox module.")
        
        # Check if Self-Improvement recorded it
        try:
            from dynamic_modules.mission_control_enhanced import SELF_IMPROVEMENT
            if SELF_IMPROVEMENT:
                print(f"   -> Self-Improvement Memory Size: {len(SELF_IMPROVEMENT.memory)}")
        except:
            pass
            
    else:
        print("❌ TEST FAILED: No changes detected in sandbox.")

if __name__ == "__main__":
    test_self_development()
