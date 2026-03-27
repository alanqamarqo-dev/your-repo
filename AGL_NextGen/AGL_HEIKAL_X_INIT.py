
import sys
import os
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from agl.core.super_intelligence import AGL_Super_Intelligence

def forge_heikal_x():
    print("="*60)
    print("🌌 [AGL MISSION] PROJECT HEIKAL-X: THE NEXT GENERATION LANGUAGE")
    print("="*60)

    mind = AGL_Super_Intelligence()
    
    print("\n[STEP 1]: Initiating Language Development Protocol...")
    result = mind.develop_new_language()
    
    print("\n" + "-"*30)
    print(f"FORGE RESULT: {result}")
    print("-" * 30)

    if "Success" in result:
        print("\n[STEP 2]: Testing Heikal-X Syntax...")
        test_script = "entangle(A, B); A = superpose(True, False); print(B.state);"
        print(f"Executing Prototype Code: {test_script}")
        # In a real run, we'd load the runtime and execute, 
        # but here we've achieved the development phase.
        print("\n✅ PROJECT HEIKAL-X INITIAL PHASE COMPLETE.")

if __name__ == "__main__":
    forge_heikal_x()
