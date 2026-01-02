
import sys
import os

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

print("=== STARTING VERIFICATION ===")

# Import the noisy modules
try:
    print("--- Importing Heikal_Quantum_Core ---")
    from AGL_Core.Heikal_Quantum_Core import HeikalQuantumCore
    hqc1 = HeikalQuantumCore()
    hqc2 = HeikalQuantumCore() # Should not print again
except ImportError as e:
    print(f"Failed to import HeikalQuantumCore: {e}")

try:
    print("--- Importing VectorizedResonanceOptimizer ---")
    from Core_Engines.Resonance_Optimizer_Vectorized import VectorizedResonanceOptimizer
    vro1 = VectorizedResonanceOptimizer()
    vro2 = VectorizedResonanceOptimizer() # Should not print again
except ImportError as e:
    print(f"Failed to import VectorizedResonanceOptimizer: {e}")

try:
    print("--- Importing Core_Engines bootstrap ---")
    from Core_Engines import bootstrap_register_all_engines
    # Mock registry
    registry = {}
    bootstrap_register_all_engines(registry, verbose=False)
    bootstrap_register_all_engines(registry, verbose=False) # Should not print report again
except ImportError as e:
    print(f"Failed to import Core_Engines: {e}")

print("=== VERIFICATION COMPLETE ===")
