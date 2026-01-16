"""
AGL_Advanced_Wave_Gates.py - Compatibility Shim
Redirects to the new AGL_NextGen engine.
"""
import sys
import os

# Ensure AGL_NextGen is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
nextgen_path = os.path.join(current_dir, 'AGL_NextGen', 'src')
if nextgen_path not in sys.path:
    sys.path.insert(0, nextgen_path)

try:
    from agl.engines.vectorized_wave_processor import VectorizedWaveProcessor as AdvancedWaveProcessor
    print("✅ [Shim] AGL_Advanced_Wave_Gates redirected to VectorizedWaveProcessor")
except ImportError:
    # Fallback dummy if nextgen is missing
    print("⚠️ [Shim] Could not load VectorizedWaveProcessor. Using Dummy.")
    class AdvancedWaveProcessor:
        def __init__(self, noise_floor=0.01):
            pass
        def batch_xor(self, a, b):
            return a ^ b
