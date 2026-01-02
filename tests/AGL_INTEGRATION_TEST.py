import sys
import os
import time

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def test_grand_integration():
    print("\n🧪 STARTING GRAND INTEGRATION TEST...")
    print("=====================================")
    
    try:
        # Initialize Core
        print("   🚀 Initializing AGL Super Intelligence...")
        asi = AGL_Super_Intelligence()
        
        print("\n🔍 VERIFYING NEWLY INTEGRATED MODULES:")
        
        # 1. Test Physics Engine
        if hasattr(asi, 'physics_engine') and asi.physics_engine:
            print("   ✅ [PHYSICS] Engine Linked.")
            mass = asi.physics_engine.generate_mass_yang_mills(0.5)
            print(f"      -> Test Calculation (Yang-Mills Mass): {mass}")
        else:
            print("   ❌ [PHYSICS] Engine NOT Linked.")

        # 2. Test Core Consciousness
        if hasattr(asi, 'core_consciousness_module') and asi.core_consciousness_module:
            print("   ✅ [CONSCIOUSNESS] Module Linked.")
            print(f"      -> IQ Level: {asi.core_consciousness_module.iq}")
            print(f"      -> Phi Level: {asi.core_consciousness_module.phi}")
        else:
            print("   ❌ [CONSCIOUSNESS] Module NOT Linked.")

        # 3. Test Heikal Quantum Core (Root)
        if hasattr(asi, 'heikal_core_root') and asi.heikal_core_root:
            print("   ✅ [QUANTUM ROOT] Core Linked.")
            # Test Ghost Interference (0, 1) -> Expecting interaction
            # Note: _ghost_interference is internal, but we can call it for testing
            try:
                res = asi.heikal_core_root._ghost_interference(0, 1)
                print(f"      -> Ghost Interference Test (0,1): {res}")
            except Exception as e:
                print(f"      -> Ghost Test Error: {e}")
        else:
            print("   ❌ [QUANTUM ROOT] Core NOT Linked.")

        # 4. Test Holographic Memory Lib
        if hasattr(asi, 'holographic_memory_lib') and asi.holographic_memory_lib:
            print("   ✅ [HOLOGRAPHIC LIB] Library Linked.")
            vec = asi.holographic_memory_lib.generate_vector()
            print(f"      -> Vector Generation Test: {len(vec)} dimensions")
        else:
            print("   ❌ [HOLOGRAPHIC LIB] Library NOT Linked.")

        print("\n🎉 INTEGRATION TEST COMPLETE.")

    except Exception as e:
        print(f"\n❌ FATAL ERROR DURING TEST: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_grand_integration()
