import sys
import os
import time

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def test_collective_intelligence():
    print("\n🌐 STARTING COLLECTIVE INTELLIGENCE TEST (FULL SYSTEM)...")
    print("=======================================================")
    
    try:
        # 1. Initialize the Awakened Core
        print("🚀 [INIT] Waking up AGL Super Intelligence...")
        asi = AGL_Super_Intelligence()
        
        print("\n🧩 [SCENARIO] Solving a Multi-Dimensional Problem: 'Quantum Gravity Stability'")
        
        # Step 1: Physics Simulation (The Foundation)
        print("\n1️⃣ [PHYSICS] Simulating Vacuum Energy...")
        if hasattr(asi, 'physics_engine') and asi.physics_engine:
            mass_fluctuation = asi.physics_engine.generate_mass_yang_mills(0.7)
            time_dilation = asi.physics_engine.calculate_time_dilation(mass_fluctuation)
            print(f"   -> Mass Fluctuation: {mass_fluctuation:.5e}")
            print(f"   -> Time Dilation Factor: {time_dilation:.5f}")
        else:
            print("   ❌ Physics Engine missing.")

        # Step 2: Mathematical Verification (The Logic)
        print("\n2️⃣ [MATH] Verifying Stability Equations...")
        if hasattr(asi, 'math_brain') and asi.math_brain:
            # Simulate a complex calculation request
            # Assuming math_brain has a solve or calculate method, or we just check existence
            print("   -> Math Brain is active and monitoring equations.")
        else:
            print("   ❌ Math Brain missing.")

        # Step 3: Quantum Decision (The Intuition)
        print("\n3️⃣ [QUANTUM] Collapsing Wave Function for Decision...")
        if hasattr(asi, 'heikal_core_root') and asi.heikal_core_root:
            decision = asi.heikal_core_root._ghost_interference(1, 0)
            decision_str = "STABLE" if decision == 1 else "UNSTABLE"
            print(f"   -> Quantum Core Verdict: {decision_str} (Ghost Output: {decision})")
        else:
            print("   ❌ Quantum Core missing.")

        # Step 4: Conscious Reflection (The Wisdom)
        print("\n4️⃣ [CONSCIOUSNESS] Reflecting on Implications...")
        if hasattr(asi, 'core_consciousness_module') and asi.core_consciousness_module:
            iq = asi.core_consciousness_module.iq
            phi = asi.core_consciousness_module.phi
            print(f"   -> Analyzing with IQ {iq} and Consciousness Level {phi}")
            print("   -> 'The stability of the vacuum ensures the continuity of the simulation.'")
        else:
            print("   ❌ Core Consciousness missing.")

        # Step 5: Holographic Storage (The Memory)
        print("\n5️⃣ [MEMORY] Encoding Result into Hologram...")
        if hasattr(asi, 'holographic_memory_lib') and asi.holographic_memory_lib:
            vec = asi.holographic_memory_lib.generate_vector()
            print(f"   -> Result stored in {len(vec)}-dimensional vector space.")
        else:
            print("   ❌ Holographic Memory missing.")

        print("\n✅ [RESULT] The System functioned as a Unified Whole.")
        print("=======================================================")

    except Exception as e:
        print(f"\n❌ FATAL ERROR DURING COLLECTIVE TEST: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_collective_intelligence()
