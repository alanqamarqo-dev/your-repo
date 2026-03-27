
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Heikal_Quantum_Core import HeikalQuantumCore

def test_heikal_engineer():
    print("Initializing Heikal Quantum Core...")
    core = HeikalQuantumCore()
    
    print("\nChecking components:")
    print(f"Moral Engine: {core.moral_engine}")
    print(f"Resonance Optimizer: {core.resonance_optimizer}")
    print(f"Neural Net (Engineer?): {core.neural_net}")
    
    if core.neural_net:
        print("\nTesting Neural Net with a coding task...")
        prompt = "Write a Python function to calculate Fibonacci sequence optimized for speed."
        # QuantumNeuralCore.collapse_wave_function(prompt)
        try:
            response = core.neural_net.collapse_wave_function(prompt)
            print("\nResponse from Neural Net:")
            print(response)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_heikal_engineer()
