
import sys
import os
import asyncio
import time

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

# Mock dependencies if needed, or just rely on the class handling None
from dynamic_modules.unified_agi_system import UnifiedAGISystem

def test_unified_quantum():
    print("--- Testing Unified AGI Quantum Integration ---")
    
    # 1. Initialize System with minimal registry
    registry = {
        'AdaptiveMemory': None,
        'ExperienceMemory': None,
        'Causal_Graph': None,
        'Reasoning_Layer': None,
        'HYPOTHESIS_GENERATOR': None,
        'Meta_Learning': None,
        'Creative_Innovation': None,
        'Self_Reflective': None,
        'Mathematical_Brain': None
    }
    
    system = UnifiedAGISystem(registry)
    
    if not system.resonance_optimizer:
        print("❌ ResonanceOptimizer not loaded. Check imports.")
        return

    print("✅ ResonanceOptimizer loaded successfully.")
    
    # 2. Test Quantum Mode Selection
    
    # Case A: High Energy, Low Barrier (Obvious match)
    # "I want to prove a quantum physics theory" -> Keywords: prove, quantum, physics, theory.
    # Energy should be high. Barrier for 'scientific' is 0.7.
    input_a = "I want to prove a new quantum physics theory about time"
    modes_a = system._quantum_mode_selection(input_a)
    print(f"\nInput: '{input_a}'")
    print(f"Selected Modes: {modes_a}")
    if 'scientific' in modes_a:
        print("✅ Scientific mode selected (Direct Resonance).")
    else:
        print("❌ Scientific mode NOT selected.")
        
    # Case B: Low Energy, High Barrier (Tunneling Test)
    # "I have a hunch about how the universe works" -> Keywords: None of the explicit ones?
    # Wait, my keywords were: ["theory", "physics", "quantum", "simulation", "prove", "hypothesis"]
    # Let's try a subtle one that requires tunneling.
    # "I have a hypothesis" -> 1 keyword. Short sentence.
    # Energy = (1 * 2.0) / sqrt(4) = 1.0.
    # Barrier = 0.7.
    # Energy > Barrier. This is classical passage.
    
    # Let's try something with NO keywords but we want it to tunnel?
    # The current implementation relies on keywords for Energy.
    # If Energy is 0, Tunneling Prob is exp(-2*L*sqrt(2m*V)).
    # If Energy=0, V=0.7.
    # Prob = exp(-2 * 1 * sqrt(2 * 1 * 0.7)) = exp(-2 * 1.18) = exp(-2.36) = 0.09.
    # Threshold is 0.25. So 0 energy won't tunnel.
    
    # We need SOME energy, but less than barrier.
    # Barrier = 0.7.
    # We need Energy < 0.7.
    # Say Energy = 0.5.
    # Deficit = 0.2.
    # Prob = exp(-2 * sqrt(2 * 0.2)) = exp(-2 * 0.63) = exp(-1.26) = 0.28.
    # 0.28 > 0.25. Tunneling!
    
    # How to get Energy = 0.5?
    # Energy = (Matches * 2.0) / sqrt(Words).
    # If Matches = 1.
    # We need 2.0 / sqrt(Words) = 0.5.
    # sqrt(Words) = 4. Words = 16.
    # So a 16-word sentence with 1 keyword.
    
    input_b = "I was walking down the street and suddenly had a strange hypothesis about the color blue."
    # Words: ~16. Keyword: "hypothesis".
    # Energy ~ 0.5. Barrier 0.7.
    # Should tunnel.
    
    modes_b = system._quantum_mode_selection(input_b)
    print(f"\nInput: '{input_b}'")
    print(f"Selected Modes: {modes_b}")
    if 'scientific' in modes_b:
        print("✅ Scientific mode selected via QUANTUM TUNNELING (Low Energy/High Noise).")
    else:
        print("❌ Scientific mode NOT selected (Tunneling failed).")

    # Case C: Creative Tunneling
    # Barrier 0.5.
    # We need Energy < 0.5.
    # Matches = 1. Words > 16.
    input_c = "Once upon a time in a land far away there was a little boy who liked to imagine dragons."
    # Keyword: "imagine". Words: ~18.
    # Energy ~ 2/4.2 = 0.47.
    # Deficit = 0.03.
    # Prob should be high.
    
    modes_c = system._quantum_mode_selection(input_c)
    print(f"\nInput: '{input_c}'")
    print(f"Selected Modes: {modes_c}")
    if 'creative' in modes_c:
        print("✅ Creative mode selected via Tunneling.")

if __name__ == "__main__":
    test_unified_quantum()
