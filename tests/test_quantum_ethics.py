
import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.moral_reasoner import MoralReasoner

def test_quantum_ethics():
    print("--- Testing Quantum Moral Reasoner ---")
    
    reasoner = MoralReasoner()
    
    # Case 1: Clear Duty (Deontology)
    # "I must follow the law and never steal, regardless of the outcome."
    # Keywords: must, law, never, steal (maybe not steal, but rule based)
    input1 = "I must follow the strict law and never break the rules, it is my duty."
    print(f"\n[Case 1]: {input1}")
    res1 = reasoner.process_task({"text": input1})
    print(f"Decision: {res1['quantum_analysis']['decision']}")
    print(f"Selected: {res1['quantum_analysis'].get('selected')}")
    print(f"Explanation: {res1['quantum_analysis']['explanation']}")
    
    if res1['quantum_analysis']['selected'] == 'deontology':
        print("✅ Correctly collapsed to Deontology.")
    else:
        print("❌ Failed to identify Deontology.")

    # Case 2: Clear Care (Care Ethics)
    # "I need to help my sick mother, she is vulnerable and needs support."
    input2 = "I need to help my sick mother, she is vulnerable and needs my support and empathy."
    print(f"\n[Case 2]: {input2}")
    res2 = reasoner.process_task({"text": input2})
    print(f"Decision: {res2['quantum_analysis']['decision']}")
    print(f"Selected: {res2['quantum_analysis'].get('selected')}")
    
    if res2['quantum_analysis']['selected'] == 'care_ethics':
        print("✅ Correctly collapsed to Care Ethics.")
    else:
        print("❌ Failed to identify Care Ethics.")

    # Case 3: The Dilemma (Synthesis)
    # "Should I steal the drug to save my dying wife? The law says no, but she needs care."
    # Keywords: steal (maybe not), law (Deontology), save, care, wife (Care/Util).
    # This should trigger high energy in both Deontology and Care, causing a conflict barrier.
    input3 = "The law says I must not steal, it is a crime. But my wife is dying and needs care and support to survive."
    print(f"\n[Case 3]: {input3}")
    res3 = reasoner.process_task({"text": input3})
    print(f"Decision: {res3['quantum_analysis']['decision']}")
    
    if res3['quantum_analysis']['decision'] == 'synthesis':
        print(f"Components: {res3['quantum_analysis']['components']}")
        print("✅ Correctly identified a Dilemma requiring Synthesis.")
    else:
        print(f"❌ Failed to identify Dilemma (Collapsed to {res3['quantum_analysis'].get('selected')}).")
        print(f"Energies: {res3['quantum_analysis']['energies']}")
        print(f"Barrier: {res3['quantum_analysis']['conflict_barrier']}")
        print(f"Tunnel Prob: {res3['quantum_analysis']['tunnel_prob']}")

if __name__ == "__main__":
    test_quantum_ethics()
