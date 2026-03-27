import sys
import os
import json

# Add repo root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'repo-copy'))

from Scientific_Systems.Scientific_Integration_Orchestrator import ScientificIntegrationOrchestrator

def run_simulation_test():
    orchestrator = ScientificIntegrationOrchestrator()
    
    print("--- 🌌 AGL Impossible Questions Simulation Test ---\n")
    
    # Test 1: Dark Matter
    print(">>> Test 1: Dark Matter WIMP Detection")
    dm_proposal = """
    Proposal to detect Dark Matter WIMPs using a 1000 kg Xenon detector.
    Expected cross-section is 1e-47 cm^2.
    Exposure time: 5 years.
    Background noise: 0.001 events/kg/year.
    """
    print(f"Input: {dm_proposal.strip()}")
    
    dm_result = orchestrator.analyze_scientific_design(dm_proposal)
    
    print("\n[Simulation Results]")
    if "simulation" in dm_result:
        sim = dm_result["simulation"]
        print(f"Feasibility: {sim['feasibility']}")
        print(f"Numerical Results: {json.dumps(sim['numerical_results'], indent=2)}")
        if sim['issues']:
            print(f"Issues: {sim['issues']}")
            
    print("\n[Mathematical Proof]")
    if "mathematical_proof" in dm_result:
        print(dm_result["mathematical_proof"])
        
    print("\n" + "="*50 + "\n")
    
    # Test 2: Arrow of Time (Entropy)
    print(">>> Test 2: The Arrow of Time (Entropy Simulation)")
    entropy_proposal = """
    Analyze the Arrow of Time using a particle box model.
    System: 500 particles.
    Steps: 2000.
    Hypothesis: Entropy will increase monotonically.
    """
    print(f"Input: {entropy_proposal.strip()}")
    
    entropy_result = orchestrator.analyze_scientific_design(entropy_proposal)
    
    print("\n[Simulation Results]")
    if "simulation" in entropy_result:
        sim = entropy_result["simulation"]
        print(f"Feasibility: {sim['feasibility']}")
        print(f"Numerical Results: {json.dumps(sim['numerical_results'], indent=2)}")
        if sim['issues']:
            print(f"Issues: {sim['issues']}")

    print("\n[Mathematical Proof]")
    if "mathematical_proof" in entropy_result:
        print(entropy_result["mathematical_proof"])

if __name__ == "__main__":
    run_simulation_test()
