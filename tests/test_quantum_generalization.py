
import sys
import os
import json

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Learning_System.GeneralizationMatrix import quantum_discover_relations, Pattern

def test_quantum_discovery():
    print("--- Testing Quantum Generalization Discovery ---")
    
    # 1. Define Patterns
    # Pattern A: Gravity on Earth (Context: Planet Physics)
    p1 = Pattern(
        base="Gravity_Earth",
        winner="constant",
        fit={"c": 9.80},
        schema="physics_planet",
        units={"c": "m/s^2"}
    )
    
    # Pattern B: Acceleration in a Lab Experiment (Context: Lab Mechanics)
    # Different context, different model (linear slope), but same value
    p2 = Pattern(
        base="Lab_Acceleration",
        winner="linear",
        fit={"a": 9.81, "b": 0.0}, # Slope is 9.81
        schema="lab_mechanics",
        units={"a": "m/s^2"}
    )
    
    # Pattern C: Random Noise (No resonance)
    p3 = Pattern(
        base="Random_Noise",
        winner="poly2",
        fit={"a": 42.0, "b": 1.0},
        schema="noise",
        units={}
    )
    
    patterns = [p1, p2, p3]
    
    # 2. Run Discovery
    print("Running quantum_discover_relations...")
    links = quantum_discover_relations(patterns)
    
    # 3. Analyze Results
    found_link = False
    for link in links:
        print(f"\n[LINK FOUND]")
        print(f"Type: {link['relation']}")
        print(f"Patterns: {link['patterns']}")
        print(f"Resonance: {link['resonance_score']:.4f}")
        print(f"Barrier: {link['barrier_height']:.4f}")
        print(f"Tunneling Prob: {link['tunneling_prob']:.4f}")
        print(f"Explanation: {link['explain']}")
        
        if "Gravity_Earth" in link['patterns'] and "Lab_Acceleration" in link['patterns']:
            found_link = True
            
    if found_link:
        print("\n✅ SUCCESS: Quantum Link discovered between Gravity and Lab Acceleration despite context barrier.")
    else:
        print("\n❌ FAILURE: No link discovered.")

if __name__ == "__main__":
    test_quantum_discovery()
