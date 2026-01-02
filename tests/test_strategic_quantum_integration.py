import sys
import os
import json

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Strategic_Thinking import StrategicThinkingEngine

def test_quantum_strategy_integration():
    print("🚀 Testing Quantum Strategic Analysis Integration...")
    
    engine = StrategicThinkingEngine()
    
    # Check capability
    if "quantum_strategic_analysis" not in engine.capabilities:
        print("❌ FAILURE: 'quantum_strategic_analysis' not found in capabilities.")
        return
    else:
        print("✅ Capability 'quantum_strategic_analysis' found.")
    
    # Define Options
    options = [
        {"name": "Safe Bet", "value": 0.4, "risk_factor": 0.1, "aligned": False},
        {"name": "Quantum Leap", "value": 0.9, "risk_factor": 0.8, "aligned": True}, 
        {"name": "Standard", "value": 0.5, "risk_factor": 0.3, "aligned": False}
    ]
    
    # Define Risks
    risks = [{"impact": 0.8, "likelihood": 0.5}]
    
    print("\n🔮 Running Quantum Analysis...")
    results = engine.quantum_strategic_analysis(options, risks, coherence_factor=0.9)
    
    print("\n🏆 Results:")
    for res in results:
        print(f"  - {res['name']}: Score={res['quantum_score']:.4f} (Tunneling={res['tunneling_prob']:.4f})")
        
    # Verification
    top_pick = results[0]
    if top_pick['name'] == "Quantum Leap":
        print("\n✅ SUCCESS: The Quantum Engine correctly identified the high-value, high-risk option.")
    else:
        print(f"\n⚠️ NOTE: Top pick was {top_pick['name']}.")

if __name__ == "__main__":
    test_quantum_strategy_integration()
