import sys
import os
import json
import numpy as np

# Add repo root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'repo-copy'))

from Scientific_Systems.Integrated_Simulation_Engine_Enhanced import PhysicsBasedSimulator

def solve_fusion_problem():
    engine = PhysicsBasedSimulator()
    
    print("--- Scientific Problem Solving: Fusion Reactor Design ---\n")
    print("Problem: 'Design a nuclear fusion reactor with a solution for unstable plasma'")
    
    # Step 1: Initial Design (Likely Unstable)
    # High temperature and density, but weak magnetic field
    initial_design = {
        "plasma_density": 2e20,      # 2e20 m^-3
        "temperature": 1.74e8,       # 15 keV (~174 Million K)
        "confinement_time": 3.0,     # 3 seconds
        "magnetic_field": 3.0        # 3 Tesla (Too weak for this pressure)
    }
    
    print(f"\n1. Analyzing Initial Design: {json.dumps(initial_design, indent=2)}")
    results_initial = engine.simulate_fusion_reactor(initial_design)
    
    print(f"   Result: Feasible={results_initial['feasibility']}")
    if not results_initial['feasibility']:
        print("   > Detected Issues:")
        for issue in results_initial['issues']:
            print(f"     - {issue}")
            
    # Step 2: Extract Solution from Analysis
    # The engine suggests increasing B field. Let's calculate the required B.
    # From the error message or recalculation:
    # P_plasma = nkT = 2e20 * 1.38e-23 * 1.74e8 = 480240 Pa
    # Beta_limit = 0.05
    # P_mag_required = P_plasma / 0.05 = 9,604,800 Pa
    # B_required = sqrt(2 * mu0 * P_mag_required)
    # B = sqrt(2 * 1.257e-6 * 9.6e6) ~ sqrt(24) ~ 4.9 Tesla
    
    print("\n2. Applying Scientific Solution...")
    print("   > Hypothesis: Increasing Magnetic Field (Magnetic Pressure) will stabilize Plasma Beta.")
    print("   > Calculation: B_required > 5.0 Tesla")
    
    optimized_design = initial_design.copy()
    optimized_design["magnetic_field"] = 6.0 # Increase to 6T for safety margin
    
    print(f"\n3. Testing Optimized Design: {json.dumps(optimized_design, indent=2)}")
    results_optimized = engine.simulate_fusion_reactor(optimized_design)
    
    print(f"   Result: Feasible={results_optimized['feasibility']}")
    if results_optimized['feasibility']:
        print("   > Stability Verified: Beta Limit Satisfied")
        print(f"   > Plasma Beta: {results_optimized['numerical_results']['beta']:.4f} (Limit < 0.05)")
        print(f"   > Ignition Status: {results_optimized['numerical_results']['ignition']}")
        print(f"   > Lawson Value: {results_optimized['numerical_results']['lawson_value']:.2e}")
        print("   > Conclusion: Design is scientifically valid.")
    else:
        print(f"   Issues: {results_optimized['issues']}")

if __name__ == "__main__":
    solve_fusion_problem()
