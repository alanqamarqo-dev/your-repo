import sys
import os
import json

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Social_Interaction import SocialInteractionEngine

def test_quantum_empathy():
    print("🚀 Testing Quantum Empathy (Social Interaction)...")
    
    engine = SocialInteractionEngine()
    
    # Scenario: User is very angry (High Barrier)
    # We have moderate rapport (0.5)
    user_text = "I hate this system! It is terrible and the worst experience ever!"
    print(f"\n🗣️ User: '{user_text}'")
    
    result = engine.quantum_empathy_analysis(user_text, current_rapport=0.5)
    
    print("\n🧠 Quantum Analysis:")
    print(f"  - Barrier (Anger): {result['barrier']:.2f}")
    print(f"  - Resonance (Alignment): {result['resonance']:.2f}")
    print(f"  - Tunneling Prob (Breakthrough): {result['tunneling_prob']:.4f}")
    print(f"  - Recommendation: {result['recommendation']}")
    
    if result['recommendation'] == "Deep Empathy (Quantum Tunneling)":
        print("\n✅ SUCCESS: System detected high barrier and recommended Quantum Tunneling (Deep Empathy) to break through.")
    else:
        print("\n⚠️ NOTE: System recommended standard support.")

if __name__ == "__main__":
    test_quantum_empathy()
