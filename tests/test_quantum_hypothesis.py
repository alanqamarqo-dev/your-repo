import sys
import os
import json

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Hypothesis_Generator import HypothesisGeneratorEngine

def test_quantum_hypothesis():
    print("🚀 Testing Quantum Hypothesis Generation (Scientific Intuition)...")
    
    engine = HypothesisGeneratorEngine()
    
    # Scenario: Analyzing Dark Matter
    topic = "Dark Matter"
    context = "Galactic rotation curves do not match visible mass. Something hidden is exerting gravity."
    
    # We manually inject some hypotheses to test the filter
    # 1. Standard: Boring, safe.
    # 2. Quantum Leap: Crazy but insightful (High Barrier, High Resonance).
    # 3. Noise: Just crazy.
    
    hypotheses = [
        "Maybe the measurements are wrong.", # Standard
        "A hidden non-linear quantum field suggests a latent mass paradigm.", # Quantum Leap (Complex words + Insight)
        "Aliens are pushing the stars." # Noise (High Barrier, Low Insight)
    ]
    
    print("\n🧪 Input Hypotheses:")
    for h in hypotheses:
        print(f"  - {h}")
        
    print("\n🔮 Running Quantum Intuition Filter...")
    ranked = engine.quantum_intuition_filter(hypotheses, context)
    
    print("\n🏆 Ranked Results:")
    for item in ranked:
        print(f"  - Type: {item['type']}")
        print(f"    Text: {item['text']}")
        print(f"    Score: {item['score']:.4f}")
        print(f"    Metrics: {item['metrics']}")
        print("-" * 40)
        
    # Verification
    top = ranked[0]
    if top['type'] == "Quantum Leap":
        print("\n✅ SUCCESS: System prioritized the 'Quantum Leap' hypothesis despite its complexity.")
    else:
        print(f"\n⚠️ NOTE: Top result was {top['type']}.")

if __name__ == "__main__":
    test_quantum_hypothesis()
