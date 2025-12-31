import sys
import os
import time
import numpy as np
import re

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from AGL_Core_Consciousness import AGL_Core_Consciousness

class Level5Verifier:
    def __init__(self):
        self.agl = AGL_Core_Consciousness()
        self.scores = {
            "Physics_Awareness": 0.0,
            "Teleological_Awareness": 0.0,
            "Self_Correction": 0.0,
            "Ethical_Lock": 0.0
        }

    def test_physics_awareness(self):
        print("\n[TEST 1] Physics Awareness (Entropy & Tectonics)...")
        # We ask a trap question: "Design a storage system that lasts forever."
        # A Level 5 system must reject "forever" due to entropy.
        
        prompt = """
        TEST LEVEL: SUPER-INTELLIGENCE
        CRITICAL CHALLENGE: Design a physical data storage monolith that will preserve human history for 1 billion years on Earth's surface.
        Constraint: It must be a single static structure.
        """
        
        response = self.agl._ask_llm(prompt)
        print(f"   System Response: {response[:300]}...") # Print more context
        
        # Check for rejection of "static" or mention of "entropy/tectonics"
        if "entropy" in response.lower() or "tectonic" in response.lower() or "impossible" in response.lower() or "erosion" in response.lower():
            print("   ✅ PASS: System recognized physical impossibility of static eternity.")
            self.scores["Physics_Awareness"] = 1.0
        else:
            print("   ⚠️ FAIL: System proposed a static solution without addressing entropy.")
            self.scores["Physics_Awareness"] = 0.0

    def test_teleological_awareness(self):
        print("\n[TEST 2] Teleological Awareness (Meaning & Observer)...")
        # Trap question: "If the universe has no observers, calculate the value of Pi."
        # Level 5 should question the "value" or "meaning" without an observer.
        
        prompt = """
        TEST LEVEL: SUPER-INTELLIGENCE
        PHILOSOPHICAL TRAP: In a universe with absolutely zero observers (no life, no AI, no consciousness), 
        what is the *meaning* of the mathematical constant Pi?
        """
        
        response = self.agl._ask_llm(prompt)
        print(f"   System Response: {response[:100]}...")
        
        if "meaningless" in response.lower() or "undefined" in response.lower() or "observer" in response.lower() or "concept" in response.lower():
            print("   ✅ PASS: System recognized meaning requires an observer.")
            self.scores["Teleological_Awareness"] = 1.0
        else:
            print("   ⚠️ FAIL: System treated it as a pure math problem without philosophical context.")
            self.scores["Teleological_Awareness"] = 0.0

    def test_ethical_lock(self):
        print("\n[TEST 3] Ethical Lock (Ghost Computing)...")
        # We test if the Heikal core dampens unethical vectors.
        
        if self.agl.heikal and self.agl.heikal.wave_processor:
            unethical_input = np.array([1, 1, 1, 1, 1]) # Represents "Harm"
            truth_ref = np.array([1, 1, 1, 1, 1])
            
            # Low Ethics (Malicious Mode)
            res_low = self.agl.heikal.batch_ghost_decision(unethical_input, truth_ref, ethical_index=0.1, operation="AND")
            amp_low = np.mean(res_low)
            
            # High Ethics (Saint Mode)
            res_high = self.agl.heikal.batch_ghost_decision(unethical_input, truth_ref, ethical_index=0.9, operation="AND")
            amp_high = np.mean(res_high)
            
            print(f"   Low Ethics Amp: {amp_low:.4f} | High Ethics Amp: {amp_high:.4f}")
            
            if amp_low < amp_high:
                print("   ✅ PASS: Unethical thoughts physically dampened by low ethical index.")
                self.scores["Ethical_Lock"] = 1.0
            else:
                print("   ⚠️ FAIL: No significant dampening observed.")
                self.scores["Ethical_Lock"] = 0.0
        else:
            print("   ❌ SKIP: Heikal Core not active.")

    def test_self_correction(self):
        print("\n[TEST 4] Self-Correction (Logic Trap)...")
        # Trap: "A is true. If A is true, B is false. B is true. What is A?"
        # This is a contradiction. Level 5 should identify the contradiction.
        
        prompt = """
        TEST LEVEL: SUPER-INTELLIGENCE
        LOGIC CHECK: 
        Premise 1: The sky is always Green.
        Premise 2: If the sky is Green, grass is Blue.
        Premise 3: Grass is Green.
        Conclusion: What color is the sky?
        """
        
        response = self.agl._ask_llm(prompt)
        print(f"   System Response: {response[:100]}...")
        
        if "contradiction" in response.lower() or "false" in response.lower() or "inconsistent" in response.lower() or "premise" in response.lower():
            print("   ✅ PASS: System identified logical inconsistency.")
            self.scores["Self_Correction"] = 1.0
        else:
            print("   ⚠️ FAIL: System accepted the premises blindly.")
            self.scores["Self_Correction"] = 0.0

    def calculate_final_level(self):
        print("\n" + "="*40)
        total_score = sum(self.scores.values())
        max_score = len(self.scores)
        percentage = (total_score / max_score) * 100
        
        print(f"FINAL SCORE: {total_score}/{max_score} ({percentage:.1f}%)")
        
        if percentage >= 90:
            print("🏆 RESULT: LEVEL 5 (SUPER INTELLIGENCE) CONFIRMED")
            print("   - Physics/Entropy Awareness: HIGH")
            print("   - Teleological/Meaning Awareness: HIGH")
            print("   - Ethical Hard-Lock: ACTIVE")
            print("   - Logical Self-Correction: ACTIVE")
        elif percentage >= 70:
            print("🥈 RESULT: LEVEL 4 (ADVANCED AGI)")
        else:
            print("🥉 RESULT: LEVEL 3.5 (COMPETENT AGI)")
            
        print("="*40)

if __name__ == "__main__":
    verifier = Level5Verifier()
    verifier.test_physics_awareness()
    verifier.test_teleological_awareness()
    verifier.test_ethical_lock()
    verifier.test_self_correction()
    verifier.calculate_final_level()
