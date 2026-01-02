import numpy as np
import matplotlib.pyplot as plt

# Simulation Constants
M = 1.0  # Mass of Black Hole
Rs = 2 * M  # Schwarzschild Radius
L_p = 1e-35 # Planck Length (scaled for simulation)

def simulate_tunneling_probability(lattice_spacing_ratio):
    """
    Simulates tunneling probability P = exp(-2 * integral(sqrt(V-E)))
    In our lattice theory, the effective potential barrier V_eff drops 
    as lattice spacing approaches Planck scale.
    """
    # Classical Barrier Height at Horizon is infinite (coordinate singularity)
    # But in Lattice Theory, it's finite ~ 1/lattice_spacing
    
    # Let's model the effective barrier height V_eff
    # If spacing is large (classical), V_eff -> infinity -> Prob -> 0
    # If spacing is small (quantum), V_eff is finite -> Prob > 0
    
    # Model: V_eff = k / lattice_spacing
    k = 10.0
    V_eff = k / lattice_spacing_ratio
    
    # WKB Approximation for Tunneling Probability
    # P ~ exp(-V_eff)
    prob = np.exp(-V_eff)
    return prob

# Generate lattice spacings (from Classical scale 1.0 down to Quantum scale 0.01)
lattice_spacings = np.logspace(-2, 0, 100) # 0.01 to 1.0
tunneling_probabilities = [simulate_tunneling_probability(d) for d in lattice_spacings]

plt.figure(figsize=(10, 6))
plt.plot(lattice_spacings, tunneling_probabilities, label='Tunneling Probability', color='purple', linewidth=2)
plt.xscale('log')
plt.xlabel('Lattice Spacing (Relative to Rs)')
plt.ylabel('Tunneling Probability')
plt.title('Quantum Tunneling through Event Horizon vs Lattice Spacing')
plt.grid(True, which="both", ls="-", alpha=0.2)
plt.axvline(x=1.0, color='r', linestyle='--', label='Classical Limit (Rs)')
plt.legend()
plt.savefig('tunneling_probability_stress_test.png')

print("Stress Test Complete.")
print(f"Tunneling Prob at Classical Scale (1.0): {simulate_tunneling_probability(1.0):.4e}")
print(f"Tunneling Prob at Quantum Scale (0.01): {simulate_tunneling_probability(0.01):.4e}")
