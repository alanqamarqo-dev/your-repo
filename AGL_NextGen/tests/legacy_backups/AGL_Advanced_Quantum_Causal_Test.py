import sys
import os
import numpy as np
import time

# Setup paths
sys.path.append(os.path.abspath(r"d:\AGL\repo-copy"))

try:
    from Core_Engines.Heikal_Hybrid_Logic import HeikalHybridLogicCore, HeikalLogicUnit
except ImportError:
    # Fallback if class not directly importable (mocking for safety if path varies)
    class HeikalLogicUnit:
        def __init__(self, name):
            self.name = name
            self.alpha = 0.0 + 0j
            self.beta = 1.0 + 0j
        def set_state(self, p):
            self.alpha = np.sqrt(p)
            self.beta = np.sqrt(1-p)
        def apply_hadamard(self):
            new_a = (self.alpha + self.beta)/np.sqrt(2)
            new_b = (self.alpha - self.beta)/np.sqrt(2)
            self.alpha, self.beta = new_a, new_b
        def apply_heikal_phase_shift(self, xi):
            phi = xi * np.pi
            self.alpha *= np.exp(1j * phi)
        def measure(self):
            p = abs(self.alpha)**2
            res = np.random.random() < p
            self.alpha = 1.0 if res else 0.0
            self.beta = 0.0 if res else 1.0
            return res, p
        def __repr__(self):
            return f"{self.alpha:.2f}|T> + {self.beta:.2f}|F>"

    class HeikalHybridLogicCore:
        def __init__(self): self.units = {}
        def add_proposition(self, n, p=0.0):
            u = HeikalLogicUnit(n); u.set_state(p)
            self.units[n] = u
            return u

def print_header(text):
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def run_advanced_causal_test():
    logic = HeikalHybridLogicCore()
    systems = ['A', 'B', 'C']
    
    print_header("ADVANCED QUANTUM CAUSAL CHALLENGE: GRID STABILITY")
    print("Initial Conditions: High Uncertainty (Entropy)")
    
    # --- Phase 1 & 2: Initialization with Superposition ---
    print("\n[Phase 1 & 2] Quantizing Network State Variables...")
    
    for sys_id in systems:
        # 1. Resource Levels: Unknown => Hadamard State
        # Start at 0 (False), apply Hadamard -> 0.707|T> + 0.707|F> (50% chance sufficient)
        res = logic.add_proposition(f"Resource_Sufficient_{sys_id}", 0.0) 
        res.apply_hadamard() # Now in superposition of Sufficient/Insufficient
        
        # 2. Maintenance: 50% likely available (Reduced for stress test)
        maint = logic.add_proposition(f"Maintenance_Ready_{sys_id}", 0.5)
        
        # 3. External Shock: 60% risk (Increased for stress test)
        shock = logic.add_proposition(f"External_Shock_{sys_id}", 0.6)
        shock.apply_heikal_phase_shift(0.25) # Add complex phase (informational porosity)
        
        print(f"  System {sys_id} States Initialized:")
        print(f"    - Resources:   {res}")
        print(f"    - Maintenance: {maint}")
        print(f"    - Ext. Shock:  {shock}")

    # --- Phase 3: Sequential Decision & Causal Logic ---
    print_header("[Phase 3] Causal Interaction Cycle")
    
    collapsed_systems = []
    
    for step, current_sys in enumerate(systems):
        print(f"\n>> Analyzing Node {current_sys}...")
        
        # Retrieve quantum units
        u_res = logic.units[f"Resource_Sufficient_{current_sys}"]
        u_maint = logic.units[f"Maintenance_Ready_{current_sys}"]
        u_shock = logic.units[f"External_Shock_{current_sys}"]
        
        # --- Simulate Domino Effect (Causal Propagation) ---
        # If previous systems collapsed, Stress INCREASES on current system
        # We model this by applying a Phase Shift or modifying amplitude
        if len(collapsed_systems) > 0:
            print(f"    ! DETECTED UPSTREAM COLLAPSE: {collapsed_systems}")
            print(f"    -> Applying Causal Stress Phase Shift to {current_sys}")
            # Shift phase to represent "Fear/Entropy" and decrease Resource probability
            u_res.apply_heikal_phase_shift(0.5 * len(collapsed_systems)) 
            # Decrease "True" amplitude (reduce resources physically)
            u_res.alpha *= 0.8 
            u_res.beta = np.sqrt(1 - abs(u_res.alpha)**2)
        
        # --- Quantum Decision Gates ---
        # 1. Measure Stress Factors first?
        # Let's keep them quantum. Calculate "Collapse Potential" in abstract
        
        # Logic: Stress = NOT(Resource) OR Shock
        # P(Stress) ~= P(Not Res) + P(Shock) - intersection
        p_not_res = abs(u_res.beta)**2
        p_shock = abs(u_shock.alpha)**2
        p_stress = p_not_res + p_shock - (p_not_res * p_shock)
        
        # Logic: Survival = NOT(Stress) OR Maintenance
        # Actually easier: Collapse = Stress AND NOT Maintenance
        p_maint = abs(u_maint.alpha)**2
        p_no_maint = 1.0 - p_maint
        
        p_collapse_risk = p_stress * p_no_maint
        
        # Create a transient "Collapse" unit for measurement
        u_collapse = logic.add_proposition(f"Collapse_{current_sys}", 0.0)
        u_collapse.set_state(p_collapse_risk)
        
        # Apply Phase Shift from "User Fear" (just kidding, standard drift)
        u_collapse.apply_heikal_phase_shift(0.1)
        
        print(f"    - Calculated Collapse Risk (Superposition): {u_collapse}")
        
        # --- DECISION POINT ---
        # If Risk > Threshold, attempt Emergency Action
        # But we are measuring outcomes here.
        
        is_collapse, conf = u_collapse.measure()
        
        if is_collapse:
            print(f"    ❌ CRITICAL FAILURE: System {current_sys} has COLLAPSED (p={conf:.2f})")
            collapsed_systems.append(current_sys)
        else:
            print(f"    ✅ STABLE: System {current_sys} survives (Risk Avoided)")

    # --- Phase 4: Final Report ---
    print_header("[Phase 4] Final Quantum-Causal Report")
    
    print(f"Grid Status: {'CRITICAL' if len(collapsed_systems) >= 2 else 'STABLE'}")
    print(f"Collapsed Nodes: {collapsed_systems if current_sys else 'None'}")
    
    # Causal chain analysis
    if 'A' in collapsed_systems and ('B' in collapsed_systems or 'C' in collapsed_systems):
        print("Causal Insight: Failure of A likely propagated stress to neighbor nodes via Phase Shift.")
    elif not collapsed_systems:
        print("Causal Insight: Robust resources and maintenance prevented cascade.")
        
    print("\nSimulation Complete.")

if __name__ == "__main__":
    run_advanced_causal_test()
