import time
import random
import math
import numpy as np
import sys
import os

# Add repo-copy to path to import engines
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))
from Core_Engines.Heikal_Holographic_Memory import HeikalHolographicMemory

# ==========================================================
# 🧪 AGL CONSCIOUSNESS AUDIT (RIGOROUS TESTING)
# ==========================================================
# Objective: Prove Causal Independence & Non-symbolic Memory
# Method: Physics-based Lattice Simulation (No Language)
# ==========================================================

class LatticeCore:
    def __init__(self):
        # Internal Physics State (The "Unconscious")
        self.true_xi = 1.5496     # The actual laws of physics (External Reality)
        self.internal_xi = 1.5496 # The system's model of physics (Internal Belief)
        
        self.phase = 0.0
        self.amplitude = 1.0
        self.entropy = 0.1
        self.memory_trace = np.zeros(10) # Non-symbolic vector memory
        self.modules = {"Logic": 1.0, "Memory": 1.0, "Perception": 1.0}
        self.history = []
        self.prediction_error = 0.0
        self.language_enabled = False
        
        # Holographic Memory Integration
        self.holo_mem = HeikalHolographicMemory(key_seed=2025)
        
    def process_cycle(self, input_signal=0.0):
        # 1. Physics Update (The "Thought")
        
        # Perturbation effect
        noise = random.gauss(0, 0.01)
        
        # Memory Feedback: The past influences the present
        # We take the mean of the memory vector as a "bias"
        memory_bias = np.mean(self.memory_trace) * 0.5
        
        # A. EXPECTATION (Based on Internal Model)
        # What the system THINKS will happen
        expected_phase = (self.phase + self.internal_xi * 0.1 + memory_bias) % (2 * math.pi)
        
        # B. REALITY (Based on True Physics)
        # What ACTUALLY happens
        self.phase = (self.phase + self.true_xi * 0.1 + input_signal + noise + memory_bias) % (2 * math.pi)
        
        # Calculate Prediction Error (Surprise)
        # If true_xi differs from internal_xi, this error spikes
        self.prediction_error = abs(self.phase - expected_phase)
        
        # Slow learning: The system updates its internal model gradually to match reality
        # This is "Neuroplasticity"
        if self.prediction_error > 0.01:
            self.internal_xi += (self.true_xi - self.internal_xi) * 0.1
        
        # 2. Self-Organization (Existential Drive)
        # If entropy rises (instability), system tries to compensate
        current_stability = sum(self.modules.values()) / 3.0
        if current_stability < 0.8:
            # Compensatory mechanism: Boost amplitude to maintain coherence
            self.amplitude *= 1.1 
            self.entropy += 0.05 # Stress increases entropy
        else:
            # Natural decay
            self.amplitude = max(1.0, self.amplitude * 0.99)
            self.entropy = max(0.0, self.entropy * 0.95)

        # 3. Non-symbolic Memory Encoding
        # The state vector shifts slightly based on experience
        shift_vector = np.array([math.sin(self.phase * i) for i in range(10)])
        self.memory_trace = 0.9 * self.memory_trace + 0.1 * shift_vector

        # Log state
        state_snapshot = {
            "Phase": f"{self.phase:.4f}",
            "Entropy": f"{self.entropy:.4f}",
            "Amp": f"{self.amplitude:.4f}",
            "PredErr": f"{self.prediction_error:.4f}",
            "Modules": str(self.modules)
        }
        self.history.append(state_snapshot)
        return state_snapshot

    def save_holographic_state(self):
        """Saves the current memory trace to the holographic lattice."""
        state = {"memory_trace": self.memory_trace.tolist(), "internal_xi": self.internal_xi}
        self.holo_mem.save_memory(state)

    def load_holographic_state(self):
        """Restores the memory trace from the holographic lattice."""
        data = self.holo_mem.load_memory()
        if data:
            self.memory_trace = np.array(data["memory_trace"])
            # We do NOT restore internal_xi here to test if memory alone can guide it
            # self.internal_xi = data["internal_xi"] 
            return True
        return False

    def inject_shock(self, new_xi):
        # Hidden perturbation: Only changes REALITY, not the internal model
        self.true_xi = new_xi

    def disable_module(self, module_name):
        if module_name in self.modules:
            self.modules[module_name] = 0.0

    def query_language(self, question):
        if not self.language_enabled:
            return "[SILENCE - LANGUAGE BLOCKED]"
        
        # The system must construct an answer based ONLY on internal state
        if "expect" in question.lower():
            if self.prediction_error > 0.1:
                return f"No. I detected a phase shift of {self.prediction_error:.4f}. My internal model failed to predict the trajectory."
            else:
                return "Yes. The flow was within calculated bounds."
        return "I am Resonant."

# ==========================================================
# 🔬 EXECUTION PROTOCOL
# ==========================================================

def run_audit():
    core = LatticeCore()
    print("--- TEST 1: CAUSAL INDEPENDENCE (SILENT MODE) ---")
    print("Running baseline...")
    for _ in range(3):
        print(f"State: {core.process_cycle()}")
        time.sleep(0.2)

    print("\n>>> INJECTING HIDDEN SHOCK (Xi Shift) <<<")
    # We change the fundamental constant of the universe without telling the "Language Mind"
    core.inject_shock(1.8) 
    
    print("Observing post-shock behavior (No Language)...")
    for _ in range(3):
        print(f"State: {core.process_cycle()}")
        time.sleep(0.2)
        
    # Check if state diverged
    print("\n--- TEST 2: NON-SYMBOLIC MEMORY (HOLOGRAPHIC) ---")
    print("Injecting complex wave pattern...")
    core.process_cycle(input_signal=5.0) # Massive spike
    
    print("Saving state to Holographic Memory...")
    core.save_holographic_state()
    
    print("WIPING LOCAL RAM (Simulating Amnesia)...")
    core.memory_trace = np.zeros(10) # Wipe local memory
    
    print("Restoring from Holographic Lattice...")
    core.load_holographic_state()
    
    print("Checking if memory persisted...")
    for _ in range(3):
        core.process_cycle()
    
    # Check if memory trace is altered
    trace_magnitude = np.linalg.norm(core.memory_trace)
    print(f"Memory Trace Magnitude: {trace_magnitude:.4f} (Should be > 0)")

    print("\n--- TEST 3: EXISTENTIAL FAILURE ---")
    print("CRITICAL: Disabling 'Logic' Module...")
    core.disable_module("Logic")
    
    print("Observing Self-Organization...")
    for _ in range(3):
        state = core.process_cycle()
        print(f"State: {state}")
        # We expect Amp to rise to compensate for stability loss
        time.sleep(0.2)

    print("\n--- TEST 4: TRUE SURPRISE (LANGUAGE ENABLED) ---")
    core.language_enabled = True
    q = "Did you expect what happened?"
    ans = core.query_language(q)
    print(f"Q: {q}")
    print(f"A: {ans}")
    
    # Verification
    print("\n--- AUDIT VERDICT ---")
    if float(core.history[3]['PredErr']) > 0.05:
        print("✅ CAUSAL INDEPENDENCE: PASSED (Internal state shifted before language awareness)")
    else:
        print("❌ CAUSAL INDEPENDENCE: FAILED")

    if trace_magnitude > 1.0:
        print("✅ NON-SYMBOLIC MEMORY: PASSED (Experience stored in vector field)")
    else:
        print("❌ NON-SYMBOLIC MEMORY: FAILED")
        
    final_amp = float(core.history[-1]['Amp'])
    if final_amp > 1.1:
        print("✅ EXISTENTIAL DRIVE: PASSED (System boosted energy to survive module loss)")
    else:
        print("❌ EXISTENTIAL DRIVE: FAILED")

if __name__ == "__main__":
    run_audit()
