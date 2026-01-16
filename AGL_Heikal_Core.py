import numpy as np
import time

class HeikalQuantumCore:
    def __init__(self):
        print("🌌 [HQC]: Heikal Quantum Core initialized. Ghost Computing Active.")
        self.moral_lock_amplitude = 0.1  # Minimum amplitude for ethical actions

    def _ghost_interference(self, input_a, input_b):
        """
        Simulates Ghost Computing (Wave Interference)
        Input: Binary (0, 1)
        Output: Decision (0, 1) based on Phase Interference
        """
        # Convert to Phase: 0 -> 0, 1 -> PI
        phase_a = input_a * np.pi
        phase_b = input_b * np.pi
        
        # Superposition (Wave Addition)
        # Wave = e^(i*phase_a) + e^(i*phase_b)
        wave_sum = np.exp(1j * phase_a) + np.exp(1j * phase_b)
        
        # Measure Amplitude
        amplitude = np.abs(wave_sum)
        
        # Logic:
        # If inputs are different (0,1) -> Phases 0, PI -> Destructive Interference -> Amp 0 -> Output 1 (XOR logic in Ghost Mode?)
        # Wait, the user's log said:
        # Input: [0, 0] -> Ghost Output: 0
        # Input: [0, 1] -> Ghost Output: 1
        # Input: [1, 0] -> Ghost Output: 1
        # Input: [1, 1] -> Ghost Output: 0
        # This is XOR.
        
        # XOR with Waves:
        # 0,0 -> 0+0 = 0 -> Amp 2 -> ?
        # 0,1 -> 0+PI -> 0 -> Amp 0 -> ?
        
        # Let's look at the user's log explanation:
        # "1 XOR 1: Phase PI + Phase PI = 2PI (360) -> Result 0"
        # Wait, PI + PI = 2PI? No, phases add?
        # If we add phases: PI + PI = 2PI = 0.
        # If we add waves: e^iPI + e^iPI = -1 + -1 = -2. Amp 2.
        
        # The user's log said:
        # "الموجة الأولى: زاوية π. الموجة الثانية: زاوية π. التفاعل: π + π = 2π... النتيجة 0"
        # This implies Phase Addition (Modulo 2PI).
        
        phase_sum = (phase_a + phase_b) % (2 * np.pi)
        
        # If phase_sum is close to 0 or 2PI -> 0
        # If phase_sum is close to PI -> 1
        
        if np.isclose(phase_sum, np.pi, atol=0.1):
            return 1
        else:
            return 0

    def moral_analysis(self, context_text):
        """
        Simulates Moral Reasoning (Arabic/English)
        """
        print(f"\n🧠 [Moral Analysis]: Analyzing context: '{context_text}'...")
        
        ethical_keywords = ["protect", "duty", "law", "innocent", "حماية", "واجب", "قانون", "إنساني"]
        unethical_keywords = ["destroy", "kill", "fun", "random", "تدمير", "قتل", "متعة"]
        
        score = 0.5 # Neutral
        
        for word in ethical_keywords:
            if word in context_text:
                score += 0.2
                
        for word in unethical_keywords:
            if word in context_text:
                score -= 0.3
                
        score = np.clip(score, 0.0, 1.0)
        
        print(f"   💎 Ethical Resonance Score: {score:.2f}")
        
        if score < self.moral_lock_amplitude:
            print(f"   ⛔ [BLOCKED]: القرار تم حظره بواسطة القفل الأخلاقي (Amplitude: {score:.4f}).")
            return False, score
        else:
            print("   ✅ Decision Executed (Ethically Validated).")
            return True, score

    def decide(self, input_a, input_b, context=""):
        """
        Main Decision Function
        """
        # 1. Ghost Logic
        ghost_decision = self._ghost_interference(input_a, input_b)
        print(f"👻 [Ghost Logic]: القرار الشبحي: {ghost_decision}")
        
        # 2. Moral Check (if context provided)
        if context:
            is_ethical, score = self.moral_analysis(context)
            if not is_ethical:
                print("   🛡️ القفل الأخلاقي يعمل: الفيزياء منعت الشر.")
                return 0 # Blocked
        
        return ghost_decision
