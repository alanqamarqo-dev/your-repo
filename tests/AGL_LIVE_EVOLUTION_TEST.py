import sys
import os
import time
import importlib

# Add path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "AGL_Core"))

from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence
import AGL_Dummy_Module

def run_evolution_test():
    print("🧬 STARTING LIVE EVOLUTION TEST...")
    
    # 1. Initialize ASI
    asi = AGL_Super_Intelligence()
    
    # 2. Run Old Code
    print("\n--- Step 1: Running Original Code ---")
    AGL_Dummy_Module.say_hello()
    
    # 3. Prepare New Code (The Patch)
    new_code = """def say_hello():
    print("🚀 Hello from Version 2 (Evolved Code!)")
    print("   -> Hot-Swap Successful.")
"""
    
    # 4. Trigger Evolution
    print("\n--- Step 2: Triggering Self-Evolution ---")
    success = asi.evolve_codebase("AGL_Dummy_Module", new_code)
    
    if success:
        print("\n--- Step 3: Verifying Evolution ---")
        # Note: In the main script scope, we might need to reload to see changes if we imported 'from ...'
        # But since we imported the module object 'AGL_Dummy_Module', accessing it again *should* show the reloaded version
        # because importlib.reload modifies the module object in place.
        AGL_Dummy_Module.say_hello()
    else:
        print("❌ Evolution Failed.")

if __name__ == "__main__":
    run_evolution_test()
