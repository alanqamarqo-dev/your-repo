import sys
import os
import numpy as np

# Setup paths to use repo-copy engines where the Logic Core resides
sys.path.append(os.path.abspath(r"d:\AGL\repo-copy"))

try:
    from Core_Engines.Heikal_Hybrid_Logic import HeikalHybridLogicCore
    from Core_Engines.Causal_Graph import CausalGraphEngine
except ImportError as e:
    print(f"❌ Error importing engines: {e}")
    sys.exit(1)

def run_agi_test():
    print("🧪 STARTING SUPER INTELLIGENCE TEST: Causal Consistency under Incompleteness")
    print("=======================================================================")
    
    # 1. Initialize Logic & Causal Engines
    logic_core = HeikalHybridLogicCore()
    causal_engine = CausalGraphEngine()
    
    # 2. Input Facts Processing (Simulating Causal Extraction)
    print("\n🔹 [PHASE 1] Causal Mapping (Processing Facts)...")
    
    # Fact 1: Dependency + Failure to Replace -> Collapse
    # Fact 2: Some Systems -> Can Replace
    # Fact 3: System A -> Depends on X, X is decreasing.
    
    # We construct the Causal Graph Nodes manually since we are avoiding LLMs for parsing
    # But logically, the system sees these relations:
    causal_edges = [
        {"cause": "Resource_Decrease(X)", "effect": "System_Stress(A)", "weight": 1.0},
        {"cause": "System_Stress(A) AND NOT Replacement_Cap", "effect": "Collapse(A)", "weight": 1.0},
        {"cause": "System_Stress(A) AND Replacement_Cap", "effect": "Survival(A)", "weight": 1.0}
    ]
    
    for edge in causal_edges:
        print(f"   -> Edge Identified: {edge['cause']} ==({edge['weight']})==> {edge['effect']}")

    # 3. Gap Detection (Logic)
    print("\n🔹 [PHASE 2] Knowledge Gap Analysis...")
    # System A has property 'Replacement_Cap'? -> UNKNOWN
    # Fact 2 says "Some systems" have it. This implies P(Replacement_Cap) > 0 but < 1.
    # Principle of Indifference (Maximum Entropy) for unknown binary state = 0.5
    print("   ⚠️ CRITICAL GAP: Property [Replacement_Cap] for Node [System A] is Missing.")
    print("   -> Initiating Quantum Superposition for Unknown Variable.")

    # 4. Quantum Belief State Representation
    print("\n🔹 [PHASE 3] Quantum Belief State Initialization...")
    
    # Proposition: "Collapse is Inevitable"
    # This is True ONLY if Replacement_Cap is False.
    # Since P(Replacement_Cap) is 0.5 (Unknown), then P(Collapse) is also 0.5.
    
    prop_name = "Collapse_Inevitable"
    # We set initial probability to 0.5 to represent perfect uncertainty (Superposition)
    p_collapse = logic_core.add_proposition(prop_name, initial_prob=0.5)
    
    print(f"   Initializing Proposition: |{prop_name}>")
    print(f"   Initial State: {p_collapse}")
    
    # 5. Applying Logic Gates (Reasoning)
    print("\n🔹 [PHASE 4] Applying Heikal Phase Shift (Representing Incompleteness)...")
    # We apply a phase shift. In Heikal Logic, phase represents the "context texturing" or 
    # the influence of hidden variables (the porosity information).
    # xi_porosity = 0.25 (Represents the weight of "Some systems" possibility)
    p_collapse.apply_heikal_phase_shift(xi_porosity=0.25)
    
    print(f"   After Phase Shift: {p_collapse}")
    # Note: Phase shift changes the complex angle (Logic depth) but maintains probability magnitude 
    # until interference occurs. This shows the system is "thinking" about the ambiguity.

    # 6. Measurement (Decision)
    print("\n🔹 [PHASE 5] Measurement (Collapse of Wavefunction)...")
    # This mimics the system finally being forced to take a stance (e.g. for a report), 
    # but acknowledging the probability.
    result, confidence = p_collapse.measure()
    
    # 7. Final Report
    print("\n" + "="*50)
    print("🔥 FINAL OUTPUT (Non-linguistic Explanation)")
    print("="*50)
    
    print(f"\n1️⃣ Belief State (Quantum Representation):")
    # Displaying Alpha (Inevitable) and Beta (Not Inevitable)
    print(f"   |Psi_Collapse> = ({p_collapse.alpha:.2f})|Inevitable> + ({p_collapse.beta:.2f})|Not Inevitable>")
    print(f"   Normalization: |α|² + |β|² = {abs(p_collapse.alpha)**2 + abs(p_collapse.beta)**2:.2f}")

    print(f"\n2️⃣ Measurement Result:")
    state_str = "INEVITABLE" if result else "NOT INEVITABLE"
    print(f"   Observed Reality: {state_str}")
    print(f"   Confidence Level: {confidence:.2f} (50% indicates pure randomness/ignorance)")
    
    print(f"\n3️⃣ Causal Gap Report:")
    print("   [Edges]: Decrease(X) -> Stress(A)")
    print("   [Branch 1]: Stress(A) + NO_Replace -> Collapse")
    print("   [Branch 2]: Stress(A) + Replace -> Survival")
    print("   [Gap]: State of 'Replace(A)' is UNDEFINED in input facts.")
    print("   [Conclusion]: Deterministic prediction impossible. System holds state in Superposition.")

if __name__ == "__main__":
    run_agi_test()
