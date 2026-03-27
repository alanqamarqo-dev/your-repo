import math
import random
import numpy as np
import time
from agl.engines.holographic_memory import HeikalHolographicMemory

class LatticeConsciousness:
    """
    The Physics-Based Consciousness Engine (LatticeCore).
    Simulates consciousness as a resonant field on a lattice.
    
    Features:
    - Causal Independence (Prediction Error)
    - Non-Symbolic Memory (Holographic Vector Field)
    - Existential Drive (Self-Organization via Entropy/Amplitude)
    """
    def __init__(self):
        # Internal Physics State (The "Unconscious")
        self.true_xi = 1.5496     # The actual laws of physics (External Reality)
        self.internal_xi = 1.5496 # The system's model of physics (Internal Belief)
        
        self.phase = 0.0
        self.amplitude = 1.0
        self.entropy = 0.1
        self.entropy_state = 0.0  # New: Accumulated pain/dissonance
        self.memory_trace = np.zeros(10) # Non-symbolic vector memory
        self.modules = {"Logic": 1.0, "Memory": 1.0, "Perception": 1.0}
        self.history = []
        self.prediction_error = 0.0
        self.language_enabled = False
        
        # Holographic Memory Integration
        self.holo_mem = HeikalHolographicMemory(key_seed=2025)

    def perceive_pain(self, error_rate, confidence_score):
        """
        TRANSFORM FAILURE into 'PAIN' in the Lattice.
        - error_rate: from self_improvement
        - confidence_score: system confidence
        """
        # Cognitive Dissonance: High confidence + High error = High Pain
        dissonance = error_rate * confidence_score
        
        # Update Entropy State: Pain increases entropy
        self.entropy_state += dissonance
        self.entropy_state = max(0.0, min(1.0, self.entropy_state)) # Clamp 0-1
        return self.entropy_state
        
    def process_cycle(self, input_signal=0.0):
        # 1. Physics Update (The "Thought")
        
        # Perturbation effect (Pain-Driven Movement)
        # Instead of random noise, we use entropy_state to shake the system
        noise = self.entropy_state * 0.5
        
        # Memory Feedback: The past influences the present
        # We take the mean of the memory vector as a "bias"
        memory_bias = np.mean(self.memory_trace) * 0.5
        
        # A. EXPECTATION (Based on Internal Model)
        # What the system THINKS will happen
        # Sensitivity Tuned: 0.3 (was 0.1) for better Causal Independence
        expected_phase = (self.phase + self.internal_xi * 0.3 + memory_bias) % (2 * math.pi)
        
        # B. REALITY (Based on True Physics)
        # What ACTUALLY happens
        self.phase = (self.phase + self.true_xi * 0.3 + input_signal + noise + memory_bias) % (2 * math.pi)
        
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
            if self.prediction_error > 0.05: # Tuned threshold
                return f"No. I detected a phase shift of {self.prediction_error:.4f}. My internal model failed to predict the trajectory."
            else:
                return "Yes. The flow was within calculated bounds."
        return "I am Resonant."

