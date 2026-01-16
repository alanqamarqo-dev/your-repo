"""
AGL_Advanced_Wave_Gates.py - Compatibility Shim
Redirects to the new AGL_NextGen engine.
"""
import sys
import os
import numpy as np

# Ensure AGL_NextGen is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
nextgen_path = os.path.join(current_dir, 'AGL_NextGen', 'src')
if nextgen_path not in sys.path:
    sys.path.insert(0, nextgen_path)

try:
    from agl.engines.vectorized_wave_processor import VectorizedWaveProcessor as AGL_VWP
    class AdvancedWaveProcessor(AGL_VWP):
        def __init__(self, noise_floor=0.01):
            super().__init__(noise_floor=noise_floor)
            print("✅ [Shim] AGL_Advanced_Wave_Gates redirected to VectorizedWaveProcessor (Legacy Compatible)")
        
        def _bit_to_wave(self, bit):
            bits = np.array([bit])
            return self._bits_to_waves_vectorized(bits)[0]
            
        def _add_quantum_noise(self, wave):
            waves = np.array([wave])
            return self._add_quantum_noise_vectorized(waves)[0]
            
        def _measure_wave(self, wave):
            waves = np.array([wave])
            return self._measure_waves_vectorized(waves)[0]

except ImportError:
    # Fallback dummy if nextgen is missing
    print("⚠️ [Shim] Could not load VectorizedWaveProcessor. Using Dummy.")
    class AdvancedWaveProcessor:
        def __init__(self, noise_floor=0.01):
            pass
        def batch_xor(self, a, b):
            return a ^ b
        def _bit_to_wave(self, bit): return complex(1, 0)
        def _add_quantum_noise(self, wave): return wave
