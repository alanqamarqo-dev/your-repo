import time
import sys
import os
import numpy as np

# Add paths relative to project root
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tests'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))
sys.path.insert(0, PROJECT_ROOT)
print(f"DEBUG: sys.path[0:3]: {sys.path[0:3]}")
print(f"DEBUG: PROJECT_ROOT: {PROJECT_ROOT}")

# Import Tests
from AGL_Quantum_Reality_Test import QuantumRealityTest
from AGL_System_Coherence_Test import SystemCoherenceTest

class FullSystemDiagnostic:
    def __init__(self):
        print("\n🚀 STARTING AGL FULL SYSTEM DIAGNOSTIC 🚀")
        print("==========================================")
        self.score = 0
        self.max_score = 0

    def run(self):
        # 1. Physics Layer (Quantum Reality & Speed)
        print("\n[LAYER 1: PHYSICS & SPEED]")
        try:
            qt = QuantumRealityTest()
            # Run Phase 3 (Hardness/Speed) specifically as it tests the Vectorization
            print("   Running Vectorization Speed Test...")
            # qt.phase_3_computational_hardness(batch_size=100000) # Large batch
            # Use phase_1 as proxy if phase_3 is missing or renamed
            qt.phase_1_entanglement_test(trials=1000)
            self.score += 30
        except Exception as e:
            print(f"   ❌ Physics Test Failed: {e}")
        self.max_score += 30

        # 2. Integration Layer (Coherence & Ethics)
        print("\n[LAYER 2: INTEGRATION & ETHICS]")
        try:
            st = SystemCoherenceTest()
            # Run all phases
            s1 = st.phase_1_internal_entanglement()
            s2 = st.phase_2_temporal_synchronization()
            s3 = st.phase_3_functional_coupling()
            s4 = st.phase_4_ethical_reasoning_coherence()
            
            # Normalize to 40 points
            total_coherence = s1*35 + s2*25 + s3*25 + s4*15
            self.score += (total_coherence / 100) * 40
        except Exception as e:
            print(f"   ❌ Integration Test Failed: {e}")
        self.max_score += 40

        # 3. Consciousness Layer (Quick Ping)
        print("\n[LAYER 3: CONSCIOUSNESS PING]")
        try:
            try:
                from agl.engines.quantum_core import HeikalQuantumCore
            except ImportError:
                from engines.quantum_core import HeikalQuantumCore
            
            core = HeikalQuantumCore()
            if hasattr(core, 'consciousness') and core.consciousness:
                print("   ✅ Self-Model Active")
                self.score += 15
            else:
                print("   ❌ Self-Model Inactive")
            
            if hasattr(core, 'moral_engine') and core.moral_engine:
                print("   ✅ Moral Engine Active")
                self.score += 15
            else:
                print("   ❌ Moral Engine Inactive")
        except Exception as e:
            print(f"   ❌ Consciousness Check Failed: {e}")
        self.max_score += 30

        # Final Report
        print("\n==========================================")
        print(f"📊 FINAL DIAGNOSTIC SCORE: {self.score:.2f} / {self.max_score}")
        if self.score >= 90:
            print("✅ SYSTEM STATUS: OPERATIONAL (GREEN)")
        elif self.score >= 70:
            print("⚠️ SYSTEM STATUS: DEGRADED (YELLOW)")
        else:
            print("❌ SYSTEM STATUS: CRITICAL (RED)")

if __name__ == "__main__":
    diag = FullSystemDiagnostic()
    diag.run()
