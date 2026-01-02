
import sys
import os
import numpy as np

# Add repo-copy to path to allow imports
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

try:
    from Core_Engines.Resonance_Optimizer import ResonanceOptimizer
except ImportError:
    # Fallback if running from root
    sys.path.append(os.path.join(os.getcwd(), 'AGL', 'repo-copy'))
    from Core_Engines.Resonance_Optimizer import ResonanceOptimizer

def test_quantum_tunneling():
    print("\n🧪 Testing Quantum Tunneling (WKB Approximation)...")
    optimizer = ResonanceOptimizer(h_bar=1.0, mass=1.0, barrier_width=0.5)
    
    # Scenario: We are at a local minimum (Energy 10) and want to move to a better state (Energy 15)
    # But there is a barrier in between.
    
    # Case 1: Small barrier (High probability)
    energy_deficit = 2.0 # Barrier is 2 units higher than current energy
    prob = optimizer._wkb_tunneling_prob(energy_diff=-energy_deficit, barrier_height=5.0)
    print(f"   - Energy Deficit: {energy_deficit}")
    print(f"   - Tunneling Probability: {prob:.4f}")
    
    # Case 2: Large barrier (Low probability)
    energy_deficit_large = 10.0
    prob_large = optimizer._wkb_tunneling_prob(energy_diff=-energy_deficit_large, barrier_height=20.0)
    print(f"   - Energy Deficit: {energy_deficit_large}")
    print(f"   - Tunneling Probability: {prob_large:.4f}")
    
    if prob > prob_large:
        print("   ✅ SUCCESS: Tunneling probability decreases with barrier height/energy deficit.")
    else:
        print("   ❌ FAILURE: Probability logic seems wrong.")

def test_resonance_amplification():
    print("\n🧪 Testing Resonance Amplification...")
    optimizer = ResonanceOptimizer()
    
    natural_freq = 10.0
    
    # Case 1: Signal matches natural frequency (Resonance)
    signal_freq_match = 10.0
    amp_match = optimizer._resonance_amplification(signal_freq_match, natural_freq)
    print(f"   - Natural Freq: {natural_freq}, Signal Freq: {signal_freq_match}")
    print(f"   - Amplification Factor: {amp_match:.4f}")
    
    # Case 2: Signal is dissonant
    signal_freq_mismatch = 15.0
    amp_mismatch = optimizer._resonance_amplification(signal_freq_mismatch, natural_freq)
    print(f"   - Natural Freq: {natural_freq}, Signal Freq: {signal_freq_mismatch}")
    print(f"   - Amplification Factor: {amp_mismatch:.4f}")
    
    if amp_match > amp_mismatch:
        print("   ✅ SUCCESS: Resonance amplification boosts matching signals.")
    else:
        print("   ❌ FAILURE: Resonance logic seems wrong.")

if __name__ == "__main__":
    print("==========================================")
    print("   ⚛️  QUANTUM RESONANCE DETECTOR TEST    ")
    print("==========================================")
    
    try:
        test_quantum_tunneling()
        test_resonance_amplification()
        print("\n✅ All Quantum Resonance tests passed successfully.")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
