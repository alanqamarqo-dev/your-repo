import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Resonance_Optimizer import ResonanceOptimizer

def test_heikal_vs_standard():
    print("=== Testing Heikal Tunneling Algorithm vs Standard WKB ===")
    
    # Initialize Optimizer
    optimizer = ResonanceOptimizer(h_bar=1.0, mass=1.0, barrier_width=2.0)
    
    # Test Case: A deep local minimum (High Barrier)
    # Current Score: 100
    # Candidate Score: 99.5 (Worse by 0.5)
    # Barrier Height: 0.5
    current_score = 100.0
    candidate_score = 99.5 # Very low barrier
    delta_E = candidate_score - current_score # -0.5
    barrier_height = abs(delta_E)
    
    print(f"\nScenario: Trying to escape a local minimum.")
    print(f"  Current Score: {current_score}")
    print(f"  Candidate Score: {candidate_score}")
    print(f"  Energy Deficit: {abs(delta_E)}")
    print(f"  Barrier Width (L): {optimizer.L}")
    
    # 1. Standard WKB (Simulate by setting porosity to 0)
    optimizer.heikal_porosity = 0.0
    prob_standard = optimizer._heikal_tunneling_prob(delta_E, barrier_height)
    print(f"\n[Standard WKB] Tunneling Probability: {prob_standard:.10f}")
    
    # 2. Heikal Tunneling (Enable porosity)
    optimizer.heikal_porosity = 1.5 # Default
    optimizer.lattice_spacing = 0.5 # Significant lattice effect
    prob_heikal = optimizer._heikal_tunneling_prob(delta_E, barrier_height)
    print(f"[Heikal Algorithm] Tunneling Probability: {prob_heikal:.10f}")
    
    # Calculate Improvement
    improvement = (prob_heikal - prob_standard) / prob_standard * 100
    print(f"\n>>> Improvement Factor: +{improvement:.2f}%")
    
    if prob_heikal > prob_standard:
        print("\nSUCCESS: Heikal Algorithm successfully increased tunneling probability!")
        print("The system is now more likely to escape local minima using the InfoQuantum Lattice effect.")
    else:
        print("\nFAILURE: No improvement detected.")

    # Simulation of Escape Rates
    print("\n--- Monte Carlo Simulation (10,000 attempts) ---")
    attempts = 10000
    
    # Standard
    optimizer.heikal_porosity = 0.0
    escapes_std = sum([1 for _ in range(attempts) if optimizer.optimize_search(current_score, candidate_score)[0]])
    
    # Heikal
    optimizer.heikal_porosity = 1.5
    escapes_heikal = sum([1 for _ in range(attempts) if optimizer.optimize_search(current_score, candidate_score)[0]])
    
    print(f"Standard Escapes: {escapes_std}/{attempts} ({escapes_std/attempts*100:.2f}%)")
    print(f"Heikal Escapes:   {escapes_heikal}/{attempts} ({escapes_heikal/attempts*100:.2f}%)")
    
    ratio = escapes_heikal / (escapes_std + 1e-9)
    print(f"Efficiency Ratio: {ratio:.2f}x more effective at escaping traps.")

if __name__ == "__main__":
    test_heikal_vs_standard()
