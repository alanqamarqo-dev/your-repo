"""
AGL Core Evolution Test
WARNING: This script attempts to evolve a core component (AGL_Unified_Python).
"""
import sys
import os
import time

# Add path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "AGL_Core"))

from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence
import AGL_Core.AGL_Unified_Python as unified_lib

def test_core_evolution():
    print("🧪 STARTING CORE EVOLUTION TEST (AGL_Unified_Python)...")
    
    # 1. Initialize System
    asi = AGL_Super_Intelligence()
    
    # 2. Check Initial State
    print(f"   -> Initial UnifiedLib Attributes: {len(dir(unified_lib.UnifiedLib))}")
    
    # 3. Trigger Evolution on a REAL module
    # We use AGL_Unified_Python as it is critical but less risky than the Super Intelligence itself for a first test.
    target = "AGL_Core.AGL_Unified_Python"
    print(f"   -> Triggering Evolution on {target}...")
    
    asi.trigger_autonomous_evolution(target_module=target)
    
    # 4. Verify Change
    import importlib
    importlib.reload(unified_lib)
    
    # Check if the new capability exists (the mock evolution adds 'evolved_capability_...')
    found = False
    for attr in dir(unified_lib):
        if "evolved_capability" in attr:
            found = True
            print(f"   ✅ Found evolved attribute: {attr}")
            break
            
    if found:
        print("✅ TEST PASSED: System successfully evolved a CORE module.")
    else:
        print("❌ TEST FAILED: No changes detected in core module.")

if __name__ == "__main__":
    test_core_evolution()
