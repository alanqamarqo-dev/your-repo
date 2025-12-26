import sys
import os
import numpy as np

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Heikal_Hybrid_Logic import HeikalHybridLogicCore

def test_hybrid_logic():
    print("=== Testing Heikal Hybrid Logic Core ===")
    
    core = HeikalHybridLogicCore()
    
    # Scenario: The system is debating two contradictory ideas
    # Idea A: "The solution is aggressive."
    # Idea B: "The solution is passive."
    
    print("\n1. Initialization (Classical State)")
    prop_A = core.add_proposition("Aggressive", initial_prob=1.0) # Definitely True
    prop_B = core.add_proposition("Passive", initial_prob=0.0)    # Definitely False
    
    print(f"  {prop_A}")
    print(f"  {prop_B}")
    
    print("\n2. Applying Hadamard Gate (Entering Superposition)")
    # We put both ideas into a state of uncertainty
    prop_A.apply_hadamard()
    prop_B.apply_hadamard()
    
    print(f"  {prop_A}")
    print(f"  {prop_B}")
    print("  >> Both ideas are now 50% True and 50% False simultaneously.")
    
    print("\n3. Applying Heikal Phase Shift (Lattice Influence)")
    # The lattice structure (context) influences the phase
    prop_A.apply_heikal_phase_shift(xi_porosity=0.5)
    print(f"  {prop_A}")
    print("  >> Phase rotated. Probability magnitude unchanged, but interference potential altered.")
    
    print("\n4. Entanglement (Hybridization)")
    # We force the ideas to interact
    core.entangle("Aggressive", "Passive")
    print(f"  {prop_A}")
    print(f"  {prop_B}")
    print("  >> The ideas are now coupled. Measuring one will determine the other.")
    
    print("\n5. Measurement (Collapse)")
    res_A, prob_A = prop_A.measure()
    res_B, prob_B = prop_B.measure()
    
    print(f"  Result A: {res_A}")
    print(f"  Result B: {res_B}")
    
    if res_A == res_B:
        print("\nCONCLUSION: The system synthesized a Hybrid State where both are True (or False).")
        print("This represents a 'Dialectical Synthesis' - finding a third path.")
    else:
        print("\nCONCLUSION: The system collapsed to a classical choice.")

if __name__ == "__main__":
    test_hybrid_logic()
