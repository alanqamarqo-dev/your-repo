import sys
import os
import json
import numpy as np

# --- SETUP PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# We need to add project root so we can import agl
src_path = os.path.join(current_dir, "AGL_NextGen", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
sys.path.append(current_dir)

from agl.core.super_intelligence import AGL_Super_Intelligence
from agl.engines.holographic_memory import HeikalHolographicMemory

def test_persistence():
    print("🧪 TESTING MEMORY PERSISTENCE")
    
    # 1. Check if file exists
    if os.path.exists("core_state.hologram.npy"):
        size = os.path.getsize("core_state.hologram.npy")
        print(f"   [DISK] core_state.hologram.npy exists (Size: {size} bytes).")
    else:
        print("   ⚠️ [DISK] No memory file found!")
        return

    # 2. Boot System
    print("   [BOOT] Initializing AGL Super Intelligence...")
    agi = AGL_Super_Intelligence()
    
    # 3. Check Memory State
    # Is there a loaded memory object?
    # Where does AGL store the loaded memory?
    # It might be in agl.holographic_memory_lib or reachable via registry
    
    holo_engine = agi.engine_registry.get('Heikal_Holographic_Memory') or agi.engine_registry.get('Holographic_Memory')
    
    if not holo_engine:
        # Try to find where it is
        print("   ⚠️ Heikal_Holographic_Memory engine not found in registry.")
        # Maybe implicitly used by Core?
        if agi.core and hasattr(agi.core, 'holographic_memory'):
            holo_engine = agi.core.holographic_memory
            print("   -> Found attached to Quantum Core.")
    
    if holo_engine:
        # Try to load explicitly to verify content matches what we expect
        # Note: The engine might not auto-load into a python dict variable, it might keep it on disk/hologram
        # until requested.
        print("   -> Attempting load from engine...")
        data = holo_engine.load_memory()
        if data:
             print(f"   ✅ MEMORY LOADED: {str(data)[:100]}...")
             keys = data.keys() if isinstance(data, dict) else []
             print(f"   -> Keys found: {list(keys)}")
        else:
             print("   ❌ MEMORY LOAD RETURNED NONE/EMPTY.")
    else:
        print("   ❌ No Holographic Engine instance found to query.")

if __name__ == "__main__":
    test_persistence()
