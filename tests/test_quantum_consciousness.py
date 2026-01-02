
import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Consciousness.Self_Model import SelfModel

def test_quantum_stream():
    print("--- Testing Quantum Stream of Consciousness ---")
    
    self_model = SelfModel()
    
    if not self_model.quantum_enabled:
        print("❌ Quantum Resonance not enabled (Import failed?)")
        return

    print("✅ Quantum Resonance Enabled in SelfModel")

    # Scenario: The mind is wandering.
    # It has 3 competing thoughts.
    thoughts = [
        "I should check the logs.",  # Boring, Low Energy
        "The user is asking about Consciousness.", # High Relevance, High Energy
        "I wonder if I can calculate Pi to infinity." # High Barrier, Low Relevance
    ]
    
    print(f"Input Thoughts: {len(thoughts)}")
    for t in thoughts:
        print(f" - {t}")

    # The logic in stream_consciousness assigns:
    # "Consciousness" -> High Energy (0.5 + 0.3? No, 'AGI' or 'Quantum' gets +0.3)
    # Let's adjust the input to trigger the keywords defined in SelfModel.py
    
    thoughts_v2 = [
        "Routine maintenance check.", # Energy 0.5, Barrier 0.4 -> Classical Pass (Prob 1.0)
        "Analyzing Quantum AGI structures.", # Energy 0.5+0.3=0.8, Barrier 0.4 -> Classical Pass (Prob 1.0)
        "A very long and complex thought about the nature of the universe that goes on and on and on and on..." # Barrier > 0.6
    ]
    
    # Let's try to force a tunneling scenario.
    # We need Energy < Barrier, but High Probability.
    # In SelfModel.py:
    # if "AGI" or "Quantum": energy += 0.3
    # if len > 100: barrier += 0.2
    
    # Case 1: High Barrier, Low Energy -> Should fail or be low prob
    # Case 2: High Barrier, High Energy -> Should tunnel
    
    complex_boring = "A" * 101 # Barrier 0.6, Energy 0.5. Delta = 0.1. Tunneling needed.
    complex_exciting = "Quantum " + ("A" * 101) # Barrier 0.6, Energy 0.8. Delta = -0.2. Classical Pass.
    
    # Wait, if Energy > Barrier, it's classical.
    # We want a case where Energy < Barrier, but it still wins against others?
    # Or just verify it works.
    
    selected = self_model.stream_consciousness(thoughts)
    print(f"\nSelected Thought: '{selected}'")
    
    # Let's test the specific tunneling math by mocking the inputs to the internal logic
    # We can't easily mock inside the method, so we rely on the output.
    
    # Let's try a list where the "Quantum" thought is selected.
    inputs = [
        "Just a normal log line.",
        "Quantum Resonance is active.",
        "Another log line."
    ]
    
    selected = self_model.stream_consciousness(inputs)
    print(f"Selection from mixed bag: '{selected}'")
    
    if "Quantum" in selected:
        print("✅ System prioritized the Quantum thought (High Energy).")
    else:
        print("❌ System failed to prioritize Quantum thought.")

if __name__ == "__main__":
    test_quantum_stream()
