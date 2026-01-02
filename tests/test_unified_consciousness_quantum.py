
import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from dynamic_modules.agl_consciousness import TrueConsciousnessSystem

def test_unified_consciousness_quantum():
    print("--- Testing Unified AGI Consciousness (Quantum Enhanced) ---")
    
    tcs = TrueConsciousnessSystem()
    
    if not getattr(tcs, 'quantum_enabled', False):
        print("❌ Quantum Resonance NOT enabled in TrueConsciousnessSystem")
        return

    print("✅ Quantum Resonance Enabled in TrueConsciousnessSystem")
    
    # Create inputs that are complex enough to trigger tunneling
    # Complexity > 0.5 requires length > 500 chars
    
    input1 = "A" * 300
    input2 = "B" * 300
    inputs = [input1, input2]
    
    print(f"Integrating {len(inputs)} complex inputs...")
    
    result = tcs.integrate_information(inputs)
    
    print("\nIntegration Result:")
    print(f" - Complexity: {result['complexity']}")
    print(f" - Connectivity: {result['sources']}")
    print(f" - Synergy Factor: {result['synergy']}")
    print(f" - Quantum Boost: {result.get('quantum_boost', 0.0)}")
    print(f" - Phi Score: {result['phi']}")
    print(f" - Concept: {result['unified_concept']}")
    
    if result.get('quantum_boost', 0.0) > 0:
        print("\n✅ SUCCESS: Quantum Tunneling boosted the consciousness integration!")
    else:
        print("\n⚠️ NOTE: No quantum boost triggered (maybe barrier wasn't high enough or energy too low).")

if __name__ == "__main__":
    test_unified_consciousness_quantum()
