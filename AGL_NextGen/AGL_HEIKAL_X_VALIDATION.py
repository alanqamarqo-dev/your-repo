import sys
import os

# AGGRESSIVE PATH FIX: Put the local src at the VERY BEGINNING of sys.path
# This ensures we use the development version even if an older version is installed.
workspace_root = r"D:\AGL\AGL_NextGen"
src_path = os.path.join(workspace_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

# Debug: Print path to verify
# print(f"DEBUG: sys.path[0] = {sys.path[0]}")

from agl.core.super_intelligence import AGL_Super_Intelligence
from agl.engines.heikal_x_vector_runtime import HeikalXRuntime

def test_heikal_x():
    print("--- [TEST] HEIKAL-X WAVE-LOGIC VALIDATION ---")
    runtime = HeikalXRuntime()
    
    # 1. Superposition
    print("Step 1: Creating variables in superposition...")
    runtime.superpose("StateA", [True, False], [0.7, 0.3])
    runtime.superpose("StateB", ["Success", "Failure"], [0.9, 0.1])
    
    print(f"  StateA: {runtime.variables['StateA']}")
    print(f"  StateB: {runtime.variables['StateB']}")
    
    # 2. Entanglement
    print("\nStep 2: Entangling StateA and StateB...")
    runtime.entangle("StateA", "StateB")
    
    # 3. Wave-Logic If (Condition in superposition)
    print("\nStep 3: Executing Wave-Logic Branching...")
    
    def on_true():
        return "Target Reached (TRUE branch)"
    
    def on_false():
        return "Retrying (FALSE branch)"
    
    # This will collapse StateA, which in turn collapses StateB due to entanglement
    result = runtime.wave_if("StateA", on_true, on_false)
    
    print(f"  Execution Result: {result}")
    print(f"  After Observation - StateA: {runtime.variables['StateA']}")
    print(f"  After Observation - StateB: {runtime.variables['StateB']}")
    
    print("\n--- [RESULT] HEIKAL-X VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    test_heikal_x()
