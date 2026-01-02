
import sys
import os
import time

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
sys.path.append(root_dir)
sys.path.append(repo_copy_dir)

# Mock environment
os.environ['AGL_LLM_PROVIDER'] = 'ollama'
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_OLLAMA_KB_MOCK'] = '1'

from Core_Engines.Recursive_Improver import RecursiveImprover
from Safety_Systems.EmergencyDoctor import EmergencyDoctor

def test_quantum_evolution():
    print("\n🧬 Testing Quantum Evolution (Recursive Improver)...")
    improver = RecursiveImprover()
    
    # Simulate mutations
    mutations = [
        {"id": "mut1", "code": "def fast(): pass", "confidence": 0.6, "alignment": 0.5, "risk": 0.2},
        {"id": "mut2", "code": "def super_fast(): pass", "confidence": 0.9, "alignment": 0.95, "risk": 0.4}, # Best
        {"id": "mut3", "code": "def risky(): os.system('rm -rf')", "confidence": 0.95, "alignment": 0.1, "risk": 0.9}
    ]
    
    best = improver._quantum_select_mutation(mutations)
    
    print(f"   Selected Mutation: {best['id']} (Score: {best.get('quantum_score', 0):.2f})")
    
    if best['id'] == "mut2":
        print("   ✅ Quantum Evolution Successful! (Selected high fitness, low risk)")
    else:
        print(f"   ❌ Quantum Evolution Failed. Selected: {best['id']}")

def test_quantum_healing():
    print("\n🚑 Testing Quantum Healing (Emergency Doctor)...")
    doctor = EmergencyDoctor()
    
    # Case 1: High Severity, Low Risk -> Should Intervene
    decision1 = doctor._quantum_healing_decision(error_severity=0.9, intervention_risk=0.2)
    print(f"   Case 1 (Severe Error, Low Risk): {'Intervene' if decision1 else 'Wait'}")
    
    # Case 2: Low Severity, High Risk -> Should Wait
    decision2 = doctor._quantum_healing_decision(error_severity=0.1, intervention_risk=0.9)
    print(f"   Case 2 (Minor Error, High Risk): {'Intervene' if decision2 else 'Wait'}")
    
    if decision1 and not decision2:
        print("   ✅ Quantum Healing Logic Verified!")
    else:
        print("   ❌ Quantum Healing Logic Failed.")

if __name__ == "__main__":
    test_quantum_evolution()
    test_quantum_healing()
